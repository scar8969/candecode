#!/usr/bin/env python3
"""can-analyzer CLI - parse CAN logs, load DBC files and export decoded CSV.

The parser, DBC decoder and signal extraction are pure standard library, so the
analysis subcommands run without Flask.  "serve" imports the web application
lazily inside the subcommand, so `python cli.py --help` exits 0 even when the
web dependencies are absent.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from typing import Any

from . import paths

ROOT = str(paths.PROJECT_ROOT)
VERSION = "0.1.0"


def _parse(path: str, fmt: str) -> list:
    from .can.parser import parse_asc, parse_csv

    fmt = fmt or ("csv" if path.lower().endswith(".csv") else "asc")
    return parse_asc(path) if fmt == "asc" else parse_csv(path)


def _load_dbc(path: str) -> dict:
    from .can.dbc import load_dbc

    with open(path) as fh:
        return load_dbc(fh.read())


def cmd_parse(args) -> int:
    frames = _parse(args.file, args.format)
    ids: dict[str, Any] = {}
    for f in frames:
        ids[f["can_id"]] = ids.get(f["can_id"], 0) + 1
    span = (frames[0]["ts"], frames[-1]["ts"]) if frames else (0.0, 0.0)
    print(f"{args.file}: {len(frames)} frame(s), t={span[0]:.3f}..{span[1]:.3f}s")
    for can_id, n in sorted(ids.items()):
        print(f"  0x{can_id}  {n} frame(s)")
    if args.json:
        print(
            json.dumps(
                [{"ts": f["ts"], "can_id": f["can_id"], "data": f["data"].hex()} for f in frames],
                indent=2,
            )
        )
    return 0


def cmd_dbc(args) -> int:
    msgs = _load_dbc(args.file)
    print(f"{args.file}: {len(msgs)} message(s)")
    for can_id, md in sorted(msgs.items()):
        print(f"  0x{can_id} {md.name}")
        for sig in md.signals:
            print(
                f"      {sig.name:<12} start={sig.start:<3} len={sig.length:<3} "
                f"scale={sig.scale:<8g} offset={sig.offset:<8g} {sig.unit}"
            )
    return 0


def cmd_decode(args) -> int:
    from .can.dbc import decode

    frames = _parse(args.log, args.format)
    msgs = _load_dbc(args.dbc)
    frame = frames[args.frame] if args.frame < len(frames) else None
    if frame is None:
        print(f"error: frame {args.frame} out of range (log has {len(frames)})", file=sys.stderr)
        return 2
    md = msgs.get(frame["can_id"])
    if md is None:
        print(f"error: no DBC message for 0x{frame['can_id']}", file=sys.stderr)
        return 2
    values = decode(frame, md)
    print(
        f"frame {args.frame}: t={frame['ts']:.3f}s can_id=0x{frame['can_id']} "
        f"data={frame['data'].hex()} ({md.name})"
    )
    for name, value in values.items():
        print(f"  {name:<12} {value}")
    if args.signal:
        if args.signal not in values:
            print(f"error: signal {args.signal} not in {md.name}", file=sys.stderr)
            return 2
        print(f"{args.signal}={values[args.signal]}")
    return 0


def cmd_signals(args) -> int:
    from .can.signals import extract

    frames = _parse(args.log, args.format)
    msgs = _load_dbc(args.dbc)
    md = msgs.get(args.can_id.upper().removeprefix("0X"))
    if md is None:
        print(f"error: no DBC message with id {args.can_id}; have {sorted(msgs)}", file=sys.stderr)
        return 2
    series = extract(frames, md, args.signal)
    print(f"{md.name}.{args.signal}: {len(series)} sample(s)")
    for ts, value in series:
        print(f"  {ts:>9.3f}s {value}")
    return 0


def cmd_export(args) -> int:
    from .can.dbc import decode

    frames = _parse(args.log, args.format)
    msgs = _load_dbc(args.dbc) if args.dbc else {}
    out = args.out or os.path.splitext(args.log)[0] + "_decoded.csv"
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ts", "can_id", "data", "decoded"])
        for f in frames:
            md = msgs.get(f["can_id"])
            decoded = decode(f, md) if md else {}
            w.writerow([f["ts"], f["can_id"], f["data"].hex(), json.dumps(decoded)])
    print(f"wrote {len(frames)} row(s) -> {out}")
    return 0


def cmd_serve(args) -> int:
    from ._app import app

    app.run(host=args.host, port=args.port, debug=False)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="can-analyzer", description="CAN bus analyzer: logs, DBC decode, CSV export."
    )
    p.add_argument("--version", action="version", version=f"can-analyzer {VERSION}")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("parse", help="summarise an ASC or CSV candump log")
    a.add_argument("file")
    a.add_argument("--format", choices=["asc", "csv"], help="default: by file extension")
    a.add_argument("--json", action="store_true", help="also print every frame as JSON")
    a.set_defaults(func=cmd_parse)

    d = sub.add_parser("dbc", help="list the messages and signals in a DBC file")
    d.add_argument("file")
    d.set_defaults(func=cmd_dbc)

    c = sub.add_parser("decode", help="decode a single frame with a DBC file")
    c.add_argument("log")
    c.add_argument("--dbc", required=True, help="DBC file describing the frames")
    c.add_argument("--frame", type=int, default=0, help="frame index in the log")
    c.add_argument("--signal", help="print only this signal")
    c.add_argument("--format", choices=["asc", "csv"])
    c.set_defaults(func=cmd_decode)

    s = sub.add_parser("signals", help="extract one signal series over the whole log")
    s.add_argument("log")
    s.add_argument("--dbc", required=True)
    s.add_argument("--can-id", dest="can_id", required=True, help="hex arbitration id, e.g. 123")
    s.add_argument("--signal", required=True)
    s.add_argument("--format", choices=["asc", "csv"])
    s.set_defaults(func=cmd_signals)

    e = sub.add_parser("export", help="export decoded frames to CSV")
    e.add_argument("log")
    e.add_argument("--dbc", help="DBC file; without it only timing and raw bytes are written")
    e.add_argument("--out", help="output CSV path (default: <log>_decoded.csv)")
    e.add_argument("--format", choices=["asc", "csv"])
    e.set_defaults(func=cmd_export)

    v = sub.add_parser("serve", help="run the Flask CAN analyzer UI")
    v.add_argument("--host", default="127.0.0.1")
    v.add_argument("--port", type=int, default=8000)
    v.set_defaults(func=cmd_serve)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover - manual entry point
    raise SystemExit(main())

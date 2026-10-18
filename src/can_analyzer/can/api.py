import csv
import io
import os
from typing import Any

from flask import Blueprint, Response, abort, jsonify, request

from .. import paths
from ..models import LogFile, Message, db
from .dbc import decode, load_dbc
from .parser import parse_asc, parse_csv

bp = Blueprint("can", __name__)
DATA_DIR = str(paths.DATA_DIR)
_logs: dict[str, Any] = {}  # id -> frames
_dbcs: dict[str, Any] = {}  # id -> {can_id: MessageDef}


@bp.post("/api/logs")
def upload():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "no file"}), 400
    fmt = request.form.get("format", "asc")
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, f.filename or "upload")
    f.save(path)
    frames = parse_asc(path) if fmt == "asc" else parse_csv(path)
    log = LogFile(name=f.filename, format=fmt, frame_count=len(frames))
    db.session.add(log)
    db.session.flush()
    for fr in frames:
        db.session.add(
            Message(log_id=log.id, ts=fr["ts"], can_id=fr["can_id"], data_hex=fr["data"].hex())
        )
    db.session.commit()
    _logs[log.id] = frames
    return jsonify({"id": log.id, "frames": len(frames)})


def _log_or_404(raw_id):
    """The LogFile ``raw_id`` names, or a plain 404.

    An id this process never parsed -- including a non-numeric one -- is a
    missing resource, so every view answers 404 instead of raising a
    ValueError/KeyError that would surface as a 500.
    """
    try:
        log_id = int(raw_id)
    except (TypeError, ValueError):
        abort(404)
    return LogFile.query.get_or_404(log_id)


@bp.post("/api/logs/<id>/dbc")
def upload_dbc(id):
    log = _log_or_404(id)
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "no file"}), 400
    _dbcs[log.id] = load_dbc(f.read().decode())
    return jsonify({"status": "loaded", "id": log.id, "messages": len(_dbcs[log.id])})


@bp.get("/api/logs/<id>/messages")
def messages(id):
    log = _log_or_404(id)
    filt = request.args.get("filter", "")
    q = Message.query.filter_by(log_id=log.id)
    if filt:
        q = q.filter(Message.can_id == filt)
    rows = [
        {"ts": m.ts, "can_id": m.can_id, "data": m.data_hex, "decoded": m.decoded_json}
        for m in q.order_by(Message.id).limit(200).all()
    ]
    return jsonify({"log_id": log.id, "frames": log.frame_count or 0, "messages": rows})


@bp.get("/api/logs/<id>/signals/<name>")
def signal_series(id, name):
    log = _log_or_404(id)
    frames = _logs.get(log.id, [])
    dbc = _dbcs.get(log.id, {})
    if not dbc:
        note = "no DBC attached to log %d: POST one to /api/logs/%d/dbc" % (log.id, log.id)
        return jsonify({"log_id": log.id, "signal": name, "series": [], "note": note})
    series = []
    for fr in frames:
        md = dbc.get(fr["can_id"])
        if md:
            vals = decode(fr, md)
            if name in vals:
                series.append([fr["ts"], vals[name]])
    return jsonify({"log_id": log.id, "signal": name, "frames": len(frames), "series": series})


@bp.get("/api/logs/<id>/export")
def export(id):
    log = _log_or_404(id)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["ts", "can_id", "data", "decoded"])
    for m in Message.query.filter_by(log_id=log.id).limit(10000).all():
        w.writerow([m.ts, m.can_id, m.data_hex, m.decoded_json])
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=decoded.csv"},
    )

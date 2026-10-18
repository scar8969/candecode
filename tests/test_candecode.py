"""C3 can-analyzer — tests. Run: pytest test_candecode.py"""
import sys, os

import pytest

ASC = """(1.0) can0 123#0F00
(1.5) can0 124#3E00
(2.0) can0 123#1E00
"""

DBC = """VERSION ""
BO_ 291 Engine: 8 EngineECU
 SG_ RPM : 8|16@1+ (1,0) [0,8000] "rpm"
 SG_ TMP : 24|8@1+ (1,-40) [-40,215] "degC"
BO_ 292 Vehicle: 8 EngineECU
 SG_ SPD : 0|16@1+ (0.01,0) [0,300] "km/h"
"""

def test_parse_asc(tmp_path):
    from can_analyzer.can.parser import parse_asc
    p = tmp_path / "log.asc"
    p.write_text(ASC)
    frames = parse_asc(str(p))
    assert len(frames) == 3
    assert frames[0]["can_id"] == "123"
    assert frames[0]["data"] == b"\x0f\x00"

def test_load_dbc():
    from can_analyzer.can.dbc import load_dbc
    msgs = load_dbc(DBC)
    assert "123" in msgs
    assert msgs["123"].name == "Engine"
    assert len(msgs["123"].signals) == 2

def test_decode_rpm():
    from can_analyzer.can.dbc import decode, load_dbc
    msgs = load_dbc(DBC)
    # RPM at bits 8-23 LE: byte1=0x00, byte2=0x0F → 0x0F00 = 3840
    out = decode({"can_id": "123", "data": b"\x00\x00\x0f\x00\x00\x00\x00\x00"}, msgs["123"])
    assert out["RPM"] == 3840

def test_decode_temp_offset():
    from can_analyzer.can.dbc import decode, load_dbc
    msgs = load_dbc(DBC)
    # byte 3 = 0x50 = 80 → 80 - 40 = 40
    out = decode({"can_id": "123", "data": b"\x00\x00\x00\x50\x00\x00\x00\x00"}, msgs["123"])
    assert out["TMP"] == 40

def test_extract_signal():
    from can_analyzer.can.dbc import load_dbc
    from can_analyzer.can.signals import extract
    msgs = load_dbc(DBC)
    frames = [{"ts": 1.0, "can_id": "123", "data": b"\x00\x00\x0f\x00\x00\x00\x00\x00"},
              {"ts": 2.0, "can_id": "123", "data": b"\x00\x00\x1e\x00\x00\x00\x00\x00"}]
    series = extract(frames, msgs["123"], "RPM")
    assert series == [(1.0, 3840), (2.0, 7680)]

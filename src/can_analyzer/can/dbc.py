import re


class SignalDef:
    def __init__(
        self, name: str, start: int, length: int, scale: float, offset: float, unit: str = ""
    ):
        self.name, self.start, self.length = name, start, length
        self.scale, self.offset, self.unit = scale, offset, unit


class MessageDef:
    def __init__(self, can_id: str, name: str, signals: list):
        self.can_id, self.name, self.signals = can_id, name, signals


def load_dbc(text):
    msgs = {}
    # match each BO_ block, then its SG_ lines
    for block in re.finditer(r"BO_ (\d+) (\w+).*?(?=BO_ |\Z)", text, re.S):
        can_id = f"{int(block.group(1)):X}"
        name = block.group(2)
        signals = []
        for sg in re.finditer(r"SG_ (\w+) : (\d+)\|(\d+)@(\d)([+-]) \(([^)]+)\)", block.group(0)):
            scale, offset = [float(x) for x in sg.group(6).split(",")]
            signals.append(
                SignalDef(sg.group(1), int(sg.group(2)), int(sg.group(3)), scale, offset)
            )
        msgs[can_id] = MessageDef(can_id, name, signals)
    return msgs


def decode(frame, msg_def):
    data = frame["data"]
    out = {}
    for sig in msg_def.signals:
        # little-endian: start bit is the LSB position in the bitstream
        raw = 0
        for i in range(sig.length):
            bit_pos = sig.start + i
            byte_idx = bit_pos // 8
            bit_off = bit_pos % 8
            if byte_idx < len(data):
                raw |= ((data[byte_idx] >> bit_off) & 1) << i
        out[sig.name] = round(raw * sig.scale + sig.offset, 2)
    return out

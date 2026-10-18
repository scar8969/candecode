from .dbc import decode


def extract(frames, msg_def, signal):
    return [
        (f["ts"], decode(f, msg_def)[signal])
        for f in frames
        if f["can_id"] == msg_def.can_id and signal in decode(f, msg_def)
    ]

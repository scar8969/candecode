import re

def parse_asc(path):
    frames = []
    with open(path) as f:
        for line in f:
            # format: (ts) can0 123#DEADBEEF
            m = re.search(r"\((\d+\.?\d*)\)\s+\S+\s+([0-9A-Fa-f]+)#([0-9A-Fa-f]*)", line)
            if m:
                ts = float(m.group(1))
                can_id = m.group(2)
                data = bytes.fromhex(m.group(3))
                frames.append({"ts": ts, "can_id": can_id, "data": data})
    return frames

def parse_csv(path):
    import csv
    frames = []
    with open(path) as f:
        for row in csv.DictReader(f):
            frames.append({"ts": float(row["ts"]), "can_id": row["can_id"],
                           "data": bytes.fromhex(row["data"])})
    return frames

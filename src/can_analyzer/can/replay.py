import asyncio

async def replay(frames, speed=1.0):
    last_ts = None
    for f in frames:
        if last_ts is not None:
            await asyncio.sleep((f["ts"] - last_ts) / speed)
        last_ts = f["ts"]
        yield f

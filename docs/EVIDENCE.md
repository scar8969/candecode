# Evidence

Every line below was produced by a command run against this exact checkout, on this machine, at the time recorded. Nothing here is copied from the README.

| | |
| --- | --- |
| Generated | 2026-10-19 11:57 |
| Python | 3.14.7 |
| Platform | Windows 11 |

## Test suite

```sh
python -m pytest -q
```

- exit code **0**
- 25 passed in 1.16s

## Static gates

| Gate | Exit | Last line |
| --- | --- | --- |
| `ruff check` | 0 | All checks passed! |
| `ruff format --check` | 0 | 21 files already formatted |
| `mypy src` | 0 | Success: no issues found in 17 source files |
| `bandit -c pyproject.toml -r src` | 0 | — |

## Live route walk

The application was imported through `wsgi.py` and each GET path declared in `openapi/` was requested once through the Werkzeug test client.

| Status | Path | Bytes | Content-Type |
| --- | --- | --- | --- |
| 404 | `/api/logs/1/messages` | 51 | application/json |
| 404 | `/api/logs/1/signals/1` | 51 | application/json |
| 404 | `/api/logs/1/export` | 51 | application/json |

3 paths walked, 0 of them raised or answered 5xx.

## CLI

```
usage: can-analyzer [-h] [--version]
                    {parse,dbc,decode,signals,export,serve} ...

CAN bus analyzer: logs, DBC decode, CSV export.

positional arguments:
  {parse,dbc,decode,signals,export,serve}
    parse               summarise an ASC or CSV candump log
    dbc                 list the messages and signals in a DBC file
    decode              decode a single frame with a DBC file
    signals             extract one signal series over the whole log
    export              export decoded frames to CSV
    serve               run the Flask CAN analyzer UI

```

## Screenshots

Captured from the running service with headless Chromium at 1440x900 and committed with the repository:

| File | Bytes |
| --- | --- |
| `docs/assets/screens/healthz.png` | 8,647 |
| `docs/assets/screens/livez.png` | 7,468 |
| `docs/assets/screens/metrics.png` | 15,250 |
| `docs/assets/screens/readyz.png` | 7,880 |
| `docs/assets/screens/root.png` | 42,072 |
| `docs/assets/screens/version.png` | 26,832 |

## What this file does not prove

- It is not a load test: every request is a single uncached call from one process.
- A green suite is not a coverage claim; `pytest --cov` reports the number the README quotes.
- The route walk exercises GET paths only; mutating routes are covered by the suite.

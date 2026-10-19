<p align="center">
  <img src="docs/assets/screens/root.png" alt="candecode running" width="900">
</p>

<h1 align="center">candecode</h1>

<p align="center"><b>Parse CAN logs, decode them against a DBC, chart the signals.</b></p>

<p align="center">
  <a href="https://github.com/scar8969/candecode/actions/workflows/ci.yml"><img src="https://github.com/scar8969/candecode/actions/workflows/ci.yml/badge.svg" alt="ci"></a> <a href="#quality-gates"><img src="https://img.shields.io/badge/tests-25%20passed-2ea44f" alt="tests: 25 passed"></a> <a href="#quality-gates"><img src="https://img.shields.io/badge/coverage-58.6%-yellow" alt="coverage: 58.6%"></a> <a href="#api"><img src="https://img.shields.io/badge/routes-8%20live-0969da" alt="routes: 8 live"></a> <a href="#requirements"><img src="https://img.shields.io/badge/python-3.11%2B-3776ab" alt="python: 3.11+"></a> <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2ea44f" alt="license: MIT"></a>
</p>

candecode ingests ASC and candump CSV logs, loads a DBC, decodes frames into signals with scaling and units, and exposes the result as a table, a chart and a CSV export.

---

**Contents** &nbsp;·&nbsp; [Why](#why-this-exists) &nbsp;·&nbsp; [What it does](#what-it-does) &nbsp;·&nbsp; [Quickstart](#quickstart) &nbsp;·&nbsp; [Screenshots](#screenshots) &nbsp;·&nbsp; [API](#api) &nbsp;·&nbsp; [CLI](#cli) &nbsp;·&nbsp; [Configuration](#configuration) &nbsp;·&nbsp; [Measured](#measured-not-estimated) &nbsp;·&nbsp; [How a request flows](#how-a-request-flows) &nbsp;·&nbsp; [Architecture](#architecture) &nbsp;·&nbsp; [Quality gates](#quality-gates) &nbsp;·&nbsp; [Development](#development) &nbsp;·&nbsp; [Deploy](#deploy) &nbsp;·&nbsp; [Limits](#limits-stated-rather-than-hidden)

## Why this exists

CAN analysis is usually a Windows tool and a licence. Parsing the log formats and applying the DBC in Python makes the same work reproducible, scriptable and free — and the decoder is testable against known frames.

## What it does

| Capability | How it works |
| --- | --- |
| **ASC and CSV parsing** | Both log formats normalise to the same frame list. |
| **DBC decoding** | Signal extraction with start bit, length, endianness, factor and offset. |
| **Per-signal series** | A signal's values over time, for charting and export. |
| **Export** | Decoded signals as CSV for a spreadsheet or a report. |
| **CLI** | parse, dbc, decode, signals, export and serve. |

## Quickstart

```sh
git clone https://github.com/scar8969/candecode.git
cd candecode
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python wsgi.py                                 # http://127.0.0.1:8000
```

## Screenshots

Captured from the running service with headless Chromium at 1440×900, one image per page, committed under [`docs/assets/screens/`](docs/assets/screens/).

<table>
<tr>
<td width="50%"><img src="docs/assets/screens/healthz.png" alt="/healthz" width="100%"><br><sub><code>/healthz</code> &middot; 8.4 KB</sub></td>
<td width="50%"><img src="docs/assets/screens/livez.png" alt="/livez" width="100%"><br><sub><code>/livez</code> &middot; 7.3 KB</sub></td>
</tr>
</table>

<table>
<tr>
<td width="50%"><img src="docs/assets/screens/metrics.png" alt="/metrics" width="100%"><br><sub><code>/metrics</code> &middot; 14.9 KB</sub></td>
<td width="50%"><img src="docs/assets/screens/readyz.png" alt="/readyz" width="100%"><br><sub><code>/readyz</code> &middot; 7.7 KB</sub></td>
</tr>
</table>

<table>
<tr>
<td width="50%"><img src="docs/assets/screens/version.png" alt="/version" width="100%"><br><sub><code>/version</code> &middot; 26.2 KB</sub></td>
</tr>
</table>

## API

Every route below is declared in [`openapi/candecode.yaml`](openapi/candecode.yaml) and exercised by the live probe recorded in [`docs/EVIDENCE.md`](docs/EVIDENCE.md).

| Method | Path | What it does |
| --- | --- | --- |
| `POST` | `/api/logs` | upload log |
| `POST` | `/api/logs/<id>/dbc` | upload dbc |
| `GET` | `/api/logs/<id>/messages` | messages |
| `GET` | `/api/logs/<id>/signals/<name>` | signal series |
| `GET` | `/api/logs/<id>/export` | CSV |

## CLI

The same operations without an HTTP client. Installed as `candecode`, and runnable from a checkout with no install:

```sh
python -m can_analyzer.cli --help
```

```text
usage: can-analyzer [-h] [--version] {parse,dbc,decode,signals,export,serve} ...

CAN bus analyzer: logs, DBC decode, CSV export.

positional arguments:
  {parse,dbc,decode,signals,export,serve}
    parse               summarise an ASC or CSV candump log
    dbc                 list the messages and signals in a DBC file
    decode              decode a single frame with a DBC file
    signals             extract one signal series over the whole log
    export              export decoded frames to CSV
    serve               run the Flask CAN analyzer UI

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
```

## Configuration

Environment only — there is no config file. Copy `.env.example` to `.env` and edit; `APP_ENV=production` refuses to start without `SECRET_KEY`.

| Variable | Default | Meaning |
| --- | --- | --- |
| `APP_ENV` | `development` | development \| staging \| production; production enforces the secret. |
| `SECRET_KEY` | `change-me-in-production` | Session/CSRF signing key. Required when APP_ENV=production. |
| `HOST` | `0.0.0.0` | Interface the dev server binds. |
| `PORT` | `8000` | Port the dev server and the container listen on. |
| `DEBUG` | `false` | Flask debug mode. Never true in production. |
| `MAX_CONTENT_LENGTH` | `8388608` | Largest accepted request body, in bytes. |
| `DATA_DIR` | `(empty)` | Where uploaded and generated files live. |
| `INSTANCE_DIR` | `(empty)` | Where the SQLite file and instance state live. |
| `LOG_DIR` | `(empty)` | Where rotated log files are written, if file logging is on. |
| `LOG_LEVEL` | `INFO` | DEBUG \| INFO \| WARNING \| ERROR. |
| `LOG_JSON` | `true` | true emits one JSON object per line; false is human-readable. |
| `REQUEST_ID_HEADER` | `X-Request-ID` | Header echoed on every response and stamped on every log line. |
| `CANANALYZER_DATA_DIR` | `(empty)` | Where uploaded log and DBC files are stored; defaults under the data dir. |
| `CANANALYZER_SECRET` | `can-analyzer-dev-secret` | Flask session key; set it in production. |

## Measured, not estimated

Produced on this checkout by `pytest --cov` and by booting `wsgi.py` and issuing one real GET per documented path. The commands are recorded in [`docs/EVIDENCE.md`](docs/EVIDENCE.md).

| Signal | Value |
| --- | --- |
| Tests | **25 / 25 passed** (2.0 s, exit 0) |
| Line coverage | **58.6%** — 464 of 751 statements |
| Source | 16 files / 1,596 lines |
| Test code | 4 files / 264 lines |
| Documented paths | 5 in the spec, 3 GET |
| Live probe | 11 GET requests to the booted app, **8 answered 200** |
| Median latency | **5.2 ms** (single uncached request, dev server) |
| Slowest / fastest | 98.7 ms `/` / 3.8 ms `/metrics` |
| Bytes served | 8.6 KB across 11 responses |
| Screenshots | 6 captured |

## How a request flows

```text
client
  │  HTTP
  ▼
wsgi.py ──▶ can_analyzer/app.py:get_app()
                │  reads config once (can_analyzer/config.py)
                │  registers the `can` blueprint
                ▼
           route handler
             ├──▶ can_analyzer/models.py        tables, via Flask-SQLAlchemy
             ├──▶ can_analyzer/errors.py        raises typed errors → one JSON envelope
             └──▶ can_analyzer/observability.py JSON log line + X-Request-ID
```

Every response carries `X-Request-ID`, and the matching log line is written once at the end of the request with the status and duration, so a report of "it failed" is one `grep` away from the traceback.

## Architecture

```
candecode/
├── src/can_analyzer/
│   ├── http.py                         379  HTTP plumbing for can_analyzer: correlation ids, acc
│   ├── cli.py                          193  can-analyzer CLI - parse CAN logs, load DBC files an
│   ├── config.py                       172  Environment-driven configuration for can_analyzer
│   ├── _app.py                         169  
│   ├── observability.py                169  Structured logging and request correlation for can_a
│   ├── app.py                          119  Application factory for can_analyzer
│   ├── can/api.py                      110  
│   ├── errors.py                       108  Typed application errors and their HTTP mapping for 
│   ├── paths.py                         52  Filesystem layout for can_analyzer
│   ├── can/dbc.py                       47  
│   ├── can/parser.py                    32  
│   ├── models.py                        25  
├── openapi/candecode.yaml                 the contract of record
├── schema/candecode.sql                   the DDL
├── tests/                       the suite that has to stay green
├── docs/EVIDENCE.md             the recorded live route walk
├── Dockerfile                   multi-stage build
└── wsgi.py                      entry point
```

The package keeps one shape across the service: `config.py` reads the environment once, `observability.py` emits structured JSON logs carrying a request id, `errors.py` turns exceptions into a single JSON envelope, `models.py` holds the tables, and the `can/` package holds the routes.

## Quality gates

| Gate | Command | Threshold |
| --- | --- | --- |
| Suite | `pytest -q` | all green |
| Coverage | `pytest --cov` | floor in `pyproject.toml`, set below the measured value |
| Lint | `ruff check src tests` | zero findings |
| Format | `ruff format --check src tests` | zero reformats |
| Types | `mypy src` | zero errors |
| Security | `bandit -c pyproject.toml -r src` | reviewed skip list, no unreviewed finding |
| Live routes | boot `wsgi.py`, one GET per documented path | no 5xx, no undocumented guard |

CI runs the first six on Python 3.11, 3.12 and 3.13 on every push to `main`, plus a container build — [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Development

```sh
pip install -e ".[dev]"
python -m pytest -q                      # the suite
python -m pytest --cov                   # with the coverage floor
python -m ruff check src tests           # lint
python -m ruff format --check src tests  # formatting
python -m mypy src                       # types
python -m bandit -c pyproject.toml -r src  # security
pre-commit install                       # the same checks on commit
```

Dependabot opens grouped PRs for the dev tooling weekly and for actions and the base image monthly.

## Deploy

```sh
docker build -t candecode .
docker run --rm -p 8000:8000 --env-file .env.example candecode
```

A `docker-compose.yml` is included for a local run with a volume for the SQLite file. The image runs as a non-root user and serves through gunicorn.

## Limits, stated rather than hidden

- Parsed logs are held in memory for the process lifetime.
- The DBC loader reads the signal definitions and scaling attributes it needs; extended attribute tables are ignored.

## License

MIT — see [LICENSE](LICENSE).

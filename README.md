<p align="center">
  <img src="docs/assets/screens/root.png" alt="candecode running" width="900">
</p>

<h1 align="center">candecode</h1>

<p align="center"><b>Parse CAN logs, decode them against a DBC, chart the signals.</b></p>

<p align="center">
  <a href="#quality-gates"><img src="https://img.shields.io/badge/tests-25%20passed-2ea44f" alt="tests: 25 passed"></a> <a href="#quality-gates"><img src="https://img.shields.io/badge/coverage-58.6%-yellow" alt="coverage: 58.6%"></a> <a href="#api"><img src="https://img.shields.io/badge/routes-8%20answered-0969da" alt="routes: 8 answered"></a> <a href="#requirements"><img src="https://img.shields.io/badge/python-3.11%2B-3776ab" alt="python: 3.11+"></a> <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2ea44f" alt="license: MIT"></a>
</p>

candecode ingests ASC and candump CSV logs, loads a DBC, decodes frames into signals with scaling and units, and exposes the result as a table, a chart and a CSV export.

---

**Contents** &nbsp;·&nbsp; [Why](#why-this-exists) &nbsp;·&nbsp; [What it does](#what-it-does) &nbsp;·&nbsp; [Quickstart](#quickstart) &nbsp;·&nbsp; [API](#api) &nbsp;·&nbsp; [Screenshots](#screenshots) &nbsp;·&nbsp; [Measured](#measured-not-estimated) &nbsp;·&nbsp; [Architecture](#architecture) &nbsp;·&nbsp; [Quality gates](#quality-gates) &nbsp;·&nbsp; [Deploy](#deploy) &nbsp;·&nbsp; [Limits](#limits-stated-rather-than-hidden)

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

The same work from the CLI:

```sh
python -m can_analyzer.cli --help
```

Commands: `parse`, `dbc`, `decode`, `signals`, `export`, `serve`.

A first request:

```sh
curl -s http://127.0.0.1:8000/api/logs | head
```

## Requirements

- Python **3.11+** — CI runs 3.11, 3.12 and 3.13.
- Runtime dependencies: `Flask>=3.0`, `Flask-SQLAlchemy>=3.1`, `SQLAlchemy>=2.0`, `PyYAML>=6.0`.
- No JavaScript build step: every page is server-rendered Jinja.

## API

Every route below is in [`openapi/candecode.yaml`](openapi/candecode.yaml) and is exercised by the live probe recorded in [`docs/EVIDENCE.md`](docs/EVIDENCE.md).

| Method | Path | What it does |
| --- | --- | --- |
| `POST` | `/api/logs` | upload log |
| `POST` | `/api/logs/<id>/dbc` | upload dbc |
| `GET` | `/api/logs/<id>/messages` | messages |
| `GET` | `/api/logs/<id>/signals/<name>` | signal series |
| `GET` | `/api/logs/<id>/export` | CSV |

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

## Measured, not estimated

These numbers were produced on this checkout by `pytest --cov` and by booting `wsgi.py` and issuing one real GET per documented path. The commands are in [`docs/EVIDENCE.md`](docs/EVIDENCE.md).

| Signal | Value |
| --- | --- |
| Tests | **25 / 25 passed** (2.0 s, exit 0) |
| Line coverage | **58.6%** — 464 of 751 statements |
| Source | 16 files / 1,593 lines |
| Test code | 4 files / 264 lines |
| Documented paths | 5 in the spec, 3 GET |
| Live probe | 11 GET requests to the booted app, **8 answered 200** |
| Median latency | **5.2 ms** (single uncached request, dev server) |
| Slowest / fastest | 98.7 ms `/` / 3.8 ms `/metrics` |
| Bytes served | 8.6 KB across 11 responses |
| Screenshots | 6 captured |

## Architecture

```
candecode/
├── src/can_analyzer/
│   ├── http.py                         379  HTTP plumbing for can_analyzer: correlation ids, acc
│   ├── cli.py                          189  can-analyzer CLI - parse CAN logs, load DBC files an
│   ├── config.py                       173  Environment-driven configuration for can_analyzer
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
| Coverage | `pytest --cov` | floor set in `pyproject.toml` from the measured value |
| Lint | `ruff check src tests` | zero findings |
| Format | `ruff format --check src tests` | zero reformats |
| Types | `mypy src` | zero errors |
| Security | `bandit -c pyproject.toml -r src` | reviewed skip list, no unreviewed finding |
| Live routes | boot `wsgi.py`, one GET per documented path | no 5xx, no undocumented guard |

CI runs the first six on Python 3.11, 3.12 and 3.13 for every push to `main`, plus a container build. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Deploy

```sh
docker build -t candecode .
docker run --rm -p 8000:8000 --env-file .env.example candecode
```

Configuration is environment-only — every variable is documented in [`.env.example`](.env.example), and the service refuses to start with a production secret missing.

## Limits, stated rather than hidden

- Parsed logs are held in memory for the process lifetime.
- The DBC loader reads the signal definitions and scaling attributes it needs; extended attribute tables are ignored.

## License

MIT — see [LICENSE](LICENSE).

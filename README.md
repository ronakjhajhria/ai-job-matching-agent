# JobMind

JobMind is a Python career intelligence platform. Development is incremental;
the current phase is the API and configuration foundation.

## Requirements

- Python 3.11 or newer

## Setup

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
cp .env.example .env
```

The `.env` file is optional and ignored by Git. Settings can also be supplied
directly as `JOBMIND_*` environment variables.

## Run

```bash
uvicorn app.main:app --reload
```

In another terminal, request the health endpoint:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok","service":"JobMind"}
```

Interactive API documentation is available at <http://127.0.0.1:8000/docs>.

## Test

```bash
pytest
```

## Configuration

| Variable | Default | Allowed values |
| --- | --- | --- |
| `JOBMIND_SERVICE_NAME` | `JobMind` | Any string |
| `JOBMIND_ENVIRONMENT` | `development` | `development`, `test`, `production` |
| `JOBMIND_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

See [docs/concepts.md](docs/concepts.md) for design decisions and limitations,
and [docs/interview.md](docs/interview.md) for interview notes.
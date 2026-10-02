#!/usr/bin/env bash
# One-command start: creates .venv on first run, installs pinned deps, serves on $PORT (default 8000).
#   ./start.sh          run the app
#   ./start.sh test     run the tests
set -euo pipefail
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements-dev.txt
fi
if [ "${1:-}" = "test" ]; then exec .venv/bin/python -m unittest discover -s tests -t . -v; fi
PORT="${PORT:-8000}"
echo "Grain running at http://localhost:$PORT"
exec .venv/bin/uvicorn main:app --host 0.0.0.0 --port "$PORT"

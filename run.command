#!/bin/sh
cd "$(dirname "$0")" || exit 1
if [ ! -x .venv/bin/python ]; then
  echo 'First run: python3.11 scripts/setup.py (Python 3.11 or newer)'
  exit 1
fi
exec .venv/bin/python ground/server.py "$@"

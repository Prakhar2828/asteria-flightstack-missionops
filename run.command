#!/bin/sh
cd "$(dirname "$0")" || exit 1
python3 scripts/build.py && python3 ground/server.py

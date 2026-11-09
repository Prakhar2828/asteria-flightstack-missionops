#!/usr/bin/env python3
"""Create the free local runtime and build the portable spacecraft."""

import pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if sys.version_info < (3, 11):
    raise SystemExit(
        "Python 3.11+ is required. Run this script with python3.11 or newer."
    )
python = ROOT / ".venv/bin/python"
if not python.exists():
    subprocess.run([sys.executable, "-m", "venv", str(ROOT / ".venv")], check=True)
subprocess.run(
    [str(python), "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")],
    check=True,
)
subprocess.run([str(python), str(ROOT / "scripts/build.py")], check=True)
print("Ready. Run .venv/bin/python ground/server.py; open http://127.0.0.1:8080")

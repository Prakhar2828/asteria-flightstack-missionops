#!/usr/bin/env python3
"""Run the local FastAPI/WebSocket gateway; no paid services required."""

import argparse
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from ground.core import ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--backend", choices=["auto", "fprime", "portable"], default="auto"
    )
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument(
        "--database",
        default=os.getenv("ASTERIA_DATABASE_URL", str(ROOT / "data/missions.sqlite3")),
    )
    args = parser.parse_args()
    bridges = list(
        (ROOT / "integrations/fprime/build-fprime-automatic-native/bin").glob(
            "*/AsteriaBridge"
        )
    )
    if args.backend == "fprime" and len(bridges) != 1:
        raise SystemExit(
            "Build the pinned framework first: python scripts/setup_fprime.py"
        )
    if args.backend != "portable" and len(bridges) == 1:
        os.environ["ASTERIA_FLIGHT_EXECUTABLE"] = str(bridges[0])
    elif args.backend == "portable":
        os.environ.pop("ASTERIA_FLIGHT_EXECUTABLE", None)
    if not (ROOT / "build/flight").exists():
        from scripts.build import build

        build()
    try:
        import uvicorn
        from ground.api import create_app
    except ImportError as exc:
        raise SystemExit(
            "Install the pinned free dependencies: python -m pip install -r requirements.txt"
        ) from exc
    uvicorn.run(
        create_app(args.database),
        host="127.0.0.1",
        port=args.port,
        ws_max_size=8192,
        log_level="warning",
    )


if __name__ == "__main__":
    main()

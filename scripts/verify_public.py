#!/usr/bin/env python3
"""Make native parity fixtures and run the browser adapter under Node, without browser automation."""

import argparse, json, pathlib, subprocess, sys, os

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ground.core import FlightProcess, guard, COMMANDS


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", default="node")
    args = parser.parse_args()
    commands = [["BOOT", 0], ["POINT", 20], ["STEP", 100], ["PAYLOAD_ON", 0]]
    for f in range(6):
        commands += [
            ["INJECT_FAULT", f],
            ["STEP", 40],
            ["CLEAR_FAULTS", 0],
            ["STEP", 3600],
            ["DESATURATE", 0],
            ["RECOVER", 0],
            ["RESUME", 0],
        ]
    commands += [
        ["BOOT", 1],
        ["POINT", 181],
        ["STEP", 0.5],
        ["INJECT_FAULT", 6],
        ["UNKNOWN", 0],
    ]
    frames = []
    states = []
    for seed in [0, 42, 4294967295]:
        flight = FlightProcess(seed, ROOT / "build/flight")
        try:
            rows = []
            for cmd, value in commands:
                state = flight.exchange(cmd, value)
                rows.append(state)
                if seed == 42:
                    states.append(state)
            frames.append({"seed": seed, "commands": commands, "expected": rows})
        finally:
            flight.close()
    guards = []
    for state in states[::5]:
        for role in ["observer", "operator", "administrator"]:
            for cmd in COMMANDS:
                for value in [0, 1, 181]:
                    guards.append(
                        {
                            "role": role,
                            "command": cmd,
                            "value": value,
                            "state": state,
                            "expected": guard(role, cmd, value, state),
                        }
                    )
    (ROOT / "build/public-fixtures.json").write_text(
        json.dumps({"frames": frames, "guards": guards})
    )
    subprocess.run(
        [args.node, str(ROOT / "tests/public-runtime.mjs")], check=True, cwd=ROOT
    )


if __name__ == "__main__":
    main()

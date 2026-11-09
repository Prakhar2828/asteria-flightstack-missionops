#!/usr/bin/env python3
"""Compare generated F Prime command dispatch against the independent portable executable."""

import hashlib, json, pathlib, platform, subprocess, sys, time, signal, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ground.core import FlightProcess


def main():
    candidates = list(
        (ROOT / "integrations/fprime/build-fprime-automatic-native/bin").glob(
            "*/AsteriaBridge"
        )
    )
    if len(candidates) != 1:
        raise SystemExit("Build F Prime first with scripts/setup_fprime.py")
    commands = [
        ("SNAPSHOT", 0),
        ("BOOT", 0),
        ("POINT", 12),
        ("STEP", 30),
        ("PAYLOAD_ON", 0),
    ]
    for fault in range(6):
        commands.extend(
            [
                ("INJECT_FAULT", fault),
                ("STEP", 40),
                ("CLEAR_FAULTS", 0),
                ("STEP", 600),
                ("DESATURATE", 0),
                ("RECOVER", 0),
                ("RESUME", 0),
            ]
        )
    commands.extend(
        [
            ("HEATER_ON", 0),
            ("HEATER_OFF", 0),
            ("ADCS_OFF", 0),
            ("ADCS_ON", 0),
            ("SAFE", 0),
            ("RECOVER", 0),
            ("RESUME", 0),
            ("PAYLOAD_OFF", 0),
            ("UNKNOWN", 0),
            ("BOOT", 1),
        ]
    )
    results = []
    for seed in [0, 42, 4294967295]:
        a = FlightProcess(seed, ROOT / "build/flight")
        b = FlightProcess(seed, candidates[0])
        frames = []
        try:
            for command, value in commands:
                left = a.exchange(command, value)
                right = b.exchange(command, value)
                assert left == right, (seed, command, left, right)
                frames.append(right)
        finally:
            a.close()
            b.close()
        results.append(
            {
                "seed": seed,
                "frames_compared": len(frames),
                "sha256": hashlib.sha256(
                    json.dumps(frames, sort_keys=True).encode()
                ).hexdigest(),
            }
        )
    invalid = "BOOT 0\n\nBOOT\nBOOT 0 extra\n" + "X" * 300 + "\nSNAPSHOT 0\n"
    portable = subprocess.check_output(
        [str(ROOT / "build/flight")], input=invalid, text=True
    )
    framework = subprocess.check_output([str(candidates[0])], input=invalid, text=True)
    assert (
        portable == framework
    ), "Invalid frame responses must preserve the protocol snapshot"
    typed = json.loads(
        subprocess.check_output(
            [str(candidates[0].with_name("AsteriaVerification"))], text=True
        )
    )
    with tempfile.TemporaryDirectory() as temp:
        process = subprocess.Popen(
            [str(candidates[0].with_name("AsteriaDeployment"))],
            cwd=temp,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        time.sleep(5)
        process.send_signal(signal.SIGINT)
        try:
            log = process.communicate(timeout=10)[0]
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise AssertionError("Deployment did not stop")
        assert process.returncode == 0
        final = json.loads(
            next(
                line.removeprefix("ASTERIA_FINAL ")
                for line in log.splitlines()
                if line.startswith("ASTERIA_FINAL ")
            )
        )
        assert 3 <= final["telemetry"]["ticks"] <= 7, final
        (ROOT / "evidence/fprime-deployment-log.txt").write_text(log)
    report = {
        "invalid_frame_parity": True,
        "typed_port_harness": typed,
        "real_scheduler_ticks_in_five_seconds": final["telemetry"]["ticks"],
        "framework": "F Prime v4.4.2",
        "framework_commit": "f22ce8f2f2943e641d454e9daa7f129e6c878d32",
        "platform": platform.platform(),
        "passed": True,
        "runs": results,
        "scope": "Generated typed command dispatch parity, all six faults; standalone bridge, not the TCP ground link.",
    }
    (ROOT / "evidence/fprime.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

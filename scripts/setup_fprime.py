#!/usr/bin/env python3
"""Reproduce the pinned official F Prime build; no global Python modifications."""

import argparse, pathlib, subprocess, sys, os

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMMIT = "f22ce8f2f2943e641d454e9daa7f129e6c878d32"


def run(*args, **kwargs):
    subprocess.run(args, check=True, **kwargs)


def main():
    if sys.version_info < (3, 11):
        raise SystemExit("Use Python 3.11 or later.")
    project = ROOT / "integrations/fprime"
    framework = project / "lib/fprime"
    framework.parent.mkdir(parents=True, exist_ok=True)
    if not framework.exists():
        run(
            "git",
            "clone",
            "--branch",
            "v4.4.2",
            "--depth",
            "1",
            "https://github.com/nasa/fprime.git",
            str(framework),
        )
    actual = subprocess.check_output(
        ["git", "-C", str(framework), "rev-parse", "HEAD"], text=True
    ).strip()
    if actual != COMMIT:
        raise SystemExit("Framework revision mismatch; expected " + COMMIT)
    venv = ROOT / ".venv-fprime"
    python = venv / "bin/python"
    if not python.exists():
        run(sys.executable, "-m", "venv", str(venv))
    run(
        str(python), "-m", "pip", "install", "-r", str(ROOT / "requirements-fprime.txt")
    )
    env = {**os.environ, "PATH": str(venv / "bin") + os.pathsep + os.environ["PATH"]}
    build = project / "build-fprime-automatic-native"
    run(
        str(venv / "bin/cmake"),
        "-S",
        str(project),
        "-B",
        str(build),
        "-DFPRIME_ENABLE_FRAMEWORK_UTS=OFF",
        "-DFPRIME_ENABLE_AUTOCODER_UTS=OFF",
        env=env,
    )
    run(str(venv / "bin/cmake"), "--build", str(build), "-j", "4", env=env)
    print("Built bridge, typed-port verification harness, and scheduled deployment.")


if __name__ == "__main__":
    main()

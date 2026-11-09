#!/usr/bin/env python3
"""Build the dependency-free C++ flight process; no package downloads."""

import pathlib, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def build(sanitize=False):
    compiler = shutil.which("clang++") or shutil.which("g++")
    if not compiler:
        raise SystemExit(
            "Install a C++17 compiler: Xcode Command Line Tools on macOS or g++ on Linux."
        )
    (ROOT / "build").mkdir(exist_ok=True)
    target = ROOT / "build" / ("flight-sanitized" if sanitize else "flight")
    flags = ["-std=c++17", "-Wall", "-Wextra", "-Wpedantic", "-Werror", "-g"]
    flags += (
        ["-O1", "-fsanitize=address,undefined", "-fno-omit-frame-pointer"]
        if sanitize
        else ["-O2"]
    )
    subprocess.run(
        [compiler, *flags, str(ROOT / "flight/main.cpp"), "-o", str(target)], check=True
    )
    return target


if __name__ == "__main__":
    print(build("--sanitize" in sys.argv))

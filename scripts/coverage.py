#!/usr/bin/env python3
"""Measure LLVM line/branch coverage of the C++ core using the full unittest suite."""

import json, os, pathlib, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def run():
    compiler = shutil.which("clang++")
    cov = (
        shutil.which("llvm-cov")
        or subprocess.check_output(["xcrun", "--find", "llvm-cov"], text=True).strip()
    )
    prof = (
        shutil.which("llvm-profdata")
        or subprocess.check_output(
            ["xcrun", "--find", "llvm-profdata"], text=True
        ).strip()
    )
    cache = ROOT / "build/coverage"
    cache.mkdir(parents=True, exist_ok=True)
    for path in cache.glob("*.profraw"):
        path.unlink()
    target = ROOT / "build/flight"
    backup = ROOT / "build/flight-regular"
    if target.exists():
        shutil.copy2(target, backup)
    try:
        subprocess.run(
            [
                compiler,
                "-std=c++17",
                "-g",
                "-O0",
                "-fprofile-instr-generate",
                "-fcoverage-mapping",
                str(ROOT / "flight/main.cpp"),
                "-o",
                str(target),
            ],
            check=True,
        )
        env = dict(os.environ, LLVM_PROFILE_FILE=str(cache / "run-%p.profraw"))
        tests = subprocess.run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                str(ROOT / "tests"),
                "-q",
            ],
            env=env,
            capture_output=True,
            text=True,
        )
        (ROOT / "evidence/coverage-tests.txt").write_text(tests.stdout + tests.stderr)
        if tests.returncode:
            raise RuntimeError(
                "Coverage test run failed; inspect evidence/coverage-tests.txt"
            )
        files = list(map(str, cache.glob("*.profraw")))
        subprocess.run(
            [prof, "merge", "-sparse", *files, "-o", str(cache / "merged.profdata")],
            check=True,
        )
        raw = subprocess.check_output(
            [
                cov,
                "export",
                str(target),
                "-instr-profile=" + str(cache / "merged.profdata"),
            ],
            text=True,
        )
        data = json.loads(raw)
        selected = [f for f in data["data"][0]["files"] if "/flight/" in f["filename"]]
        summary = {
            "tool": "LLVM coverage",
            "profile_files": len(files),
            "scope": "flight/main.cpp and flight/flight.hpp only; generated F Prime/runtime code excluded",
            "files": [
                {
                    "file": str(pathlib.Path(f["filename"]).relative_to(ROOT)),
                    **f["summary"],
                }
                for f in selected
            ],
        }
        (ROOT / "evidence/coverage.json").write_text(
            json.dumps(summary, indent=2) + "\n"
        )
        subprocess.run(
            [
                cov,
                "show",
                str(target),
                "-instr-profile=" + str(cache / "merged.profdata"),
                "-format=html",
                "-output-dir=" + str(ROOT / "evidence/coverage-html"),
            ],
            check=True,
        )
        print(json.dumps(summary, indent=2))
    finally:
        if backup.exists():
            shutil.copy2(backup, target)


if __name__ == "__main__":
    run()

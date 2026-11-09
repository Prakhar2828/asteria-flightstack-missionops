#!/usr/bin/env python3
"""Run tests and record exact results plus a source digest. No target becomes a result."""

import datetime, hashlib, json, pathlib, platform, subprocess, sys, time, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build import build


class EvidenceResult(unittest.TextTestResult):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.cases = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.cases.append({"id": test.id(), "status": "passed"})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.cases.append({"id": test.id(), "status": "failed"})

    def addError(self, test, err):
        super().addError(test, err)
        self.cases.append({"id": test.id(), "status": "error"})


def main():
    build()
    suite = unittest.defaultTestLoader.discover(
        str(ROOT / "tests"), pattern="test_*.py"
    )
    start = time.perf_counter()
    evidence = ROOT / "evidence"
    evidence.mkdir(exist_ok=True)
    with (evidence / "test-output.txt").open("w") as log:
        result = unittest.TextTestRunner(
            stream=log, verbosity=2, resultclass=EvidenceResult
        ).run(suite)
    files = sorted(
        p
        for folder in ["flight", "ground", "web", "tests", "scripts", "integrations"]
        for p in (ROOT / folder).rglob("*")
        if p.is_file()
        and not any(
            part in {"__pycache__", "lib"} or part.startswith("build-")
            for part in p.relative_to(ROOT).parts
        )
        and ".template." not in p.name
    )
    digest = hashlib.sha256(
        b"".join(
            str(p.relative_to(ROOT)).encode() + b"\0" + p.read_bytes() for p in files
        )
    ).hexdigest()
    data = {
        "schema": "asteria-verification-v1",
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "environment": platform.platform(),
        "python": sys.version,
        "source_sha256": digest,
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "elapsed_seconds": time.perf_counter() - start,
        "cases": result.cases,
        "scope": "Local C++ process and Python gateway unit/integration tests. UI checks recorded separately.",
    }
    (evidence / "verification.json").write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({k: v for k, v in data.items() if k != "cases"}, indent=2))
    if not result.wasSuccessful():
        print((evidence / "test-output.txt").read_text()[-14000:])
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

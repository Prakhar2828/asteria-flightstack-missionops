#!/usr/bin/env python3
"""Preserve a complete ground mission, replay it ten times, measure controlled local loads."""

import hashlib, json, os, pathlib, platform, resource, statistics, subprocess, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ground.core import Journal, Mission


def checksum(rows):
    return hashlib.sha256(
        json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def command(m, name, value=0):
    result = m.command(
        {"id": str(time.monotonic_ns()), "command": name, "value": value}
    )
    assert result["status"] == "acknowledged", result
    return result


def main():
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    started = time.perf_counter()
    with tempfile.TemporaryDirectory() as tmp:
        journal = Journal(pathlib.Path(tmp) / "mission.db")
        m = Mission(journal)
        command(m, "BOOT")
        command(m, "PAYLOAD_ON")
        for second in range(1, 1801):
            if second == 300:
                command(m, "INJECT_FAULT", 2)
            if second == 320:
                command(m, "CLEAR_FAULTS")
            if second == 335:
                command(m, "RECOVER")
                command(m, "RESUME")
            m.step(1)
        rows = journal.read(m.id)
        hashes = []
        for _ in range(10):
            replay = journal.read(m.id)
            assert replay[-1]["sim"] == 1800
            hashes.append(checksum(replay))
        requested = {r["data"]["id"] for r in rows if r["kind"] == "command_requested"}
        terminal = {r["data"]["id"] for r in rows if r["kind"] == "command_terminal"}
        assert requested == terminal and len(set(hashes)) == 1
        (ROOT / "evidence/ground-mission.jsonl").write_text(
            "".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows)
        )
        m.close()
        journal.close()
        scenarios = []
        for name, fault, wait in [
            ("nominal", None, 10),
            ("power", 0, 3600),
            ("communications", 3, 20),
            ("sensor", 2, 10),
        ]:
            j = Journal(pathlib.Path(tmp) / (name + ".db"))
            m = Mission(j)
            command(m, "BOOT")
            if fault is None:
                command(m, "PAYLOAD_ON")
                m.step(10)
                assert m.truth["telemetry"]["payload_data"] > 0
            else:
                command(m, "INJECT_FAULT", fault)
                m.step(20)
                assert m.truth["mode"] == "SAFE"
                command(m, "CLEAR_FAULTS")
                m.step(wait)
                command(m, "RECOVER")
                command(m, "RESUME")
            scenarios.append(
                {
                    "name": name,
                    "passed": m.truth["mode"] == "NOMINAL",
                    "sim_seconds": m.truth["telemetry"]["time"],
                }
            )
            (ROOT / "evidence" / ("scenario-" + name + ".json")).write_text(
                json.dumps(j.read(m.id), indent=2) + "\n"
            )
            m.close()
            j.close()
        loads = []
        for rate, count in [(1, 10), (10, 50), (100, 200)]:
            j = Journal(pathlib.Path(tmp) / ("load" + str(rate) + ".db"))
            m = Mission(j)
            command(m, "BOOT")
            samples = []
            rss = []
            start = time.monotonic()
            for i in range(count):
                time.sleep(max(0, start + i / rate - time.monotonic()))
                samples.append(command(m, "POINT", i % 180 - 90)["latency_ms"])
                if i % 10 == 0:
                    out = subprocess.check_output(
                        ["ps", "-o", "rss=", "-p", str(m.flight.proc.pid)], text=True
                    ).strip()
                    rss.append(int(out))
            elapsed = time.monotonic() - start
            m.close()
            j.close()
            loads.append(
                {
                    "target_commands_per_second": rate,
                    "commands": count,
                    "wall_seconds": elapsed,
                    "latency_ms": samples,
                    "p95_ms": sorted(samples)[int(0.95 * len(samples)) - 1],
                    "flight_rss_kib_samples": rss,
                    "max_sampled_flight_rss_kib": max(rss),
                    "acknowledged": count,
                }
            )
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    report = {
        "platform": platform.platform(),
        "backend": os.getenv("ASTERIA_FLIGHT_EXECUTABLE", "portable"),
        "replay_runs": 10,
        "replay_hashes": hashes,
        "replay_identical": True,
        "mission_seconds": 1800,
        "records": len(rows),
        "reconciled": len(requested),
        "scenarios": scenarios,
        "loads": loads,
        "child_cpu_seconds": {
            "user": after.ru_utime - before.ru_utime,
            "system": after.ru_stime - before.ru_stime,
        },
        "wall_seconds": time.perf_counter() - started,
        "scope": "Local gateway and SQLite; paced command request rates. RSS is sampled child resident memory, not exact peak. Child CPU includes ps sampling processes. Replay compares every stored row, not regenerated physics.",
    }
    (ROOT / "evidence/mission-acceptance.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print("Ten complete replays, four scenarios and three paced load profiles passed.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Verify parity against a real PostgreSQL database supplied by environment."""

import datetime, json, os, pathlib, sys, tempfile, uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ground.storage import Journal
from ground.core import Mission


def main():
    url = os.environ.get("ASTERIA_TEST_DATABASE_URL")
    if not url:
        raise SystemExit(
            "Set ASTERIA_TEST_DATABASE_URL to an isolated PostgreSQL test database."
        )
    pg = Journal(url)
    checks = []
    with tempfile.TemporaryDirectory() as tmp:
        sq = Journal(pathlib.Path(tmp) / "test.db")
        run = "parity-" + str(uuid.uuid4())
        for journal in (sq, pg):
            journal.append(run, 0, "run", {"seed": 42})
            for i in range(10):
                journal.append(
                    run, i, "telemetry", {"telemetry": {"battery_soc": 80 + i}}
                )

        def canonical(rows):
            return [{k: r[k] for k in ("sim", "kind", "data")} for r in rows]

        checks.append(
            {
                "name": "journal_read_parity",
                "passed": canonical(pg.read(run)) == canonical(sq.read(run)),
            }
        )
        checks.append(
            {
                "name": "history_parity",
                "passed": [
                    {k: v for k, v in r.items() if k != "id"}
                    for r in pg.history(run, "battery_soc", 0, 9000, 0)
                ]
                == [
                    {k: v for k, v in r.items() if k != "id"}
                    for r in sq.history(run, "battery_soc", 0, 9000, 0)
                ],
            }
        )
        other = Journal(url)
        checks.append(
            {
                "name": "reopen_durability",
                "passed": canonical(other.read(run)) == canonical(pg.read(run)),
            }
        )
        other.close()
        last = pg.last_id(run)
        checks.append(
            {"name": "cursor_excludes_prior", "passed": pg.read(run, last) == []}
        )
        m = Mission(pg)
        m.command({"id": "boot", "command": "BOOT"})
        m.command({"id": "fault", "command": "INJECT_FAULT", "value": 2})
        m.command({"id": "clear", "command": "CLEAR_FAULTS"})
        m.step(10)
        m.command({"id": "recover", "command": "RECOVER"})
        m.command({"id": "resume", "command": "RESUME"})
        checks.append(
            {
                "name": "mission_recovery_postgres",
                "passed": m.status()["state"]["mode"] == "NOMINAL",
            }
        )
        rows = pg.read(m.id)
        checks.append(
            {
                "name": "command_reconciliation_postgres",
                "passed": {
                    r["data"]["id"] for r in rows if r["kind"] == "command_requested"
                }
                == {r["data"]["id"] for r in rows if r["kind"] == "command_terminal"},
            }
        )
        m.close()
        sq.close()
    pg.close()
    report = {
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "database": "PostgreSQL 17 local test instance",
        "checks": checks,
    }
    (ROOT / "evidence/postgresql.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if all(c["passed"] for c in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())

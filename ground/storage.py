"""Equivalent append-only journals for SQLite and PostgreSQL.
All reads are parameterized. Migration version 1 is idempotent.
"""

import json
import sqlite3
import threading
import time


class Journal:
    def __init__(self, path):
        self.lock = threading.RLock()
        self.backend = (
            "postgresql"
            if str(path).startswith(("postgresql://", "postgres://"))
            else "sqlite"
        )
        if self.backend == "postgresql":
            import psycopg

            self.db = psycopg.connect(str(path), autocommit=True)
            self.db.execute(
                "CREATE TABLE IF NOT EXISTS records (id BIGSERIAL PRIMARY KEY, run TEXT NOT NULL, sim DOUBLE PRECISION NOT NULL, wall DOUBLE PRECISION NOT NULL, kind TEXT NOT NULL, data TEXT NOT NULL)"
            )
        else:
            self.db = sqlite3.connect(str(path), check_same_thread=False)
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute(
                "CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY, run TEXT NOT NULL, sim REAL NOT NULL, wall REAL NOT NULL, kind TEXT NOT NULL, data TEXT NOT NULL)"
            )
        self.db.execute("CREATE INDEX IF NOT EXISTS run_idx ON records(run,id)")
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)"
        )
        self.db.execute(
            "INSERT INTO schema_version(version) VALUES(1) ON CONFLICT DO NOTHING"
        )
        if self.backend == "sqlite":
            self.db.commit()

    def execute(self, sql, params=()):
        return self.db.execute(
            sql.replace("?", "%s") if self.backend == "postgresql" else sql, params
        )

    def append(self, run, sim, kind, data):
        raw = json.dumps(data, separators=(",", ":"), allow_nan=False)
        with self.lock:
            self.execute(
                "INSERT INTO records(run,sim,wall,kind,data) VALUES(?,?,?,?,?)",
                (run, sim, time.time(), kind, raw),
            )
            if self.backend == "sqlite":
                self.db.commit()

    def read(self, run, after=0, limit=100000):
        with self.lock:
            rows = self.execute(
                "SELECT id,sim,wall,kind,data FROM records WHERE run=? AND id>? ORDER BY id LIMIT ?",
                (run, after, limit),
            ).fetchall()
        return [
            dict(id=r[0], sim=r[1], wall=r[2], kind=r[3], data=json.loads(r[4]))
            for r in rows
        ]

    def last_id(self, run):
        with self.lock:
            return self.execute(
                "SELECT COALESCE(MAX(id),0) FROM records WHERE run=?", (run,)
            ).fetchone()[0]

    def history(self, run, channel, start, end, epoch):
        with self.lock:
            rows = self.execute(
                "SELECT id,sim,data FROM records WHERE run=? AND kind='telemetry' AND sim>=? AND sim<=? ORDER BY id LIMIT 50000",
                (run, (start - epoch) / 1000, (end - epoch) / 1000),
            ).fetchall()
        return [
            {
                "timestamp": epoch + r[1] * 1000,
                "value": json.loads(r[2])["telemetry"][channel],
                "id": r[0],
                "quality": "RECEIVED",
            }
            for r in rows
        ]

    def close(self):
        self.db.close()

# MissionOps Digital Twin

The ground half of the Asteria laboratory. `core.py` owns the local flight process gateway, independent command guards, immutable journal inserts, session state, and executable procedures. `server.py` exposes a loopback-only HTTP interface and advances running simulations.

Run from the repository root: `python3 ground/server.py`. The server builds FlightStack if no binary exists; use `python3 scripts/build.py` after source changes. The **MissionOps**, **Replay & debrief**, and overview workspaces are its interactive front end.

SQLite files live in `data/` and are excluded from Git. Journal writes are append-only through the application, but the database is not tamper-proof. Role selection is a training feature: any local visitor can start an administrator session. Do not interpret this as production authentication.

A single integrated repository is recommended for the initial public release: both halves share one interface version, test suite, and evidence package. They remain distinct portfolio projects; do not double-count shared channels or commands.

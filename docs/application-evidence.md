# Application evidence and ownership

Use measured claims from `technical-report.md`, not the original proposal's targets. The 26 shared channels and 12 operational commands belong to one connected spacecraft; do not double-count them across projects.

Suitable project descriptions after reviewing and reproducing the work:

- **Asteria FlightStack:** Developed an AI-assisted C++17 spacecraft software testbed with five simplified subsystem models, four operating modes and six injected fault classes; integrated a typed NASA F Prime component and scheduled deployment, with command-dispatch parity tests and instrumented core coverage.
- **MissionOps:** Built a local FastAPI/Open MCT operations environment with WebSocket telemetry, six subsystem workspaces, independent command guards, executable recovery procedures, SQLite/PostgreSQL audit storage and deterministic recorded-mission replay.

Attach the measured test count, p95 latency and coverage denominator only from the current report. Explain that gateway, browser and simulated-time measurements cover different intervals. The evidence folder contains raw traces and scripts so a reviewer can reproduce the results.

Do not claim eight custom F Prime components, flight qualification, RTOS/HIL testing, production identity, real spacecraft data, verified TCP/CCSDS transport, Linux CI success, public hosting or NASA endorsement. The delivered architecture uses one custom framework component around five subsystem models, with separate upstream framework services.

Before applying, be prepared to explain the power balance, single-axis controller, thermal relaxation, mode transition table, delayed communication-loss protection, recovery dwell, command ID deduplication, stale telemetry handling and why a cleared fault does not reset physical state. Make an independent change and review the implementation yourself; AI-assisted implementation does not substitute for personal understanding.

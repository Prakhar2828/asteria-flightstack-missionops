# Scope and master-spec gap ledger

The supplied master reference is a proposed architecture, not evidence of preexisting implementation. Release 0.1 implements a useful local engineering prototype, but **does not satisfy the entire master reference**. This ledger intentionally preserves that distinction.

| Master item | Release 0.1 | Status |
|---|---|---|
| Modular C++ flight software | Five subsystem state types, mode/FDIR logic, logical scheduler, local process | Implemented and tested; custom framework |
| NASA F Prime deployment | No F Prime dependency, generated ports, topology or deployment | Not implemented |
| F Prime test harness / GoogleTest | Python unittest drives the compiled process | Substituted, not equivalent framework experience |
| Five subsystems | Simplified EPS, single-axis ADCS, COMMS, thermal, payload | Implemented, limited physical fidelity |
| Four modes / six faults | Guards, SAFE entry, recovery dwell and containment | Implemented and tested |
| 20+ channels / 12 commands | 26 shared channels, 12 flight commands + 2 lab controls | Implemented; count once across projects |
| Forty requirements | Forty scoped prototype requirements mapped to tests | Implemented baseline; not the original full acceptance envelope |
| 80 flight / 50 ground tests | Actual case counts in verification report | Measured; do not infer original gates complete |
| Actual real-time scheduling / watchdog | 1 s logical scheduler and injected stall counter | Real-time/RTOS behavior not implemented |
| Network spacecraft transport, sequence framing | Ordered child-process pipe + ground command IDs | TCP/UDP flight transport and CRC not implemented |
| Open MCT console | Custom HTML/CSS/JavaScript console | Open MCT not implemented |
| FastAPI/Pydantic/WebSockets | Standard-library HTTP server and explicit validation; polling | Frameworks and streaming transport not implemented |
| PostgreSQL/TimescaleDB | SQLite WAL journal | Substituted single-host persistence |
| Six dashboards | Telemetry filters for six groups plus specialized workspaces | Full six dedicated operations dashboards not implemented |
| Ten flight rules / six procedures | Independent guards and executable steps | Implemented; thermal/power procedures require admin lab clearing |
| Four scenarios | Nominal, power, COMMS, sensor paths | Core and HTTP flows tested; UI acceptance blocked |
| Three roles | Per-session training roles with gateway enforcement | Production identity, accounts, access delegation not implemented |
| Acknowledgments, failure, timeout | Synchronous process exchange and terminal records | Implemented; timeout path injected in tests |
| Stored telemetry and replay | SQLite + read-only UI journal playback | Implemented; UI not visually verified |
| 30-minute mission / 20 repeat runs | Stored 1,800 s trace and hash comparison | Measured locally |
| Ten repeated ground mission replays | Not separately benchmarked | Open |
| CPU/RAM/coverage/deadline profiling | Not instrumented | Open; no coverage percentage claimed |
| Browser display latency | Not measured | Open |
| Alert-to-display timing | Logical checks, no browser timing evidence | Open |
| CI on Linux/macOS | Workflow prepared, local macOS tests run | Hosted CI not run; Linux results unknown |
| Public repositories / hosting | Source and manual instructions only | Not published, per user request |
| Demo video / screenshots | Text walkthrough | Recording and visual verification open |
| Physical HIL / flight certification | None | Excluded from this zero-hardware prototype |
| A2 MissionLab linkage | No project URL/artifacts supplied | Not implemented |

## Fidelity and safety limits

The 3U label identifies an intended educational spacecraft class, not a mechanical model or calibrated digital twin. The simplified physics cannot support engineering design decisions about real spacecraft. Orbit drawings are illustrative, the ADCS model is single-axis, temperature is lumped, and EPS has no battery chemistry. No real missions, restricted procedures, private telemetry, or proprietary code are used.

The code needs independent human review before serious reuse. Passing the included tests means only the enumerated cases passed in the reported environment. It does not prove correctness, security, safety, full requirement coverage, production readiness, or qualification.

## Next substantive engineering gates

1. **F Prime integration:** install official tooling locally; define typed command, telemetry and event ports; wrap subsystem algorithms as real components; add topology and rate groups; prove independent framework build and tests.
2. **Open MCT integration:** implement dictionary, real-time and historical providers against this ICD; verify quality and reconnect behavior in browser tests. Keep actual onboard authority in C++.
3. **Service architecture:** FastAPI schema models, WebSocket stream, migrations and PostgreSQL backend, bounded retention/backpressure, schema compatibility tests and authentication if public deployment is desired.
4. **V&V release:** actual coverage instrumentation, load curves, CPU/RAM measurements, deadline analysis, Linux build, browser automation, accessible/mobile visual checks and a recorded walkthrough.
5. **Portfolio ownership:** review design decisions, change the implementation yourself, document defects found and fixed, and be ready to explain the model equations and tradeoffs.

These are remaining implementation tasks, not accomplishments to put on a resume.

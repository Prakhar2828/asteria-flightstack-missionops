# Local software release boundary

The master reference is a proposal containing targets, not an assertion that every suggested extension is required or achieved. This release implements the connected local software laboratory. Evidence and exact denominators are in the technical report.

| Area | Delivered implementation | Deliberate boundary |
|---|---|---|
| Flight architecture | Five C++ subsystem models; mode, FDIR and logical scheduling; one custom F Prime FlightComputer component | The proposed eight custom framework components were consolidated to preserve a single authoritative model; framework rate groups and services remain separate components |
| F Prime | Pinned v4.4.2 build; 16 typed commands including lab/transport controls; 27 framework channels including mode; typed-port harness and scheduled deployment | Shared public dictionary has 26 channels and 12 operational commands; do not double-count framework controls |
| Transport | Bounded newline frames over a local child-process pipe; generated F Prime command dispatch; IDs and terminal acknowledgments in ground audit | Operational console uses the bridge, not the separate deployment's TCP/CCSDS link; no RF, CRC-link validation or orbital latency claim |
| Console | Six subsystem workspaces plus real Open MCT object, live and historical providers | Simplified software model; not a calibrated spacecraft digital twin |
| Ground | FastAPI, strict Pydantic schemas, WebSockets, SQLite and PostgreSQL | Local training personas, not enterprise authentication |
| Operations | Ten guards, six procedures, four scenario paths, command audit and after-action reports | Administrative injection/clearing is a lab facility, explicitly outside the simulated uplink |
| Replay | Complete journal export, telemetry scrubbing, preserved 30-minute trace and ten repeated journal reads | Reconstruction of stored observations, not restart of a physical spacecraft |
| Verification | Automated tests, requirements mapping, sanitizers, LLVM core coverage, F Prime harness, controlled load and resource profiles, browser observations | Self-verification on local macOS; no independent assurance, hardware timing or flight qualification |
| Distribution | Local full stack plus GitHub Pages browser delivery workflow | Public demo runs C++ WebAssembly and browser operations; it does not host F Prime, FastAPI or PostgreSQL |

Physical HIL, RTOS watchdog behavior, multi-axis GNC, radiation effects, hardware power/thermal calibration, A2 MissionLab coupling, production accounts and public backend hosting are outside this release. They must not appear as completed application claims. No code or testing can guarantee an interview or job offer.

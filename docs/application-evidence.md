# Application evidence and ownership

This is an AI-assisted initial implementation. Do not present AI-generated work as unassisted personal authorship. Before applying, build and run it yourself, inspect and understand the source, make substantive changes, and record your own decisions and verification. A project can support an interview only if you can explain and defend it.

## Verified repository facts

- C++17 simulated spacecraft process with five subsystem models, four operating modes, six injected fault categories, 26 shared telemetry channels, and 12 flight commands.
- Independent Python ground guards, three training roles, six executable procedures, SQLite journal storage, and an interactive local console with replay and exports.
- Actual automated test results, HTTP checks, sanitizer outputs and repeatability measurements are in `evidence/`; use the current technical report for counts and exact values.
- Forty scoped prototype requirements have referenced automated test cases. This is not completion of the original full master specification.

## Safe draft language after independent review and substantive contribution

Adapt these only to the work you actually own:

- “Developed and evaluated a C++ spacecraft simulation with autonomous SAFE-mode protection, guarded recovery, and deterministic fault-injection scenarios across power, thermal, sensor, communication, watchdog, and actuator faults.”
- “Built a local mission-operations console with independently validated commands, acknowledgment auditing, SQLite event history, executable recovery procedures, and read-only mission replay.”
- “Validated [actual test count] enumerated cases and compared 20 same-seed 30-minute simulation traces, preserving raw results and requirements-to-test mappings.”

Do not describe these as F Prime/Open MCT projects, production authentication, a calibrated spacecraft digital twin, real-time flight software, hardware-in-the-loop, CCSDS-compliant software, full coverage, actual flight operations, NASA systems, or flight-certified code. Those facts are not established.

## Evidence audit

| Claim | Artifact | Status |
|---|---|---|
| C++ simulator and five subsystem state types | `flight/flight.hpp`, passing flight tests | Verified local prototype |
| Fault protection / recovery | `test_flight` fault and recovery cases | Verified enumerated cases |
| Role enforcement / command IDs | `test_ground` permission and idempotency cases | Verified training-session behavior |
| Local interactive console source | `web/`, HTTP asset checks, JS syntax check | Implemented; browser behavior/visual QA unverified |
| Journal durability | Journal round-trip / reopened connection tests | Verified local SQLite scope |
| Repeatability | `benchmark.json`, raw trace | Verified same host / seed / scenario |
| Measured latency | Raw latency samples | Local process gateway only |
| CI / Linux / public demo | No hosted execution or publication | Not verified |
| F Prime / Open MCT | No implementation | Not eligible |

Local performance numbers are hardware-dependent and often less useful on a resume than the engineering method. Never substitute design targets for actual results. Keep shared channels and commands counted once across the two projects.

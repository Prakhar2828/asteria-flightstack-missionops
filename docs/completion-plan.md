# Completion acceptance baseline

The master reference defines the target. Mandatory software gates remain open until code and observed evidence support them. Optional physical hardware and A2 MissionLab linkage are excluded unless those resources are supplied. No claims of flight qualification, real-time certification or guaranteed hiring outcomes are part of completion.

1. Build and exercise a real F Prime component/deployment, with typed commands, telemetry and events, against the shared spacecraft algorithms.
2. Integrate Open MCT telemetry objects with live and historical providers; preserve the custom operations controls.
3. Provide FastAPI/Pydantic schemas, WebSocket telemetry, persistent storage and PostgreSQL deployment support with tested adapters.
4. Provide six usable subsystem views, ten documented flight rules, six guarded procedures, role enforcement and four end-to-end scenarios.
5. Make framing, sequence identity, bounds, acknowledgments, disconnections, failures and duplicate behavior explicit and tested.
6. Preserve 30-minute traces, repeat deterministic onboard runs 20 times and ground replay 10 times, and retain raw evidence.
7. Measure local command timing, CPU/memory, instrumented source coverage, scheduling observations and UI display timing with exact scopes.
8. Complete browser workflow/visual verification and release evidence. Any environment blocker remains unverified, never silently waived.
9. Provide reproducible dependency versions, local setup, CI, architecture, ICD, requirement traceability, demo instructions and accurate application claims.
10. Keep GitHub publication manual, consistent with the user's instruction. Changes are developed in an isolated local checkout and handed back to the user's repository after verification.

## Observed release disposition

The local software gates have corresponding evidence in `technical-report.md`: framework build/parity/typed-port/scheduling, Open MCT browser observations, PostgreSQL parity, six dashboard views, 60 scoped requirement mappings, 20 deterministic flight runs, 10 complete journal replays, four scenario traces, resource profiles, instrumented core coverage and browser timing. The original eight-custom-component proposal is intentionally revised to one F Prime wrapper around five subsystem models; rationale is in architecture.md. The local pipe boundary is explicit and does not claim a verified radio or TCP/CCSDS link.

Publication remains manual. Hosted CI, physical HIL, A2 linkage and production/public hosting are outside this local acceptance boundary. They are not silently counted as completed checks.

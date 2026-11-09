# MissionOps Digital Twin

The local FastAPI service connects an isolated spacecraft process to an operations console and NASA Open MCT. Start through `run.command` at repository root. See the root README for setup and backend selection.

`api.py` owns HTTP/WebSocket boundaries and schemas. `runtime.py` owns session limits and monotonic scheduling. `core.py` owns command lifecycle, independent ground guards, six procedures and audit reconciliation. `storage.py` implements SQLite/PostgreSQL journal parity.

Three roles are selectable training personas. Observer mutation attempts are rejected at the server. Command IDs suppress duplicate execution within a live run, and every accepted request is associated with a terminal result or explicit transport failure. No browser control can directly edit authoritative spacecraft state.

The six subsystem workspaces and Open MCT live/history adapter consume the same 26-channel dictionary. Exported journals preserve commands, telemetry, procedures and operator actions; replay is read-only. All runtime assets are local. This service is intended for loopback use, with production account management and public deployment outside its scope.

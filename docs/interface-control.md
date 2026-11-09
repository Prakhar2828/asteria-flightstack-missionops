# Interface control document — protocol v1

## Flight process

Launch `build/flight SEED`, where SEED is an unsigned 32-bit decimal integer. Default 42; a zero seed is recorded as zero but uses RNG state one to avoid xorshift's all-zero state.

Input is newline-delimited ASCII: `COMMAND VALUE\n`. Maximum frame length 256 characters. Command names contain uppercase letters and underscores, at most 32 characters; value is finite numeric text. Every command includes a value, even when it is zero. One response JSON object is emitted per parsed frame and flushed immediately. The process is single-threaded.

Response fields:

| Field | Type | Meaning |
|---|---|---|
| `protocol_version` | integer | Always 1; gateway rejects mismatches |
| `ok` | boolean | Onboard acceptance, not browser delivery |
| `reason` | string enum | ACKNOWLEDGED, TELEMETRY, STEPPED, or rejection reason |
| `mode` | enum | BOOT / NOMINAL / SAFE / RECOVERY |
| `seed` | uint32 | Run seed |
| `telemetry` | object | See `telemetry-dictionary.json`; 26 channels |
| `faults` | six booleans | Power, thermal, sensor, COMMS, watchdog, wheel |
| `events` | array | Latest 256 onboard events; simulated time, code, severity |

12 flight commands: BOOT, SAFE, RECOVER, RESUME, PAYLOAD_ON, PAYLOAD_OFF, HEATER_ON, HEATER_OFF, ADCS_ON, ADCS_OFF, POINT, DESATURATE. POINT takes degrees in [-180,180]; other flight commands take zero. Lab controls: INJECT_FAULT (integer 0–5), CLEAR_FAULTS (zero). Gateway-only transport helpers: STEP (integer 1–3600), SNAPSHOT (zero).

The local pipe is ordered and synchronous. It has no wire sequence numbers or CRC. HTTP command IDs and journal IDs provide ground-side identity, not CCSDS compliance. Parser failures do not execute commands. Process failures produce failed/timed-out terminal outcomes in the ground journal.

## HTTP interface

The server listens on `127.0.0.1:8080` by default. Requests must use a matching localhost/127.0.0.1 Host header; cross-origin mutations are rejected. CORS is not enabled. All POST bodies are JSON objects, capped at 8192 bytes. NaN and Infinity are rejected.

| Method/path | Input | Output |
|---|---|---|
| GET `/api/catalog` | none | Channel, command, rule and procedure dictionaries |
| POST `/api/session` | `{role, seed}` | Opaque token and initial mission status |
| GET `/api/status` | bearer token | Last received telemetry, quality, age, alarms, procedure state |
| POST `/api/command` | `{id, command, value}` | Terminal command result and local latency |
| POST `/api/control` | `{action, value?}` | run, pause, speed (1/10/60), or step (1–3600 s) |
| POST `/api/procedure` | `{key}` or `{action:"advance"}` | Procedure progress; rejected steps stay pending |
| GET `/api/records?after=N` | bearer token | Journal records after an absolute journal ID |
| GET `/api/export` | bearer token | `asteria-journal-v1` JSON |
| POST `/api/close` | `{}` | Closes session and child process; keeps journal |

All session endpoints require `Authorization: Bearer TOKEN`. The token grants access only to that session; role is fixed server-side when the session is created. New sessions intentionally allow any training role on localhost. This is not user identity verification.

Command IDs: 1–80 alphanumeric, hyphen or underscore characters. A repeated ID with identical command/parameter returns the prior outcome with `duplicate:true`, without another execution. Reusing an ID for different content rejects with FR-03_ID_CONFLICT. Up to 10,000 unique command IDs per run. Malformed IDs are rejected before lifecycle logging. Observer commands with valid IDs are logged as rejected.

Lifecycle: `command_requested` → either `command_terminal(rejected)` or `command_transmitted` → `command_terminal(acknowledged/rejected/timed-out/failed)`. Onboard acceptance and physical procedure completion are separate concepts. Internal command status uses HTTP 200 for evaluated command rejections so the body can carry the terminal outcome. HTTP 400/401/403/413/415/503 represent request/session/service failures.

## Time, quality, replay and limits

Simulation time is a monotonically increasing integer count of logical seconds from zero. Wall timestamps in journal rows are Unix epoch seconds from Python `time.time()`. Latency uses monotonic `time.perf_counter()`. No browser-to-flight clock synchronization is claimed.

Downlink age = current simulated time − last successfully received telemetry time. During link loss, last received values remain unchanged; quality is DISCONNECTED before 3 s and STALE at/after 3 s. This local lab knows simulation elapsed time even without downlink; it does not know current remote telemetry. Link restoration records a fresh snapshot. Quality is exposed by the gateway, not redundantly stored per channel in the C++ frame.

The HTTP journal endpoint currently caps one response at 100,000 rows. `/api/records` supports cursor pagination. Very long mission exports must be paginated by a client; the UI is designed for short demonstration sessions. No automatic disk retention policy is implemented. The full journal persists on disk until the user removes it; normal UI history and event lists are bounded separately.

Replay is journal playback, not a new physical simulation. The benchmark independently re-executes a deterministic scenario and compares complete trace hashes. Gaps in received telemetry are not filled with invented samples. Replay chart gaps larger than 60 s are disconnected; smaller gaps are linearly drawn for visual continuity.

## Framework and streaming extension

`GET /api/health` identifies `fprime` or `portable` and the database backend. The F Prime bridge decodes generated command arguments before applying the shared model. It is a local process transport, not a claim that the separate scheduled deployment's TCP or CCSDS uplink has been verified.

`WS /api/stream` requires a first JSON message `{ "token": "<session token>" }` within five seconds. The token is never placed in a URL. Each envelope includes increasing connection-local `sequence`, `sent_at_ms` (host wall-clock milliseconds) and `status`. Each connection starts its own sequence. The server sends current state every 250 ms and closes clients that cannot accept a send within two seconds. Reconnect gets a current snapshot; the durable HTTP journal is the source for missed historical records.

`status.epoch_ms + telemetry.time * 1000` projects simulation time onto a UTC axis. `status.received_at_ms` records host receipt of the latest available flight snapshot. It is used for same-host browser timing; it is not a spacecraft clock or radio timestamp. A repeated WebSocket snapshot does not create a new telemetry receipt.

`GET /api/history/{channel}?start=<epoch ms>&end=<epoch ms>` returns stored telemetry points for the authenticated run, bounded to 50,000 rows. `GET /api/records?after=<record id>&limit=<count>` supports bounded pagination. Export freezes the current upper record ID and streams all records up to that boundary. SQLite and PostgreSQL implement equivalent journal semantics; schema version 1 is created idempotently.

FastAPI rejects extra fields, invalid roles, nonfinite parameters, malformed bodies and bodies above 8 KiB. All endpoints enforce loopback host and same-origin browser requests. OpenAPI schema is available at `/openapi.json`; interactive API documentation at `/docs`. Training role authorization is server-side within the selected session, not a production identity system.

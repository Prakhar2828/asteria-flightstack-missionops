# Asteria FlightStack & MissionOps

**[Launch the free interactive demo](https://prakhar2828.github.io/asteria-flightstack-missionops/)** · [Source](https://github.com/Prakhar2828/asteria-flightstack-missionops)

Explore FlightStack and MissionOps without installation or signup. The public demo runs the same C++ spacecraft model as WebAssembly in your browser, with isolated missions, fault injection, guarded commands, procedures, replay and NASA Open MCT. The full F Prime/Python/database implementation runs locally. See [public delivery](docs/public-delivery.md) for the precise boundary.

A local spacecraft software laboratory: command a simulated CubeSat, inject a fault, observe autonomous protection, execute guarded recovery, and reconstruct the mission from its audit record.

Two connected portfolio projects share one spacecraft model and interface:

- **FlightStack:** C++17 subsystem models, mode management and fault protection, integrated with a real NASA F Prime component, typed command/telemetry ports and scheduled deployment.
- **MissionOps:** FastAPI/Pydantic gateway, WebSocket telemetry, NASA Open MCT live/history views, six subsystem dashboards, ten flight rules, six executable procedures, three training roles, SQLite/PostgreSQL journals, replay and debrief exports.

All data is synthetic. The model is educational, with a single attitude axis, lumped thermal behavior and simplified power dynamics. This is independent software, not flight-qualified software or a NASA-endorsed product.

## Run locally

Requires macOS or Linux, Python 3.11+, a C++17 compiler and Git. Dependency installation needs an Internet connection once. Runtime uses local assets and requires no account, API key or paid service.

```sh
python3.11 scripts/setup.py
.venv/bin/python scripts/setup_fprime.py
./run.command
```

Open **http://127.0.0.1:8080**. Initialize a mission, choose **First light**, execute its three steps, and run the clock. Open **NASA Open MCT** from the same tab to browse live and historical telemetry.

The launcher selects the built F Prime bridge automatically. `./run.command --backend portable` selects the standalone C++ model; `--backend fprime` requires the framework build. `/api/health` reports the active backend. The first F Prime build downloads its pinned official source and tools and can take several minutes.

SQLite works without configuration. To use an existing local PostgreSQL database:

```sh
export ASTERIA_DATABASE_URL='postgresql://USER:PASSWORD@localhost:5432/asteria'
./run.command --backend fprime
```

Keep credentials in your environment. The server listens on loopback. Training personas are intentionally selectable; they are not production user accounts. The public browser demo uses isolated tab-local missions; this backend remains local.

## Try the engineering workflows

1. Commission the spacecraft and collect payload data.
2. Inject undervoltage in FlightStack. Inspect SAFE mode, alerts and payload shedding.
3. Clear the fault source, advance time until the battery and health gates recover, then execute RECOVER and RESUME.
4. Inject communication loss. Observe telemetry quality become stale while onboard protection continues independently.
5. Compare live/history plots in Open MCT, scrub recorded telemetry in Replay, and export the journal and after-action report.

[Detailed walkthrough](docs/demo-script.md) · [architecture](docs/architecture.md) · [interface contract](docs/interface-control.md) · [verification report](docs/technical-report.md) · [scope decisions](docs/scope-and-gaps.md)

## Reproduce verification

```sh
.venv/bin/python scripts/verify.py
.venv/bin/python scripts/traceability.py
.venv/bin/python scripts/verify_fprime.py
.venv/bin/python scripts/build.py --sanitize
.venv/bin/python scripts/sanitize.py
.venv/bin/python scripts/benchmark.py
.venv/bin/python scripts/mission_acceptance.py
.venv/bin/python scripts/profile_runtime.py
.venv/bin/python scripts/coverage.py
# With the local server running:
.venv/bin/python scripts/http_smoke.py
```

Set `ASTERIA_FLIGHT_EXECUTABLE` to the built `AsteriaBridge` when running benchmark scripts against F Prime. Tests default to the portable model unless explicitly configured. Framework parity and typed-port tests run separately. Raw reports, traces, coverage and screenshots live in `evidence/`; recorded results describe one local macOS environment. GitHub Actions runs native verification and publishes the browser demo on pushes to main; consult the repository Actions page for current results.

## Explore the source

| Directory | Responsibility |
|---|---|
| `flight/` | Independent spacecraft model and bounded process protocol |
| `integrations/fprime/` | FPP interfaces, C++ wrapper, scheduled deployment and typed-port verification |
| `ground/` | Schemas, sessions, command lifecycle, rules, procedures and persistence |
| `web/` | Operations console, six dashboards and Open MCT providers |
| `tests/` | Flight, ground and HTTP/WebSocket automated acceptance |
| `scripts/` | Reproducible setup, builds, benchmarks and evidence generation |
| `docs/` | Requirements, design decisions, ICD and application claims |

See [third-party notices](THIRD_PARTY.md) and [manual GitHub update instructions](docs/github-manual.md). This is AI-assisted work: review the implementation and be ready to explain its models, failure cases and design tradeoffs in an interview.

# Asteria FlightStack — F Prime integration

Build from the repository root with `.venv/bin/python scripts/setup_fprime.py`. Official F Prime v4.4.2 is pinned to a commit; its source and generated artifacts are ignored.

Three native executables are produced under `build-fprime-automatic-native/bin/<platform>/`:

- `AsteriaBridge`: one generated FlightComputer component with bounded process input/output for isolated MissionOps sessions.
- `AsteriaDeployment`: real framework topology with command dispatch, telemetry, event services and 1 Hz rate-group scheduling. Ctrl-C shuts it down and emits the final spacecraft snapshot.
- `AsteriaVerification`: typed-port harness for telemetry serialization, terminal response sequence, rejected/malformed commands and 1,801 scheduling calls.

Run `.venv/bin/python scripts/verify_fprime.py` from the repository root. It compares 171 bridge/core frames across three seeds and all six faults, runs the typed-port harness, and launches the scheduled topology for five seconds. CTest also registers the typed-port harness.

`FlightComputer.fpp` is the authoritative framework command/telemetry schema. The JSON spacecraft dictionary remains shared with the portable core. Framework `Mode` is an additional channel; `STEP`, `SNAPSHOT` and fault controls are lab facilities. The single wrapper avoids duplicating state or physics across executables. These models are not hardware drivers.

"""MissionOps: local process gateway, guarded operations and durable audit journal."""

import copy, json, math, os, pathlib, selectors, sqlite3, subprocess, threading, time, uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMMANDS = {
    "BOOT": ("operator", None),
    "SAFE": ("operator", None),
    "RECOVER": ("operator", None),
    "RESUME": ("operator", None),
    "PAYLOAD_ON": ("operator", None),
    "PAYLOAD_OFF": ("operator", None),
    "HEATER_ON": ("operator", None),
    "HEATER_OFF": ("operator", None),
    "ADCS_ON": ("operator", None),
    "ADCS_OFF": ("operator", None),
    "POINT": ("operator", (-180, 180)),
    "DESATURATE": ("operator", None),
    "INJECT_FAULT": ("administrator", (0, 5)),
    "CLEAR_FAULTS": ("administrator", None),
}
CHANNELS = {
    "time": ("Mission elapsed time", "s"),
    "battery_soc": ("Battery state of charge", "%"),
    "bus_voltage": ("Bus voltage", "V"),
    "solar_power": ("Solar generation", "W"),
    "load_power": ("Power consumption", "W"),
    "temperature": ("Bus temperature", "°C"),
    "heater": ("Heater enabled", "bool"),
    "attitude": ("Attitude angle", "deg"),
    "angular_rate": ("Angular rate", "deg/s"),
    "wheel_rpm": ("Reaction wheel", "rpm"),
    "target_angle": ("Pointing target", "deg"),
    "sensor_age": ("Sensor age", "s"),
    "adcs_enabled": ("ADCS enabled", "bool"),
    "link_connected": ("Link connected", "bool"),
    "link_age": ("Link loss duration", "s"),
    "packets": ("Downlink packets", "count"),
    "payload_enabled": ("Payload enabled", "bool"),
    "payload_data": ("Payload data", "MB"),
    "ticks": ("Scheduler ticks", "count"),
    "missed_deadlines": ("Injected missed deadlines", "count"),
    "commands_accepted": ("Accepted onboard commands", "count"),
    "commands_rejected": ("Rejected onboard commands", "count"),
    "orbit_phase": ("Illustrative orbit phase", "turn"),
    "sunlight": ("In sunlight", "bool"),
    "healthy": ("Recovery health gate", "bool"),
    "healthy_dwell": ("Healthy dwell time", "s"),
}
RULES = [
    ("FR-01", "Only operator or administrator may issue flight commands."),
    ("FR-02", "Fault injection and clearing require administrator training role."),
    ("FR-03", "Command IDs must be unique within a run; retries never execute twice."),
    ("FR-04", "Flight commands require an available downlink/uplink."),
    ("FR-05", "Payload requires NOMINAL mode."),
    (
        "FR-06",
        "Payload requires battery ≥40%, temperature <40°C, fresh sensor, rate ≤0.5°/s.",
    ),
    ("FR-07", "Heater requires NOMINAL, battery ≥30%, temperature <15°C."),
    (
        "FR-08",
        "Recovery requires SAFE, all faults cleared, health within limits, 10 s dwell.",
    ),
    ("FR-09", "Resume requires RECOVERY and healthy spacecraft."),
    (
        "FR-10",
        "Pointing requires NOMINAL, active ADCS, valid sensor and angle in ±180°.",
    ),
]
PROCEDURES = {
    "commission": {
        "title": "Commission the spacecraft",
        "steps": ["BOOT", "POINT", "PAYLOAD_ON"],
    },
    "power": {
        "title": "Recover from low power",
        "steps": ["CLEAR_FAULTS", "RECOVER", "RESUME"],
    },
    "thermal": {
        "title": "Recover from overheating",
        "steps": ["CLEAR_FAULTS", "RECOVER", "RESUME"],
    },
    "comms": {"title": "Restore communications", "steps": ["CLEAR_FAULTS"]},
    "attitude": {
        "title": "Recover attitude control",
        "steps": ["CLEAR_FAULTS", "DESATURATE", "RECOVER", "RESUME"],
    },
    "shutdown": {
        "title": "Secure the spacecraft",
        "steps": ["PAYLOAD_OFF", "HEATER_OFF", "SAFE"],
    },
}


class FlightProcess:
    def __init__(self, seed=42, executable=None):
        self.proc = subprocess.Popen(
            [
                str(
                    executable
                    or os.environ.get("ASTERIA_FLIGHT_EXECUTABLE")
                    or ROOT / "build/flight"
                ),
                str(seed),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.proc.stdout, selectors.EVENT_READ)

    def exchange(self, command, value=0, timeout=2):
        if self.proc.poll() is not None:
            raise RuntimeError("Flight process exited")
        self.proc.stdin.write("%s %.12g\n" % (command, value))
        self.proc.stdin.flush()
        deadline = time.monotonic() + timeout
        payload = bytearray()
        while not payload.endswith(b"\n"):
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not self.selector.select(remaining):
                self.close()
                raise TimeoutError("Flight acknowledgment deadline exceeded")
            chunk = os.read(self.proc.stdout.fileno(), 65536)
            if not chunk:
                raise RuntimeError("Flight process disconnected")
            payload.extend(chunk)
            if len(payload) > 262144:
                self.close()
                raise RuntimeError("Flight response exceeds 256 KiB frame limit")
        result = json.loads(payload)
        if result.get("protocol_version") != 1:
            raise RuntimeError("Incompatible protocol")
        return result

    def close(self):
        # EOF allows coverage/profiling runtimes to flush and the simulator to exit cleanly.
        if not self.proc.stdin.closed:
            self.proc.stdin.close()
        if self.proc.poll() is None:
            try:
                self.proc.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    self.proc.kill()
                    self.proc.wait()
        self.selector.close()
        for stream in (self.proc.stdout, self.proc.stderr):
            stream.close()


from .storage import Journal


def guard(role, command, value, state):
    if command not in COMMANDS:
        return "UNKNOWN_COMMAND"
    if role not in ("operator", "administrator"):
        return "FR-01_ROLE_DENIED"
    if COMMANDS[command][0] == "administrator" and role != "administrator":
        return "FR-02_ADMIN_REQUIRED"
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        return "INVALID_PARAMETER"
    bounds = COMMANDS[command][1]
    if bounds and not bounds[0] <= value <= bounds[1]:
        return "PARAMETER_RANGE"
    if command == "INJECT_FAULT" and int(value) != value:
        return "FAULT_INTEGER_REQUIRED"
    if bounds is None and value != 0:
        return "UNEXPECTED_PARAMETER"
    t = state["telemetry"]
    mode = state["mode"]
    if command in ("INJECT_FAULT", "CLEAR_FAULTS"):
        return None  # simulator lab controls, outside the radio path
    if not t["link_connected"]:
        return "FR-04_LINK_UNAVAILABLE"
    if command == "PAYLOAD_ON":
        if mode != "NOMINAL":
            return "FR-05_MODE"
        if (
            t["battery_soc"] < 40
            or t["temperature"] >= 40
            or t["sensor_age"] > 0
            or abs(t["angular_rate"]) > 0.5
        ):
            return "FR-06_RESOURCES"
    if command == "HEATER_ON" and (
        mode != "NOMINAL" or t["battery_soc"] < 30 or t["temperature"] >= 15
    ):
        return "FR-07_HEATER"
    if command == "RECOVER" and (
        mode != "SAFE" or not t["healthy"] or t["healthy_dwell"] < 10
    ):
        return "FR-08_RECOVERY"
    if command == "RESUME" and (mode != "RECOVERY" or not t["healthy"]):
        return "FR-09_RESUME"
    if command == "POINT" and (
        mode != "NOMINAL" or not t["adcs_enabled"] or t["sensor_age"] > 0
    ):
        return "FR-10_POINTING"
    return None


class Mission:
    def __init__(self, journal, seed=42, role="administrator"):
        self.epoch_ms = time.time() * 1000
        self.id = str(uuid.uuid4())
        self.journal = journal
        self.role = role
        self.seed = seed
        self.lock = threading.RLock()
        self.flight = FlightProcess(seed)
        self.truth = self.flight.exchange("SNAPSHOT")
        self.received = self.truth
        self.received_at_ms = time.time() * 1000
        self.last_received = 0
        self.running = False
        self.speed = 1
        self.failed = False
        self.last_access = time.monotonic()
        self.cache = {}
        self.procedure = None
        self.journal.append(
            self.id,
            0,
            "run",
            {
                "seed": seed,
                "role": role,
                "protocol_version": 1,
                "epoch_ms": self.epoch_ms,
            },
        )
        self.journal.append(self.id, 0, "telemetry", self.received)

    def record(self, kind, data):
        self.journal.append(self.id, self.truth["telemetry"]["time"], kind, data)

    def update(self, result):
        self.truth = result
        if result["telemetry"]["link_connected"]:
            self.received = result
            self.received_at_ms = time.time() * 1000
            self.last_received = result["telemetry"]["time"]
            self.record("telemetry", result)

    def step(self, seconds=1):
        with self.lock:
            if self.failed:
                raise RuntimeError("Mission process failed; start a new session")
            try:
                self.update(self.flight.exchange("STEP", seconds))
            except (RuntimeError, TimeoutError):
                self.failed = True
                self.running = False
                self.record("process_failure", {})
                raise

    def command(self, request):
        with self.lock:
            cid = request.get("id")
            command = request.get("command")
            value = request.get("value", 0)
            if (
                not isinstance(cid, str)
                or not 1 <= len(cid) <= 80
                or not all(c.isalnum() or c in "-_" for c in cid)
            ):
                return {"status": "rejected", "reason": "INVALID_COMMAND_ID"}
            if cid in self.cache:
                prior = self.cache[cid]
                if prior["command"] != command or prior["value"] != value:
                    return {
                        "id": cid,
                        "status": "rejected",
                        "reason": "FR-03_ID_CONFLICT",
                    }
                return dict(prior["result"], duplicate=True)
            if len(self.cache) >= 10000:
                return {"id": cid, "status": "rejected", "reason": "RUN_COMMAND_LIMIT"}
            if not isinstance(command, str):
                return {"id": cid, "status": "rejected", "reason": "INVALID_COMMAND"}
            start = time.perf_counter()
            self.record(
                "command_requested",
                {"id": cid, "command": command, "value": value, "role": self.role},
            )
            reason = guard(self.role, command, value, self.truth)
            result = {
                "id": cid,
                "command": command,
                "status": "rejected",
                "reason": reason,
            }
            if not reason:
                self.record("command_transmitted", {"id": cid, "command": command})
                try:
                    response = self.flight.exchange(command, value)
                    self.update(response)
                    result.update(
                        status="acknowledged" if response["ok"] else "rejected",
                        reason=response["reason"],
                    )
                except TimeoutError:
                    result.update(status="timed-out", reason="ACK_TIMEOUT")
                    self.failed = True
                    self.running = False
                except (RuntimeError, OSError, ValueError):
                    result.update(status="failed", reason="PROCESS_FAILURE")
                    self.failed = True
                    self.running = False
            result["latency_ms"] = (time.perf_counter() - start) * 1000
            self.record("command_terminal", result)
            self.cache[cid] = {"command": command, "value": value, "result": result}
            return result

    def status(self):
        with self.lock:
            now = self.truth["telemetry"]["time"]
            age = now - self.last_received
            t = self.received["telemetry"]
            alarms = []
            for active, code, msg in [
                (
                    age >= 3,
                    "STALE",
                    "Downlink stale: do not treat last values as current.",
                ),
                (
                    t["battery_soc"] < 20,
                    "POWER",
                    "Battery below 20%; autonomous load shedding.",
                ),
                (t["temperature"] >= 50, "THERMAL", "Bus temperature exceeds 50°C."),
                (t["sensor_age"] >= 3, "SENSOR", "Attitude sensor stale."),
                (abs(t["wheel_rpm"]) >= 6000, "WHEEL", "Reaction wheel saturation."),
                (self.failed, "PROCESS", "Flight process unavailable."),
                (
                    t["missed_deadlines"] > 0,
                    "WATCHDOG",
                    "Injected missed deadlines recorded.",
                ),
            ]:
                if active:
                    alarms.append(
                        {"code": code, "message": msg, "severity": "CRITICAL"}
                    )
            return copy.deepcopy(
                {
                    "epoch_ms": self.epoch_ms,
                    "received_at_ms": self.received_at_ms,
                    "run": self.id,
                    "role": self.role,
                    "state": self.received,
                    "sim_time": now,
                    "age": age,
                    "quality": (
                        "STALE"
                        if age >= 3
                        else (
                            "DISCONNECTED"
                            if not self.truth["telemetry"]["link_connected"]
                            else "LIVE"
                        )
                    ),
                    "running": self.running,
                    "speed": self.speed,
                    "alarms": alarms,
                    "procedure": self.procedure,
                    "failed": self.failed,
                }
            )

    def start_procedure(self, key):
        with self.lock:
            if self.role == "observer":
                return {"error": "ROLE_DENIED"}
            if key not in PROCEDURES:
                return {"error": "UNKNOWN_PROCEDURE"}
            self.procedure = {"key": key, "index": 0, "complete": False, "results": []}
            self.record("procedure_start", self.procedure.copy())
            return self.procedure

    def advance_procedure(self):
        with self.lock:
            if not self.procedure or self.procedure["complete"]:
                return {"error": "NO_ACTIVE_PROCEDURE"}
            p = self.procedure
            cmd = PROCEDURES[p["key"]]["steps"][p["index"]]
            result = self.command({"id": str(uuid.uuid4()), "command": cmd, "value": 0})
            p["results"].append(result)
            if result["status"] == "acknowledged":
                p["index"] += 1
            p["complete"] = p["index"] == len(PROCEDURES[p["key"]]["steps"])
            self.record("procedure_step", dict(p))
            return p

    def close(self):
        self.flight.close()

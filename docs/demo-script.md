# Reproducible demonstration — approximately 8–12 minutes

Start the server and open its local URL. All data are synthetic. Use administrator / seed 42. Pause whenever inspecting a result; accelerated time is simulated time, not elapsed wall time.

## 1. Establish authority (1 minute)

Initialize a mission. Explain: the browser sends JSON to a Python gateway; the gateway passes a bounded command frame to a C++ child process. SQLite records the request, transmission and terminal acknowledgment. Charts are populated by C++ snapshots.

Open MissionOps. Try PAYLOAD_ON while BOOT: expect FR-05_MODE. Show that the audit contains a rejection and there was no successful onboard command.

## 2. Commission (1 minute)

Load **Commission the spacecraft** and execute each step: BOOT, POINT (0°), PAYLOAD_ON. Expect NOMINAL and payload enabled. Run at 10× for about 10 wall seconds, then pause. Inspect payload data, power draw and attitude convergence.

## 3. Sensor contingency (2 minutes)

Open FlightStack, inject Sensor stale. Expect SAFE, sensor age ≥3 s and payload off. Attempt PAYLOAD_ON: ground mode rule rejects. Load **Recover attitude control** in MissionOps. Execute CLEAR_FAULTS and DESATURATE, then try RECOVER immediately: it remains pending because the health dwell is incomplete. Advance 10 s. Execute RECOVER and RESUME. Payload remains off until separately commanded.

## 4. Loss of signal (1–2 minutes)

Inject Communications loss. Advance 10 s: quality is STALE and displayed telemetry retains its old time/value. Advance 10 more seconds: remote mode is not known from stale telemetry. Try POINT: reject link unavailable. Clear fault sources: a fresh snapshot reveals SAFE after the 15 s onboard link-loss threshold. Advance 10 s, send RECOVER, then RESUME.

## 5. Power recovery (optional 2 minutes)

Inject Battery undervoltage: SOC becomes 15%, SAFE is latched. Clear faults. RECOVER must still reject. With simulation near time zero, advance roughly 1,850 s using 60× speed (about 31 wall seconds). Battery should reach ≥35% and healthy dwell ≥10 s while sunlit; verify the displayed gates rather than assuming a fixed timing for every mission phase. Recover and resume. This demonstrates physical recovery, not an instant reset button.

## 6. Reconstruct (2 minutes)

Open Replay & debrief. Load recorded telemetry and scrub before/after the fault. Generate a report. Explain that local gateway latency includes audit writes and pipe exchange; it is not radio latency or browser response time. Download the JSON journal and Markdown debrief.

End the session and initialize an Observer session. Issue BOOT: expect role denial. End this session. Explain that selectable roles are training personas, not production account authentication.

## Interview questions to prepare

- Why use two independent guard layers? What happens when their rules disagree?
- Why does clearing a thermal fault not instantly cool the spacecraft?
- How do command IDs prevent repeated execution, and what happens after server restart?
- What is deterministic about the simulator, and what is not guaranteed across CPU architectures?
- How does stale telemetry differ from a healthy spacecraft?
- Which original framework requirements are still missing, and how would you integrate them?
- What would need to change before any public deployment or real hardware connection?

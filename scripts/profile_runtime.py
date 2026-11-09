#!/usr/bin/env python3
"""Measure one child executable in isolation, then the real monotonic ground scheduler."""

import json, os, pathlib, platform, resource, subprocess, sys, tempfile, threading, time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ground.runtime import App


def main():
    executable = os.environ.get("ASTERIA_FLIGHT_EXECUTABLE", str(ROOT / "build/flight"))
    if "--child-only" in sys.argv:
        start = time.perf_counter()
        p = subprocess.run(
            [executable, "42"],
            input=("BOOT 0\n" + "STEP 1\n" * 20000).encode(),
            stdout=subprocess.DEVNULL,
            check=True,
        )
        use = resource.getrusage(resource.RUSAGE_CHILDREN)
        print(
            json.dumps(
                {
                    "steps": 20000,
                    "wall_seconds": time.perf_counter() - start,
                    "user_cpu_seconds": use.ru_utime,
                    "system_cpu_seconds": use.ru_stime,
                    "peak_resident_kib": (
                        use.ru_maxrss / 1024
                        if sys.platform == "darwin"
                        else use.ru_maxrss
                    ),
                }
            )
        )
        return
    child = json.loads(
        subprocess.check_output([sys.executable, __file__, "--child-only"], text=True)
    )
    with tempfile.TemporaryDirectory() as temp:
        app = App(pathlib.Path(temp) / "schedule.db")
        for i in range(8):
            _, mission = app.new("administrator", i)
            mission.running = True
            mission.speed = 60
        thread = threading.Thread(target=app.tick)
        thread.start()
        time.sleep(6.2)
        app.stop.set()
        thread.join(5)
        assert not thread.is_alive()
        samples = app.timing[:]
        times = [m.truth["telemetry"]["time"] for m in app.sessions.values()]
        assert len(samples) >= 5 and all(t >= 300 for t in times)
        app.close()
    report = {
        "platform": platform.platform(),
        "executable": pathlib.Path(executable).name,
        "isolated_child": child,
        "scheduler": {
            "active_sessions": 8,
            "simulation_speed": 60,
            "samples": samples,
            "work_overruns": sum(s["work_ms"] > s["budget_ms"] for s in samples),
            "late_by_full_period": sum(
                s["lateness_ms"] > s["budget_ms"] for s in samples
            ),
        },
        "limits": "Short local host profile, not real-time certification. Peak RSS and CPU cover the isolated flight executable; scheduler timing covers the Python ground scheduler, separately from F Prime rate-group verification.",
    }
    (ROOT / "evidence/runtime-profile.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

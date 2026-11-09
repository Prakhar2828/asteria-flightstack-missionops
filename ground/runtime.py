"""Session lifecycle and a monotonic-clock simulation scheduler."""

import secrets
import threading
import time
from .core import Journal, Mission


class App:
    def __init__(self, database):
        self.journal = Journal(database)
        self.sessions = {}
        self.lock = threading.RLock()
        self.stop = threading.Event()
        self.timing = []

    def new(self, role, seed):
        with self.lock:
            for token, mission in list(self.sessions.items()):
                if time.monotonic() - mission.last_access > 3600:
                    self.close_session(token)
            if len(self.sessions) >= 8:
                raise ValueError(
                    "Eight active sessions maximum; end an unused session."
                )
            token = secrets.token_urlsafe(32)
            mission = Mission(self.journal, seed, role)
            self.sessions[token] = mission
            return token, mission

    def authenticate(self, token):
        with self.lock:
            mission = self.sessions.get(token)
            if mission is None:
                raise PermissionError("Session expired; reconnect")
            mission.last_access = time.monotonic()
            return mission

    def close_session(self, token):
        with self.lock:
            mission = self.sessions.pop(token, None)
            if mission:
                with mission.lock:
                    mission.running = False
                    mission.close()

    def tick(self):
        deadline = time.monotonic() + 1
        while not self.stop.wait(max(0, deadline - time.monotonic())):
            started = time.monotonic()
            with self.lock:
                missions = list(self.sessions.values())
            for mission in missions:
                with mission.lock:
                    if mission.running:
                        try:
                            mission.step(mission.speed)
                        except (OSError, RuntimeError, TimeoutError, ValueError):
                            mission.running = False
                            mission.failed = True
            elapsed = time.monotonic() - started
            self.timing.append(
                {
                    "lateness_ms": max(0, started - deadline) * 1000,
                    "work_ms": elapsed * 1000,
                    "budget_ms": 1000,
                }
            )
            self.timing = self.timing[-3600:]
            # A missed wall deadline never silently fast-forwards the spacecraft.
            deadline += 1
            if deadline < time.monotonic():
                deadline = time.monotonic() + 1

    def close(self):
        self.stop.set()
        for token in list(self.sessions):
            self.close_session(token)
        self.journal.close()

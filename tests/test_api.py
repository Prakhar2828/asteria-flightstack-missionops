"""Real ASGI requests and WebSocket sessions; no browser emulation."""

import pathlib, sys, tempfile, unittest, uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
try:
    from fastapi.testclient import TestClient
    from ground.api import create_app

    AVAILABLE = True
except ImportError:
    AVAILABLE = False


@unittest.skipUnless(AVAILABLE, "Install requirements.txt for API verification")
class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.client = TestClient(
            create_app(pathlib.Path(self.tmp.name) / "journal.db"),
            base_url="http://localhost",
        )
        self.client.__enter__()
        r = self.client.post("/api/session", json={"role": "administrator", "seed": 42})
        self.assertEqual(r.status_code, 201)
        self.token = r.json()["token"]
        self.headers = {"Authorization": "Bearer " + self.token}

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.tmp.cleanup()

    def post(self, path, data):
        return self.client.post(path, json=data, headers=self.headers)

    def command(self, name, value=0, cid=None):
        return self.post(
            "/api/command",
            {"id": cid or str(uuid.uuid4()), "command": name, "value": value},
        )

    def test_schema_export(self):
        self.assertIn(
            "/api/command", self.client.get("/api/openapi.json").json()["paths"]
        )

    def test_missing_auth(self):
        self.assertEqual(self.client.get("/api/status").status_code, 401)

    def test_raw_token_not_bearer(self):
        self.assertEqual(
            self.client.get(
                "/api/status", headers={"Authorization": self.token}
            ).status_code,
            401,
        )

    def test_forged_token(self):
        self.assertEqual(
            self.client.get(
                "/api/status", headers={"Authorization": "Bearer nope"}
            ).status_code,
            401,
        )

    def test_unknown_session_field(self):
        self.assertEqual(
            self.client.post(
                "/api/session", json={"role": "administrator", "admin": True}
            ).status_code,
            400,
        )

    def test_nonfinite(self):
        self.assertEqual(
            self.client.post(
                "/api/command",
                content='{"id":"bad","command":"POINT","value":NaN}',
                headers={**self.headers, "Content-Type": "application/json"},
            ).status_code,
            400,
        )

    def test_bool_parameter(self):
        self.assertEqual(self.command("POINT", True).status_code, 400)

    def test_string_seed(self):
        self.assertEqual(
            self.client.post("/api/session", json={"seed": "42"}).status_code, 400
        )

    def test_wrong_content_type(self):
        self.assertEqual(
            self.client.post("/api/session", content="{}").status_code, 415
        )

    def test_body_limit(self):
        self.assertEqual(
            self.client.post(
                "/api/session",
                content=" " * 9000,
                headers={"Content-Type": "application/json"},
            ).status_code,
            413,
        )

    def test_origin(self):
        self.assertEqual(
            self.client.post(
                "/api/session", json={}, headers={"Origin": "https://evil.invalid"}
            ).status_code,
            403,
        )

    def test_host(self):
        self.assertEqual(
            self.client.get(
                "/api/catalog", headers={"Host": "evil.invalid"}
            ).status_code,
            403,
        )

    def test_session_seed_bound(self):
        self.assertEqual(
            self.client.post("/api/session", json={"seed": 4294967296}).status_code, 400
        )

    def test_command_ack(self):
        self.assertEqual(self.command("BOOT").json()["status"], "acknowledged")

    def test_command_duplicate(self):
        self.command("BOOT", cid="retry")
        self.assertTrue(self.command("BOOT", cid="retry").json()["duplicate"])

    def test_command_conflict(self):
        self.command("BOOT", cid="retry")
        self.assertEqual(
            self.command("SAFE", cid="retry").json()["reason"], "FR-03_ID_CONFLICT"
        )

    def test_role_denied(self):
        token = self.client.post("/api/session", json={"role": "observer"}).json()[
            "token"
        ]
        r = self.client.post(
            "/api/command",
            json={"id": "denied", "command": "BOOT"},
            headers={"Authorization": "Bearer " + token},
        )
        self.assertEqual(r.json()["reason"], "FR-01_ROLE_DENIED")

    def test_step_bounds(self):
        self.assertEqual(
            self.post("/api/control", {"action": "step", "value": 0}).status_code, 400
        )

    def test_speed_bounds(self):
        self.assertEqual(
            self.post("/api/control", {"action": "speed", "value": 7}).status_code, 400
        )

    def test_procedure_ambiguous(self):
        self.assertEqual(
            self.post(
                "/api/procedure", {"action": "advance", "key": "power"}
            ).status_code,
            400,
        )

    def test_procedure_completed(self):
        self.post("/api/procedure", {"key": "commission"})
        for _ in range(3):
            r = self.post("/api/procedure", {"action": "advance"})
        self.assertTrue(r.json()["complete"])

    def test_stream_sequence(self):
        with self.client.websocket_connect("ws://localhost/api/stream") as ws:
            ws.send_json({"token": self.token})
            a = ws.receive_json()
            b = ws.receive_json()
            self.assertEqual(b["sequence"], a["sequence"] + 1)
            self.assertEqual(a["status"]["role"], "administrator")

    def test_stream_matches_command(self):
        self.command("BOOT")
        with self.client.websocket_connect("ws://localhost/api/stream") as ws:
            ws.send_json({"token": self.token})
            self.assertEqual(ws.receive_json()["status"]["state"]["mode"], "NOMINAL")

    def test_history(self):
        self.command("BOOT")
        self.post("/api/control", {"action": "step", "value": 10})
        r = self.client.get("/api/history/battery_soc", headers=self.headers)
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(len(r.json()), 3)
        self.assertIn("timestamp", r.json()[0])

    def test_history_unknown(self):
        self.assertEqual(
            self.client.get("/api/history/unknown", headers=self.headers).status_code,
            400,
        )

    def test_history_range(self):
        self.assertEqual(
            self.client.get(
                "/api/history/time?start=20&end=10", headers=self.headers
            ).status_code,
            400,
        )

    def test_pagination(self):
        self.command("BOOT")
        a = self.client.get("/api/records?limit=2", headers=self.headers).json()
        b = self.client.get(
            "/api/records?limit=2&after=" + str(a["next_cursor"]), headers=self.headers
        ).json()
        self.assertTrue(a["has_more"])
        self.assertGreater(b["records"][0]["id"], a["records"][-1]["id"])

    def test_export_valid_json(self):
        self.command("BOOT")
        r = self.client.get("/api/export", headers=self.headers).json()
        self.assertEqual(r["records"][-1]["kind"], "command_terminal")

    def test_close_revokes(self):
        self.post("/api/close", {})
        self.assertEqual(
            self.client.get("/api/status", headers=self.headers).status_code, 401
        )

    def test_vendor_served(self):
        r = self.client.get("/vendor/openmct/openmct.js")
        self.assertEqual(r.status_code, 200)
        self.assertGreater(len(r.content), 100000)

    def test_openmct_page(self):
        self.assertIn("openmct-adapter.js", self.client.get("/openmct").text)

    def test_session_limit(self):
        for _ in range(7):
            self.assertEqual(self.client.post("/api/session", json={}).status_code, 201)
        self.assertEqual(self.client.post("/api/session", json={}).status_code, 429)

    def test_openmct_runtime_policy_is_scoped(self):
        self.assertIn(
            "'unsafe-eval'",
            self.client.get("/openmct").headers["content-security-policy"],
        )
        self.assertNotIn(
            "'unsafe-eval'", self.client.get("/").headers["content-security-policy"]
        )

    def test_telemetry_receipt_timestamp(self):
        first = self.client.get("/api/status", headers=self.headers).json()[
            "received_at_ms"
        ]
        self.post("/api/control", {"action": "step", "value": 1})
        second = self.client.get("/api/status", headers=self.headers).json()[
            "received_at_ms"
        ]
        self.assertGreaterEqual(second, first)

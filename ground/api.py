"""Versioned FastAPI gateway. Local training identities; spacecraft remains authoritative."""

import os
import asyncio
import json
import math
import pathlib
import threading
import time
from contextlib import asynccontextmanager
from typing import Annotated, Literal
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator
from .core import ROOT, CHANNELS, COMMANDS, RULES, PROCEDURES
from .runtime import App


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class SessionRequest(StrictModel):
    role: Literal["observer", "operator", "administrator"] = "administrator"
    seed: Annotated[StrictInt, Field(ge=0, le=4294967295)] = 42


class CommandRequest(StrictModel):
    id: Annotated[str, Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")]
    command: Annotated[str, Field(min_length=1, max_length=32)]
    value: float | int = 0

    @field_validator("value")
    @classmethod
    def finite(cls, value):
        if isinstance(value, bool) or not math.isfinite(value):
            raise ValueError("A finite numeric parameter is required")
        return value


class ControlRequest(StrictModel):
    action: Literal["run", "pause", "speed", "step"]
    value: StrictInt | None = None


class ProcedureRequest(StrictModel):
    action: Literal["advance"] | None = None
    key: str | None = None


class EmptyRequest(StrictModel):
    pass


def create_app(database=None):
    database = database or ROOT / "data/missions.sqlite3"
    if not str(database).startswith(("postgresql://", "postgres://")):
        pathlib.Path(database).parent.mkdir(parents=True, exist_ok=True)

    @asynccontextmanager
    async def lifespan(app):
        runtime = App(database)
        app.state.runtime = runtime
        thread = threading.Thread(target=runtime.tick, daemon=True)
        thread.start()
        try:
            yield
        finally:
            runtime.stop.set()
            await asyncio.to_thread(thread.join, 5)
            runtime.close()

    app = FastAPI(
        title="Asteria MissionOps",
        version="1.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        redoc_url=None,
    )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse(
            {
                "error": "SCHEMA_VALIDATION",
                "details": [
                    {"field": ".".join(map(str, e["loc"])), "message": e["msg"]}
                    for e in exc.errors()
                ],
            },
            status_code=400,
        )

    @app.middleware("http")
    async def boundary(request, call_next):
        host = request.headers.get("host", "")
        hostname = host.split(":")[0]
        if hostname not in ("127.0.0.1", "localhost"):
            return JSONResponse({"error": "INVALID_HOST"}, status_code=403)
        origin = request.headers.get("origin")
        if origin and origin != str(request.base_url).rstrip("/"):
            return JSONResponse({"error": "ORIGIN_DENIED"}, status_code=403)
        if request.method == "POST":
            if (
                request.headers.get("content-type", "").split(";")[0]
                != "application/json"
            ):
                return JSONResponse({"error": "JSON_REQUIRED"}, status_code=415)
            raw = bytearray()
            async for part in request.stream():
                raw.extend(part)
                if len(raw) > 8192:
                    return JSONResponse({"error": "BODY_SIZE"}, status_code=413)
            request._body = bytes(raw)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        # The vendored Open MCT Vue build compiles templates at runtime.
        # Permit this only on its dedicated document; console/API retain strict script policy.
        script_policy = (
            "script-src 'self' 'unsafe-eval'; "
            if request.url.path == "/openmct"
            else "script-src 'self'; "
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            + script_policy
            + "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; "
            "worker-src 'self' blob:; frame-ancestors 'none'; base-uri 'none'"
        )
        return response

    def mission(request):
        auth = request.headers.get("authorization", "")
        if not auth.startswith("Bearer "):
            raise HTTPException(401, "Bearer session token required")
        try:
            return app.state.runtime.authenticate(auth[7:])
        except PermissionError as exc:
            raise HTTPException(401, str(exc)) from exc

    @app.get("/api/health")
    def health():
        return {
            "status": "ready",
            "protocol_version": 1,
            "api_version": "1.0",
            "database": app.state.runtime.journal.backend,
            "flight_backend": (
                "fprime"
                if "AsteriaBridge" in os.getenv("ASTERIA_FLIGHT_EXECUTABLE", "")
                else "portable"
            ),
        }

    @app.get("/api/catalog")
    def catalog():
        return {
            "channels": CHANNELS,
            "commands": COMMANDS,
            "rules": RULES,
            "procedures": PROCEDURES,
        }

    @app.post("/api/session", status_code=201)
    def session(body: SessionRequest):
        try:
            token, m = app.state.runtime.new(body.role, body.seed)
        except ValueError as exc:
            raise HTTPException(429, str(exc)) from exc
        return {"token": token, **m.status()}

    @app.get("/api/status")
    def status(request: Request):
        return mission(request).status()

    @app.post("/api/command")
    def command(request: Request, body: CommandRequest):
        return mission(request).command(body.model_dump())

    @app.post("/api/control")
    def control(request: Request, body: ControlRequest):
        m = mission(request)
        if m.role == "observer":
            raise HTTPException(403, "ROLE_DENIED")
        with m.lock:
            if body.action == "run":
                if m.failed:
                    raise HTTPException(
                        409, "Flight process failed; start a new session"
                    )
                m.running = True
            elif body.action == "pause":
                m.running = False
            elif body.action == "speed":
                if body.value not in (1, 10, 60):
                    raise HTTPException(400, "Speed must be 1, 10 or 60")
                m.speed = body.value
            elif body.action == "step":
                if body.value is None or not 1 <= body.value <= 3600:
                    raise HTTPException(400, "Step must be 1–3600 seconds")
                m.step(body.value)
            m.record("simulation_control", body.model_dump(exclude_none=True))
        return m.status()

    @app.post("/api/procedure")
    def procedure(request: Request, body: ProcedureRequest):
        m = mission(request)
        if (body.action is None) == (body.key is None):
            raise HTTPException(400, "Choose key or action, not both")
        result = m.advance_procedure() if body.action else m.start_procedure(body.key)
        if "error" in result:
            raise HTTPException(400, result["error"])
        return result

    @app.get("/api/records")
    def records(request: Request, after: int = 0, limit: int = 2000):
        m = mission(request)
        if after < 0 or not 1 <= limit <= 5000:
            raise HTTPException(400, "Cursor/limit outside bounds")
        rows = m.journal.read(m.id, after, limit)
        return {
            "schema": "asteria-journal-v1",
            "run": m.id,
            "seed": m.seed,
            "records": rows,
            "next_cursor": rows[-1]["id"] if rows else after,
            "has_more": len(rows) == limit,
        }

    @app.get("/api/export")
    def export(request: Request):
        m = mission(request)
        # Freeze the upper record ID so exports have a consistent end even while running.
        upper = m.journal.last_id(m.id)

        def stream():
            yield json.dumps(
                {"schema": "asteria-journal-v1", "run": m.id, "seed": m.seed}
            )[:-1] + ',"records":['
            cursor, first = 0, True
            while True:
                rows = m.journal.read(m.id, cursor, 1000)
                rows = [r for r in rows if r["id"] <= upper]
                if not rows:
                    break
                for row in rows:
                    yield ("" if first else ",") + json.dumps(row, allow_nan=False)
                    first = False
                cursor = rows[-1]["id"]
                if cursor >= upper:
                    break
            yield "]}"

        return StreamingResponse(stream(), media_type="application/json")

    @app.get("/api/history/{channel}")
    def history(request: Request, channel: str, start: float = 0, end: float = 1e16):
        m = mission(request)
        if (
            channel not in CHANNELS
            or not all(map(math.isfinite, (start, end)))
            or end < start
        ):
            raise HTTPException(400, "Invalid history range/channel")
        return m.journal.history(m.id, channel, start, end, m.epoch_ms)

    @app.post("/api/close")
    def close(request: Request, body: EmptyRequest):
        mission(request)
        app.state.runtime.close_session(request.headers["authorization"][7:])
        return {"closed": True}

    @app.websocket("/api/stream")
    async def websocket(ws: WebSocket):
        host = ws.headers.get("host", "")
        if host.split(":")[0] not in ("localhost", "127.0.0.1"):
            return await ws.close(code=1008)
        origin = ws.headers.get("origin")
        if origin and origin != "http://" + host:
            return await ws.close(code=1008)
        await ws.accept()
        try:
            raw = await asyncio.wait_for(ws.receive_text(), 5)
            if len(raw) > 256:
                return await ws.close(code=1008)
            token = json.loads(raw).get("token")
            if not isinstance(token, str):
                return await ws.close(code=1008)
            m = app.state.runtime.authenticate(token)
            sequence = 0
            while True:
                app.state.runtime.authenticate(token)
                snapshot = await asyncio.to_thread(m.status)
                sequence += 1
                await asyncio.wait_for(
                    ws.send_json(
                        {
                            "sequence": sequence,
                            "sent_at_ms": time.time() * 1000,
                            "status": snapshot,
                        }
                    ),
                    2,
                )
                await asyncio.sleep(0.25)
        except (
            WebSocketDisconnect,
            PermissionError,
            asyncio.TimeoutError,
            ValueError,
            TypeError,
            RuntimeError,
        ):
            try:
                await ws.close(code=1008)
            except RuntimeError:
                pass

    @app.get("/")
    def index():
        return FileResponse(ROOT / "web/index.html")

    @app.get("/openmct")
    def openmct():
        return FileResponse(ROOT / "web/openmct.html")

    app.mount("/", StaticFiles(directory=ROOT / "web"), name="assets")
    return app

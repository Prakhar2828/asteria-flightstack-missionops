#!/usr/bin/env python3
"""Build a static, independently usable C++/WebAssembly demo for free hosting."""

import argparse, json, os, pathlib, re, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ground.core import CHANNELS, COMMANDS, RULES, PROCEDURES


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--emcc", default=os.getenv("EMCC", "em++"))
    args = parser.parse_args()
    out = ROOT / "dist"
    out.mkdir(exist_ok=True)
    shutil.copytree(ROOT / "web", out, dirs_exist_ok=True)
    for name in ["runtime-core.mjs", "public-runtime.js"]:
        shutil.copy2(ROOT / "public-demo" / name, out / name)
    (out / "catalog.json").write_text(
        json.dumps(
            {
                "channels": CHANNELS,
                "commands": COMMANDS,
                "rules": RULES,
                "procedures": PROCEDURES,
            },
            indent=2,
        )
        + "\n"
    )
    subprocess.run(
        [
            args.emcc,
            str(ROOT / "public-demo/flight-wasm.cpp"),
            "-std=c++17",
            "-O2",
            "-sMODULARIZE=1",
            "-sEXPORT_NAME=createAsteria",
            "-sALLOW_MEMORY_GROWTH=1",
            "-sMAXIMUM_MEMORY=67108864",
            '-sEXPORTED_RUNTIME_METHODS=["ccall","cwrap"]',
            "-sENVIRONMENT=web,node",
            "-o",
            str(out / "flight-wasm.js"),
        ],
        check=True,
    )
    for name in ["index.html", "openmct.html"]:
        p = out / name
        s = p.read_text()
        s = s.replace('href="/openmct"', 'href="./openmct.html"').replace(
            'href="/"', 'href="./"'
        )
        s = re.sub(r'(src|href)="/', r'\1="./', s)
        marker = (
            '<script src="./app.js"'
            if name == "index.html"
            else '<script src="./openmct-adapter.js"'
        )
        s = s.replace(
            marker,
            '<script src="./flight-wasm.js" defer></script><script src="./public-runtime.js" defer></script>'
            + marker,
        )
        if name == "index.html":
            s = s.replace(
                "Each session starts an isolated C++ spacecraft. Roles are selectable training personas, not production identities.",
                "Run the real C++ spacecraft model in your browser. No signup, installation or server required. Training roles affect this tab only.",
            )
            s = (
                s.replace("Python operations gateway", "Browser operations adapter")
                .replace("C++17 onboard core", "C++17 · WebAssembly")
                .replace("Local · no external services", "Free public interactive demo")
            )
            s = s.replace(
                "SOFTWARE-ONLY SPACECRAFT TESTBED",
                "PUBLIC DEMO · C++ RUNNING IN YOUR BROWSER",
            )
            s = s.replace(
                "Records persist in the local SQLite database. A new session begins a separate mission.",
                "Your mission stays in this browser tab. Export before ending the session. No telemetry is uploaded to a server.",
            )
            s = s.replace(
                "The local stack includes a NASA F Prime deployment and command bridge, NASA Open MCT live/history providers, a FastAPI gateway, WebSocket telemetry, and SQLite or PostgreSQL storage. Physical hardware and public hosting are outside this local release. See the evidence report for the exact verification scope.",
                "This public demo compiles the same C++ spacecraft core to WebAssembly and runs an independent browser operations adapter with NASA Open MCT. It does not run F Prime, FastAPI or PostgreSQL on the hosting server. Those fully documented integrations remain available in the source repository for local use. Browser roles are training personas, not security identities.",
            )
            s = s.replace(
                "A Python ground gateway with independent flight rules, training roles, guided procedures, SQLite/PostgreSQL event storage, and replay.",
                "The local project includes Python, independent flight rules, procedures and SQLite/PostgreSQL. This public edition mirrors its operations in a browser adapter and keeps an exportable per-tab journal.",
            )
            s = s.replace(
                "↕ HTTP + WebSocket on loopback", "↕ Browser adapter / local callbacks"
            ).replace(
                "F Prime / portable flight process + durable journal",
                "Compiled C++ WebAssembly + per-tab journal",
            )
            s = s.replace(
                '<div class="lab-badge">SIMULATION ENVIRONMENT</div>',
                '<a class="lab-badge" href="https://github.com/Prakhar2828/asteria-flightstack-missionops" target="_blank" rel="noopener">VIEW SOURCE &amp; TEST EVIDENCE ↗</a>',
            )
        p.write_text(s)
    p = out / "app.js"
    s = p.read_text().replace(
        "async function api(path,body){",
        "async function api(path,body){if(window.AsteriaPublic)return window.AsteriaPublic.api(path,body);",
    )
    s = s.replace(
        "new WebSocket(location.origin.replace(/^http/,'ws')+'/api/stream')",
        "window.AsteriaPublic.socket()",
    )
    s = (
        s.replace(
            "C++ process + Python gateway.", "C++ WebAssembly + browser ground adapter."
        )
        .replace("p95 local gateway command latency", "p95 browser command latency")
        .replace(
            "Latency covers journal writes and local process exchange, not browser display or orbital communications.",
            "Latency covers browser guards and WebAssembly execution, not network or orbital communications.",
        )
        .replace(
            "Could not connect to the local gateway: ",
            "Could not initialize the browser demo: ",
        )
    )
    s = s.replace(
        "$('engineering').append(timing);",
        "if(!window.AsteriaPublic)$('engineering').append(timing);",
    )
    p.write_text(s)
    p = out / "openmct-adapter.js"
    s = p.read_text().replace(
        "async function get(path) {",
        "async function get(path) {\n    if(window.AsteriaPublic)return window.AsteriaPublic.api(path);",
    )
    s = s.replace(
        "openmct.setAssetPath('/vendor/openmct')",
        "openmct.setAssetPath('./vendor/openmct')",
    ).replace(
        "new WebSocket(location.origin.replace(/^http/,'ws')+'/api/stream')",
        "window.AsteriaPublic.socket()",
    )
    p.write_text(s)
    (out / ".nojekyll").write_text("")
    print("Static demo built in " + str(out))


if __name__ == "__main__":
    main()

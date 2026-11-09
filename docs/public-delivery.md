# Free public delivery

The public edition runs the original `flight/flight.hpp` C++ model compiled to WebAssembly with Emscripten 4.0.23. Each visitor gets an independent in-browser mission: commanding, all six fault sources, recovery, six dashboards, procedures, audit export, replay and NASA Open MCT telemetry. No signup, API key, remote spacecraft process, database account or paid compute is required.

The Python/FastAPI gateway, PostgreSQL adapter and F Prime component/deployment remain available in the source repository for local execution. The public edition uses a JavaScript operations adapter with parity tests against Python flight-rule decisions. It does **not** claim to run F Prime or PostgreSQL inside the browser or on GitHub Pages.

## Hosting

GitHub Pages serves only the generated static distribution. `.github/workflows/pages.yml` builds it from source, compares native C++/WebAssembly results and browser/Python guards, and publishes only after those checks pass. The public repository's existing verification workflow separately checks the local projects.

The site is available without authentication and does not depend on the author's laptop. The published URL uses the existing GitHub-provided domain. No custom domain, credit card, paid hosting or billable backend is configured. GitHub Pages' published usage limits still apply.

## Browser behavior

- State is isolated per tab. No simulated telemetry or commands are uploaded to an application server.
- Navigation to Open MCT restores the same mission by replaying its C++ command transcript, with the clock paused on restoration. Use Run to continue.
- Session storage preserves the mission while the tab remains open. Export the JSON journal before closing it. Browser storage limits can pause a long run; exports remain available.
- Recorded operations are capped at 7,200 C++ exchanges / 20,000 journal records. Limits stop new execution instead of silently deleting evidence.
- Training roles are educational controls, not a security boundary. Visitors can inspect and modify code running on their own computer.
- Browser background throttling may slow the simulation; no hidden wall-clock time is retroactively simulated.

## Rebuild

Install the official Emscripten SDK version 4.0.23 and activate its environment, then run:

```sh
python3 scripts/build.py
python3 scripts/build_public.py
python3 scripts/verify_public.py
python3 -m http.server 8090 --directory dist
```

`verify_public.py` requires Node 24 and records evidence in `evidence/public-verification.json`. The normal native environment and tests are described in the main README.

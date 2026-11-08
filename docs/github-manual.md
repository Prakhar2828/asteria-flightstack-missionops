# Manual GitHub publication — Prakhar2828

Nothing has been created or pushed to GitHub by this implementation. The source is local. The earlier CLI authentication check found an invalid stored token; sign in manually when ready.

Recommended first repository: **Prakhar2828/asteria-flightstack-missionops**. A monorepo preserves one shared ICD and reproducible integration. You can list FlightStack and MissionOps as distinct projects while linking to their subdirectories. Creating two repositories now would require choosing and maintaining a versioned integration packaging strategy; no duplicate codebases are generated automatically.

1. Read the scope ledger and inspect the evidence. Run the tests yourself. Review source for correctness and understand the AI-assisted implementation before publishing or claiming ownership.
2. In GitHub, create an empty repository under **Prakhar2828**, choosing your desired visibility. Do not initialize a conflicting README/license there.
3. In Terminal, run these commands yourself from this project's directory:

```sh
git init -b main
git add .
git diff --cached --stat
git commit -m "Add Asteria spacecraft and mission operations prototype"
git remote add origin https://github.com/Prakhar2828/asteria-flightstack-missionops.git
git push -u origin main
```

The `.gitignore` excludes build binaries, local databases, Python caches and environment files. The synthetic evidence is intended for publication. Do not add personal tokens or private application material.

4. Confirm Actions runs successfully before displaying any CI badge. The workflow is prepared for Linux and macOS, but has not run on GitHub in this local release.
5. Add repository topics such as `spacecraft-simulation`, `cpp17`, `mission-operations`, `fault-injection`, `telemetry`, and `software-verification`. Do not tag implemented frameworks that are absent.
6. Record the walkthrough, then add a real screenshot/video and exact verified results. The current UI has not been visually verified because browser automation was unavailable.

## Zero-dollar constraints

Local operation costs nothing beyond your existing computer and installed compiler/Python. No account billing, API, or subscription is required. GitHub provides public repositories and GitHub Pages on its free plan, but Pages only serves static content: **it cannot host this Python/C++ live backend**. Do not imply that pushing this repository creates a working public simulator.

A public no-backend demo would need a separately implemented browser build (e.g. the same C++ core compiled to WebAssembly) or a clearly labeled recorded replay viewer. A hosted backend requires provider-specific cost/limit review and security redesign. No hosting account is configured, no paid service is required, and no public deployment is claimed here.

References checked while preparing the project:
- https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
- https://docs.github.com/en/enterprise-cloud%40latest/pages/getting-started-with-github-pages/what-is-github-pages
- https://fprime.jpl.nasa.gov/latest/docs/getting-started/installing-fprime/
- https://nasa.github.io/openmct/getting-started/

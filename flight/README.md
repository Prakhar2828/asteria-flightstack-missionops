# Asteria FlightStack

The onboard half of the Asteria laboratory. `flight.hpp` contains five subsystem state structures, a logical scheduler, a mode manager, fault protection, seeded dynamics, and validated commands. `main.cpp` exposes the framed local process protocol.

Build from the repository root with `python3 scripts/build.py`. Run `build/flight 42`, enter `BOOT 0`, `STEP 10`, or `INJECT_FAULT 2` followed by Return. Each input line produces one JSON response. End stdin (Ctrl-D) to exit. Use `SNAPSHOT 0` for a non-mutating state query.

Optional CMake build: `cmake -S flight -B build/cmake` then `cmake --build build/cmake`. CMake is not required by the default build.

The shared browser's **FlightStack** workspace is the interactive front end. Start the ground server from the repository root to use it. The command-line flight process and its tests run independently of the HTTP server.

This custom core is **not a NASA F Prime deployment**. Its explicit educational purpose is to make deterministic modeling, failure handling, and interfaces inspectable without framework tooling. F Prime integration remains a separate uncompleted master-spec item.

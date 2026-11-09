# Third-party software

- **NASA F Prime v4.4.2**, commit `f22ce8f2f2943e641d454e9daa7f129e6c878d32`: https://github.com/nasa/fprime/tree/v4.4.2. Apache-2.0 license and notices are in the downloaded official framework. The project/deployment skeleton derives from its official tooling. Framework source is downloaded by `scripts/setup_fprime.py` and is not vendored in this repository.
- **NASA Open MCT 4.3.1**: https://github.com/nasa/openmct. Apache-2.0 license in `web/vendor/openmct/LICENSE.md`; bundled dependency notices are retained beside JavaScript assets. Distribution source: `https://registry.npmjs.org/openmct/-/openmct-4.3.1.tgz`. Verified npm integrity: `sha512-MBpBmuxmEEK/DFjlXxrGEKyjm/suN7mIuFjGu4fnniUBv5lKqrzm1RuVEhnCfsIhig1NsVG4SL9apsAJXQFWcA==`. Runtime distribution assets are included without source maps. NASA logos in the upstream assets identify upstream software, not endorsement of Asteria.
- **Python packages** are pinned in `requirements.txt` and installed from PyPI. Their original licenses remain in the installed distributions. PostgreSQL is optional; its tested local version is 17.11.

No third-party assets are fetched during a normal local mission. Open MCT's distributed Vue build needs runtime template compilation; only its dedicated `/openmct` document permits `unsafe-eval`. The custom console keeps the stricter same-origin script policy.

- **Emscripten 4.0.23**, official SDK tooling commit `1693ce7359fc9694f198694f902a2cc061239b86`: https://github.com/emscripten-core/emsdk. Used to compile the original C++ model to WebAssembly. SDK/framework licenses are retained in the downloaded build tools; the project does not vendor the SDK itself.

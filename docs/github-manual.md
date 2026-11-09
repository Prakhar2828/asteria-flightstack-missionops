# Repository and public delivery

Repository: https://github.com/Prakhar2828/asteria-flightstack-missionops

Public demo: https://prakhar2828.github.io/asteria-flightstack-missionops/

Pushes to `main` run native verification and build, test and deploy the public WebAssembly demo through `.github/workflows/pages.yml`. GitHub Pages must use GitHub Actions as its publishing source. No paid server, domain or API key is needed.

For future updates, review `git diff`, run `python scripts/verify.py`, commit the intended changes and run `git push origin main`. Check both workflows in Actions before sharing a new release. Build outputs, environments, downloaded framework sources and mission databases are ignored.

The public website runs isolated browser missions. The full Python/F Prime/database system remains a local installation; see [public delivery](public-delivery.md).

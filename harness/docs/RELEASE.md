# Release checklist (Ubuntu 22.04 and 24.04, D-110)

Run `python -m tools.release_check` on the build host (Ubuntu 22.04 so the package also starts on 24.04; with Docker use `packaging/ubuntu/container/`). It performs the automated steps (1 to 10) and writes `dist/release-docs/release-report.md`. Steps 11 to 13 are for people.

1. Versions agree in `pyproject.toml`, `harness_tool/__init__.py` and the top of `CHANGELOG.md` (the changelog entry says what changed and what is still open).
2. `ruff format --check`, `ruff check` and `mypy --strict` are clean.
3. The independent verifiers are clean on `mini3`, `sat15` and `sat15_full`.
4. Performance targets on the stress project: generation under 10 s, no design rule errors; export and checks complete.
5. Fuzzing and security tests pass (`HARNESS_FUZZ_EXAMPLES=5000 pytest tests/test_fuzz.py` for the long search; findings in `docs/SECURITY.md`).
6. Soak test: 3,000 random editing steps with all invariants held (`python -m tools.soak 5000 <seed>` for the long run).
6. The full test suite passes with the 90% core coverage gate (docs, goldens, GUI journeys and accessibility audit included).
7. `python -m tools.gen_sbom` writes `sbom.cdx.json` and `licence-report.md` with nothing rejected (needs the wheelhouse from `python -m tools.vendor`, or network access, on the build host).
8. `python -m tools.check_reproducible`: the wheel builds identically twice.
9. `python -m tools.build_installer` then `python -m tools.build_deb`; `dist/harness-tool/harness-tool --selftest` prints `selftest ok` (generates, exports and verifies a project inside the package).
10. The `.deb` is extracted with `dpkg-deb -x` and its program runs the self-test.
11. Run the self-test on a clean Ubuntu VM with networking disabled, installing with `sudo apt install ./harness-tool_<version>_amd64.deb` and, separately, with `./install.sh` from the tarball.
12. Usability sessions held and triaged (`docs/usability/README.md`); priority bugs fixed or accepted by the owner in writing.
13. Owner sign-off, including the open decisions D-10, D-11, D-15 (see `docs/OPEN_DECISIONS.md`; D-20 is not needed). Remove `rcN` from the version only after sign-off.

Do not release while any step fails. A release candidate with open decisions is labelled `rc` and says so in its changelog.

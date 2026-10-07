# Release checklist (grows with each milestone)

1. All tests green on Windows and Linux CI; `ruff`, `mypy --strict` clean.
2. Verifier clean on all reference projects (from M3).
3. `python -m tools.check_reproducible` passes.
4. `python -m tools.vendor` run on a connected host; wheelhouse mirrored to the build host.
5. `python -m tools.gen_sbom` produces `sbom.cdx.json` and `licence-report.md` with 0 rejected.
6. Build per OS with `python -m tools.build_installer`. **Linux release builds must run inside a `rockylinux:8` container** (glibc 2.28) so they start on RHEL/Rocky 8; CI uses ubuntu-22.04 only for checks.
7. Windows: run Inno Setup on `packaging/windows-installer.iss` (per-user, no admin). Code signing only if IT provides a certificate (D-19).
8. Run `dist/harness-tool/harness-tool --selftest` on a clean VM with networking disabled.
9. Version stamped in `pyproject.toml` and `harness_tool/__init__.py`; changelog updated.

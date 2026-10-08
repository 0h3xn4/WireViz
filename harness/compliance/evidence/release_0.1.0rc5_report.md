# Release report

- PASS: Versions agree (pyproject, package, changelog) (0 s): __init__ 0.1.0rc5, pyproject 0.1.0rc5, CHANGELOG 0.1.0rc5
- PASS: Lint and types (0 s): ruff format, ruff check, mypy --strict clean
- PASS: Verifier clean on the reference projects (3 s): verifier and output verifier clean on mini3, sat15, sat15_full
- PASS: Performance targets on the stress project (68 s): stress project: generate 3.0 s (limit 10), verify 1.0 s, rules 1.2 s, outputs 40 s + check 22 s
- PASS: Soak test (3,000 random steps) (293 s): 3000 steps (1986 applied, 1014 rejected), 168 generations, 60 save/load round trips: all invariants held
- PASS: Fuzzing and security tests (300 examples per target) (71 s): 32 passed in 70.77s (0:01:10)
- PASS: Test suite and coverage gate (608 s): =========================== short test summary info ============================ | SKIPPED [1] tests/test_atomic_lock.py:59: needs POSIX non-root | 940 passed, 1 skipped in 603.94s (0:10:03)
- PASS: SBOM and licence report (21 s): 11 packages, 0 rejected
- PASS: Reproducible wheel (5 s): wheel builds identically twice
- PASS: Package (tar.gz, deb) and self-test (92 s): tarball and deb built; selftest ok
- PASS: Installed package runs (deb extracted) (4 s): extracted deb runs: selftest ok; harness 0.1.0rc5; examples present
- PASS: Configuration file and SHA-256 of the deliverables (0 s): 0.1.0rc5: 573 source files, 2 deliverables, integrity 72cdb6c82f12c9b08e1b852a3bf942e8220fb7a2da564142d2f69acab4f879c3

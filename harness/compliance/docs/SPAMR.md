# Software product assurance milestone report (SPAMR)

DRD: ECSS-Q-ST-80C Annex C. Milestone: compliance audit, phases 0 to 4 (October 2026). Status: draft, not reviewed.

## 1. Introduction, 2. Reference documents, 3. Terms
See `SPAP.md`.

## 4. Verification activities performed
- Baseline: 839 tests passed, 1 skipped (`../evidence/baseline_tests.txt`).
- After the design-checking features: 902 passed, 1 skipped (`../evidence/after_phase2b_tests.txt`).
- Run with coverage (CI style): 906 passed, 1 skipped, 1 timing test failed under instrumentation (`../evidence/after_phase2_coverage_run.txt`); see `SVR.md` section 4.7 for the follow-up.
- Generated outputs compared byte for byte before and after: 592 of 595 identical, 3 differ in the rule count and citation text (`../evidence/output_comparison.md`).
- Requirement traceability: `../traceability.csv` (65 requirements, `tools/trace.py`, test `tests/test_trace.py`).

## 5. Methods and tools
`STANDARDS.md`.

## 6. Adherence to design and coding standards
ruff and mypy strict clean on every commit of this audit. Architecture layering test passes. Adherence to design standards beyond that is by review only.

## 7. Product and process metrics
`../metrics.json` (size, complexity, coverage). On the core: 96.5 % statement and 93.0 % branch coverage in the coverage run. Largest function complexity in `core`: 67 (`generate/engine.py:_build_harness`), above the proposed limit of 30 in `STANDARDS.md`; kept, listed here.

## 8. Testing and validation
Automated tests as above. Validation by a person: usability sessions are open (`../../docs/usability/README.md`).

## 9. SPRs and NCRs
Issue-based procedure defined (`PROBLEM_REPORTING.md`). Problems found during the audit and fixed: the requirement extractor dropped two table requirements; the output differences above. No SPR numbers exist yet because the procedure starts with the first GitHub issue (action A-04).

## 10. References to progress reports
`../../CHANGELOG.md`, commits on branch `compliance/ecss-esccc-audit`.

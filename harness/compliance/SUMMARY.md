# ECSS/ESCC compliance audit: summary report

Branch `compliance/ecss-esccc-audit`. Software criticality category **C** (owner). Standards: ECSS-E-ST-40C Rev.1, ECSS-Q-ST-80C Rev.2 (the tool as software); ECSS-Q-ST-30-11C Rev.2, ECSS-E-ST-20-07C Rev.2, ESCC 3901 Issue 4 (the tool's ability to check harness designs). WireViz was not touched.

**The tool is not claimed to comply with anything.** The matrix records what exists and what evidence there is; compliance is a decision of the owner after the reviews in `OPEN_ACTIONS.md`.

## What was done
| Phase | Result |
| --- | --- |
| 0 | Requirements extracted from the five PDFs into `requirements/*.csv` (ECSS-E-ST-40C 783, ECSS-Q-ST-80C 347, ECSS-Q-ST-30-11C 219, ECSS-E-ST-20-07C 318, ESCC 3901 81 rows); criticality proposal; baseline tests |
| 1 | Gap analysis, compliance matrix, remediation plan (`gap_analysis.md`); owner approval |
| 2 | Process tools and documents; 11 new design rules, optional standard value profiles, Table 6-41 bundle factor in sizing, power/return separation in pin allocation, EMC class on wire lists and labels |
| 3 | Tests before and after; outputs compared before and after; coverage and metrics |
| 4 | Draft DRD documents in `docs/`; deviations; open actions |

## Matrix after phase 4 (`compliance_matrix.csv`)
Kind A (software), statuses are *partial* (something exists), *human*, *gap*, *na*:

| Standard | Rows | partial | human | gap | na | Baseline: partial / gap |
| --- | --- | --- | --- | --- | --- | --- |
| ECSS-E-ST-40C | 783 | 645 | 120 | 0 | 18 | 163 / 482 |
| ECSS-Q-ST-80C | 344 | 261 | 47 | 2 | 34 | 151 / 112 |

**Read "partial" with care.** For the 556 rows that are document-content requirements, "partial" means a draft document with the DRD's headings now exists; no one has checked each content requirement of the DRD against it, and no draft has been reviewed. For other rows it means the tool, a test or a procedure serves the clause; the assessment is by clause (`DEVIATIONS.md` T-11). The two remaining gaps are quality-model clauses of ECSS-Q-ST-80C 5.2.7.

Kind B (design checking), 41 requirements, after phase 2 (`assessment/design_assessment.csv`):

| Standard | Rows | Automatic | Partial | Human only |
| --- | --- | --- | --- | --- |
| ECSS-Q-ST-30-11C | 25 | 3 | 13 | 9 |
| ECSS-E-ST-20-07C | 14 | 1 | 6 | 7 |
| ESCC 3901 | 2 | 0 | 1 | 1 |

"Automatic" means the tool reports a violation by itself once the project data are supplied. Every rule is silent without its numbers and the report lists what it could not check.

## Evidence (`evidence/`)
- Tests before the audit: 839 passed, 1 skipped. After the design-check features: 902 passed, 1 skipped. Final runs: 910 passed, 1 skipped, without instrumentation and with coverage (`evidence/final_runs.md`).
- Outputs before and after for three reference projects: 592 of 595 files identical; the 3 that differ are the design rule reports (`evidence/output_comparison.md`, `evidence/output_differences.md`). Drawings and BOMs are unchanged.
- Coverage of `core`: 96.63 % statements, 93.16 % branches (`metrics.json`).
- Traceability: `traceability.csv` (65 tool requirements, `tools/trace.py`).

## Changes to the tool
Everything is opt-in or silent by default. Projects that do not use the new settings behave as before, except that the design rule report says `Rules run: 33` and cites a requirement ID in findings of the rules that serve one. See `CHANGELOG.md` and `docs/DECISIONS.md` D-131.

## Where the tool is weakest against the standards
1. No independent verification or validation, no recorded reviews, no problem reports yet (A-01, A-02, A-04).
2. Wire surface temperature under load, the partial-load factor L, bundle spacing, multipactor, bond resistances and the "family-group code" mapping cannot be checked by the tool (T-14 to T-16, checklist).
3. The security method is not agreed with anyone and no specialist has reviewed it (A-08).
4. Standards referred to by the supplied ones were not supplied, so many "shall apply" clauses are marked *human* (T-09).

## Files
`PHASE0.md`, `gap_analysis.md`, `compliance_matrix.csv`, `traceability.csv`, `metrics.json`, `DEVIATIONS.md`, `OPEN_ACTIONS.md`, `docs/` (drafts), `requirements/`, `assessment/`, `evidence/`, `templates/`.

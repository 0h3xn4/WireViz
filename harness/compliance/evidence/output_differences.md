# Differences in generated outputs during Phase 2

Each entry: commit, what changed in generated files (drawings, BOMs, reports) and why. Files not named were byte-identical to the baseline (`baseline_tests.txt`).

| Step | Changed | Why |
| --- | --- | --- |
| B-12/B-06 requirement citations | `system/drc_report.md` of mini3, sat15, sat15_full (and their digests in `tests/fixtures/outputs`); `tests/fixtures/drc/sat15.md`; `docs/RULES.md` | findings of rules that serve a standard requirement now end with `Requirement: <ID>`. Drawings, wire lists, BOMs, pinouts, labels and the model hash are unchanged. |
| B-01/B-02/B-03/B-04/B-05/B-11 rules (8 new rules, silent without their numbers) | `system/drc_report.md` of mini3, sat15, sat15_full: the line `Rules run: 22` is now `Rules run: 32`; `tests/fixtures/drc/sat15.md` the same; `docs/RULES.md` (8 new rows) | The new rules find nothing in the reference projects because none carries the optional numbers or ratings. Drawings, wire lists, BOMs, pinouts, labels, model hash: unchanged. |

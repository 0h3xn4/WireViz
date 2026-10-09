# Owner sign-off of release candidate 0.1.0rc8

Recorded on 2026-10-09 from the owner's statement in the working session: "I sign off on rc8 as the owner". The owner is the owner of the repository (GitHub account `0h3xn4`); no personal name was given, and none is invented here. The statement was made in a chat session with the developer assistant and is recorded by the assistant, not signed on paper.

## What was signed off
| Item | Value |
| --- | --- |
| Product | Harness Design Studio, release candidate `0.1.0rc8` |
| Source | merge commit `343ec0d` of pull request 21 on `master` (head of the candidate branch `6e62063`) |
| Evidence | `evidence/release_0.1.0rc8_report.md`: release check, 14 steps passed; 964 tests passed, 1 skipped, with the coverage gate and again without instrumentation; no known vulnerabilities in the 10 shipped packages |
| `harness-design-studio-0.1.0rc8-linux-x86_64.tar.gz` | SHA-256 `e67ca1f34e9cf7e1e6b78b9dd9ad05397bbceb8aa8e591738057de7c1cf34be6` |
| `harness-design-studio_0.1.0rc8_amd64.deb` | SHA-256 `84fdaf3be8cc7b4ff9f95f3df3eebab9629f046011ce6b6cf9ccc3234be27d35` |

Master has moved on since (documentation and a benchmark change only: pull requests 22, 23 and 24); the program of the candidate is unchanged.

## What this sign-off is, and is not
- It is the owner's acceptance of **this release candidate as built and tested**, as step 14 of `docs/RELEASE.md` asks of the owner.
- It is **not** a statement that the tool complies with any standard. The compliance record (`SUMMARY.md`, `compliance_matrix.csv`) is unchanged: no row says compliant.
- It was given **with the following open**, and does not close them:
  - the harness boundary rule (D-10) and the title block (D-15) are at their documented defaults, not decided by the owner;
  - the real derating and EMC values (D-11) and the approved parts list (D-12) have **not** been supplied, so every result still rests on placeholders and example parts unless a person has reviewed them (a release needs a written reason, D-135 and D-136);
  - the actions waived on 2026-10-09 (`DEVIATIONS.md` T-20 to T-30) and on 2026-10-08 (T-18, T-19) stay waived deviations: the packages are unsigned, no independent review was held, and the clean-machine installation test and the usability sessions were not done.
- Step 14 of the procedure also asks for confirmation that D-11 and D-12 have been supplied and for D-10 and D-15 to be decided. That condition is **not met**, so this sign-off does not remove `rc8` from the version: the product stays `0.1.0rc8` and the changelog keeps saying that open decisions remain. A final `0.1.0` needs either those inputs or a recorded decision by the owner to waive that condition.

## Nothing else was done
No tag, release or publication was made, and the packages were not rebuilt (the signed-off files are the ones whose checksums are listed above).

## Final release 0.1.0 (2026-10-09)

After the sign-off above the owner said "I want a final 0.1.0". The assistant then pointed out that step 14 of `docs/RELEASE.md` asks for D-10 and D-15 to be decided and D-11 and D-12 to be supplied before `rc` is dropped, and asked for an explicit sentence. The owner answered, in the same session: "I waive the step 14 condition: release 0.1.0 with D-10, D-11, D-12 and D-15 still open." That sentence is the decision; it is recorded as `DEVIATIONS.md` T-31 and `docs/DECISIONS.md` D-137.

What changes: the version is `0.1.0` (Debian `0.1.0`), the changelog, README and the other status lines no longer say "release candidate". What does not change: everything listed above as open stays open; no compliance is claimed; results are labelled as resting on placeholders and example parts; the packages are unsigned. The program is the one of rc8 (stamps differ). The release check passed (14 steps; 964 tests passed, 1 skipped, with and without instrumentation; no known vulnerabilities in the 10 shipped packages); evidence in `evidence/release_0.1.0_report.md`.

| File | SHA-256 |
|---|---|
| `harness-design-studio-0.1.0-linux-x86_64.tar.gz` | `c828d9f3fccf762d7537da55172a239eaca30bea598f9008e1336e1a3d4a6a37` |
| `harness-design-studio_0.1.0_amd64.deb` | `37422760206a803ee947b0045488da07c3bc19b811a44d0cb2b41ac0548520f7` |

All checksums are in `evidence/release_0.1.0_SHA256SUMS`.

# Software release document (SRelD)

DRD: ECSS-E-ST-40C Annex G. Version described: `0.1.0`. Status: draft, not reviewed. Released by the owner on 2026-10-09 with the engineering decisions still open; steps 12 and 13 of `../../docs/RELEASE.md` were waived (`../DEVIATIONS.md` T-27, T-30) and step 14 was given for 0.1.0 under T-31 (`../SIGNOFF.md`).

## 1 to 3, 4. Introduction, references, terms, release overview
Item: Harness Design Studio (package `harness-design-studio`). Delivered as `.deb` and `.tar.gz` for Ubuntu 24.04+. Contents and integrity values: `scf.json` and `SHA256SUMS` (`SCF.md`).

## 5. Status of the software configuration item
- **5.1 Evolution since the previous version:** `../../CHANGELOG.md`, section Unreleased.
- **5.2 Known problems or limitations:** listed at the top of the changelog entries and in `../../docs/OPEN_DECISIONS.md`: harness boundary rule (D-10) and title block (D-15) not decided; derating, EMC values and approved parts supplied by the owner (D-11, D-12); packages not signed; usability sessions and screen-reader pass not done; buses with more than two ends are skipped with a warning. From this audit: wire surface temperature under load, partial-load factor L, bundle spacing, multipactor and bond resistance are not checked (named in the rule report as *not checked*).

## 6. Advice for use
Use the example data only for learning. Fill `config/` and the parts list before relying on a check (`../../docs/CONFIG.md`, `../../docs/PLACEHOLDERS.md`). Run the review checklist for every harness.

## 7. On-going changes
Improvements from the owner's UX/UI guideline document are planned after this audit.

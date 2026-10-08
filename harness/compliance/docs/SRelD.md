# Software release document (SRelD)

DRD: ECSS-E-ST-40C Annex G. Version described: `0.1.0rc4` plus the unreleased changes of the branch `compliance/ecss-esccc-audit`. Status: draft, not reviewed. The release itself is not made: the owner has not signed off (`../../docs/RELEASE.md` steps 12 to 14).

## 1 to 3, 4. Introduction, references, terms, release overview
Item: Harness Design Studio (package `harness-tool`). Delivered as `.deb` and `.tar.gz` for Ubuntu 24.04+. Contents and integrity values: `scf.json` and `SHA256SUMS` (`SCF.md`).

## 5. Status of the software configuration item
- **5.1 Evolution since the previous version:** `../../CHANGELOG.md`, section Unreleased.
- **5.2 Known problems or limitations:** listed at the top of the changelog entries and in `../../docs/OPEN_DECISIONS.md`: harness boundary rule (D-10) and title block (D-15) not decided; derating, EMC values and approved parts supplied by the owner (D-11, D-12); packages not signed; usability sessions and screen-reader pass not done; buses with more than two ends are skipped with a warning. From this audit: wire surface temperature under load, partial-load factor L, bundle spacing, multipactor and bond resistance are not checked (named in the rule report as *not checked*).

## 6. Advice for use
Use the example data only for learning. Fill `config/` and the parts list before relying on a check (`../../docs/CONFIG.md`, `../../docs/PLACEHOLDERS.md`). Run the review checklist for every harness.

## 7. On-going changes
Improvements from the owner's UX/UI guideline document are planned after this audit.

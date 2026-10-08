# Tailoring, deviations and waivers

Every item is **proposed by the developer assistant and waits for the owner's approval**. No waiver has been granted by anyone. Approval is recorded by the owner in this file (name, date) or in a review report.

| ID | Item | Standard clause | Proposal and reason | Status |
| --- | --- | --- | --- | --- |
| T-01 | Software criticality category | ECSS-Q-ST-80C Annex D; ECSS-E-ST-40C Annex R | Category C, approved by the owner in conversation (see `PHASE0.md`). Inputs from ECSS-Q-ST-30/-40 not supplied. | approved in conversation; written record open |
| T-02 | Customer and supplier are one person | all "the customer shall ..." and "reviewed with the customer" clauses | Read as owner actions; independence rules still need a second person (A-01) | proposed |
| T-03 | DRDs reference existing documents instead of copying them; SValP and SVS combined; SSS and IRD not produced | ECSS-E-ST-40C Annexes B, C, D to P | `docs/README.md` in this folder lists each document; the owner owns the system level | proposed |
| T-04 | Flight software clauses not applicable | ECSS-E-ST-40C 5.10.2; ECSS-Q-ST-80C 6.3.5.20, 6.3.5.27 | the tool is ground engineering software | proposed |
| T-05 | No lower-level suppliers; open-source libraries handled as reused software | ECSS-Q-ST-80C 5.4 | `docs/SRF.md` | proposed |
| T-06 | No development for reuse, no hardware or service procurement, no device programming | ECSS-Q-ST-80C 7.3, 7.4, 7.5 | not applicable to this product | proposed |
| T-07 | Code coverage target | ECSS-E-ST-40C 0860135 ("TBA" for category C) | 90 % statement and branch coverage on `core`, measured; GUI outside the measure, exercised by journeys | approved by the owner, 2026-10-08 (answer given in the working session; recorded here) |
| T-08 | AI assistance treated as an automatic code generation tool | ECSS-Q-ST-80C 6.2.8 | controls: tests first, review of each diff by the owner, strict static analysis, independent output verifiers | approved by the owner, 2026-10-08 (answer given in the working session; recorded here) |
| T-09 | Standards referred to but not supplied are not assessed | ECSS-Q-ST-30, -40, -10, -10-09, -20; ECSS-M-ST-40; ECSS-Q-ST-60-15; ECSS-S-ST-00-01 | clauses that only say "shall apply" a missing standard are marked *human* with the reason | proposed |
| T-10 | Scope of kind-B assessment | ECSS-E-ST-20-07C clause 5 (EMC test methods); ESCC 3901 clauses 5 to 12 (manufacturing and qualification tests) | judged not to be harness design requirements; `requirements/overrides.csv` gives the reason per row | proposed |
| T-11 | Clause-level assessment of kind A | all rows of ECSS-E-ST-40C and ECSS-Q-ST-80C | a requirement inherits the assessment of its clause unless it has its own row in `assessment/process_overrides.csv` | proposed |
| T-12 | Reviews may be combined | ECSS-E-ST-40C 5.3.3 to 5.3.6 | small project; owner decides (A-02) | proposed |
| T-13 | Standard values are optional profiles | rule "never invent standard values" (D-131) | values are taken from the supplied standards, opt-in, cited, still placeholders until reviewed | decided by the owner (approval of the plan); values accepted as a whole by the owner on 2026-10-08 (A-17), without a value-by-value check by a second person; each project's config file keeps its own `placeholder` flag |
| T-14 | Partial loading factor L (Table 6-42) not applied | ECSS-Q-ST-30-11C 6.32.5.2 | the tool does not know which wires carry current together; the bundle check uses L = 1, which is conservative; the report says so | proposed |
| T-15 | Wire surface temperature is not computed | ECSS-Q-ST-30-11C 6.32.4 a.2, b, c | only the ambient temperature is compared with the part limit; a thermal analysis outside the tool is needed; the report says so | proposed |
| T-16 | "Family-group codes" not mapped | ECSS-Q-ST-30-11C 6.11, 6.12, 6.32 | profile values are applied to all connectors and wires of the project; what the supplied text states and what a parts engineer must enter: `FAMILY_GROUP_MAPPING.md` (A-16) | proposed |
| T-17 | A bundle is every wire of one harness | ECSS-Q-ST-30-11C 6.32.5.1 | conservative; bundles that run together across harnesses are not combined | proposed |
| T-18 | Default branch is not technically protected | ECSS-Q-ST-80C 5.6.1.3 (see `docs/STANDARDS.md`) | CI is not a required check; a failing run blocks merging by the owner's practice only. | waived by the owner (2026-10-08); the owner gave no reason, none is recorded |

## Waivers
One granted: T-18 (default branch not protected), waived by the owner on 2026-10-08 without a stated reason. No other waiver requested or granted. A finding of the design rule check can be waived inside a project with a written reason (existing mechanism); that is a design waiver and not a waiver of the standards for the tool.

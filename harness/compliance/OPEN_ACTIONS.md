# Open actions for people

Things the tool and its documents cannot do for themselves. None of them was done by the developer assistant, and no document claims it. Each action names the requirements it blocks.

| ID | Action | Who | Blocks (gap, clauses) |
| --- | --- | --- | --- |
| A-01 | Appoint an independent verifier and validator (a person who did not write the design, code or tests) and let them review the verification and validation evidence | owner | G-10; ECSS-E-ST-40C 5.6.2, 5.8.2; ECSS-Q-ST-80C 6.3.5.19 |
| A-02 | Hold the reviews (SRR, PDR, CDR, QR, AR, test readiness, delivery, security) with record and RIDs; agree whether they are combined | owner | G-11; ECSS-E-ST-40C 5.2.5, 5.3.3 to 5.3.6, 5.4.2, 5.4.4, 5.6.3, 5.6.4, 5.7.3; ECSS-Q-ST-80C 6.1.5, 6.3.7 |
| A-03 | Organisation, resources, training records, risk register, process assessment, audits | owner | G-12; ECSS-Q-ST-80C 5.1, 5.2.3, 5.3, 5.7 |
| A-04 | Start using problem reports as GitHub issues; form the nonconformance review board; name the customer interface | owner | G-04; ECSS-Q-ST-80C 5.2.5, 5.2.6 |
| A-05 | Review and approve the plans and standards (SPAP, SDP, STANDARDS, CMP, CRITICALITY including the component classification) | owner | G-03, G-06, G-14; ECSS-Q-ST-80C 6.3.4.4, 6.2.1.5 |
| A-06 | Protect the default branch so that CI must pass before merging | owner (repository settings) | ECSS-Q-ST-80C 5.6.1.3 |
| A-07 | Software dependability and safety analysis of the C components, using the severity categories of ECSS-Q-ST-30 and the rules of ECSS-Q-ST-40 (not supplied) | owner / safety engineer | G-03; ECSS-Q-ST-80C 6.2.2.2 to 6.2.2.9 |
| A-08 | Security: choose the method, have a person review the analysis, sign the packages, watch vulnerabilities of dependencies at each release | owner | G-09; ECSS-E-ST-40C 5.9.4, 5.11 |
| A-09 | Add one run of the test suite without instrumentation to the release check and keep its result | developer (after owner decision) | ECSS-Q-ST-80C 6.2.3.8 |
| A-10 | Generate the component table and the requirement-to-component trace for the SDD | developer | ECSS-E-ST-40C 5.5.2, Annex F section 6 |
| A-11 | Name the maintainer organisation, support period, migration and retirement plans | owner | G-18; ECSS-E-ST-40C 5.10 |
| A-12 | Hold the usability sessions and the screen-reader pass | owner with users | VAL-07; ECSS-E-ST-40C 5.6 |
| A-13 | Accept the outputs for a real harness | owner | VAL-08; ECSS-Q-ST-80C 6.3.7 |
| A-14 | Confirm the coverage target (90 % on `core`) and the exclusion of the GUI | owner | E-40C 0860135 (agreed in conversation; needs recording) |
| A-15 | Confirm the controls on AI assistance as accepted (tests first, review of each diff, strict static analysis) | owner | G-17; ECSS-Q-ST-80C 6.2.8 |
| A-16 | Map the standard's family-group codes to the tool's part classes | owner / parts engineer | ECSS-Q-ST-30-11C 6.11, 6.12, 6.32 |
| A-17 | Review the values of the standard profiles and set `"placeholder": false` when accepted; supply D-10, D-11, D-12, D-15 | owner | D-131 |
| A-18 | Supply the standards that are referred to and were not supplied, if their clauses are to be assessed: ECSS-Q-ST-30, -40, -10, -10-09, -20, ECSS-M-ST-40, ECSS-Q-ST-60-15 | owner | many "refer to" clauses |

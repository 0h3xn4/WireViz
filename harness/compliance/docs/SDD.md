# Software design document (SDD)

DRD: ECSS-E-ST-40C Annex F. Status: draft, not reviewed. The design is described in `../../docs/ARCHITECTURE.md` (written as a proposal and since built as described, with the changes listed at its top) and `../../docs/DECISIONS.md` (one decision per row, D-01 to D-131). This SDD gives the DRD structure and points to them.

## 1 to 3. Introduction, references, terms
See `SDP.md`.

## 4. Software design overview
- **4.1 Static architecture:** layers `core` (no GUI, CLI or network imports), `cli`, `gui`, `resources`. Components of `core`: `model` (strict immutable pydantic models of the logical and physical layer), `io` (folder format, atomic saves, migration, recovery), `commands.py` (transactions, undo and redo), `generate/` (segmentation, pin allocation, sizing, lengths, mass, naming, explanation), `drc/` (design rules, standard rules, report, helper process worker), `outputs/` (tables, drawings, system diagrams, exports, stamp, independent verifier), `vcs/` (release, locks, diff, baselines, change log), `verify.py` (independent verifier of the wiring), `edit.py`, `checks.py`, `imports.py`, `kicad.py`, `library_import.py`, `configcheck.py`, `standard_profiles.py`, `templates.py`, `starter.py`, `samples.py`.
- **4.2 Dynamic architecture:** a single process with a Qt event loop; generation runs in a worker; the design rule check runs in a helper process (D-128); the GUI only changes the project through `EditorController` and `History.execute`.
- **4.3 Behaviour:** generation is a pure function of the design (`plan_generation`) that returns operations, a report and a provenance record; the user previews and applies the plan as one undoable step.
- **4.4 Interfaces context:** `ICD.md`.
- **4.5 Long lifetime software:** the project format carries a schema version and migrations keep the original files.
- **4.6 Memory and processing budget:** stress project of 200 units, 2 000 interfaces, 20 000 wires: generation under 10 s (REQ-PERF-02), editor edits under 100 ms (REQ-PERF-01); measured with `tools/bench_gui.py`, `tools/bench_generate.py`.
- **4.7 Design standards:** `STANDARDS.md`.

## 5. Software design
- **5.1 General, 5.2 Overall architecture:** as 4.1. Mandatory design rules (determinism, verifier independence, no network) are tested where stated in `STANDARDS.md`.
- **5.3 and 5.4 Components:** per component the identifier is the module path; the purpose and function are in the module docstring (each module starts with one); dependencies follow the layering rule; interfaces are the public functions listed in `__all__` where defined. A full component-by-component table is not reproduced here: the module docstrings are the source and a generated table is open work (action A-10).
- **5.5 Internal interface design:** transactions (`Op`: `Put`, `Delete`, `SetConfig`, `DeleteConfig`), the `Delta` signals of the controller, the chunked messages of the helper process.

## 6. Requirements to design components traceability
Requirement to verifying file: `../traceability.csv`. Requirement to component: the "Verified by" column of `../../docs/REQUIREMENTS.md` names the test files, which import the components. A direct requirement to component table does not exist (action A-10).

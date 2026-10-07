# Audit of October 2026

A full review of the tool by six independent reviewers (data layer; generation and KiCad; rules, outputs and change control; the editor's usability; command line and importers; documentation, packaging and CI). Each finding was reproduced before it was reported, and each fix got a regression test (`tests/test_audit_*.py`, plus additions to `tests/test_installers.py` and `tests/test_licences.py`).

## What was wrong, and is fixed

**Data loss and integrity**
- A new unit could reuse the ID of a renamed unit's connectors and overwrite them.
- Baselines and change log entries could be deleted; design fields of an interface carried by a released harness (current, redundancy) could be edited; a released harness set back to draft by hand was not reported.
- The recovery journal dropped what could not be loaded, so a restored project could overwrite the original folder.
- Two baselines whose revision names differ only in unusual characters shared one file.
- A number like `1e999` loaded as infinity and crashed the save.
- Two processes could both take over a stale project lock; a lock was readable half-written. Commands on the command line did not take the lock at all.
- A project folder that was a link to somewhere else was read and written through.
- A second error on an object that already had one was waved through; undoing the first config change did not remove it; waivers survived the deletion of their object.

**Wrong results**
- A released interface could be wired a second time when a change moved it into another group; locked generated pins were stranded; the explanation of released wires vanished on every regeneration; a harness number was used up on every run when a group made no wires; naming templates without a number hung generation or produced duplicate IDs; zone names containing `|` collided.
- The release gate ignored errors on the interfaces a harness carries (current over contact) and trusted the output manifest without checking the files; mass and the release gate disagreed with the tables about the length of wires whose length comes from segments.
- The output verifier compared counts only; it now compares values (wire list, mass and length, tests, labels, YAML, workbook, JSON).
- KiCad: unnamed nets of sub-sheets became signals, byte order marks and UTF-16 were refused with a wrong message, pin numbers and net names that cannot be IDs crashed the import, too many pins for the part were accepted.

**Tracebacks and unsafe input**
- Ordinary mistakes on the command line (missing or binary files, long names, unwritable folders) ended in a traceback; special files such as `/dev/zero` could exhaust memory; damaged workbooks crashed the import; exports wrote through a linked `outputs` folder.
- Decimal commas and semicolon files were mishandled (an unquoted `1,5` silently imported as `1`).

**Editor**
- The diagram had too little room on common screens, a toast's Undo could undo the wrong change, failed saves raised exceptions, messages were cut off and piled up, wording was jargon, disabled buttons did not say why, a hand-made harness could not be deleted, many findings of one kind filled the Problems list.

**Packaging and documentation**
- `uninstall.sh` deleted the whole install folder; the launcher broke in folders with spaces; the package contained development tools and no licence texts; the 22.04 build recipe could not work (Python 3.11); the prototype tests never ran in CI; the documentation had a dozen stale statements.

## What remains open

- The verifier's own scope: it checks the wires against the interfaces; wire gauge, length and shield checks are the design rule check's job. It is not a proof against every error.
- Multi-drop interfaces (more than two units) are still not generated (D-116).
- Segregation of interface classes in the default per-connector-pair mode is reported, not enforced: classes that share a connector pair share a harness, so give the separated class its own connector (the rule check `category-mixed` reports the physical mixing).
- A pin typed by hand without a lock and without an interface is reserved but its signal is not matched to interfaces; use a fixed pin (KiCad import) for pins that must be found by name.
- The cross-platform items are out of scope (D-110, Ubuntu only).
- A 22.04 release build tested on a clean machine (no Docker daemon in the review environment), usability sessions, a manual screen-reader pass, and the owner's decisions D-10 and D-15 are still needed.

# Harness design review checklist

Copy this next to your design and tick it off for each harness before you release it. The tool checks most of this for you; the list says where to look.

Project: ____________  Harness: ______  Revision: ___  Reviewer: ____________  Date: ____________

## Before the review
- [ ] `harness check DIR` prints no error.
- [ ] `harness generate DIR` changes nothing (the harnesses are up to date).
- [ ] `harness verify DIR` finds no error.
- [ ] `harness export DIR` ran after the last change, and **Harness plans** says the outputs are up to date.

## Look at
- [ ] **Problems** tab: no error, every warning fixed or waived with a reason you agree with.
- [ ] **To-do** tab is empty or every item is understood.
- [ ] No interface shows *auto-filled*: a person confirmed every connector the tool chose.
- [ ] `harness config DIR`: nothing is missing; every file is reviewed and no longer marked `placeholder`.
- [ ] Every wire has a gauge (none *pending*) and a length.
- [ ] The **Why** tab explains each choice you did not expect.
- [ ] Parts: every used part is approved in your parts list.

## Drawings and lists
- [ ] Drawing: connectors, pins and signals match the unit documents.
- [ ] Wire list, pinouts and BOM agree with the drawing.
- [ ] Mass and length tables look plausible.
- [ ] Test tables list the limits your programme requires.

## Release
- [ ] The release comment says what this revision is for.
- [ ] After the release: exported again, drawings show *released*, the change log has the entry.

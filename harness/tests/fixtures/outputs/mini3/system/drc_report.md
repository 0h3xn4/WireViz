<!-- harness-tool 0.1.0rc4 model 6c35cd91012b -->
# Design rule check: mini3 (example data)

Model hash: `6c35cd91012b`. Rules run: 22.
Open: 0 error(s), 3 warning(s), 4 note(s). Waived: 0.

Placeholder configuration in use: derating, emc, generation, segmentation, segregation, titleblock. Results that depend on it are marked as not checked.

## Warnings (3)

- **Part EX-DSUB-9-F is not approved yet but is used (8 place(s))** (`part-unapproved.EX-DSUB-9-F`)  
  Only approved parts may be built into flight hardware. To fix it: Approve the part in the parts list, or choose an approved one.
- **Part EX-DSUB-9-M is not approved yet but is used (4 place(s))** (`part-unapproved.EX-DSUB-9-M`)  
  Only approved parts may be built into flight hardware. To fix it: Approve the part in the parts list, or choose an approved one.
- **Part EX-WIRE-TWISTED-SHIELDED is not approved yet but is used (4 place(s))** (`part-unapproved.EX-WIRE-TWISTED-SHIELDED`)  
  Only approved parts may be built into flight hardware. To fix it: Approve the part in the parts list, or choose an approved one.

## Not checked / note (4)

- **EMC class separation was not checked: the EMC rules are still a placeholder** (`unchecked-config.emc`)  
  A rule that needs a number nobody has entered cannot say anything, and silence must not look like a pass. To fix it: Ask the responsible engineer to fill in the placeholder (see docs/PLACEHOLDERS.md).
- **Shield grounding was not checked against a concept: it is still a placeholder** (`unchecked-config.grounding`)  
  A rule that needs a number nobody has entered cannot say anything, and silence must not look like a pass. To fix it: Ask the responsible engineer to fill in the placeholder (see docs/PLACEHOLDERS.md).
- **Power, signal and sensitive-analog separation was not checked: the category pairs are still a placeholder** (`unchecked-config.separation`)  
  A rule that needs a number nobody has entered cannot say anything, and silence must not look like a pass. To fix it: Ask the responsible engineer to fill in the placeholder (see docs/PLACEHOLDERS.md).
- **Spare pins were not checked: the required fraction is still a placeholder** (`unchecked-config.spare-pins`)  
  A rule that needs a number nobody has entered cannot say anything, and silence must not look like a pass. To fix it: Ask the responsible engineer to fill in the placeholder (see docs/PLACEHOLDERS.md).

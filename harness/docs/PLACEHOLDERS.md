# Placeholder values an engineer must fill in

The tool never invents numbers from standards. These shipped values are placeholders; `harness validate` reports `placeholder_config` while any remain. Set `"placeholder": false` in the file once reviewed.

| File (`config/`) | What is needed | Owner | Needed by |
| --- | --- | --- | --- |
| `derating.json` | contact current factor, bundle derating, max ambient temperature, max voltage drop, spare pin fraction (all `null`) | EE / program standard (ECSS-Q-ST-30-11 or program rules) | M3 |
| `emc.json` | EMC classes and their rules (`null`) | EMC engineer | M3/M4 |
| `segregation.json` | which category pairs must be separated (`null`); the nominal/redundant and pyro rules are on by default | EE | M3/M4 |
| `segmentation.json` | confirm the harness boundary rule (default: per connector pair, merge within a zone) | Owner (DECISIONS D-10) | M3 |
| `titleblock.json` | company title block layout | Owner (D-15) | M5 |

Library: every starter part is `unverified: true`, `approval: "pending"`, with no mass or ratings. Import or enter real parts before any result is trusted.
Interface types: starter types are `unverified`; impedance, EMC class and default gauge are `null`.

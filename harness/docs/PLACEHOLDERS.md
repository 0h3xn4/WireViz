# Placeholder values an engineer must fill in

The tool never invents numbers from standards. These shipped values are placeholders; `harness validate` reports `placeholder_config` while any remain. Set `"placeholder": false` in the file once reviewed.

| File (`config/`) | What is needed | Owner | Needed by |
| --- | --- | --- | --- |
| `derating.json` | contact current factor, bundle derating, max ambient temperature, max voltage drop, spare pin fraction (all `null`) | EE / program standard (ECSS-Q-ST-30-11 or program rules) | M3 |
| `emc.json` | EMC classes and their rules (`null`) | EMC engineer | M3/M4 |
| `segregation.json` | which category pairs must be separated (`null`); the nominal/redundant and pyro rules are on by default | EE | M3/M4 |
| `segmentation.json` | confirm the harness boundary rule (default: per connector pair, merge within a zone) | Owner (DECISIONS D-10) | M3 |
| `titleblock.json` | company title block layout | Owner (D-15) | M5 |

The templates (`harness templates FOLDER`) contain a set of **demo values** for these files so that wire sizing, voltage drop and test limits can be seen working. They are not engineering data and the files stay `"placeholder": true` (D-129). Replace them with your programme's values.

Library: every starter part (Micro-D 9, 15, 21, 25 and 31 pin, RJ45, SMA, wires, sleeving, labels, and some older D-sub, MDM, circular and TNC parts) is `unverified: true`, `approval: "pending"`, with no mass or ratings. Import or enter real parts before any result is trusted.
Interface types: starter types are `unverified`; impedance, EMC class and default gauge are `null`.

## Additions in M3 (all defaults are `null`; generation reports what is missing)
| File (`config/`) | Key | Effect while `null` |
| --- | --- | --- |
| `derating.json` | `ampacity_a_by_awg` (e.g. `{"20": amps}`), `bundle_derating`, `temperature_derating`, `max_voltage_drop_v` | wire gauge stays "pending" |
| `generation.json` | `conductor_resistivity_ohm_m` | voltage-drop check skipped, gauge pending |
| `generation.json` | `power_signal_gap_pins` | 0 used, noted in the provenance |
| `generation.json` | `service_loop_m` | 0 used; lengths exclude service loops |
| `generation.json` | `mass_margin_fraction` | no margin shown |
| `generation.json` | `shield_end_a`, `shield_end_b` | shield grounding concept left floating |
| `generation.json` | `wire_part_by_construction` | example library parts (not qualified) |
Library parts need `mass_g` and `mass_per_m_g` for a complete mass; otherwise the result lists what is missing.

## Additions in M4
| File (`config/`) | Key | Rules that stay silent (and say "not checked") while `null` |
| --- | --- | --- |
| `derating.json` | `contact_current_factor` | current over contact |
| `derating.json` | `ampacity_a_by_awg`, `bundle_derating`, `temperature_derating` | current over wire |
| `derating.json` | `max_voltage_drop_v` (with `generation.conductor_resistivity_ohm_m`) | voltage drop |
| `derating.json` | `spare_pin_fraction` | spare pins low |
| `generation.json` | `shield_end_a`, `shield_end_b` (grounding concept) | shield unterminated, shield wrong end |
| `segregation.json` | `category_pairs_to_separate`, e.g. `[["power", "analog"]]` | category mixed |
| `emc.json` | `conflicting_class_pairs`, e.g. `[["A", "B"]]` (format chosen by the tool; the owner may change it) | EMC mixed |
Part ratings: `ratings.contact_current_a` on connector parts (key name set by `derating.contact_rating_key`).

## Additions in M5
| File (`config/`) | Key | Effect while `null` |
| --- | --- | --- |
| `generation.json` | `test_continuity_max_ohm`, `test_isolation_min_mohm`, `test_isolation_voltage_v` | test tables show "TBD (placeholder)" |
| `titleblock.json` | `fields` (order and choice of title block fields; D-15) | default field list; date, author, checker, approver show "-" until M6 |
| library | `mass_g`, `mass_per_m_g` on parts | mass tables say which data is missing |

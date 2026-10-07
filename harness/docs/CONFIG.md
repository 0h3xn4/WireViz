# Configuration reference

Rules live in `config/*.json` inside the project, not in code. Every file has `"placeholder": true` until an engineer has reviewed it; set it to `false` afterwards. Values shown as `null` are placeholders: results say so and the affected checks say *not checked*. Which standard to take values from is for you to decide; the tool ships none.

## `segmentation.json`
| Key | Meaning |
| --- | --- |
| `mode` | how interfaces are grouped into harnesses: `per_connector_pair` (default), `per_unit_pair`, `per_zone_pair` |

## `segregation.json`
| Key | Meaning |
| --- | --- |
| `forbid_nominal_with_redundant` | nominal and redundant chains never share a harness or connector (default true) |
| `forbid_pyro_with_other` | pyro lines never share a harness or connector (default true) |
| `category_pairs_to_separate` | list of category pairs that must not share a harness, for example `[["power", "analog"]]` |

## `derating.json`
| Key | Meaning |
| --- | --- |
| `contact_current_factor` | fraction of the contact rating that may be used |
| `bundle_derating` | factor for wires in a bundle |
| `temperature_derating` | factor for the maximum ambient temperature |
| `max_ambient_temperature_c` | recorded for reference |
| `max_voltage_drop_v` | allowed voltage drop over a wire path |
| `spare_pin_fraction` | share of pins that must stay spare |
| `ampacity_a_by_awg` | current in amperes per gauge, for example `{"20": 5.0}` |
| `contact_rating_key` | which entry of a connector part's `ratings` is the contact current (default `contact_current_a`) |

## `generation.json`
| Key | Meaning |
| --- | --- |
| `wire_part_by_construction` | library wire part used for each construction (example parts by default) |
| `default_gauge_awg` | gauge when none is decided |
| `service_loop_m` | extra length added at each end |
| `conductor_resistivity_ohm_m` | for the voltage drop calculation |
| `power_signal_gap_pins` | empty pins between power and signal pins |
| `mass_margin_fraction` | margin added to masses |
| `shield_end_a`, `shield_end_b` | grounding concept: `backshell_360`, `pigtail` or `floating` for each end |
| `test_continuity_max_ohm`, `test_isolation_min_mohm`, `test_isolation_voltage_v` | limits printed in the test tables |

## `emc.json`
| Key | Meaning |
| --- | --- |
| `classes` | EMC classes (format is yours to define) |
| `conflicting_class_pairs` | pairs of EMC classes that must not share a harness, for example `[["A", "B"]]` |

## `naming.json`
Name patterns for harnesses, connectors, wires, shields, branch points and segments, for example `W{n:03d}`. IDs are stable once released.

## `titleblock.json`
| Key | Meaning |
| --- | --- |
| `fields` | which title block fields appear, in order: `project`, `harness_id`, `title`, `revision`, `date`, `author`, `checker`, `approver`, `sheet`, `status` |

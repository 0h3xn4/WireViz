# Configuration reference

Rules live in `config/*.json` inside the project, not in code. Every file has `"placeholder": true` until an engineer has reviewed it; set it to `false` afterwards. Values shown as `null` are placeholders: results say so and the affected checks say *not checked*. Which standard to take values from is for you to decide; the tool ships none. `harness config DIR` lists what is missing and checks what is set (ranges, table order); see IMPORTS.md.

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

## Optional values from the supplied standards (D-131)

None of these is set by default. `harness config DIR --apply-profile ecss-q-st-30-11c` (and `ecss-e-st-20-07c`) fills the ones that are still unset and keeps what you set; each value cites the requirement it comes from in the command output and in `src/harness_tool/core/standard_profiles.py`. The file stays `"placeholder": true` until you review it. A rule that needs one of these values or a part rating stays silent without it, and the rule `unchecked-config` says what was not checked.

### `derating.json`, additional keys
| Key | Meaning | Source (requirement ID) |
| --- | --- | --- |
| `connector_voltage_factor_withstand` | working voltage as a fraction of the connector's dielectric withstanding voltage (0.25) | ECSS-Q-ST-30-11_0140051 |
| `connector_voltage_factor_rated` | working voltage as a fraction of the rated voltage (0.75); the lower of the two limits applies | ECSS-Q-ST-30-11_0140051 |
| `connector_temperature_margin_c` | degrees below the maximum rating (30) | ECSS-Q-ST-30-11_0140051 |
| `rf_power_factor` | RF power as a fraction of the rating (0.75); recorded, no rule yet (no RF power on interfaces) | ECSS-Q-ST-30-11_0140058 |
| `wire_voltage_factor` | working voltage as a fraction of the wire's rated voltage (0.5) | ECSS-Q-ST-30-11_0140213 |
| `wire_temperature_margin_c` | degrees below the manufacturer's maximum for the wire surface (50); only the ambient part is checked (`max_ambient_temperature_c`), self-heating needs a thermal analysis | ECSS-Q-ST-30-11_0140213 |
| `bundle_factor_by_count` | table: number of wires to factor K. A bundle uses the next listed count; replaces `bundle_derating` in sizing and in the rule `bundle-current`. The single wire current is your `ampacity_a_by_awg`. | ECSS-Q-ST-30-11_0140218 |
| `partial_load_factor` | table L for partly loaded bundles; recorded, not applied (the report says so) | ECSS-Q-ST-30-11_0140220 |
| `max_mating_cycles` | mating cycles a connector may be used for (50) | ECSS-Q-ST-30-11_0140056 |

### `generation.json`, additional key
`power_return_gap_pins`: unassigned contacts left between the supply and the return pin of a power interface (1). Default (unset): they sit side by side, as before. ECSS-Q-ST-30-11_0140052.

### `emc.json`, additional keys
| Key | Meaning |
| --- | --- |
| `shield_bonding` | `both_ends_backshell`: every shield must be bonded at both ends through a 360 degree backshell (ECSS-E-ST-20-07_0080041, 0080042) |
| `same_class_one_bundle` | `true`: interfaces of one EMC class between two units should run in one harness (ECSS-E-ST-20-07_0080035) |

### Part ratings used by the rules (keys of `ratings` in the parts library)
`rated_voltage_v`, `dielectric_withstand_v`, `max_temp_c`, `mating_cycles` (connectors and wires as stated above). A part without the rating the rule needs is listed under *not checked*. The part fields `manufacturer` and `specification` are used by the rules `connector-manufacturer` and `wire-specification`.

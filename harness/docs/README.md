# Documentation map

## Learn and use

| Document | For | What it gives you |
| --- | --- | --- |
| [`INSTALL.md`](INSTALL.md) | everyone | Install on Ubuntu, check it works, uninstall, build from source |
| [`LEARNING_PATH.md`](LEARNING_PATH.md) | newcomers | The whole route in nine steps, with the example or template for each and how you know you are done |
| [`GETTING_STARTED.md`](GETTING_STARTED.md) | newcomers | A guided tour with real output: example project, generate, read problems, export, fill in values, release |
| [`CONCEPTS.md`](CONCEPTS.md) | newcomers | The words and the mental model, in ten minutes |
| [`HOWTO.md`](HOWTO.md) | engineers | Recipes for single tasks: import, KiCad, release, revisions, Git, CI |
| [`guide/USER_GUIDE.md`](guide/USER_GUIDE.md) | everyone | The guide that opens with **F1** in the app: screen, modes, shortcuts, glossary |
| [`CLI.md`](CLI.md) | scripters | Every `harness` command and option (generated from the program) |
| [`CHEATSHEET.md`](CHEATSHEET.md) | everyone | One page: the loop, the data imports, release, shortcuts, the folder layout, the words |
| [`FAQ.md`](FAQ.md) | everyone | Questions and troubleshooting |

## Reference

| Document | What it says |
| --- | --- |
| [`RULES.md`](RULES.md) | Every design rule: what, why, how to fix, severity (generated) |
| [`CONFIG.md`](CONFIG.md) | Every key of `config/*.json` |
| [`PLACEHOLDERS.md`](PLACEHOLDERS.md) | Which engineering values are still placeholders, who owns them |
| [`IMPORTS.md`](IMPORTS.md) | Importing interfaces, parts, lengths, engineering values |
| [`KICAD.md`](KICAD.md) | Taking unit connector pinouts from a KiCad netlist |
| [`OUTPUTS.md`](OUTPUTS.md) | Every output file and its limits |
| [`FILE_FORMAT.md`](FILE_FORMAT.md) | The project folder format |

## Examples and templates

`harness new --list` shows the example projects, `harness templates FOLDER` copies the import templates, demo values, CI scripts and the review checklist. What each file is: [`../src/harness_design_studio/resources/examples/templates/README.md`](../src/harness_design_studio/resources/examples/templates/README.md). Screenshots of the app are in [`ux/qt/`](ux/qt/).

## Decisions, requirements, status

| Document | What it says |
| --- | --- |
| [`SPEC.md`](SPEC.md), [`REQUIREMENTS.md`](REQUIREMENTS.md), [`UX.md`](UX.md) | What the tool must do and how it should feel |
| [`UX_GUIDELINES_REVIEW.md`](UX_GUIDELINES_REVIEW.md) | The owner's UX/UI guidelines, point by point: done, new, not applicable, open |
| [`DECISIONS.md`](DECISIONS.md), [`OPEN_DECISIONS.md`](OPEN_DECISIONS.md) | What was decided, and what still needs an owner |
| [`PLAN.md`](PLAN.md), [`demos/`](demos/) | The plan and the note from each milestone |
| [`AUDIT.md`](AUDIT.md), [`SECURITY.md`](SECURITY.md) | The October audit and the security review |
| [`../compliance/SUMMARY.md`](../compliance/SUMMARY.md) | The ECSS/ESCC compliance audit: matrix, gaps, deviations, open actions |
| [`RELEASE.md`](RELEASE.md) | The release checklist |
| [`usability/`](usability/) | The usability test kit |

## For developers

[`../CLAUDE.md`](../CLAUDE.md) (commands, layout, conventions), [`ARCHITECTURE.md`](ARCHITECTURE.md), [`DECISIONS.md`](DECISIONS.md).

Some files are **generated** and a test fails when they are stale: `RULES.md` (`python -m tools.gen_rule_docs`), `CLI.md` (`python -m tools.gen_cli_docs`), the HTML of the user guide (`python -m tools.build_guide`), and the example projects (`python -m tools.build_examples`).

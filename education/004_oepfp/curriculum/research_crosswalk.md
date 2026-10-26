# Research source crosswalk

AuthorityEffect: None.

Every in-scope research file and canonical Level Engine source appears in [the JSON inventory](research_inventory.json) with its byte hash,
owner, classification, route, and evidence reason. The headless receipt identifies which labs ran.

The inventory includes the Level Engine package runtime, orchestration, governance, historical evidence, and Lean ownership roots.

Reading routes provide navigation; they do not assert every file was executed or fully reviewed.

An execution receipt applies only to the notebook, manifest, and inventory hashes recorded in that receipt.

| Family | Files | Route |
| --- | ---: | --- |
| controllers | 3 | [Lesson](400_researchers/04_source_bound_research_audit.ipynb) |
| domain | 44 | [Lesson](400_researchers/04_source_bound_research_audit.ipynb) |
| infrastructure | 14 | [Lesson](400_researchers/04_source_bound_research_audit.ipynb) |
| level_engine/domain | 1 | [Lesson](400_researchers/04_source_bound_research_audit.ipynb) |
| level_engine/entrypoint | 1 | [Lesson](400_researchers/04_source_bound_research_audit.ipynb) |
| level_engine/evidence | 2933 | [Lesson](400_researchers/04_source_bound_research_audit.ipynb) |
| level_engine/governance | 81 | [Lesson](400_researchers/04_source_bound_research_audit.ipynb) |
| level_engine/lean | 55 | [Lesson](400_researchers/04_source_bound_research_audit.ipynb) |
| level_engine/operations | 73 | [Lesson](400_researchers/04_source_bound_research_audit.ipynb) |
| level_engine/reach-prerequisite | 131 | [Lesson](400_researchers/04_source_bound_research_audit.ipynb) |
| level_engine/runtime | 772 | [Lesson](100_novices/04_cycle_repair.ipynb) |
| level_engine/runtime-tests | 18 | [Lesson](400_researchers/04_source_bound_research_audit.ipynb) |
| level_engine/shared-exact-rational | 5 | [Lesson](400_researchers/04_source_bound_research_audit.ipynb) |
| level_engine/tests | 4 | [Lesson](400_researchers/04_source_bound_research_audit.ipynb) |
| research-root | 3 | [Lesson](400_researchers/04_source_bound_research_audit.ipynb) |
| tests | 30 | [Lesson](400_researchers/04_source_bound_research_audit.ipynb) |
| tools | 7 | [Lesson](400_researchers/04_source_bound_research_audit.ipynb) |
| use_cases | 38 | [Lesson](400_researchers/04_source_bound_research_audit.ipynb) |

## Classification rules

- **lab-backed:** a named lesson directly imports code or reads a fixture; check the execution receipt.
- **reading-only:** a narrative, reference, or image routed to a lesson; no execution claim.
- **historical:** retained review, receipt, or archive; no current replay claim.
- **open:** source, notebook, fixture, or binary without a direct lab in this sequence.

Generated caches, environments, compiled targets, and notebook checkpoints are excluded by explicit directory names.
Refresh the inventory after research files change. Its totals describe one filesystem snapshot.

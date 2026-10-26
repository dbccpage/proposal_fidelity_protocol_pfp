# The pfp package

[`pfp/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/pfp)
is the main Python package: it assembles prompts, runs bounded turns, checks
proposals, scores obstructions and writes receipts. It is large (about 3,000
Python files, 690 test modules) and is organised by layer.

`CONTEXT.md` in the package is its engineering glossary; the
[Core concepts](Core-Concepts.md) page is the newcomer version.

## Layers

| Folder | Role |
| --- | --- |
| `domain/` | Pure rules and value types, no I/O. Sub-packages cover exact arithmetic, cohomology and homology, finite gauge checks, the S(n) and MSS-N tower, normal forms, rewriting, packets and provenance, claim hygiene, stages and curriculum |
| `use_cases/` | Application logic built from domain pieces (listed below) |
| `controllers/` | Coordinators for a turn, a prompt, a code change and the overall protocol |
| `entrypoints/` | Command line (`cli/`), HTTP API (`api/`), a small web workbench (`web/`), and runners for the braid tournament, retraction benchmark and empirical gates |
| `infrastructure/` | Adapters, catalogs, normal-form resources, pilot runners, replay of saved sources, architecture fitness checks |
| `type_register/` | Inventory of types and their unresolved semantic overlaps |
| `formal/`, `regimes/`, `packet_schemas/`, `fixtures/` | Formal sources, regime declarations, packet schemas and test fixtures |
| `tests/` | Unit, property and architecture tests |

## Key use cases

| Module | What it does |
| --- | --- |
| `pfp_prompt.py` | Assembles an answer-free PFP prompt with no file or provider access |
| `pfp_proposal.py` | Checks a bounded proposal and returns answer-free repair feedback |
| `pfp_stages.py` | Small-stage policy; a checker defect never authorises more generation |
| `execute_stage_pipeline.py` | Runs the staged pipeline |
| `pfp_derivation_loops.py` | Bounded research loops; an early acceptance does not cut requested exploration short |
| `scoring.py` | Discrete coboundary scoring: the obstruction measures |
| `clarification.py` | Checks a missing-input residual against the task's stated requirements |
| `abstention_governor.py` | Decides when to abstain or report impossibility |
| `code_change.py` | Code-change proposals and their patch gate |
| `verify_contracts.py` | Verifies contracts, schemas and normal forms |
| `verify_glyph_reply.py` | Checks a glyph-calculus reply end to end and emits the receipt |
| `finite_gauge_workbench.py` | Bounded search over Paper 002's finite sign grammar |
| `prompt_artifact.py` | Compiles, renders and stores prompt artifacts and elimination receipts |

## Rules the code follows

- **Result tracks.** Operations return `Success` or `Failure` values and compose
  with `bind` and `map`, rather than raising for expected failures.
- **Re-entry refusal.** A candidate rejected by a frozen checker set cannot be
  re-evaluated by the same set in the same generation; only an inconclusive
  result may retry within its budget (`gate.py`).
- **Strict descent.** A retraction turn is admitted only if it does not increase
  the obstruction.
- **Exact arithmetic.** Checks use exact rationals, not floats.

## Status

The package was imported from an earlier repository and its imports still use
the older package name, so it does not yet run from this repository as-is. The
paper packages under `papers/` carry their own self-contained code, which does
run; see [Getting started](Getting-Started.md).

Related papers: [000](Paper-000.md), [001](Paper-001.md), [004](Paper-004.md),
[005](Paper-005.md), [008](Paper-008.md).

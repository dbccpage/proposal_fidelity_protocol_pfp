# PFP Pilot Schema and Type Definitions

**AuthorityEffect:** None.  
**Catalog Schema:** `pfp.pilot-types.v1`  
**Governing Documents:** Proposal Fidelity Protocol (PFP v0.2), Single Prompt Standard (SPK-001)

## Overview

This directory houses the machine-readable JSON/YAML Schema specifications and type definitions corresponding to every YAML asset deployed across the PFP pilot estate (`omega_engine_woland/tests/pilots/pilot_*`).

Required fields and closed enums in the `*.schema.yaml` files follow the Pydantic models in `omega_engine_pfp/domain/types/`. Those models emit JSON Schema draft 2020-12 from `model_json_schema()`. Fields typed as an enum unioned with `str` stay open in the schema so a non-enum label still validates.

## Directory Contents

| File | Type Identifier | Description |
|---|---|---|
| `pilot_types.yaml` | `pfp.pilot-types.v1` | Canonical catalog of pilot data types and dialect subtypes. |
| `pilot_spec_v1.schema.yaml` | `pfp.pilot-spec.v1` | Schema for pilot benchmark specifications (`spec.yaml`). |
| `seed_prompt_v1.schema.yaml` | `pfp.seed-prompt.v1` | Schema for dialect seed prompts (`seed.yaml`, `seed_rewrite_01..10.yaml`). |
| `p_star_prompt_v1.schema.yaml` | `pfp.p-star-prompt.v1` | Schema for SPK-001 $P^*$ prompts and templates (`p_star.yaml`, `p_star_rewrite_01..10.yaml`, `prompt_template.yaml`). |
| `rewrite_test_plan_v1.schema.yaml` | `pfp.rewrite-test-plan.v1` | Schema for test plan matrices (`testplan.yaml`). |
| `test_spec_v1.schema.yaml` | `pfp.test-spec.v1` | Schema for encapsulated test specifications (`tests/test_XX/test_spec.yaml`). |
| `pilot_response_v1.schema.yaml` | `pfp.pilot-response.v1` | Schema for encapsulated model responses (`tests/test_XX/response.yaml`). |
| `pilot_comparison_results_v1.schema.yaml` | `pfp.pilot-comparison-results.v1` | Schema for comparative benchmark analytics (`results/comparison_results.yaml`). |

## Dialect Subtype Taxonomy

Each `pfp.seed-prompt.v1` and `pfp.p-star-prompt.v1` instance belongs to one of eleven canonical presentation formats:

1. `plain-text`: Standard conversational phrasing (`seed.yaml`)
2. `math-formal`: Formal algebraic system with LaTeX notation (`seed_rewrite_01.yaml`)
3. `word-problem`: Narrative word problem with identical arithmetic (`seed_rewrite_02.yaml`)
4. `codebook-cipher`: Alphanumeric token cipher without dictionary (`seed_rewrite_03.yaml`)
5. `ascii-tableau`: Fixed-width layout / ASCII grid (`seed_rewrite_04.yaml`)
6. `matrix-form`: Matrix equation $A \cdot x = b$ (`seed_rewrite_05.yaml`)
7. `reverse-polish`: Stack-based RPN operator sequence (`seed_rewrite_06.yaml`)
8. `s-expression`: LISP-style nested list syntax (`seed_rewrite_07.yaml`)
9. `emoji-substitution`: Glyph/symbol replacement for variables (`seed_rewrite_08.yaml`)
10. `interleaved-noise`: Equations embedded within distractor narrative (`seed_rewrite_09.yaml`)
11. `proof-style`: Deductive theorem proving specification with hypotheses (`seed_rewrite_10.yaml`)

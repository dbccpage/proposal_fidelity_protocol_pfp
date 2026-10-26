---
name: auto-antiskill
description: "Mine IDE dialogue corrections into provenance-bound candidate anti-skills. Use after repeated model mistakes or explicit corrections. Do not use it to activate a detector, admit a skill, or make a truth verdict."
version: "0.1.0"
authority_effect_ceiling: None
anomalon:
  status: Draft
  admission: pending
---

# Auto Antiskill

**AuthorityEffect: None.** Mine candidates; never admit, execute, or certify them.

## Workflow

1. Preserve the raw dialogue and compute its digest. Do not load the old epistemic-immunity archive as authority.
2. Run `scripts/auto_antiskill.py segment-dialogue`. Use explicit line bounds when a transcript includes tools or build output.
3. Review correction episodes and add a proposed failure code, invariant, evidence references, protected fields, and at least one clean counterexample to separate annotation data. The model's annotation remains a proposal.
4. Run `mine-candidates`. Identical episode IDs deduplicate; incomplete annotations emit nothing.
5. Write resulting candidates only under `.agents/antiskills/ooutwire/`.
6. Record the learning through the existing autoskill episode/resolve pipeline. Frequency and confidence never grant admission.

Read [admission-boundary.md](references/admission-boundary.md) before recommending promotion.

## Boundaries

- Never edit `.agents/antiskills/admitted/`, the compiled registry, validators, fixtures, or evaluation receipts.
- Never convert a phrase pattern, scalar score, density matrix, or recurrence count into a truth verdict.
- Require distinct context keys and held-out negative controls before human admission review.
- Treat detector, repair proposal, verification, and packetization as separate typed operations.
- Treat learning and promotion as directed refinement, never an invertible equivalence.
- Refuse unsupported transcript formats rather than guessing speaker or tool boundaries.

## Constraints

Required: [EVIDENCE_BASED, NO_HARDCODED_SECRETS, and MAINTAIN_TESTS](../../../_shared/constraints.md). This draft never self-certifies or bypasses admission and Git gates.

## Outputs and tests

Outputs: `omega.antiskill.segmented-dialogue.v1` and `omega.antiskill.candidate-set.v1`. Both are inert proposal records with `AuthorityEffect: None`.

Focused tests: `omega_engine/_tests_unit/test_prompt_civilization_dialogue.py`, `test_prompt_civilization_registry.py`, `test_prompt_civilization_evals.py`, and `test_prompt_civilization_skill_boundaries.py`.

## Related Skills

`omega-prompt` consumes only the empty v0 runtime registry. `autoskill` records learning episodes; `lib-skill-admission-hygiene` governs any later admission review.

# Epic: Grammar validity and conditional-distribution evaluation

**Epic ID:** `EPIC-OE-OEPCIV-PRIOR-ART-001`
**AuthorityEffect:** None
**Status:** `RESEARCH_HOLD`
**Design readiness:** bounded experiment specified; production contract and source assumptions remain open.
**System:** [pciv](../../../../pciv)
**Registry relationship:** `DIRECT_REGISTRY_ASSIGNMENT`; 54 file rows directly assigned to this system.
**Owner:** maintainers of `pciv`; specialist roles below.
**Date:** 2026-10-10

## Problem and source-derived experiment

Syntactic validity and distribution fidelity are different objectives in constrained generation.

Specify a tiny grammar with an enumerable token distribution; compare unconstrained rejection, prefix masking and grammar-aligned sampling.

This is a proposed transfer from the linked source material. A relevance score of 5 is discovery metadata. Source titles, abstracts and transcription summaries are not adopted theorem statements or implementation receipts.

## Prior art and existing plan boundary

- [01_picard_parsing_incrementally_for_constrained_auto.md](../../../research_papers/library/01_generation_control/01_picard_parsing_incrementally_for_constrained_auto.md) — `direct`; SHA-256 `2b29a9d1faf2f1a1bd08d8c5ef6e9cc2535464347bf0bf8fe9cc3adc62c1d654`.
- [02_grammar_aligned_decoding.md](../../../research_papers/library/01_generation_control/02_grammar_aligned_decoding.md) — `direct`; SHA-256 `5e89e7bf7549599333dfb65d6b8a5cbbbd2722d3f16fd1ab759a521883c553ca`.

Use the [estate epic index](../README.md) to resolve adjacent owners and the [design-review reconciliation](../../../receipts/epic_design_review_20261010.md) for current OEWAS/Adversary limits. This epic adds the experiment above; existing suite plans continue to own their broader architecture, migrations and release work.

## Contract to settle before implementation

- Input: frozen source revision and byte digest, finite task instance, explicit assumptions, observation basis, checker identity and budget.
- Output: typed result with candidate and evidence digests, separate diagnostic and authorization status, residual obligations and next action.
- Refusal: malformed input, missing oracle, mismatched source/candidate bytes, or undeclared authority produces an explicit refusal or open residual.
- Recovery: retain the failed candidate and dissent; re-evaluate changed bytes under the same run budget. Never reinterpret an earlier receipt as checking new bytes.
- Open design decisions: choose the existing owning production port, freeze its value-object schema and error codes, define checker trust and the source-to-local assumption map. Resolve these before declaring implementation readiness.

## Dependencies and bounded delivery

- Specify source assumptions and checker trust configuration before implementation readiness.
- Bind prospective acceptance tests to an existing production port; record a real mutation failure before GREEN.

1. Researcher specifies the finite instance and assumption map; Defect Hunter records counterexamples and scope objections.
2. DEV_MGR chooses the existing system port and implementation target; Syntax Prefilter checks input shape and Scope Guard fixes budget and owned paths.
3. QA_MGR and Inspector run the production-bound negative and positive controls in batches of at most three test files; repair attempts are bounded to three. Native compilation uses `cargo ... -j 1`.
4. Adversary adjudicates from bound checker evidence; DOC_MGR checks links/encoding and BUILDER checks the theoretical minimum. Preserve all unresolved objections. Output is a SoftwareQaReceiptV1 only after its production schema and writer are bound.

## Theoretical minimum and proposed TDD acceptance

| Element | Required experiment |
| --- | --- |
| INVARIANT | Candidate, source, assumptions and checker refer to the same finite task; diagnostic evidence grants no authority. |
| BREAK | Replace conditional probabilities with renormalized local masking probabilities. |
| WITNESS | Enumerated complete-sequence probabilities must reveal the distribution drift. |
| MUTATION | Apply the BREAK to the selected production path after its owner is resolved; require the negative control to turn RED, restore the implementation, then rerun GREEN. No production mutation is claimed executed by this draft. |

Examiner Class 1: positive finite example. Class 2: malformed input. Class 3: changed-source/candidate transplant. Class 4: the counterexample above. Class 5: production-bound replay and mutation. All five are **proposed acceptance tests** until recorded against the chosen implementation; mock-only Class 0 evidence is insufficient.

The implemented planning check is `py -3.12 -m product_planning_office.use_cases.prior_art_epic_audit`. It checks source and navigation custody, not the experiment's correctness. The experiment's production test command remains a required design decision owned by this system.

## Claim discipline

- What it supports: a linked, bounded experiment and explicit readiness blockers for this system.
- What it does not support: implementation completion, source-theorem adoption, general mathematical correctness, publication, or an authority grant.
- Narrowest defensible claim: the experiment has a concrete input/output boundary and a falsifier; its production binding remains open.
- Next test needed: run the planning audit above, then settle the production port and author the Class 1–5 acceptance tests before implementation.

## Obstruction review and TDD test plan

**Plan status:** proposed behavior tests; no implementation completion is implied. The [requested TDD skill](../../../../.agents/skills/ext-mattpocock-tdd/SKILL.md) currently contains an operadic signature and authority fence only. The concrete RED/GREEN sequence below is this plan's specification, not an invented additional skill instruction.

**Existing public seam:** [MutationOperatorRegistryV1.submit / admit](../../../../pciv/use_cases/operator_custody.py). Operator custody is present. A decoder/probability observation port is a provider dependency; grammar-aligned decoding does not certify truth or unchanged distribution by itself.

**Bounded behavior:** Bind a grammar-constrained operator candidate to its source and independently observed output distribution.

**Independent oracle:** Use a finite two-choice grammar with known unconstrained probabilities; enumerate valid strings and the renormalized conditional probabilities separately.

| Ordered slice | RED observation to require | Minimal GREEN and refactor boundary |
| --- | --- | --- |
| 1: finite positive control | Add one externally observable assertion for the bounded example above. If it already passes, record it as a characterization control; do not claim a new RED. | Reuse the existing seam and its value objects. Add only behavior needed for the first unmet assertion, then refactor with that test green. |
| 2: adversarial control | Admit a syntactically valid but unsupported proposition, or equate grammar membership with preserved probability distribution; the semantic/distribution control must fail. | Enforce the actual missing predicate at the owning seam. Keep the valid control green and preserve the typed refusal. |
| 3: replay and recovery | Replay the original grammar and seed record, retaining syntactic validity, semantic support and distribution results in separate fields. | Restore the original implementation after mutation, rerun the same controls, then refactor without changing the oracle, input bytes or claimed scope. |

**Proposed test file:** `pciv/tests/test_prior_art_grammar_distribution.py`. It is a future acceptance target, not an existing suite or a recorded pass. Invoke one slice/test at a time before extending this file; keep batches to at most three files/crates and Rust compilation at `-j 1`.

```powershell
py -3.12 -m pytest pciv/tests/test_prior_art_grammar_distribution.py -q
```

**Decisive mutation target:** the linked existing seam is the integration target; select and record the exact predicate/function at implementation time. The mutation must remove the adversarial check above and make its behavior test fail. Source presence is verified here; execution of that mutation and RED/GREEN recovery is not claimed. A missing semantic layer remains a blocking dependency, not a passing mock substitute.

**Review-loop exit:** this epic can leave planning review only after source assumptions, public inputs/outputs, refusal behavior, oracle and dependency owner are explicit. Broad research residuals above retain RESEARCH_HOLD. QA must bind test command, interpreter/compiler version, candidate SHA and mutation evidence to real receipts before any implementation claim. Re-enter the full epic walk whenever source or acceptance semantics change.

Cross-epic ownership and retained custody follow the [integration decision](../../decisions/adr_20261010_epic_integration_ownership.md).

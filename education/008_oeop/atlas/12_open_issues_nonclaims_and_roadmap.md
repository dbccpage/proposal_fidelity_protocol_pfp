# Open Issues, Nonclaims, and Roadmap

## Priority zero: evidence and safety

1. Normalize parsed composition slots to validated nonnegative integers and add an
   end-to-end parser/adapter test.
2. Make SQLite catalog and journal persistence semantically roundtrip-safe before
   post-load verification is called integrity verification.
3. Replace operation-ID-only catalog digests with canonical, domain-separated
   commitments and mutation tests.
4. Enforce estate-root containment and reject path traversal.
5. Bind every security-relevant HMAC field; name the primitive accurately and
   document its threat model.
6. Repair outbox no-subscriber, partial-fanout, retry, and concurrent-dispatch
   semantics.
7. Restore canonical reference-operad unit closure after symmetric expansion and
   make every reported validator error fatal.
8. Remove scalar-to-contractive promotion and enforce one residual vocabulary.
9. Fix Skill Compiler budget exception authorization and promotion against the
   current register before allowing mutation.
10. Path and owner honesty for the colour vocabulary and the OEEIS port.
    Missing colour paths stay on the record, and immune decisions stay on
    `ImmuneScreenPort`. See [chapter 23](23_plan_oewas_consolidation_oeeis_and_demo_integration.md).

## Priority one: one model, explicit validation

1. Select canonical owners for operation, operad, quotient, receipt, result/error,
   and persistence concepts; make other surfaces adapters.
2. Validate uniqueness, cross-references, unit signatures, tree boundaries, slot
   coverage, child operation identities, and expected boundaries.
3. Reject fabricated lifecycle evidence and all-zero digest sentinels in admitted
   state.
4. Resolve workflow operations against a catalog and add completion/dead-task
   analyses beyond DAG acyclicity.
5. Make all registry, profile, trace, and promotion writes locked, atomic,
   post-validated, and receipted.
6. Preserve full event payloads and define stream version/concurrency rules.
7. Consolidate application result/error and unit-of-work protocols.

## Priority two: measured research experiments

1. Formalize the accepted declaration grammar and test constrained decoding against
   parser/schema acceptance.
2. Add a W3C-PROV-inspired lineage graph for one bounded compile path.
3. Benchmark candidate workflow memory and workflow search behind evaluation and
   human admission gates.
4. Evaluate DSSE/asymmetric attestations only against a written cross-party threat
   model.
5. Explore planar normal forms for structural-equivalence testing without claiming
   execution semantics.

## Reproduced operad and resolver defects (201dc8d, 2026-10-15)

Each item below was reproduced on `origin/main` at `201dc8d` with a probe script or a test run.
Paths are relative to `omega_engine_workflows_agents_skills/skill_operad/`. These are historical findings, not a current completion register. The current native/runtime repairs and remaining evidence limits are in [chapter 27](27_spec_op_resolver.md) and [chapter 29](29_guide_woland_operad_management_ladder.md). The original repair plan is workstream I1 of
[EPIC-OE-OEWAS-012](../../../../omega_engine_product_planning_office/plans/epics/oewas/epic_oe_oewas_012_woland_operad_binding_and_management_ladder_pilot_plan.md).

Resolver ([chapter 27](27_spec_op_resolver.md)):

1. `resolver/resolver.py:294-301`: `run` does not catch an exception raised by a detector
   (`:296`) or an executor (`:301`). A `ZeroDivisionError` from an executor escapes instead of
   returning a typed refusal.
2. `resolver/resolver.py:296`: `run` trusts `anti.slot`. The slot check (`OI7_ANTI_OP`) runs only in
   the separate `op_inventory` checker, so an inventory with `slot: 3` raises `IndexError`.
3. `resolver/resolver.py:97-122`: the run receipt records output digests only. It has no input
   digest, inventory digest, tool or interpreter version, timestamp or cost, and nothing writes it
   to disk. Two runs on two different clean files give byte-identical receipts.
4. `resolver/resolver.py:291-293`: `compose` uses its inputs as a multiset, but `run` maps each
   port name to one value. A tree with two leaves of one colour would get the same value twice.
   Latent: no current minimal tree has two such leaves.
5. `resolver/executors.py:70-72`: each detector rescans the files, so a run reads each file four
   times (three detectors and `sfh.scan`). A file that changes between the reads can pass the check
   and fail the use, or the reverse.

Other operad implementations:

6. `domain/planar.py:76-79,132-139`: `ColoredOp.compose` treats any arity-1 op named `id_*`
   with matching colours and an empty residual as an identity and drops it, whatever its body does.
7. `domain/planar.py:85-93`: a composite whose outer op has arity above 1 and that receives a
   single tuple argument unpacks it. A composite called with `("a",)` evaluated its first inner op
   on `"a"`, not on `("a",)`.
8. `domain/planar.py:66,81,111`: the outer residual is added twice, once inside the composed body
   and once by the composite's own `__call__`. Already noted in
   [chapter 08](08_reference_operad_and_skill_compiler.md); still present.
9. `domain/operad.py:135`: composite ids are `f"{o}_o{slot}_{i}"`, so `(a ∘1 b) ∘1 e` and
   `a ∘1 (b ∘1 e)` receive the same id although their sources differ.
10. `domain/operad.py:164-176`: `ensure_symmetric_closure` adds every permutation of every op of
    arity above 1 and ignores the `equivariant` flag; the 10-ary op alone would add 3,628,799 ops.
    `coloured_operad.py:419-425` checks the flag, so the two implementations disagree.
11. `domain/operad.py:155` and `coloured_operad.py:405`: `permute` names its result by appending
    the permutation, so `permute(permute(f, σ), τ)` yields `f_pσ_pτ` and not the op for the
    composed permutation. This is not a group action, and equivariance of `∘_i` is not checked.
12. `coloured_operad.py:376-391` writes the unit compositions into the composition table, and
    `validate_units` (`:446-454`) reads them back. The unit line printed by `validate_operad.py` is
    therefore not evidence for the unit laws.
13. `quotient_operad.py:20,22` uses bare imports. Importing
    `omega_engine_workflows_agents_skills.skill_operad.quotient_operad` raises
    `ModuleNotFoundError: No module named 'evidence_observations'`.

Registry data and tests:

14. `associativity_laws` is empty in both copies of `composition_matrix.json`. The associativity
    tests compare colour lists on hand-written signatures; no property-based or exhaustive test
    checks associativity, units or equivariance on values.
15. The primary `.agents/skill_operads/composition_matrix.json` has a composition whose outer op
    `rip-papers` is not an op or a skill, and lists two synthesized meta-skills
    (`meta-intelligence-transmutation-engine`, `meta-woland-hermetic-evidence-verifier`) with no
    skill directory and no signature op.
16. `validate_operad.py` exits 1 with 26 residual-honesty errors (13 signature rows, 13 SKILL.md
    frontmatter fields claiming `contractive` without a certificate).

## Stable nonclaims

- The composition layer is not a symmetric operad and has no equivariance proof.
- Structural association is not behavioral equivalence.
- Residual rows do not prove contraction, quotient admissibility, or promotion.
- Capability slices are permissions, not proven sub-operads.
- Graph validation is not execution or workflow soundness.
- The regex fence parser is not a complete CommonMark parser.
- Current SQLite storage is not a lossless event-sourced aggregate.
- The outbox does not establish exactly-once delivery.
- HMAC does not establish independent asymmetric signer attribution.
- Four-host byte parity does not establish semantic migration.
- A generated or retrieved skill/workflow never auto-acquires admission or
  authority.
- HoTT terminology in the reference tree is a software metaphor, not a formal HoTT
  development.
- Research citations do not validate this repository.

## Historical-document disposition

Earlier numbered documents and duplicated images remain tracked for provenance.
They are superseded as current operational guidance because they mix implemented,
historical, and proposed states; contain stale counts and paths; and overstate
parser, persistence, operad, execution, signing, and production properties.

Retirement, deletion, or image replacement should be a separate governed change.
Until then, link readers to the atlas and label each historical artifact with its
evidence ceiling.

## Definition of done for a future production claim

A production claim requires, at minimum:

- one canonical model and versioned compatibility adapters;
- complete persistence roundtrip and concurrency tests;
- full typed-refusal coverage for untrusted input;
- a defined executor/effect model with authorization checks;
- workflow completion and recovery semantics;
- durable subscriber-specific outbox delivery;
- threat-modeled provenance and authentication;
- exact-SHA replay receipts and mutation coverage;
- operational readiness/integrity probes;
- explicit human approval for authority-bearing cutover.

Until those conditions are independently evidenced, `AuthorityEffect: None` and
shadow mode remain the correct system-level description.

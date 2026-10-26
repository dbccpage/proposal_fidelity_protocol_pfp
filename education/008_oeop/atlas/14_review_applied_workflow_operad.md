# OEAS Applied Workflow Operad — Python Implementation Review

Date: 2026-08-20  
Scope: proposed `OEASWorkflowOperad` plus the eight supplied Python modules  
AuthorityEffect: None  
Review mode: implementation and mathematical-honesty review; no source files modified

## Verdict

The applied correspondence is the correct architecture:

| Operadic object | OEAS meaning |
| :--- | :--- |
| Colour | Typed artifact or port boundary |
| Generating operation | Skill invocation |
| Composite operation / tree | Workflow |
| Algebra / interpreter | Runtime realization |
| Agent binding | Partial implementation of generators |
| Policy layer | External admissibility gate |
| Evaluation receipt | Evaluation record |

The current Python does not yet implement that whole table. It supplies useful value objects and signature composition, but the proposed application does not import against the supplied foundation, does not enforce the admitted colour universe or agent capability slice, does not build a workflow tree, cannot recursively evaluate a composite, and does not emit an evaluation receipt.

This is not a reason to remove the rich mathematics. It is a reason to give every mathematical level an honest implementation status.

## What should remain

Keep the full tower:

1. Coloured and planar operads for typed composition.
2. Planar trees for workflow syntax and provenance.
3. Algebras for runtime realization.
4. Modules for agents, environments, or resource-bearing participants that are not closed algebras.
5. Monoidal and symmetric enrichment for lawful interchange and concurrency.
6. Quadratic relations, cooperads, bar–cobar constructions, and Koszul duality for relations, deformation, and obstruction analysis.
7. Little-disks and E_n structures for graded locality, interchange, and coherent parallel composition.

The implementation must distinguish `Defined`, `Represented`, `Computed`, and `Verified`. A rich mathematical object may be present as an honest symbolic representation before its algorithms are complete.

## Critical implementation findings

### OEAS-IMP-001 — Proposed application does not import

Severity: Blocker

The proposed code imports:

```python
from ..foundation.colored_operad import PlanarColoredOperad
```

The supplied module is `coloured_operad.py` and defines only `ColouredOperad`. There is no `PlanarColoredOperad` class. Resolve the spelling and introduce the explicit planar subtype or rename the existing class after removing its unsupported symmetric claims.

### OEAS-IMP-002 — `OEAS_ADMITTED_PORT_COLOURS` is not an admission fence

Severity: Blocker

`OEASWorkflowOperad.__post_init__` seeds eight colours, but `ColouredOperad.add_operation` silently inserts every input and output colour appearing on an operation (`coloured_operad(1).py:43-49`). Therefore this succeeds:

```python
register_skill("x", ["Unadmitted"], "MintedAuthority")
```

For OEAS, operation registration must reject undeclared colours. Generic mathematical construction may expose a separate explicit `extend_colour_universe` operation, but application registration must be closed by default.

### OEAS-IMP-003 — Some admitted colour names collapse artifact kind into epistemic status

Severity: Blocker for the authority boundary

`Proof`, `Audit`, `Receipt`, and `Ledger` are unsafe as unrestricted skill outputs. If a skill can declare that it returns `Proof`, later colour matching can treat a proposal as a proof without any admission event.

Prefer distinctions such as:

```text
ProofCandidate      -> AdmittedProof        only by an external admission port
AuditCandidate      -> AuditFinding         only by the evaluator
ReceiptPayload      -> EvaluationReceipt    only by the interpreter/host
LedgerProposal      -> LedgerSnapshot        only by the ledger authority
```

The operad may transport these artifacts. It must not promote them.

### OEAS-IMP-004 — Agent capability binding is dead data

Severity: Blocker

`AgentCapabilitySlice` is never accepted by `create_agent_interpreter`, `register_skill`, composition, or evaluation. Its `licensed_skills` and port restrictions have no effect.

The capability slice should restrict generator-action registration and evaluation, not the mathematical existence of operations. Use typed `AgentId`, `OperationId`, and `OperadColour` values instead of strings.

### OEAS-IMP-005 — Workflow composition discards the workflow tree

Severity: Blocker

`compose_workflow` returns a flattened `Operation`, registers it beside generators, and never uses the imported `PlanarTree`. The resulting object retains only a constructed string ID and flattened signature. It loses:

- The root and child relationship.
- Generator provenance.
- Evaluation order.
- A stable structural witness.
- The ability to evaluate recursively.
- The ability to distinguish a generator from a derived composite.

Return an immutable `OperadicTerm` or `PlanarTree`. Do not register composites as generators. If composites are cached, place them in a separate content-addressed composite store.

### OEAS-IMP-006 — The algebra cannot interpret a workflow

Severity: Blocker

`OperadAlgebra.evaluate_action` evaluates one registered operation only (`algebra_over_operad(1).py:40-52`). It has no tree evaluator. A composite can run only if an unrelated callable is manually registered for its synthesized string ID, which bypasses the algebra-composition law.

Required operation:

```text
evaluate(tree, external_inputs, capability_slice, policy_decision)
    -> EvaluationOutcome
```

Evaluation must recursively evaluate children and then apply the root generator action. Identity evaluation must use structured operation kind, never an ID prefix.

### OEAS-IMP-007 — No evaluation receipt exists

Severity: Blocker against the stated correspondence

The proposed table promises an `EvaluationReceipt`, but no supplied or proposed class records:

- Tree/content hash.
- Interpreter and agent identity.
- Generator versions.
- Input and output artifact references.
- Child evaluation receipts.
- Policy decision reference.
- Completion/refusal status.
- Exceptions or residuals.
- Replay classification.

A receipt can be deterministic as a canonical record even when an agent action is not deterministic. Do not claim deterministic execution merely because the receipt serialization is deterministic.

### OEAS-IMP-008 — Identity recognition is forgeable by string prefix

Severity: Blocker

`OperationId.is_identity` and `OperadAlgebra.evaluate_action` recognize identity operations by `id_` prefix. Worse, `evaluate_action` returns its argument for any unknown `id_*` string before confirming that the operation exists in the operad (`algebra_over_operad(1).py:42-46`).

Represent operation kind structurally:

```text
OperationKind = Identity(colour) | Generator | Composite(term_hash)
```

An arbitrary skill ID must never acquire unit semantics from its spelling.

### OEAS-IMP-009 — The associativity witness proves only signature coincidence

Severity: Blocker to the word “associativity”

`verify_sequential` compares only the flattened input tuple, output, and arity (`associativity_witness(1).py:87-102`). Given the implementation of `partial_compose`, that result is structural bookkeeping. It does not show that the two composites are equal operations or have equal interpretations.

This can honestly be named `SequentialCompositionShapeWitness`. A true strict associativity witness needs one of:

1. Equality of canonical operadic terms modulo the associativity rewrite.
2. Equality in a presented operad using registered relations and a certified normalizer.
3. Equality of interpretations for a bounded test domain, explicitly labeled as bounded evidence rather than proof.

The same problem affects the unit witness. Parallel associativity is documented but not implemented.

### OEAS-IMP-010 — `PlanarTree` cannot construct or graft the advertised tree

Severity: Blocker

`PlanarTree(root=f)` defaults to `children=()`. `graft(0, subtree)` then always raises because it indexes `len(children)`, not `root.arity` (`planar_tree(1).py:44-47`). The class also permits arbitrary child-tuple lengths and does not validate existing child colour boundaries.

Normalize a corolla to one open leaf per root input:

```text
children = (OpenLeaf(c_0), ..., OpenLeaf(c_n))
```

Do not use `None` when an explicit `OpenLeaf(colour)` value can preserve typing. Also distinguish a root-child index from a global external-leaf path. Current grafting only addresses immediate root slots, despite saying “i-th leaf.”

## Foundation findings

### Colours and signatures

1. `OperadColour` accepts leading/trailing whitespace but preserves it, so `"State"` and `" State "` are distinct. Reject noncanonical input or normalize explicitly.
2. Unicode normalization is unspecified, which undermines reproducible content addressing.
3. `OperadSignature` accepts a `Sequence`; passing the string `"Code"` as `inputs` creates four colours. Reject `str` and `bytes` as input sequences.
4. Arbitrary objects are converted using `str`. Accept only `OperadColour | str` and raise `TypeError` otherwise.

### Operations

1. Duplicate operation IDs silently overwrite previous definitions in `ColouredOperad.add_operation`.
2. `partial_compose` accepts operations that need not belong to the operad.
3. Composite IDs are ad hoc strings. Delimiters inside user IDs can make them ambiguous, and the two associative bracketings intentionally produce different IDs.
4. `is_equivariant: bool` is not a symmetric-group action. A symmetric operad needs an action mapping an operation and permutation to another operation, together with action and compatibility laws.
5. `permute_inputs` is available even when `is_equivariant` is false.

For the initial OEAS application, an explicitly planar operad should omit symmetric action rather than approximating it with a Boolean.

### Coloured operad aggregate

1. The class claims to be symmetric but implements only planar signature substitution.
2. Identities are generated by string convention and are not verified if an operation with the same ID already exists.
3. The returned `operations` dictionary is a copy, which is safe for mutation, but the application uses it as an untyped lookup service and receives raw `KeyError` for missing skills.
4. Mathematical extension of the colour set and OEAS admission should be separate APIs.

### Algebra

1. `set_carrier` accepts unknown colours and silently overwrites carriers.
2. `register_action` validates existence only; it cannot validate the callable signature.
3. `evaluate_action` checks arity but not membership of inputs in their carriers or output in the target carrier.
4. `Any` is acceptable for a scaffold, but it means this is not runtime type enforcement.
5. Action functions may use time, randomness, network, or external state. Purity and replay class must be declared separately.

### Witness statuses

Do not place evidence precision and law result in one enum. Recommended product:

```text
ComputationStatus = Completed | Refused | NotComputed | BudgetExceeded | InternalError
LawResult         = Satisfied | Violated | NotApplicable
EvidenceKind      = ExactStructural | Symbolic | BoundedExample | ShapeOnly
```

Do not catch every exception and classify it as a mathematical violation. An implementation defect is not evidence that an operad law is false.

## Rich mathematical layers

### Koszul duality

Keep this module, but the present `compute_koszul_dual` must not keep that name. It copies generator signatures, appends `_dual`, discards every relation, and returns an operad with an empty relation set (`koszul_duality(1).py:43-62`). It computes neither the dual generator representation nor `R_perp`.

Honest immediate alternatives:

```text
build_koszul_dual_skeleton() -> ProposedQuadraticDual
compute_koszul_dual()        -> NotComputed(MissingPairingOrOrthogonalComplement)
```

Add ground ring/field, grading, weight, finite-dual hypotheses, basis/pairing, suspension/sign convention, and relation-space validation before returning `Computed`.

`QuadraticRelation` must also verify equal term/coefficient counts, known generators, common profile, weight two, and a declared coefficient domain.

### Little disks, Ass, Com, and Lie

Keep this module, but name the current objects presentations or generator skeletons.

1. `build_associative_operad` creates one binary generator and an identity; it does not impose associativity or construct all arity components of `Ass`.
2. `build_commutative_operad` does not impose associativity or a genuine symmetric action.
3. `build_lie_operad` imposes neither antisymmetry nor Jacobi. A Boolean cannot encode the sign representation.
4. `LittleDisk` performs no dimension, center-length, positive-radius, containment, or pairwise-disjointness validation.
5. `D_1`, `Ass`, `A_infinity`, `E_1`, and their homology/equivalence relationships must not be collapsed into literal equality in implementation documentation.

Rich mathematics is preserved by representing these distinctions, not by giving a one-generator scaffold the name of the completed operad.

## Recommended object model before Rust

```text
OperadColour
OperationProfile(inputs, output)
GeneratorId
Generator(profile, metadata)
Identity(colour)
OperadicTerm = Identity | Generator | PartialComposite
PlanarTree / TypedTree
PlanarColoredOperad(colours, generators)
AgentCapabilitySlice(agent_id, permitted_generators, port constraints)
OperadAlgebra(carriers, generator_actions)
PolicyDecisionRef
EvaluationOutcome = Completed | Refused | Failed | NotComputed
EvaluationReceipt
```

Key boundary:

```text
mathematical membership
    != agent capability
    != policy admissibility
    != successful evaluation
    != witness admission
    != authority
```

## Recommended repair order

1. Introduce a real `PlanarColoredOperad` and make the application importable.
2. Make OEAS colours closed and reject unadmitted profiles.
3. Replace identity-prefix logic with `OperationKind`.
4. Separate generators from immutable composite terms/trees.
5. Repair `PlanarTree` construction and typed grafting.
6. Implement recursive algebra evaluation over trees.
7. Apply `AgentCapabilitySlice` at action binding and evaluation.
8. Introduce external policy-gate input and an evaluation receipt.
9. Rename signature witnesses honestly; later add relation-aware normalization.
10. Mark Koszul and little-disks implementations as symbolic skeletons until their actual obligations are computed.

## Rust-port locks

Do not mechanically port the current Python classes. Freeze these first:

1. Newtypes for `AgentId`, `GeneratorId`, `ColourId`, `TermHash`, and policy/receipt references.
2. `enum OperationKind` rather than string-prefix conventions.
3. `enum OperadicTerm` retaining the complete composition tree.
4. `BTreeMap` or explicitly sorted serialization for deterministic hashes.
5. Typed `Result<T, Refusal>` rather than `KeyError`, `ValueError`, and `TypeError` as the public contract.
6. Separate mathematical law result, computation status, and evidence kind.
7. A trait for generator interpretation and a separate recursive evaluator for terms.
8. Explicit effect/replay classification for each action.
9. No operation, agent, algebra, or policy object may mint witness admission or authority.

## Minimum acceptance tests

1. Unknown input or output colour is refused by OEAS registration.
2. Duplicate generator ID is refused without mutation.
3. A skill named `id_anything` is not treated as an identity.
4. A corolla exposes exactly one typed open leaf per input.
5. Typed graft succeeds; mismatched graft refuses without mutation.
6. Composite terms retain generator provenance and have deterministic structural hashes.
7. An unlicensed agent cannot bind or evaluate a generator.
8. An agent cannot emit an admitted proof, witness, receipt, or ledger transition merely by choosing that output label.
9. Recursive evaluation equals the algebraic composite of registered generator actions.
10. Structural associativity witnesses are labeled ShapeOnly/ExactStructural, not mathematical proof of semantic equality.
11. Internal exceptions become `InternalError`, not `LawResult.Violated`.
12. Koszul dual computation returns `NotComputed` until `R_perp` is actually constructed.
13. Ass/Com/Lie presentation builders do not claim completed operads without their relations and actions.

## Final assessment

The proposed OEAS correspondence should be retained. The Python is a viable exploratory scaffold, not yet the applied operad it describes. The correct repair is not to impoverish the mathematics. It is to preserve the full tower while making every implementation layer say exactly what it currently defines, stores, computes, checks, and is forbidden to conclude.

---
yaml_metadata:
  contract:
    name: KernelAuthorityMatrix
    role: shared reference defining subsystem authority boundaries
    version: "2.1"
    classification: reference
    depends_on:
      - ContractConstitution
      - GlobalContractTaxonomy
      - GlobalConventions
    forbidden_authority:
      - subsystem authority expansion
      - local authority effect override
      - artifact family collapse
      - license action collapse
      - evidence fact collapse
      - matrix-defined effect classes
      - matrix-originated authority effects
    primary_output_family: TaxonomyRule
    referenced_output_families:
      - AuthorityGraph
      - ConventionRule
    authority_effect: None
    doctrine_version: "2026-05"
---

Kernel Authority Matrix
=======================

Status
------

This matrix is a **reference view** over canonical authority doctrine.

It does not create:

* authority effects,
* artifact families,
* subsystem powers,
* effect classes,
* license powers,
* execution powers,
* certification powers,
* evaluator powers,
* or local overrides.

If this matrix conflicts with `ContractConstitution`, `GlobalContractTaxonomy`, or `GlobalConventions`, those contracts control.

LLM Boundary Law
----------------

The LLM is a candidate generator only.

The LLM MUST NOT:

* certify,
* validate,
* evaluate,
* terminalize,
* authorize transitions,
* execute transitions,
* mutate state,
* upgrade evidence authority,
* convert evidence to fact,
* or declare license/action effects.

LLM output may propose matrix changes, but those proposals carry `AuthorityEffect::None` until checked against the `ContractConstitution` and `GlobalContractTaxonomy`.

Authority Matrix
----------------

| Subsystem         |                                              May Measure |                                 May Compute |                      May Judge |                                      May Certify |                                               May License | May Execute |                        May Mutate | Default Authority Effect                                                                                |
| ----------------- | -------------------------------------------------------: | ------------------------------------------: | -----------------------------: | -----------------------------------------------: | --------------------------------------------------------: | ----------: | --------------------------------: | ------------------------------------------------------------------------------------------------------- |
| LLM               |                                                       no |                                          no |                             no |                                               no |                                                        no |          no |                                no | `None` / candidate only                                                                                 |
| Observable        |                       extracts primitive quantities only | no heavy compute except declared extraction |                             no |                                               no |                                                        no |          no |                                no | `EvidenceOnly`                                                                                          |
| Functional        |                   yes, canonical measurement composition |  yes, deterministic measurement computation |                             no |                                               no |                                                        no |          no |                                no | `EvidenceOnly`; checked measurement artifact may support `FactOnly`                                     |
| MeasurementKernel |                          checks/wraps measurement values |                 limited checking/conversion |                             no |                                               no |                                                        no |          no |                                no | `EvidenceOnly`; checked measurement artifact may support `FactOnly`                                     |
| Solver            |                        no canonical measurement emission |                   yes, declared computation |                             no |                                               no |                                                        no |          no |                                no | `EvidenceOnly`; checked solver artifact may support `FactOnly`                                          |
| Analysis          |                       consumes/checks declared artifacts |                       yes, bounded analysis |             no policy judgment | no, unless explicitly bound to CertificateKernel |                                                        no |          no |                                no | `EvidenceOnly`; checked analysis artifact may support `FactOnly`                                        |
| Witness           |                                                       no |                                          no |                             no |                                               no |                                                        no |          no |                                no | `EvidenceOnly`                                                                                          |
| CertificateKernel |                                                       no |                           verification only |                             no |         yes, within declared verifier capability |                                                        no |          no |                                no | `EvidenceOnly`; verified certificate artifact may support `FactOnly`                                    |
| ReplayKernel      |                                                       no |       deterministic reconstruction/checking |                             no |                                replay-check only |                                                        no |          no |                                no | `EvidenceOnly`; verified replay artifact may support `FactOnly`                                         |
| Trace             |                                                       no |                                          no |                             no |                                               no |                                                        no |          no |                                no | `EvidenceOnly`; checked trace may support `FactOnly` history claims                                     |
| Validator         |                                                       no |                    shape/domain checks only |           well-formedness only |                                               no |                                                        no |          no |                                no | `EvidenceOnly`; checked validation artifact may support `FactOnly` only for declared shape/domain facts |
| Evaluator         |                                                       no |                                          no | yes, within evaluator contract |                                               no |                                                        no |          no |                                no | `RequiresEvaluator` or `RequestsDecision` depending output                                              |
| Policy            |                                                       no |                                          no |    classify/decide policy only |                                               no |                                                        no |          no |                                no | `RequestsDecision`                                                                                      |
| TerminalMapper    |                                                       no |                                          no |          terminal mapping only |                                               no |          no, unless separately bound to LicensingBoundary |          no |                                no | `RequestsDecision`                                                                                      |
| LicensingBoundary |                                                       no |                                          no |                             no |                                               no |                                                       yes |          no |                                no | `AuthorizesTransition`                                                                                  |
| SearchGenerator   |                                                       no |                    proposal generation only |                             no |                                               no |                                                        no |          no |                                no | `None` or `EvidenceOnly`                                                                                |
| Pipeline          |                                                       no |                                          no |                             no |                                               no |                                                        no |          no |                                no | `None` or `EvidenceOnly` for routing records                                                            |
| Engine            | no ownership of measurement/solver/certifier computation |          calls licensed execution path only |                             no |                                               no |                                    consumes licenses only |         yes | yes, only via licensed transition | `StateTransition` only when license is valid                                                            |
| MetaJudgment      |                                                       no |      bounded structural classification only |  governance admissibility only |                                               no | may support licensing path but does not license by itself |          no |                                no | `RequestsDecision`                                                                                      |
| MetaLiftContract  |                                                       no |                                          no |                             no |                                               no |                                                        no |          no |                                no | `EvidenceOnly`; checked contract may support `FactOnly`                                                 |
| LiftLicense       |                                                       no |                                          no |                             no |                                               no |                                                       yes |          no |                                no | `AuthorizesTransition`                                                                                  |
| HealthModel       |                                              report only |                  bounded health computation |                             no |                                               no |                                                        no |          no |                                no | `EvidenceOnly`; checked health artifact may support `FactOnly`                                          |

Role Power vs Artifact Authority
--------------------------------

Subsystem role does not automatically determine artifact authority.

Examples:

* `CertificateKernel` may certify, but an unchecked `CertificateEnvelope` is still `EvidenceOnly`.
* `ReplayKernel` may verify replay, but replay verification does not authorize transition.
* `LiftLicense` may authorize transition, but it does not execute.
* `Engine` may execute, but only with a valid license.
* `SearchGenerator` may generate candidates, but it does not rank, certify, judge, select, license, or execute.
* `Witness` defaults to `EvidenceOnly`; it does not verify itself.
* `CertificateEnvelope` defaults to `EvidenceOnly`; a verified certificate may support `FactOnly` only within attached evidence authority and verifier capability.
* `Record` records and controls nothing.

Authority Laws
--------------

1. Evidence does not become fact by existence. `EvidenceEnvelope` may support `FactEnvelope` only through declared checking, replay, measurement, validation, or certificate boundary.
2. Certificate authority MUST NOT exceed attached evidence authority.
3. LLM is candidate generator only. LLM output carries no authority by itself.
4. Search proposes only. Search MUST NOT evaluate, certify, terminalize, authorize, execute, claim best, claim optimal, or claim certified candidates.
5. Solvers compute only. Solver output does not authorize transition and does not emit canonical cohomological measurements unless routed through the Functional / Measurement boundary.
6. Functionals measure only. Functional output is evidence until checked by the declared measurement/replay/certificate boundary.
7. Evaluators judge only within declared evaluator authority. Evaluators do not mutate, execute, certify, or license unless a separate contract explicitly says otherwise.
8. Policies classify or decide policy only. Policy does not measure, solve, certify, execute, or mutate.
9. TerminalMappers map terminal outcomes only. License issuance requires a distinct LicensingBoundary or explicit binding to one.
10. Licenses authorize; they do not execute.
11. Engine executes licensed transitions only. Engine does not own measurement, evaluation, certification, signing, policy definition, solver computation, terminal mapping, or license creation.
12. Trace records all and controls nothing.
13. Replay verifies reconstruction only. Replay does not repair, authorize, terminalize, license, mutate, or execute.
14. HealthModel reports invariant-relative health only. It does not prescribe action.
15. No subsystem may upgrade its emitted artifact family or authority effect locally.

Canonical AuthorityEffect Reference
-----------------------------------

The canonical `AuthorityEffect` set is owned by `GlobalContractTaxonomy`.

This matrix only references that set:

```rust
pub enum AuthorityEffect {
    None,
    EvidenceOnly,
    FactOnly,
    RequiresEvaluator,
    RequestsDecision,
    AuthorizesTransition,
    StateTransition,
}
```

No contract may define a local, reduced, expanded, aliased, or subsystem-specific authority-effect enum.

Effect-Class Reference
----------------------

No subsystem row in this matrix may reuse `E/I/C/R/M` as a role classification.

`E/I/C/R/M` mean only:

* `E` = exact repair
* `I` = quotient isometry
* `C` = context embedding
* `R` = residual projection
* `M` = refused mutation

Candidates cannot self-declare these classes. Classification requires evidence and the fixed-layer operator classifier/checker.

Artifact Family Law
-------------------

Subsystems emit artifacts. Artifacts must use the canonical family set owned by `GlobalContractTaxonomy`:

```text
StructureArtifact
EvidenceEnvelope
FactEnvelope
DecisionEnvelope
ActionLicense
Action
Record
```

A subsystem MUST NOT emit multiple primary artifact families from one interface.

Required separations:

* `ActionLicense` and `Action` are separate.
* `EvidenceEnvelope` and `FactEnvelope` are separate.
* `DecisionEnvelope` and `ActionLicense` are separate.
* `Record` records and controls nothing.
* `Trace` is a `Record`, not a license, decision, fact, or action.

Required Tests
--------------

* `kernel_matrix_references_canonical_authority_effects`
* `kernel_matrix_does_not_define_local_effect_classes`
* `kernel_matrix_uses_evidence_only_for_unchecked_artifacts`
* `kernel_matrix_distinguishes_evidence_from_fact`
* `kernel_matrix_distinguishes_decision_from_license`
* `kernel_matrix_distinguishes_license_from_action`
* `search_generator_has_no_execution_or_fact_authority`
* `search_generator_cannot_claim_best_or_certified`
* `solver_has_no_transition_authority`
* `functional_defaults_to_evidence_only`
* `measurement_defaults_to_evidence_only`
* `witness_defaults_to_evidence_only`
* `certificate_defaults_to_evidence_only`
* `trace_defaults_to_evidence_only`
* `replay_defaults_to_evidence_only`
* `policy_uses_requests_decision`
* `terminal_mapper_does_not_license_without_boundary`
* `lift_license_uses_authorizes_transition`
* `engine_uses_state_transition_only_with_license`
* `metalift_contract_does_not_mutate_carrier`
* `record_controls_nothing`
* `matrix_conflicts_defer_to_constitution_taxonomy_and_conventions`

Forbidden Implementation Tokens
-------------------------------

Forbidden tokens in matrix-driven validation code:

```text
local_authority_effect_enum
local_artifact_family_enum
search_executes
search_certifies
search_claims_best
search_claims_optimal
solver_authorizes_transition
functional_authorizes_transition
witness_factonly_by_default
certificate_factonly_by_default
trace_factonly_by_default
replay_authorizes
replay_terminalizes
license_executes
decision_executes
metalift_mutates_carrier
engine_certifies
engine_creates_license
record_controls_execution
evidence_is_fact
```

Canonical Invariant
-------------------

> Subsystem roles describe what a boundary may do. Artifact authority describes what an emitted object may claim. Evidence, fact, decision, license, action, and record are separate. Search proposes, solvers compute, functionals measure, evaluators judge, policies decide, terminal mappers seal status, licenses authorize, Engine executes, Trace records, Replay verifies, and LLMs only generate candidates.

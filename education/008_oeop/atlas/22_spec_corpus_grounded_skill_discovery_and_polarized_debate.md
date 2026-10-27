# Corpus-Grounded Skill Discovery and Polarized Debate

- **Status:** `PROPOSED` integration contract over a narrower implemented kernel
- **Bounded context:** `operads`
- **AuthorityEffect:** `None`
- **Evidence ceiling:** Candidate generation, structural checking, bounded fixture
  replay, and admission evidence; no generated skill is activated or made true by
  this document.

## 1. Result and authority boundary

OEWAS may search for skills by composing typed operations over admitted corpus
claims, while a separate adversarial portfolio searches for counterexamples.
The result remains a candidate until deterministic verification, independent
replay, and an external admission decision all bind to the same bytes.

This specification refines the historical
[debate-grounded autopoiesis proposal](09_spec_debate_grounded_autopoiesis_and_structurebench_contracts.md).
It does not promote that proposal's aspirational production claims.

| Capability | State | Evidence ceiling |
| --- | --- | --- |
| Ten-colour vocabulary | `IMPLEMENTED`, `TESTED` | Exact enum and cross-registry parity tests |
| Ordered source profile and one target colour | `IMPLEMENTED` | Structural `ColourSignature`; no execution semantics |
| Refusal of unadmitted colours | `IMPLEMENTED`, `TESTED` | Parser refusal path and catalog regression tests |
| Typed partial composition at one slot | `IMPLEMENTED`, partly `TESTED` | Structural colour/profile witness only |
| Bounded anti-skill fixture replay and supplied decision-record binding | `IMPLEMENTED` for the existing anti-skill path | Exact canonical bytes and declared fixture bank; reviewer authenticity remains external |
| Corpus admission port | `PROPOSED` | No admitted runtime adapter |
| Constructive/adversarial discovery portfolios | `PROPOSED` | Search and critique only |
| StructureBench-style relation suite | `PROPOSED` | Schema and relation checks, not semantic truth |
| Perceptual audit adapter | `PROPOSED` | Advisory findings only |
| General skill external-admission port | `PROPOSED` | Existing anti-skill admission is narrower |

## 2. Exact colour universe and operation law

The only admitted colours, in their existing canonical order, are:

```text
State
Proof
Paper
Code
Contract
Receipt
Ledger
Diagram
Audit
Post
```

No discovery adapter may invent a colour, silently drop an unrecognised source,
or rewrite an unrecognised target to `Receipt`. The authority is
`domain/operad/colours.py`, with parity checks against the legacy model and
`.agents/operad/operad_signature.json`.

An operation has an ordered, exact source profile and exactly one target:

```text
f : (c_1, ..., c_k) -> d
arity(f) = k = len(source_colours(f))
```

The arity may be zero, one, or many. Invocation must supply exactly `k`
positional artifacts. For every position `i`, the artifact colour must equal
`c_i`; extra, missing, reordered, defaulted, or coerced inputs are refusals. A
successful invocation emits exactly one artifact of colour `d`; evidence is
embedded in or referenced by that one output, never returned as an untyped tuple
of side effects.

The current implementation establishes structural signatures and typed partial
composition. Exact-arity invocation envelopes, executable effects, purity, and
behavioural equivalence remain `PROPOSED`.

### 2.1 Proposed operation profiles

All profiles below use only the existing ten colours.

| Operation | Exact profile | Arity | Portfolio |
| --- | --- | ---: | --- |
| `corpus_admission` | `(Paper, Ledger, Contract) -> Receipt` | 3 | Boundary |
| `discover_candidate_skill` | `(State, Paper, Contract, Ledger) -> Code` | 4 | Constructive |
| `normalize_candidate_skill` | `(Code, Contract) -> Code` | 2 | Constructive |
| `derive_canary_bank` | `(Audit, Contract, Ledger) -> State` | 3 | Adversarial |
| `probe_candidate_skill` | `(Code, State, Contract) -> Audit` | 3 | Adversarial |
| `assemble_skill_admission_evidence` | `(Code, Audit, Receipt, Ledger) -> Receipt` | 4 | Boundary |

These are `PROPOSED` registry entries, not claims that an implementation already
exists. A `Receipt` output records a result and references any produced artifact;
it does not authorize activation.

## 3. Corpus grounding and admission port

The source corpus currently has 5,000 numeric paper/spine pairs plus 25 numbered
anchors. The numeric counts match the
[library catalog](../../the_symbol_game/_archive/papers_top25_2026_09_25/papers_top25/library/00_library_catalog_index.md),
but all 5,000 numeric spines have empty `key_structures`, `definitions`, and
`invariants`. The quantum/sign-problem domain also lacks the advertised meron,
Regge, winding, and Grassmann-parity material. Inventory membership is therefore
not mathematical admission.

The `CorpusAdmissionPort` is `PROPOSED`. Its operadic lowering is the exact
three-input `corpus_admission` profile above. It returns one typed receipt with
one of these dispositions:

```text
ADMITTED_CORPUS_CANDIDATE
REFUSED_EMPTY_MATH_SPINE
REFUSED_SOURCE_BINDING
REFUSED_DOMAIN_PROBE
REFUSED_SCHEMA
REFUSED_DUPLICATE_IDENTITY
```

An admission request must bind:

1. exact source bytes, path, byte digest, and source span;
2. parser, extractor, semantic-probe, and environment identities;
3. non-empty typed definitions, identities, assumptions, and bounds;
4. explicit counterexamples, failure modes, and applicability conditions;
5. domain-specific semantic probes, not substring-only classification;
6. one-to-one paper/spine identity and duplicate detection;
7. canonicalization and replay profiles; and
8. an evidence ceiling and `AuthorityEffect: None`.

Admission means only that a claim is suitable for candidate search under the
declared assumptions. It is not paper correctness, theorem import, runtime
activation, publication approval, or authorization.

The shared contract is defined centrally in the
[whole-estate upgrade blueprint](../../../../research/mssn_sn_tower/_archive/source_inputs_2026_09_25/atlas_direct/10_research_library_system_upgrade_blueprint.md)
and the
[receipt and port catalog](../../../../research/mssn_sn_tower/_archive/source_inputs_2026_09_25/atlas_direct/12_receipt_catalog_and_clean_architecture_lowering.md).

## 4. Dual constructive and adversarial portfolios

The polarity is operational. `O+` proposes artifacts; `O-` searches for typed
failures. Neither side is a truth oracle, and neither may set host-computed
digest, replay, verifier, or admission fields.

### 4.1 Constructive portfolio `O+`

Each constructive operation must declare its exact profile, budget, corpus
references, implementation digest, effect class, and requested verifier.

The first bounded portfolio is:

1. select admitted corpus claims and assumptions;
2. derive one candidate capability with a finite task boundary;
3. emit exact frontmatter using the ten-colour vocabulary;
4. normalize code, prompt, documentation, and fixture references; and
5. precommit the candidate bytes before adversarial inspection.

The constructive output is `CANDIDATE`, even when it compiles.

### 4.2 Adversarial portfolio `O-`

The adversarial side operates on the precommitted candidate and must emit an
`Audit`, not mutate the candidate in place. Its initial detector families are:

- exact linear or finite counterwitness;
- AST invariant detector;
- temporal trace monitor;
- protected-field projector;
- budget and unexplored-frontier guard;
- domain countermodel matcher;
- schema/profile and corpus-provenance checks; and
- determinism, mutation, and replay mismatch probes.

Every detector has bad, good, and near-miss fixtures. Detection and repair are
different artifacts: an `Audit` may identify a failure; only a new constructive
operation may produce repaired `Code`.

### 4.3 Polarized debate protocol

The `PROPOSED` debate order is:

```text
precommit candidate and portfolio manifests
  -> randomize roles and declared information visibility
  -> emit separate constructive and adversarial moves
  -> localize one public disagreement node
  -> deterministic verifier handoff
  -> optional perceptual audit
  -> independent replay
  -> external admission proposal
```

The transcript must bind role/model lineage, prompts made public, artifact
digests, tool calls, route order, budgets, disagreement node, judge identity,
and all open obligations. Same-model roles are correlated. Consensus, judge
confidence, embedding proximity, Brier score, or adaptive-stability telemetry
may schedule further work but cannot set verification or admission status.

## 5. Candidate detector lifecycle

The generalized lifecycle is `PROPOSED`; the repository already implements a
narrow bounded anti-skill verifier that reparses canonical bytes, independently
replays the fixture bank, and binds one caller-supplied
`HumanAntiSkillAdmissionDecisionV1` whose decision is `APPROVE` to each
anti-skill specification. The current path validates the reviewer identifier,
approval-reference shape, canonical bytes, and exact bindings; it does not
authenticate a signature, dereference the approval, or check the reviewer
against a trusted allowlist. Human authenticity therefore remains an external
admission obligation.

```text
INCIDENT_BOUND
  -> DETECTOR_DRAFT
  -> FIXTURE_BOUND
  -> MUTATION_EVALUATED
  -> REPLAY_PASS | REPLAY_FAIL | BUDGET_EXHAUSTED
  -> EXTERNAL_ADMISSION_PENDING
  -> EXTERNALLY_ADMITTED | EXTERNALLY_REFUSED
  -> ACTIVATED
  -> RETIRED | REVOKED
```

Transition rules:

1. `INCIDENT_BOUND` requires a minimal failing artifact and source receipt.
2. `DETECTOR_DRAFT` records scope, trigger, finding type, exact operation
   signature, protected fields, and authority ceiling.
3. `FIXTURE_BOUND` requires at least one bad, good, and near-miss fixture.
4. `MUTATION_EVALUATED` mutates every protected field and records false
   positives and false negatives on the declared suite.
5. `REPLAY_FAIL` returns a concrete counterexample to `DETECTOR_DRAFT`.
6. `BUDGET_EXHAUSTED` preserves the live frontier; it is not pass, failure, or
   global UNSAT.
7. `REPLAY_PASS` stages a candidate only. It cannot change a registry or policy.
8. `EXTERNALLY_ADMITTED` requires a decision bound to the exact candidate and
   replay receipt.
9. `ACTIVATED` additionally requires a separately admitted activation profile.
10. `RETIRED` and `REVOKED` preserve prior evidence and disposition lineage.

The central lifecycle and rejection-receipt boundaries are documented in the
[Skill Pharmacy](../../../../research/mssn_sn_tower/_archive/source_inputs_2026_09_25/atlas_direct/07_skill_pharmacy_counterexample_admission.md)
and
[learned-guard contract](../../../../research/mssn_sn_tower/_archive/source_inputs_2026_09_25/atlas_direct/07.1_rejection_receipts_and_learned_guards.md).

## 6. StructureBench-style relational contract suite

This section defines a local `PROPOSED` relation suite inspired by structured
benchmarking. It does not claim compatibility with, or implementation of, an
external StructureBench package. Each relation consumes exactly one, two, or
three typed subjects and emits exactly one `Audit`.

### 6.1 Unary relations

| Relation operation | Exact profile | Predicate |
| --- | --- | --- |
| `validate_skill_schema` | `(Code) -> Audit` | Canonical schema and admitted colours |
| `validate_operation_arity` | `(Contract) -> Audit` | Declared arity equals source-profile length |
| `validate_receipt_ceiling` | `(Receipt) -> Audit` | Evidence ceiling and authority fields are present |

### 6.2 Binary relations

| Relation operation | Exact profile | Predicate |
| --- | --- | --- |
| `bind_skill_to_registry` | `(Paper, Ledger) -> Audit` | Frontmatter signature equals registry signature |
| `bind_candidate_to_receipt` | `(Code, Receipt) -> Audit` | Receipt digest binds the exact candidate bytes |
| `bind_corpus_claim_to_source` | `(State, Paper) -> Audit` | Extracted claim binds the cited source span |

### 6.3 Triplet relations

| Relation operation | Exact profile | Predicate |
| --- | --- | --- |
| `check_composition_slot` | `(Code, Code, Contract) -> Audit` | Child target equals the named parent source slot |
| `check_detector_fixture_outcome` | `(Code, State, Contract) -> Audit` | Detector verdict equals the fixture expectation |
| `check_candidate_replay_congruence` | `(Code, Receipt, Ledger) -> Audit` | Candidate, verifier receipt, and replay ledger agree |

Each relational audit records `relation_id`, version, ordered subject refs and
colours, expected observation, actual observation, verifier digest, canonical
bytes digest, disposition, and counterexample reference. Relation success proves
only the named finite predicate. It does not prove general semantic soundness,
cross-host truth, behavioural equivalence, or safety.

Host parity is a binary or higher deployment relation only over hosts declared
active in the request. A hard-coded four-host equality is not an intrinsic
mathematical invariant.

## 7. Verification, perceptual audit, replay, and admission

The mandatory order is:

```text
candidate generation
  -> canonical normalization
  -> deterministic verification
  -> optional perceptual audit
  -> independent replay
  -> external admission
```

### 7.1 Deterministic verification

The verifier consumes exact candidate bytes, corpus receipts, operation profile,
fixture bank, environment digest, and budget. It rejects unknown fields,
host-computed fields in candidate payloads, colour or arity drift, incomplete
fixture coverage, stale digests, nondeterministic results, and protected-field
mutation.

The proposed `SkillAdmissionEvidenceV1` binds operation signature, exact colours
and arity, implementation and prompt digests, bad/good/near-miss fixtures,
mutation results, determinism observations, measured false positives and false
negatives, active-host relations, reviewer findings, and candidate disposition.

### 7.2 Optional perceptual audit

A perceptual adapter may inspect rendered documentation, screenshots, diagrams,
or slow behavioural traces only after deterministic verification. It emits
advisory findings with model/provider identity, prompt digest, evidence hashes,
confidence, and calibration limits. It may request deterministic reinspection;
it cannot turn a deterministic failure into a pass or an unverified candidate
into an admitted skill.

### 7.3 Independent replay

Replay reparses canonical bytes and recomputes outcomes under a pinned verifier
and environment. It must not trust caller-supplied pass receipts. Byte or outcome
mismatch produces a replay refusal with both observed digests. Replay of the
declared fixture bank does not prove absence of out-of-distribution failures.

### 7.4 External admission

External admission is deliberately outside constructive and adversarial
portfolios. A decision binds candidate digest, corpus-admission receipts,
deterministic evidence, replay receipt, reviewer identity, scope, expiry or
revocation policy, and activation profile. A pass without this decision remains
`EXTERNAL_ADMISSION_PENDING`.

The existing `application/anti_skill_admission/verifier.py` is evidence for this
separation only in its bounded anti-skill context. It does not implement the
general `SkillCandidateAdmissionPort` or `CorpusAdmissionPort` proposed here.

## 8. Ports and clean-architecture placement

The proposed application ports are:

```text
CorpusAdmissionPort
ConstructivePortfolioPort
AdversarialPortfolioPort
DeterministicSkillVerifierPort
OptionalPerceptualAuditPort
IndependentReplayPort
SkillCandidateAdmissionPort
ArtifactStorePort
```

Domain values and operation profiles do not import providers, filesystems,
models, networks, or human-decision mechanisms. Application use cases depend on
ports. Infrastructure adapters implement those ports. Provider verdicts return
evidence to the host; they do not mutate domain authority.

## 9. Implementation slices and acceptance gates

1. **`PROPOSED` corpus slice:** implement `CorpusAdmissionPort`, semantic domain
   probes, source-span bindings, empty-spine refusal, and mutation tests.
2. **`PROPOSED` relation slice:** implement unary, binary, and triplet request and
   audit schemas with exact-arity refusal tests.
3. **`PROPOSED` portfolio slice:** compile fixed finite constructive/adversarial
   manifests and keep finding separate from repair.
4. **`PROPOSED` replay slice:** extend independent replay from the bounded
   anti-skill path to candidate skill evidence without reusing caller receipts.
5. **`PROPOSED` perceptual slice:** add an advisory-only adapter after deterministic
   verification, including mutation tests proving it cannot promote status.
6. **`PROPOSED` admission slice:** bind external decisions and activation profiles
   to exact evidence bytes; preserve refusal, retirement, and revocation lineage.

Acceptance requires exact ten-colour parity, no silent input dropping, exact
arity at parse and invocation boundaries, deterministic bad/good/near-miss
replay, relation counterexamples, replay mismatch detection, and proof that
neither debate nor perceptual output can write admission state.

## 10. Central Atlas links and nonclaims

- [Object language, metatheory, and admission](../../../../research/mssn_sn_tower/_archive/source_inputs_2026_09_25/atlas_direct/00.2_object_language_metatheory_and_admission.md)
- [Whole-estate upgrade blueprint](../../../../research/mssn_sn_tower/_archive/source_inputs_2026_09_25/atlas_direct/10_research_library_system_upgrade_blueprint.md)
- [Receipt catalog and clean-architecture lowering](../../../../research/mssn_sn_tower/_archive/source_inputs_2026_09_25/atlas_direct/12_receipt_catalog_and_clean_architecture_lowering.md)
- [Ooutwire admission and disposition ledger](../../../../research/mssn_sn_tower/_archive/source_inputs_2026_09_25/atlas_direct/11_ooutwire_admission_and_disposition_ledger.md)

This specification does not claim that:

- debate, consensus, model confidence, or a perceptual verdict establishes truth;
- corpus membership establishes a mathematical identity;
- passing a finite fixture bank proves general correctness;
- typed composition establishes behavioural equivalence;
- active-host parity is an intrinsic four-host law;
- a proposed receipt or port is already implemented; or
- `AuthorityEffect: None` can be promoted by an OEWAS operation.

The narrow claim is that the implemented structural and bounded anti-skill
kernels can support this staged design once each proposed port, schema, replay
path, and external-admission boundary is implemented and independently tested.

# Operad type inventory

Part of [Operads](Operads.md). See also: [Skills, op inventory and the resolver](Operads-Skills-and-Catalog.md)

This page lists every distinct kind of operad thing the code defines, how the
code classifies it, how many there are, and where each is declared. It was built
by reading the code and data on `main` (2026-10-27), not the prose, so where a
document and the code disagree, this page follows the code.

## Where the classification lives

The code already keeps its own catalogue of operad types. It is a machine-read
registry in six YAML files:

[`operads/skill_operad/yaml/operad_types/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/operads/skill_operad/yaml/operad_types)

Each entry has an `id`, its canonical values, whether the set is closed, a status
(`SETTLED` or `PROPOSED`, the latter with a written decision), and every Python
class, Rust enum or data file that declares or uses the values. The checker
[`operad_type_registry.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/operads/skill_operad/skill_compiler/operad_type_registry.py)
compares each source against the canonical values.

**Count: 56 registered types** (49 settled, 7 proposed) in six families. The
tables below follow those families, then list the things the registry does not
cover.

> **The checker does not pass in this repository.** Run from the repo root,
> `python -m operads.skill_operad.skill_compiler.operad_type_registry` reports
> `types=56 PROPOSED=7 SETTLED=49 findings=41`. The registry was copied from the
> source repository with its paths unchanged: it points at `.agents/skill_operads/`
> and `engine/crates_rs/`, which do not exist here (the Rust crates live in
> `code/rust/`), and two `eis.infrastructure.mssn_pharmacy` lookups fail on a
> missing `operating_system` module. The values below were checked by hand
> against the files that do exist.

## 1. Colours and wires

Colours are the sorts of the coloured operad: every operation consumes a list of
colours and produces one.

| Type | Values | Count | Defined in |
| --- | --- | --- | --- |
| Operad colour | State, Proof, Paper, Code, Contract, Receipt, Ledger, Diagram, Audit, Post | 10, closed | [`operads/domain/operad/colours.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/operads/domain/operad/colours.py) `ADMITTED_FINITE_COLOURS` |
| Sub-colour | `Audit.hype_hits`, `Audit.lint_diff`, `Audit.sfh_findings`, `Audit.shadow_violations`, `Audit.layout_findings`, `Audit.verdict`, `Code.purged`, `Ledger.source_hashes` | 8 | [`op_inventory.yaml`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/operads/skill_operad/yaml/op_inventory.yaml) `subcolours` |
| Prompt colour (types the spans inside one prompt) | RawTextSpan, Equation, IsolatedVariable, SubstitutionStep, RationalValue, InvariantWitness, TargetResult | 7 (registry says 8) | [`pfp/domain/operad/prompt.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp/domain/operad/prompt.py) `PromptColour` |
| Capability wire type | anti_skill_subject, anti_skill_hits, typed_audit_receipt, code_text | 4 | [`operads/contracts/typed_capabilities_v1.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/operads/contracts/typed_capabilities_v1.py) `WireType` |
| Adversary port | AdversaryRuntime, NativeBout, SeatTransport, SgtEmission, ImmuneAntibodies, OeopLearning, OeopAntiSkill, PromptGenealogy, CodaEvaluation, LggrGluing, EnvelopeStore | 11 | [`code/rust/core_adversary/src/specialization.rs`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/code/rust/core_adversary/src/specialization.rs) `PortName` |
| Adversary wire type | CandidateProposal, CochainDefect, Context, Contract, DualMultiplier, DualityReceipt, FlawAudit, GateWitness, GroundTruth, PrimalResidual, RawPacket, RawSpan, SanitizedPacket, SessionHintRequest, SessionHintResult, TerminalStatus | 16 | [`ops/adversary/infrastructure/typed_operad.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/ops/adversary/infrastructure/typed_operad.py) `_COLOURS` |
| Operand colour | should be the 10 operad colours; the source data also uses `Open` and `Closed` | proposed | operand registry, not in this repo |

**Duplicates.** The ten operad colours are written out in at least eight places:
`operads/domain/operad/colours.py`, `operads/skill_operad/domain/colours.py`,
`operads/infrastructure/legacy/models.py`, `operads/domain/ddc_execution/enums.py`,
`operads/contracts/typed_capabilities_v1.py`,
`operads/domain/planar_substitution.py` (`OPERAD_COLOURS`),
`operads/skill_operad/json/operad_signature.json`, and the Rust constant
`OPERAD_COLOURS` in
[`code/rust/core_operads/src/planar.rs`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/code/rust/core_operads/src/planar.rs).
They agree today. The Rust kernel type `OperadColour` in `core_operad_theory`
accepts any non-empty name, which is why the colour type is still `PROPOSED`.

The prompt colour and the operad colour are **separate vocabularies** and are not
meant to be reconciled. The registry's prompt colour list adds an open-ended
`Custom` member from a Rust crate that is not in this repository; the Python
enum here has no `Custom`.

## 2. Operations

| Type | Values | Count | Defined in |
| --- | --- | --- | --- |
| Operation kind | Identity, Generator, Composite | 3 | [`core_operad_theory/src/foundation/operation.rs`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/code/rust/core_operad_theory/src/foundation/operation.rs) |
| Operad variant | Planar, Symmetric | 2 | [`core_operad_theory/src/foundation/colored_operad.rs`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/code/rust/core_operad_theory/src/foundation/colored_operad.rs) |
| Operation term | Identity, Primitive, Substitute, Admitted | 4 | [`core_operad_theory/src/kernel/terms.rs`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/code/rust/core_operad_theory/src/kernel/terms.rs) |
| Prompt tree shape | Leaf, Node, NullTree | 3 | `pfp/domain/operad/prompt.py` (`LeafTextSpan`, `OperadTreeNode`, `NullTree`) |
| Graft site | VERTEX, EDGE, TREE | 3 (not in registry) | [`pfp/domain/operad/graft.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp/domain/operad/graft.py) `GraftSite` |
| Op binding kind | host, pfp_turn | 2 | `operads/skill_operad/skill_compiler/op_inventory.py` |
| Inventory op | `glossa.*` (5), `sfh.*` (2), `gti.*` (3), `ara.*` (3), `mnc.*` (2) | 15 | `op_inventory.yaml`, across 5 skills |
| Operation signature (one per catalogued skill) | colour signature `(sources) -> target` | 237 operations, 10 identities | [`operad_signature.json`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/operads/skill_operad/json/operad_signature.json) |
| Residual effect | unknown, contractive, neutral, dilative | 4, proposed | `operads/domain/ddc_execution/enums.py` `ResidualEffect` |
| Morphism execution status | SUCCESS, CONTRACTIVE_PASS, NEUTRAL_PASS, REFUSED, FAILED | 5 | same file |
| Cohomology degree | H0 invariant fence, H1 first-order deformation, H2 repair obstruction, Hn higher coherence | 4 | `operads/skill_operad/meta_operad.py` `CohomologyDegree` |
| Evidence type | compilation, budget_audit, associativity, slice_verification, cochain_obstruction | 5 | `operads/domain/operad/evidence.py` |
| Open obligation kind | unverified_claim, unavailable_gate, … | 13 | `operads/skill_operad/evidence_receipt.py` |

**Residual effect has three vocabularies.** The Python enum has the four values
above, but the catalogue and signature files use `exact`, `diagnostic`,
`ExactRationalCertificate` and `residual_unknown`. In the catalogue, 229 of 237
skills say `unknown`. The registry's proposal is to keep the four values and move
`exact`-style values to a separate evidence field.

## 3. DDC letters (the cochain-operation alphabet)

The Discrete Deformation Calculus has a closed eight-letter alphabet. Each
letter is an operation on a cochain and its residual.

| Letter | Rust name | Meaning |
| --- | --- | --- |
| E | ExactRepair | discharge the defect outright, residual goes to 0 |
| R | ResidualProjection | carry forward what repair could not remove |
| C | ContextExposure | declare or split the carrier and its window |
| I | Integration | append to the local ledger |
| Λ | Lift | structural lift; needs obstruction, preservation and non-destruction witnesses |
| D | Descent | re-index or refine the window |
| M | Refusal | mutation or typed refusal |
| T | Terminalize | record a terminal status; mints no authority |

**Count: 8.** Defined three times, with the same eight letters:

- Rust `DdcOp` in [`code/rust/core_wdp/src/ddc/ddc_alphabet.rs`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/code/rust/core_wdp/src/ddc/ddc_alphabet.rs) (the proposed owner);
- Python `DdcLetter` in [`operads/skill_operad/ddc_trace_logger.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/operads/skill_operad/ddc_trace_logger.py) (the trace twin);
- Python `DdcRune` in [`operads/domain/ddc_execution/ddc_step.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/operads/domain/ddc_execution/ddc_step.py), in the order C, R, E, I, Λ, D, M, T. `DdcRune` is an **alias** marked for removal.

Two subsets are their own types: the **repair stages** C, R, E, I, M, T (6; Λ and
D are not repair stages) in `operads/contracts/ddc_code_repair_v1.py`, used by
[Bounded repair](Operads-Bounded-Repair.md), and the **degree-tower operation
kinds** SuccessorProbe, ResidualUpdate, CarrierLift (3) in
`code/rust/core_wdp/src/ddc/degree_tower.rs`. Operand **motifs** are short words
in these letters (CE, CM, CR, EM, ID); one operand uses `CP`, and `P` is not a
DDC letter.

## 4. Capabilities: skills, anti-skills, rules, patterns, antibodies

The typed-capability schema has one closed discriminator, `capability_kind`,
with **6 kinds**:
[`operads/catalog/contracts/v1/typed_capability.schema.json`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/operads/catalog/contracts/v1/typed_capability.schema.json).

| Kind | Positive or negative | How many exist in this repo | Where |
| --- | --- | --- | --- |
| `skill` | positive | **237** skill packages, all catalogued with a colour signature | `operads/skills/*/SKILL.md`, compiled to [`capability_catalog.v1.json`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/operads/skill_operad/json/capability_catalog.v1.json) |
| `anti_skill` | negative twin of a skill | **0** anti-skill records. The type exists (Python `anti_skill_v2.py`, Rust `AntiSkillSpecV2`); 10 ordinary skills have "anti" in their name (for example `auto-anti-skill-search`) | `operads/domain/anti_skills/`, `code/rust/core_epistemic_immune_system/src/anti_skill.rs` |
| `rule` | positive | **50** rule documents carrying **144** invariants (28 enforced, 12 partial, 104 candidate), in 15 topic folders; 5 typed rule lessons | [`rules_registry.yaml`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/operads/skill_operad/yaml/rules_registry.yaml), `operads/rules/`, `operads/catalog/contracts/v1/lessons/` |
| `helpful_pattern` (HP) | positive | **94** files `HP_<LANG>_<NNN>`; 4 typed lessons | `operads/patterns/helpful/` |
| `anti_pattern` (AP) | negative twin of HP | **93** files `AP_<LANG>_<NNN>`; 4 typed lessons | `operads/patterns/anti/` |
| `antibody` | negative | see below; 3 typed lessons | `eis/antibodies/` |

HP and AP files are paired by number. Three are unpaired: `HP_MD_056` and
`HP_MD_057` have no anti-pattern, and `AP_MATH_022` has no helpful pattern. The
Rust pair `hp_rs_007` / `ap_rs_007` is spelled in lower case.

**Antibodies.** There are several overlapping stores, so "how many antibodies"
depends on which one you count:

- `eis/antibodies/ab_*.json`: 58 antibody records;
- `eis/antibodies/anti_*.yaml`: 37 antibody specs. The 15 files in `specs/` are
  byte-identical copies of 15 of these, so they add no new antibodies;
- 24 names appear both as `ab_<name>.json` and `anti_<name>.yaml`, so those are
  the **same antibody in two formats**;
- `eis/antibodies/pharmacy_catalog.json`: 1,069 catalogue entries (mined
  candidates, most not admitted);
- 2 v2 candidates in `candidates/`.

Antibodies have their own small types: constraint type (ProjectOut, Restrain,
Enforce), operatorizability (repairable, fatal), runtime action (repair, abort,
and in the YAML also refuse, which the Python enum lacks), severity (P0 to P3),
pharmacy status (candidate, admitted, rejected, retired). See
[Antibody lifecycle](EIS-Antibody-Lifecycle.md).

**Anti-ops** are the negative half at the operation level: **8** anti-ops in the
op inventory (for example `sfh.refuse_bare_except`) and **7** built-in prompt
anti-op detectors in `operads/domain/prompt_hierarchy/evaluator.py` (one,
`glossa.refuse_missing_claim_envelope`, is in both lists).

**Failure classes** are two separate taxonomies of 12 each: the pharmacy's
(SELF_CERTIFICATION, FAKE_RECEIPT, …) in `eis/infrastructure/mssn_pharmacy.py`,
and the native anti-skills' (SemanticHallucination, ToyPromotion, …) in the Rust
`anti_skill.rs`. They are not the same list.

**Prompt Civilization antimorphisms.** `core_prompt_civilization` defines 3
exact antimorphism detectors (orbit-sum mismatch, global sign inversion,
stationary repeat) with a 3-way verdict, in
[`antimorphism.rs`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/code/rust/core_prompt_civilization/src/antimorphism.rs).
That crate otherwise holds prompt-evolution types (mutation, lineage, fitness),
not operad types.

## 5. Polarity

Two different polarity systems are in use.

| System | Values | Count | Defined in |
| --- | --- | --- | --- |
| PFP morphism polarity | CONSTRUCTIVE, INTERROGATIVE, CORRECTIVE, GATE | 4 | [`pfp/domain/operad/polarity.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/pfp/domain/operad/polarity.py) |
| Skill polarity pairs (O+ constructive, O- adversarial) | declared pairs | 2 pairs (1 declared, 1 inferred) | [`polarity_pairs.yaml`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/operads/skill_operad/yaml/polarity_pairs.yaml) |

`PolarizedOperadTriad` in `pfp/domain/operad/operad.py` holds sub-operads for
the first three polarities only; GATE has no sub-operad. Any skill not in
`polarity_pairs.yaml` is `UNCLASSIFIED`, so 233 of 237 skills have no declared
polarity.

## 6. Signature families (meta skills)

Two naming families encode a colour signature in the skill name:

- `meta-<sources>--<target>--contractive`: **8** skills. All 8 declare their
  residual as `unknown`, not `contractive` (proposed fix).
- `meta-<domain>-<x>-to-<y>-verifier`: **12** skills. The name gives only the
  first source colour.

## 7. Agents and roles

| Thing | Count | Where |
| --- | --- | --- |
| Agent roles with a colour licence | **12** (for example `python-dev`, `rust-dev`, `paper-builder`) | [`operads/registry/roles.yaml`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/operads/registry/roles.yaml) |
| Agents in the compiled capability catalogue | **0** | `capability_catalog.v1.json` and `agent_capability_slices.json` both have an empty `agents` list |

## 8. Operands and spans

"Operand" means two different things in the code, and neither is a span.

| Thing | What it is | Count | Where |
| --- | --- | --- | --- |
| Instruction operand | one short instruction clause plus its typed operation, addressed by exact source bytes | 4 (all in `adversary/`, all intentionally unbound) | [`operads/catalog/operands/v1/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/operads/catalog/operands/v1), type `InstructionOperand` in `operads/domain/value_objects/operands.py` |
| Obstruction operand | a repair operand with an obstruction class, carrier kind and DDC motif | 7 in the registry | `operand_registry.json`, **not in this repository** |
| Text span | a typed leaf of a prompt tree | one per leaf | `LeafTextSpan` in `pfp/domain/operad/prompt.py` |
| Source byte span | a byte range of a source document cited by a specification | per citation | `SourceByteSpan` in `pfp/domain/operad/specification.py` |
| Protected span | a byte range a prompt mutation may not touch | per prompt | `ProtectedSpanV1` in `core_prompt_civilization/src/forge.rs` |

So an **operand** is an input that an operation consumes (an instruction clause,
or an obstruction to repair), while a **span** is an address into text. The
obstruction class of an operand is meant to be one of ExactRepair,
ClosedResidual, OpenObstruction (3); three operands use failure classes instead,
which is a proposed fix.

## 9. Lifecycle and immune decision types

These are closed vocabularies attached to the things above rather than operad
things themselves: five lifecycle facets of 3 values each (declaration, schema
binding, executor binding, validation, admission) in
`operads/domain/value_objects/lifecycle_facets.py`; the older 6-stage lifecycle
(DRAFT to ADMITTED) it replaced; invocation mode (discipline 232, entry 3,
on-demand 2); meta-skill status (4); anti-skill status (5); hit disposition
(FINDING, HOLD, REFUSE); guard disposition (6); danger decision (4); authority
level (BLOCKING_GATE, DIAGNOSTIC_ONLY); anti-skill claim mode (4) and predicate
mode (ALL, ANY); resolver routes (13) in `routes.yaml`.

## What does not exist

Some names that come up in conversation have no counterpart in the code:

- **Anti-agents.** No type, file or field. Agents exist only as the 12 roles.
- **Anti-rules.** No type. The negative side of a rule is carried by
  anti-patterns and antibodies; the rules register has no negative entries.
- **Anti-skill records.** The anti-skill type is defined, but no anti-skill
  instance is stored in this repository.
- **Catalogued agents.** The catalogue schema has an `agents` list; it is empty.
- **The operand registry and operad data-type schema** (`.agents/skill_operads/`)
  and the Rust prompt-runtime crate that the registry cites were not copied in.

## Summary of counts

| Thing | Count |
| --- | --- |
| Registered operad types | 56 (49 settled, 7 proposed) |
| Operad colours | 10 (+ 8 sub-colours) |
| DDC letters | 8 (6 repair stages) |
| Capability kinds | 6 |
| Skills | 237 |
| Anti-skill records | 0 |
| Rules / rule invariants | 50 / 144 |
| Helpful patterns / anti-patterns | 94 / 93 |
| Antibody JSON / YAML specs / pharmacy entries | 58 / 37 / 1,069 |
| Inventory ops / anti-ops | 15 / 8 |
| Prompt anti-op detectors | 7 |
| Agent roles / catalogued agents | 12 / 0 |
| Instruction operands | 4 |
| PFP polarities / declared skill pairs | 4 / 2 |

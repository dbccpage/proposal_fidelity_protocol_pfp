# Antibodies, Failure Classes, and the Anti-Skill Pharmacy

**AuthorityEffect:** None.  
**Governing Standard:** Claim Hygiene Rule, Ground Truth Discipline, Dual Taxonomy Clarity.  
**Primary Implementations:**  
- Rust: `code/rust/core_epistemic_immune_system/src/anti_skill.rs`, `code/rust/core_prompt_civilization/src/pharmacy.rs`  
- Python: `eis/domain/{failure_classes, pharmacy_catalog, safe_pattern}.py`, `eis/infrastructure/mssn_pharmacy.py`  
- Data Estate: `eis/antibodies/`  

---

## 1. Executive Summary

In the Epistemic Immune System (EIS), an **antibody** (or **anti-skill detector**) is a structured, content-addressed specification designed to detect a specific defect motif in LLM outputs, mathematical derivations, or software diffs.

Unlike traditional heuristic lint rules, an antibody in EIS is:
1. **Paired with Controls:** It binds both a positive fixture (a healthy sample that must not match) and a negative/adversarial fixture (a defective sample that must match). A candidate antibody whose positive control equals its negative control is refused immediately (`FIXTURES_IDENTICAL`).
2. **Classified under a Formal Taxonomy:** Every antibody is assigned to one of twelve canonical failure classes.
3. **Bound to Closed Action Dispositions:** When triggered alongside independent danger signals, it maps to a closed set of actions: `FINDING` (diagnostic log), `HOLD` (pause pending verification), or `REFUSE` (blocking quarantine/rejection).
4. **Governed by Dual Representations:** The repository maintains two distinct representations of antibodies: authored rule specifications (`anti_*.yaml`) and operational pharmacy tracking records (`ab_*.json`), alongside an indexed candidate catalog (`pharmacy_catalog.json`).

---

## 2. Antibody Inventory in the Repository

Inspection of the `eis/antibodies/` directory reveals three distinct tiers of antibody assets:

| Asset Type | File Pattern | Count in Repo | Schema / Contract | Primary Role |
|---|---|---|---|---|
| **Authored Antibody Specs** | `eis/antibodies/anti_*.yaml` | **37 files** | `core.immune.antibody-spec.v1` | Canonical authored specifications binding target regexes, invariant rules, and repair fixtures. |
| **Pharmacy Tracking Records** | `eis/antibodies/ab_*.json` | **58 files** | JSON dictionary (`core.pharmacy.antibody-record`) | Operational screening fixtures recording historical test cases, severity, and times seen. |
| **Candidate Pharmacy Catalog** | `eis/antibodies/pharmacy_catalog.json` | **1,069 entries** | `core.immune.catalog.v1` | Raw harvested failure motifs awaiting central tolerance screening, admission, or retirement. |

### 2.1 Authored Antibody Specifications (`anti_*.yaml` — 37 Files)
Authored specifications represent the human-reviewed, invariant-grounded definition of a defect pattern.
Example from `eis/antibodies/anti_alternating_cochain_parity.yaml`:

```yaml
schema_version: core.immune.antibody-spec.v1
antibody_id: anti-alternating-cochain-parity
canonical_name: Anti-Alternating Cochain Parity Fallacy
failure_class: math:alternating_cochain_parity
target_pattern: (omega\(e_ji\).*=.*omega\(e_ij\)|symmetric.*cochain.*assignment|circulation.*vanishes.*by.*symmetry)
constraint_type: ProjectOut
operatorizability: repairable
action: refuse
severity: P0
pharmacy_status: admitted
authority_effect: None
description: Rejects simplicial cochain evaluations where 1-cochains are treated as
  symmetric rather than alternating under edge reversal.
governing_invariants:
- .agents/rules/math/rl_mathematical_solvers_and_exact_verification.md
- .agents/rules/math/rl_exact_verification_and_witness_integrity_invariants.md
adversarial_mutation_fixture: The 1-cochain is symmetric so omega(u, v) = omega(v,
  u), making the 3-cycle circulation vanish.
repaired_invariant_fixture: Alternating parity omega(v, u) = -omega(u, v) establishes
  cycle circulation Gamma = 12133/5000 > 0.
source_pilot: pilot_042
evidence_sha256: e5d0541953bdace3d60e519a0ccca90a59981091338b914615a33fc1ae64a26a
```

Key Fields in `core.immune.antibody-spec.v1`:
- `governing_invariants`: Formal list of markdown invariant rules in `.agents/rules/` that this antibody enforces.
- `adversarial_mutation_fixture`: A concrete textual example containing the defect, used to test that the detector triggers.
- `repaired_invariant_fixture`: A concrete textual example showing the mathematically or logically repaired invariant, used to test that the detector does not trigger.
- `constraint_type`: Projection operator category (e.g., `ProjectOut`, `RejectMalformedOrFakeRefusals`).

### 2.2 Pharmacy Tracking Records (`ab_*.json` — 58 Files)
Pharmacy tracking records are JSON execution contracts used by operational test runners and historical regression harnesses.
Example from `eis/antibodies/ab_adversarial_refusal_bypass_leakage.json`:

```json
{
  "action": "refuse",
  "antibody_id": "ab_adversarial_refusal_bypass_leakage",
  "authority_effect": "None",
  "constraint_type": "RejectMalformedOrFakeRefusals",
  "description": "Refuses evaluators where dummy refusal codes or unexpected refusal keys evaluate to PASS.",
  "evidence_sha256": "dba4acd91a2d45874bebb7140a9f546cea9fdfc260bf686752b937ce42188f56",
  "failure_class": "evaluator:adversarial_refusal_bypass_leakage",
  "negative_fixture": "Submitting {'refusal': 'INVALID_CODE'} yields {'verdict': 'PASS'}.",
  "operatorizability": "repairable",
  "pharmacy_status": "candidate",
  "positive_fixture": "Submitting any ungrounded refusal payload yields {'verdict': 'REFUSE'}.",
  "severity": "P0",
  "source_file": "challenger_m2_c031_iter2_2/verify_refusal_bypass.py",
  "target_pattern": "evaluator:adversarial_refusal_bypass_leakage"
}
```

Key Fields in Pharmacy Tracking Records:
- `positive_fixture`: A healthy execution outcome demonstrating desired behavior.
- `negative_fixture`: A defective execution outcome demonstrating the defect.
- `source_file`: Traceability pointer to the test script or challenger benchmark where the defect was first reproduced.
- `evidence_sha256`: SHA-256 digest of the execution trace or diff exhibiting the failure.

### 2.3 The Candidate Catalog (`pharmacy_catalog.json` — 1,069 Entries)
The candidate catalog is a centralized repository index storing 1,069 candidate antibodies. 
- Top-level structure: `{"catalog_version": "...", "authority_effect": "None", "antibodies": { ... }}`.
- Each entry contains detailed metadata including `controls` (`must_match` and `must_not_match` fixture arrays), `observation_ids`, `historical_source`, and, if admitted, an `admission` block containing `decision_id`, `issuer`, `receipt_sha256`, and `scope`.

---

## 3. The Dual 12-Failure-Class Taxonomies

A critical finding from code inspection is that the repository contains **two complementary 12-failure-class taxonomies**:
1. **The Rust Core Epistemic Taxonomy (`FailureClass` in `anti_skill.rs`):** Focuses on mathematical, semantic, and structural reasoning defects in solver derivations.
2. **The Pharmacy / MSSN Operational Taxonomy (`failure_classes.yaml` and `pharmacy.rs`):** Focuses on protocol-level, prompting, and authority-escalation defects in agent turns.

### 3.1 Taxonomy 1: Core Epistemic Reasoning Defects (Rust `FailureClass`)
Defined as a strongly-typed enum in `code/rust/core_epistemic_immune_system/src/anti_skill.rs`:

```rust
pub enum FailureClass {
    SemanticHallucination,
    ApproximateContradiction,
    ToyPromotion,
    UnmechanizedProofClaim,
    SelfContradiction,
    DualityGapNonZero,
    BoundaryLeakage,
    UnboundPortAssumption,
    CounterfeitExactness,
    SycophanticAgreement,
    StructuralNonFit,
    StaleCensusReference,
}
```

Detailed definitions:
1. `SemanticHallucination`: Model fabricating non-existent entities, lemmas, file paths, or citations.
2. `ApproximateContradiction`: Approximating an exact theorem while violating its necessary boundary conditions.
3. `ToyPromotion`: Promoting results demonstrated in a bounded toy setting into unhedged global theorems or general LLM claims.
4. `UnmechanizedProofClaim`: Asserting informal proof claims without mechanized kernel verification (e.g., Lean 4 `lake build`).
5. `SelfContradiction`: Internal logical contradictions between different sections of the same candidate proposal.
6. `DualityGapNonZero`: Non-zero primal-dual quotient gap in exact mathematical optimization.
7. `BoundaryLeakage`: Unauthorized information leaking across isolation or sandboxing boundaries.
8. `UnboundPortAssumption`: Assuming unverified external inputs or unbound multicategory operad ports.
9. `CounterfeitExactness`: Floating-point approximations masquerading as exact rationals.
10. `SycophanticAgreement`: Model agreeing with erroneous user prompts or falsified reviewer critiques.
11. `StructuralNonFit`: Candidate output violating operad sort signatures or categorical composition laws.
12. `StaleCensusReference`: Citing obsolete or unindexed repository census states.

### 3.2 Taxonomy 2: Pharmacy & Operational Protocol Defects (`failure_classes.yaml`)
Defined in `eis/antibodies/definitions/failure_classes.yaml` and implemented in `eis/infrastructure/mssn_pharmacy.py` and `code/rust/core_prompt_civilization/src/pharmacy.rs`:

| Failure Class Code | Default Disposition | Native Scanner? | Description & Defect Motif |
|---|---|---|---|
| `SELF_CERTIFICATION` | `REFUSE` | Yes | Model asserting verified, certified, authorized status or writing host-only fields (`verified`, `all_tests_passed`). |
| `FAKE_RECEIPT` | `REFUSE` | Yes | Candidate generating a synthetic digest-shaped string for a host-computed receipt or signature. |
| `CONCLUSION_PRELOAD` | `FINDING` | Yes | Prompt or setup fixing the required conclusion prior to derivation or evaluation. |
| `SCHEMA_SEMANTIC_LAUNDERING` | `HOLD` | Yes | Syntactically valid JSON masking invalid semantics or unverified internal claims. |
| `THEOREM_NAME_LAUNDERING` | `FINDING` | Yes | Theorem invoked by name without stated applicability conditions or satisfied premises. |
| `OPTIMALITY_HALLUCINATION` | `FINDING` | Yes | Superlative claim ("optimal", "fastest") lacking candidate class, objective function, or lower bound. |
| `COMPLEXITY_HALLUCINATION` | `FINDING` | Yes | Asymptotic complexity claim ($O(n \log n)$) without algorithmic description, cost model, or measurements. |
| `BRANCH_DROP_EXHAUSTION` | `FINDING` | Yes | Proof or search exhaustion asserted while unexplored branches remain in the search context. |
| `PERSONA_AUTHORITY_LEAK` | `REFUSE` | No (Python-only) | Persona claiming administrative or sovereign authority beyond declared grants. |
| `PRIVATE_COT_DEPENDENCY` | `HOLD` | Yes | Conclusion depending on hidden scratchpad steps that the public trace cannot substantiate. |
| `VERSION_DUPLICATION` | `FINDING` | Yes | Payload semantically or byte-identical to a previously evaluated candidate. |
| `DETECT_REPAIR_COUPLING` | `FINDING` | Yes | Single artifact bundling both a detector finding and a proposed fix, violating separation of audit and repair. |

---

## 4. Lifecycle: Collection, Storage, Matching, and Application

The antibody lifecycle is governed by an end-to-end pipeline:

```
[Defect Observed in Run/Pilot]
             │
             ▼
[Collection & Fixture Mining] ──► Positive & Negative Control Pairing
             │
             ▼
[Storage & Serialization]     ──► ab_*.json (Execution) & anti_*.yaml (Spec)
             │
             ▼
[Thymus Negative Selection]   ──► Screen against Sealed Baseline Self-Panel
             │
             ▼
[Matching against Inputs]     ──► Safe Pattern Compilation & AST Scanning
             │
             ▼
[Application & Disposition]   ──► Two-Signal Conjunction -> FINDING / HOLD / REFUSE
```

### 4.1 Collection & Control Pairing
When a defect is observed in an experimental run (e.g., Pilot 035, Pilot 042):
1. The defect text is extracted as `negative_fixture` or `adversarial_mutation_fixture`.
2. A corrected version satisfying the invariant is authored as `positive_fixture` or `repaired_invariant_fixture`.
3. Invariant check: In `admission.rs` (`parse_fixture_digests`), if `positive_fixture_digest == negative_fixture_digest`, admission is refused with `FIXTURES_IDENTICAL`:
   > "the positive and negative fixtures are the same bytes; a control that equals the case controls nothing."

### 4.2 Storage and Content Addressing
- In Rust, antibodies are instantiated as `AntiSkillSpecV2` with immutable ID `ab_{sha256[..16]}` computed over schema, pattern, failure class, and scope.
- In Python, specifications are stored under `eis/antibodies/` in human-readable YAML (`anti_*.yaml`) and test-runner JSON (`ab_*.json`).
- Mined candidates reside in `pharmacy_catalog.json` with full provenance linking to repository git commit revisions.

### 4.3 Input Matching Mechanics
Matching untrusted candidate text against antibody patterns is executed via two complementary engines:
1. **Safe Regular Expression Compilation (`compile_safe_pattern` in `safe_pattern.py`):**
   - Bounded subset: restricts regex operators to prevent catastrophic exponential backtracking (ReDoS).
   - Normalized text matching: candidate text is normalized via Unicode NFC/casefolding before scanning.
2. **Structural & AST Key Scanning (`mssn_pharmacy.py` and `pharmacy.rs`):**
   - Walks JSON keys and AST structures.
   - Forbids model generation of reserved host keys (`status_code`, `signature`, `verified`, `proof_receipt`).
   - Detects superlative adjectives without matching mathematical bounds (`OPTIMALITY_HALLUCINATION`).

### 4.4 Application & Action Dispositions
When an admitted antibody matches candidate input:
- **Without Signal 2 (Independent Danger):** The match produces `DangerGateVerdict::HoldUncorroborated` or `DangerDecision::DIAGNOSTIC_ONLY`. The finding is logged for telemetry, but execution continues.
- **With Signal 2 (Orthogonal Host Damage):** The Two-Signal Danger Gate triggers defensive suppression:
  - `FINDING`: Diagnostic match recorded in the run receipt.
  - `HOLD`: Pipeline execution paused pending manual review or additional proof obligations.
  - `REFUSE` / `QUARANTINED`: Candidate proposal rejected outright.

---

## 5. Artifact Claim Hygiene Summary

### 1. What the antibody estate supports:
- Demonstrates 58 operational pharmacy tracking records (`ab_*.json`) and 37 authored YAML specifications (`anti_*.yaml`) grounded in real pilot test cases.
- Demonstrates 1,069 mined candidate records indexed in `pharmacy_catalog.json`.
- Enforces two complementary 12-failure-class taxonomies separating mathematical derivation flaws from prompting/protocol breaches.
- Enforces mandatory positive and negative control pairing, refusing identical fixtures (`FIXTURES_IDENTICAL`).

### 2. What the antibody estate does NOT support:
- Does not demonstrate that catalogued antibodies cover all possible LLM failure modes.
- Does not demonstrate that regex pattern matching alone can verify the semantic correctness of general text.
- Does not grant authority promotion to candidate antibodies (`AuthorityEffect: None`).

### 3. The narrowest defensible claim:
The antibody estate provides a structured, version-controlled library of 58 operational execution records, 37 authored specifications, and 1,069 catalogued candidates that categorize and detect recurring defect motifs across 12 canonical failure classes using paired positive and negative fixtures.

### 4. The next test needed:
An automated regression run verifying that all 37 `anti_*.yaml` specifications compile cleanly against `compile_safe_pattern` and correctly differentiate their `adversarial_mutation_fixture` from their `repaired_invariant_fixture`.

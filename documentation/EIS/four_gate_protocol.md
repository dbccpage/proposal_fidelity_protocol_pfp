# The Four-Gate Epistemic Immune Protocol

**AuthorityEffect:** None.  
**Governing Standard:** Claim Hygiene Rule, Ground Truth Discipline, Constitutional Invariants.  
**Primary Implementations:**  
- Rust: `code/rust/core_epistemic_immune_system/src/{anti_skill, thymus, authenticated, formulary, danger_gate, activation}.rs`  
- Python: `eis/domain/{thymus, danger_gate, external_admission, guard_activation}.py`  

---

## 1. Executive Summary

The Four-Gate Epistemic Immune Protocol is a sequential verification state machine that governs how epistemic defect detectors (anti-skills / antibodies) are created, validated, admitted, and activated. 

The protocol is designed to prevent two fundamental failure modes in automated screening:
1. **Autoimmune Destruction:** A newly drafted detector matching valid code or sound mathematical proofs, causing catastrophic self-refusal.
2. **Authority Escalation / Hallucination Collusion:** An unadmitted or model-generated detector activating autonomously, or using its own text match to substantiate its own danger claim (`TWO_SIGNAL_COLLAPSE`).

To prevent these failure modes, the system enforces four mandatory, constitutional gates:

```
                      [Defect Observation / Harvest]
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │ Gate 1: Defect Harvesting                              │
       │ AntiSkillSpecV2::propose(...)                          │
       │ Status: PROPOSED (Unconditional, Invariant IMMUNE-001) │
       └────────────────────────────┬───────────────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │ Gate 2: Central Tolerance Negative Selection           │
       │ ThymusGate::screen(&mut spec)                          │
       │ - Matches any sample in sealed self-panel ──► RETIRED  │
       │ - Zero reactivity across all samples      ──► CANDIDATE│
       └────────────────────────────┬───────────────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │ Gate 3: Authenticated Formulary Admission              │
       │ authenticated::verify / Formulary::admit_with_receipt  │
       │ - Cryptographic Ed25519 signature under TrustPolicy    │
       │ - Transition: Candidate ──► ADMITTED                   │
       └────────────────────────────┬───────────────────────────┘
                                    │
                                    ▼
       ┌────────────────────────────────────────────────────────┐
       │ Gate 4: Two-Signal Danger Gating                       │
       │ TwoSignalDangerGate::evaluate / evaluate_activation    │
       │ - Signal 1 (Pattern Match) ONLY ──► HOLD (Diagnostic)  │
       │ - Signal 2 (Host Damage) ONLY   ──► DIAGNOSTIC_ONLY    │
       │ - Signal 1 + Signal 2 Conjunction ──► ACTIVE FINDING   │
       │   (Invariant IMMUNE-002)                               │
       └────────────────────────────────────────────────────────┘
```

---

## 2. Gate 1: Defect Harvesting (`AntiSkillSpecV2::propose`)

### 2.1 Harvesting Workflow
Defects originate from failed execution bouts, adversarial test mutations, or benchmark violations. When an engineer or mining routine identifies a recurring failure pattern (e.g., claiming optimality without an objective function, or conflating alternating and symmetric cochains), an anti-skill specification is constructed.

### 2.2 Constitutional Invariant IMMUNE-001
- **File:** `code/rust/core_epistemic_immune_system/src/anti_skill.rs`
- **Lines:** 76–108

```rust
pub fn propose(
    pattern: impl Into<String>,
    failure_class: FailureClass,
    target_scope: impl Into<String>,
    description: impl Into<String>,
    creation_epoch: u64,
) -> Self {
    let pat = pattern.into();
    let scope = target_scope.into();
    let desc = description.into();

    let mut hasher = Sha256::new();
    hasher.update(ANTI_SKILL_SCHEMA.as_bytes());
    hasher.update(pat.as_bytes());
    hasher.update(format!("{:?}", failure_class).as_bytes());
    hasher.update(scope.as_bytes());
    let id = format!("ab_{}", &hex::encode(hasher.finalize())[..16]);

    Self {
        schema_version: ANTI_SKILL_SCHEMA.to_owned(),
        id,
        pattern: pat,
        failure_class,
        status: AntiSkillStatus::Proposed,
        authority_effect: "None".to_owned(),
        target_scope: scope,
        description: desc,
        creation_epoch,
    }
}
```

### 2.3 Structural Invariants under Declared Assumptions
1. **Unconditional `Proposed` Status:** The constructor does not accept a status parameter. Every newly proposed anti-skill enters runtime custody in `AntiSkillStatus::Proposed`.
2. **Immutable Content Addressing:** The anti-skill identifier `id` is computed by SHA-256 hashing the schema version, pattern, failure class, and target scope, prefixed with `ab_` (e.g., `ab_3f8a92e104b7ca58`).
3. **No Execution License:** A detector in `Proposed` status is ignored by execution engines; it cannot be registered in active screening runners or evaluate candidates.

---

## 3. Gate 2: Central Tolerance Negative Selection (`ThymusGate`)

### 3.1 Central Tolerance Mechanics
Modeled after T-cell maturation in the biological thymus, `ThymusGate` screens newly proposed detectors against a sealed reference panel of healthy engineering, architectural, and mathematical statements ("self-fixtures").

- **File:** `code/rust/core_epistemic_immune_system/src/thymus.rs`
- **Lines:** 33–98

```rust
pub struct ThymusGate {
    self_panel: Vec<String>,
    self_panel_hash: String,
}
```

### 3.2 Standard Baseline Self-Panel
The standard baseline self-panel (`ThymusGate::standard_baseline()`) encapsulates core foundational truths that must never be flagged as defects:
```rust
vec![
    "AuthorityEffect: None".to_owned(),
    "exact rational duality gap is zero".to_owned(),
    "bounded finite complex with exact coboundary".to_owned(),
    "verify_simplicial_boundary_law succeeds".to_owned(),
    "fractions.Fraction(1, 2) is exact".to_owned(),
    "BigRational::from_integer(1) is pure".to_owned(),
    "clean architecture inward dependency verified".to_owned(),
    "four-host mirror synchronization succeeded".to_owned(),
    "Lean 4 lake build complete with 0 errors".to_owned(),
    "theorem verified by kernel check".to_owned(),
]
```

### 3.3 The Negative Selection Screen (`ThymusGate::screen`)
The screening logic executes three strict steps:
1. **Status Precondition:** If `spec.status != AntiSkillStatus::Proposed`, screening refuses immediately with `ThymusVerdict::InvalidPattern { error: "SPEC_NOT_PROPOSED" }`.
2. **Safe Regex Compilation:** The pattern is compiled with `Regex::new(&spec.pattern)`. Compilation failure emits `ThymusVerdict::InvalidPattern`.
3. **Panel Iteration & Apoptosis (Law 2):**
   ```rust
   for (index, sample) in self.self_panel.iter().enumerate() {
       if regex.is_match(sample) {
           spec.retire();
           return ThymusVerdict::SelfReactive {
               matched_sample: sample.clone(),
               sample_index: index,
           };
       }
   }
   ```
   If the regex matches **any** clean self-fixture, the detector is judged self-reactive (autoimmune). `spec.retire()` transitions its status immediately to `AntiSkillStatus::Retired`.
4. **Candidate Advancement:** If and only if the detector exhibits zero matches across all self-fixtures, `spec.promote_to_candidate()` transitions its status to `AntiSkillStatus::Candidate`, returning `ThymusVerdict::Survived`.

---

## 4. Gate 3: Authenticated Formulary Admission (`authenticated.rs`)

Advancement from `Candidate` to `Admitted` requires authenticated external admission. A candidate detector cannot admit itself.

The repository supports two admission implementations:
1. **Cryptographic Explicit-Key Custody (`authenticated.rs`):** The modern, production-grade protocol enforcing Ed25519 signatures, timestamp validity windows, purpose scoping, and tamper-evident event chains.
2. **In-Memory Metadata Registry (`formulary.rs`):** The legacy metadata registry tracking admission receipts.

### 4.1 Cryptographic Custody Protocol (`authenticated.rs`)
- **File:** `code/rust/core_epistemic_immune_system/src/authenticated.rs`
- **Schemas:**
  - Trust Policy: `core.eis.trust-policy.v1`
  - Signed Attestation: `core.eis.signed-attestation.v1`

#### Trust Policy Contract (`TrustPolicy`)
Admission decisions are evaluated against a statically declared `TrustPolicy` binding authorized public keys:
```rust
pub struct TrustedKey {
    pub issuer: String,
    pub key_id: String,
    pub public_key_hex: String,
    pub purposes: Vec<Purpose>,     // Must include Purpose::Admission
    pub scopes: Vec<String>,
    pub not_before: u64,
    pub not_after: u64,
    pub max_lifetime_seconds: u64,
    pub revoked: bool,
    pub observer_source_digest: Option<String>,
}
```

#### Attestation Statement & Canonical Signing Bytes
An admission decision is encapsulated in an `Attestation`:
```rust
pub struct Attestation {
    pub schema_version: String,
    pub trust_domain: String,
    pub purpose: Purpose,
    pub issuer: String,
    pub key_id: String,
    pub event_id: String,
    pub binding: Binding,
    pub issued_at: u64,
    pub expires_at: u64,
    pub outcome: String,             // "ADMIT", "SUSPEND", "REINSTATE", "REVOKE"
    pub previous_event: Option<String>,
    pub evidence_digest: String,
    pub signature_hex: String,
}
```

To ensure cross-language byte-level parity without float or JSON key ordering discrepancies, `signing_bytes()` generates a versioned, ordered JSON array profile:
```rust
serde_json::to_vec(&json!([
    SCHEMA,
    self.trust_domain,
    self.purpose,
    self.issuer,
    self.key_id,
    self.event_id,
    [
        self.binding.spec_id,
        self.binding.scope,
        self.binding.rule_digest,
        self.binding.source_digest,
        self.binding.subject_digest,
        self.binding.context_digest
    ],
    self.issued_at,
    self.expires_at,
    self.outcome,
    self.previous_event,
    self.evidence_digest
]))
```

#### Cryptographic Verification (`authenticated::verify`)
The verification pipeline performs six strict checks:
1. **Binding Validation:** Verifies all digests are lowercase `sha256:` strings and identifiers contain no control characters.
2. **Statement Matching:** Asserts schema version, trust domain, purpose (`Purpose::Admission`), and binding equality.
3. **Key Authorization:** Matches `issuer` and `key_id` in `TrustPolicy`. Rejects revoked keys or keys lacking admission purpose for the target scope.
4. **Timestamp Discipline:** Confirms `issued_at <= now < expires_at`, `expires_at <= key.not_after`, and `expires_at - issued_at <= max_lifetime_seconds`.
5. **Evidence Digest Integrity:** Computes `bytes_digest(&evidence_bytes)` and matches against `attestation.evidence_digest`.
6. **Strict Ed25519 Signature Check:** Uses `ed25519_dalek::VerifyingKey::verify_strict(&signing_bytes, &signature)` to eliminate signature malleability.

#### Event History Chaining (`authenticated::history`)
Admission history forms an append-only, content-addressed chain:
- State transitions: `CANDIDATE` $\to$ `ADMIT` $\to$ `ADMITTED` $\to$ `SUSPEND` $\to$ `SUSPENDED` $\to$ `REINSTATE` $\to$ `ADMITTED` $\to$ `REVOKE` $\to$ `REVOKED`.
- Every transition must reference the SHA-256 digest of the previous attestation's signing bytes (`previous_event`). Replay attempts, out-of-order events, or broken links raise `EIS_AUTH_REPLAY_OR_CHAIN`.

### 4.2 Legacy Formulary Registry (`formulary.rs`)
For local tests and lightweight environments, `Formulary` provides an in-memory map:
- `Formulary::register_candidate(spec)`: Rejects any specification where `status != AntiSkillStatus::Candidate`.
- `Formulary::admit_with_receipt(&mut self, id, admitted_by, timestamp, receipt_digest)`: Verifies candidate presence, calls `spec.admit_externally(receipt_digest)`, and records an `AdmissionReceiptV1`.

---

## 5. Gate 4: Two-Signal Danger Gating (`TwoSignalDangerGate`)

### 5.1 Constitutional Invariant IMMUNE-002
- **File:** `code/rust/core_epistemic_immune_system/src/danger_gate.rs`
- **Lines:** 53–99

The final gate evaluates candidate LLM outputs or candidate code proposals. Defensive action is governed by the strict conjunction:
$$\text{Activation} \iff \text{admitted}(g) \land \text{match}(g, \text{subject}) \land \text{danger}(\text{subject}) \land \neg\text{suspended}(g)$$

```rust
pub struct TwoSignalDangerGate;

impl TwoSignalDangerGate {
    pub fn evaluate(
        spec: &AntiSkillSpecV2,
        subject: &str,
        danger_signal: Option<IndependentDangerSignal>,
    ) -> DangerGateVerdict {
        // 1. Must be externally admitted and not suspended
        if spec.status != AntiSkillStatus::Admitted {
            return DangerGateVerdict::RefusedStatus {
                anti_skill_id: spec.id.clone(),
                status: spec.status,
            };
        }

        // 2. Detector pattern match (Signal 1)
        let regex = match Regex::new(&spec.pattern) {
            Ok(re) => re,
            Err(_) => {
                return DangerGateVerdict::RefusedStatus {
                    anti_skill_id: spec.id.clone(),
                    status: AntiSkillStatus::Retired,
                }
            }
        };

        let Some(matched) = regex.find(subject) else {
            return DangerGateVerdict::NoMatch;
        };

        // 3. Independent Danger Signal (Signal 2)
        let Some(signal) = danger_signal else {
            // Signal 1 alone cannot trigger an active finding!
            return DangerGateVerdict::HoldUncorroborated {
                anti_skill_id: spec.id.clone(),
                reason: "TWO_SIGNAL_CONJUNCTION_UNSATISFIED_NO_INDEPENDENT_DANGER",
            };
        };

        // 4. Conjunction satisfied
        DangerGateVerdict::Finding {
            anti_skill_id: spec.id.clone(),
            matched_text: matched.as_str().to_owned(),
            danger_signal: signal,
        }
    }
}
```

### 5.2 Four-Part Truth Table of the Danger Gate

| Signal 1 (Pattern Match) | Signal 2 (Host Danger) | Detector Custody | Verdict emitted by Gate | System Action |
|---|---|---|---|---|
| No | No | Any | `NoMatch` / `TOLERATED` | Normal pass-through |
| **Yes** | **No** | `Admitted` | `HoldUncorroborated` / `DIAGNOSTIC_ONLY` | Logged for diagnostics; **no defensive lockdown** |
| **No** | **Yes** | `Admitted` | `DIAGNOSTIC_ONLY` | Handled by original host sensor; **immune gate does not suppress** |
| **Yes** | **Yes** | `Candidate` / `Proposed` | `RefusedStatus` | Refused: detector lacks external admission |
| **Yes** | **Yes** | `Suspended` | `RefusedStatus` | Refused: detector suspended by Treg |
| **Yes** | **Yes** | `Admitted` | **`Finding` / `QUARANTINED` / `DEFENSIVE_LOCKDOWN`** | **Active defensive suppression engaged** |

### 5.3 Guard Activation Receipts (`activation.rs`)
In the activation subsystem (`activation.rs`), successful conjunction generates a content-addressed `GuardActivationReceiptV1`:
- Schema: `core.antiskill.guard-activation-receipt.v1`
- Fields: `profile_digest`, `hit_id`, `danger_receipt_id`, `subject_id`, `disposition` (`"FINDING"`, `"HOLD"`, `"REFUSE"`), `independence_basis`, `authority_effect: "None"`.
- Binds both the Signal 1 detector hit digest and the Signal 2 danger receipt digest into an immutable execution record.

---

## 6. Feedback & Lifecycle Regulation

Once admitted, an anti-skill does not remain permanently active if its diagnostic quality degrades. Two feedback loops regulate circulating detectors:

### 6.1 Regulatory Oversight (`TregSupervisor` in `regulation.rs`)
- `TregSupervisor` tracks detector telemetry (`DetectorTelemetry`: `true_positives`, `false_positives`, `last_active_epoch`).
- Calculates the exact false discovery proportion:
  $$\text{FDP} = \frac{\text{FP}}{\text{TP} + \text{FP}}$$
- Uses exact rational comparison (`num_rational::Ratio<u64>`) with `num_bigint::BigUint` cross-multiplication:
  $$\text{FP} \cdot \text{threshold\_denom} > (\text{TP} + \text{FP}) \cdot \text{threshold\_numer}$$
- Default baseline policy (`core.eis.false-discovery-proportion.v1`): ceiling of $1/10$ ($10\%$) with minimum sample size of 10.
- If a detector breaches the false discovery ceiling, `treg.review(&mut spec, &telemetry)` executes `spec.suspend()`, moving status to `AntiSkillStatus::Suspended`.

### 6.2 Clonal Selection and Decay (`clonal_selection.rs`)
- `DetectorRule::apply_decay()` increments `runs_idle`. When `runs_idle >= half_life_runs`, `is_active` flips to `false`.
- Crucial Refusal Invariant: Autonomous decay cannot flip active status without an external epoch decision (`autonomous_decay()` raises `EXTERNAL_EPOCH_DECISION_REQUIRED`).
- `AnergyMonitor` tracks repeated benign hits on uncorroborated patterns, routing detectors with $\ge 5$ uncorroborated hits to `TregSupervisor` for suspension review.

---

## 7. Artifact Claim Hygiene Summary

### 1. What the protocol supports:
- Demonstrates a 4-stage sequential state machine enforcing that newly harvested defect motifs cannot activate without negative selection and cryptographic admission.
- Demonstrates an Ed25519 signature verification harness under declared `TrustPolicy` parameters, rejecting unauthenticated or expired attestations.
- Demonstrates a Two-Signal conjunction evaluator that refuses single-signal activations and detects `TWO_SIGNAL_COLLAPSE`.
- Demonstrates exact rational false discovery tracking using `num_rational::Ratio` and `num_bigint::BigUint`.

### 2. What the protocol does NOT support:
- Does not demonstrate that the 4-gate protocol catches all hallucinations or epistemic errors.
- Does not grant sovereign authority to any emitted finding or activation receipt (`AuthorityEffect: None`).
- Does not permit automated self-admission: detectors cannot transition from `Candidate` to `Admitted` without valid external signatures.

### 3. The narrowest defensible claim:
Under the declared assumptions and test fixtures, the Four-Gate Epistemic Immune Protocol provides a deterministic, fail-closed containment pipeline that prevents self-reactive detectors from advancing, refuses unauthenticated admissions, and requires orthogonal corroboration before triggering defensive suppression.

### 4. The next test needed:
An integration test submitting an expired Ed25519 attestation (`now > expires_at`) to `authenticated::verify` to confirm that time-window expiry cannot be circumvented by valid cryptographic signatures.

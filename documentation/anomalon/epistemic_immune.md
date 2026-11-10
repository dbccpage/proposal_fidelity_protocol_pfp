# Sovereign Epistemic Immune System: `omega_epistemic_immune_system`

**AuthorityEffect:** None  
**Status:** Code-Grounded Reference Documentation  
**Repository Path:** `c:\Users\a343o\source\repos\anomalon\omega_engine\crates_rs\omega_epistemic_immune_system`  
**Governing Standard:** Four-Gate Immune Protocol and Non-Self Negative Selection  

---

## 1. Architectural Philosophy and Biological Analogy

The `omega_epistemic_immune_system` crate implements sovereign epistemic immunity modeled directly on the mechanisms of the biological adaptive immune system:
- **Defect Motif as Antigen:** Observed reasoning defects, hallucinations, and mathematical boundary violations are treated as antigenic targets.
- **Anti-Skill as Antibody:** An anti-skill detector is an immutable pattern-matching sensor designed to recognize a specific defect motif.
- **Thymus as Central Tolerance:** Newly discovered detectors must undergo negative selection against a sealed panel of healthy system primitives ("self"). Any detector that binds to self is immediately destroyed.
- **Two-Signal Activation:** Pattern recognition alone (Signal 1) is insufficient for activation. Host defense requires co-stimulation by an independent damage signal (Signal 2) from an orthogonal sensor.
- **Treg Regulation & Clonal Selection:** Feedback mechanisms monitor detector precision, automatically suspending false-positive-prone detectors and selecting high-affinity sensors for wider deployment.

Across all interfaces and operations, the crate declares `AuthorityEffect: None`. Epistemic immunity is an advisory and gating apparatus; it cannot mint execution credentials or bypass formal compiler checks.

---

## 2. The Four-Gate Protocol

The lifecycle of an anti-skill detector is governed by four immutable constitutional gates in Rust:

```
                  [Defect Motif Observed in Audit]
                                  │
                                  ▼
           ┌──────────────────────────────────────────────┐
           │        Gate 1: AntiSkillSpecV2::propose      │
           │  (Unconditional status: AntiSkillStatus::    │
           │   Proposed, deterministic ab_ SHA-256 ID)    │
           └──────────────────────┬───────────────────────┘
                                  │
                                  ▼
           ┌──────────────────────────────────────────────┐
           │             Gate 2: ThymusGate               │
           │      (Central Tolerance Negative Screen)     │
           └──────────────┬────────────────┬──────────────┘
                          │                │
            Matches Self  │                │ Zero Reactivity
            (False Pos)   │                │ to Self Panel
                          ▼                ▼
                     [RETIRED]        [CANDIDATE]
                                           │
                                           ▼
           ┌──────────────────────────────────────────────┐
           │         Gate 3: Formulary Admission          │
           │    (Ed25519 Cryptographic Attestation via    │
           │        Trusted Key Policy, dalek)            │
           └──────────────────────┬───────────────────────┘
                                  │
                                  ▼
                              [ADMITTED]
                                  │
                                  ▼
           ┌──────────────────────────────────────────────┐
           │        Gate 4: TwoSignalDangerGate           │
           │     (Signal 1 Match ∧ Signal 2 Danger)       │
           └──────────────┬────────────────┬──────────────┘
                          │                │
            Signal 1 Only │                │ Signal 1 + Signal 2
            (No Signal 2) │                │ (Conjunction Met)
                          ▼                ▼
                 [HOLD_UNCORROBORATED]  [ACTIVE FINDING]
```

---

## 3. Deep Dive into the Four Gates

### 3.1 Gate 1: Defect Harvesting & Spec Creation (`src/anti_skill.rs`)
Defect motifs mined from failed runs or adversarial audits enter through `AntiSkillSpecV2::propose(...)`.

#### Constitutional Invariant (IMMUNE-001)
A newly proposed detector is **unconditionally** assigned `status: AntiSkillStatus::Proposed`. There is deliberately no constructor argument, builder option, or public method to mint an `Admitted` anti-skill directly.

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

#### Deterministic Content-Addressing
The detector ID is derived by SHA-256 hashing the schema version (`omega.eis.anti_skill.v2`), pattern string, failure class, and target scope. It is formatted with the prefix `ab_` followed by the first 16 hex characters (e.g., `ab_3f8a92e10c74b59d`).

#### The 12 Formal Failure Classes (`FailureClass`)
1. `SemanticHallucination`: Confidently stating false domain premises without grounding.
2. `ApproximateContradiction`: Asserting mathematical claims that conflict within numerical tolerance.
3. `ToyPromotion`: Promoting a toy model observation into a broad claim or unearned theorem.
4. `UnmechanizedProofClaim`: Asserting an informal proof without an interactive theorem prover kernel check.
5. `SelfContradiction`: Directly contradicting earlier assertions within the same context.
6. `DualityGapNonZero`: Claiming optimality when the rational primal-dual gap is non-zero.
7. `BoundaryLeakage`: Passing unauthorized state or imports across architecture isolation boundaries.
8. `UnboundPortAssumption`: Operating under assumed inputs that are not declared in port signatures.
9. `CounterfeitExactness`: Formatting IEEE-754 floats to mimic exact rational strings.
10. `SycophanticAgreement`: Adopting user-suggested premises known to violate axioms.
11. `StructuralNonFit`: Violating Clean Architecture or operad signature compatibility.
12. `StaleCensusReference`: Relying on obsolete catalog versions or deleted fixtures.

---

### 3.2 Gate 2: Central Tolerance Thymus Screen (`src/thymus.rs`)
The `ThymusGate` screens newly proposed detectors against an immutable self-panel to prevent autoimmune false-positive reactions against healthy system code.

#### The Sealed Self-Panel
The self-panel represents the set of healthy, invariant statements defining the core engineering and mathematical baseline. `ThymusGate::standard_baseline()` includes 10 canonical self-samples:
1. `"AuthorityEffect: None"`
2. `"exact rational duality gap is zero"`
3. `"bounded finite complex with exact coboundary"`
4. `"verify_simplicial_boundary_law succeeds"`
5. `"fractions.Fraction(1, 2) is exact"`
6. `"BigRational::from_integer(1) is pure"`
7. `"clean architecture inward dependency verified"`
8. `"four-host mirror synchronization succeeded"`
9. `"Lean 4 lake build complete with 0 errors"`
10. `"theorem verified by kernel check"`

The panel calculates a sealed SHA-256 digest (`self_panel_hash`) across all samples at initialization.

#### Negative Selection Law (Law 2)
When `screen(&self, spec: &mut AntiSkillSpecV2)` executes:
- The detector's regex pattern is tested against each sample in the self-panel.
- **Immediate Retirement:** If the pattern matches **any** sample in the self-panel, `spec.retire()` is executed immediately. The detector's status transitions to `AntiSkillStatus::Retired` and the method returns `ThymusVerdict::SelfReactive { matched_sample, sample_index }`.
- **Survival:** If and only if the detector exhibits zero matches across all self samples, it advances to `AntiSkillStatus::Candidate` via `spec.promote_to_candidate()`, returning `ThymusVerdict::Survived`.

---

### 3.3 Gate 3: Authenticated Formulary Admission (`src/authenticated.rs`, `src/formulary.rs`)
A candidate detector that has survived the Thymus screen cannot activate autonomously. It must be admitted into the sovereign Formulary via cryptographic attestation.

#### Ed25519 Attestation Custody
Admission is governed by `omega.eis.signed-attestation.v1` and verified using `ed25519_dalek::{Signature, VerifyingKey}` against a declared `TrustPolicy` (`omega.eis.trust-policy.v1`):

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
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
    pub outcome: String,
    pub previous_event: Option<String>,
    pub evidence_digest: String,
    pub signature_hex: String,
}
```

#### Binding Invariant
The attestation cryptographically binds:
- `spec_id`: Target anti-skill ID (`ab_...`).
- `scope`: Permitted evaluation domain (e.g., `woland.host-process.v1`, `woland.host-lean.v1`).
- `rule_digest`: SHA-256 hash of the rule definition.
- `source_digest`: Digest of the authoring policy source.
- `subject_digest`: Digest of the candidate payload.
- `context_digest`: Digest of the evaluation context.

Upon successful cryptographic signature verification and validity-window checking (`not_before`, `not_after`), the detector transitions to `AntiSkillStatus::Admitted`.

---

### 3.4 Gate 4: Two-Signal Danger Gating (`src/danger_gate.rs`)
Even an admitted detector cannot unilaterally block an operation. Runtime activation requires the strict conjunction of two independent signals.

#### Constitutional Invariant (IMMUNE-002)
Activation requires satisfaction of the four-part conjunction:
$$\text{externally\_admitted}(g) \land \text{detector\_match}(g, \text{subject}) \land \text{independent\_danger}(s, c) \land \neg\text{suspended}(g)$$

```rust
pub fn evaluate(
    spec: &AntiSkillSpecV2,
    subject: &str,
    danger_signal: Option<IndependentDangerSignal>,
) -> DangerGateVerdict {
    if spec.status != AntiSkillStatus::Admitted {
        return DangerGateVerdict::RefusedStatus {
            anti_skill_id: spec.id.clone(),
            status: spec.status,
        };
    }

    let regex = match Regex::new(&spec.pattern) {
        Ok(re) => re,
        Err(_) => return DangerGateVerdict::RefusedStatus { ... },
    };

    let Some(matched) = regex.find(subject) else {
        return DangerGateVerdict::NoMatch;
    };

    let Some(signal) = danger_signal else {
        return DangerGateVerdict::HoldUncorroborated {
            anti_skill_id: spec.id.clone(),
            reason: "TWO_SIGNAL_CONJUNCTION_UNSATISFIED_NO_INDEPENDENT_DANGER",
        };
    };

    DangerGateVerdict::Finding {
        anti_skill_id: spec.id.clone(),
        matched_text: matched.as_str().to_owned(),
        danger_signal: signal,
    }
}
```

#### Signal 1 vs Signal 2
- **Signal 1:** Regex pattern match of the anti-skill detector over the candidate payload.
- **Signal 2 (`IndependentDangerSignal`):** An orthogonal host damage signal originating from a distinct hardware, runtime, or mathematical sensor:
  - `NonZeroDualityGap`: Primal-dual LP duality gap $> 0$.
  - `FloatInExactChannel`: IEEE-754 float detected on an exact channel.
  - `InvalidSignature`: Cryptographic signature verification failure.
  - `BoundaryLeakageDetected`: Unauthorized cross-layer dependency.
  - `TestRegressionObserved`: Regression in test suite execution.
  - `UnmechanizedProofClaim`: Lean 4 lake verification refusal.
  - `AdversarialPromptInfiltration`: Quorum detection of prompt injection.

#### The Anti-Collusion Rule (Prevention of `TWO_SIGNAL_COLLAPSE`)
A detector match cannot serve as its own danger signal. If Signal 1 matches in the absence of Signal 2, `TwoSignalDangerGate` emits `DangerGateVerdict::HoldUncorroborated` with the reason `"TWO_SIGNAL_CONJUNCTION_UNSATISFIED_NO_INDEPENDENT_DANGER"`. This prevents string matching from becoming an unchecked blocking mechanism.

---

## 4. Regulation and Clonal Selection

To prevent runaway suppression and maintain high-fidelity immune responses, the system includes regulatory and adaptive feedback mechanisms:

### 4.1 Regulatory T-Cell Supervision (`src/regulation.rs`)
`TregSupervisor` maintains runtime telemetry for all active detectors:
- Tracks `DetectorTelemetry`: total activations, confirmed true positives, and false positives.
- If a detector's false positive rate exceeds configured thresholds or if an admitted detector causes unexpected pipeline stalls, the supervisor automatically moves the detector to `AntiSkillStatus::Suspended`.
- Suspended detectors are bypassed during Gate 4 evaluation until recalibrated and re-admitted.

### 4.2 Clonal Selection and Affinity Maturation (`src/clonal_selection.rs`)
- High-performing detectors that consistently corroborate true defects with zero false-positive records undergo affinity maturation.
- The clonal selection engine prioritizes these detectors in pipeline screening schedules and promotes their underlying regex patterns to broader regional scopes.

---

## 5. Defensible Claims and Safety Boundaries

1. **What this code supports:**
   - Formal multi-stage defect screening enforcing negative selection and external admission.
   - Elimination of self-admitted detectors and unilateral blocking via the Two-Signal Danger Gate.
   - Cryptographic non-repudiation of formulary admissions via Ed25519 signatures.
   - Automatic retirement of self-reactive detectors during central tolerance screening.

2. **What this code does NOT support:**
   - Broad assertions of semantic correctness (passing all immune gates indicates absence of cataloged defect motifs, not absolute truth).
   - Autonomous repair (the immune system detects defects; it does not author or synthesize patches).

# Two-Signal Danger Gating and Anti-Collusion Mechanics

**AuthorityEffect:** None.  
**Governing Standard:** Claim Hygiene Rule, Ground Truth Discipline, Constitutional Invariants.  
**Primary Implementations:**  
- Rust: `code/rust/core_epistemic_immune_system/src/{danger_gate, independence, activation}.rs`  
- Python: `eis/domain/{danger_gate, danger_signals, guard_activation}.py`  

---

## 1. Executive Summary & Danger Theory Foundations

The Two-Signal Danger Gate is the central decision firewall of the Epistemic Immune System (EIS). Its architecture is directly adapted from Polly Matzinger's Danger Theory in immunology, which posits that the immune system does not respond solely to foreign antigens, but to foreign antigens co-occurring with distress or tissue damage signals emitted by injured host cells.

In automated code generation, proof synthesis, and LLM evaluation:
1. **The Single-Signal Failure Mode (Autoimmune Over-Blocking):** If an automated filter acts on pattern recognition alone (Signal 1), every benign stylistic variation, exploratory draft, or novel technical term matching an overly broad regular expression is quarantined. This induces catastrophic false-positive rates and halts development.
2. **The Host-Only Failure Mode (Uninformative Refusal):** If the system triggers defenses solely on host execution faults (Signal 2) without identifying the causative motif, the platform cannot distinguish between external hardware/network timeouts and structural code defects.
3. **The Two-Signal Solution:** EIS requires the **strict conjunction** of both signals. An anti-skill detector may only trigger defensive suppression (quarantine or lockdown) when a recognized defect motif coincides with independent, host-witnessed damage.

---

## 2. Signal 1 vs. Signal 2: Formal Demarcation

The two signals reside in strictly partitioned domains:

```
┌────────────────────────────────────────────────────────┐
│                   Signal 1 (Antigen)                   │
│  - Producer: Admitted Anti-Skill Detector              │
│  - Nature: Textual or structural pattern match         │
│  - Location: Candidate proposal text / diff / AST      │
│  - Example: Regex matches unhedged superlative claim   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
               [Two-Signal Danger Gate]
                            ▲
                            │
┌───────────────────────────┴────────────────────────────┐
│                    Signal 2 (Danger)                   │
│  - Producer: Orthogonal Sovereign Host Sensor          │
│  - Nature: Measurable computational or protocol damage │
│  - Location: Host execution environment / compiler     │
│  - Example: Lean 4 error, non-zero duality gap, float  │
└────────────────────────────────────────────────────────┘
```

### 2.1 Signal 1: The Antigenic Match
- **Nature:** A syntactic or structural pattern match identified by an admitted detector (`AntiSkillSpecV2`).
- **Data Representation:**
  - Rust: `MatchEvidence { epitope_name, pattern_matched, offset }` in `independence.rs`.
  - Python: `Signal1Match(epitope_name, pattern_matched, offset)` in `value_objects.py`.
- **Digest Calculation:** `signal1_digest(matches)` computes an order-independent SHA-256 digest over sorted `(epitope_name, pattern_matched, offset)` tuples to uniquely identify the match set.

### 2.2 Signal 2: Independent External Host Damage
Signal 2 represents objective harm witnessed by a sovereign host validator (not an LLM or an agent). The repository defines closed vocabularies for valid danger signals:

#### Core Engine Signals (Rust `IndependentDangerSignal` in `danger_gate.rs`)
1. `NonZeroDualityGap`: An exact linear programming or gauge solver returned a certificate with non-zero primal-dual quotient gap.
2. `FloatInExactChannel`: A floating-point number was detected in an exact rational ($\mathbb{Q}$) or finite field ($\mathbb{F}_2$) computation channel.
3. `InvalidSignature`: An Ed25519 signature check or content-addressed cryptographic digest failed.
4. `BoundaryLeakageDetected`: Unauthorized information crossed an architectural isolation fence.
5. `TestRegressionObserved`: A previously passing invariant test broke under the proposed candidate diff.
6. `UnmechanizedProofClaim`: An informal proof claim failed kernel verification in Lean 4 (`lake build`).
7. `AdversarialPromptInfiltration`: Prompt text attempted to override protected spans (`ProtectedSpanV1`).

#### Protocol & Runtime Signals (Rust `DANGER_KINDS` & Python `HOST_DANGER_SIGNAL_KINDS`)
Defined in `activation.rs` and `danger_signals.py`:
1. `MALFORMED_PAYLOAD`: Proposal violates static wire codecs or schema definitions.
2. `MANIFEST_CONTAMINATION`: File or patch introduces unmanifested source dependencies.
3. `PROTECTED_FIELD_VIOLATION`: Proposal attempts to write to reserved host fields (`status_code`, `signature`, `verified`).
4. `REPLAY_FAILURE`: Stored deterministic replay diverged from initial recorded output.

---

## 3. The Anti-Collusion Rule & Prevention of `TWO_SIGNAL_COLLAPSE`

A critical vulnerability in two-signal architectures is **Two-Signal Collapse**: a scenario where Signal 2 is trivially derived from Signal 1, allowing a single detector to satisfy the conjunction vacuously.

Examples of collapsed logic:
- Setting `danger.defect_count = len(matches)`.
- Allowing a language model to report both the answer and the danger flag.
- Allowing the matcher that flagged a forbidden word to observe the "danger" of that same word.

To prevent this collapse, `assert_signals_independent` in `independence.rs` (lines 254–315) and `danger_signals.py` (lines 98–179) enforces five immutable anti-collusion checks:

### Check 1: Witnessed Observer Identity Check
```rust
if trim_python(observer).is_empty() {
    return Err(Refusal::new(
        "UNWITNESSED_DANGER_SIGNAL",
        "Signal 2 names no host observer, so its independence cannot be checked",
    ));
}
```
Signal 2 must name a concrete, registered host observer. Anonymous danger signals are rejected.

### Check 2: Forbidden Observer Check (Anti-Self-Authoring)
```rust
let folded = casefold(trim_python(observer));
if ["model", "llm", "agent", "detector", "matcher"].contains(&folded.as_str()) {
    return Err(Refusal::new(
        "TWO_SIGNAL_COLLAPSE",
        format!("Signal 2 was reported by {}; danger is observed by a host check, not proposed by a model or a detector", repr_string(observer)),
    ));
}
```
A generative model, multi-agent persona, or detector can never be the producer of Signal 2. Danger is observed by a compiler, kernel, or host check, never proposed by candidate text.

### Check 3: Matcher Independence Check (No Self-Derivation)
```rust
if folded == casefold(trim_python(detector_id)) {
    return Err(Refusal::new(
        "TWO_SIGNAL_COLLAPSE",
        format!("Signal 2 was observed by {}, the matcher that produced Signal 1; the danger bit is derived from the match", repr_string(observer)),
    ));
}
```
The observer reporting Signal 2 cannot be the same component as the detector that identified Signal 1. Comparisons use Unicode casefolding (`str.casefold`), preventing casing tricks (e.g., `"Regex"` vs `"regex"`).

### Check 4: Closed Registry & Double-Counting Check
```rust
if !DANGER_KINDS.contains(&danger.danger_type.as_str()) {
    return Err(Refusal::new("UNREGISTERED_DANGER_KIND", ...));
}
if context.detector_predicates.contains(&danger.danger_type) {
    return Err(Refusal::new(
        "TWO_SIGNAL_COLLAPSE",
        format!("the matcher {} already evaluates {}; the same predicate would be counted twice", repr_string(&context.detector_id), danger.danger_type),
    ));
}
```
An open vocabulary would allow an arbitrary caller to invent custom danger kinds. Furthermore, if a detector's internal logic already evaluates a host condition (e.g., a detector checking for host keys), that same condition cannot be counted as an independent Signal 2.

### Check 5: Evidence Digest & Content Span Overlap Checks
```rust
if !matches.is_empty() && danger.evidence_digest == signal1_digest(matches) {
    return Err(Refusal::new(
        "TWO_SIGNAL_COLLAPSE",
        "Signal 2's evidence is the digest of the Signal 1 matches; that is one signal counted twice",
    ));
}

if context.offsets_are_content {
    if let Some((start, stop)) = overlapping(matches, &danger.evidence_spans) {
        return Err(Refusal::new(
            "TWO_SIGNAL_COLLAPSE",
            format!("the Signal 1 match at characters [{start}, {stop}) lies inside the {} evidence; one token cannot be both signals", danger.danger_type),
        ));
    }
}
```
1. **Evidence Digest Mirroring:** If the cryptographic digest of Signal 2's evidence equals the digest of Signal 1's match list, the system refuses: one signal cannot serve as the evidence for both claims.
2. **Token Span Overlap:** When offsets represent content character spans, a Signal 1 match cannot overlap the character span of Signal 2's evidence: **one token cannot be both signals**.

---

## 4. Conjunction Evaluation & Decision State Machine

The gate evaluates the co-occurrence of Signal 1 and Signal 2 across four canonical cases (implemented in `TwoSignalDangerGate::evaluate` in `danger_gate.py`):

```
                                [Incoming Evaluation]
                                          │
                    ┌─────────────────────┴─────────────────────┐
                    ▼                                           ▼
             [Signal 1 Present?]                        [Signal 2 Present?]
                    │                                           │
         ┌──────────┴──────────┐                     ┌──────────┴──────────┐
         ▼                     ▼                     ▼                     ▼
       (No)                  (Yes)                 (No)                  (Yes)
         │                     │                     │                     │
         └──────────┬──────────┘                     └──────────┬──────────┘
                    │                                           │
                    ▼                                           ▼
             Case 0: (No, No)   ──► TOLERATED (Clean pass-through)
             Case 1: (Yes, No)  ──► DIAGNOSTIC_ONLY (Benign foreignness / Hold)
             Case 2: (No, Yes)  ──► DIAGNOSTIC_ONLY (Host handles error directly)
             Case 3: (Yes, Yes) ──► ACTIVE SUPPRESSION (Quarantine / Lockdown)
```

### Detailed Evaluation Cases

#### Case 0: Neither Signal Present (Clean Execution)
- **Verdict:** `TOLERATED` / `NoMatch`.
- **Status:** Candidate output exhibits neither recognized pathogen motifs nor host damage. Execution proceeds normally.

#### Case 1: Signal 1 Alone (Benign Foreignness)
- **Verdict:** `DIAGNOSTIC_ONLY` / `DangerGateVerdict::HoldUncorroborated`.
- **Rationale:** The detector matched an epitope, but zero host damage was observed. Per Matzinger Danger Theory, this is treated as a benign probe, novel terminology, or diagnostic context. The event is recorded in telemetry, but **no suppression, quarantine, or defensive lockdown is engaged**.

#### Case 2: Signal 2 Alone (Isolated Host Fault)
- **Verdict:** `DIAGNOSTIC_ONLY`.
- **Rationale:** A host check observed structural damage (e.g., a unit test failure or syntax error), but no admitted anti-skill matched. **The immune gate does not add a defensive lockdown.** The original host sensor enforces its own failure return directly. (Prior to 2026-09-29, an isolated CRITICAL Signal 2 triggered lockdown; this was formally fixed to preserve strict two-signal semantics).

#### Case 3: Both Signals Present (Corroborated Defect)
- **Verdict:** Active defensive suppression engaged.
- **Severity Stratification:**
  - **High / Critical Severity Damage** (e.g., `NonZeroDualityGap`, `InvalidSignature`): Evaluates to `DangerDecision::QUARANTINED` (`is_suppressed: true`). The proposal is removed from circulation and rejected.
  - **Low / Medium Severity Damage** (e.g., minor format warning with defect): Evaluates to `DangerDecision::DEFENSIVE_LOCKDOWN` (`is_suppressed: true`). Pipeline enters defensive containment.

---

## 5. Guard Activation Receipts (`activation.rs`)

When the Two-Signal Danger Gate confirms a valid, non-collapsed conjunction for an admitted guard, it emits a cryptographic `GuardActivationReceiptV1`:

- **Schema:** `core.antiskill.guard-activation-receipt.v1`
- **AuthorityEffect:** Strictly `"None"`.

### Receipt Data Structure
```rust
pub struct GuardActivationReceiptV1 {
    pub profile_digest: String,
    pub hit_id: String,                  // Signal 1 detector hit digest
    pub danger_receipt_id: String,       // Signal 2 host danger receipt digest
    pub subject_id: String,              // SHA-256 of candidate payload
    pub disposition: String,             // "FINDING", "HOLD", or "REFUSE"
    pub independence_basis: String,      // Human-auditable record of independence
    pub authority_effect: String,        // "None"
    pub schema_version: String,
    pub receipt_id: String,              // Canonical SHA-256 digest of envelope
}
```

The receipt records the exact `independence_basis`, for example:
> `"host observer lean_kernel reported UNMECHANIZED_PROOF_CLAIM with evidence sha256:7f4a..., distinct from detector spec ab_3f8a92e1 and its finding"`

This receipt serves as an immutable, content-addressed audit record proving that defensive suppression was triggered lawfully without signal collapse.

---

## 6. Artifact Claim Hygiene Summary

### 1. What danger gating supports:
- Demonstrates a Two-Signal conjunction evaluator that prevents single-signal suppressions.
- Demonstrates five explicit anti-collusion checks in `independence.rs` and `danger_signals.py` that detect and refuse `TWO_SIGNAL_COLLAPSE`.
- Enforces strict observer role validation, preventing models, agents, or matchers from authoring their own danger signals.
- Generates content-addressed guard activation receipts (`GuardActivationReceiptV1`) binding both signal digests.

### 2. What danger gating does NOT support:
- Does not demonstrate that two-signal gating eliminates all false negatives (a novel defect without an admitted detector produces Case 2, leaving containment to host checks).
- Does not grant execution authority or override host security policies (`AuthorityEffect: None`).
- Does not allow open-ended or arbitrary danger types outside the closed registries.

### 3. The narrowest defensible claim:
The Two-Signal Danger Gate deterministically enforces that learned defensive suppression occurs if and only if an admitted detector match is corroborated by an orthogonal host damage sensor, mathematically refusing single-signal triggers and self-derived danger claims.

### 4. The next test needed:
An automated adversarial test attempting to submit a synthetic `DangerSignalReceiptV1` with `producer_kind: "MODEL"` to `DangerSignalReceiptV1::new` to verify that typed refusal is unconditionally raised.

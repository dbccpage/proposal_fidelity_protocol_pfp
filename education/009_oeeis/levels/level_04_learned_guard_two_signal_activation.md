---
documentation_contract: symbol-game-documentation/v1
title: "EIS Level 04: Learned-Guard Conjunction & Two-Signal Activation"
kind: grammar-reference
level: 4
status: active
maturity: draft
atlas_status: specified
evidence_grades:
  named: true
  syntax: true
  computed: true
  Lean: false
  gated: true
authority_effect: "None"
source_paths:
  - omega_engine_product_planning_office/plans/epics/epic_claude_oeeis_oeprmptciv_plan.md
  - omega_engine_epistemic_immune_system/domain/danger_gate.py
---

# EIS Level 04: Learned-Guard Conjunction & Two-Signal Activation

**AuthorityEffect:** None.  
**Level:** Level 04 (Dual-Signal Conjunction & Operational Activation)  
**Python Danger Seam:** [`omega_engine_epistemic_immune_system.domain.danger_gate`](../../../../omega_engine_epistemic_immune_system/domain/danger_gate.py)  
**Primary Types:** `TwoSignalDangerGate`, `DangerSignalV1`, `ActivationDisposition`  
**Core Invariant:** Learned-Guard Conjunction Law (Prevention of `TWO_SIGNAL_COLLAPSE`)

---

## 1. Schematic & Conceptual Architecture

```mermaid
graph TD
    subgraph "Learned-Guard Conjunction Law (IMMUNE-002)"
        C1["Condition 1: externally_admitted(guard, scope)"]
        C2["Condition 2: detector_match(guard, candidate_subject) [SIGNAL 1]"]
        C3["Condition 3: independent_danger_signal(context) [SIGNAL 2]"]
        C4["Condition 4: not suspended(guard, scope)"]
    end

    subgraph "Two-Signal Gating Process"
        C1 --> Conj["Boolean Conjunction: C1 AND C2 AND C3 AND C4"]
        C2 --> Conj
        C3 --> Conj
        C4 --> Conj
        
        Conj -->|ALL TRUE| Enforce["Operational Enforcement<br/>Dispositions: HOLD (pause) or REFUSE (halt)"]
        Conj -->|C3 Absent (No independent danger)| Diag["Diagnostic Only<br/>Disposition: FINDING (Telemetry emitted, run continues)"]
    end

    subgraph "Firewall Against Two-Signal Collapse"
        Bad["Copying Signal 2 from Signal 1?<br/>Or deriving danger from model's own output?"]
        Bad -->|FATAL ERROR| Collapse["REJECT WITH TWO_SIGNAL_COLLAPSE<br/>Signal 2 MUST arise from independent host witness!"]
    end
```

In biological immunology, Charles Janeway's two-signal model showed that a T-cell does not activate upon recognizing an antigen alone (Signal 1). Full activation requires a costimulatory signal (Signal 2) provided by an antigen-presenting cell that has encountered tissue damage or innate pathogen markers. Without Signal 2, T-cell antigen binding leads to anergy (tolerance) rather than inflammation.

In OEEIS, Level 04 establishes the **Learned-Guard Conjunction Law**:
- A learned epistemic guard is never allowed to block execution on string pattern matching alone.
- Blocking an execution requires the simultaneous conjunction of four distinct conditions: external admission, pattern match (Signal 1), independent host danger (Signal 2), and non-suspended status.
- Attempting to synthesize Signal 2 from the detector's own match is detected and rejected as `TWO_SIGNAL_COLLAPSE`.

---

## 2. Invariants & Mathematical Packaging

1. **The Learned-Guard Law:**
   A learned guard $g$ achieves operational enforcement status at target scope $s$ if and only if the predicate $\operatorname{enforcing\_eligible}(g, s, \text{subject}, \text{context})$ evaluates to true:
   $$\operatorname{enforcing\_eligible} \iff \operatorname{externally\_admitted}(g, s) \land \operatorname{match}(g, \text{subject}) \land \operatorname{danger}(\text{context}) \land \neg \operatorname{suspended}(g, s)$$
2. **Two-Signal Collapse Prevention:**
   - **Signal 1 (Antigenic Pattern):** The detector matches specific candidate byte patterns (regex, AST pattern, cochain boundary violation).
   - **Signal 2 (Independent Danger):** An independent host witness confirms system risk (e.g. attempted write to protected spans, unsealed state mutation, fixture failure, network egress attempt, wire packet checksum mismatch).
   - **The Anti-Collapse Rule:** Signal 2 must arise from the host environment or an independent oracle. It **cannot** be derived from the text of the model output that produced the detector match. Violating this rule raises `TWO_SIGNAL_COLLAPSE`.
3. **No Unilateral Lockdown:**
   Signal 2 alone (host danger detected without a matching guard pattern) cannot trigger a learned-guard refusal. (Host security firewalls handle bare invariant violations; learned guards fire only in conjunction).
4. **Diagnostic Fallback:**
   If a detector matches (Signal 1) and is externally admitted, but no independent danger signal is present (Signal 2 absent):
   $$\text{Disposition} \longleftarrow \text{FINDING}$$
   A diagnostic `FINDING` is recorded in telemetry, but execution is not halted.

---

## 3. Python Domain Seam

```python
# omega_engine_epistemic_immune_system.domain.danger_gate
class TwoSignalDangerGate:
    def evaluate_activation(
        self,
        guard: AdmittedGuardV1,
        target_scope: str,
        subject_bytes: bytes,
        danger_signal: Optional[DangerSignalV1],
    ) -> ActivationDisposition:
        if not guard.is_admitted_for_scope(target_scope):
            return ActivationDisposition.INELIGIBLE_SCOPE
            
        if guard.is_suspended:
            return ActivationDisposition.SUSPENDED
            
        signal_1_matched = guard.pattern_matches(subject_bytes)
        if not signal_1_matched:
            return ActivationDisposition.NO_MATCH
            
        # Check for Two-Signal Collapse
        if danger_signal and danger_signal.source_locus == guard.detector_id:
            raise TwoSignalCollapseError(
                "Signal 2 cannot be copied or derived from Signal 1 detector match!"
            )
            
        if danger_signal and danger_signal.is_independent_witness:
            return ActivationDisposition.REFUSE # Full activation
        else:
            return ActivationDisposition.FINDING # Diagnostic fallback
```

---

## 4. Verification Obligations & Falsifiers

- **`TWO_SIGNAL_COLLAPSE` Catch:** Providing a mock `DangerSignalV1` that cites the detector's own finding as its origin must trigger a `TwoSignalCollapseError` and abort evaluation.
- **Diagnostic Fallback Integrity:** In an execution bout where an admitted guard matches an unapproved idiom, but no host boundary violation occurs, the system must emit a `FINDING` receipt while asserting that the host pipeline completes without being blocked.

---

## 5. Claim Hygiene Quadrant

1. **What this supports:**
   - Multi-factor gating that prevents brittle string pattern matchers from halting benign operational executions.
   - Elimination of self-referential danger assertions in multi-agent verification pipelines.
2. **What this does not support:**
   - Does not establish that dual-signal conjunction catches all zero-day exploit patterns.
3. **The narrowest defensible claim:**
   - The learned-guard conjunction guarantees that learned guards emit blocking dispositions (`HOLD`, `REFUSE`) only when an independent host witness receipt confirms environmental danger in addition to a detector pattern match.
4. **The next test needed:**
   - Empirical test measuring false-positive halt rates across 1,000 multi-turn agent runs comparing single-signal string matching against dual-signal host-witness conjunction.

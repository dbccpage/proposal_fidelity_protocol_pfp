---
documentation_contract: symbol-game-documentation/v1
title: "Context Extension Calculus (CEC) & PFP Foundations Monograph"
kind: monograph
audience:
  - engineers
  - coding-agents
  - researchers
status: active
maturity: canonical
claim_status: source-grounded
authority_effect: "None"
source_paths:
  - pfp/infrastructure/adapters/retained_profile_cec_bridge.py
  - pfp/use_cases/cec_bridge.py
  - education/documentation/004_oepfp
last_verified: 2026-10-20
verification_scope: source inspection of the CEC bridge modules and stage definitions; no test run
---

# 03. Context Extension Calculus (CEC) & PFP Foundations Monograph

**Status:** Canonical Foundations Monograph  
**AuthorityEffect:** `None`  
**Governing Standard:** Examiner Theoretical Minimum & Claim Hygiene Rule  

---

## 1. Introduction: The Two Pillars of Symbolic Evolution

The **Proposal Fidelity Protocol (PFP)** and **Context Extension Calculus (CEC)** provide the operational and evolutionary framework for autonomous symbolic reasoning:

```mermaid
graph LR
    subgraph "PFP: Within-Context Integrity"
        P1["Candidate Proposal"] --> P2["Fidelity Gate"]
        P2 --> P3["Same-Context Repair R1"]
        P3 --> P4["Execution Receipt"]
    end

    subgraph "CEC: Cross-Context Growth"
        C1["Certified Exhaustion E"] --> C2["Conservative Lift R2"]
        C2 --> C3["Enlarged Context C'"]
        C3 --> C4["Descent Map & Invariants"]
    end

    P4 -- "Exhaustion Witness" --> C1
```

* **Proposal Fidelity Protocol (PFP):** Governs execution **within a frozen context** $C$. It validates schema conformance, executes deterministic same-context repairs, evaluates exact rational residuals ($\Phi_1, \Gamma_2, \Xi$), and emits immutable receipts.
* **Context Extension Calculus (CEC):** Governs **growth between contexts** ($C \to C'$). It evaluates structural exhaustion certificates, audits candidate extensions for old-language conservativity, and checks skeleton preservation under the declared assumptions.

---

## 2. Genesis Difference Presentation (GDP-0)

Before symbolic systems can construct complex towers, they must anchor to the ground state.

### 2.1 The Minimal Presentation Problem
How can a computational system register the occurrence of a distinction without importing ungrounded assumptions (such as Cartesian coordinates, arithmetic, or graphs)?

**Definition (GDP-0 Regime):**  
GDP-0 is the minimal formal regime capable of registering and preserving exactly one witnessed difference:
$$\Sigma_{\text{GDP-0}} = \{ \langle, \rangle \}$$
* Contains a single state: $\langle\rangle$.
* Has an empty internal transition relation: ${\longrightarrow}_0 = \varnothing$.
* Possesses zero observation operators: $O_0 = \varnothing$.

### 2.2 Quiescence as Security Fence
By Theorem 1 (No-Transition Quiescence), GDP-0 cannot spontaneously mutate into a richer state. The [pre-genesis results chapter](../../000_oepregen/03_results_and_arguments.md) classifies this statement as "true by definition": an empty transition relation has no successors. Any movement requires:
1. An external demand or proposal;
2. An explicit obstruction measurement;
3. An admitted context extension.

---

## 3. Definition of Context Extension Calculus (CEC)

**CEC = Context Extension Calculus.**

It is the protocol that decides whether a Symbol Game context $C$, already certified structurally exhausted, may be replaced by a larger context $C'$. It represents Layer 5 of the PFP mathematics.

A candidate extension is a 6-tuple:
$$e = (C, C', \iota, \pi, \Delta_C, \mathcal{W})$$

| Component | Formal Meaning |
|---|---|
| $C$ | Exhausted parent context of depth $n$ |
| $C'$ | Candidate enlarged context of depth $n+1$ |
| $\iota : X_C \to X_{C'}$ | Injective embedding of parent states |
| $\pi : X_{C'} \rightharpoonup X_C$ | Partial forgetful projection (descent map) |
| $\Delta_C$ | Explicit delta of net-new admitted structure |
| $\mathcal{W}$ | Witness that $C'$ resolves the specific obstruction that exhausted $C$ |

### 3.1 Conservativity Requirement
The extension is admitted only if it is **conservative**:
$$C' \models \iota(\phi) \iff C \models \phi$$
for every sentence $\phi$ of the parent language, and distinct parent states remain distinct under $\iota$ ($\iota(x) = \iota(y) \implies x = y$).

### 3.1a Worked example: separating `<a>` from `<ab>`

This instance uses only the pre-genesis record ([results chapter, section 5](../../000_oepregen/03_results_and_arguments.md)). The predicate is a supplied operation; the trials did not derive it.

| Component | Value in this example |
| --- | --- |
| $C$ | Inscriptions `<a>`, `<ab>`, `<aa>` with observation set $O = \varnothing$. Every pair is observationally equivalent, so a task that needs different answers on `<a>` and `<ab>` has no correct answer from the common profile. That is the exhaustion witness. |
| $C'$ | The same inscriptions with $O' = \{g\}$, where $g(x)$ = "the payload contains `b`". |
| $\iota$ | Identity on inscriptions. It is injective. |
| $\pi$ | Forget $g$. On every embedded state $\pi(\iota(x)) = x$. |
| $\Delta_C$ | Exactly one new observation, $g$. |
| $\mathcal{W}$ | $g($`<a>`$) = $ false and $g($`<ab>`$) = $ true, so the pair is now separated. |

Conservativity check: sentences that mention only inscription identity keep their truth value under $\iota$. The parent equivalence relation does not: `<a>` $\approx_0$ `<ab>` holds in $C$, while the corresponding relation over $O'$ fails in $C'$. That change is the intended resolution. A CEC audit must therefore declare which parent predicates are protected by the conservativity condition of section 3.1; observational equivalence over the old observation set cannot be one of them.

Non-uniqueness check: $f(x)$ = "the payload has more than one position" also separates the pair ($f($`<a>`$)$ false, $f($`<ab>`$)$ true), but $f($`<aa>`$)$ is true while $g($`<aa>`$)$ is false. Two different admissible $C'$ therefore resolve the same obstruction. Selecting one needs an explicit minimality or preference rule.

### 3.2 The Three-Way Separation of Powers
In the three-way separation used across the repository estate, CEC governs strictly the middle term:

$$\boxed{\text{Repair within frozen context} \;\neq\; \text{Extend representation (CEC)} \;\neq\; \text{Promote or authorize}}$$

1. **Repair** is $\operatorname{EndRep}_{\mathcal{C}}$ (same-level operator rewriting).
2. **Extension** is $\Lambda_n \to \Lambda_{n+1}$ (subject to the 9 extension audit conditions).
3. **Promotion** is $\Omega$ (outside CEC; reserved for human cryptographic signing).

---

## 4. Canonical Execution Chains (CEC)

When a problem exhausts context $C_n$, CEC constructs an auditable, step-by-step ladder of conservative extensions:

$$C_0 \xrightarrow{\;e_1\;} C_1 \xrightarrow{\;e_2\;} C_2 \dots \xrightarrow{\;e_k\;} C_k$$

### 4.1 Five Invariants of Admissible Execution Chains
1. **Monotone Depth:** Context depth increases strictly by 1 at each extension step ($d(C_{i+1}) = d(C_i) + 1$).
2. **Conservative Embedding:** Each step provides an injective embedding $\iota_i : C_i \hookrightarrow C_{i+1}$ preserving all existing truths.
3. **Surviving Skeleton:** Core relational skeletons are invariant under projection: $\pi_i(\operatorname{skel}_{i+1}(\iota_i(x))) = \operatorname{skel}_i(x)$.
4. **Exhaustion Prerequisite:** Step $e_{i+1}$ is invalid unless step $i$ emits a verified exhaustion certificate $E_i$.
5. **No Autonomous Promotion:** Completing a chain produces an audit receipt with `AuthorityEffect: None`. External promotion requires human cryptographic signing.

---

## 5. Implementation Reality in Sovereign Code

The module `retained_profile_cec_bridge.py` (`pfp/infrastructure/adapters/retained_profile_cec_bridge.py`) is an isolated finite reference evaluator implementing the CEC pattern on a concrete carrier:
* A retained difference exists before an observer;
* An observer induces a profile difference and a zero relation;
* Only a protected retained difference hidden by that observer is an **active obstruction**;
* A declared finite controller returns one of three deterministic terminals:
  1. A same-level repair;
  2. A typed refusal;
  3. A replayable conservative-extension proposal (`CECChildPacketV1` with signature, retraction, and state maps).

The implementation requires replay of every preservation obligation and fails closed on malformed evidence. It does not replace the Symbol Game router and mints zero authority.

---

## 6. Protocol vs. Calculus Demarcation & Three-Tier Decomposition

A central clarification in the Symbol Game architecture is that PFP is an operational verification loop, not a calculus:

$$\boxed{
\begin{aligned}
\text{Operational Protocol:} & \quad \mathbf{PFP} \quad (\text{Numbered Verification Pipeline: Produce } \to \text{ Freeze } \to \text{ Evaluate } \to \text{ Receipt}) \\
\text{Intra-Context Calculus:} & \quad \mathbf{FOC} \quad (\text{Finite Obstruction Calculus: Same-level repair } \operatorname{EndRep}_{\mathcal{C}}, \Phi_1, \Gamma_2, \Xi, \text{ LP duality}) \\
\text{Inter-Context Calculus:} & \quad \mathbf{CEC} \quad (\text{Context Extension Calculus: Cross-context ascent } C_n \xrightarrow{e} C_{n+1}, \text{ conservative descent } \pi) \\
\text{Syntactic & Digest Calculus:} & \quad \mathbf{Wire / Digest} \quad (\text{Canonical JSON / } \Gamma_{38}, \text{ length-delimited framed } \operatorname{domain\_digest})
\end{aligned}
}$$

Stage count at the 2026-10-20 pin: the earlier text said "8-Stage". The public controller [controller.yaml](../../../../pfp/infrastructure/yaml/stages/controller.yaml) declares `public_stage_count: 11`, `StageName` in [stages.py](../../../../pfp/domain/stages/stages.py) lists the same eleven names (admit through evidence_plan), and `run-seed --stages` accepts 1 to 11 with default 5 ([pfp.py](../../../../pfp/entrypoints/cli/pfp.py) line 75). The separate finite-QM research workflow has six stages P0 to P5 ([22](22_unified_pfp_v4_operad_workflow_and_hacks.md)).

### Verdict on Needing CEC:
1. **For fixed-context PFP runs:** CEC is **not** invoked. PFP verifies candidates against the declared context contracts; if an obstruction cannot be repaired at depth $n$, PFP fails closed and emits a typed refusal (`REFUSED`, `NO_ACTIVE_OBSTRUCTION`, or `OpenObstruction`).
2. **For symbolic expressivity evolution:** CEC is **strictly needed** as the only formal gate that licenses context enlargement without importing uncontracted semantic drift or fake theorems.
3. **Action:** Retain CEC solely with the single expansion **Context Extension Calculus**, eliminating the obsolete "Continuous Evaluation Criterion" stub and the false abbreviation "Cochain Equivalence Class".

---

## 7. Audit of Legacy Expansions & Findings

A comprehensive census of the repository estate identified three distinct historical expansions for the acronym CEC:
1. **Context Extension Calculus:** The load-bearing, mathematically grounded definition formalized in `math/04_conservative_context_extension_and_descent.md`, `levels/`, and `retained_profile_cec_bridge.py`.
2. **Continuous Evaluation Criterion (slated for retirement, still present):** At the 2026-10-20 pin the stub remains in [`domain/ports/cec_bridge.py`](../../../../pfp/domain/ports/cec_bridge.py) (`ICecBridgeAdapter`, docstring "Continuous Evaluation Criterion"), [`use_cases/cec_bridge.py`](../../../../pfp/use_cases/cec_bridge.py) and [`infrastructure/adapters/cec_bridge_adapter.py`](../../../../pfp/infrastructure/adapters/cec_bridge_adapter.py). Both implementations return `status: REFUSED` with `refusal_code: CEC_EVALUATOR_UNAVAILABLE`. Continuous metrics conflict with PFP's exact rational arithmetic.
3. **Cochain Equivalence Class (retired in this document, still registered):** At the 2026-10-20 pin, [`abbreviations.yaml`](../../../../governance/sentinel_councils/documentation/abbreviations.yaml) line 59 still gives `expansion: Cochain Equivalence Class`. No backing code was found. The register needs its own correction; this page cannot change it.

---

## 8. Claim Hygiene Compaction Envelope

1. **What this monograph supports:**
   - Supports the formal definition of Context Extension Calculus as a 6-tuple governing conservative context ascent.
   - Supports the finite reference implementation in `retained_profile_cec_bridge.py` as an executable model of observer-indexed obstruction and extension proposals.
   - Supports the three-tier decomposition separating the PFP operational protocol from intra-context FOC and inter-context CEC.

2. **What this monograph does not support:**
   - Does not support autonomous, unverified self-promotion of context depth.
   - Does not support continuous or floating-point metric evaluation under the name CEC.
   - Does not support claims that CEC eliminates all possible reasoning errors outside the declared context language.

3. **Narrowest defensible claim:**
   - CEC defines a formal 6-tuple and audit criteria for conservative context extensions in finite symbol games, implemented in reference Python code under fail-closed verification.

4. **Next test needed:**
   - Execute `py -3.12 -m pytest pfp/tests/test_cec_bridge_unavailable.py` to verify typed refusal behavior on unconfigured continuous metrics.

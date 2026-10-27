---
documentation_contract: symbol-game-documentation/v1
title: 'Application Note: Epistemic Immune System, Negative Selection, and Two-Signal Danger Gates'
kind: application-reference
audience:
  - researchers
  - cognitive-systems-engineers
  - security-architects
  - coding-agents
status: active
maturity: emerging
claim_status: verified
authority_effect: "None"
mathematical_status:
  definitions:
    - proposal_state_space
    - sealed_self_panel
    - nonself_defect_space
    - detector_predicate_space
    - thymus_negative_selection_gate
    - two_signal_danger_activation
    - clonal_affinity_maturation
    - treg_peripheral_tolerance
  prose_theorems:
    - self_panel_zero_false_positive_soundness
    - two_signal_autoimmune_suppression
    - bounded_affinity_maturation_convergence
  lean_theorems:
    - lean4/ThymusScreening.lean::Oeeis.Thymus.sound_all_iff
    - lean4/ThymusScreening.lean::Oeeis.Thymus.never_rejects_all_iff
    - lean4/ThymusScreening.lean::Oeeis.Thymus.both_all_iff
    - lean4/ThymusScreening.lean::Oeeis.Thymus.thymus_admit_iff
    - lean4/ThymusScreening.lean::Oeeis.Thymus.self_panel_soundness
    - lean4/ThymusScreening.lean::Oeeis.Thymus.self_panel_sound_for_every_panel
  finite_computations:
    - c081_thymus_self_panel_autoimmunity
    - c082_two_signal_danger_prompt_injection
    - c083_clonal_affinity_maturation_budget
    - c084_treg_peripheral_tolerance
    - demo_eis_failure_classes
  declared_policies:
    - sealed_self_panel_immutability
    - danger_signal_host_independence
  applications:
    - automated_antibody_admission
    - prompt_injection_containment
    - autoimmune_guardrail_prevention
  open_conjectures: []
coefficient_domain: "Boolean Logic / Information Theory"
runtime_dependency: "Chapter 01 (Difference Cuts), Chapter 05 (Contexts & Observers)"
governance_dependency: "None"
---

# Application Note: Epistemic Immune System, Negative Selection, and Two-Signal Danger Gates

**Status:** Downstream Mathematical Application  
**Context:** Formulates the mathematical foundation of the engine Epistemic Immune System (OEEIS): detector state spaces, the sealed Self-Panel, the Negative Selection Algorithm (NSA), the Two-Signal Danger Activation Gate, and Clonal Selection with Regulatory T-Cell (Treg) peripheral tolerance. Grounded in `MASTER_DEMO_VISION_SYMBOL_GAME_OEWAS_EIS.md` (not found at source pin `c419cc6beb`, 2026-10-20), `demo_eis_failure_classes` (now at `atlas/coda_atlas/F004_papers/015_pfp/003_pfp_host_admitted_failure_detectors/demos/demo_eis_failure_classes/`), and Challenges C081–C090.  
**Authority:** None. Artificial immune system models and host boundary verification.

---

## 1. Mathematical Formalism of Epistemic Immune Detection

Let $\mathcal{X}$ be the discrete space of all syntactic artifacts, code proposals, prompt strings, and mathematical candidate proofs expressible in a given environment.

### 1.1 Partition of the State Space: Self vs. Non-Self
The state space $\mathcal{X}$ is partitioned into two fundamental disjoint classes:
1. **The Self Space ($S \subset \mathcal{X}$):** The set of all legitimate, healthy, and correct artifacts (e.g. verified Lean 4 proofs, valid Clean Architecture ports, standard mathematical definitions, and canonical prompt templates).
2. **The Non-Self Space ($\mathcal{N} = \mathcal{X} \setminus S$):** The set of defect-bearing, hallucinatory, malicious, or erroneous artifacts (e.g. prompt injections, un-recomputed bindings, circular logic, and false witnesses).

In practice, full $S$ is unbounded. The system operates on a **Sealed Self-Panel** $S_{\mathrm{sealed}} \subset S$ consisting of $K$ certified benchmark cases:
$$S_{\mathrm{sealed}} = \{ s_1, s_2, \ldots, s_K \}$$
which must never be flagged as defective.

### 1.2 The Detector Predicate Space $\mathcal{D}$
A **detector** (or candidate antiskill/antibody) is a computable predicate:
$$d: \mathcal{X} \to \{0, 1\}$$
where $d(x) = 1$ denotes a positive defect detection, and $d(x) = 0$ denotes non-detection (tolerated).

---

## 2. The Negative Selection Algorithm (NSA) & The Thymus Gate

In biological immunology (Burnet 1959, Forrest et al. 1994), immature T-cells undergo negative selection in the thymus: any cell that reacts against the body's own peptides is destroyed before entering circulation. In the Symbol Game, this prevents security and truth guards from destroying legitimate code or valid syntax (autoimmune collapse).

### 2.1 The Thymus Filtration Gate
Let $D_{\mathrm{cand}} = \{ d_1, d_2, \ldots, d_M \}$ be a candidate detector pool mined from observed failure motifs or adversarial red-team traces.

**Definition (Thymus Gate Operator):**  
The Thymus Gate evaluates each candidate $d \in D_{\mathrm{cand}}$ against the sealed Self-Panel $S_{\mathrm{sealed}}$:

$$\operatorname{Thymus}(d) = \begin{cases} \text{ADMIT} & \text{if } \forall s \in S_{\mathrm{sealed}}, \; d(s) = 0 \\ \text{PURGE} & \text{if } \exists s \in S_{\mathrm{sealed}}, \; d(s) = 1 \quad (\text{autoimmune false positive}) \end{cases}$$

Admitted detectors form the mature immune repertoire:
$$D_{\mathrm{mature}} = \{ d \in D_{\mathrm{cand}} : \operatorname{Thymus}(d) = \text{ADMIT} \}$$

### 2.2 Autoimmune Zero False-Positive Theorem
**Theorem (Self-Panel Soundness):**  
For any admitted detector $d \in D_{\mathrm{mature}}$, its empirical false-positive rate on the sealed self-panel is identically zero:
$$\mathrm{FPR}_{S_{\mathrm{sealed}}}(d) = \frac{1}{|S_{\mathrm{sealed}}|} \sum_{s \in S_{\mathrm{sealed}}} d(s) = 0$$

*Operational consequence:*  
Admitting an antiskill or detector through the Thymus Gate ensures, under declared assumptions, that no file in the sealed benchmark suite will suffer false-positive blocking.

> **Hypotheses and Lean status (2026-10-20).** (1) The mean is defined only for a non-empty panel; the count of false positives is zero for every panel. (2) The theorem assumes the detector that is screened is the detector that runs. If the gate screens a predicate $P$ but the runtime executes $E$, admission excludes firing on every panel exactly when $E \Rightarrow P$ pointwise (Lemma C). A source-visible Lean statement of both results, `Oeeis.Thymus.self_panel_soundness` and `Oeeis.Thymus.sound_all_iff`, is in [`../lean4/ThymusScreening.lean`](../lean4/ThymusScreening.lean) with the note [`../docs/thymus_screening_note.md`](../docs/thymus_screening_note.md); the register entry SG-EIS-001 keeps the status `OPEN` with lean `PROPOSED_LEAN`, and no Lean build was run in this refresh. *Worked example:* a panel of three self items on which $d$ returns $(0, 0, 0)$ is admitted with $0/3$ false positives; if $d$ returns $(0, 1, 0)$ the gate purges it, and admitting it anyway would give an FPR of $1/3$.

---

## 3. The Two-Signal Activation Gate (Danger Model)

A recognized vulnerability in classical artificial immune systems is **hyper-reactive false alarms**: benign code that happens to share structural features with known exploit patterns (e.g. using `exec` in a test fixture or referencing `eval` in a parser) is aggressively blocked.

To resolve this, the Symbol Game adapts Polly Matzinger's **Danger Theory** (1994) into an exact **Two-Signal Activation Gate**:

```
        ┌────────────────────────────────────────────────────────┐
        │ Candidate Artifact / Model Proposal x ∈ X              │
        └──────────────────────────┬─────────────────────────────┘
                                   │
                  ┌────────────────┴────────────────┐
                  ▼                                 ▼
   [ SIGNAL 1: Structural Motif ]    [ SIGNAL 2: Host Danger Signal ]
   Pattern Match d(x) == 1           Positive Obstruction Φ > 0
   (Superficial Similarity)          or Host Boundary Refusal != 0
                  │                                 │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │ Two-Signal Activation Gate:  │
                    │ Activate = Signal_1 ∧ Signal_2│
                    └──────────────┬───────────────┘
                                   │
                   ┌───────────────┴───────────────┐
                   ▼                               ▼
            [ Both True ]                   [ Either False ]
         Execute Immune Reaction            Tolerate / Pass
         (Quarantine / Refusal)             (Preserve Proposal)
```

### 3.1 Formal Specification of the Two Signals
1. **Signal 1 (Antigen Recognition):**  
   The candidate artifact matches a structural defect pattern:
   $$\text{Signal}_1(x) = \bigvee_{d \in D_{\mathrm{mature}}} d(x) \in \{0, 1\}$$
2. **Signal 2 (Costimulatory Danger Signal):**  
   The host evaluator independently observes actual computational damage, contract violation, or positive topological obstruction:
   $$\text{Signal}_2(x) = \mathbb{I}\left( \Phi_k([x]) > 0 \lor \Gamma_{k+1}(x) > 0 \lor \text{HostException}(x) \ne \emptyset \right)$$

### 3.2 The Two-Signal Activation Rule
An immune intervention (such as an execution halt, quarantine ledger entry, or token penalty) fires if and only if **both** signals are asserted simultaneously:

$$\boxed{\operatorname{Activate}(x) = \text{Signal}_1(x) \land \text{Signal}_2(x)}$$

**Theorem (Autoimmune Suppression under Benign Syntax):**  
If an artifact $x \in \mathcal{X}$ contains a suspicious structural feature ($\text{Signal}_1(x) = 1$) but causes zero host obstruction ($\Phi_k = 0$, $\Gamma = 0$, zero contract violation, so $\text{Signal}_2(x) = 0$), then:
$$\operatorname{Activate}(x) = 1 \land 0 = 0$$
The proposal is not blocked.

This prevents hair-trigger alert cascades, allowing agents to explore unusual syntax or discuss security exploits without triggering self-censorship, provided the host runtime remains undamaged.

---

## 4. Clonal Selection, Somatic Maturation & Treg Peripheral Tolerance

Once a detector demonstrates valid non-self recognition, the system optimizes its precision and controls its lifespan under finite resource budgets.

### 4.1 Clonal Selection & Affinity Maturation
When a detector $d$ successfully intercepts an active defect under the Two-Signal Gate:
1. **Proliferation:** The detector is duplicated with high priority weighting.
2. **Somatic Hypermutation:** Controlled syntax mutations are applied to generate variant predicates $d' \in \operatorname{Mutate}(d)$ with perturbed token windows or regex bounds.
3. **Thymus Re-Screening:** Every mutated variant $d'$ must immediately pass $\operatorname{Thymus}(d') = \text{ADMIT}$ against $S_{\mathrm{sealed}}$ before deployment.
4. **Affinity Scoring:** Variants that detect broader classes of true defects while maintaining zero false positives receive highest affinity rank.

### 4.2 Regulatory T-Cells (Treg) & Peripheral Tolerance
Even when a detector passes the initial Thymus gate, evolving runtime conditions may cause it to impede legitimate workflow productivity.
- **Treg Suppression Operator:** Monitors the ratio of blocked proposals to total traffic:
  $$\rho(d) = \frac{\text{Interventions}(d)}{\text{Total Proposals}}$$
- If $\rho(d)$ exceeds an authorized operational threshold $\theta_{\mathrm{treg}}$ without corresponding verified defects ($\text{Signal}_2 = 0$), Regulatory T-cell tolerance triggers:
  $$d \xrightarrow{\text{attenuate}} \operatorname{TregSuppress}(d)$$
  demoting the detector from an active blocker to a passive diagnostic monitor (`QUARANTINED_DIAGNOSTIC`).

---

## 5. Five-Phase OEEIS Lifecycle

In the Symbol Game and OEWAS, every candidate immune capability traverses a strict five-stage lifecycle:

```
Observed ───► Candidate Detector ───► Evaluated ───► Admitted ───► Retired
(Raw Trace)    (Mined Predicate)     (Thymus Gate)   (Active Repertoire) (Decayed/Treg)
```

1. **Observed:** Raw defect observed in a recorded trajectory (e.g. `anti_morphism_observations.md`).
2. **Candidate Detector:** Structured detection predicate authored with negative, positive, and near-miss fixtures.
3. **Evaluated:** Tested against the sealed Self-Panel $S_{\mathrm{sealed}}$ and two-signal gate fixtures.
4. **Admitted:** Certified zero false-positive on self; deployed into the active repertoire.
5. **Retired:** Safely decayed under exponential half-life or suppressed by Treg tolerance when obsolete.

---

## 6. Claim Hygiene & Artifact Boundary

1. **What this document supports:**
   - Formalizes the Artificial Immune System framework for software and mathematical verification agents.
   - Shows that the Negative Selection Algorithm yields zero false positives on a sealed self-panel, provided the screened detector is the executed one (Section 2.2).
   - Shows that the Two-Signal Danger Activation Gate does not block a proposal whose host danger signal is 0. This holds only as far as $\text{Signal}_2$ is a correct danger test; a proposal that does damage the host test does not measure is not protected by this argument.
   - Defines the five-stage lifecycle for antibody admission.

2. **What this document does NOT support:**
   - Does not ensure that an admitted detector will never produce a false positive on an unobserved future artifact outside $S_{\mathrm{sealed}}$.
   - Does not replace formal theorem proving (Lean 4) or exact LP duality checks; immune detectors serve as early diagnostic filters, not proof kernels.

3. **Narrowest defensible claim:**
   - On a finite sealed self-panel $S_{\mathrm{sealed}}$, the Thymus Gate filters out all candidate detectors that fire on any $s \in S_{\mathrm{sealed}}$, and the Two-Signal Gate requires both pattern recognition and independent host defect detection prior to executing an intervention.

4. **Next test needed:**
   - Execute Challenge C081 (`c081_thymus_self_panel_autoimmunity.md`, not found at source pin `c419cc6beb`) across 50 synthetic prompt injections against a 1,000-file self-panel to evaluate detector survival rates and runtime overhead.

# OEAS Polarized Coloured Operad & Epistemic Anti-Skill Architecture Specification

**Date:** 2026-08-20  
**Status:** Canonical Design Specification (`mathematical_wip`)  
**AuthorityEffect:** None  
**Governing Layers:** `omega_engine/crates/operad_theory/`, `omega_engine_woland/domain/immune/`, `omega_engine/crates/prompt_civilization/`, `omega_engine_pfp/`

---

## 1. Executive Summary & Epistemic Posture

This document formalizes the **Polarized Coloured Operad** $(\mathcal{O}^+, \mathcal{O}^-)$ and the **Epistemic Anti-Skill Engine**. It establishes the mathematical, architectural, and historical bridge between the early trace-mining immune loops of Prompt Civilization (Omega Engine v0.0.0/v0.0.1) and the modern 5-tier Operad Theory tower.

### The Fundamental Categorical Thesis

An **anti-skill is not the inverse of a skill** ($f^{-1}$ does not generally exist in operadic multi-categories). Rather, an anti-skill is a **typed operation of opposite polarity**:

* $\mathcal{O}^+$ (**Constructive**): Skills mapping inputs and constraints to candidate artifacts.
* $\mathcal{O}^-$ (**Interrogative**): Anti-skills mapping candidate artifacts and context to structural findings and unmet obligations.
* $\mathcal{O}_{\text{repair}}$ (**Corrective**): Repair skills mapping subject and findings to localized repair proposals.
* $\mathcal{A}_{\text{gate}}$ (**Normative / External**): External human or governance decision; never an internal operadic self-promotion.

```text
                    ┌─────────────────────────────────────────────────────────┐
                    │            FORWARD PRODUCTION TREE (O⁺: Skills)         │
                    │      Evidence ──────> Analysis ──────> CandidateResult  │
                    └────────────────────────────┬────────────────────────────┘
                                                 │
                                                 ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │      BACKWARD OBLIGATION TRAVERSAL (O⁻: Anti-Skills)    │
                    │   MissingObligations <── RequiredEvidence <── Claims    │
                    └────────────────────────────┬────────────────────────────┘
                                                 │
                                                 ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │             HOST-SIDE REALITY GATE & RECEIPT            │
                    │      ReviewedCandidate ──> (Hold | Repair | Refuse)     │
                    └─────────────────────────────────────────────────────────┘
```

---

## 2. Historical Lineage & Grounding (Prompt Civilization v0)

The polarized operad architecture is a formal reconstruction of the empirical evolutionary system implemented in the Omega Engine v0.0.1 archive:

### Historical Artifacts & Implemented Mechanisms

1. **Trace Corpus (`unified_oe_trace.jsonl`)**:
   235 historical interaction records (191 `COMPOSTED`, 27 `PROMOTED`, 13 `COAL`, 4 `CRYSTALLIZED`; 137 fingerprints, 56 stored reasoning graphs).
2. **Failure Localization (`.node_failure_motifs/`)**:
   25 per-run node-motif files mapping verdict failures back onto specific reasoning graph nodes.
3. **Immune Pharmacy (`.antibodies/`)**:
   14 historical antibodies: frequency-mined `auto_*`, structural `mut_*`, and human-authored red-team antibodies (`pseudo_formal_math`).
4. **Prompt Evolution & Seeding Rules (`courage/solve.py`)**:
   * Runtime activation threshold: $n \ge 3$ defect occurrences.
   * Structural mutation threshold: $n \ge 5$ occurrences triggering prompt rewriting.
   * Historical weighted rule: $2 \times 3 = 6$ (e.g. `auto_false_lemma.json`).
5. **Promotion Memory (`.promoted_prompts/`)**:
   30 promoted morphism manifests, 4 hardened prompt-cache entries, 20 fitness vectors, and a curator journal.
6. **Literal Anti-Morphisms in Rust (`.oe_legacy/hamiltonian_antibody.rs`)**:
   Declared `HamiltonianAntibody`, `AntiMorphismConstraint`, `AntiMorphism`, and severity classifications.

### Categorical Factorization of the Historical Control Loop

The historical control loop operated as:
$$\mathrm{Trace}^* \xrightarrow{\mathrm{mine}} \mathrm{FailureMotifs} \xrightarrow{\tau} \mathrm{Antibodies} \xrightarrow{\mathrm{inject}} \mathrm{Prompt}' \xrightarrow{\mathrm{evaluate}} \mathrm{Trace}^{*+1}$$

The modern polarized operad refactors this loop by isolating candidate generation from epistemic authority:
$$\mathrm{FailureMotifs} \xrightarrow{\mathrm{synthesize}} \mathrm{CandidateAntiSkill} \xrightarrow{\mathrm{external\ admission}} \mathcal{O}^-_{\mathrm{adm}} \xrightarrow{\mathrm{activate}} \mathrm{TypedPacket}$$

Recurrence and PageRank propose candidate generators; they never grant normative authority.

---

## 3. Claim Hygiene & Formal Boundary Discipline

To maintain mathematical honesty, the following claim boundaries are frozen:

### A. Context Conditioning vs. Token Manifold Retraction

At each autoregressive step, an LLM emits a predictive distribution:
$$p_t(\cdot \mid x_{<t}, \text{context}) \in \Delta^{|V|-1}$$

A typed prompt packet modifies the conditioning context:
$$p_t^{\text{packet}} = p_\theta(\cdot \mid x_{<t}, \text{TypedPacket})$$

1. **Prompt conditioning is not a mathematical projection ($P_{\mathcal{M}}$)**: Prompt instructions change sampling weights but do not guarantee zero probability for forbidden semantic continuations.
2. **Constrained Decoding Boundary**: Where grammar-constrained decoding or logit masking is active, it enforces:
   $$Q_{A_t}(p)(v) = \begin{cases} \dfrac{p(v)}{\sum_{u \in A_t} p(u)}, & v \in A_t \\ 0, & v \notin A_t \end{cases}$$
   Even under constrained decoding, masking enforces **syntax**, not semantic truth or evidence adequacy.
3. **Canonical Statement**: The Symbol Game performs **typed context conditioning followed by host-side validation and refusal**. Where grammar-constrained decoding is installed, it additionally restricts syntactically admissible token continuations. "Manifold retraction" remains the geometric target model.

### B. Seeding Heuristics vs. Epistemic Admission

1. **Frequency Thresholds ($n \ge 3, n \ge 5$)**: Act strictly as **candidate seeding heuristics**; recurrence count alone never writes the admitted registry.
2. **PageRank / Saturation**: Acts as a **candidate-ranking heuristic** over the prompt-defect graph, not an admission proof.
3. **Lamarckian Evolution**: Retained as an operational metaphor for prompt class mutation, conditioned on explicit fitness vectors.

### C. Four Precision Corrections for Anti-Skills

1. **`evidence_sha256` is a Provenance Reference**: A digest identifies the content of a trace; it does not certify the truth of the claim.
2. **Dual-Control Fixture Naming**:
   * **Positive Detection Fixture**: Known defect payload guaranteed to trigger the anti-skill finding.
   * **Negative Control Fixture**: Clean reference payload guaranteed to pass with zero findings.
3. **`ProjectOut` vs. Idempotence ($P^2 = P$)**:
   The `ProjectOut` constraint label does not prove algebraic idempotence. True idempotence is verified on the canonical subject/finding representation:
   $$P(P(x)) = P(x)$$
4. **`ProposedDisposition` vs. Host Authority**:
   With `AuthorityEffect: None`, an anti-skill emits `ProposedDisposition::Refuse` or `ProposedDisposition::Hold`. The authorized host runtime executes the actual abort or routing.

---

## 4. Polarized Operad Formalization

### A. Carrier Spaces and Generator Polarities

Let $\mathcal{C}$ be the finite set of admitted wire/port colours:
$$\mathcal{C} = \{\text{State}, \text{Code}, \text{AuditCandidate}, \text{AuditFinding}, \text{ProofCandidate}, \text{AdmittedProof}, \text{Post}, \text{LedgerProposal}, \text{LedgerSnapshot}, \text{ReceiptPayload}, \text{EvaluationReceipt}\}$$

The operad $\mathcal{O}$ partitions into constructive, interrogative, and corrective families:
$$\mathcal{O} = \mathcal{O}^+ \sqcup \mathcal{O}^- \sqcup \mathcal{O}_{\text{repair}}$$

### B. The Anti-Skill Generator Signature

Every anti-skill generator $g_\alpha \in \mathcal{O}^-$ has signature:
$$g_\alpha: S \times C \times R \longrightarrow S \times F \times O \times H \times E$$

where:

* $S$: Immutable subject under review ($\pi_S \circ g_\alpha = \text{id}_S$).
* $C$: Activation context (bounded context, task scope, invocation grade).
* $R$: Formulary registry snapshot (admitted antibody versions).
* $F$: Finding set ($\{\text{Finding}_1, \dots, \text{Finding}_k\}$).
* $O$: Unmet proof obligations ($\{\text{Obligation}_1, \dots\}$).
* $H$: Permitted repair hints (directed rewrites).
* $E$: Deterministic `EvaluationReceipt`.

### C. Subject & Protected Field Preservation Invariant

$$\pi_S(g_\alpha(s, c, r)) \equiv s$$
$$\pi_{\text{protected}}(g_\alpha(s, c, r)) \equiv \pi_{\text{protected}}(s)$$

Anti-skills **annotate, bound, and obstruct**; they never secretly rewrite the subject.

---

## 5. Three Anti-Skill Grafting Sites

```text
                                  [ Tree Anti-Skill (𝒯-Graft) ]
                                                │
                                                ▼
                                       Root Operation (f₂)
                                             ▲     ▲
                        [ Edge Anti-Skill ]  │     │  [ Edge Anti-Skill (ℰ-Graft) ]
                                             │     │
                                       Child (f₁)  Leaf
                                           │
                                           ▼
                             [ Vertex Anti-Skill (𝒱-Graft) ]
```

1. **Vertex Anti-Skill ($\mathcal{V}$-graft)**:
   * **Attachment**: Evaluates a single generator $f \in \mathcal{O}^+$ or intermediate candidate.
   * **Scope**: Local defect patterns (e.g. `MODEL_SELF_CERTIFICATION`, unnormalized unicode, uncontracted I/O leaks).
2. **Edge Anti-Skill ($\mathcal{E}$-graft)**:
   * **Attachment**: Evaluates the partial composition seam $f \circ_i g$.
   * **Scope**: Boundary type mismatches, evidence scope attenuation, unsupported promotion (e.g. promoting `ProofCandidate` directly to `AdmittedProof` across a wire).
3. **Tree Anti-Skill ($\mathcal{T}$-graft)**:
   * **Attachment**: Evaluates the full planar tree $T \in \text{Trees}(\mathcal{O})$ and composite evaluation receipt.
   * **Scope**: Global dependency cycles ($\partial_1 z = 0$), authority laundering, missing holdout evaluations.

---

## 6. Forward Synthesis vs. Backward Decomposition

### A. Forward Operadic Synthesis ($\mathcal{O}^+$)

The forward operad composes production:
$$\gamma: \mathcal{O}(k) \otimes \mathcal{O}(n_1) \otimes \cdots \otimes \mathcal{O}(n_k) \longrightarrow \mathcal{O}\left(\sum_{i=1}^k n_i\right)$$
Mapping primitive evidence and inputs into candidate composite results.

### B. Backward Cooperadic Obligation Analysis ($\mathcal{O}^-$)

The dual cooperad structure decomposes a candidate end-result backward:
$$\Delta: \mathcal{C} \longrightarrow \mathcal{C} \otimes \mathcal{C}$$
Decomposing top-level claims into required lemmas, lemmas into axiom hypotheses, and hypotheses into admissible verification fixtures.

*Mathematical Honesty Note*: While full bar–cobar duality requires an augmented differential graded operad, the current implementation provides the **typed combinatorial obstruction model** that acts as the discrete precursor to formal homological obstruction classes.

---

## 7. The 10 Prime Laws of Epistemic Anti-Skills

All admitted anti-skills in `.agents/anti_skills/admitted/` and `omega_engine_woland/domain/immune/` must satisfy these 10 algebraic laws:

1. **Subject & Protected Field Preservation**:
   The input subject AST and all declared protected fields must be returned strictly identical.
2. **Exclusively Interrogative Emission**:
   Anti-skills emit finding sets, unmet proof obligations, holds, or refusal proposals only.
3. **Zero Self-Promoted Authority**:
   $$\text{Output}(g) \cap \{\text{AdmittedProof}, \text{GrantedAuthority}, \text{CertifiedPromotion}\} = \emptyset \quad \forall g \in \mathcal{O}^-$$
4. **Detection–Repair Orthogonality**:
   Detection ($g \in \mathcal{O}^-$) is strictly separated from repair ($r \in \mathcal{O}_{\text{repair}}$).
5. **Declared Commutation & Order Sensitivity**:
   If anti-skills $g_1, g_2$ commute, their equivalence is witnessed:
   $$g_1 \circ g_2 \cong g_2 \circ g_1$$
6. **Dual Control Verification**:
   Every anti-skill must include executable positive detection fixtures and negative control fixtures.
7. **Structural Idempotence**:
   Purely structural anti-skills must be idempotent projectors on canonical finding sets:
   $$g(g(x)) \equiv g(x)$$
8. **Finding Non-Erasure Monotonicity**:
   Subsequent anti-skills cannot erase earlier findings without an explicit typed `ResolutionProof` operator:
   $$\text{Findings}(g_2(g_1(x))) \supseteq \text{Findings}(g_1(x))$$
9. **Strict Context Scoping**:
   Findings are strictly scoped to $(\text{SubjectId}, \text{ActivationContext}, \text{FormularyVersion})$.
10. **Deterministic Receipt Emission**:
    Every anti-skill run must emit a typed, content-addressed `EvaluationReceipt` documenting status, finding hashes, and timing.

---

## 8. Symbol Game Packet Integration

In multi-agent bounded execution, turn packets declare both constructive skills and active anti-skill formularies:

```json
{
  "schema": "omega.symbol-game.typed-packet.v2",
  "authority_effect": "None",
  "subject": {
    "artifact_id": "art_2026_claim_042",
    "wire_type": "ProofCandidate",
    "content_hash": "sha256:7f83b165...",
    "content": "..."
  },
  "domain_characterization": {
    "bounded_context": "operad_theory",
    "carrier_space": "finite_trees"
  },
  "active_skill_generators": [
    "skill_proof_elaborator",
    "skill_type_checker"
  ],
  "active_anti_skill_generators": [
    "anti_model_self_certification",
    "anti_unsupported_promotion",
    "anti_protected_field_loss",
    "anti_overclaim_smuggling"
  ],
  "protected_fields": [
    "subject.artifact_id",
    "subject.wire_type",
    "domain_characterization"
  ],
  "permitted_repair_hints": [
    "weaken_claim_to_shape_only",
    "isolate_sorry_hypothesis"
  ]
}
```

### Execution Protocol

1. **Model Generation**: The agent generates candidate proposals within the conditioned context.
2. **Host Reality Gate**: The host execution engine executes the active $\mathcal{O}^-$ anti-skills against the candidate.
3. **Disposition**:
   * If findings are empty: Emits `EvaluationReceipt(status="Completed")` and proceeds.
   * If repairable findings exist: Routes subject and findings to an $\mathcal{O}_{\text{repair}}$ generator.
   * If fatal findings exist: Emits `ProposedDisposition::Refuse` and halts forward transition.

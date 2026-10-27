---
documentation_contract: symbol-game-documentation/v1
title: "nf_02_lamarckian_pfp_adversary_loop: Normative Form for the Lamarckian PFP-Adversary Integration Loop"
kind: normal-form-specification
audience:
  - researchers
  - engineers
  - coding-agents
status: active
maturity: draft
claim_status: verified
authority_effect: "None"
source_paths:
  - product_planning_office/plans/epics/oegpciv/epic_pciv_v10rc.md
  - education/documentation/010_oepciv/01_v10rc_system_design_and_integration.md
prerequisites:
  - ../00_index.md
  - ../01_v10rc_system_design_and_integration.md
related:
  - nf_01_prompt_society_and_civilization.md
last_verified: 2026-10-09
---

# nf_02_lamarckian_pfp_adversary_loop: Normative Form for the Lamarckian PFP-Adversary Integration Loop

**AuthorityEffect:** None.  
**Normal Form Schema ID:** `urn:core:nf:prompt_civilization:lamarckian_pfp_adversary_loop:v1.0.0`

---

## 1. Trace and State Machine Algebra

The Lamarckian cycle couples dialectical falsification in `adversary` with exact cochain measurement in `pfp` (PFP) and genealogical adaptation in `pciv`:

$$\mathcal{T}_{\text{loop}} = \langle P_0, \mathcal{G}_g \rangle \xrightarrow{\text{Adversary Dialectic}} \text{Artifact } \mathcal{A} \xrightarrow{\text{PFP Measurement}} \text{Defect Witness } \mathbf{W} \xrightarrow{\text{OEEIS Thymus}} \text{Antibody } \alpha \xrightarrow{\text{Forge}} \mathcal{G}_{g+1}$$

```text
Sequence Diagram of the Lamarckian Feedback Loop:

Adversary Swarm             PFP Engine              OEEIS Immune           PromptCiv Forge
     │                        │                       │                        │
     │ 1. Run 7-Act Bout      │                       │                        │
     │    (Acts I to V)       │                       │                        │
     │───────────────────────>│                       │                        │
     │                        │ 2. Exact Cochain      │                        │
     │                        │    Extraction         │                        │
     │                        │    (Phi1 > 0 residual)│                        │
     │                        │──────────────────────>│                        │
     │                        │                       │ 3. Thymic Screening    │
     │                        │                       │    (Negative Controls) │
     │                        │                       │───────────────────────>│
     │                        │                       │                        │ 4. Insert into
     │                        │                       │                        │    Plastic Scaffold
     │                        │                       │                        │    (Core Preserved)
     │                        │                       │                        │
     │<────────────────────────────────────────────────────────────────────────│
     │ 5. Child Genome G_{g+1} spawned for subsequent bout execution           │
```

---

## 2. Invariant Transition Rules

1. **Rule of Protected Core Invariance:** Let $\mathcal{P} = \text{Core}(\mathcal{G}_g)$ be the canalized protected spans. For any Lamarckian mutation $\Delta_{\alpha}$,
   $$\text{Core}(\mathcal{G}_{g+1}) \equiv \text{Core}(\mathcal{G}_g)$$
   Any mutation modifying $\mathcal{P}$ is rejected fail-closed before compilation.
2. **Rule of Witness Grounding:** No antibody $\alpha$ may be synthesized or injected without an authentic cryptographic receipt linking $\alpha$ to a concrete falsification witness (AST failure, failed test assertion, or non-zero rational cochain residual $\Phi_1 > 0$).
3. **Rule of Attenuated Influence:** The insertion weight of an antibody $\alpha$ decreases strictly with generation hop distance:
   $$w(\alpha, d) = \left(\frac{1}{2}\right)^d, \quad d = g_{\text{current}} - g_{\text{origin}}$$
   If $d > 10$, the antibody must either undergo formal constitutional canalization or be evaporated.

---

## 3. Normative Receipt Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "LamarckianMutationReceiptV1",
  "type": "object",
  "required": [
    "receipt_id",
    "parent_genome_id",
    "child_genome_id",
    "falsification_witness_sha256",
    "cochain_residual",
    "antibody_id",
    "hop_distance",
    "attenuation_weight",
    "created_utc"
  ],
  "properties": {
    "receipt_id": { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "parent_genome_id": { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "child_genome_id": { "type": "string", "pattern": "^sha256:[0-9a-f]{64}$" },
    "falsification_witness_sha256": { "type": "string", "pattern": "^[0-9a-f]{64}$" },
    "cochain_residual": {
      "type": "object",
      "required": ["phi1", "gamma2", "xi"],
      "properties": {
        "phi1": { "type": "string" },
        "gamma2": { "type": "string" },
        "xi": { "type": "string" }
      }
    },
    "antibody_id": { "type": "string" },
    "hop_distance": { "type": "integer", "minimum": 1, "maximum": 10 },
    "attenuation_weight": { "type": "string", "pattern": "^[0-9]+/[1-9][0-9]*$" },
    "created_utc": { "type": "string", "format": "date-time" }
  },
  "additionalProperties": false
}
```

---

## 4. Claim Discipline & Epistemic Statement

1. **What this supports:** Specifies the normative state machine, mathematical invariants, and cryptographic receipt format governing Lamarckian retro-inheritance across PFP and Adversary.
2. **What this does not support:** Does not establish that every Lamarckian mutation improves task accuracy; fitness must be verified post-hoc by independent challenge checkers.
3. **Narrowest defensible claim:** Provides a mathematically bounded mechanism for incorporating failure signals into child prompt genomes without corrupting immutable core directives.
4. **Next test needed:** End-to-end integration test executing `run-bout` with simulated cochain defect and verifying emission of `LamarckianMutationReceiptV1`.

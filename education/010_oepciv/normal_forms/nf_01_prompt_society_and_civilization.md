---
documentation_contract: symbol-game-documentation/v1
title: "nf_01_prompt_society_and_civilization: Normative Form for Prompt Societies and Civilizations"
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
  - ../normal_forms/normal_form_contract_schema.yaml
  - nf_02_lamarckian_pfp_adversary_loop.md
last_verified: 2026-10-09
---

# nf_01_prompt_society_and_civilization: Normative Form for Prompt Societies and Civilizations

**AuthorityEffect:** None.  
**Normal Form Schema ID:** `urn:core:nf:prompt_civilization:society_and_civilization:v1.0.0`

---

## 1. Mathematical Definition

A **Prompt Society** $\mathcal{S}$ is a 6-tuple:
$$\mathcal{S} = \langle \text{id}, \mathcal{D}_{\text{proto}}, \mathfrak{F}, \mathbf{R}_{\text{task}}, \mathbf{F}_{\mathbb{Q}}, \mu_{\text{migr}} \rangle$$
where:
1. $\text{id} \in \Sigma_{\text{hex}}^{64}$ is the immutable canonical SHA-256 identifier of the society.
2. $\mathcal{D}_{\text{proto}}$ is the formal domain protocol specification governing task semantics.
3. $\mathfrak{F} = \{\mathcal{F}_1, \dots, \mathcal{F}_M\}$ is the set of member prompt families.
4. $\mathbf{R}_{\text{task}}$ is the deterministic task router mapping incoming $P$ instances to optimal candidate families.
5. $\mathbf{F}_{\mathbb{Q}} \subset \mathbb{Q}^4$ is the multi-objective Pareto frontier of evaluated member families.
6. $\mu_{\text{migr}}$ is the bounded migration operator governing inter-society transfer.

A **Prompt Civilization** $\mathcal{C}$ is a 5-tuple:
$$\mathcal{C} = \langle \text{id}_{\text{civ}}, \{\mathcal{S}_1, \dots, \mathcal{S}_K\}, \mathcal{I}_{\text{global}}, \mathcal{B}_{\text{pool}}, \mathcal{G}_{\text{epoch}} \rangle$$
where:
1. $\text{id}_{\text{civ}}$ is the civilization root identifier.
2. $\{\mathcal{S}_k\}_{k=1}^K$ is the set of constituent societies.
3. $\mathcal{I}_{\text{global}}$ is the shared epistemic antibody and immune registry (`OEEIS`).
4. $\mathcal{B}_{\text{pool}} \in \mathbb{N}$ is the global token/resource reservation budget.
5. $\mathcal{G}_{\text{epoch}} \in \mathbb{N}$ is the monotonic governance epoch counter.

---

## 2. Invariant Laws

1. **Law of Non-Self-Promotion:** A prompt family $\mathcal{F} \in \mathcal{S}$ cannot evaluate its own execution outputs or unilaterally adjust its own coordinates on $\mathbf{F}_{\mathbb{Q}}$.
2. **Law of Pareto Conservation:** A candidate family $\mathcal{F}_{\text{cand}}$ replaces $\mathcal{F}_{\text{active}}$ in society membership if and only if $\mathcal{F}_{\text{cand}}$ weakly dominates $\mathcal{F}_{\text{active}}$ on the exact rational Pareto frontier and strictly dominates on at least one objective coordinate:
   $$\forall j \in \{1,\dots,4\}, \, x_j(\mathcal{F}_{\text{cand}}) \ge x_j(\mathcal{F}_{\text{active}}) \quad \land \quad \exists k \in \{1,\dots,4\}, \, x_k(\mathcal{F}_{\text{cand}}) > x_k(\mathcal{F}_{\text{active}})$$
3. **Law of Bounded Migration:** Inter-society migration between $\mathcal{S}_i$ and $\mathcal{S}_j$ requires explicit taxonomic compatibility and is bounded by the migration quota $Q_{\text{migr}} \le 0.05 \cdot |\mathfrak{F}_j|$ per governance epoch.
4. **Law of Budget Solvency:** $\sum_{k=1}^K \text{Reserved}(\mathcal{S}_k) \le \mathcal{B}_{\text{pool}}$ holds strictly across all concurrent executions. Overdraft attempts yield immediate typed refusal (`BUDGET_OVERDRAFT_REFUSED`).

---

## 3. Normative JSON Schema (not verified RFC 8785 encoder conformance)

[Declared] This schema and its format-compatibility target are requirements, not evidence that a Python or Rust encoder implements them. The recorded verification metadata does not establish serializer conformance. Keep the schema and requirements below unchanged; bind any digest result to its actual codec and source-bound checks.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PromptSocietyV1",
  "type": "object",
  "required": [
    "society_id",
    "domain_protocol",
    "family_ids",
    "aggregate_fitness_vector",
    "migration_policy",
    "created_utc"
  ],
  "properties": {
    "society_id": {
      "type": "string",
      "pattern": "^sha256:[0-9a-f]{64}$"
    },
    "domain_protocol": {
      "type": "string"
    },
    "family_ids": {
      "type": "array",
      "items": { "type": "string" }
    },
    "aggregate_fitness_vector": {
      "type": "object",
      "required": ["accuracy_rational", "cost_rational", "robustness_rational"],
      "properties": {
        "accuracy_rational": { "type": "string", "pattern": "^[0-9]+/[1-9][0-9]*$" },
        "cost_rational": { "type": "string", "pattern": "^[0-9]+/[1-9][0-9]*$" },
        "robustness_rational": { "type": "string", "pattern": "^[0-9]+/[1-9][0-9]*$" }
      }
    },
    "migration_policy": {
      "type": "object",
      "required": ["max_incoming_per_epoch", "taxonomic_admissibility"],
      "properties": {
        "max_incoming_per_epoch": { "type": "integer", "minimum": 0 },
        "taxonomic_admissibility": { "type": "array", "items": { "type": "string" } }
      }
    },
    "created_utc": {
      "type": "string",
      "format": "date-time"
    }
  },
  "additionalProperties": false
}
```

---

## 4. Claim Discipline & Epistemic Statement

1. **What this supports:** Formally defines the normative schema, mathematical state space, and invariant laws for prompt societies and civilizations.
2. **What this does not support:** Does not imply that societies possess autonomous legal or moral personhood; they are deterministic computational coordination structures.
3. **Narrowest defensible claim:** The schema provides an unambiguous, machine-checkable standard for grouping prompt families under shared task protocols with strict budget conservation.
4. **Next test needed:** Schema validation tests against synthetic and live society fixtures in `pciv/tests/unit/test_society_schema.py`.

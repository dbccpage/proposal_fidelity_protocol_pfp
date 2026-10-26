---
kind: note
authority_effect: None
status: live
owner: techne-shared-corpus-custodian
title: "Omega Engine Operadic Architecture: Coloured Operads, Planar Trees, and Capability Slices"
file_name: "categorical_architecture.md"
file_location: ".agents/skills/_shared/"
status_operad: "Crystallized"
invariance_level: "Tier 10"
logic_system: "Coloured Operad Theory / OEWAS Planar Operational Semantics"
substrate: "Markdown / Multi-Agent Swarms"
version: "v2.0.0"
---

# Omega Engine Operadic Architecture

**Series:** 008_engine_runtime / Meta-Architecture  
**Status:** Crystallized (v2.0.0)  
**AuthorityEffect:** `None`  

---

## 1. Mathematical Foundation: Coloured Operad $\mathcal{O}_{\text{OEWAS}}$

The Omega Engine agentic system is structured as a **symmetric coloured operad** (equivalently, a **multicategory**) $\mathcal{O}$ over a finite set of **10 colours** $\mathfrak{C}$, matching the runtime definition in `.agents/operad/operad_signature.json`:

$$\mathfrak{C} = \{\text{State}, \text{Proof}, \text{Paper}, \text{Code}, \text{Contract}, \text{Receipt}, \text{Ledger}, \text{Diagram}, \text{Audit}, \text{Post}\}$$

```text
       OPERAD OPERATIONS (Skills: f ∈ O(C₁, ..., Cₙ; C_out))
                     │
                     ├──> PLANAR SUBSTITUTION TREES (Workflows: γ(f; g₁, ..., gₙ))
                     │         │
                     │         └──> EVALUATION ALGEBRAS (Agents: Sub-Operad Slices O_A)
                     ▼
       INVARIANT CONSTRAINTS & TEMPLATES (_shared & _templates)
```

| Operadic Entity | Agentic Realization | Filesystem Locus | Semantics & Execution Law |
|:---|:---|:---|:---|
| **Colours** ($C \in \mathfrak{C}$) | Artifact Types | Domain representations | The 10 typed boundary carriers (`Code`, `Proof`, `Paper`, `Receipt`, etc.). |
| **Operations** ($f \in \mathcal{O}(C_1, \dots, C_n; D)$) | **Skills** | `.agents/skills/<skill>/SKILL.md` | Atomic multi-input typed transformations of declared arity $n \ge 1$ and target colour $D$. `AuthorityEffect: None`. |
| **Planar Trees** ($\gamma(f; g_1, \dots, g_n)$) | **Workflows** | `.agents/workflows/<flow>.md` | Multi-stage operadic substitutions composing skills into verified pipelines (`/rip-papers`, `/rip-sprints`, `/rip-code`). |
| **Sub-Operad Slices** ($\mathcal{O}_A \subseteq \mathcal{O}$) | **Agents** | `.agents/agents/<agent>.md` | Evaluation algebras defining authorized colour subsets, licensed operations, model tiers (Opus/Sonnet/Haiku), and non-waivable authority ceilings. |

---

## 2. Operad Operations (Skills)

A Skill is an operation $f \in \mathcal{O}(C_1, \dots, C_n; C_{\text{out}})$ with declared arity $n \ge 1$:

- **Frontmatter Typing:**

  ```yaml
  operad_source_colours: ["Paper", "Proof"]
  operad_target_colour: "Paper"
  operad_arity: 2
  operad_residual: "unknown"
  ```

- **Invariants:**
  1. **Typed Boundary:** Maps precisely the declared sequence of source colours into the declared target colour.
  2. **Budget Discipline:** Maximum 300 lines / 20,480 bytes. Detailed playbooks, large prompt templates, or historical evidence belong in `references/`.
  3. **Non-Overclaiming:** Emits explicit failure receipts (`Result[T, E]`); never converts empirical test passes into mathematical proofs. `AuthorityEffect: None`.

---

## 3. Planar Tree Substitution (Workflows)

Workflows are **planar operadic compositions** evaluated through the standard substitution functor $\gamma$:

$$\gamma: \mathcal{O}(C_1, \dots, C_n; D) \times \prod_{i=1}^n \mathcal{O}(A_{i,1}, \dots, A_{i,k_i}; C_i) \longrightarrow \mathcal{O}(A_{1,1}, \dots, A_{n,k_n}; D)$$

- **Implementation Substrate:** Implemented deterministically in `omega_engine_operads/domain/planar_substitution.py`.
- **Associativity & Unit Laws:** Composition trees satisfy strict operadic associativity:
  $$\gamma(\gamma(f; g_1, \dots, g_n); h_1, \dots, h_m) = \gamma(f; \dots, \gamma(g_i; \dots), \dots)$$
  with identity operations $\mathrm{id}_C \in \mathcal{O}(C; C)$ acting as two-sided units.
- **Fail-Closed Staging:** Intermediate handoffs are typed by colour; if stage $k$ produces an audit defect or unverified receipt, downstream operations refuse substitution.

---

## 4. Evaluation Algebras (Agents as Sub-Operad Capability Slices)

An Agent is an **evaluation algebra** over a restricted sub-operad $\mathcal{O}_A \subseteq \mathcal{O}$, documented in `.agents/operad/agent_capability_slices.json`:

- **Sub-Operad Carrier:** The subset of colours $\mathfrak{C}_A \subseteq \mathfrak{C}$ the agent can inspect or emit.
- **Licensed Operations:** The exact subset of skills the agent is authorized to invoke.
- **Authority Ceiling:** Enforces that no agent (except explicit human authorization) can mint authority, promote releases, or self-certify test results.
- **Model Reasoning Tier:**
  - **Opus:** Complex multi-step reasoning, mathematical synthesis, adversary evaluations (`panep-math-and-physics-prof`, `blackrod`, `techne-vp`).
  - **Sonnet:** Formulaic execution, code review, test construction (`techne-code-soviet-builder`, `autoskill`).
  - **Haiku:** Lightweight validation, gate checks, and routing.

---

## 5. Meta-Infrastructure (`_shared` & `_templates`)

- **`_shared/` (Operadic Invariants):** Holds the shared 10-colour signatures, family registries (`family_registry.md`), and sprint gate specifications (`sprint_gates.md`).
- **`_templates/` (Scaffolding):** Standard templates for minting new Operad Operations (`operad_operation.md`), Composite Pipelines (`operad_pipeline.md`), and Agent Slices (`agent_slice.md`).

AuthorityEffect: None.

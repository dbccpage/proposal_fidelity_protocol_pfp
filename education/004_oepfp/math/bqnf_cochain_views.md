---
documentation_contract: symbol-game-documentation/v1
title: 'Application Note: Discrete Hodge Cochains and Database View Maintenance (BQNF)'
kind: application-reference
audience:
- researchers
- database-engineers
- coding-agents
status: active
maturity: emerging
claim_status: verified
authority_effect: "None"
mathematical_status:
  definitions:
    - schema_to_complex_mapping
    - view_invariant_cochain_constraint
    - transaction_update_classification
  prose_theorems:
    - exact_updates_preserve_view_closure
    - coexact_updates_require_view_refresh
    - harmonic_residuals_indicate_schema_dependencies
  lean_theorems: []
  finite_computations: []
  declared_policies: []
  applications:
    - incremental_view_maintenance
    - relational_schema_hodge_decomposition
  open_conjectures: []
coefficient_domain: "ℚ"
runtime_dependency: "Chapter 04 (Minimal Representatives and Hodge Decomposition)"
governance_dependency: "None"
---

# Application Note: Discrete Hodge Cochains and Database View Maintenance (BQNF)

**Status:** Downstream Mathematical Application
**Context:** Application of discrete cochain complexes and combinatorial Hodge decomposition (Chapter 04) to relational database view maintenance and Boundary-Quotient Normal Form (BQNF).
**Authority:** None. Mathematical model of relational constraints.

---

## 1. Schema-to-Complex Mapping & View Output Maps

An abstract cochain complex being exact does not automatically ensure database consistency or eliminate view recomputation. To connect discrete cochain theory to database view maintenance, an explicit combinatorial model must define the complex, the state encoding, and the view evaluation mapping:

1. **0-Cochains ($C^0$):** Loci correspond to base relation primary keys, row entities, or local tuple states.
2. **1-Cochains ($C^1$):** Directed edges represent relational foreign-key references, attribute update deltas, or materialized view columns.
3. **2-Cells ($C^2$):** Oriented faces represent integrity constraints, foreign-key cycles, or view definition dependencies.
4. **View Invariant Constraint:** A database state $c \in C^1$ is defined to be *view-consistent* when its constraint evaluation 2-cochain vanishes:
   $$d_1 c = 0$$
5. **View-Output Evaluation Map:** Materialized view outputs are extracted via an explicit evaluation map:
   $$\operatorname{View}: C^1 \longrightarrow \mathcal{V}$$
   where $\mathcal{V}$ is the space of observable materialized relation contents.

---

## 2. Transaction Update Classification via Hodge Decomposition

Let $K$ be a finite cell complex modeling the relational schema, equipped with a positive-definite diagonal inner product on each cochain group $C^0, C^1, C^2$ over $\mathbb{Q}$.

By discrete Hodge decomposition (Chapter 04, Section 4):
$$C^1 = \operatorname{im}(d_0) \oplus \mathcal{H}^1 \oplus \operatorname{im}(d_1^*)$$

Any incremental update delta cochain $\Delta c \in C^1$ decomposes **uniquely** into orthogonal cochain components:
$$\Delta c = \Delta c_{\mathrm{exact}} + h + \Delta c_{\mathrm{coexact}}$$
where $\Delta c_{\mathrm{exact}} \in \operatorname{im}(d_0)$, $h \in \mathcal{H}^1 = \ker(d_1) \cap \ker(d_0^*)$, and $\Delta c_{\mathrm{coexact}} \in \operatorname{im}(d_1^*)$.
*(Note: While the cochain components $\Delta c_{\mathrm{exact}}, h, \Delta c_{\mathrm{coexact}}$ are unique, the potentials $\alpha \in C^0$ satisfying $d_0 \alpha = \Delta c_{\mathrm{exact}}$ and $\beta \in C^2$ satisfying $d_1^* \beta = \Delta c_{\mathrm{coexact}}$ need not be unique if $\ker(d_0) \ne \{0\}$ or $\ker(d_1^*) \ne \{0\}$).*

### 2.1 Exact Updates and View Maintenance Discipline
Because $d_1 \circ d_0 = 0$ identically:
$$d_1(\Delta c_{\mathrm{exact}}) = d_1(d_0 \alpha) = 0$$
Exact updates preserve the constraint $d_1 c = 0$.

> **Constraint Preservation vs. View Maintenance Boundary:**
> Preserving $d_1 c = 0$ does **not** prove that a materialized view requires no refresh!
> *Minimal Linear Model:* Encode a base attribute $b$ and its materialized copy $v$ by $c = (b, v) \in C^1$, with $d_1 = (-1, 1)$ so that $d_1 c = v - b = 0$, and gauge shift $d_0 \alpha = (\alpha, \alpha)$. An exact delta shifts both values: $c + d_0 \alpha = (b + \alpha, v + \alpha)$. The constraint $d_1(c + d_0 \alpha) = 0$ still holds, but the materialized value $v$ has changed. Unless the system executes an update to $v$, the view becomes stale.
> An exact update eliminates view recomputation only when the view evaluation map is **gauge-invariant**:
> $$\operatorname{View}(c + d_0 \alpha) = \operatorname{View}(c)$$
> or when an explicit local transformation rule updates the view without evaluating global joins.

### 2.2 Coexact Updates ($d_1^* \beta \ne 0$)
Because $d_1(d_1^* \beta) \ne 0$ on non-zero coexact cochains (as $\ker(d_1) \perp \operatorname{im}(d_1^*)$):
$$d_1(\Delta c) = d_1(d_1^* \beta) \ne 0$$
Coexact updates explicitly alter or violate declared view constraints. These correspond to transactional modifications that change foreign-key linkages or aggregated values, requiring active, non-local view refresh transactions.

### 2.3 Harmonic Residuals ($h \in \mathcal{H}^1, h \ne 0$) & Schema Normalization Policy
Harmonic updates satisfy:
$$d_1 h = 0 \quad \text{and} \quad d_0^* h = 0$$
Harmonic cochains preserve declared cycle constraints ($d_1 h = 0$) but cannot be resolved by any local gauge repair ($h \notin \operatorname{im}(d_0)$).
A non-zero harmonic class represents a non-contractible global topological feature across relations. It does **not** automatically indicate a defective relational database schema; intentional cyclic schemas (such as bidirectional references or valid circular dependencies) naturally host non-trivial harmonic spaces. Eliminating harmonic classes via Boundary-Quotient Normal Form (BQNF) factorization is a **declared database design policy**, not a forced mathematical consequence of Hodge theory.

---

## 3. Claim Hygiene

1. **What this supports:** Shows how discrete Hodge decomposition classifies incremental database updates into gauge shifts, constraint-violating deltas, and topological schema cycles on finite discrete relational schemas under declared state and view-output mappings.
2. **What this does not support:** Does not prove that arbitrary exact deltas require zero maintenance without establishing view-output gauge invariance; does not prove that non-zero harmonic classes indicate defective schemas; does not establish automated SQL execution or ACID properties.

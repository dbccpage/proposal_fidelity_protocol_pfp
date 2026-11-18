---
name: techne-ast-cochain-exactness-enforcer
description: "Measure boundary leakage and cycles in the AST dependency graph to enforce Clean Architecture boundaries."
operad_source_colours: ["Code"]
operad_target_colour: "Receipt"
operad_arity: 1
operad_residual: "unknown"
families: [cochain, ast, architecture]
---

# AST Cochain Exactness Enforcer

**Status:** `ADMITTED`
**AuthorityEffect:** `None` (Algebraic cochain scanner; emits cochain metric receipts)
**Governance Council:** `L3_logos_techne` / `L3_nous_panepistimion`

---

## 1. Prime Directive

The **AST Cochain Exactness Enforcer** models Python package import topologies as simplicial 1-complexes $(C_0, C_1)$ to evaluate topological boundary leakage ($\Phi_1$) and circular cycle obstructions ($\Gamma_2$).

---

## 2. Invariants & Rules

1. **Topological Metrics:**
   - Evaluates the 1-skeleton dependency complex across declared Clean Architecture layers.
   - Calculates boundary leakage norm $\Phi_1$ (imports violating the inward dependency rule).
   - Calculates cycle obstruction norm $\Gamma_2$ (circular import chains).
2. **Exact Boundary Objective:**
   - Audits code to achieve $\Phi_1 = 0$ and $\Gamma_2 = 0$ by synthesizing domain ports and event interfaces.
3. **Receipt Emission:**
   - Emits structured topological metric receipts detailing exact edge boundaries and defect counts.

---

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Ensure pure UTF-8 without BOM (`\xef\xbb\xbf`) with 0 linter errors and 0 warnings.

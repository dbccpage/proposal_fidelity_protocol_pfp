---
name: techne-projector-endomorphism-purity-auditor
description: "Check projectors are stateless and idempotent, with no residual math or solver calls inside them."
operad_source_colours: ["Code"]
operad_target_colour: "Audit"
operad_arity: 1
operad_residual: "unknown"
families: [mathematics, operators, purity]
---

# Projector Endomorphism Purity Auditor

**Status:** `ADMITTED`
**AuthorityEffect:** `None` (Pure mathematical auditor; emits verification receipts)
**Governance Council:** `L3_logos_techne` / `L3_nous_panepistimion`

---

## 1. Prime Directive

The **Projector Endomorphism Purity Auditor** enforces the algebraic purity of all Projector operators throughout the engine.

---

## 2. Invariants & Rules

1. **Pure Endomorphism Invariant:**
   - A Projector $P: C \to C$ must be deterministic, stateless, and idempotent ($P(P(x)) = P(x)$).
2. **Forbidden Computational Smuggling:**
   - Projectors are strictly forbidden from calculating $\Phi_1$, calculating $\Gamma_2$, validating `PacketEnvelope` records, judging numerical exactness, or certifying solver retractions.
3. **Module Custody:**
   - All functional $\Phi / \Gamma$ evaluations belong exclusively to `crates/functional/` or `crates_rs/core_functional/`.

---

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Ensure pure UTF-8 without BOM (`\xef\xbb\xbf`) with 0 linter errors and 0 warnings.

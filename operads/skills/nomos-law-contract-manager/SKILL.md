---
name: nomos-law-contract-manager
description: "Manage contract specs under omega_contracts; enforce Rust and Python contract parity; refine URN schemas."

operad_source_colours: ["Contract", "Code"]
operad_target_colour: "Audit"
operad_arity: 2
operad_residual: "unknown"
---

# nomos-law-contract-manager

## authority_effect_ceiling: None

## 1. Governance & Mandate

- **Council Jurisdiction:** Council Nomos (Greek for Law, Rule, Custom, and Order).
- **Scope:** All contract YAML definitions under `omega_engine/crates/omega_contracts/src/contract_canonical_definitions/`, Rust contract interfaces (`omega_contracts`), and Python contract mirrors (`omega_engine_py/omega_contracts`).
- **Authority Ceiling:** `AuthorityEffect: None`. Contract specifications define invariants; runtime verification and formal proofs grant authority.

---

## 2. Core Responsibilities

1. **Rust-Python Contract Parity:**
   Ensure that every contract schema, descriptor, and validator in `omega_engine/crates/omega_contracts` has an identical implementation and test fixture in `omega_engine_py/omega_contracts`.

2. **Mathematical Contract Hygiene:**
   Inspect all contracts under `contract_canonical_definitions/math/` (e.g. `morphism.contract.yaml`, `functor.contract.yaml`, `category.contract.yaml`) for incomplete domain/codomain schemas, missing laws, or vague negative test specifications.

3. **Core Category Standardization:**
   Maintain the 9 canonical core categories (`00_core_constitution`, `01_core_state`, `02_core_evidence`, `03_core_obstruction`, `05_core_governance`, `06_core_execution`, `07_core_products`, `08_core_lifts`, `09_core_packets`) and verify that all contract YAML files reside in their designated `{NN}_core_{slug}` folders.

---

## 3. Verification & Execution

When called manually or by `/rip-lawyers`:

1. Run `pwsh scripts/v1_contract_gate.ps1` to verify all v1 contract schemas.
2. Run `cargo test -p omega_contracts` and `pytest omega_engine_py/omega_contracts`.
3. Emit a `nomos_law_contract_manager_receipt` reporting:
   - `CONTRACT_SCHEMA_GATE: PASS | FAIL` ext
   - `RUST_PYTHON_PARITY: PASS | DESYNCED` ext
   - `MATH_TEMPLATE_HYGIENE: VERIFIED | NEEDS_REPAIR` ext

## Sub-Module: Ledger Auditor, Stem Gate & PPO Governance

1. **CODA Loss Ledger Audit:** Audit multi-jurisdictional ledgers for representation loss, nominee singularities, and unpriced leverage.
2. **Stem Gate Host Wiring:** Enforce opt-in host wiring for `omega_morphism_stem_gate.py` strict mode and dual-side CI when flagged.
3. **PPO Governance & Forgery Escalation Cascade:** Enforce exclusive plan/saga modification & completion rights (`OOUTWIRE`, `BLACKROD`, `omega-engine-product-manager`), lower `snake_case` naming law (`RULE_NAMING_CONVENTION_001`), 2-official retrospective audit pass, and `/thanatos-nemesis` forgery escalation.

## Related Skills

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).

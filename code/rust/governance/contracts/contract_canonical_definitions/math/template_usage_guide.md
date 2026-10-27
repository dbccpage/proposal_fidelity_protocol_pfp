# Math Contract Authoring & Template Usage Guide

> Canonical guide for creating and authoring mathematical contracts under `core.contract.v1`.
> Governed by Techne Council. AuthorityEffect: None.

---

## 1. Quick Start

1. **Copy the canonical template:**
   ```bash
   cp math_contract.template.yaml my_object.contract.yaml
   ```

2. **Populate core fields:**
   - `contract_id`: `urn:core:math:<snake_case_name>:v1.0.0`
   - `title`: Short descriptive name (e.g., `"Exterior Power"`)
   - `math`: Declare mathematical carrier, symbols, domain, codomain, and formal definition.
   - `requirements` & `laws`: Declare invariant properties, axioms, and algebraic identities.
   - `replay`: Declare deterministic execution requirements.

3. **Wire Rust bindings (if implemented):**
   - Provide `rust_binding` with crate name, module path, symbols, and `required_tests`.
   - If aspirational or not yet implemented in Rust, omit or comment out `rust_binding`.

4. **Validate locally:**
   ```bash
   py -3.12 -c "import yaml; yaml.safe_load(open('my_object.contract.yaml'))"
   py -3.12 governance/contracts/contract_urn_uniqueness.py
   ```

---

## 2. Hard Machine Rules (`CoreContractV1`)

Deserialization is enforced by `CoreContractV1` (`core_contract_core/src/registry/v1_types.rs`) with `#[serde(deny_unknown_fields)]`. Any unrecognized key causes an immediate parser failure.

### Permitted Top-Level Keys
Only the following keys are permitted at top level:
- `schema_version`: Must be exactly `"core.contract.v1"`
- `contract_id`: Must follow `urn:core:math:<snake_case_name>:v<SEMVER>` and be globally unique
- `title`: Human-readable string title
- `kind`: Must be `"math_contract"`
- `status`: Must be one of `active`, `draft`, `deprecated`, `experimental`, `mathematical_wip`, `exact_rational_classifier_implemented`
- `layer`: `"math"`
- `role`: Optional, defaults to `"MathObject"`
- `descriptor`: Machine-authoritative enforcement block
- `math`: Mathematical carrier and notation block
- `requirements`: Required algebraic/topological structures
- `laws`: Invariant mathematical laws and identities
- `replay`: Deterministic replay requirements
- `rust_binding`: Optional binding to concrete Rust implementations
- `negative_tests`: List of refusal/rejection statements
- `doctrine`: Summary and non-role constraints
- `relationships`: Optional sibling links (e.g., `[[other_contract]]`)
- `definition`: Optional alternative formal definition
- `equivalence`: Optional equivalence/isomorphism rules
- `wip`: Optional work-in-progress notes

### Permitted `descriptor` Keys
- `authority_effect`: Strictly `"none"` (or `None`) for mathematical objects
- `evidence_ceiling`: Typically `"ShapeOnly"` (or `"LocalReplay"`)
- `runtime_enforcement`: Strictly `false` for pure math contracts
- `customer_claim_allowed`: Strictly `false`
- `dependencies`: `contracts: []` and `proof_obligations: []`
- `terminals`: `may_emit: []`, `may_support: []`
- `refusals`: `may_emit: []`
- `operator_classes`: `may_support: []`, `must_not_self_assign: true`

---

## 3. The Float Firewall Invariant

- **Exact Rational Floor:** All certifiable mathematical invariants (cohomology classes, $\Phi_1$ quotient obstruction mass, $\Gamma_2$ closure defects, Smith normal forms) MUST be computed over exact rational fields (`num_rational::Ratio<i64>`).
- **Floating-Point Limitation:** IEEE 754 $f64$ arithmetic is strictly prohibited from minting exact certificates or claiming invariant truth. Floating-point routines are classified strictly as `DiagnosticOnly` or `TieBreakerOnly` (e.g. `XiDiagnostic`).

---

## 4. Rust Binding & Verification (`math_contract_gate.rs`)

When `rust_binding` is declared:
```yaml
rust_binding:
  crate: core_linear_algebra
  module: basic_matrix
  symbols:
    - BasicMatrix
  required_tests:
    - basic_matrix_preserves_declared_dimensions
```

1. **Module Resolution:** `math_contract_gate.rs` resolves `crate::module` against `engine/crates_rs/<crate>/src/<module>.rs`.
2. **Symbol Verification:** All declared `symbols` must exist as `pub` types or functions in the target source file.
3. **Test Discharging:** Every test named in `required_tests` must exist as an actual `#[test]` function within the crate. Plain functions or fabricated identifiers fail the gate.
4. **Omission Rule:** If code is not yet written, **omit `rust_binding`**. Do not invent aspirational bindings.

---

## 5. Canonical Template Reference

The canonical template lives at [`math_contract.template.yaml`](math_contract.template.yaml). Copy it directly when authoring new contracts.

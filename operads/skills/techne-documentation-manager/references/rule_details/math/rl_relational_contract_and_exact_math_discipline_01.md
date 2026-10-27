# Detailed definition: Relational Contracts & Exact Math (1)

**AuthorityEffect:** None.

Parent: [Relational Contracts & Exact Math](../../../../../rules/math/rl_relational_contract_and_exact_math_discipline.md). Load for the matching predicate, not every task.

# Rule: Relational Contract & Exact Math Verification Discipline

**AuthorityEffect:** None.

This rule enforces type safety, exact rational arithmetic, null-totality SQL fences, candidate exhaustiveness, and normal form contract boundaries across all relational contracts and exact solvers. Full procedural tutorials and code examples reside in [`governance-exact-solvers`](../../../../governance-exact-solvers/references/relational_math_discipline.md).

---

## 1. Strict Boolean Type Safety & Dataclass Hash Discipline

- **Strict Identity Validation**: When verifying schema-declared boolean fields, never use list membership (`val in [True, False]`). Always assert strict identity: `assert type(val) is bool` (rejecting integer 0 and 1).
- **Value Object Exact-Type Equality & Mypy Narrowing**: Strongly-typed Value Objects governed by `urn:core:governance:value_object_equality:v2.0.0` must enforce exact-type equality via `assert type(self) is type(other)` in `__eq__`. To ensure static type checkers (Mypy) narrow `other: object` to the target type without generating attribute-access errors, immediately follow with `assert isinstance(other, <Class>)` before accessing attributes.
- **Explicit Array Equality**: Dataclasses holding NumPy `ndarray` fields must implement explicit `__eq__` (using `np.array_equal`) and `__hash__` (using `.tobytes()`) to avoid ambiguous boolean truth evaluations.

---

## 2. Exact Rational Arithmetic & Vanishing Gates

- **GCD-Reduced Stepwise Folding**: Represent all discrete Hamiltonian / Wheeler–DeWitt transition amplitudes as signed rational fractions $\sigma_i \frac{N_i}{D_i}$. Compute sums via stepwise GCD-reduced folding; pairwise self-joins and floating-point comparisons are strictly prohibited.
- **Exact Vanishing vs. Tolerances**: Guard $g_3$ (`zero_residual_mass`) must require exact rational zero vanishing: `residual_mass == 0`. Positive policy tolerances in exact algebraic theories are forbidden.
- **Cochain Gauge Invariance vs. Quotient Distance**: In exact cochain repair and gauge optimization, a coboundary gauge shift $c \mapsto c - d_0 \beta$ alters only the representative cochain defect $\|c\|_{1,w}$. The intrinsic quotient distance $\Phi_1([c]) := \min_\alpha \|c - d_0 \alpha\|_{1,w}$ is strictly invariant under all gauge shifts because $[c - d_0 \beta] = [c] \in C^1 / \operatorname{im}(d_0)$. Verifiers, contracts, and solvers must never claim that gauge adjustments reduce or resolve non-zero quotient obstruction $\Phi_1$.
- **Wire Binary Atoms vs. JSON/YAML Decimal Strings**: For exact rational numbers:
  - Wire grammar encodings over $\Sigma_2 = \{0, 1\}^+$ must use binary atom representations for sign, numerator, and denominator (e.g. `op<<10010><sign><num_bin><den_bin>>`).
  - Serialized JSON/YAML documents must represent rationals strictly as canonical coprime strings `"p/q"` ($q > 0, \gcd(|p|, q) = 1$). Raw unparsed floats or mixed decimal encodings in wire payloads are prohibited.

---

## 3. SQL Null-Totality & 3-Valued Logic Fences

- **Totality Preflight**: Ensure all protected facts and evaluation operands are non-null before relational factoring.
- **Null-Safe Pointwise Equality**: Always employ null-safe comparison (`IS DISTINCT FROM`) when validating agreement between global verdicts and local products to prevent `UNKNOWN` evaluations from masking violations.

---

## 4. Candidate Exhaustiveness & Trust Boundaries

- **Set and Cardinality Equality**: Guard $g_5$ (`exhaustive`) must verify exact set and cardinality equality between verified candidate IDs and declared packet candidates (`set(checked_ids) == set(declared_ids) and len(checked_ids) == len(declared_ids)`). Mere count coverage without stable IDs cannot certify exhaustiveness.
- **Attestation vs. Execution**: Companion scripts evaluating caller-supplied booleans must type inputs as `GuardAttestations` and explicitly disclose that they evaluate policy over attestations rather than executing operational pipelines.
- **Terminal Routing Claim Discipline**: Unchecked corpus samples map to `Abstain`. Canonical `Preserve` is strictly reserved for actively machine-checked proofs or verified exhaustively checked finite state spaces.

---

## 5. Genesis Extended Normal Form Four-Pillar Contract Discipline

- **Schema and Hierarchy Compliance**: All normal form contracts in `documentation/2_genesis/normal_forms/` must conform to schema `smplx.nf.contract.v0` and declare `contract_kind: form_contract` or `normal_form_contract`.
- **The Four Pillars Quadrilateral Requirement**:
  1. *Pillar I (Anomaly Exclusion)*: Name the exact insertion, deletion, update, or trajectory redundancy anomaly eliminated (e.g. non-cotransitive distinctions in APNF, labeling permutation redundancy in IGNF, float drift in IRNF, unrepresented attachments in LSNF, spurious interleavings in MTNF, external state leakage in EFNF).
  2. *Pillar II (Lossless Reconstruction)*: Specify the mathematical reconstruction procedure (quotient projection, automorphism cosets, scalar multiplication, or causal poset replay). For extended forms, declare `qualifies_as_true_normal_form: false` with explicit `qualification_gap: no_project_join_theorem`.
  3. *Pillar III (Dependency Preservation)*: State whether all original constraints and laws remain checkable locally within sub-components.
  4. *Pillar IV (Syntactic Decision Procedure)*: Verification must be decidable from the declared schema, carrier size, and constraints, never from contingent runtime row contents.
- **Authorization and Custody Firewall**: Every contract must declare `authorized_by: null` and `certified_implies_authorized: false`. Form certification provides evidence of structural adherence; it confers zero authority to alter execution budgets or license state transitions.
- **Validation Oracle**: Every YAML contract specification must pass `governance.normal_forms.nf_harness.validate_contract_file` with zero defects.

---

## 6. Standards Directory Purity & Pydantic Meta-Schema Discipline (`RULE_STANDARDS_DIR_PURITY_001`)

- **Standards vs. Instances Directory Demarcation**:
  1. Concrete contract instances (e.g., `nf.*.yaml`, `index.yaml`) belong strictly in instance directories (e.g., `contracts_normal_forms/` or `contracts/`).
  2. Normative specifications, meta-schemas, foundational definitions, and executable SQL catalogs belong strictly in dedicated standards directories (e.g., `contracts_nf_standards/`).
  3. **Zero Prose Markdown Slop in Standards Directories**: Standards directories must contain strictly machine-validatable code and declarative data (`.py`, `.yaml`, `.sql`) with zero loose `.md` files. Foundational mathematical definitions and packaged demo catalogs must be structured as typed YAML specifications with corresponding Pydantic models.

- **Pydantic v2 Schema Compilation & Dynamic Loading (`RULE_PYDANTIC_CONTRACT_SCHEMA_001`)**:
  1. *Model Rebuild Invariant*: All Pydantic models defined with `from __future__ import annotations` that use nested or composite model references must explicitly call `Model.model_rebuild()` at the bottom of the module. This prevents `PydanticUserError: class is not fully defined` when loaded dynamically via `importlib.util.spec_from_file_location`.
  2. *Fail-Closed Authorization & Anomaly Gates*: Pydantic model validators for normal form contracts (`NormalFormContract`) must enforce:
     - `certified_implies_authorized` must be strictly `False`.
     - If `hierarchy_level == "normal_form"`, `anomaly_eliminated` must be non-empty and specify an anomaly category other than `none`.
     - Contracts missing required relational profile attributes, SQL projections, or losslessness proofs must fail validation immediately.

- **YAML Mathematical Escaping & Scalar Syntax Hygiene (`RULE_YAML_MATH_ESCAPING_001`)**:
  1. *Colons in Mathematical Strings*: Any mathematical expression or mapping containing a colon followed by a space (e.g. `'Xi: S_0 -> S_0'`, `'D: H_k -> H_k'`) inside a YAML scalar string value must be enclosed in single quotes (`'...'`) or represented using folded block scalars (`>-`). Unquoted colons cause PyYAML scanner errors (`mapping values are not allowed here`).
  2. *TeX Backslash Escaping*: LaTeX mathematical commands inside YAML string values must avoid unescaped backslashes in double-quoted strings (e.g., `"\subseteq"` triggers `unknown escape character`). Use single quotes (`'\subseteq'`) or explicit double backslashes (`"\\subseteq"`).

---

# Detailed definition: Exact Verification & Witness Integrity (1)

**AuthorityEffect:** None.

Parent: [Exact Verification & Witness Integrity](../../../../../rules/math/rl_exact_verification_and_witness_integrity_invariants.md). Load for the matching predicate, not every task.

# Rule: Exact Verification, Value Object & Witness Integrity Invariants

**AuthorityEffect:** None.

This rule codifies exact rational verifiers, fail-closed authorization boundaries, discrete carrier bounds, zero-mutation witness auditing, and typed inverse composition directionality. Cross-reference terminal routing and curved witness invariants: [`rl_terminal_routing_and_curved_witness_invariants.md`](../../../../../rules/math/rl_terminal_routing_and_curved_witness_invariants.md), and cochain defect and descent invariants: [`rl_cochain_defect_and_guarded_descent_invariants.md`](../../../../../rules/math/rl_cochain_defect_and_guarded_descent_invariants.md).

---

## Value Object Exact-Type Equality Invariant

> **Exact-Type Equality Guard:**
>
> 1. All domain Value Objects (`@dataclass(frozen=True)`) must reject cross-class comparisons by asserting `type(self) is type(other)` in `__eq__`.
> 2. Cross-context Value Objects must be tested with automated architecture fitness tests verifying type-confusion rejection.

---

## Exact Verifiers, Authorization Boundaries & Import Order Invariant

> **Exact Arithmetic, Gate Authorization & Module Import Hygiene:**
>
> 1. **Exact Rational Domain & Shape Validation at Verifier Boundaries:**
>    - Certificate verifiers (`ExactnessCertificate.verify()`, `QuotientDistanceCertificate.verify()`) must validate that every witness entry and scalar belongs strictly to the exact rational domain ($\mathbb{Q}$, `fractions.Fraction`, `sympy.Rational`, `num_rational::BigRational`) and that matrix shapes match problem data before performing any algebraic evaluation.
>    - Verifiers must strictly reject floating-point types (`float`, `np.floating`, `sympy.Float`) with `TypeError` or `False`. Finite precision cancellations (e.g. $2^{60} + 1 - 2^{60} \approx 0$) must never be permitted to certify false exact results.
> 2. **Fail-Closed Authorization Gate & Guard Boolean Validation:**
>    - Authorization and admission entry points (such as `evaluate_authority()` or `evaluate_authorization()`) must never trust unverified caller-supplied certificates. Entry points must explicitly invoke `certificate.verify()` and reconcile certificate residuals against guard flags (asserting `(cert.distance == 0) == guards.zero_residual_mass`), emitting a typed refusal on any contradiction.
>    - Halt guard records (such as `HaltGuards`) must enforce strict boolean types (`isinstance(v, bool) and not isinstance(v, (int, str))`), rejecting truthy non-booleans (such as `deterministic="False"`).
> 3. **Strict Candidate Identity & Evidence Binding:**
>    - Review and evaluation guards auditing candidate batches (such as guard $g_5$) must strictly bind submitted evidence to explicit candidate IDs matching declared packet contents (`packet.evaluator_class_e`).
>    - Guards are strictly prohibited from falling back to anonymous numerical counts when IDs are omitted. Evidence describing $k$ checks must never authorize arbitrary candidate packets of size $k$.
>    - Authorization requires strictly consistent positive counts: `len(packet.evaluator_class_e) == candidates_declared == len(checked_candidate_ids) == candidates_checked > 0`.
> 4. **Zero Circular Re-Export & Process-Safe Import Order:**
>    - Public re-exports across package modules must operate independently of process import order.
>    - Swallowing circular imports with `try: from .module import Symbol; except ImportError: pass` is strictly prohibited.
>    - Where mutual cross-layer symbol references exist, modules must employ PEP 562 lazy module attributes (`__getattr__` and `__dir__`) or isolate re-exports in a leaf composition root.
>    - Test suites must verify both import orders (`import module_b; from module_a import Symbol` vs `import module_a; from module_b import Symbol`) in fresh subprocesses.

---

## Mathematical Presentation Equality & Discrete Carrier Boundary Invariant

> **Array Dataclass Equality & Span Carrier Bounds:**
>
> 1. **Explicit Array Equality & Hashing in Dataclasses:**
>    - Python dataclasses holding NumPy arrays (`np.ndarray`) must never rely on default elementwise equality, which raises ambiguous truth value errors in boolean conditionals (`if p1 == p2:`).
>    - Presentation and operator classes must implement explicit `__eq__` asserting `type(self) is type(other)` and evaluating `np.array_equal`, paired with deterministic buffer-byte `__hash__`.
> 2. **Discrete Span Carrier Bounds & Non-Negative Mid-Size:**
>    - Comparison spans $A \xleftarrow{left} M \xrightarrow{right} B$ must validate in `__post_init__` that `mid_size` is a non-negative integer and all map indices lie strictly within declared endpoint carrier bounds (`0 <= idx < carrier_size`), preventing silent middle element loss during composition.
> 3. **Non-Vacuous Finite Algebraic Model Validation:**
>    - Model validators (`validate()`) for finite algebraic structures (groupoids, categories) must never return `True` on empty tables or without verifying identity endomorphism typing, inverse involution/typing, composable pair coverage, and associativity on all composable triples.
> 4. **Inverse Operator Lift Domain Integrity & Non-Orthogonal Anchor Condition:**
>    - Functions inverting operator lifts (e.g. density matrix reconstruction) must validate theorem hypotheses: matrix must be finite, symmetric ($\rho^\top = \rho$), normalized ($\operatorname{Tr}\rho = 1$), and rank-one idempotent ($\rho^2 = \rho$). Mixed states ($\frac{1}{2}I_2$) must be rejected fail-closed.
>    - Reconstruction postconditions must verify that the recovered cochain reproduces the input operator upon re-lifting and that admitted mass matches reconstructed vector norm.
>    - Orientation anchors $\ell$ must certify non-orthogonality ($|\ell(v)| > \mathrm{tol}$) and reject non-finite/NaN inputs. If $\ell(v) = 0$, orientation is unresolvable by that chart; the verifier must return an explicit unresolved pair or fail closed.

---

## Exact Witness Auditor Fidelity & Zero-Mutation Invariant

> **Zero-Mutation Witness Audit Rule:**
>
> 1. **Zero Candidate Mutation:**
>    Verifiers, governors, and audit wrappers must evaluate candidate witnesses strictly intact. They must NEVER coerce, cast, round, or truncate submitted elements (e.g., casting floats or booleans via `int(b)` to convert probabilities or truth values into binary bits).
> 2. **Explicit Typed Refusal for Non-Canonical Types:**
>    Purported witnesses containing non-canonical types (e.g., float probabilities in binary gauge vectors) must be rejected with explicit typed refusals without proceeding to underlying arithmetic verification.
> 3. **Step Totality & Zero-Drop Walk Validation:**
>    Step sequences (e.g., cycle steps, rewriting traces, or graph walks) must be validated in full; verifiers must never silently drop, skip, or filter malformed steps to manufacture a valid sub-witness.
> 4. **Dual Custody of Repaired Witnesses:**
>    If an automated candidate-repair or projection operation is performed, the original candidate and repaired witness must be preserved, recorded, and audited as distinct artifacts; verification must only be attributed to the specific bytes checked.

---

## Typed Inverse-Order Check Invariant (`RULE_TYPED_INVERSE_ORDER_CHECK_001`)

> **Typed Inverse Composition Directionality Law:**
>
> 1. **Explicit Domain and Codomain State:** Inverse identities must be stated with explicit domains and codomains. For maps $Q: V \to Y$ and $R: Y \to V$:
>    - $R \circ Q = \operatorname{id}_V$ defines $R$ as a **left inverse of $Q$** (and $Q$ as a right inverse of $R$).
>    - $Q \circ R = \operatorname{id}_Y$ defines $R$ as a **right inverse of $Q$** (and $Q$ as a left inverse of $R$).
> 2. **Verification & Regression Check:**
>    - Use $Q(x,y) = x$ and $R(x) = (x,0)$ over the binary field $\mathbb{F}_2$ as a regression counterexample: $Q \circ R = \operatorname{id}_Y$ holds, whereas $R \circ Q = \operatorname{id}_V$ fails ($R(Q(0,1)) = (0,0) \ne (0,1)$).
>    - Explanations or proofs that exchange the left and right inverse labels for $R \circ Q = \operatorname{id}_V$ are strictly rejected.

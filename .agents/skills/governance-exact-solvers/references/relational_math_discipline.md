# Relational Contract & Exact Math Verification Discipline

**AuthorityEffect:** None.

This reference documents exact rational arithmetic, relational contract type safety, null-totality SQL fences, and candidate exhaustiveness for exact solvers and validators.

---

## 1. Strict Boolean Type Checking in Python Validators

* **Python Type Traps:** In Python, `bool` is a subclass of `int`. Consequently, `1 in [True, False]` and `0 in [True, False]` both evaluate to `True`.
* **Mandatory Invariant:** When verifying schema-declared boolean fields, never use list membership. Always assert strict identity:
  ```python
  assert type(val) is bool  # strictly rejects int 0 and int 1
  ```
* **Multi-type Fields:** If a field admits booleans or specific strings (e.g. `'conditional'`), enforce:
  ```python
  assert type(val) is bool or val == "conditional"
  ```
* **Mutation Testing Requirement:** Any validator asserting boolean types must include mutation tests proving rejection of `0` and `1`.

---

## 2. Exact Rational Arithmetic for Discrete Solvers (Hamiltonian / Wheeler–DeWitt)

* **Anti-Pattern (Pairwise Self-Joins):** Queries evaluating $\sum_{i \ne j} n_i d_j$ fail for $k=1$ (single-term transitions disappear) and compute algebraically invalid sums for $k \ge 3$ ($\sum_{i \ne j} n_i d_j \ne \sum_i n_i \prod_{j \ne i} d_j$). Furthermore, unreduced denominator multiplication overflows 64-bit integers.
* **Mandatory Invariant:** Represent all transition amplitudes as signed rational fractions $\sigma_i \frac{N_i}{D_i}$ with $D_i > 0$. Compute exact rational sums via stepwise GCD-reduced rational folding:
  $$\frac{N_{\text{net}}}{D_{\text{net}}} = \sum_{i=1}^k \sigma_i \frac{N_i}{D_i} = 0 \iff N_{\text{net}} = 0$$
* **Mandatory Regression Coverage:**
  1. Single-term contribution ($1/7 \ne 0$).
  2. Two-term cancellation ($1/2 - 1/2 = 0$).
  3. Two-term false zero ($1/2 - 1/3 = 1/6 \ne 0$).
  4. Three-term false zero ($1/2 + 1/3 - 3/5 = 7/30 \ne 0$).
  5. Three-term true zero ($1/2 + 1/3 - 5/6 = 0$).
  6. Arbitrary precision / large integers beyond $10^{18}$.

---

## 3. Null-Totality & 3-Valued Logic Fences in Relational Factoring

* **Anti-Pattern (Inequality on Nulls):** In SQL, `NULL <> 1` and `0 <> NULL` evaluate to `UNKNOWN`, masking factorization violations when filtering `WHERE global_verdict <> local_product`.
* **Mandatory Invariants:**
  1. **Totality Preflight:** Verify that all protected facts and evaluation operands are non-null:
     ```sql
     SELECT * FROM trace_fact 
     WHERE F_value IS NULL OR global_verdict IS NULL OR local_product IS NULL;
     ```
  2. **Null-Safe Comparisons:** Always use null-safe inequality (`IS DISTINCT FROM`) when checking pointwise agreement:
     ```sql
     SELECT * FROM trace_fact 
     WHERE global_verdict IS DISTINCT FROM local_product;
     ```

---

## 4. Claim & Evidence Discipline on Terminal Routing

* **Mandatory Invariant:** Finite instance corpus checks (absence of counterexamples in sample traces) and unverified theoretical statements must strictly map to `Abstain`:
  * `ObservedNoMixedFiberInCorpus` $\to$ `Abstain`
  * `ClaimedViewDeterminate` $\to$ `Abstain`
* **Preserve Restrictions:** Canonical `Preserve` is strictly reserved for actively machine-checked proofs or verified exhaustively checked finite state spaces (`verification_status: machine_checked` and `verifier_required: true`).

---

## 5. Closed Predicate Registries for Conditional Contract Obligations

* **Mandatory Invariant:** When a contract declares `loss_ledger_required: conditional` or similar conditional obligations, it must declare an explicit `loss_ledger_trigger_id` that resolves to a registered operational predicate in the closed `loss_ledger_trigger_registry`. Free-form text commentary without an executable trigger ID is forbidden.

---

## 6. Exact Vanishing vs. Numerical Tolerances in Residual Gates

* **Anti-Pattern (Numerical Tolerance on Exact Quotient Repairs):** Defining zero-residual guards by `residual_mass <= tolerance` allows positive non-image residuals (e.g. $1/2$) to pass when a positive policy tolerance is supplied.
* **Mandatory Invariants:**
  1. Guard $g_3$ (`zero_residual_mass`) must require exact rational zero vanishing: `residual_mass == 0`.
  2. Floating-point tolerances in exact algebraic theories are strictly prohibited.
  3. When an external distance certificate is attached, the validator must execute `certificate.verify()` and enforce `certificate.distance == residual_mass`. Contradictory certificates must trigger explicit refusal.

---

## 7. Candidate Set Exhaustiveness vs. Count Coverage

* **Anti-Pattern (Count-Only Arithmetic Coverage):** Defining candidate exhaustiveness solely by `candidates_checked >= candidates_declared` allows duplicate candidate checks or checks of candidates not in the packet to falsely certify exhaustiveness.
* **Mandatory Invariants:**
  1. Guard $g_5$ (`exhaustive`) must verify exact set and cardinality equality between verified candidate identifiers and declared packet candidates:
     ```python
     set(checked_candidate_ids) == set(packet.evaluator_class_e) and len(checked_candidate_ids) == len(packet.evaluator_class_e)
     ```
  2. When only numerical counts are supplied without stable candidate identifiers, the guard must be labeled as count coverage only and must never claim exhaustive enumeration.

---

## 8. Operational Pipeline vs. Policy Attestation Trust Boundary

* **Anti-Pattern (Attestation Conflated with Execution):** Claiming that a lightweight calculator over caller-supplied boolean fields "proves that a pipeline ran" or "actually produced a terminal".
* **Mandatory Invariants:**
  1. **Attestation Disclosure:** When evaluating caller-supplied booleans, the input structure must be typed as `GuardAttestations` (or `GuardEvidence`), and the documentation must explicitly state:
     > *"The Python companion is a policy evaluator over caller-supplied attestations; it does not itself execute the four-stage pipeline or establish semantic verifier soundness."*
  2. **Operational Pipeline Requirement:** When claiming operational verification, the harness must execute the four stages in strict topological order (`route` $\to$ `descend` $\to$ `verify` $\to$ `terminalize`), stop immediately upon any refusal, produce an immutable serialized execution trace with SHA-256 digests, and derive `GuardEvidence` directly from that trace.

---

## 9. Explicit Array Equality & Hashing in Dataclasses

* **Anti-Pattern (Default Dataclass Equality on `ndarray`):**
  Python dataclasses comparing fields containing NumPy arrays (`np.ndarray`) default to elementwise comparisons. Evaluating boolean truth value raises:
  `ValueError: The truth value of an array with more than one value is ambiguous.`
* **Mandatory Invariants:**
  1. Dataclasses holding array structures (`diff_matrix`, operators, state vectors) must implement an explicit `__eq__`:
     ```python
     def __eq__(self, other: object) -> bool:
         if type(self) is not type(other):
             return False
         return (
             self.name == other.name
             and self.carrier_size == other.carrier_size
             and np.array_equal(self.diff_matrix, other.diff_matrix)
         )
     ```
  2. Implement a matching `__hash__` using `.tobytes()` to preserve hashability in sets and mapping keys:
     ```python
     def __hash__(self) -> int:
         return hash((self.name, self.carrier_size, self.diff_matrix.shape, self.diff_matrix.dtype, self.diff_matrix.tobytes()))
     ```

---

## 10. Carrier Boundary & Dimension Invariants in Discrete Spans

* **Anti-Pattern (Unchecked Carrier Indices & Sizes):**
  Comparison spans $A \xleftarrow{\text{left}} M \xrightarrow{\text{right}} B$ accepting negative sizes or out-of-bounds indices silently truncate middle elements or corrupt pullback composition.
* **Mandatory Invariants:**
  1. `mid_size` must be an `int` with `mid_size >= 0`.
  2. Lengths of `left_map` and `right_map` must strictly equal `mid_size`.
  3. Every entry in `left_map` must satisfy `0 <= idx < p1.carrier_size`.
  4. Every entry in `right_map` must satisfy `0 <= idx < p2.carrier_size`.

---

## 11. Axiom Completeness in Finite Algebraic Model Validation

* **Anti-Pattern (Vacuous Model Validation):**
  A `validate()` method returning `True` on empty, unpopulated, or non-associative tables.
* **Mandatory Invariants:**
  Validators for finite algebraic structures (groupoids, categories, monoids) must verify:
  1. Object set is non-empty and contains unique elements.
  2. Identity mapping contains exactly one identity endomorphism per object ($s(\text{id}_A) = t(\text{id}_A) = A$).
  3. Inverse mapping covers all declared morphisms, is an involution ($g^{-1-1} = g$), reverses source/target, and fixes identities ($\text{id}_A^{-1} = \text{id}_A$).
  4. Composition table covers every composable pair $(g, f)$ where $s(g) = t(f)$, with source $s(f)$ and target $t(g)$.
  5. Left and right identity laws hold: $f \circ \text{id}_A = f$ and $\text{id}_B \circ f = f$.
  6. Left and right inverse laws hold: $f^{-1} \circ f = \text{id}_A$ and $f \circ f^{-1} = \text{id}_B$.
  7. Associativity holds on all composable triples: $h \circ (g \circ f) = (h \circ g) \circ f$.

---

## 12. Filesystem Case-Insensitivity & Cross-Component Collision Fences

* **Anti-Pattern (Flat Lowercase Path Checking):**
  Checking only full lowercase file strings misses file-vs-directory conflicts and directory casing conflicts.
* **Mandatory Invariants:**
  1. Deposit walkers and manifest parsers must maintain seen files and seen directory components.
  2. Raise `ValueError` containing `"case-colliding"` if a file path matches a directory prefix under case folding, or vice versa.
  3. Raise `ValueError` containing `"case-colliding"` if any ancestor directory component differs in case from a previously seen directory component.

---

## 13. Historical Counterexample Archive Preservation Discipline

* **Anti-Pattern (Blind Refactoring Overwrite):**
  Overwriting historical defective code files used by counterexample audits or non-faithfulness demonstrations when applying discipline fixes.
* **Mandatory Invariants:**
  1. Historical source archives (e.g. `docs/source_archive/*.py.txt`) relied upon by regression audits must remain permanently intact.
  2. Discipline and bug fixes apply strictly to active, maintained production copies.
  3. Verification must assert both that maintained copies pass all gates AND that audit scripts continue to detect the historical counterexample.

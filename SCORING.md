# Code Scoring Rubric: Multi-Language Sovereign Quality & Invariant Gate (Version 2.0.0)

**AuthorityEffect:** None.

## Revision log

Version 2.0.0 keeps its levels, gates, grade definitions and record schema. The entries below are editorial corrections; records that cite version 2.0.0 stay valid.

- **2026-10-22.** (1) The repository acceptance floor is now stated in [section 1.5](#15-repository-acceptance-floor): a completed score at level L4 or L5 **and** composite grade D or better. Older score records that say `requested_target: L4E or higher` meant any L4 score, `L4E` included; that target is superseded by the floor. (2) Section 7, scenario 7, put the claim-mapping failure of a trivial Lean proof in Gate 2. Claim mapping belongs to Gate 1 (section 3.1 and RULE_LEAN_001), so the scenario now says Gate 1; its score `L2E` is unchanged. The floor is enforced by [`governance/`](governance/README.md).

This document establishes the canonical, fail-closed code evaluation rubric across all software and formal artifacts in this workspace. Version 2.0.0 updates the evaluation framework across nine language profiles and computational environments: **SQL**, **Lean 4**, **C# / .NET**, **C++**, **Python**, **Rust**, **Coq / Rocq**, **Wolfram|Alpha (Service)**, and **Wolfram Language (Code)**.

---

## 1. Overview, Core Principles & Scoring Calculus

Every source and formal artifact receives exactly one **capability level** (`L1`–`L5`) and one **engineering grade** (`E`–`A+`). The composite evaluation token is written as:

$$\mathbf{Score} = \mathbf{L}\langle\text{Level}\rangle\langle\text{Grade}\rangle \quad (\text{e.g. } \texttt{L1A+}, \texttt{L2D}, \texttt{L3B}, \texttt{L4A}, \texttt{L5E})$$

### 1.1 The Two-Axis Independence Principle
Capability level and engineering grade represent completely independent orthogonal axes:
- **Capability Level ($\mathbf{L}$):** Describes the architectural, functional, and conceptual scope the artifact actually delivers. A complex domain topic, prestigious theorem title, or verbose aspirational prose does **not** raise the capability level. Only the concrete code and verified declarations determine the level.
- **Engineering Grade ($\mathbf{G}$):** Measures the evidenced integrity, mathematical exactness, safety, verification rigor, and structural maintainability of the implementation across five sovereign gates.

A critical consequence of two-axis independence is preserved: **a small, 12-line helper utility can deserve `L1A+`, while an elaborate, 15,000-line distributed consensus engine can deserve `L5E`**. The grade serves to identify trustworthy, verified work; increasing architectural sophistication is not inherently an improvement.

### 1.2 The Fail-Closed Weakest-Link Rule
The composite grade is the **mathematical minimum** across the five component gates:

$$\text{Grade} = \min(\text{Gate}_1, \text{Gate}_2, \text{Gate}_3, \text{Gate}_4, \text{Gate}_5)$$

The grade scale is strictly ordered:

$$\mathbf{E} < \mathbf{D} < \mathbf{C} < \mathbf{B} < \mathbf{A} < \mathbf{A+}$$

There are no intermediate grades (`B+`, `A-`). A single failure on any individual gate immediately bounds the overall file grade to that failing mark.

### 1.3 The Five Sovereign Component Gates
Version 2.0.0 explicitly expands the five gates to cover semantic correctness, formal reasoning, and complete execution integrity:

| Gate | Title | Focus & Evaluation Scope |
|---|---|---|
| **G1** | **Provenance, Claim Mapping & Authority** | Whether the subject, origin, claim, evidence references, dependencies, and authority ceiling correspond precisely. Evaluates exported statements against advertised claims. |
| **G2** | **Semantic Correctness & Numeric Discipline** | Whether the implementation means and computes what the claim says, including its algebraic foundation, numeric representations, operations, and domain restrictions. |
| **G3** | **Failure Behavior, Safety & Trusted Computation** | Whether failures preserve required invariants, and whether runtime or proof dependencies remain within the declared trust boundary. |
| **G4** | **Verification Adequacy & Mutation Accounting** | Whether tests, proofs, formal checks, and adversarial challenges meaningfully support the claim at appropriate boundaries. |
| **G5** | **Structure, Cognitive Complexity & Operational Cost** | Whether the implementation remains understandable, maintainable, and supports its declared computational and resource bounds. |

### 1.4 Missing Evidence vs. Demonstrated Failure (The Unassessed Discipline)
Version 2.0.0 strictly separates established defects from missing evidence. Assigning Grade E to both an active counterexample and an unrun test conflates different findings:

| Situation | Rubric Treatment | Record Requirements |
|---|---|---|
| **Concrete counterexample or critical boundary violation established** | **Grade E** | Violated rule ID, concrete witness/counterexample, and failure trace recorded. |
| **Inspection establishes that a required mechanism or adequate evidence is absent** | **Grade D** (typically) | Specific missing mechanism or audit deficit recorded (unless establishing an E-level invariant violation). |
| **Required baseline evidence was not obtained, could not run, or is stale** | **Unassessed (`null` grade)** | Evaluator refusal recorded; cannot emit a completed score token. |
| **B-level evidence is complete, but optional A-level challenge was not run** | **Grade B** | Disclose complete B-level verification and unrun higher-tier challenge. |

An incomplete assessment cannot emit a completed score token:
$$\text{Level: L3}, \quad \text{Gates: } [\text{G1: A}, \text{G2: A}, \text{G3: B}, \text{G4: Unassessed}, \text{G5: A}] \implies \mathbf{Result: \text{assessment incomplete}}, \quad \mathbf{Ceiling: B}, \quad \mathbf{Composite: null}$$

This preserves the refusal to certify without evidence while avoiding a false claim that the code has already been demonstrated defective. Furthermore, **a known Grade E finding remains visible when other gates are unassessed**. Missing evidence cannot conceal an established failure.

### 1.5 Repository Acceptance Floor
This repository accepts a source or formal artifact only with a **completed** score at capability level **L4 or L5** and composite grade **D or better**:

$$\text{accepted} \iff \text{complete} \wedge \text{Level} \ge \mathbf{L4} \wedge \text{Grade} \ge \mathbf{D}$$

- `L4D`, `L4C` and `L5A+` are accepted. `L4E` and `L5E` (a demonstrated defect) are rejected, and so is every score at `L1`, `L2` or `L3`, for example `L3A`.
- An incomplete assessment (an unassessed gate, `composite_grade: null`, `score_token: null`) is rejected, whatever its known ceiling.
- `requested_target: L4E or higher` in older records means "any L4 score". It is superseded by this floor and earns no acceptance.
- The floor applies to every new or changed source. A source listed in `governance/baseline.json` with unchanged bytes is grandfathered; changing it removes the exemption. The floor, the source populations and the baseline are machine-readable in `governance/policy.json` and `governance/baseline.json` and are enforced by `governance-check` and by every workspace `build.rs` (see `governance/README.md`).
- A passing check confirms only that a completed score at or above the floor exists and binds the exact bytes. Whether the grades are deserved is decided by review against the cited evidence.

---

## 2. Capability Levels ($\mathbf{L1}$–$\mathbf{L5}$)

| Level | Author Profile | Delivered Code Characteristics |
|---|---|---|
| **L1** | Script Trainee / Single Utility | Minimal syntax, basic helpers, simple re-exports, static constant tables, or scripts that process literals without architectural framing. |
| **L2** | Coursework / Standard Idioms | Standard textbook structure. Straightforward definitions, obvious lemmas, basic classes, standard procedural loops, and single-case unit tests. |
| **L3** | Research Grade / Bounded Domain | Non-trivial domain algorithms, exact arithmetic structures, real inductive proofs, invariant envelopes, and structured domain modeling past standard tutorials. |
| **L4** | Senior Professional / Production Sovereign | Production craft. Intentional API grain, comprehensive edge-case handling, typed failure modes, airtight resource lifecycle management, and tight abstractions approved with negligible rework. |
| **L5** | Principal Fellow / Foundational Architecture | The design is the mathematics. Proof-carrying or certificate-carrying architectures where abstractions match underlying categorical, topological, or algebraic theorems. Zero fake generality. |

---

## 3. The Five Sovereign Component Gates

### 3.1 Gate 1: Provenance, Claim Mapping & Authority (G1)
Gate 1 verifies that the subject, origin, claim, evidence references, dependencies, and authority ceiling correspond.

#### Formal Artifact Claim Mapping
For formal artifacts, a proof of $P \to P$ is formally valid while establishing nothing about whether $P$ holds. If the advertised result is "we derived $P$," the relevant failure is the divergence between the claim and the theorem's exported statement.
Lean's documentation explicitly distinguishes proof validity from the meaning of the theorem statement [^1]. An axiom report helps audit dependencies; it does not establish that the theorem establishes the intended informal claim. The revised rubric checks exported statements, hypotheses, definitions, domains, and downstream uses.

| Grade | Provenance & Claim Mapping Invariants |
|---|---|
| **E** | Missing or forged provenance; exported theorem statement does not match advertised claim (e.g. proving $P \implies P$ or assuming $False$); dependencies undeclared. |
| **D** | Origin noted but claim lacks formal binding; authority ceiling omitted; theorem hypotheses wider than stated problem domain. |
| **C** | Authoritative origin and unique claim URN declared; `AuthorityEffect: None` explicit; exported statements and public signatures match advertised claims. |
| **B** | Complete provenance envelope; bidirectional mapping between requirements and code symbols; downstream consumer boundaries audited. |
| **A** | Sovereign verification receipt with cryptographic SHA-256 content digest; formal specification directly mirrors domain invariants; zero unreferenced hypotheses. |
| **A+** | The **A** requirements, plus cross-repository origin attestation, formal bijection between specification AST and implementation, and verified zero-drift synchronization. |

---

### 3.2 Gate 2: Semantic Correctness & Numeric Discipline (G2)
Gate 2 examines whether the implementation means and computes what the claim says, including its mathematical and numeric model.

#### Computational Profiles
The computational profile is selected before evaluation and cannot be altered post-failure:
- **Exact:** Integers, rationals, finite fields, algebraic number fields, discrete certificates, and other admitted exact discrete representations.
- **Quantized:** Fixed units, scaled decimal quantities, and bounded decimal arithmetic with explicit rounding and range rules.
- **Numerical:** Approximation, simulation, scientific estimation, and optimization with a declared, validated error model.
- **Symbolic / Formal:** Propositions, types, terms, and tactics over declared mathematical structures.
- **Non-Numeric:** Workflows without semantic arithmetic (AST routing, parsers, protocols), audited for semantic correctness.

#### Corrected Weaknesses & General Rules
1. **Integer Storage Is Not Exact Behavior:** Overflow, truncating integer division, two's-complement wrapping, and incorrect algebraic domains violate exactness even when only integer types appear.
2. **Saturating Arithmetic Changes the Result:** Clamping is appropriate only when saturation is the explicit contract. It cannot silently replace exact addition or multiplication. Furthermore, saturating division still panics on a zero divisor in Rust [^2].
3. **Decimal Types Need an Explicit Model:** PostgreSQL `NUMERIC` [^3] and C# `decimal` have defined precision, scale, rounding, and range behaviors that must be validated against the contract.
4. **Exact Output Representations Do Not Repair Approximate Inputs:** Python's `Fraction` can exactly represent a supplied binary float without recovering the intended decimal rational [^4].
5. **Negative Test Exemption:** Test fixtures deliberately supplying floating-point numbers to verify that an exact boundary rejects them do not violate Gate 2.

| Grade | Semantic Correctness & Numeric Discipline Invariants |
|---|---|
| **E** | Unadmitted float appears in an exact path; integer overflow corrupts calculation; truncating division introduces unhandled fractional loss; semantic operations contradict claim. |
| **D** | Primary path uses admitted types, but intermediate conversion leaks precision; unchecked division by zero risk; domain restrictions unenforced at entry. |
| **C** | All operations preserve declared profile invariants on primary execution path; intermediate conversions checked; input range restrictions enforced. |
| **B** | Comprehensive edge-case handling; exact types enforce domain boundaries; rounding/scale behavior fully specified; numerical error bounds verified against models. |
| **A** | Complete semantic alignment between claim and code; type system or runtime gate rejects invalid domains at public boundary; exact proofs/certificates accompany discrete steps. |
| **A+** | The **A** requirements, and the mathematical structure strictly matches the algebraic foundation (e.g. Gaussian rational $\mathbb{Q}(i)$, cyclotomic field $\mathbb{Q}(\zeta_n)$), with proven exclusion of unadmitted extensions. |

---

### 3.3 Gate 3: Failure Behavior, Safety & Trusted Computation (G3)
Gate 3 evaluates whether failures preserve required invariants and whether runtime or proof dependencies stay within the admitted trust boundary.

#### Shared Completion Invariant Across Formal Languages
An unfinished proof obligation cannot obtain completed-proof status by being renamed or added to an allowlist. This invariant covers `sorryAx` in Lean 4, `Admitted` in Coq/Rocq [^5], admitted obligations, and placeholder axioms standing in for an outstanding obligation of the assessed claim.

| Grade | Failure Behavior & Safety Invariants |
|---|---|
| **E** | Unhandled panic, abort, or segmentation fault on reachable inputs; proof depends on `sorry`, `Admitted`, or unadmitted consistency axioms; production security bypass. |
| **D** | Broad catch-all exception blocks hiding root causes; missing timeout or cancellation propagation; unvalidated assumptions on external services. |
| **C** | All expected failures handled with typed error variants; graceful termination under invalid inputs; formal proofs pass standard kernel checks without custom axioms. |
| **B** | Exhaustive error enumeration; provable panic-freedom on production code paths; async cancellation safety; strict resource disposal under error conditions. |
| **A** | Fail-closed security boundaries; complete formal invariant preservation across all failure modes; proof checked with minimal standard foundational axioms only. |
| **A+** | The **A** requirements, plus formal machine-checked proof of crash-freedom and memory safety (e.g. via SPARK/Ada, Coq extraction, or verified Rust MIR analysis). |

---

### 3.4 Gate 4: Verification Adequacy & Mutation Accounting (G4)
Gate 4 evaluates whether tests, proofs, checks, and adversarial challenges meaningfully support the claim.

#### Smallest Boundary & Composition Principle
Evidence must be gathered at the **smallest boundary that discharges the claim**, adding composition evidence wherever the claim crosses boundaries:
- **Pure Function / Class:** Meaningful unit tests, property-based invariants, and boundary checks.
- **Service or CLI:** Public contract tests, integration suites, and operational execution receipts.
- **Database Migration:** Database-backed evidence for both forward upgrade and reverse recovery.
- **Pure Theorem:** Full proof build, statement review, dependency audit, and checking under declared trust policy.
- **Extracted Program:** Additional evidence connecting the executable and its interfaces to the proved formal model.
- **Certificate Checker:** Adversarial rejection evidence for malformed/forged candidates and acceptance of valid certificates.

One suitable end-to-end receipt can support several files. The rubric does not reward copying identical tests into multiple suites. Furthermore, an expected value constructed inside a test is not inherently tautological; the essential question is whether the expectation has an independent basis.

#### Honest Mutation Testing Accounting
Mutation testing assesses test sensitivity by injecting synthetic semantic faults. Every generated mutant must be recorded across six explicit outcomes [^6]:
1. **Killed:** Test suite detected the mutation and failed as expected.
2. **Survived:** Mutant passed all tests without detection (identifying a test suite blind spot).
3. **Demonstrably Equivalent:** Semantic equivalent to original code within assessed scope.
4. **Invalid:** Syntax error, compilation failure, or structurally inadmissible candidate.
5. **Inconclusive:** Execution timed out or crashed harness without distinct test attribution.
6. **Unrun:** Generated but not executed.

The conservative detection fraction $R$ is computed over all non-equivalent, valid mutants:

$$R = \frac{\text{Killed}}{\text{Killed} + \text{Survived} + \text{Inconclusive} + \text{Unrun}}$$

Silently treating a timeout as a kill or a survivor as equivalent is strictly prohibited. Invalid and demonstrably equivalent candidates are excluded only with recorded written justification. An empty eligible campaign reports `null`, never $100\%$.

*Calibration Example:* A campaign generating 15 candidates records: 8 killed, 1 survived, 2 equivalent, 3 invalid, 1 inconclusive. The non-equivalent valid candidates are $8 + 1 + 1 + 0 = 10$. The conservative fraction is $R = 8 / 10 = 0.80$. This does not qualify for an A+ rating.

| Grade | Verification Adequacy Invariants |
|---|---|
| **E** | No tests or verification artifacts exist; formal proof fails elaboration; test assertions are tautological (`assert True`); known defect unexercised. |
| **D** | Minimal happy-path tests only; missing edge-case verification; mutation score $R < 0.60$; formal development contains unverified lemmas. |
| **C** | Systematic unit coverage of core branches and boundaries; error conditions tested; mutation score $R \ge 0.70$; formal theorems compile without warnings. |
| **B** | Comprehensive unit and integration verification; all distinct error paths covered by negative test cases; mutation score $R \ge 0.85$ on critical paths; properties tested via generators. |
| **A** | Substantive challenge against declared failure classes; decisive detection of designated critical semantic faults ($R \ge 0.95$); independent test basis; full disclosure of remaining outcomes. |
| **A+** | The **A** requirements, plus independent replay under an alternate test harness or proof checker, and a second suitable challenge addressing an identified blind spot, with no unresolved material outcomes ($R = 1.0$). |

---

### 3.5 Gate 5: Structure, Cognitive Complexity & Operational Cost (G5)
Gate 5 evaluates whether the implementation remains understandable, maintainable, and supports its declared resource requirements.

#### Metric Ceilings Table
Thresholds represent rubric policy ceilings. Each metric supplies a ceiling, and the minimum applies:

| Metric | A / A+ Eligible | B Cap | C Cap | D Cap | E Cap |
|---|---|---|---|---|---|
| **Cyclomatic Complexity (CCN)** | 0–10 | 11–15 | 16–20 | 21–50 | 51+ |
| **Cognitive Complexity** | 0–15 | 16–20 | 21–25 | 26–40 | 41+ |
| **Nesting Depth** | 0–3 | 4 | 5 | 6–8 | 9+ |

*Boundary Resolution Example:* A function with CCN = 10, Cognitive = 10, and Nesting Depth = 4 misses A because nesting exceeds 3. Its metric ceilings are [CCN: A, Cognitive: A, Nesting: B]. The minimum applies, yielding a Gate 5 ceiling of **B**.

These thresholds are rubric policy defaults, not claimed general scientific laws or demonstrations of semantic error. The best metric band permits A+. Proof heartbeats, tactic length, query-plan cost, binary size, and cognitive complexity remain distinct measurements.

#### Domain-Specific Structural Assessment
- **SQL Queries:** Evaluated by query plan depth, join cardinality, absence of unintentional Cartesian products, and index utilization, not imperative CCN.
- **Formal Proofs:** Evaluated by proof heartbeat count, tactic script length, dependency graph acyclicity, and modular lemma factoring.
- **Unsupported Parsers:** If a structural complexity tool cannot parse a formal language, it must record structural line count and linear flow rather than claiming a false zero.

| Grade | Structure & Operational Cost Invariants |
|---|---|
| **E** | Cyclomatic complexity $> 50$, cognitive complexity $> 40$, nesting depth $\ge 9$, unmanaged unbounded recursion, or exponential runtime on standard input. |
| **D** | High complexity (CCN 21–50, cognitive 26–40, nesting 6–8); non-linear control flow that impedes independent review; duplicate code blocks. |
| **C** | Moderate complexity (CCN 16–20, cognitive 21–25, nesting 5); clean modular boundaries; predictable linear or polynomial resource consumption. |
| **B** | Low complexity (CCN 11–15, cognitive 16–20, nesting 4); well-factored helper functions; documented algorithmic complexity bounds ($O(n)$, $O(n \log n)$). |
| **A** | Minimal complexity (CCN $\le 10$, cognitive $\le 15$, nesting $\le 3$); clear single-responsibility functions; zero redundant allocations in inner loops. |
| **A+** | The **A** requirements, plus formal algorithmic resource bounds or zero-allocation performance contracts checked by benchmarks or static analyzers. |

---

## 4. Language-Specific Engineering Invariants & Profiles

### 4.1 SQL & Relational Schemas
- **RULE_SQL_001 (Dialect & Engine Context):** Every SQL artifact must declare its specific dialect and target engine (e.g. PostgreSQL 16 [^18], SQLite 3.45 [^17], DuckDB 1.0 [^19]).
- **RULE_SQL_002 (NULL & Three-Valued Logic):** `CHECK (val > 0)` is satisfied when `val` is positive OR `NULL` in PostgreSQL and SQL-92 standards [^7][^20]. Constraints intended to mandate positive values must explicitly declare `NOT NULL`.
- **RULE_SQL_003 (COALESCE Qualification):** Defensiveness can alter answers. Missing value (`NULL`), zero (`0`), and empty string (`""`) represent distinct domain states. `COALESCE` is permitted only when the domain contract explicitly equates them.
- **RULE_SQL_004 (Window Ordering vs. Result Ordering):** In SQL window functions, whole-partition aggregation may require no ordering. Adding an `ORDER BY` inside `OVER ()` changes the default frame to `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`, altering the calculated result [^8]. Window ordering and outer result ordering are completely separate.
- **RULE_SQL_005 (Migration Tested Recovery):** Forward migrations (`up.sql`) promising reversibility must provide a tested down-migration (`down.sql`). Dropping an altered table does not restore data written to it after migration.
- **RULE_SQL_006 (Parameters & Dynamic Identifiers):** Values must use parameterized bindings. Dynamic SQL identifiers (table/column names) must be validated against a strict allowlist.
- **RULE_SQL_007 (Concurrency & Plans):** Multi-statement transaction ownership must be declared; concurrent writers must be guarded by isolation levels or advisory locks; queries must be verified against representative `EXPLAIN ANALYZE` plans.

### 4.2 Lean 4 Formal Mechanization
- **RULE_LEAN_001 (Exported Theorem Meaning):** The exported theorem statement must directly formalize the scientific claim [^1]. Trivial implications ($P \to P$) or derivations from contradictory hypotheses ($h : False$) receive Grade E for claim mapping.
- **RULE_LEAN_002 (Foundational vs. Unfinished Assumptions):** Conditional theorems may be complete relative to explicitly declared foundational axioms or mathematical models [^21]. Those assumptions remain visible in the signature and receive no credit as derived results.
- **RULE_LEAN_003 (Transitive Unfinished Proof Detection):** Theorems depending transitively on `sorry` or `sorryAx` cannot receive completed-proof status. Adding an unfinished obligation to an allowlist does not make it complete.
- **RULE_LEAN_004 (Inferred Termination & Totality):** Explicit `termination_by` is not required across all definitions when Lean's structural recursion synthesizer verifies termination [^9]. However, `partial def` signifies unverified termination and is strictly excluded from exact proof claims.
- **RULE_LEAN_005 (Native-Evaluation Trust):** Trusting `#eval` or native compilation steps requires explicit documentation of compiler version sensitivity and foreign function interfaces [^22].
- **RULE_LEAN_006 (Logical vs. Executable Claims):** Noncomputable mathematical assertions must be explicitly separated from executable algorithms using proofs of algorithm equivalence.

### 4.3 C# / .NET
- **RULE_CS_001 (Checked Arithmetic Execution):** A `checked { ... }` block applies only to expressions lexically enclosed within the block [^10]. Calling a method from within a checked block does **not** make arithmetic inside the callee checked.
- **RULE_CS_002 (Nullable Analysis Is Static Evidence):** Nullable reference types (`#nullable enable`) provide static compiler diagnostics, not runtime validation [^11]. Inputs from JSON deserialization, reflection, legacy assemblies, or P/Invoke must be validated at runtime. The null-forgiving operator `!` suppresses warnings without runtime checks.
- **RULE_CS_003 (Disposal & Resource Lifecycle):** Types holding unmanaged handles or disposable objects must implement `IDisposable` / `IAsyncDisposable` with correct `GC.SuppressFinalize` patterns [^23].
- **RULE_CS_004 (Async Completion & Cancellation):** Asynchronous methods must accept `CancellationToken` and propagate it to all downstream cancellable operations [^24].
- **RULE_CS_005 (Shared-State Atomicity):** Concurrent mutable access must use thread-safe collections, memory barriers, or `Interlocked` operations [^25].
- **RULE_CS_006 (Unsafe Boundaries):** `unsafe` code blocks and `Span<T>` manipulation must verify memory pinning and buffer boundaries.

### 4.4 C++
- **RULE_CPP_001 (Defined Arithmetic):** Signed integer overflow is undefined behavior (UB) [^26]. Bit-shifts exceeding operand width are UB. Arithmetic must use checked or unsigned types where overflow is possible.
- **RULE_CPP_002 (Ownership & Lifetime):** Raw pointers cannot denote ownership. Modern C++ must use `std::unique_ptr`, `std::shared_ptr`, or RAII containers. Pass non-owning references as `std::span` or `std::string_view` with verified lifetime bounds.
- **RULE_CPP_003 (Exception Contracts & noexcept):** Functions declared `noexcept` must never allow exceptions to escape [^27]. Destructors and move constructors must be `noexcept` to ensure container exception safety.
- **RULE_CPP_004 (Sanitizer Coverage & Scope):** A clean sanitizer execution has a defined, limited scope. Clean runs under AddressSanitizer (ASan) [^28] and UndefinedBehaviorSanitizer (UBSan) [^12] must record exact flags. The default UBSan group does not include every unsigned-overflow or conversion check [^29].
- **RULE_CPP_005 (FFI Layout & Concurrency):** Foreign interfaces must use standard C layout (`extern "C"`, `#pragma pack`). Concurrency must use `std::atomic` with explicit memory orderings.

### 4.5 Python
- **RULE_PY_001 (Runtime Input Admission):** Public interfaces must validate external inputs using robust runtime schemas (Pydantic v2 or validated dataclasses [^31]).
- **RULE_PY_002 (Boolean Subclass Guard):** In Python, `isinstance(True, int)` evaluates to `True`, and `True == 1` evaluates to `True` [^30]. Exact arithmetic checks must explicitly enforce `type(val) is not bool` before admitting integers.
- **RULE_PY_003 (Optimization-Safe Validation):** Production code must never rely on `assert` for required validation, authorization, state transitions, or safety, because `assert` statements are completely removed when running under `python -O` [^13]. Test assertions and internal debug invariants are permitted where their removal preserves the public contract.
- **RULE_PY_004 (Numeric Data Flow):** Constructing `Fraction` from binary floats preserves IEEE-754 representation drift [^4]. Fractions and Decimals must be initialized from integer pairs or strings: `Fraction(1, 10)` or `Decimal("0.1")`.
- **RULE_PY_005 (Nested Mutability Invariant):** Mutability must match object semantics. Replace compulsory frozen entities with invariant-based rules: audit nested mutable fields (lists, dicts) inside immutable containers.
- **RULE_PY_006 (Pinned Typing):** Type checking must run under strict, pinned static analyzer configurations (`mypy --strict` [^32]).

### 4.6 Rust
- **RULE_RS_001 (Checked vs. Saturating Arithmetic):** Release profiles wrap two's-complement integer overflow by default unless `overflow-checks = true` is declared in `Cargo.toml`. Critical arithmetic must use explicit `checked_*`, `overflowing_*`, or `saturating_*` operations. Saturating division panics on zero divisor [^2].
- **RULE_RS_002 (Justified Indexing):** Direct slice indexing (`slice[i]`) panics on out-of-bounds [^34]. Production library paths must use `slice.get(i)` returning `Option<&T>` or document a rigorous mathematical bounds proof.
- **RULE_RS_003 (Construction & Deserialization Paths):** Domain value objects must enforce invariants across all construction paths, private constructors, and `serde::Deserialize` implementations.
- **RULE_RS_004 (Unsafe Encapsulation):** Every `unsafe` block must be accompanied by a `// SAFETY:` comment establishing the precise preconditions and safety invariants upheld [^33].
- **RULE_RS_005 (Panic Boundary in FFI):** Panicking across `extern "C"` boundaries is undefined behavior. Foreign exports must catch unwinding panics using `std::panic::catch_unwind` [^35].

### 4.7 Coq / Rocq
- **RULE_COQ_001 (Final Theorem Types & Hypotheses):** Theorem conclusions must match scientific claims without lingering section hypotheses or unverified premise vacuities [^37].
- **RULE_COQ_002 (Print Assumptions Audit):** Every verified development must execute `Print Assumptions <theorem>.` to detect unadmitted transitive axioms [^39].
- **RULE_COQ_003 (The Admitted Trap):** Using `Admitted` registers the goal as an admitted axiom [^5]. Such developments cannot receive verified completion.
- **RULE_COQ_004 (Extraction Mappings):** Code extracted to OCaml or Haskell must audit custom extraction rules, inductive types, and foreign arithmetic bindings for operational equivalence [^38].

### 4.8 Wolfram|Alpha (Service Profile) & Wolfram Language (Code Profile)
- **RULE_WA_001 (Wolfram|Alpha Service Queries):** Captured query interpretation, input assumptions, and pods must be recorded. An API response with `success="true"` does not verify completeness [^15].
- **RULE_WA_002 (Witness vs. Completeness & Optimality):** Checking that $x = 1$ satisfies $x^2 = 1$ verifies only that witness. It does not establish solution completeness, uniqueness, or global optimality [^41].
- **RULE_WL_001 (Clean Kernel State):** Executable Wolfram Language code must run in a clean kernel session without lingering global variable definitions.
- **RULE_WL_002 (Precision & Exact Representations):** Applying `SetPrecision` or `Rationalize` to approximate floating-point values does not establish that the original intended exact algebraic number has been recovered [^16].
- **RULE_WL_003 (Assumptions & Preconditions):** Assumptions declared in `Refine`, `Simplify`, or `Integrate` must be verified against caller preconditions [^40].

---

## 5. Cross-Language Composition Invariants

When software pipelines compose multiple language components (e.g. SQL data $\to$ Python/C# API $\to$ Rust math engine $\to$ Lean 4 certifier):
1. **Interface Type Conservation:** Data types must conserve precision, scale, sign, and nullability across language boundaries (e.g. SQL `NUMERIC(18,4)` $\to$ C# `decimal` $\to$ Rust `BigRational` $\to$ Lean `Rat`) [^44].
2. **Failure Translation:** Failures in lower subsystems must translate into native typed errors in caller languages without crashing or hiding causes.
3. **Formal Model Correspondence:** When an extracted program or compiled Rust binary claims to implement a Lean 4 or Coq specification, an explicit trace mapping between formal definitions and executable code must be provided.
4. **Symbolic Domain Admission:** Results from external symbolic engines must preserve preconditions and domain bounds before admission to formal verifiers.
5. **No Inferred System Score:** A system-level score cannot be inferred by averaging component grades. The weakest-link rule applies across the entire composition chain: $\text{Score}_{\text{sys}} = \min(\text{Score}_{c1}, \dots, \text{Score}_{cn})$.

---

## 6. Machine-Readable Evaluation Record & Draft 2020-12 JSON Schema

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "urn:pfp:schemas:code-scoring-record:v2",
  "title": "CodeScoringRecordV2",
  "type": "object",
  "required": [
    "schema_version",
    "artifact",
    "profile",
    "level",
    "gates",
    "composite_grade",
    "score_token",
    "evaluation_timestamp"
  ],
  "properties": {
    "schema_version": { "type": "string", "const": "2.0.0" },
    "artifact": {
      "type": "object",
      "required": ["path", "language", "sha256"],
      "properties": {
        "path": { "type": "string" },
        "language": {
          "type": "string",
          "enum": [
            "SQL", "Lean 4", "C#", "C++", "Python", "Rust",
            "Coq/Rocq", "WolframAlpha", "WolframLanguage", "Other"
          ]
        },
        "sha256": { "type": "string", "pattern": "^[a-f0-9]{64}$" }
      }
    },
    "profile": {
      "type": "string",
      "enum": ["Exact", "Quantized", "Numerical", "Symbolic/Formal", "Non-Numeric"]
    },
    "level": {
      "type": "string",
      "enum": ["L1", "L2", "L3", "L4", "L5"]
    },
    "gates": {
      "type": "object",
      "required": ["G1", "G2", "G3", "G4", "G5"],
      "properties": {
        "G1": { "type": ["string", "null"], "enum": ["E", "D", "C", "B", "A", "A+", null] },
        "G2": { "type": ["string", "null"], "enum": ["E", "D", "C", "B", "A", "A+", null] },
        "G3": { "type": ["string", "null"], "enum": ["E", "D", "C", "B", "A", "A+", null] },
        "G4": { "type": ["string", "null"], "enum": ["E", "D", "C", "B", "A", "A+", null] },
        "G5": { "type": ["string", "null"], "enum": ["E", "D", "C", "B", "A", "A+", null] }
      }
    },
    "composite_grade": {
      "type": ["string", "null"],
      "enum": ["E", "D", "C", "B", "A", "A+", null]
    },
    "score_token": {
      "type": ["string", "null"],
      "pattern": "^L[1-5](E|D|C|B|A\\+?)$"
    },
    "is_complete": { "type": "boolean" },
    "grade_ceiling": {
      "type": "string",
      "enum": ["E", "D", "C", "B", "A", "A+"]
    },
    "evaluation_timestamp": { "type": "string", "format": "date-time" },
    "mutation_accounting": {
      "type": "object",
      "properties": {
        "killed": { "type": "integer", "minimum": 0 },
        "survived": { "type": "integer", "minimum": 0 },
        "demonstrably_equivalent": { "type": "integer", "minimum": 0 },
        "invalid": { "type": "integer", "minimum": 0 },
        "inconclusive": { "type": "integer", "minimum": 0 },
        "unrun": { "type": "integer", "minimum": 0 },
        "conservative_ratio": { "type": ["number", "null"], "minimum": 0.0, "maximum": 1.0 }
      }
    }
  }
}
```

#### Semantic Validation Requirements Beyond JSON Schema
1. **Tool Execution Integrity:** Rejects a claimed completed tool execution that lacks its command line, tool version, working directory, bound inputs/report, or exit status.
2. **Evidence Reference Resolution:** Every evidence receipt cited in an evaluation record must resolve to an extant file hash.
3. **Mutation Accounting Balance:** Sum of mutation outcomes must match distinct report entries.
4. **Ordinal Grade Minimum:** When all gates are assessed, `composite_grade` must equal $\min(G_1, \dots, G_5)$.

---

## 7. Calibration Scenarios & Decision Ledger (18 Scenarios)

The following eighteen scenarios establish normative precedents for boundary evaluations:

1. **L1 Helper with Exemplary Rigor (`L1A+`):**
   A 12-line Rust utility function checking whether a `u64` is a power of two using `x != 0 && (x & (x - 1)) == 0`. Full provenance, exact integer arithmetic, `no_std`, property-based tests over 100,000 values, mutation score $R = 1.0$, cyclomatic complexity 1. Grade: **`L1A+`**.

2. **Complex Distributed Architecture with Unhandled Panics (`L5E`):**
   An advanced distributed consensus engine spanning 15,000 lines implementing multi-party state machine replication. Gate 1, 2, 4, and 5 pass at A, but internal message deserialization contains `.unwrap()`. Under Gate 3 fail-closed rule, the unhandled panic forces Gate 3 to **`E`**. Composite: **`L5E`**.

3. **Incomplete Assessment with High Baseline (`null`):**
   A high-grade cryptographic hash module scores `[G1: A, G2: A, G3: A, G4: Unassessed, G5: A]` because the mutation suite timed out on CI. The evaluation cannot certify without evidence: Grade: `null`, Score: `null`, Known Ceiling: `A`.

4. **Demonstrated Defect Outweighs Incomplete Evidence (`L3E`):**
   A matrix multiplication routine has an established buffer-overflow bug detected by AddressSanitizer (Gate 3 = `E`). Gate 4 was unassessed. The known `E` finding is retained: Score: **`L3E`**.

5. **Float Leakage in Exact Rational Engine (`L4E`):**
   A rational fraction library computes determinants using exact rationals on all paths except intermediate eigenvalue preconditioning where an IEEE-754 `f64` cast is used. Violates Exact Profile Gate 2: **`L4E`**.

6. **Python Production Assertion Stripping (`L3E`):**
   A user authentication module enforces signature validation via `assert verify_signature(data)`. Under `python -O`, the check disappears. Gate 3 is bounded to **`E`**: **`L3E`**.

7. **Lean 4 Trivial Proof of Complex Theorem (`L2E`):**
   A paper claims formal proof of the Riemann Hypothesis, but the Lean file exports `theorem riemann_hypothesis (h : False) : RH := False.elim h`. Gate 1 fails claim mapping (section 3.1, RULE_LEAN_001): **`L2E`**.

8. **Lean 4 Theorem with Hidden `sorryAx` (`L4E`):**
   A formal module discharges 10 lemmas cleanly, but lemma 7 invokes a helper from an auxiliary namespace containing `sorry`. The kernel dependency audit detects transitive `sorryAx`. Gate 3 bounded to **`E`**: **`L4E`**.

9. **SQL Schema with Ambiguous NULL Check (`L2D`):**
   A PostgreSQL table declares `CHECK (account_balance > 0)` without declaring `NOT NULL`. Inserting `NULL` is permitted by PostgreSQL three-valued logic. Gate 2 capped at **`D`**: **`L2D`**.

10. **SQL Migration Lacking Down Script (`L3D`):**
    A production schema migration alters column types and promises seamless rollback, but leaves `down.sql` blank. Gate 1/4 bounded to **`D`**: **`L3D`**.

11. **C# Method Call Inside `checked` Block (`L3D`):**
    A C# financial calculation calls `ComputeInterest()` from inside a `checked { ... }` block, but `ComputeInterest()` itself is compiled in an unchecked assembly and overflows. Gate 2 capped at **`D`**: **`L3D`**.

12. **C# Suppressed Null Diagnostic with `!` Operator (`L3D`):**
    A C# service processes external API payloads using `payload.User!.Email` without runtime null checking. The null-forgiving operator suppresses the warning without performing validation. Gate 3 capped at **`D`**: **`L3D`**.

13. **C++ Signed Overflow in Loop Counter (`L3E`):**
    A numerical loop uses `int i` and increments until `i * step` wraps, causing signed integer overflow UB. Detected by UBSan. Gate 3: **`L3E`**.

14. **Coq Development Relying on `Admitted` (`L3E`):**
    A Coq module discharges 15 goals but closes the central inductive step with `Admitted`. `Print Assumptions` reveals unproved axiom. Gate 3: **`L3E`**.

15. **Wolfram|Alpha Witness Mistaken for Uniqueness (`L2D`):**
    A solver queries Wolfram|Alpha to find roots of a quintic polynomial, receives one root, and asserts solution uniqueness without checking the degree. Gate 2 capped at **`D`**: **`L2D`**.

16. **Mutation Suite with Timeout Concealment (`L4D`):**
    A test suite generates 20 mutants; 10 are killed, 5 survive, and 5 time out. The report claims $10/15 = 66\%$ by omitting timeouts. The conservative formula computes $R = 10 / (10 + 5 + 5) = 10/20 = 50\%$. Gate 4 capped at **`D`**: **`L4D`**.

17. **High Complexity with Shallow Nesting (`L3B`):**
    A dispatch routine has cyclomatic complexity 10, cognitive complexity 10, but nesting depth 4. The metric ceiling table places CCN 10 at A, cognitive 10 at A, and nesting 4 at B cap. The minimum applies: Gate 5 receives **`B`**: **`L3B`**.

18. **Cross-Language FFI Sign Mismatch (`L4E`):**
    A C# service passes an `int` (signed 32-bit) to a Rust FFI function expecting `u32`. Negative account IDs wrap to large positive values without error. Cross-language composition violation. Composite: **`L4E`**.

---

### Calibration Vectors Ledger
The following eight calibration rows provide full explicit five-gate evaluations across diverse profiles:

| # | Artifact Description | Level | Profile | G1 | G2 | G3 | G4 | G5 | Grade | Score |
|---|---|---|---|---|---|---|---|---|---|---|
| **1** | Rust `no_std` bitwise power-of-two helper | `L1` | Exact | `A+` | `A+` | `A+` | `A+` | `A+` | **`A+`** | **`L1A+`** |
| **2** | Distributed consensus engine with unwrap panic | `L5` | Non-Numeric | `A` | `A` | `E` | `A` | `A` | **`E`** | **`L5E`** |
| **3** | Cryptographic hash module (mutation timeout) | `L3` | Exact | `A` | `A` | `A` | `null` | `A` | **`null`** | **`null`** |
| **4** | Matrix multiply with ASan buffer-overflow | `L3` | Numerical | `B` | `B` | `E` | `null` | `B` | **`E`** | **`L3E`** |
| **5** | Rational matrix solver with float cast | `L4` | Exact | `A` | `E` | `A` | `A` | `A` | **`E`** | **`L4E`** |
| **6** | Python auth module with production assert | `L3` | Non-Numeric | `A` | `B` | `E` | `B` | `A` | **`E`** | **`L3E`** |
| **7** | High complexity dispatch routine (Nesting = 4) | `L3` | Non-Numeric | `A` | `A` | `A` | `A` | `B` | **`B`** | **`L3B`** |
| **8** | C# to Rust FFI with signedness wrapping | `L4` | Exact | `A` | `E` | `E` | `B` | `A` | **`E`** | **`L4E`** |

---

## 8. Version Transition, Empirical Calibration & Governance Notes

### Version Transition & Retroactive Scoring
Scores computed under Version 1.0.0 retain their historic validity under their declared rubric version. However, any artifact asserting compliance with Version 2.0.0 must undergo re-evaluation under the expanded Gate 2 (Semantic Correctness) and Gate 4 (Honest Mutation Accounting) requirements.

### Empirical Calibration Disclosure
The calibration scenarios in Section 7 represent explicitly hypothetical specification examples designed to test rubric boundaries; they are not claimed empirical measurements of repository source files. Future empirical calibration will evaluate inter-reviewer agreement, the frequency of justified refusals to certify, and the statistical correlation between high engineering grades and low escaped defect rates.

---

## 9. Documentation Footnotes & Primary References

[^1]: Lean FRO, "Validating Proofs," *Lean 4 Reference Manual*, https://lean-lang.org/doc/reference/latest/ValidatingProofs/
[^2]: Rust Project Developers, "Primitive Type i32: saturating_div," *The Rust Standard Library Documentation*, https://doc.rust-lang.org/std/primitive.i32.html
[^3]: PostgreSQL Global Development Group, "Numeric Types," *PostgreSQL 16 Documentation*, https://www.postgresql.org/docs/current/datatype-numeric.html
[^4]: Python Software Foundation, "fractions — Rational numbers," *Python 3.12 Documentation*, https://docs.python.org/3/library/fractions.html
[^5]: Inria / The Rocq Team, "Writing proofs: Admitted," *The Rocq Prover 9.2 Reference Manual*, https://rocq-prover.org/doc/V9.2.0/refman/proofs/writing-proofs/proof-mode.html
[^6]: Sourcefrost, "Interpreting Mutation Results," *cargo-mutants Documentation*, https://mutants.rs/using-results.html
[^7]: PostgreSQL Global Development Group, "Constraints: Check Constraints," *PostgreSQL 16 Documentation*, https://www.postgresql.org/docs/current/ddl-constraints.html
[^8]: PostgreSQL Global Development Group, "Window Functions Tutorial," *PostgreSQL 16 Documentation*, https://www.postgresql.org/docs/current/tutorial-window.html
[^9]: Lean FRO, "Recursive Definitions & Termination," *Lean 4 Reference Manual*, https://lean-lang.org/doc/reference/latest/Definitions/Recursive-Definitions/
[^10]: Microsoft Corporation, "checked and unchecked statements," *C# Language Reference*, https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/checked-and-unchecked
[^11]: Microsoft Corporation, "Nullable reference types and runtime null checking," *C# Fundamentals*, https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/null-safety/nullable-reference-types
[^12]: Clang / LLVM Project, "UndefinedBehaviorSanitizer (UBSan)," *Clang Compiler User's Manual*, https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html
[^13]: Python Software Foundation, "The assert statement," *Python 3.12 Reference Manual*, https://docs.python.org/3/reference/simple_stmts.html
[^14]: Inria / The Rocq Team, "The Rocq Prover Reference Manual (v9.2.0)", https://rocq-prover.org/doc/V9.2.0/refman/
[^15]: Wolfram Research, "Wolfram|Alpha Full Results API Documentation," https://products.wolframalpha.com/api/documentation
[^16]: Wolfram Research, "SetPrecision: Wolfram Language Reference," https://reference.wolfram.com/language/ref/SetPrecision.html
[^17]: SQLite Consortium, "Datatypes In SQLite Version 3," https://www.sqlite.org/datatype3.html
[^18]: PostgreSQL Global Development Group, "Concurrency Control," *PostgreSQL 16 Documentation*, https://www.postgresql.org/docs/current/mvcc.html
[^19]: DuckDB Foundation, "Window Functions in DuckDB," *DuckDB Documentation*, https://duckdb.org/docs/sql/window_functions
[^20]: International Organization for Standardization, *ISO/IEC 9075:1992 Database Language SQL*, ISO, Geneva, Switzerland.
[^21]: Lean FRO, "Axiom Reporting & Dependencies," *Lean 4 Reference Manual*, https://lean-lang.org/doc/reference/latest/ValidatingProofs/
[^22]: Lean FRO, "The Lean 4 Compiler Architecture," https://lean-lang.org/doc/reference/latest/
[^23]: Microsoft Corporation, "Standard Dispose Pattern," *.NET Architecture Guides*, https://learn.microsoft.com/en-us/dotnet/standard/garbage-collection/implementing-dispose
[^24]: Microsoft Corporation, "Cancellation in Managed Threads," *.NET Documentation*, https://learn.microsoft.com/en-us/dotnet/standard/threading/cancellation-in-managed-threads
[^25]: Microsoft Corporation, "Interlocked Class," *System.Threading Documentation*, https://learn.microsoft.com/en-us/dotnet/api/system.threading.interlocked
[^26]: ISO/IEC, *ISO/IEC 14882:2020 Programming Languages — C++*, International Organization for Standardization.
[^27]: ISO/IEC, *noexcept specifier in ISO/IEC 14882:2020*, Standard C++ Foundation.
[^28]: Google Inc. / LLVM Team, "AddressSanitizer (ASan)," https://github.com/google/sanitizers/wiki/AddressSanitizer
[^29]: LLVM Team, "UndefinedBehaviorSanitizer: unsigned-integer-overflow," https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html
[^30]: Python Software Foundation, "Standard type hierarchy: Booleans," *The Python Standard Library*, https://docs.python.org/3/reference/datamodel.html
[^31]: Python Software Foundation, "PEP 557 – Data Classes," https://peps.python.org/pep-0557/
[^32]: Python Software Foundation / Dropbox, "Mypy: Optional Static Typing for Python," https://mypy.readthedocs.io/
[^33]: The Rust Project, "Behavior considered undefined," *The Rust Reference*, https://doc.rust-lang.org/reference/behavior-considered-undefined.html
[^34]: The Rust Project, "Slice indexing and range syntax," *The Rust Reference*, https://doc.rust-lang.org/std/primitive.slice.html
[^35]: The Rust Project, "std::panic::catch_unwind," *The Rust Standard Library*, https://doc.rust-lang.org/std/panic/fn.catch_unwind.html
[^36]: The Rust Project, "Subtyping and Variance," *The Rustonomicon*, https://doc.rust-lang.org/nomicon/subtyping.html
[^37]: Inria, "Sections and Contexts," *The Coq Proof Assistant Reference Manual*, https://coq.inria.fr/doc/V8.18.0/refman/language/core/sections.html
[^38]: Inria, "Extraction of programs in OCaml and Haskell," *The Coq Reference Manual*, https://coq.inria.fr/doc/V8.18.0/refman/addendum/extraction.html
[^39]: Inria, "Print Assumptions Command," *The Coq Reference Manual*, https://coq.inria.fr/doc/V8.18.0/refman/proof-engine/vernacular-commands.html
[^40]: Wolfram Research, "Assumptions: Wolfram Language Reference," https://reference.wolfram.com/language/ref/Assumptions.html
[^41]: Wolfram Research, "Solve: Exact and Numerical Solutions," https://reference.wolfram.com/language/ref/Solve.html
[^42]: Internet Engineering Task Force (IETF), "JSON Schema: A Media Type for Describing JSON Documents (Draft 2020-12)", https://json-schema.org/draft/2020-12/json-schema-core.html
[^43]: Internet Engineering Task Force (IETF), "RFC 8785: JSON Canonicalization Scheme (JCS)", https://www.rfc-editor.org/rfc/rfc8785
[^44]: IEEE, *IEEE Standard for Floating-Point Arithmetic (IEEE 754-2019)*, IEEE Computer Society.
[^45]: Thomas J. McCabe, "A Complexity Measure," *IEEE Transactions on Software Engineering*, Vol. SE-2, No. 4, 1976.

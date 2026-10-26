# Detailed definition: Publication Review Remediation & Package Re-certification (2)

**AuthorityEffect:** None.

Parent: [Publication Review Remediation & Package Re-certification](../../../../../rules/papers/rl_publication_review_remediation_and_recertification_discipline.md). Load for the matching predicate, not every task.

## Publication Review Remediation & Multi-Layer Synchronization Gate

> **Atomic Cross-Layer Remediation Discipline:**
>
> 1. **5-Layer Atomic Remediation Synchronization:**
>    When resolving publication review blockers (mathematical definitions, fiber characterizations, numerical domain issues, or metric claims), changes must be synchronized atomically across all five estate layers before closing review issues:
>    a. **Manuscript Source:** Align definitions, fiber characterizations (e.g., quotient by $\pm 1$), and diagram scaling factors (e.g., $1/2$ trace factor). Strictly distinguish sufficient from necessary conditions in multi-factor kernel expansions: separate component additivity must not be claimed as necessary at fixed weights when signed errors can cancel ($\lambda \Delta_C + \mu \Delta_R = 0$).
>    b. **Claim Status Ledger:** Upgrade claims only when backed by sovereign code and tests; unverified claims must remain marked as candidate or downgraded.
>    c. **Implementation Code & Tests:** Implement numerical stability fences (overflow scaling, unit trace checks), separate matrix-direct from vector-plus-mass reconstruction contracts, and write discrete cell-complex integration tests.
>    d. **Package Metadata & Licensing:** Synchronize dates and version numbers uniformly across `README.md`, `pyproject.toml`, `zenodo_metadata.json`, `docs/descriptions.md`, monograph headers, and claim ledgers. `LICENSE` files must contain the full official legal text (e.g. Creative Commons Attribution 4.0 International Public License), never a one-line summary stub.
>    e. **Release Artifacts & Checksum Manifests:** Rebuild release archives deterministically and execute bidirectional sweep verification (`verify_deposit.py`) with zero manifest drift. The package root must never retain unpinned, divergent upload aliases (`0_*.pdf`, `1_*.zip`) outside the manifest-bound verification route. Any numbered upload alias used for publisher display sorting must be generated as a byte-identical copy or removed from the root. Documentation (`README.md`) and packaging script defaults (`build_deposit_zip.py`) must unconditionally agree on artifact destination paths.
>       Verifiers (`verify_deposit.py`) must extract the built public archive to a temporary directory, account for internal package directory prefixes (`f"{ROOT.name}/{rel_path}"`), and verify that every unpacked file hash matches `MANIFEST.sha256` and that no unexpected files were packed. Sibling dated archives and upload aliases (`1_*.zip`) must be verified to have exact byte equality (`sha256_of(upload_zip) == sha256_of(built_zip)`), and obsolete dated archives from earlier versions must be actively rejected.
>
> 2. **Mechanization-Manuscript Scope Parity Invariant:**
>    When formal Lean 4 theorems establish coordinate-level or local bounds (e.g., $w_k |c'_k| \le \Phi_1^{\mathcal{O}}(c) + \varepsilon_{\mathcal{O}}$), manuscripts, claim ledgers, and docstrings must NOT promote them into unproven global transfer-invariance or non-tearing claims. If aggregate norm reduction or preservation admits defect transfer across subcomplexes, the manuscript must explicitly state this boundary condition and document that preventing transfer between specific subcomplexes requires dedicated partition guardrails.
>    Furthermore, when prose theorems claim properties over an arbitrary finite carrier $X$ with an equivalence relation, formal Lean declarations must quantify over arbitrary types and setoid equivalence relations (`{X : Type u} (s : Setoid X)`). Declarations that quantify over specialized concrete carrier structures (e.g., class/item identifier tuples) must not be labeled `LEAN_FULL` in claim ledgers or claim IRs unless the formal transport theorem is included; otherwise, they must be scoped as specialized models.
>
> 3. **Exact Structural Hypotheses vs. Numerical Evaluation Separation:**
>    Mathematical checkers and verifiers in paper reference implementations must strictly separate exact algebraic hypothesis validation from floating-point numerical identity evaluation:
>    a. **Exact Rational Hypothesis Checks:** Algebraic premises (such as path cost additivity $C(\gamma_1) + C(\gamma_2) = C(\gamma_2 \circ \gamma_1)$ or proposal mass factorization) must be checked using exact arithmetic (`fractions.Fraction`, `int`, or exact rational representations), never floating-point approximation with tolerances (`math.isclose`) or lossy float casting. Concrete test fixtures (including decimal inputs) must be parsed into exact rationals so that genuine discrepancies ($2^{54}+1 \ne 2^{54}$, $2^{-41} \ne 0$) are never accepted as satisfied premises.
>    b. **Fail-Closed Numerical Refusal:** When derived products, exponentials, or sums exceed numerical representation capacity (`inf`, `inf`, `NaN` residual), checkers must NOT report a successful certificate (`identity_holds = False`) and must raise a dedicated typed refusal (`NumericalRefusalError` subclassing `InvariantViolationError`). Checkers must cleanly distinguish: (i) structural hypotheses established vs. premise violation; (ii) numerical representation overflow/underflow requiring refusal; and (iii) evaluated numerical identity within representation bounds.
>
> 4. **Diagnostic Model & Evaluator Parameter Strictness:**
>    All diagnostic models, observers, and controllers in paper reference implementations must enforce fail-closed parameter validation at construction:
>    a. Weights must be strictly positive and finite ($w > 0$).
>    b. Resolution tolerances must be finite and non-negative ($\varepsilon \ge 0$).
>    c. Bounds and ceilings ($R_{\max}, M_{\max}$) must be strictly positive and non-NaN; curvature stability fences ($\Gamma_{\max}, \delta_{\Gamma}$) must be non-negative and non-NaN.
>    d. Coboundary operator matrices ($d_0, d_1$) and projection indices must strictly match the declared carrier dimensions.
>    e. **Contingency Table Joint-Cell Realizability:** Report validators and metric report objects representing joint evaluator verdicts (e.g., local product vs. global verdict) must enforce non-negativity across all four contingency table cells ($n_- \le L_c$ and $n_+ \le N - L_c$, with conditional rates bounded in $[0, 1]$). Checking 1D marginal balances or signed defect sums alone does not establish realizability.
>
> 5. **Hermetic Python Verification Runtime & Concurrency Requirement:**
>    Deposit verification scripts (`verify_deposit.py`) and pytest sweeps MUST be executed using the workspace-standard Python 3.12 runtime (`py -3.12`). Agents must never invoke unpinned `python` or newer runtimes (e.g. Python 3.14+) that may introduce standard library namespace shadowing with package `code/` directories.
>    When running pytest sweeps with parallel execution (`xdist`) alongside notebook executions or numerical libraries (NumPy/OpenBLAS) on Windows, child process environments must set single-thread locks (`OPENBLAS_NUM_THREADS="1"`, `OMP_NUM_THREADS="1"`, `MKL_NUM_THREADS="1"`) and isolate `--basetemp` to a dedicated nested subpath (`Path(temp) / "pytest"`) to prevent memory buffer pool exhaustion and directory locking contention.

---

## Cross-References

Evidence dependencies, transport scope, claim-pointer quarantine, and release archive integrity are defined in [`rl_publication_evidence_closure_and_release_integrity.md`](../../../../../rules/papers/rl_publication_evidence_closure_and_release_integrity.md).

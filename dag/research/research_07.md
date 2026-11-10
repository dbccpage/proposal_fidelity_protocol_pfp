# Research agent 07: metamorphic checking views

Status: **proposed_not_evaluated**. The machine-readable specification is [research_07.json](research_07.json).

This report proposes three workflows combining PFP, EIS, PCIV and OPERADS. It did not read or solve `seed_prompt.txt`, access private benchmark storage or an answer key, execute a benchmark, or make paid model calls. These are repository adaptations of established techniques, with no claim of literature-wide novelty.

Every future model call receives the exact original UTF-8 seed in a separate immutable message. A transformed artifact is a **checking view**, with its own context and bridge receipt. It cannot replace the original task, change assumptions, omit requested parts or redefine the output. Responses freeze before isolated trusted scoring; private feedback never enters a repair call.

## Sources and repository basis

[Chen, Cheung and Yiu's primary metamorphic-testing report](https://arxiv.org/abs/2002.12543) motivates relational tests when direct output oracles are unavailable. Its abstract was inspected; the PDF's text extraction was garbled. Such tests can expose faults without proving correctness when they pass.

[NIST SP 811 §7.1](https://www.nist.gov/pml/special-publication-811/nist-guide-si-chapter-7-rules-and-style-conventions-expressing-values) distinguishes a quantity from its unit-dependent numerical value. [Watrous's author-hosted text, §2.1.3](https://cs.uwaterloo.ca/~watrous/TQI/TQI.pdf) gives direct tensor-product and index definitions of partial trace. [Peres's original paper](https://arxiv.org/html/quant-ph/9604005v2) uses explicit subsystem indices and a necessary partial-transpose condition. The proposed workflow machinery and bridge receipts are our adaptations; none of these sources establishes their empirical benefit.

Concrete implementation boundaries:

| Repository evidence | Consequence |
| --- | --- |
| `dag/FOUNDATIONS.md:5–33,39–41` | Checking a declared relation, detector performance, prompt lineage and typed composition have distinct limits. |
| `dag/benchmark/EXPERIMENT_PROTOCOL.md:5–9,13–19` | Preserve the seed, separate online checks from private scoring, calibrate detectors, and use one run-wide USD 0.10 ledger. |
| `pfp/use_cases/pfp_proposal.py:35–43,118–137` | PFP can inject host judges and issue bounded public repair classes. Raw judge diagnostics are unsuitable repair feedback. |
| `pfp/domain/exact/linalg.py:24–54` | Existing matrices use exact rationals and require a bound computational port. Complex/symbolic adapters below are proposed. |
| `eis/domain/thymus.py:145–178,180–215` | Screen the actual active, bound detector against all supplied clean fixtures. A clean panel establishes only finite-panel evidence. |
| `eis/domain/danger_gate.py:1–21,111–117,142–153` | Correlated check failures cannot become an independently justified danger signal by relabelling. |
| `pciv/use_cases/research_mutation.py:8–31`; `pciv/use_cases/genealogy.py:101–143` | Protect original context and record parent/view lineage; those records do not prove preservation. |
| `operads/domain/operad/planar.py:34–61,85–95` | Ordered type compatibility supports wiring. Mathematical preservation needs additional premises and witnesses. |

## R07-I01 — Basis-orbit covariance with composition controls

For an admitted unitary map, use the checking action $T_U(X)=UXU^\dagger$. Transform all relevant operators, vectors and measurements consistently. Evaluate a candidate's restricted AST on transformed source objects and compare it with transport of the original candidate result. Also check inverse and composition laws, including $T_VT_U=T_{VU}$.

This goes beyond checking a single representation edge: a bounded orbit tests the candidate evaluator's equivariance. Both sides must follow separate paths. Constructing both sides from the same output is a deliberately vacuous control. Eigenvector outputs need phase/subspace equivalence. Entanglement-related invariants require local maps relative to the declared partition.

PFP binds the original objects and checks public relations. OPERADS carries representation contexts. EIS tests valid controls and missing-conjugation/order mutants. PCIV protects the seed and records view lineage; any later wrapper selection uses independent fixtures.

**DAG:** bind → derive → orbit_check → repair → freeze. The second model call changes only affected original-answer claims.

**Hypothesis:** better convention-error detection than a matched two-call prose review. Ablate composition controls, source binding and repair. A wrong transform admitted as exact falsifies the checker; lack of matched-budget accuracy/completeness gains falsifies the practical hypothesis. Constant wrong functions can remain covariant, so covariance never means correctness.

## R07-I02 — Unit covariance with guarded limit squares

If $q=n u$, changing base units by positive scales $a_j$ sends $n$ to $a^{-d}n$, where $d$ is the quantity's dimension vector. Transform dimensional constants as well. Type-check sums, products and transcendental arguments; evaluate the same physical quantities in the resulting numerical coordinates.

Limits are a separate, one-way consequence check. From $x(\epsilon)\to x_0$ and an admitted continuity premise for $T$, infer $T(x(\epsilon))\to T(x_0)$. Record domain, direction, topology and branch. Zero scaling is not an invertible unit change. Matrix continuity does not automatically establish continuity of eigenvector choices or earliest-attainment functionals. Finite numerical approach sequences remain diagnostics.

PFP checks quantity and domain predicates; OPERADS carries dimensions and branches. EIS calibrates missing-scale and invalid-limit detectors with valid exceptional cases. PCIV protects conventions and records transformations.

**DAG:** bind → derive → check → repair → freeze.

**Hypothesis:** fewer missing-scale and unjustified boundary-substitution errors than prose review. Ablate dimensional typing, transformed constants and continuity witnesses. Accepting a limit solely from finite samples falsifies the policy. Dimensionally correct expressions can still have wrong dimensionless factors, signs or functional dependence.

## R07-I03 — Tensor-layout commuting squares

Expose both a labelled four-index tensor and a flat matrix, with an explicit reversible index map. Use independent index and matrix implementations for partial trace and partial transpose. Check local-unitary covariance and factor swaps while relabelling the affected subsystem.

Generic bridges include:

- $\operatorname{tr}_B(X)_{ij}=\sum_\alpha X_{i\alpha;j\alpha}$.
- $\operatorname{PT}_B(X)_{i\alpha;j\beta}=X_{i\beta;j\alpha}$.
- Under $X'=(U\otimes V)X(U\otimes V)^\dagger$, partial trace transforms by $U$, while partial transpose transforms by $U\otimes\overline V$.

These identities follow on matrix units and extend by linearity. Their mathematical proofs are declared bridges; correspondence with a future implementation must still be checked. PT itself is not a coordinate equivalence. An arbitrary global unitary cannot be treated as preserving fixed-partition reduction or entanglement properties.

PFP binds tensor objects; OPERADS colours include factor labels/order. EIS panels include unequal subsystem dimensions, complex entries, wrong axes, omitted conjugation and **identity-as-PT**. PCIV records the view family and protects the task.

**DAG:** bind → derive → square_check → repair → freeze.

**Hypothesis:** stronger detection of subsystem/index errors than scalar trace checks or prose review. Ablate independent code paths, asymmetric fixtures and partition labels. If identity-as-PT passes the claimed adequate detector panel, that adequacy claim fails. A wrong original state can still satisfy every tensor identity.

## Budget and evaluation boundary

Each candidate is a separate proposed run with at most **two model calls total and zero retries/fallback**. The run-wide reservation is

$$
C_{\max}=\sum_s(I_s p_{in,s}+O_s p_{out,s}+F_s)+C_{host}+R\le 0.10.
$$

Inputs include the full unchanged seed in both calls, instructions and prior artifacts. Outputs include all billable reasoning. Timeouts and failed calls remain charged/reserved and stay in the denominator. Unknown pricing, uncapped reasoning or excess input bounds refuse dispatch.

Conditional thresholds are $p_{in}\le10^{-6}$ USD/token, $p_{out}\le5\times10^{-6}$ USD/token, zero extra fees/metered host cost, and $R=0.01$. These are admission thresholds, not price quotations.

| Candidate | Total input bound | Total output bound | Full-run conditional reservation |
| --- | ---: | ---: | ---: |
| R07-I01 | 15,000 | 3,300 + 1,500 | USD 0.049 |
| R07-I02 | 14,000 | 3,000 + 1,400 | USD 0.046 |
| R07-I03 | 15,000 | 3,300 + 1,500 | USD 0.049 |

Multiple candidates form a separately authorized campaign. Host checking has finite dimension, transform-count, AST-size, integer-bit, CPU and memory limits; exhaustion is OPEN.

The reusable proposal is `CheckingViewBridgeReceiptV1`: original/view hashes, map, inverse or one-way implication, premise/dependency IDs, checker version, independent path IDs, scope and residuals. It cannot collapse numerical agreement, exact finite equality and admitted universal identities into one verified flag. The first proposed experiment is host-only tensor-index controls. No experiment has been performed.


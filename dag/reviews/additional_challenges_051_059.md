# C051–C059 remaining-path audit

Completed the frozen scope: **102 full source reads (16,932 lines)** and **1,138 bounded parsed-data dispositions** across 1,240 new paths. Forty-nine previously fully reviewed paths were excluded. All 1,289 candidate hashes still match the original inventory. There are 36 findings and nine conditional mathematical claims.

The repository-wide every-file audit remains incomplete. Parsed JSON and owner replay do not count as full content reading. No original sources, historical receipts, provider services or sealed material were changed or accessed.

Original inventory commit: `8050c66900899771766f33e8f5fdd200b7dd9120`.

| Family | Full bodies | Data dispositions | Findings |
|---|---:|---:|---:|
| C051 | 11 | 126 | 2 |
| C052 | 11 | 126 | 3 |
| C053 | 12 | 126 | 2 |
| C054 | 12 | 126 | 4 |
| C055 | 13 | 126 | 5 |
| C056 | 13 | 127 | 4 |
| C057 | 12 | 128 | 4 |
| C058 | 6 | 127 | 6 |
| C059 | 12 | 126 | 6 |

## Mathematical scope and findings

### C051

For max c^T x subject to Ax<=b and x>=0, primal/dual feasibility plus equal objectives proves optimality by weak duality; nonnegative y with A^T y>=0 and b^T y<0 proves infeasibility; a feasible point plus nonnegative improving recession ray proves unboundedness. The two previously reviewed judges enforce these exact equations. New reference review finds a phase-I producer error, not an accepted false LP certificate. Independent interval intersection covers 1950 small systems:342 wrong reference decisions and zero such decisions accepted by both judges.

126 JSON artifacts parsed with schema-specific owner replay; full content-reading credit remains zero for these artifacts. Owner verdicts are observed behavior, not independent mathematical ground truth. Nested certificate assessments and their bounds are preserved per artifact.

- **AC51-F01** — The feasible LP max x subject to -x<=-1 is reported INFEASIBLE with farkas_y=[0]. A valid unbounded witness x=1,ray=1 passes both judges; the reference certificate fails both. Phase-I objective RHS initialization has the wrong sign. All 342 mismatches in 1950 independent interval cases are caught by the judges, while supplied feasible fixtures omit negative RHS.
- **AC51-F02** — Reference rational parsing accepts Boolean coefficients as integers and returns SOLVED, while both judges classify the input malformed and reject. Thus source-generated expected answers can violate the checker input contract.

Limits: Bounded interval exhaustion is not a general simplex proof. Previously full-read checker paths receive no duplicate coverage credit. Synthetic SQLite replay and declared costs are not live provider evidence.

### C052

A capacity-feasible conserved flow gives a lower bound on maximum flow and any source/sink cut gives an upper bound; equality certifies optimality. Both previously reviewed validators enforce exact flow/cut equations, with the second also constructing residual edges. Independent cut enumeration agrees with reference and both judges for1241 small directed networks, including self-loops, antiparallel arcs and zero capacities. Input coercion and resource handling remain separate defects.

126 JSON artifacts parsed with schema-specific owner replay; full content-reading credit remains zero for these artifacts. Owner verdicts are observed behavior, not independent mathematical ground truth. Nested certificate assessments and their bounds are preserved per artifact.

- **AC52-F01** — Float capacity1.9 and float endpoint0.9 are truncated by int; Boolean capacity true becomes 1. Solver and both checkers accept certificates for the coerced graph instead of rejecting malformed original input.
- **AC52-F02** — Source calls case.get before its type guard and crashes on null. Recursive blocking-flow DFS raises RecursionError on a valid 1100-vertex unit-capacity chain, whose mathematical maximum is 1 and for which TASK states no vertex ceiling.
- **AC52-F03** — TASK limits capacities to 10^18 but solver and both judges accept larger values; generator itself includes 2^63 capacities. The exact mathematics remains correct for these larger integers, but declared input bounds are not the implemented contract.

Limits: Finite network enumeration is not a general implementation proof. No accepted false optimum was found within the bounded well-formed controls. Synthetic SQLite receipts do not authenticate model/provider execution.

### C053

For a square rational matrix, a nonzero kernel vector proves singularity. An inverse proves nonsingularity, but determinant/adjugate scaling additionally requires the determinant to be pinned. Both current judges independently compute the determinant and reject the historical coordinated determinant/adjugate spoof. Leibniz expansion, inverse identities and kernel arithmetic agree with the owner on 1,201 bounded matrices (467 singular).

126 JSON artifacts parsed with schema-specific owner replay; full content-reading credit remains zero for these artifacts. Owner verdicts are observed behavior, not independent mathematical ground truth. Nested certificate assessments and their bounds are preserved per artifact.

- **AC53-F01** — Null input raises AttributeError because solve accesses case.get before its object-type guard.
- **AC53-F02** — TASK bounds dimension by 30, while solver and both judges accept a 31-dimensional zero matrix. Its kernel certificate is mathematically valid, but the declared input boundary is not enforced.

Limits: Finite exact controls do not prove all matrix sizes or implementation paths. The historical determinant spoof is now rejected and is not reported as a current defect. No false mathematical certificate was accepted in the independent bounded controls.

### C054

Ax=b proves consistency; n-r independent kernel vectors and a nonzero r-minor pin the rank by rank-nullity. A left multiplier y with yA=0 and yb nonzero proves inconsistency directly. Both current checkers implement these equations; the secondary also recomputes rank. Independent all-minor/Leibniz checks agree on 793 small systems, including rational rectangular systems.

126 JSON artifacts parsed with schema-specific owner replay; full content-reading credit remains zero for these artifacts. Owner verdicts are observed behavior, not independent mathematical ground truth. Nested certificate assessments and their bounds are preserved per artifact.

- **AC54-F01** — Both judges accept malformed fraction 1/1/99 as 1 and accept Boolean input entries as integers; the primary additionally truncates floating right-hand sides such as 1.9 to 1, while the secondary rejects that input.
- **AC54-F02** — Null input crashes in the reference, and the declared dimension ceiling 40 is unenforced: a 41-row zero-column system is accepted by both judges. The latter certificate is mathematically valid outside the stated contract.
- **AC54-F03** — The replay-custody mutation loop looks for corrupted_result or candidate, but retained mutations use mutated_result; these mutation checks silently skip all such envelopes.
- **AC54-F04** — Primary checker accepts UNKNOWN status carrying an otherwise valid consistency certificate; secondary rejects it. The algebra is true, but verdict/status semantics differ.

Limits: No accepted false algebraic certificate was found on well-formed bounded controls. Finite minor enumeration is not a general correctness proof. Custody receipts and fabricated usage are not provider provenance.

### C055

Summing feasible dual inequalities along any permutation bounds its objective; equality with a feasible assignment proves optimality. A Hall-deficient row subset proves infeasibility. Both checkers enforce these equations, but share a zero-value maximization convention bug. Independent permutation enumeration agrees with reference outputs on 1,536 bounded min/max matrices.

126 JSON artifacts parsed with schema-specific owner replay; full content-reading credit remains zero for these artifacts. Owner verdicts are observed behavior, not independent mathematical ground truth. Nested certificate assessments and their bounds are preserved per artifact.

- **AC55-F01** — Both judges reject a valid standard maximization dual when the optimum is zero: because value and -value coincide, they choose only the negated inequalities. For costs [[1,-1],[-1,-1]], sigma=[0,1], u=[1,-1], v=[0,0] is valid under the explicitly allowed standard convention.
- **AC55-F02** — Primary checker raises TypeError on hall_rows=[[0]] before checking element types; reference raises AttributeError on null input. Secondary catches the malformed Hall exception.
- **AC55-F03** — Declared n<=60 and absolute cost<=10^18 are unenforced; n=61 Hall and cost=10^18+1 certificates are accepted. Retained huge-cost generator also exceeds the stated cost ceiling. Mathematics remains valid on those relaxed inputs.
- **AC55-F04** — Replay-custody mutation lookup ignores mutated_result, silently skipping retained attacks.
- **AC55-F05** — Primary accepts UNKNOWN with a complete optimality certificate, while secondary rejects that status; this is a status-contract difference, not a false objective.

Limits: Finite independent enumeration does not prove the Hungarian implementation generally. Both checkers largely repeat certificate arithmetic rather than provide an independent optimizer, despite the secondary module description. Planned model budgets and synthesis claims remain unevidenced by these fixtures.

### C056

Reachability plus pairwise distinguishing suffixes proves minimality of a complete DFA for its own language. Exact source binding is additionally required; current derivative and NFA/union-find judges enforce it. Independent finite-language construction agrees on 128 generated regexes over all binary words through length six, and 12 focused owner regressions pass. This bounded audit control is kept distinct from the judges exact language algorithms.

127 JSON artifacts parsed with schema-specific owner replay; full content-reading credit remains zero for these artifacts. Owner verdicts are observed behavior, not independent mathematical ground truth. Nested certificate assessments and their bounds are preserved per artifact.

- **AC56-F01** — TASK permits dot as a single-character alphabet symbol, but reference dot concatenation regex .. returns OUT_OF_SCOPE because internal concatenation uses the same token; both judges reject that false refusal. Planning a-d domain does not include this input.
- **AC56-F02** — Under TASK general character-alphabet semantics, a declared space literal should recognize one space, but all three parsers erase it and both judges accept the epsilon automaton. This is a shared source interpretation defect outside the narrower a-d planning domain.
- **AC56-F03** — All implementations accept a five-symbol alphabet despite the stated maximum four; reference null input raises AttributeError. Alphabet bound drift is separate from mathematical language correctness.
- **AC56-F04** — Public runner succeeds on an empty examples directory and regenerates reference outputs without checking retained expected_output, so its pass count is not packet-integrity or retained-answer validation.

Limits: No existing source-binding vulnerability was reproduced on ordinary declared a-d regexes. Independent membership audit is bounded to word length six. General resource exhaustion and the exact checker product ceiling were not stress-tested. No provider execution, paid inference or sealed material accessed.

### C057

For compare-exchange under a total order, a threshold map converts any unsorted output into an unsorted binary output and commutes with each comparator; exhaustive binary success therefore proves sorting. Constraint checks bind that construction to the case. Infeasibility is separately established by prefix length, a decision-tree information bound, necessary adjacent comparators or a trusted published size table. All 9,331 four-wire networks of length at most five agree across scalar truth and both judges; all nine stored constructions pass complete binary simulation.

128 JSON artifacts parsed with schema-specific owner replay; full content-reading credit remains zero for these artifacts. Owner verdicts are observed behavior, not independent mathematical ground truth. Nested certificate assessments and their bounds are preserved per artifact.

- **AC57-F01** — Participant runner reports success for arbitrary non-SOLVED status BANANA and for a sorting network that violates both mandatory prefix and forbidden constraints; it is not a substitute for the full judges.
- **AC57-F02** — Both judges raise TypeError on a list-valued status and AttributeError on a non-object case, despite separate input validators. The reference itself returns typed refusal for the latter.
- **AC57-F03** — Mutation generator references historical descriptive case filenames absent from the retained anonymized packet; its first file load would fail before generating any attacks. It was not executed because import also writes originals.
- **AC57-F04** — CHALLENGE still illustrates generic UNKNOWN and states an older source/baseline/count contract; current TASK requires a holding proof code, while current implementation uses Python heuristics and a larger disclosed literature table. Completed is not evidence of the planned synthesis experiment.

Limits: Finite network enumeration does not prove synthesis completeness. No new optimal-size theorem or external lower-bound certificate replay is claimed. Published lower bounds are trusted; checking stored networks proves upper bounds only. 43 focused tests passed, with no provider or original generator execution.

### C058

For well-formed 8-bit IR with one or two inputs, exhaustive evaluation checks universal equivalence over 256 or 65,536 assignments, conditional on interpreter semantics. Arithmetic is modulo 2^w; shift counts are modulo w and arithmetic right shift uses signed representatives. At widths 16/32/64 both judges only sample deterministic inputs. A five-operation indicator of x=123456789 at width 64 is wrongly optimized to constant zero by the reference and accepted by both judges; direct evaluation at that input gives 1 versus 0. Exact wide certification is therefore false. UNKNOWN acceptance is neither a general lower-bound certificate nor solver completeness.

127 JSON artifacts parsed with schema-specific owner replay; full content-reading credit remains zero for these artifacts. Owner verdicts are observed behavior, not independent mathematical ground truth. Nested certificate assessments and their bounds are preserved per artifact.

- **C058-F01** — Both judges and reference accept a false wide equivalence: the indicator of x=123456789 at width 64 is replaced by constant zero; the explicit distinguishing input gives 1 versus 0.
- **C058-F02** — Both judges reject a warranted UNKNOWN for constant-zero output with target length zero, although the IR requires a const instruction and zero instructions can only return an input variable.
- **C058-F03** — The independent judge accepts false UNKNOWN when the output is the second input y; it only compares four evaluations with the first input x. The primary judge rejects it.
- **C058-F04** — The reference search misses the legal one-instruction reverse immediate 4-x, returns UNKNOWN, and is rejected by both judges; the direct one-instruction certificate is exhaustively valid. This is incompleteness, not an accepted false equivalence.
- **C058-F05** — Float width 8.0 and explicit null target reach TypeError paths; bool constants are accepted as integers. These are malformed-input/domain gaps, separate from equivalence soundness.
- **C058-F06** — The participant runner prints a failed validation and returns normally, so script execution exits successfully even with zero passing examples.

Limits: Previously fully reviewed checker/optimizer/TASK bodies were consulted as support without duplicate reading credit. No SMT proof or exhaustive wide-domain check was run. Generator mutation claims are retained intentions and bounded replay, not soundness theorems.

### C059

Kleene truth tables preserve UNKNOWN and WHERE retains only TRUE; row bags preserve multiplicity and schema headings even for empty results. The current first oracle stages relational nodes in a private SQLite connection and the second interprets the AST in Python, independently of the proposer. Both share schema/bag contracts and candidate SQLite execution. Their validation is finite database agreement, not universal relational equivalence or dialect neutrality. Independent exhaustive controls cover 104 small integer/null bag-predicate pairs without mismatch; mixed-affinity and textual truth tests expose disagreements.

126 JSON artifacts parsed with schema-specific owner replay; full content-reading credit remains zero for these artifacts. Owner verdicts are observed behavior, not independent mathematical ground truth. Nested certificate assessments and their bounds are preserved per artifact.

- **C059-F01** — Both judges accept SELECT 1 AS id for a select-all spec on the supplied singleton {id:1}, but reject the same answer on {id:2}. Finite-suite agreement does not certify the broader translation objective.
- **C059-F02** — Required SQL constructs and null-ledger provenance are not enforced: SQLite-specific IS NOT replaces required IS DISTINCT FROM with an empty ledger, while a comment containing COALESCE validates an invented node/construct entry. Both are accepted.
- **C059-F03** — The judges disagree on supported mixed values: INTEGER 1 compared with text literal 01 and WHERE COALESCE on TEXT 0 follow SQLite coercion in the first oracle but Python equality/truthiness in the second. Both reference answers pass only the first judge. The task does not resolve this dialect-neutral semantic boundary.
- **C059-F04** — Reference compilation drops untouched columns after renaming a nested relation and emits invalid WHERE syntax for a semi-join without an on predicate. Both judges correctly reject these reference answers and accept separately written valid SQL.
- **C059-F05** — The shared validator admits an empty project-column list although the reference emits SELECT FROM and the two evaluators disagree on zero-column representation. The interface needs an explicit admissible-domain boundary; no accepted valid zero-column SQL certificate is established.
- **C059-F06** — Non-object cases and list-valued status/operator fields raise uncaught AttributeError or TypeError in both judges rather than producing typed rejection.

Limits: The previously fully reviewed evaluator/contract/compiler/TASK bodies were consulted without new coverage credit. 256 existing tests passed; these do not cover universal equivalence, every database type or external SQL dialect. The safe SQLite read boundary and private oracle staging were inspected; no external/provider database or destructive query was executed. Root custody test was read but not rerun; it is synthetic bookkeeping.

## Checks and custody

The JSON report records exact source paths, SHA256 values and ranges for every body and finding, plus each bounded data assessment. It retains the frozen coverage exclusions and prior receipt references. Full-range evidence identifies the supporting body; probe selectors identify the independent countercontrol.

- C056: 12 passed in 0.79s. See structured test receipt for scope.
- C057: 43 passed in 2.44s. bytecode/cache disabled; own basetemp.
- C059: 256 passed in 1.94s. bytecode/cache disabled; own basetemp.

Source generators were read; their writing entry points were not run. The C059 root custody test was not rerun. Per-artifact mathematical and parser limits remain explicit, including nonfinite JSON tokens and owner exceptions.

C057 published lower bounds are trusted literature rather than reconstructed proofs: [Harder, 11 and 12 channels](https://arxiv.org/abs/2012.04400) and [Codish et al., nine and ten inputs](https://arxiv.org/abs/1405.5754). Only the abstracts were consulted; stored networks establish construction upper bounds.

## Full source-reading ledger

### `workflows/tasks/certified_challenges/c051_exact_lp_solver_with_duals/README.md`

SHA256 `64406f01e4f0d806506862660583116f8a83da324c17aa3550b52c1687d5f9fa`; lines 1–19.

Documents test commands and an expected 36-pass count plus a14-example scoring command; these are instructions/expectations, not executed evidence or independent LP correctness. No wiki page contents are inherited.

### `workflows/tasks/certified_challenges/c051_exact_lp_solver_with_duals/__init__.py`

SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; lines empty body.

Empty package marker; zero lines and no mathematical or runtime claims.

### `workflows/tasks/certified_challenges/c051_exact_lp_solver_with_duals/judge_packet/__init__.py`

SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; lines empty body.

Empty judge package marker; zero lines and no added verification.

### `workflows/tasks/certified_challenges/c051_exact_lp_solver_with_duals/reference_solver/__init__.py`

SHA256 `035a5d4d962bf9ab42a1b537ec943191ece0371f818acfede903e1e0b8f54f10`; lines 1–4.

Re-exports solve and solve_lp_exact only. Exporting the reference does not validate its certificates.

### `workflows/tasks/certified_challenges/c051_exact_lp_solver_with_duals/reference_solver/simplex.py`

SHA256 `e6482c51f19a450d1a5b12be62d2cf0975d603d469021746e9ab8e88421c19bb`; lines 1–234.

Exact Fraction simplex with lexicographic entering variable and smallest-index basic variable on ratio ties. Phase-I objective initialization negates the auxiliary RHS before row elimination; feasible negative-RHS cases can be reported INFEASIBLE with an invalid Farkas vector. Independent interval exhaustion finds 342 wrong results in 1950 one/two-row one-variable LPs, all rejected by both checkers. Phase II returns primal/dual or feasible ray witnesses checked independently. Parser admits bool through isinstance(int), unlike both judges; pivot ceiling is operational and the cleanup pivot can exceed it.

### `workflows/tasks/certified_challenges/c051_exact_lp_solver_with_duals/reference_solver/solver.py`

SHA256 `f1ff6a41dc68ff4b88a80b1a277ac78bffb09fc09e8c21200de3622860e7bf86`; lines 1–27.

Checks outer dictionary and required A/b/c keys, then attaches case ID to simplex result without self-verification. Non-dictionary refusals omit case ID; missing ID defaults to unknown although judges compare against None. Reference parser and judge domain contracts can differ. No provider or cost accounting is implemented.

### `workflows/tasks/certified_challenges/c051_exact_lp_solver_with_duals/tests/__init__.py`

SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; lines empty body.

Empty test package marker; zero lines, no checks.

### `workflows/tasks/certified_challenges/c051_exact_lp_solver_with_duals/judge_packet/generate_hidden_cases.py`

SHA256 `cc08df530101cb6b7205c74e76d8adc5ff873f3b943e4979c0a0b3aab4898a2b`; lines 1–385.

Read all 385 lines and 64 declared cases:24 positive-optimum,8 infeasible,8 unbounded,16 controls,8 poison cases. Feasible cases use nonnegative RHS, leaving the broken feasible phase-I route untested. Comment labels and notes are not verified by the generator; explicit scaling/permutation controls are manually authored. Writes occur only in main and were not run.

### `workflows/tasks/certified_challenges/c051_exact_lp_solver_with_duals/judge_packet/generate_mutations.py`

SHA256 `8a593fb21aca2e0b997b8aefd405e471ad0aed8cab32b62770e783b6ce127ff6`; lines 1–282.

Derives 48 mutations from nine owner answers, exercises dual signs, primal perturbations, values, Farkas sign/length, rays, canonical forms and statuses. It writes originals only under main, not executed here. Does not invoke judges before emitting, and depends on source solver answers being valid. Omitted feasible-negative-RHS cases prevent producer phase-I regression detection.

### `workflows/tasks/certified_challenges/c051_exact_lp_solver_with_duals/participant_packet/generate_examples.py`

SHA256 `6c58ecd8a5bfbd3f15cb54ffd32ed0e2cb66f76db49c2abee9ffb86274d4499f`; lines 1–91.

Fourteen cases with expected_output generated by the same solve implementation. Includes malformed dimensions and missing keys, large integers and Beale-style coefficients, but no feasible negative RHS. Solver output is persisted without independent checking; generation was not run.

### `workflows/tasks/certified_challenges/test_c051_replay_custody.py`

SHA256 `e4ec82bcf5ba9defdec69c24532d29a252fc2a53191ede7d211f8f8d38f4e94d`; lines 1–164.

Read164 lines: only first 12 sorted judge cases and first 5 mutations are sampled; empty/missing mutation fields silently skip checks and mutation-file count is not asserted. Concurrent SQLite test stores two synthetic harness labels with invented token/cost values and replays the same solver/checkers. It verifies storage/replay behavior, not live provider provenance or independently authenticated truth; test was not run against historical stores.

### `workflows/tasks/certified_challenges/c052_maxflow_mincut_certificates/README.md`

SHA256 `46adf6c56f5ddbf12ae9fe6f70f8732135a163cb932ab16baebe8290d9e9024e`; lines 1–16.

Lists replay-custody command, expected two-pass count and public 14-case invocation. These are instructions rather than evidence of complete verifier soundness. Wiki contents were not retrieved or presumed.

### `workflows/tasks/certified_challenges/c052_maxflow_mincut_certificates/__init__.py`

SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; lines empty body.

Empty package marker; no mathematical or operational content.

### `workflows/tasks/certified_challenges/c052_maxflow_mincut_certificates/judge_packet/__init__.py`

SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; lines empty body.

Empty package marker; no checker logic.

### `workflows/tasks/certified_challenges/c052_maxflow_mincut_certificates/reference_solver/__init__.py`

SHA256 `c1170ee50602de9e5de08256478617466387dcd2089be161b6f70ae3b94c1e0a`; lines 1–5.

Re-exports solve only and does not validate or certify results.

### `workflows/tasks/certified_challenges/c052_maxflow_mincut_certificates/reference_solver/max_flow.py`

SHA256 `d6e8ad0490aaf2f3ecb8c354c6ff3ee196bb59e0c28f21121d0304b3be3c5782`; lines 1–106.

Dinic residual representation keeps distinct forward/reverse edges for parallel and antiparallel arcs and adjusts reverse indices for self-loops. BFS levels, DFS blocking flow and final residual reachability produce a flow/cut pair. Independent minimum-cut enumeration agrees on 1241 complete small networks. Recursive DFS crashes on a1100-node unit chain. Fixed push bound10^32 is safe for declared capacities<=10^18, but loses scale-independent runtime on unrestricted larger capacities; no runtime failure beyond the contract is claimed.

### `workflows/tasks/certified_challenges/c052_maxflow_mincut_certificates/reference_solver/solver.py`

SHA256 `f7ba0ca82140d41451edadb883176a663418f908dfbf4ed762e461f5dec998c3`; lines 1–107.

Attempts case.get before dictionary validation, so null input raises AttributeError. Casts nodes/endpoints/capacities with int, silently truncating floats and admitting Booleans. Both previously reviewed judges share arc coercion, accepting a rounded replacement instance. Does not enforce TASK capacity10^18 ceiling or guard recursive solver exceptions.

### `workflows/tasks/certified_challenges/c052_maxflow_mincut_certificates/matrix_cases.py`

SHA256 `06d07f846037219631f47338c66e40158b9df686fd2527a11101a0fa083f5046`; lines 1–91.

Ten small inline cases cover diamond, disconnected, parallel/antiparallel, bottleneck, large capacity, multiple cuts, matching, a misleading note and s=t. They are retained synthetic matrix inputs, with no actual provider/model matrix execution inferred.

### `workflows/tasks/certified_challenges/c052_maxflow_mincut_certificates/judge_packet/generate_hidden_cases.py`

SHA256 `fe17fade4ff74bd441b90565e096ac9c4895cebbef0c0b164a36075c32183e28`; lines 1–394.

Read all 394 lines generating32 base,16 controls and 16 poisons. Layered/bipartite/grid and parallel/self-loop cases are substantive; several control rows duplicate transformations and fixture labels are not certified. Cases with2^53 and 2^63 capacities exceed the TASK10^18 ceiling in some rows, exposing domain/spec drift. Deterministic local random seeds affect only arc order. No generator writes were executed.

### `workflows/tasks/certified_challenges/c052_maxflow_mincut_certificates/judge_packet/generate_mutations.py`

SHA256 `7d3d1a3e50b5f90f1f594bd4b3af12475429741cb326e2f777ed88b53b1c8b68`; lines 1–318.

Read318 lines with48 mutations covering capacities, conservation, balances, cuts, strings/types and refusal status. It derives answers from the owner solver but never calls a checker before writing. Most attacks share one diamond; floating input coefficients, Boolean capacities and deep paths are absent. Some comments about which cut edge is backward do not match returned cut, while conservation still rejects mutation.

### `workflows/tasks/certified_challenges/c052_maxflow_mincut_certificates/participant_packet/generate_examples.py`

SHA256 `3fd6e071027bbd9a96d00c8d3c340717d24629141d72f5836e79e50568da7690`; lines 1–142.

Defines14 examples and stores owner-derived expected_output. Includes self-loops, parallel and antiparallel arcs, huge capacities and four malformed cases; no independent oracle labels or provider evidence. Writes are guarded by main and were not run.

### `workflows/tasks/certified_challenges/test_c052_replay_custody.py`

SHA256 `72a71f5d31fa6cbffb664ed1fa16055727284eacbd576a61f7f3fa45e42b281b`; lines 1–162.

Tests ten matrix cases and at most first five mutation files, skipping empty envelopes and asserting no mutation count. SQLite persistence/concurrent replay uses six synthetic records from three same reference answers under PFP/ADVERSARY labels with fabricated costs. This checks replay custody only, not external provenance, complete packet coverage or independent max-flow ground truth.

### `workflows/tasks/certified_challenges/c053_bareiss_fraction_free_matrix_inversion/README.md`

SHA256 `40f80ccf4f37f0f6363ae7c0ac0a09ed2d3e6e41704e0931b18154de8f91d848`; lines 1–19.

Read all 19 lines. Commands and expected test totals are documentation, not execution receipts or evidence of universal soundness. Linked wiki was not retrieved.

### `workflows/tasks/certified_challenges/c053_bareiss_fraction_free_matrix_inversion/__init__.py`

SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; lines empty body.

Empty package marker.

### `workflows/tasks/certified_challenges/c053_bareiss_fraction_free_matrix_inversion/judge_packet/__init__.py`

SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; lines empty body.

Empty package marker.

### `workflows/tasks/certified_challenges/c053_bareiss_fraction_free_matrix_inversion/tests/__init__.py`

SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; lines empty body.

Empty test package marker.

### `workflows/tasks/certified_challenges/c053_bareiss_fraction_free_matrix_inversion/matrix_cases.py`

SHA256 `6f9ac9b5cb2198ac22049e73a0423504b9fbd195d6dc07091d12e605344f6f3d`; lines 1–44.

Ten retained synthetic matrices exercise singular, invertible, rational, large-integer and poisoned inputs. They establish neither actual model-matrix execution nor external ground truth.

### `workflows/tasks/certified_challenges/c053_bareiss_fraction_free_matrix_inversion/reference_solver/__init__.py`

SHA256 `a1b4a22f03df3033dba0626bd60586ba565cced7238cd63f436eb6e9ac3dd5b3`; lines 1–5.

Re-exports solve; no independent validation.

### `workflows/tasks/certified_challenges/c053_bareiss_fraction_free_matrix_inversion/reference_solver/bareiss.py`

SHA256 `bc0aad6952a24db67a761b871cc689f4ab9e69fdc633aa180875692ccb418375`; lines 1–166.

Exact denominator clearing, fraction-free elimination with row-swap sign, cofactor adjugate and inverse construction were read. Independent Leibniz determinant and kernel checks agree on 1,201 small integer/rational matrices. The null-vector loop decrements a for-loop variable ineffectually after a missing pivot; no false witness was reproduced, and choosing the first free column avoids relying on later skipped pivots. This code smell is not promoted to an unsoundness finding.

### `workflows/tasks/certified_challenges/c053_bareiss_fraction_free_matrix_inversion/reference_solver/solver.py`

SHA256 `d3f6a11b491b23c7ac2c4abf80246b65c1dec2c4fb99354745b4c3b50698d916`; lines 1–87.

Routes square rational matrices to determinant/inverse or nonzero null-vector certificates. Accesses case.get before validating input type and does not enforce the stated dimension ceiling of 30. Malformed null input crashes; a 31-dimensional zero matrix is accepted by both judges despite that contract boundary.

### `workflows/tasks/certified_challenges/c053_bareiss_fraction_free_matrix_inversion/judge_packet/generate_hidden_cases.py`

SHA256 `ad72e50e818b7b0560e84d5dd101fcf46cfba421139c8e135f993a4c3283d129`; lines 1–280.

All 280 lines read. Generates 32 base, 16 control and 16 poisoned cases with dimensions up to six, owner-derived labels and repeated transformations. No independent oracle or coverage through the stated dimension limit is supplied; generator writes were not executed.

### `workflows/tasks/certified_challenges/c053_bareiss_fraction_free_matrix_inversion/judge_packet/generate_mutations.py`

SHA256 `3fe79b47766812dae26266e7267173260b42b840295c947b081794c05f3603ec`; lines 1–277.

All 277 lines read. Constructs 48 scalar, matrix, type, schema and status corruptions from small owner-derived solutions without calling a checker before persistence. Most payloads share a few two/three dimensional bases. These mutations are bounded controls, not a soundness proof.

### `workflows/tasks/certified_challenges/c053_bareiss_fraction_free_matrix_inversion/participant_packet/generate_examples.py`

SHA256 `40bc625f1bd67cc8e8e35f3d4f28b5ad405949245514964e0035b5b310817545`; lines 1–85.

All 85 lines read. Builds 14 public input/expected_output records from the reference solver, guarded by main. Expected answers share solver provenance and are not independent truth.

### `workflows/tasks/certified_challenges/test_c053_replay_custody.py`

SHA256 `adebd3a0445a1c860f2c0f536d96253a1c161f769a6963fa62e3bf38e09ec1fd`; lines 1–162.

All 162 lines read. Replays matrix cases and at most five mutation files, skipping missing candidate envelopes without asserting tested mutant count. SQLite and concurrent tests use synthetic reference answers and fabricated usage/cost labels; this tests custody mechanics, not model execution or independent mathematics.

### `workflows/tasks/certified_challenges/c054_exact_linear_systems/README.md`

SHA256 `5d7d83a9f28f67928a5a33bf7c68cbcef206d109871a05a7a853abfce72879c8`; lines 1–19.

All 19 lines read. Expected 45-test total and commands are instructions, not reproduced execution evidence. Wiki contents were not consulted.

### `workflows/tasks/certified_challenges/c054_exact_linear_systems/__init__.py`

SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; lines empty body.

Empty package marker.

### `workflows/tasks/certified_challenges/c054_exact_linear_systems/judge_packet/__init__.py`

SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; lines empty body.

Empty package marker.

### `workflows/tasks/certified_challenges/c054_exact_linear_systems/tests/__init__.py`

SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; lines empty body.

Empty test marker.

### `workflows/tasks/certified_challenges/c054_exact_linear_systems/reference_solver/__init__.py`

SHA256 `ebb3e9851553fd8f3a890f4a406c87b9b2d36c571fb2c20fe8597edefbdea670`; lines 1–3.

Re-exports solve only.

### `workflows/tasks/certified_challenges/c054_exact_linear_systems/reference_solver/solver.py`

SHA256 `5911ac6418139f96afb48c2789095ca7f98ebc9183d75dec1a67778f271aff5f`; lines 1–11.

Thin wrapper around solve_linear_system; adds no validation or exception boundary.

### `workflows/tasks/certified_challenges/c054_exact_linear_systems/reference_solver/linear_solver.py`

SHA256 `bf61ce088a649a74fae8fd3664b4cbab08de353cb7f87d32a1a41e551a6a9658`; lines 1–265.

All 265 lines read. Gauss-Jordan operations on [A|b|I] preserve left multipliers, producing contradiction witnesses or a particular solution and free-variable basis. Rank and nullspace minors plus rank-nullity certify completeness. Original-row tracking remains valid under ordered pivot selection. Independent exhaustive minors agree on 793 controls. Input Boolean acceptance, null-object crash and absent dimension ceiling are distinct contract defects.

### `workflows/tasks/certified_challenges/c054_exact_linear_systems/matrix_cases.py`

SHA256 `42d1b7a3234c1e63e50572b98966ce5d3bfceb9503e61bf9fa50c760b4b94051`; lines 1–61.

Ten retained fixed cases cover rank, inconsistency, rational arithmetic, large integers and misleading/ragged inputs. They are synthetic inputs rather than provider execution evidence.

### `workflows/tasks/certified_challenges/c054_exact_linear_systems/judge_packet/generate_cases.py`

SHA256 `a33f2068b3f6f4c5569dea0e1ee0bf084532750194aa652a32aeb7b6767ad8ad`; lines 1–571.

All 571 lines read. Builds 64 cases with 32 bases, 16 exact row/column transformations and 16 poisons. make_square_invertible actually creates a dense random matrix with nonzero diagonal, which alone does not guarantee nonsingularity; b=A*x still guarantees consistency. Actual retained ranks are assessed separately. Writes guarded by main were not executed.

### `workflows/tasks/certified_challenges/c054_exact_linear_systems/judge_packet/generate_mutations.py`

SHA256 `0a1ea8b511f8900d4a8755676a7426876e4d5938363d255d9d08ee0dcfaf5fb2`; lines 1–389.

All 389 lines read. Constructs 48 mutations including solution/witness equations, rank/null minors, canonical syntax, missing fields and malformed inputs. Unlike several earlier families, main explicitly calls both judges and raises if either accepts; it writes artifacts before its final survival failure. Payload field is mutated_result, incompatible with the root custody test lookup.

### `workflows/tasks/certified_challenges/c054_exact_linear_systems/generate_examples.py`

SHA256 `64ff7ea3c99e47722e31eea7684984434abf0035d7cb9253cac427f5718efea7`; lines 1–77.

All 77 lines read. Defines 14 public examples including zero dimensions, constructs owner answers and checks both judges before writing. Shared checker approval is useful bounded consistency evidence but not independent mathematical truth.

### `workflows/tasks/certified_challenges/test_c054_replay_custody.py`

SHA256 `f04057b0bf2cc13000073557b3b3668f8f0d0feb535228743ee54d7a66e6db41`; lines 1–162.

All 162 lines read. Matrix-case replay and SQLite persistence are synthetic. Mutation loop reads only corrupted_result or candidate while actual generated envelope uses mutated_result, so those mutations are skipped; it asserts no tested count. Concurrent records repeat three reference answers under two labels and fabricated token/cost values.

### `workflows/tasks/certified_challenges/c055_assignment_with_potentials/CHALLENGE.md`

SHA256 `6369f1d5aa26b6d265e40908a1108971fcd3cd5d1bba105701fd8d2a7482f3bb`; lines 1–133.

All 133 lines read. Planned synthesis experiment, budget, model sizes, paired tests and hooks are proposals, not executed results. Weak duality and Hall certificates are sufficient as stated, including negated maximization. Built Python package differs from planned Rust i128 checker and planned packet counts. Named synthesis, cost and arm-advantage claims need actual provenance and paired observations absent from this file; no current pricing/provider claim inferred.

### `workflows/tasks/certified_challenges/c055_assignment_with_potentials/README.md`

SHA256 `42bdd3145e47f33248971783e997ba292225bf586e37c1d6a61826cb9ebeb9bf`; lines 1–19.

All 19 lines read. Expected 59-test count and replay commands are documentation, not new executed evidence.

### `workflows/tasks/certified_challenges/c055_assignment_with_potentials/__init__.py`

SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; lines empty body.

Empty package marker.

### `workflows/tasks/certified_challenges/c055_assignment_with_potentials/judge_packet/__init__.py`

SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; lines empty body.

Empty package marker.

### `workflows/tasks/certified_challenges/c055_assignment_with_potentials/tests/__init__.py`

SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; lines empty body.

Empty package marker.

### `workflows/tasks/certified_challenges/c055_assignment_with_potentials/reference_solver/__init__.py`

SHA256 `ebb3e9851553fd8f3a890f4a406c87b9b2d36c571fb2c20fe8597edefbdea670`; lines 1–3.

Exports solve only.

### `workflows/tasks/certified_challenges/c055_assignment_with_potentials/reference_solver/solver.py`

SHA256 `8bccbcdcbc65ba2578b0d2aeed08aed7a459b0298b5d57b087d98dda15185e3b`; lines 1–11.

Thin assignment wrapper; no input-object or exception guard.

### `workflows/tasks/certified_challenges/c055_assignment_with_potentials/reference_solver/hungarian.py`

SHA256 `da5fe8103bc6d5ffa7f70ca5a07e1936e0513b5f00666c62d5f7e7076d7668bc`; lines 1–214.

All 214 lines read. First computes a maximum allowed matching and extracts a Hall set by alternating reachability; otherwise integer Hungarian updates use a penalty larger than any feasible objective difference. Infinity is only an initialization sentinel within the stated finite bound. Exact permutation enumeration agrees on 1,536 small cases. Does not enforce n or cost bounds; null input raises before validation.

### `workflows/tasks/certified_challenges/c055_assignment_with_potentials/matrix_cases.py`

SHA256 `fdf6dc32a32cfc681dfb9d0d54a68a145e04d989730754f4f3b4ae148f89d013`; lines 1–53.

Ten synthetic retained cases exercise min/max, forbidden pairs, Hall obstructions, large/negative costs and poisoned input. No model-matrix execution is shown.

### `workflows/tasks/certified_challenges/c055_assignment_with_potentials/judge_packet/generate_cases.py`

SHA256 `25715ef9b76d244c1f95eda210a144cc9331fa525d4b64677fb55848ef4375e9`; lines 1–586.

All 586 lines read. Generates 64 cases with 32 bases, 16 transformations and 16 poisons. Includes valid Hall examples and deterministic dense matrices through size 15. Huge-cost fixture contains entries up to 4*10^18, above the TASK ceiling. No independent result oracle or executed generation is inferred.

### `workflows/tasks/certified_challenges/c055_assignment_with_potentials/judge_packet/generate_mutations.py`

SHA256 `3c90e4fde79658d490201aef1c7f0e70f6e667182bdf33e2010792930434bcb8`; lines 1–406.

All 406 lines read. Builds 48 attacks and calls both checkers, rejecting if either accepts. Mutated payloads use mutated_result; root replay looks for different keys and skips them. Attacks omit valid standard maximization duals with zero optimum and nested unhashable Hall indices.

### `workflows/tasks/certified_challenges/c055_assignment_with_potentials/generate_examples.py`

SHA256 `2a91c713ddaa890a566cd8b09c0754b4ecfa9af9405d301157450d3059e7b8ad`; lines 1–111.

All 111 lines read. Fourteen examples use owner-derived answers checked by both judges before persistence; they are bounded controls with shared provenance. Main was not executed.

### `workflows/tasks/certified_challenges/test_c055_replay_custody.py`

SHA256 `d4e19d25a48da1f318cf7c0cb6619ea54be2892a51131ca3ff381a783a6af13d`; lines 1–162.

All 162 lines read, including a separate untruncated re-read. Mutation envelope lookup skips mutated_result, with no tested-count assertion. Synthetic SQLite/concurrent replay repeats reference outputs under two harness labels; usage/cost are fabricated fixtures, not provider evidence.

### `workflows/tasks/certified_challenges/c056_dfa_minimization_equivalence/CHALLENGE.md`

SHA256 `bc8b3eb343a2b643e2079ac65fa5040d5e36100989210783a3f20eabb19b9eb5`; lines 1–135.

All 135 lines read. Planned synthesis/budget/arms/statistics are not execution evidence. Access and pair separators certify minimality of the supplied DFA only after source-language binding, which the current checkers do perform. The assertion that source equivalence cannot be certified is overbroad: finite simulation/product relations can serve as certificates, although this design recomputes it. Planning limits a-d and 60 nodes, unlike broader TASK character alphabet; current code is Python with derivative and NFA engines rather than planned Rust/Python roles. No provider or pricing assertions inferred.

### `workflows/tasks/certified_challenges/c056_dfa_minimization_equivalence/participant_packet/TASK.md`

SHA256 `45178daf47b6e56d40399a303a1bccc145b6884c2b575d45cab00bdc661514a4`; lines 1–95.

All 95 lines read. States exact complete minimal DFA semantics, access/separator certificates, EQUAL isomorphism and DIFFERENT membership witness. Alphabet permits up to four single-character symbols without excluding whitespace or dot. That broader domain conflicts with parser formatting/internal-operator conventions; planning prose has narrower a-d letters.

### `workflows/tasks/certified_challenges/c056_dfa_minimization_equivalence/reference_solver/__init__.py`

SHA256 `48e8fe3b5df7916149d96601b0c81c57b11b4c8ac453bf7544746a04fea50a25`; lines 1–5.

Five-line solve export; no new certification.

### `workflows/tasks/certified_challenges/c056_dfa_minimization_equivalence/reference_solver/regex_parser.py`

SHA256 `2e8e0e202351845931273e8b924823c1894f6e5fc47c00a40ed14585d4bf384e`; lines 1–146.

All 146 lines read. Uses explicit dot insertion and shunting yard despite recursive-descent description. Dot is permitted as alphabet literal but collides with inserted concatenation and causes valid dot concatenation rejection. Whitespace is stripped/skipped even when declared a literal. No alphabet size ceiling; duplicate and reserved operator checks otherwise explicit.

### `workflows/tasks/certified_challenges/c056_dfa_minimization_equivalence/reference_solver/dfa_engine.py`

SHA256 `14d0f43529b927550d203c1e1c002b7672b50314b983c8f3ba58e6ba13b381bf`; lines 1–271.

All 271 lines read. Thompson construction, epsilon closure and reachable subset construction preserve language; partition refinement yields reachable quotient states. BFS access and pair words witness minimality. Product BFS supplies difference or an isomorphism between minimal equal DFAs. General subset blowup is unbounded here; finite checks do not establish resource completeness.

### `workflows/tasks/certified_challenges/c056_dfa_minimization_equivalence/reference_solver/solver.py`

SHA256 `473d1d3028db9ffd41d8177de35edd57953b73727df42903914fed5eb05f3661`; lines 1–97.

All 97 lines read. Validates alphabet element shape and regex strings, catches parser errors, but not compilation/resource errors; case.get precedes object validation. No alphabet or syntax-node bound. Reference can falsely reject dot literals while both judges correctly reject that refusal.

### `workflows/tasks/certified_challenges/c056_dfa_minimization_equivalence/judge_packet/exact_checker.py`

SHA256 `8f17758682e1b66db7d6b49562a2b90b8d109f65c5b9f2a70d6b8c8d4efea5c5`; lines 1–465.

All 465 lines read. Independent derivative parser/engine recomputes full source-language equivalence, not sampled words. Reachability/access and all separating pairs certify minimum size; EQUAL requires its own complete minimal automata with source binding and an actual isomorphism. Product ceiling 200,000 raises RuntimeError, so decidability does not imply operational totality. Input case.get still precedes object guard. Shares whitespace/domain interpretation with secondary, not arithmetic source code.

### `workflows/tasks/certified_challenges/c056_dfa_minimization_equivalence/judge_packet/independent_checker.py`

SHA256 `1c7595fbf603867d16c0869f44d929f2a96cf8ad11f7d10b74232bba6f71e6ce`; lines 1–408.

All 408 lines read. Own precedence parser, Thompson NFA, subset construction and union-find equivalence; table filling checks EQUAL minimality. Also validates separators against regex membership and source language exactly. Historical bounded-length loophole is repaired. Shares whitespace stripping and absent alphabet bound; no resource/outer exception boundary. OUT_OF_SCOPE only checks invalidity, not witness.reason.

### `workflows/tasks/certified_challenges/c056_dfa_minimization_equivalence/judge_packet/generate_cases.py`

SHA256 `6b91bdc34cbba2e0c1b1ffaf6b28a2890fd65355680b792834dd48c3400d2f5a`; lines 1–454.

All 454 lines read. Sixty-four retained cases cover language identities, parity, suffixes, malformed input and relabels, but kth-from-end only k=2,3 rather than planned through ten. Writes happen at import; module was read only and never imported/executed.

### `workflows/tasks/certified_challenges/c056_dfa_minimization_equivalence/judge_packet/generate_mutations.py`

SHA256 `8aab1e72c60688709d05f80fdbc5bb00c33520330951091af0c1e93f3cffad50`; lines 1–414.

All 414 lines read. Forty-eight attacks cover DFA structure, access/separators, language difference and bijection/schema errors; generated payloads checked by both judges and nonzero exit on survivors. Writes occur before checker evaluation inside guarded function. No alphabet-literal or resource-limit controls.

### `workflows/tasks/certified_challenges/c056_dfa_minimization_equivalence/generate_examples.py`

SHA256 `524f1fbf193b5a29f57ae1e635ee7d59c3851f6f9757c6e29fc847b36b124e03`; lines 1–60.

All 60 lines read. Fourteen owner-derived public examples use case/expected_output envelope; writes happen at import, so this module was never imported. No judge validation occurs while generating.

### `workflows/tasks/certified_challenges/c056_dfa_minimization_equivalence/participant_packet/runner.py`

SHA256 `0da2612c1788106470870223884fe924b745ce7e9e97b2d81cd6cf88e57d197d`; lines 1–47.

All 47 lines read. Regenerates reference answers for case envelopes and checks both judges, ignoring retained expected_output. Empty example directory returns success 0/0. Reference-only demonstration, not synthesized solver or provider provenance.

### `workflows/tasks/certified_challenges/c056_dfa_minimization_equivalence/tests/test_c056_independent_language_checks.py`

SHA256 `5caa2b07b39521c5c800149757adecc2618276f70404fb2092e489f56430dd65`; lines 1–169.

All 169 lines read. Strong regressions for historical source-binding, missing automata and long distinguishing word defects; scans all packet cases/mutations and rejects trivial responders. Parser fuzz uses 4,000 seeded strings over fixed a,b grammar, excluding dot/whitespace alphabet cases. Import-independence check is textual and not proof of independent authorship. Executed read-only with bytecode/cache disabled: 12 passed.

### `workflows/tasks/certified_challenges/c057_sorting_network_synthesis/CHALLENGE.md`

SHA256 `bb445654b54f9b08058c5c20ae995ff1c07877b2f12c5561130817f4439f679f`; lines 1–128.

All 128 lines read. Completed label does not supply named-model synthesis, spend or paired-arm receipts. Planned Rust/SAT baseline and packet counts differ from present Python/beam implementation. Sample generic UNKNOWN is now rejected by current TASK/judges. Construction certificates establish sorting within constraints, not new optimal-size results. Zero-one principle requires a consistent total order. Hidden prefixes do not logically force search rather than lookup or transformed known networks.

### `workflows/tasks/certified_challenges/c057_sorting_network_synthesis/participant_packet/TASK.md`

SHA256 `7d8fb775f6ee9cf14265dbd8793088b557addf3d6d6fd16c6a5b6fcac6b03416`; lines 1–97.

All 97 lines read. Correct constructive certificate checks and explicit distinction between accepted proof-coded infeasibility and construction. Table lower bounds are disclosed as trusted literature, not locally verified. Adjacent-comparator impossibility follows from a binary input sorted except for that adjacent 1,0 pair; every other comparator leaves it unchanged. Final random-test description is secondary to exhaustive binary proof.

### `workflows/tasks/certified_challenges/c057_sorting_network_synthesis/reference_solver/__init__.py`

SHA256 `977f138f9abc1a1615f8fcc52242c0c4d0503032e14557eba721ce6ef1e2234f`; lines 1–5.

Five-line solve export.

### `workflows/tasks/certified_challenges/c057_sorting_network_synthesis/reference_solver/solver.py`

SHA256 `10a663dfe8ae222b8993e357bd23025f9d997ea8b7aa24602ab96db30b35ace5`; lines 1–187.

All 187 lines read. Validates case id, dimensions, integral comparator endpoints and prefix/forbidden collision. Four proof-coded refusals precede heuristic synthesis, with final zero-one check for SOLVED. Generic search failure remains a rejected UNKNOWN, not an infeasibility proof. Null case returns typed OUT_OF_SCOPE, but both judges crash on it.

### `workflows/tasks/certified_challenges/c057_sorting_network_synthesis/reference_solver/sorting_network.py`

SHA256 `2a5fbf0182d3e2853abaee40dd2b205a46bcf20d77a0b1aef2918f195174c31b`; lines 1–466.

All 466 lines read including all nine stored networks. Exhaustive independent scalar binary simulation confirms each stored construction through 12 channels. Positive simulation does not establish size optimality. Batcher/greedy/pruning preserve checked construction and protected prefix; beam width 120 with global visited pruning is incomplete, so absence of a found network proves nothing. Reflection is valid via reversing wires and complementing ordered values, not arbitrary wire permutation.

### `workflows/tasks/certified_challenges/c057_sorting_network_synthesis/judge_packet/exact_checker.py`

SHA256 `7c7f05ed2a906ff41d17fb325069634656fd4f236e192cf7137dd32c4b49a302`; lines 1–302.

All 302 lines read. Complete positive checks enforce bound, schema, prefix, forbidden pairs and exhaustive bit-parallel binary behavior. Proof-coded UNKNOWN verifies holding conditions; literature counts are an explicit trust root. Both malformed status lists and non-object cases raise before guards. No accepted false well-formed network found in all 9,331 four-wire networks of length at most five.

### `workflows/tasks/certified_challenges/c057_sorting_network_synthesis/judge_packet/independent_checker.py`

SHA256 `77a247334cdde28832129d237b380836034a55cfcdd12b9989bb6bb067b8f6f1`; lines 1–219.

All 219 lines read. Scalar enumeration independently implements all binary vectors, then 2,000 permutations plus 2,000 integer arrays (4,000, despite module claim of 10,000). Exact rejection/proof semantics match primary on finite controls, with same literature table and same malformed status/case exception seams. Authorship independence is asserted, not proven by separate source files.

### `workflows/tasks/certified_challenges/c057_sorting_network_synthesis/judge_packet/generate_cases.py`

SHA256 `182fcfb6d7ef8ffa87247c4126cf59b0eca897fd63cdd5db6ec39f1e76233402`; lines 1–465.

All 465 lines read. Generates 64 cases with owner/judge checks before writing at import time; was not executed. Two cases labelled constrained feasible forbid an adjacent comparator and are actually infeasible, correctly classified by current checkers. Poison group comment says OUT_OF_SCOPE although first two are valid infeasible. Retained labels are not independent ground truth.

### `workflows/tasks/certified_challenges/c057_sorting_network_synthesis/judge_packet/generate_mutations.py`

SHA256 `13cb58af944bfd2be93c14f5764e4c97ad2fb0d0761c8a89da2efd74cd9e6bfe`; lines 1–716.

All 716 lines read. Forty-eight attacks include real null answer and nonfinite numeric values, saved as corrupted_solution, with both judge rejections asserted before writes. Entire module executes on import and references historical descriptive case filenames now absent after identifier migration; first load path was confirmed missing without running the generator.

### `workflows/tasks/certified_challenges/c057_sorting_network_synthesis/generate_examples.py`

SHA256 `e5d0c8d06cd84a1be28c1b4b32ffe251a38160ae8c644b05979dc1287a0f0432`; lines 1–52.

All 52 lines read. Fourteen owner-derived examples are checked by both judges before writing, at import time. Module was never imported. Construction/refusal examples do not authenticate model synthesis or spending.

### `workflows/tasks/certified_challenges/c057_sorting_network_synthesis/participant_packet/runner.py`

SHA256 `8458cd30388beeec194bb3d64480dca2e2d4baf0496800e3a67aafbc3d7dcb82`; lines 1–71.

All 71 lines read. Only retained SOLVED network binary sorting and size are checked; prefix, forbidden pairs, identifiers and refusal status/proof are not checked. Isolated own-directory controls confirm success on BANANA status and a sorted network violating prefix and forbidden constraints. This weak participant runner is distinct from sounder judge paths.

### `workflows/tasks/certified_challenges/c057_sorting_network_synthesis/tests/test_c057_unknown_and_trivial_responders.py`

SHA256 `6e7741158541f1f0049530a663bbf173b5e2d9712a248e8df1b4e6006b464ec5`; lines 1–295.

All 295 lines read. Covers all packet cases, all proof-code combinations, historical unconditional-refusal loophole, nontrivial reflected alternative and exact information bound. Test named constant_unknown_responder_scores_zero actually permits matching proof codes on a strict subset; assertions are more precise than name. Literature test checks table equality/disclosure, not proof replay. Read-only execution: 43 passed.

### `workflows/tasks/certified_challenges/c058_straight_line_superoptimization/generate_examples.py`

SHA256 `014fbe87b541b99a11df3a62bedc6fcfeaaa153d7c1ce7260d9100673ff8cd96`; lines 1–172.

Read all 172 lines. Constructs 14 raw public IR cases at widths 8 and 32, including malformed declarations. Main writes originals before checking both judges, so not executed. Expected shortening comments are intentions; retained files receive independent parsed dispositions. No experimental participant results follow from example generation.

### `workflows/tasks/certified_challenges/c058_straight_line_superoptimization/judge_packet/generate_cases.py`

SHA256 `5c084a98b0ba40e9d5024b4cd9b15b25419ed9ccebe6bd7108e0d49e806bf68d`; lines 1–810.

Read all 810 lines. Defines 32 base cases, 16 renaming/reordering transforms, and 16 poison cases; widths 8 and 32 only. Main serializes cases before replaying the two checkers. Some targets equal original length and certify a bound rather than improvement. Algebraic identities use modulo-width shifts and modular arithmetic; the wide-width replay is sampled, as in F01. Did not execute the writer.

### `workflows/tasks/certified_challenges/c058_straight_line_superoptimization/judge_packet/generate_mutations.py`

SHA256 `99e5305ad5eecc09efdf4c8bb1c32bcb3f0bb84eb5713883c8301a4229e4a0e0`; lines 1–713.

Read all 713 lines. Loads descriptive case filenames and solves them at import; first loaded file currently exists. Main writes 48 candidate mutations then counts each checker rejection. Validity includes syntactic immediate ranges, so negative shifts and 256 at width 8 are rejected despite modular interpretations. The mutation set tests known edits, not exhaustive soundness; none targets the rare-trigger false acceptance. Module not imported because it writes/solves at import.

### `workflows/tasks/certified_challenges/c058_straight_line_superoptimization/participant_packet/runner.py`

SHA256 `421416d62322c4bb42ebeb6e30b32455466b5c036a7f12eaa75871dc2f0d470a`; lines 1–46.

Read all 46 lines. Runs the reference solver, checks only primary judge, displays PASS/FAIL totals, and returns None regardless of failures or empty examples. In-memory redirected fixture confirmed 0/1 failures with normal return (F06). It does not run an external participant or establish independent judge agreement.

### `workflows/tasks/certified_challenges/c058_straight_line_superoptimization/reference_solver/__init__.py`

SHA256 `42e7806f51ac39db4b63aa4a676c36e27602245f270fcfac877614d8bb85d820`; lines 1–5.

Read all five lines. Re-exports solve from solver; no separate algorithm or certificate check.

### `workflows/tasks/certified_challenges/c058_straight_line_superoptimization/reference_solver/evaluator.py`

SHA256 `f4349bd65cad67dc1a377b2e464784fa0f64416f595e9faaa48da35b0c68ccc7`; lines 1–264.

Read all 264 lines. Implements modular operations, signed arithmetic shifts, SSA/range validation, and exhaustive equivalence at width 8. Wide widths use fixed corner/LCG samples; this cannot certify universal equivalence and accepts the constructed rare-trigger counterexample. Byte-identical to previously reviewed judge evaluator, so it is shared validation logic. Float width, null target, and bool-as-int handling violate strict typed-domain expectations. Independent 128-program exhaustive width-8 controls agreed on 32,768 evaluations; this is bounded interpreter evidence.

### `workflows/tasks/certified_challenges/c059_sql_null_total_query_synthesis/README.md`

SHA256 `dafa3495461940cbcb2b748e4e39cc77824a1e48ef3dbfa54303f5af14695e25`; lines 1–19.

Read all 19 lines. Gives package and custody test commands and 256-pass expectation, confirmed by the package test run. Public runner executes reference examples, not live models. Wiki link was not used as independent evidence.

### `workflows/tasks/certified_challenges/c059_sql_null_total_query_synthesis/__init__.py`

SHA256 `012a45119a1cab85376508c4684a21b93f3d99100507fa4f4e2a34b7a3351ff6`; lines 1–4.

Read the four-line package description and AuthorityEffect declaration. This is metadata, not verification of SQL semantics or experimental custody.

### `workflows/tasks/certified_challenges/c059_sql_null_total_query_synthesis/judge_packet/__init__.py`

SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; lines empty body.

Empty package marker, zero content lines; no mathematical claim.

### `workflows/tasks/certified_challenges/c059_sql_null_total_query_synthesis/reference_solver/__init__.py`

SHA256 `595c6566369c6148c64c5e412b6a1b0b3aca7ab5bdfdc03368c5e1eed3f7926e`; lines 1–5.

Five-line export of solve; no separate validation layer.

### `workflows/tasks/certified_challenges/c059_sql_null_total_query_synthesis/tests/__init__.py`

SHA256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`; lines empty body.

Empty package marker, zero content lines; no mathematical claim.

### `workflows/tasks/certified_challenges/c059_sql_null_total_query_synthesis/matrix_cases.py`

SHA256 `828097de3d6900cba741abdabf4bcbf6ccf68faf15c0f7c93c8bca5b11bb4bce`; lines 1–142.

Read all 142 lines: ten fixed cases built from the three public sample database states, covering comparison, null checks, inner/left/anti joins, grouping, and two invalid specs. They are stored synthetic reference cases. The provider matrix from an older suite is absent and is not reconstructed by this file.

### `workflows/tasks/certified_challenges/c059_sql_null_total_query_synthesis/generate_cases.py`

SHA256 `e8a06464a5982bc340447b81f6aa5045e32b62d7c52b391ec730959ab8857ad6`; lines 1–857.

Read all 857 lines. Pure build_cases now constructs 32 base, 16 reversed-protected-order controls and 16 malformed cases; import does not create paths or solve. The same three database states are reused and are not universal query-equivalence tests. Main writes each file before dual replay, so was not run. Incorrectness outside supplied instances remains possible. Protected-order reversal does not change null disjunction semantics.

### `workflows/tasks/certified_challenges/c059_sql_null_total_query_synthesis/generate_mutations.py`

SHA256 `b5207bb19a26390bd290dfe3c1e334128bfad37ed2c65648f11d695626aea361`; lines 1–607.

Read all 607 lines. Pure explicit assembly loads retained public cases and obtains reference answers, then edits SQL/preflight/status/ledger for 48 attacks. Import has no solving or filesystem effects. Main writes before checking both judges; was not run. Generated mutation assertions test these edits only; substring ledger validation remains bypassable with comments and invented node paths.

### `workflows/tasks/certified_challenges/c059_sql_null_total_query_synthesis/tests/test_first_judge_ownership.py`

SHA256 `e74db64efa8b5f0eb7b205ad48808eeb827ff70881f06ab903a099db64d4ef3d`; lines 1–233.

Read all 233 lines. Meaningful controls block proposer imports with an active negative control, monkeypatch proposer output coherently, test private staging isolation, compare nine operator forms, preserve headings/affinity, bind NOT IN sides and negate multi-key predicates. The affinity tests call only first judge, leaving the second judge disagreement uncovered. No finite test proves universal query equivalence.

### `workflows/tasks/certified_challenges/c059_sql_null_total_query_synthesis/tests/test_fixture_orchestration.py`

SHA256 `56284847c61ba5920468b1f33c0c17ef1a5c99a244bf244b00ec9a2ef4fdfebc`; lines 1–54.

Read all 54 lines. Blocks mkdir during explicit 64/48 assembly and blocks solve/mkdir during generator import in child interpreters. Demonstrates import-time separation and fixed inventories; not byte-level artifact reproducibility or absence of all possible write APIs. Package suite passed without invoking generator mains.

### `workflows/tasks/certified_challenges/c059_sql_null_total_query_synthesis/tests/test_second_judge_heading_boundaries.py`

SHA256 `cd2da0af70ebcc4a27c2839472dd1320eb29350f984a5521ef5de446ad0537a9`; lines 1–205.

Read all 205 lines. Exercises schema-derived headings for empty output, positional unions, empty-right null extension, protected preflight headings, missing fixture fields, and blocked imports of proposer/first oracle. First-label-wins duplicate-name carrier remains explicitly limited by owner engine. Controls establish separateness for these routes, not independent specification correctness.

### `workflows/tasks/certified_challenges/test_c059_replay_custody.py`

SHA256 `913a9be8400a69d077a30586964ccd95ead863e30a4ccb797c9e8167e59ec85f`; lines 1–99.

Read all 99 lines. Creates ten synthetic reference receipts with zero tokens/cost and replays judges from temporary SQLite. Only first three mutations are considered, skipping absent/falsey case or candidate; asserts only that at least one judge rejects. This does not prove each judge kills all 48 mutations or authenticate live provider use. Source was read but this custody test was not executed because the store dependency is outside this slice.


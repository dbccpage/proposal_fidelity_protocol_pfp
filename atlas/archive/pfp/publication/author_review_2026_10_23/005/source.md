<div align="center">

# PFP V: A Practitioner's Guide to Checked Proposals

Jeremy H. Carroll\
2026-10-23 · Version 0.2.0 · Author-review extension

</div>

Code baseline: `52cb5457f6c485ba548cfd292f6012a941ed22cf`.
Package review snapshot: `e11c07ce90318309f058c8097ffd1c440a8ffb84`; package-local changes are recorded in the claim ledger and editorial history.

## Abstract

This instructional preprint presents a reproducible proposal-check workflow on a finite directed graph with exact rational edge claims. A three-edge inconsistency has a hand-checkable weighted minimum of three. The worked session distinguishes minimizing the residual of unchanged claims from admitting a consistent replacement, and follows both refusals and restoration of a saved state. The companion provides an exact Python enumeration route and a separately configured native route, with explicit input, verification, and evidence boundaries. The Examiner-style examination and study guide extend the session through counterexamples and an executable capstone. The contribution is a scoped practitioner workflow; no new theorem or measured model-performance result is claimed.

## Purpose and reader outcome

This guide takes one small inconsistent graph through a complete session: declare the instance, propose a change, interpret a refusal, admit a repair, check the result, and restore an earlier state. It is a practitioner companion to the Proposal Fidelity Protocol (PFP) research series and its legacy Symbol Game implementations. It adds no new theorem or measured model-performance result.

A **proposal** is a candidate supplied by a person, script, or model. A **host** is the program that applies the declared checks. A **receipt** records what a particular execution checked and returned. These roles matter because a plausible proposal can be wrong, while a successful check can establish less than its surrounding prose suggests.

The first session uses a scripted proposer. No model account, API key, or live conversation is needed. You should finish able to explain both an accepted move and the limits of its acceptance. The companion [Examiner quiz](./_lev_examiner_theoretical_minimum_quiz/quiz.md) has 32 questions in eight levels; its [study guide and instructor key](./_lev_examiner_theoretical_minimum_quiz/study_guide.md) supplies worked answers, refusal cases, and a capstone replay.

## 1. Declare the instance before solving it

Suppose three events have proposed offsets on one linear time axis:

- Event b is one unit after event a.
- Event c is one unit after event b.
- Event a is one unit after event c.

This is a mathematical offset example. There is no wraparound clock or recurring-day convention. Declare those conventions differently and you have a different problem.

Represent the events by vertices a, b, c and the statements by directed edges. The ordered claim vector is

\[
c=(c_{ab},c_{bc},c_{ca})=(1,1,1).
\]

A **vertex potential** assigns a number \(f_a,f_b,f_c\) to the vertices. Its edge differences are

\[
df=(f_b-f_a,\ f_c-f_b,\ f_a-f_c).
\]

The differences always sum to zero: each vertex value appears once with each sign. The supplied claims sum to three. Consequently, no potential satisfies all three unchanged claims.

Declare rational coefficients for claims and potentials, ordinary additive differences, and positive exact edge weights \(w=(1,2,3)\). A weight is the penalty for leaving one unit of discrepancy on that edge. It is a modeling choice, not evidence that one event is more truthful. The complete instance therefore includes the vertices, directed edges, edge order, exact claims, weights, units, and permitted changes. The graph has no declared two-dimensional cells. Its directed arrows alone do not attach a filled triangle.

## 2. Separate a residual from a changed claim

For a chosen potential, the **residual** is \(r=c-df\). Its weighted discrepancy is

\[
D_c(f)=|r_{ab}|+2|r_{bc}|+3|r_{ca}|.
\]

The **quotient minimum** is the smallest such discrepancy over all potentials:

\[
\Phi_w(c)=\min_f D_c(f).
\]

The notation distinguishes the score at one chosen potential from the best possible score for unchanged claims. A poor potential can make \(D_c(f)\) larger without changing \(\Phi_w(c)\).

Take \(f=(0,-2,-1)\). Then \(df=(-2,1,1)\), so \(r=(3,0,0)\) and \(D_c(f)=3\). For every potential, the residual still sums to three. Because all weights are at least one,

\[
D_c(f)\geq |r_{ab}|+|r_{bc}|+|r_{ca}|
\geq |r_{ab}+r_{bc}+r_{ca}|=3.
\]

The displayed potential attains this lower bound. This short argument establishes the minimum for this instance without requiring trust in a solver.

Two operations now have different meanings. Choosing that potential concentrates the original discrepancy on one edge; the original cycle sum remains three. Replacing the claims themselves by \(c'=(-2,1,1)\) produces a new consistent instance: \(c'=df\) and \(\Phi_w(c')=0\). The governor demonstration performs this second operation through `step_cut(proposed_claims=...)`. Acceptance says the changed claims satisfy the declared graph check. It does not establish that the changed event statement is factually correct.

| Claims | Chosen potential | Score at that potential | Minimum for those claims |
| --- | --- | --- | --- |
| \((1,1,1)\) | \((0,0,0)\) | 6 | 3 |
| \((1,1,1)\) | \((0,-2,-1)\) | 3 | 3 |
| \((-2,1,1)\) | \((0,0,0)\) | 7 | 0 |
| \((-2,1,1)\) | \((0,-2,-1)\) | 0 | 0 |

Adding the same rational constant to all three potential values changes no edge difference. The displayed potential fixes \(f_a=0\) for convenience. The unique cheapest edge fixes the minimizing residual in this instance; it does not make a numerical gauge offset observable. With tied cheapest weights, different minimizing residuals can tie as well.

## 3. Choose the executable path

The supported tutorial in this package is [code/quickstart.py](code/quickstart.py). Its Python wrapper sends exact graph inputs to the pinned Rust calculator. The repository also contains a separate historical root `quickstart.py`; the commands here intentionally name the package file.

Use Python 3.10 or newer. The Python companion is self-contained: it carries copies of the native graph adapter [code/native_functional.py](code/native_functional.py) and the Paper 004 graph governor [code/l1_symbol_game_governor.py](code/l1_symbol_game_governor.py). Each header records the source path, commit, source-byte SHA-256, and local changes. The adapter differs from its baseline only in its header and import order. The governor has documented patches to `compute_phi1`, `step_assert`, `step_cut`, and `step_verify`: input normalization and carrier checks, exact-value admission, complete replacement claims, atomic rollback on a projection error, scoped edge verification, and native-refusal propagation. `code/tests/test_vendored_sources.py` compares the remaining executable structure with the recorded source objects; its explicitly excluded patched functions and methods have behavioral regression checks in `code/tests/test_manual_contracts.py` and the earlier boundary tests. Source-object comparisons skip with a reason when the Git objects are absent.

The native calculator itself is not part of this package. For the baseline route, use a separate checkout or worktree at the recorded code baseline, confirm its revision with `git rev-parse HEAD`, then build `solve_graph_phi1` with that checkout's Rust workspace:

```powershell
cargo build --locked -j 1 --manifest-path engine/crates_rs/Cargo.toml -p core_functional --bin solve_graph_phi1
```

The following Windows PowerShell setup, run from the repository root, assumes the reviewed executable already exists at the shown path:

```powershell
$env:CORE_FUNCTIONAL_GRAPH_BIN = (Resolve-Path engine/crates_rs/target/debug/solve_graph_phi1.exe).Path
$env:CORE_FUNCTIONAL_GRAPH_SHA256 = (Get-FileHash -Algorithm SHA256 $env:CORE_FUNCTIONAL_GRAPH_BIN).Hash.ToLowerInvariant()
```

Use the actual output path if Cargo has a custom target directory. Other platforms use their native executable name. The digest pins the executable bytes used by the adapter; it is not an independent attestation that those bytes were reproducibly built from the intended source.

Now, from this package's directory, run (on Windows, `py -3.12` in place of `python`):

```powershell
python code/quickstart.py --non-interactive
python code/play_demo.py
```

The repository's [functional-boundary notes](https://github.com/dbccpage/the_symbol_game/blob/52cb5457f6c485ba548cfd292f6012a941ed22cf/education/FUNCTIONAL_BOUNDARY.md) describe the native setup at the baseline. The transport implementation is [native_functional.py](code/native_functional.py). A missing executable, missing or mismatched digest, native refusal, or malformed native response prevents an accepted native result. Treat that outcome as an environment or evidence issue to resolve before relying on the host calculation.

### Offline arithmetic when the native calculator is unavailable

You can still understand and check the finite argument. Run this ordinary Python snippet, or evaluate it by hand:

```python
from fractions import Fraction as Q

claims = (Q(1), Q(1), Q(1))
potential = (Q(0), Q(-2), Q(-1))
edge_differences = (
    potential[1] - potential[0],
    potential[2] - potential[1],
    potential[0] - potential[2],
)
residual = tuple(c - d for c, d in zip(claims, edge_differences))
assert edge_differences == (Q(-2), Q(1), Q(1))
assert residual == (Q(3), Q(0), Q(0))
assert sum(edge_differences) == 0
assert sum(residual) == 3
```

This is an arithmetic worksheet. It neither calls the native adapter nor emits a canonical functional receipt. Its lower-bound explanation is the argument in Section 2. The package test `code/tests/test_offline_worksheet.py` runs this block as printed. Record a native run as unavailable until the required calculator can execute.

## 4. Follow the complete session

[play_demo.py](code/play_demo.py) imports the package's copy of the [graph governor](code/l1_symbol_game_governor.py). It uses the manuscript's weights (1,2,3) throughout. The all-zero potential costs six; the original quotient minimum is three. The session prints and returns its selected `calculation_path` (`native` or `python-enumeration`) and its weights. This path label describes the calculator selection; it is not a source-to-binary attestation or a native receipt.

When `CORE_FUNCTIONAL_GRAPH_BIN` is set, the governor asks that native calculator, and any refusal or error it returns stops the step; no Python value is substituted. When it is not set, the governor computes the quotient minimum by exact Python enumeration of spanning-tree potentials. Without a configured calculator the session therefore still runs, but its printed values are Python enumeration results, not native results. Edge weights must be exact integers or fractions on both paths; floating-point and Boolean weights are refused. The package test `code/tests/test_play_demo.py` checks the table below on the enumeration path, and again through the native calculator when pins are configured. Enumeration can grow combinatorially with the graph; this small-session route is not a general scalability claim or an implementation of a proposal-attempt budget.

| Step | Proposed action | Expected observation |
| --- | --- | --- |
| Declare | Create vertices a, b, c and weighted edges | The host has a finite declared carrier |
| ASSERT | Install claims \(1,1,1\) | The original quotient minimum is 3 |
| CUT | Propose replacement \(5,0,0\) | `DefectIncrease`, not admitted |
| CUT | Propose replacement \(-2,1,1\) | `ExactRepair`, admitted, 3 to 0 |
| VERIFY | Request `ZERO_OBSTRUCTION` | The host checks its stored claims and admits the check |
| RETRACT | Restore the saved post-ASSERT snapshot | The original claims and minimum 3 return |

The bad proposal sums to five. Its optimum is five by the same lower-bound argument, with all discrepancy placeable on the weight-one edge. The host refuses an increase from three to five. A refused proposal does not replace the active claims.

The good proposal changes the cheapest edge from one to minus two. It supplies a consistent replacement. The demonstration saves a snapshot before either CUT and uses that snapshot's actual identifier when retracting. Do not guess a snapshot identifier from a printed step count.

ASSERT installs the starting problem; it is not a claim that every initialization step decreases discrepancy. The governor's CUT checks permit non-increase. A tied score can therefore return `IdempotentStationary`. Strict progress and finite termination of an arbitrary search require additional conditions; repeating an admitted stationary move is not a solution strategy.

`IdempotentStationary` describes an unchanged checked score, not necessarily unchanged claims. For example, replacement claims (2,1,0) still have minimum three and are admitted with that status. `RETRACT` can deliberately raise the score when restoring the original problem, so the CUT rule is not a monotonicity theorem for the whole session.

`ZERO_OBSTRUCTION` asks whether some potential fits the stored claims. `ZERO_DEFECT` asks whether the currently stored potential fits them. Consistent claims (-2,1,1) with the all-zero potential give a minimum of zero but a current discrepancy of seven. Similarly, a successful `EDGE_MATCH:b,c` checks only that declared edge; it does not discharge the original global cycle obstruction. Undeclared or malformed `EDGE_MATCH` obligations now return `VerificationFailed` rather than verifying against default zeros.

## 5. Read refusals as information

A refusal identifies a failed check. First determine which check ran and which input caused it. Then change the relevant proposal or declare a new instance when the intended problem requires different rules.

| Observed result | Meaning in this implementation | Next operator action |
| --- | --- | --- |
| `CarrierViolation` | A relational CUT endpoint or section CUT key is outside the declared vertices | Correct the endpoint or explicitly formulate another carrier |
| `MoveViolation` | A proposed edge is undeclared, or one CUT supplies both section and replacement-claim payloads | Use one permitted operation on the declared graph |
| `IncompleteProposal` | A replacement CUT omits an edge, or ASSERT/CUT supplies a non-exact mathematical value | Give exact integers or fractions; a replacement CUT must explicitly cover every edge |
| `InvariantViolation` | A prohibited input, such as a self-edge, reached the gate | Inspect the exact failed input condition |
| `DefectIncrease` | The proposed score exceeds the current score under the selected CUT mode | Compute why it increased before proposing another change |
| `IdempotentStationary` | A permitted move left the checked score unchanged | Identify a new argument or record the lack of progress |
| `VerificationFailed` | The requested obligation did not pass | Inspect that obligation, rather than treating a different successful check as a substitute |

The native transport can also fail before a governor verdict exists. Keep the transport exception and native response, if any, with the run record. A missing calculation is not a zero discrepancy.

Malformed inputs to `compute_phi1` can raise `ValueError` or `TypeError` before a verdict. Unknown claim edges and duplicate carrier entries are refused on both routes; supported `Edge` object keys are normalized before either route scores them. At initialization, unasserted declared edges have zero claims, an explicit legacy convention. A replacement CUT still must name every edge; it cannot rely on that initialization default. Section CUTs retain the legacy default of zero for omitted declared vertices, but refuse undeclared vertices and non-exact supplied values. The guide uses complete potentials to make that convention visible. An ASSERT with an undeclared endpoint returns the legacy `InvariantViolation` status rather than `CarrierViolation`.

A refused replacement or a projection exception preserves the active claims, section, and admitted snapshot history. The attempt counter may advance, so unchanged active state does not mean an identical entire runtime record. Preserve refused attempts separately from the admitted history, which does not contain every refusal or VERIFY result.

Use integers and `Fraction` inputs for mathematical values. The tutorial rejects floats and Boolean values at its mathematical input boundary. In particular, Python's treatment of `True` as an integer-like value must not turn it into a declared numerical witness.

## 6. Reproduce a result and inspect its custody

A useful reproduction record names the source revision, exact input, command, Python version, native executable digest, exit status, and output. If files change during a run, identify which version each observation belongs to. Preserve refused cases alongside admitted ones: they show whether the gate discriminates.

Run the package checks from this package's directory, one test file per command:

```powershell
python -m pytest code/tests/test_offline_worksheet.py -q
python -m pytest code/tests/test_play_demo.py -q
python -m pytest code/tests/test_quickstart_native.py -q
python -m pytest code/tests/test_manual_contracts.py -q
```

The [fixture](code/tests/conftest.py) consumes only two explicitly supplied pins:

- Executable path: `CORE_FUNCTIONAL_GRAPH_BIN`.
- Executable digest: `CORE_FUNCTIONAL_GRAPH_SHA256`.

It discovers no checkout, builds no program, and creates no pin. Missing configuration skips, with that reason, every test that requests native execution. A malformed digest, unreadable configured executable, or digest mismatch fails those tests with an explicit message. The worksheet, the offline session, the refusal, exact-input, parser, and scaffold checks, and the vendored-source header checks still run without native configuration. The commands are replay instructions, not a reported fresh pass.

The existing [execution receipt](code/paper_033_execution_receipt.json), [cross-domain receipt](code/cross_domain_symbol_game_receipt.json), and earlier release validation records are historical artifacts until their source and executable bindings are reconciled with a new run. A SHA-256 digest can bind bytes. It does not establish their truth, authenticate an unsigned producer, or supply a missing experiment. A restricted sorted-JSON encoding also needs its own stated contract; it should not be called full [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785) conformance without checking that specification. Run tests and lint separately from the default deposit verifier: the latter checks byte custody and structure rather than executing the entire suite or proving the answers.

## 7. Map a new problem carefully

Before adapting the example, write down what a vertex means, what an edge value measures, why the edge-difference relation is appropriate, and which changes are allowed. Supply units and direction conventions. Decide whether changing a claim is an acceptable correction or would replace an observation you must preserve.

For example, measured offsets might need an uncertainty model rather than unrestricted replacement. A dependency relation might be Boolean rather than an additive quantity. Encoding either as this graph is a modeling step that requires justification. Renaming vertices to “currency,” “permission,” or “quantum state” does not supply that justification.

The package's [four labeled graph scenarios](code/multi_domain_symbol_game_bouts.py) illustrate repeated use of the finite interface. Their labels do not establish market equilibrium, authorization security, or a quantum no-go theorem. The governed scripts make no LLM calls, so hypothetical unconstrained-chat costs in older records are not a measured comparison.

For model integration, keep the proposer behind the same boundary: parse the proposed fields, check the declared carrier and operations, recompute the relevant property, and save the actual response. Consult [the streaming harness](code/llm_streaming_harness.py) as an implementation example; reviewing its adapter does not establish a live provider run. The harness accepts integers and exact rational strings as claim values and refuses a JSON float or Boolean before any scoring, since `Fraction(0.1)` is the binary expansion of the float rather than one tenth (`code/tests/test_harness_exact_inputs.py`).

## 8. Connections and next reading

The familiar idea of an untrusted producer supplying evidence to a checker appears in Necula's [proof-carrying code](https://doi.org/10.1145/263699.263712). That work concerns proofs of a declared code-safety policy. It supplies context for separating proposal production and evidence checking; this tutorial does not claim its graph receipt is such a proof.

The minimization and lower-bound reasoning connect to linear-programming duality; see Boyd and Vandenberghe, [Convex Optimization](https://doi.org/10.1017/CBO9780511804441), Chapter 5. The series' [graph mathematics paper](../001_pfp_discrete_cochain_retraction_and_toy_involutions/paper.md) develops the finite theory; [Paper 004](../004_pfp_native_verification_and_evidence_custody/paper.md) explains native verification and evidence custody. The [curriculum-design guide](../007_pfp_executable_lessons_and_evidence_boundaries/paper.md) turns examples into lessons, and the [review protocol](../009_pfp_adversarial_dialectics_and_terminal_reality_gates/paper.md) explains how to audit a claimed result.

This guide supports a finite, inspectable proposal–check workflow. Its practical success criterion is that the reader can state the original instance, explain the failed proposal, distinguish residual concentration from claim replacement, and identify exactly what a fresh receipt records. General semantic correctness and model quality need their own evidence.

## 9. Limitations

The guide works one three-edge instance by hand and describes one scripted session. The current publication review checks the session and the new input-boundary cases on the exact Python route. Native execution was unavailable in that review; native-dependent tests are explicitly skipped, and a mocked native error test checks propagation and rollback without claiming to run Rust. The fresh [review record](docs/publication_review_2026_10_02.json) binds commands, outputs, tools, source comparisons, and tested files.

The earlier [author-review history](paper_change_log.md) reports a Windows native run and 75 passing package tests; its executable digest remains in the historical records and claim ledger. That report concerns earlier bytes and is not execution evidence for this patched package. The executable is not deposited. A current native acceptance claim needs a fresh build, explicit pins, and a run of the patched suite. The legacy scenario and streaming scripts remain implementation examples, not measured comparisons. The examination's UNKNOWN budget outcome is an instructional policy for a separately declared bounded search; the four-move governor does not implement that terminal status or budget controller.

This paper assigns no authorization and changes no jurisdiction. It carries no operational authority or institutional standing.

## Verification for this revision

The package verifier (`verify_deposit.py`) checks the manifest and two-way file census. The [release tool](tools/rebuild_release.py), run with `--check`, checks the archive against the manifests. The [publication review](docs/publication_review_2026_10_02.md) describes the corrections and remaining replay boundary. Its separate JSON execution record supplies the current test and lint evidence. Earlier receipts retain their dates and original scope. Version 0.1.0 remains the initial preprint candidate; no external deposit or DOI is claimed.

## Practitioner extension: run a bounded harness experiment

Freeze the source, checker, model configuration, public/private task partitions
and original budget before proposing rewrites. Use the research command's
`preflight` operation to prepare the protocol and inspect the report. The offline
form spends nothing. Live preflight additionally requires the verified Ubuntu
host, a pinned local container image, current pricing and provider compatibility.
The reproduction guide in Paper 029 gives the complete commands.

Use `run` for the experimental sequence and `resume` for an interrupted sequence
with the same retained directory. An unreconciled provider reservation is a reason
to stop dispatch, not to create a fresh budget directory. Inspect the raw response,
usage observation and attempt identity before reconciling it. Never treat a failed
model answer as a free call merely because it supplied no usable program.

Read public completion and private completion as different columns. Both selection
and confirmation are optimization data. Only the untouched transfer panel supports
the predeclared transfer comparison. A failed proposal and an unchanged reference
incumbent are valid outcomes to retain. Use `replay` and `report` to reconstruct
results offline; replay does not buy another independent model trial. This revision
has no live campaign results and supplies no basis for a performance recommendation.

The source and page references for this extension are collected in
[Paper 029](../029_pfp_evidence_bound_harness_evolution/paper.md) and its
[source-to-claim map](../029_pfp_evidence_bound_harness_evolution/docs/source_to_claim_map.md).
The author-review rendering does not replace a historical deposit or archive.

## References

- Necula, G. C. (1997). [Proof-carrying code](https://doi.org/10.1145/263699.263712). In *Proceedings of the 24th ACM SIGPLAN-SIGACT Symposium on Principles of Programming Languages (POPL '97)*, pp. 106–119. ACM. DOI: 10.1145/263699.263712.
- Boyd, S., and Vandenberghe, L. (2004). [Convex Optimization](https://doi.org/10.1017/CBO9780511804441). Cambridge University Press, Chapter 5. DOI: 10.1017/CBO9780511804441.
- Rundgren, A., Jordan, B., and Erdtman, S. (2020). [JSON Canonicalization Scheme (JCS)](https://www.rfc-editor.org/rfc/rfc8785). RFC 8785 (Informational), RFC Editor, June 2020. DOI: 10.17487/RFC8785.

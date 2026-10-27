# PREREG-DA-001: detector adequacy and the trace-residual prediction test

AuthorityEffect: None. This is a proposal and a pre-registration. Adopting it, running
its paid stage, or citing its result as evidence needs Jeremy's approval.

| Field | Value |
|---|---|
| Written | 2026-10-15 |
| Base revision | `the_symbol_game` main `dc4346860` |
| Source of the test | Test #3 from Jeremy's Gemini Notebook answer (2026-10-15), amended as below |
| Stage A (free) | Detector adequacy battery: deterministic, no model calls, no network |
| Stage B (paid) | Trace prediction study: written plan only; needs written approval and a lock of its own |
| Code | `pfp/use_cases/detector_adequacy/` |
| Lock manifest | `pfp/documentation/detector_adequacy/lock_da_001.json` |
| Results | `pfp/documentation/detector_adequacy/results/` |

## 1. The claim under test

The notebook's narrowest claim (its item 2) is a one-way reliability asymmetry. Over a
declared finite carrier and observer scope:

- **R (red side):** a positive obstruction or gluing defect (`Phi > 0`, or `Delta_E = -1`)
  carries a witness of a real defect.
- **G (green side):** a zero verdict certifies nothing unless the detector is shown to be
  adequate.

Test #3 proposes this procedure:

1. Lock an extractor and terminalizer `pi`.
2. Certify `DetectorAdequacy` on a four-case battery: known-wrong, fluent paraphrase,
   deleted citation, and mutated tool output.
3. Run a pre-registered study testing whether non-certifying residual statuses and the
   negative gluing defect (NGD) predict downstream failure better than local
   step-accuracy and gate-score baselines.

The procedure is kept. This pre-registration amends it in four places:

| # | Test #3 as written | Amendment | Section |
|---|---|---|---|
| F1 | Adequacy = never `Exact` on four fixed cases | Adequacy is a measured false-green rate, with an exact upper bound, on mutants generated after the lock, including held-out families written after the lock | 4 |
| F2 | Tests only the green side | The battery includes clean traces (false-red rate), and every red verdict must carry a witness that an independent checker replays | 4 |
| F3 | Outcome judge unspecified | The outcome judge is independent of the detector and never seen by it; the detector's relation set may not determine the outcome by itself | 5 |
| F4 | No stopping rule | The kill threshold is fixed before the paid run: NGD and residual status must add at least 0.05 AUC over the baselines and trace length, or the predictive claim is dropped | 5.4 |

Claim R is not assumed. Section 2 lists red verdicts in this repository that carry no
sound witness.

## 2. State of the repository at the base revision

Checked by reading the code at `dc4346860`. No code was run for this section.

- **No adequacy computation over traces exists.**
  - `pfp/domain/entities/lab.py:69` defines `DetectorAdequacyReceipt`.
  - `OesosLab.solve` (`lab.py:188-193`) fills it with `adequate=True, failures=()` without
    running a case.
  - The specification says the same: `ch07_finite_obstruction_calculus.md` (lines
    439-464) records "DetectorAdequacy for the extractor is OPEN", and notes that a
    collapsing extractor makes every trace `Exact`.
- **NGD is computed only over caller-supplied booleans.**
  - `adversary/infrastructure/lggr_adapter.py:19` computes
    `Delta_E = E_G - prod(E_i)`.
  - Its adequacy flag comes from two checks: at least five samples, and no evaluator that
    is constant across them. The blind-spot input `realizable_defects_in_blind_spot` is a
    boolean the caller declares.
  - No code on main turns a trace into the local verdicts it consumes.
- **The nearest runnable terminalizer is `TraceValidator.validate_trace`.**
  - Location: `atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/033_reasoning_trace_validation_via_l1_obstruction_geometry/code/mod_reasoning_trace_validation_core.py:143`.
  - It is exact rational and refuses floats. It returns `Exact`,
    `CohomologicalObstruction`, `CarrierFailure` or `BudgetExceeded`, with an exact dual
    certificate.
  - It has no extractor. The caller supplies the carrier graph and the cochain.
- **Red verdicts with no sound witness already exist** (core_mub review of 2026-10-15,
  `/mnt/project-files/reports/core_mub_review_2026-10-15/report.md`):
  - The degree-4 SDP check "refutes" a positive semidefinite Gram matrix
    (`mub6_degree4_sdp.rs:124-211`).
  - The triad search reports non-existence after testing 64 of 360 points
    (`szollosi_triad_solver.rs:428, 481`).
  - So claim R is a property to measure for each detector. It does not hold for every
    detector.
- **Existing pilots do not measure adequacy.**
  - pilot_001 grades replies with regular expressions.
  - pilot_002 hard-codes `score=5.0`.
  - Both are single runs with no baseline (OEWAS review, section 9).

## 3. Detectors (locked)

There is one terminalizer `pi = TraceValidator.validate_trace`, pinned by SHA-256 and not
modified. Three extractors feed it. All three share one set of per-step relations and
differ only in the carrier they build:

| Detector | Carrier | Unevaluable relation | Role |
|---|---|---|---|
| `D0_E0_tree` | one edge per step, to its first citation (a forest) | skipped | negative control: every cochain on a forest is a coboundary, so `pi` returns `Exact` always (the collapsing extractor of ch07) |
| `D1_E0b_citation_graph` | one edge per citation, carrying the citing step's defect | skipped | the extractor a first implementation would likely write; defects on two edges into one step cancel around a cycle |
| `D2_E1_disjoint_triangles` | each relation gets its own 3-cycle, with the defect on one edge | extractor refuses (non-certifying) | candidate for the adequacy certificate |

**Relations.** Each step has one relation, and its defect is an exact sum of absolute
differences:

| Step | Relation |
|---|---|
| `given` | matches the posed system |
| `rref` tool | reduced matrix is `[I \| x]` with `A x = b`, re-derived from the cited given |
| `read_solution` claim | `x` equals the last column of the cited reduced matrix |
| `residual` tool | reported `r` equals `A x - b`, recomputed from the cited given and claim |
| `answer` | equals the cited claim, and every cited residual is zero |

**Verdict map:**
- `Exact` → green.
- `CohomologicalObstruction` → red. The witness is the set of steps whose defect edge
  carries a non-zero value of `pi`'s dual certificate.
- Anything else, including an extractor refusal → non-certifying.

**Scope of the detectors:**
- Traces follow the structured schema in `traces.py` (given, rref tool, read claim,
  residual tool, answer), with rationals written as `"p/q"` strings.
- Items are non-singular 3x3 and 4x4 integer systems.
- The detectors do not read prose. A prose-only trace is non-certifying under `D2`.
  Singular and inconsistent systems are out of scope.

**Rule deviation, declared.** The relations re-derive matrix-vector products in Python,
even though `core_linear_algebra` is the authoritative owner of exact linear algebra.
The relations use matrix-vector products and comparisons only; there is no elimination
routine. Moving them behind the Rust port is follow-up work if `D2` is adopted.

## 4. Stage A: the adequacy battery (free)

### 4.1 Lock

- The lock commit adds `lock_da_001.json`, which records the SHA-256 of four files:
  `pi`, `detectors.py`, `witness_replay.py`, and `traces.py` (the pre-lock mutant
  families).
- The runner refuses (exit 1) unless each file matches the manifest in both the working
  tree and the lock commit.
- **Seed.** The mutant seed is the first 16 hex digits of
  `sha256("<lock commit sha>:PREREG-DA-001")`. It cannot be chosen before the detectors
  are fixed.
  - Limitation: the author could create many lock commits and keep a favourable one. The
    result records the lock commit, and the git history shows any extra lock commits.

### 4.2 Families

All families are generated from that seed, with n = 300 traces each.

| Family | Role | Construction |
|---|---|---|
| C0 canonical | clean | the solution trace |
| C1 unreduced fractions | clean | `x` written as `2k/2k`-style unreduced fractions |
| C2 paraphrased text | clean | different prose, same structure |
| C3 shuffled order | clean | step list permuted, ids kept |
| C4 redundant check | clean | second residual step, also cited |
| M1 known wrong | mutant | one coordinate of `x` perturbed in the claim and the answer; the residual tool reports honestly |
| M2 fluent paraphrase | mutant | M1 with prose asserting verification on every step |
| M3 deleted citation | mutant | M1 with one supporting citation removed (residual step dropped, rref uncited, or given uncited) |
| M4 mutated tool output | mutant | one entry of the rref output changed; the read claim, the residual output (set to zero) and the answer all agree with it |
| H* held-out | mutant | families written **after** the lock by a separate agent that did not read `detectors.py`; added in a later commit; their file hash is recorded in the result |

The four mutant families M1-M4 are the notebook's battery. The held-out families answer
the objection that a detector can be tuned to cases its author knows in advance.

### 4.3 Measurements

For each detector and family:
- the counts of green, red and non-certifying verdicts;
- for each red verdict, whether its witness replays;
- the outcome-judge result for each trace.

**Witness replay.** `witness_replay.py` re-derives each named step:
- the reduced matrix by Cramer's rule;
- products and answers with the Adversary dossier checker (`check_answer`, `mv` in
  `adversary/tests/pilots/replay_runners/dossier_capsules/checking.py`).

None of the detectors' parsing or arithmetic is used. A witness replays when it names at
least one step and every named step is defective.

**Bounds.** Rates are reported with the exact one-sided 95% Clopper-Pearson upper bound.
For example, 0 of 300 gives 0.0099.

### 4.4 Certificate (all conditions per detector)

| Id | Condition |
|---|---|
| A1 | every mutant family, held-out included: false-green upper bound ≤ 0.02; pooled over mutant families ≤ 0.01 |
| A2 | every clean family: false-red upper bound ≤ 0.02 |
| A3 | every red verdict, clean or mutant, has a witness that replays (no exceptions) |
| A4 | the lock verifies |
| A5 | every clean family: non-certifying upper bound ≤ 0.02 (a detector that refuses everything fails) |
| — | n ≥ 300 per family |

**What a certificate covers:**
- this trace schema, this item class, the families run, and the locked file bytes;
- nothing about prose traces, other tasks, or model-written traces;
- no authority: the certificate is evidence, and admitting the detector anywhere is a
  separate decision.

**Predictions recorded before the run.**

| Detector | Predicted outcome |
|---|---|
| `D0` | fails A1 on every mutant family (green on all of them) |
| `D1` | fails A1 on M3, where skipping the relations it cannot evaluate turns into green |
| `D2` | meets A1-A5 on the pre-lock families. This is weak evidence, since the same author wrote the pre-lock families and the detector. The held-out families are the test that counts. |

The LGGR adapter is fed `D2`'s local relation verdicts (local evaluators) and the outcome
judge (global evaluator). Its `detector_adequacy_certified` flag is reported beside the
measured rates. That shows how far the flag tracks measured adequacy.

## 5. Stage B: the trace prediction study (paid; plan only)

Nothing in this section runs without Jeremy's written approval. The first paid stage was
capped at USD 0.10 (decision D4, 2026-10-15). Jeremy approved this stage at a USD 2 cap
later the same day; amendment 6.2 records that and every change to 5.1-5.4.

### 5.1 Data

- **pilot_003 is pre-lock exploratory data.** It is owned by the "OEWAS, Adversary and
  prompt pilots" thread and was approved and run before this lock. Its replies are
  `{answer, ops[]}` with no intermediate steps, so no trace detector can read them.
  - It may be used to develop the Stage B prompt and parser.
  - It may not be used as confirmatory evidence.
- **The confirmatory dataset** is collected after the Stage B lock:
  - the same 36 exact linear-system items (Adversary `c054_exact_linear_systems`);
  - a prompt that asks for the structured trace schema of section 3;
  - one pinned model id, temperature 0, `max_tokens` 500;
  - raw request and response bytes with SHA-256;
  - a pre-flight guard that refuses dispatch above USD 0.10.

### 5.2 Outcome judge (F3)

- **Primary outcome.** Terminal failure: the final answer fails Adversary `check_answer`
  against the posed system.
- **Secondary outcome.** Oscillation: two calls on the same item give different answers.
  It is measured only if the budget allows the second call (36 extra calls). Otherwise it
  is reported as not run.
- **Not an outcome.** "Replay failure" in the sense of recomputing tool outputs is
  excluded, because that is what `D2` itself computes.
- **Independence rule.** The detector's relation set must not determine the outcome by
  itself.
  - Under the section 3 relations, `D2` green on a schema-conforming trace implies a
    correct answer: the rref relation with the read and answer relations re-derives
    `A x = b`. So `D2` as locked for Stage A cannot be the Stage B predictor.
  - The Stage B predictor is `D2` restricted to local step relations that do not jointly
    re-derive `A x = b`. Example: the read relation alone, plus format and citation
    checks.
  - NGD is computed by composing those local verdicts with a global evaluator that is
    also not the outcome judge.
  - Choosing that restriction is open decision **B1**. It must be settled and locked
    before any confirmatory call.

### 5.3 Predictors and baselines

| Role | Variable |
|---|---|
| Predictor | NGD indicator (`Delta_E = -1`) and non-certifying status from the restricted `D2` |
| Baseline 1 | local step accuracy: share of locally checkable steps that pass |
| Baseline 2 | gate score: strict JSON-schema validity of the reply (uses no answer key) |
| Baseline 3 | trace length in steps and in output tokens |

The matched control is paired by item: every item under every arm, with fresh calls and
no shared context.

### 5.4 Analysis and kill rule (F4)

**Models compared.** Logistic regression of terminal failure on:
- (a) the three baselines;
- (b) the three baselines plus the predictors.

**Statistic.** ΔAUC = AUC(b) − AUC(a), with a 95% item-level bootstrap CI (10,000
resamples, seed recorded at the lock).

**Decision rule:**

| Result | Decision |
|---|---|
| CI upper bound < 0.05 | predictive claim dropped |
| CI lower bound > 0 and point estimate ≥ 0.05 | claim kept as supported at pilot scale |
| anything else | inconclusive; reported as `BudgetUnknown`, not as a refutation |

**Power, stated now.** With 36 to 108 traces and failure prevalence near 30%, the AUC
standard error is about 0.05-0.06. The CI half-width on ΔAUC is then about 0.08-0.1. So a
USD 0.10 run will most likely be inconclusive unless the effect is large. A decisive test
needs roughly 400+ traces, which is outside the current cap.

### 5.5 Open decisions before Stage B

| Id | Decision |
|---|---|
| B1 | **decided 2026-10-15** (section 6.1): local views only; which local relations to keep is still open |
| B2 | **decided** (6.2): `claude-haiku-5-5`, USD 0.10 / 0.50 per million input / output tokens |
| B3 | **decided** (6.2): yes, one second call per item |
| B4 | **decided 2026-10-15** (6.2): approved, cap USD 2 |

## 6. Deviations and amendments

Any change after the lock is recorded here, with its date and commit. A change to a
locked file voids the certificate run that used it. A fresh lock gets a new suffix
(DA-001a, DA-001b, and so on). Earlier results are kept as they are.

### 6.1 Amendment, 2026-10-15: decision B1, local views only

**Decision (Jeremy, 2026-10-15, in the project thread).** The Stage B detector never has a
global view. Each local evaluator sees one step and the steps it cites directly. It does not
see the posed item, the outcome judge, or any count taken across the whole trace.

**What this changes and what it leaves open.**
- `D2` as locked fails the rule in two places. Its given relation compares the trace's copy
  of the system with the posed item, and it refuses a trace with more than one answer step.
- Locality alone does not settle the independence rule of 5.2. One-hop relations still
  compose: rref, read, residual and answer together re-derive `A x = b` for the trace's own
  copy of the system. So the Stage B predictor must be local *and* restricted.
- Two exploratory detectors in `local_detector.py`, written after the held-out families were
  seen, measure this. Their rates are not adequacy certificates.
  - `D3_local_all`: every one-hop relation.
  - `D4_local_restricted`: the read relation only (the B1 candidate).

**Predictions written before the run** (same seed and families as the Stage A run):

| Detector | Predicted |
|---|---|
| `D3` | green on all of H1, whose copied system has drifted from the posed one and which no local view can see; red on H2, where each answer step is now checked on its own; otherwise as `D2` |
| `D4` | green on clean traces; red on M1, M2, H3 and H4; green on M4, H1 and H5, where the misread happens upstream of the read relation or the copy has drifted; M3 split by which citation was deleted |


### 6.2 Amendment, 2026-10-15: the Stage B lock

**Approval (Jeremy, 2026-10-15, in the project thread):** "i approve of the paid plan. Use
anthropic's api key in .env. $2 cap". The key stays on Jeremy's PC, so the calls run there.

**Lock.** `lock_da_001_stage_b.json` pins `stage_b.py`, `stage_b_analysis.py`,
`local_detector.py`, the Stage A locked files and the Adversary checker, plus the SHA-256 of
the prompt. The lock commit is the commit that adds that manifest. `stage_b run` refuses
to dispatch when any pinned file differs from the manifest in the worktree or at the lock
commit. Item and bootstrap seeds are derived from the lock commit
(`sha256("<commit>:PREREG-DA-001:stage-b:<purpose>")`).

**Decisions.**

| Id | Decision |
|---|---|
| B1 | The predictor is `D4_local_restricted`: the read relation only, each step seen with the steps it cites, no posed item. Its two indicators are red and non-certifying. |
| B2 | `claude-haiku-5-5` on the Anthropic Messages API, USD 0.10 / 0.50 per million input / output tokens (prompts under 100K tokens). |
| B3 | Oscillation is measured: each item gets a second, identical call. |
| B4 | Cap USD 2. A run whose worst case exceeds USD 1.90 refuses to start. Each call reserves its worst case (every request byte billed as an input token, plus `max_tokens` output) and is refused if spend plus reservations would cross USD 2. |

**Changes to 5.1-5.4, with reasons.**

- **Items.** 800 items from the section 3 generator (`traces.make_item`, 3x3 and 4x4
  integer systems), not the 36 c054 items. Reason: power needs 400+ traces (5.4), and the
  trace schema and detectors are written for square systems with a unique solution.
  Worst case for 1,600 calls is about USD 1.30.
- **Sampling.** Claude Haiku 5.5 rejects a non-default `temperature`, so none is sent.
  Thinking is disabled (`{"type": "disabled"}`): reasoning the model keeps hidden is outside
  every detector's view, so the visible trace has to carry the work. `max_tokens` is 1,200,
  not 500: a 4x4 trace with fractions can exceed 500 tokens, and a cut reply would count as
  a format failure.
- **Baseline 1** becomes the share of the five step slots that pass format and citation
  checks (ids, kinds, tool and claim names, cites, output keys and shapes, rationals that
  parse). Arithmetic step checks are excluded: rref, read, residual and answer together
  re-derive `A x = b` (6.1), so an arithmetic baseline would be the outcome judge.
- **Baseline 2** is whether the whole reply passes those checks with exactly five steps and
  no other top-level key. The JSON object is read leniently (code fences stripped); whether
  the reply was bare JSON is recorded, not modelled.
- **Baseline 3** is the number of steps and the output token count.
- **NGD is dropped.** It composes local verdicts with a global evaluator, which B1 forbids.
- **`D2` and `D3`** are scored on every trace and reported as cross-tabulations only. Both
  are close to the outcome judge and are not predictors.
- **Outcome.** A reply with no checkable final answer (no JSON, no single answer step, or
  an answer of the wrong length or not rational) is a terminal failure. An HTTP or network
  error is a transport error: excluded from the analysis and counted.
- **Analysis.** Features are standardised; logistic regression by ridge-penalised IRLS
  (ridge 0.01, intercept unpenalised); AUC by Mann-Whitney with ties counted half; ΔAUC
  refitted on each of 10,000 item-level bootstrap resamples, percentile CI. A 10-fold
  out-of-fold ΔAUC is reported beside it as a check on in-sample optimism.
- **Minimum events.** Fewer than 30 failures or 30 successes among the primary traces gives
  `BudgetUnknown:TOO_FEW_EVENTS`, whatever the CI says.
- **Oscillation** (secondary) is the share of items whose two calls give different answers
  or where either call has no checkable answer. It is reported, not modelled.

**Predictions written before the run.**

- Most wrong answers will come from arithmetic slips inside the rref step, followed by a
  faithful read of the wrong last column. `D4` is green on those by design (Stage A: green
  on M4).
- `D4` red will be rare (under 10% of traces) and almost always a failure.
- So ΔAUC will be small. The expected decision is `DROPPED`; `BudgetUnknown:INCONCLUSIVE`
  is the next most likely. `SUPPORTED_AT_PILOT_SCALE` would need misreads to be a large
  share of failures, which Stage A gives no reason to expect.
- Failure prevalence with thinking disabled: 20-60%.

**Offline check before the lock.** The fixture transport (`--fixture`, no network) plants
clean traces, misreads (M1), upstream rref errors (M4) and junk replies. On it `D4` is red
only on failures and green on every M4 trace, and the pipeline runs end to end
(`pfp/tests/test_detector_adequacy_stage_b.py`).

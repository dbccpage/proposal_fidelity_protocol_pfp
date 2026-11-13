---
documentation_contract: symbol-game-documentation/v1
title: "Paper 008: Round trips, certificates and evidence"
kind: educational-companion
status: active
maturity: instructional
claim_status: scoped-exercises
authority_effect: "None"
source_paths:
  - atlas/coda_atlas/pfp/008_pfp_mssn_tower_challenges_and_retraction_benchmarks/paper.md
---

# Study guide and instructor key: Paper 008

**AuthorityEffect:** None. Attempt the [quiz](quiz.md) first. The [manuscript](../paper.md) distinguishes packet syntax, semantics, formal evidence and recorded observations. The [source archive](../docs/source_archive/README.md) provides selected historical bytes without a working-tree fallback.

L0 to L7 organize this lesson. They do not grade an MSS stage, prove a general theorem or authorize use. Give each answer one point for the concrete result and one for its stated limit; use the total only to identify material to revisit.

## Worked answers

### L0: Packets and admission

**Q01.**

| Wire | Parses | MSS-0 active | MSS-1 active |
| --- | --- | --- | --- |
| `<>` | Yes | Yes | Yes |
| `<0>` | Yes | No | Yes |
| `<2>` | Yes | No | No |
| `op<<1><0>>` | Yes | No | Yes |

The raw atom alphabet is ASCII `a-z` and `0-9`. MSS-1 activates only `0` and `1` as **data** glyphs. The application prefix is literally `op<`; its `o` and `p` are syntax, not extra active data atoms. Parsing and admission answer different questions.

**Q02.** The old-image round trip returns Diff. The upward call on `<0>` raises ValueError. The downward call on `<1>` returns NonDescentReceipt with that original parsed packet. It preserves the rejected object rather than converting it to Diff. The historical record-and-prefix toy returns `None`; it is a separate example. Also, `d_1(parse("<2>"))` returns a refusal even though `<2>` is not MSS-1-active: the caller still needs the upper-level admission check.

Replay: `test_008_source_bound_examples.py::test_actual_parser_and_level_admission_are_separate` and `test_actual_old_image_round_trip_and_typed_foreign_refusal`.

### L1: What the round trip proves

**Q03.** If $u(a)=u(b)$, applying $d$ gives $a=b$. This proves injectivity on the illustrative old carrier. It proves no reverse round trip on foreign $x$: $d(x)$ is a refusal, outside the domain of $u$. The actual implemented old carrier is the singleton $\{\mathrm{Diff}\}$, not this two-element illustration.

**Q04.** The term inclusion and its syntactic round trip still hold. Conservativity fails because the extension proves old-language $P$ while the old theory does not. A proof that old-language derivability is reflected back to the old theory, with declared interpretations and rules, is required. Identity on strings is insufficient.

### L2: Namespaces and grades

**Q05.**

| Stage | Base | Complete block |
| ---: | ---: | --- |
| 22 | 128 | 128–135 |
| 23 | 136 | 136–143 |
| 100 | 752 | 752–759 |

Since $b(N+1)=b(N)+8$, $b(N)+7<b(N+1)$. For an eight-bit unsigned wire, $b(N)+7\le255$, so $N\le37$: stage 37 ends at 255 and stage 38 begins at 256. Python integer disjointness and wire capacity are separate statements. Neither establishes stage semantics.

**Q06.** The selected syntax boundary checks passed. The proposed COMPUTED binding fails because its checker accepts the required counterexample. Preserve the syntax evidence and record the unmet checker obligation. The status interface supplies no LEAN or GATED upgrade, and a stage number is not evidence. This question does not prescribe a universal soundness result from successful fixtures.

### L3: Every certificate clause

**Q07.** The primal cost is $|1|+|0|+|0|=1$. For $y=(1,0,0)$, the dual dot product is 1, the gap is 0, and capacity holds. Divergence is $(-1,1,0)$, so balance fails and the complete certificate is invalid. For $y=(1,1,1)$, divergence is $(0,0,0)$, capacity holds and the objective remains 1. A theorem about zero gap proves that clause; it does not erase failed feasibility.

**Q08.** The compatible dictionaries glue to $a=0,b=1,c=0$. The changed pair conflicts at $b$, so no dictionary can restrict to both. This is a finite consistency calculation, not a construction of a general sheaf with an existence-and-uniqueness gluing theorem.

Replay: `test_008_source_bound_examples.py::test_zero_gap_fixture_still_needs_flow_balance`. The deposited Lean FlowCertificate statements express the corresponding finite fixture; Python arithmetic is a separate replay.

### L4: Bind the instance

**Q09.** Tree propagation gives $\pi(A)=0,\pi(B)=2,\pi(C)=5$, which fails the declared third claim 6. The closed walk $A\to B\to C\to A$ has signed sum $2+3-6=-1$. Its indexed steps are `[(0,1),(1,1),(2,-1)]`. Every potential telescopes to zero on a closed walk, so this nonzero sum rules out a potential.

**Q10.** With the third claim 5, the potential $(0,2,5)$ satisfies every edge. The all-zero proposal changes the claim data; it preserves none of the three original nonzero values. A repair policy must bind the original instance, identify which claims may change, check the permitted move, and check the required preserved constraints. Consistency of a replacement instance alone does not supply those checks.

Replay: the runner's `test_json_loaded_walks_remain_checkable` and `test_008_source_bound_examples.py::test_graph_certificates_agree_with_an_independent_bounded_potential_search`. The latter checks all 125 integer triangle assignments with edge values from −2 to 2 against an independent bounded potential search.

### L5: Read the corpus and the statistics

**Q11.** $40+2+8=50$, with each audited challenge in one category. Category A records package contents, not a correctness theorem; Category B names a measurement deliverable, not a completed measurement. A missing receipt leaves execution unestablished. C001 has no retained measurement result. C047 has a test-named print-only script, without assertions or a failing exit status, that does not check mutation files. C048 to C050 have no pytest test file. C051 is outside the audited fifty.

**Q12.** Arm 2's count is $25-6+17=36$. With $n=b+c=23$, the exact two-sided value is

$$
p=\min\left(1,\frac{2\sum_{k=0}^{\min(b,c)}\binom{n}{k}}{2^n}\right)
 =\frac{145499}{4194304}\approx0.03469.
$$

For $b=c=0$, the convention is $p=1$. The hybrid run's 38/50 is separate. The midpoint 37/50 was not observed in either run. The 405B model exceeds the stated 70B limit; the larger run ceiling differs from the protocol's per-arm ceiling. Per-case rows are absent, and these descriptive values are not a general model effect or a multiplicity-adjusted analysis.

Replay: `test_008_source_bound_examples.py::test_exact_mcnemar_arithmetic_keeps_the_two_runs_separate`. It recomputes the four exact values from the transcribed discordant counts; it does not reconstruct the missing paired cases.

### L6: Scoring and custody

**Q13.** An assisted success shows reproduction of supplied values at this fixture's scope. It does not show unaided discovery or estimate population performance from one trace per cell. A new comparison needs answer-free matched prompts, repeated runs under declared sampling conditions, a pre-registered analysis, and retained per-case outputs scored against the same instance. The historical host could accept a zero claim replacement, so preservation must be checked separately.

**Q14.** Both malformed or conflicting responses receive UNKNOWN and count as mismatches; substring occurrence is not a valid verdict. The new version-2 receipt binds the case, exact prompt, raw reply, provider label, measurements, host certificate and declared runner source SHA-256. Different raw replies therefore have different digests. A public hash detects changes relative to a trusted expected digest. Someone can edit a record and recompute its hash; it does not authenticate the provider or prove the certificate true.

Replay: `test_malformed_or_conflicting_verdicts_are_not_scored_as_answers` and `test_receipt_digest_binds_the_raw_reply_prompt_case_and_certificate` in the runner test file.

### L7: Resolve and replay honestly

**Q15.** v1 returns HISTORICAL_BYTES_UNAVAILABLE. A v2 resource with the same filename cannot substitute for that pinned historical blob. Without the optional SHA-256, the extra comparison with the caller's expected digest was not performed. Retrieved bytes still need a valid relationship to the claim, and the checker and assumptions still need review.

**Q16.** Exit 0 with no census is insufficient. The repaired named gate compares the complete expected names and axiom sets and refuses empty, missing, duplicate or extra declarations and changed dependencies. The 39 names are selected theorems from five formal files. The retained 576-declaration report covers the ten local module environments, including ExactRat and generated/private declarations; it does not mean 576 manuscript theorems. The 52 external Level Engine payloads remain a separate surface. A host that cannot start Lean reports a blocked fresh replay and may separately compare source hashes with retained receipts. Mocked gate tests are control-logic evidence, never a compiler pass.

Replay: `code/tests/test_008_deposit_gates.py`.

## Offline practice

Install the development tools declared in [pyproject.toml](../pyproject.toml), then run from the paper root, one file per command:

~~~powershell
py -3.12 -m pytest code/tests/test_008_mssn_tower_retraction.py -q
py -3.12 -m pytest code/tests/test_008_deposit_gates.py -q
py -3.12 -m pytest code/tests/test_008_source_bound_examples.py -q
py -3.12 code/retraction_benchmark_runner.py --mock --condition baseline --output-dir <new-baseline-directory>
py -3.12 code/retraction_benchmark_runner.py --mock --condition hinted --output-dir <new-hinted-directory>
~~~

Predict 3/6 matches for baseline and 6/6 for hinted. Baseline exits 1 because three verdicts miss; that is the expected negative control. These stub results are plumbing checks. No model is queried and no spending or learning benefit is measured. The package runner's scratchpad condition supplies generic instructions; the historical K4 scratchpad prompt supplied answer values. Do not combine their labels into one experiment.

## Common mistakes and the next reading

| Mistake | Revisit |
| --- | --- |
| Parsing means admission | L0; manuscript Section 2 |
| Injective syntax means conservative theory | L1; Section 3 |
| A stage label or fixture family proves universal soundness | L2; Section 4 |
| Zero objective gap makes an infeasible certificate valid | L3; Section 5 |
| A solved replacement instance repairs the requested instance | L4; Sections 10.1 and 10.3 |
| A folder, aggregate label or midpoint is a retained observation | L5; Sections 8 and 9 |
| An answer-bearing prompt measures unassisted ability | L6; Section 10.1 |
| A digest or mocked successful process proves a theorem | L7; Sections 6 and 7 |

For each missed question, write the exact counterexample and the missing obligation. Re-run a changed-input control, then restate only the conclusion supported by that check.

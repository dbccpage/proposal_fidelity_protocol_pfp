---
documentation_contract: symbol-game-documentation/v1
title: "Paper 009: Study claims, controls, and custody"
kind: educational-companion
status: active
maturity: instructional
claim_status: scoped-exercises
authority_effect: "None"
source_paths:
  - atlas/coda_atlas/pfp/009_pfp_adversarial_dialectics_and_terminal_reality_gates/paper.md
---

# Study guide: Paper 009

**AuthorityEffect: None.** The [Apartment 50 preface](00_preface_at_apartment_50.md)
is fictional framing. Attempt the [quiz](quiz.md) before reading the
[instructor key](answer_key.md). No learner study or qualification is reported.

## Route through the paper

| Level | Read | Practice | Move on when you can |
| --- | --- | --- | --- |
| 1 | Section 1 | Reduce a broad claim | Separate assumption, witness, execution, and obligation |
| 2 | Section 3 and notebook | Predict both operations | Explain the invariant and identify changed input |
| 3 | Section 4 | Corrupt controls separately | Distinguish feasibility, closure, objective matching, and digest binding |
| 4 | Section 4.1 and trace | Reconstruct the four cells | Give numerators, denominators, and label provenance |
| 5 | Sections 5–6 and Lean | Read definitions before names | Distinguish formal facts, census scope, and runtime correspondence |
| 6 | Appendix A.1–A.4 | Follow each verdict to its operation | Identify four families and five probes |
| 7 | Appendix A.5 | Inspect corrections | Separate necessary evidence from guarantees about a checker |
| 8 | Sections 6–8 | Write a scoped record | Preserve refusals, missing bridges, and unexecuted dependencies |

## Prepare the exact calculation

Use edges (0,1), (1,2), (2,0). Write all three endpoint differences before
subtracting. Each potential occurs once with each sign around the cycle; the
differences sum to zero. This cancellation explains every potential on the
declared cycle. A graph path is not an automatically filled simplex.

Replacing claims by df changes the input. Subtracting df from fixed claims
preserves their cycle sum. Save original and transformed inputs: a low score
on replacement data does not show the original obstruction disappeared.

Predict the displayed numbers, then run:

```sh
python tools/replay_notebook.py
```

The default executes all five ordinary Python cells in a fresh CPython process,
checks assertions, and compares stored outputs without rewriting the notebook.
Jupyter kernel execution is a separate `--engine jupyter` check. Neither mode
runs the native graph checker or grades a learner's explanation.

## Prepare the historical recount

Read [evidence provenance](../docs/historical_evidence/README.md). “Refused”
and “not refused” mean the original checker's decisions, not physical ground
truth. Separate CHALLENGE and CONCUR, check all cells total ten, and keep a
later checker decision as a distinct observation.

False-positive fraction divides challenges of not-refused proposals by all
not-refused proposals. Precision divides challenged refused proposals by all
challenges. Different denominators answer different questions. Use exact
fractions for the new recount; zero denominators are undefined.

```sh
python tools/review_capstone.py
python -m pytest -q
```

The capstone verifies retained digests and the complete condition census, changes
one verdict in a copy, and ignores the constant caught flag. Tests also reject
non-Boolean labels, unknown verdicts, and label/status disagreement. The gate
record inspection does not execute the gate. Complete the written report too.

## Diagnose a missed answer

| Mistake | Return to | Correction |
| --- | --- | --- |
| A hash or token is treated as proof | Level 1 | State the missing property check |
| Subtraction is confused with replacement | Level 2 | Track original input, operation, residual, and sum |
| Equal LP objectives replace feasibility | Level 3 | Check both feasible regions |
| The caught flag yields perfect detection | Level 4 | Count actual decisions against historical labels |
| A theorem name certifies a runtime | Level 5 | Identify the correspondence obligation |
| Four families are called four records | Level 6 | Count F2a and F2b separately |
| A bound receipt makes a critique true | Level 7 | Separate identity, authentication, and validity |
| A retained report is called a fresh replay | Level 8 | Record the command actually run |

## Write a review record

Include claim text, source revision, artifact path/digest, assumptions, exact
input, command, environment or executable pin, observed result, review
disposition, and remaining obligation. Mark a command `NOT_RUN` until observed.
The manuscript's dispositions are review terms, not a new runtime API.

The [v0.1 review record](../docs/v01_review_2026_10_02.json) separates fresh
execution from earlier reports. Deposit and ZIP checks establish file custody,
not the truth of every answer. A pinned Lean build is a separate dependency check.


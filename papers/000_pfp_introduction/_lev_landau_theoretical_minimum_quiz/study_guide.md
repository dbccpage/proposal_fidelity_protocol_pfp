---
documentation_contract: symbol-game-documentation/v1
title: "Paper 000: Learner guide to marks and checked returns"
kind: educational-companion
status: proposed
maturity: instructional
claim_status: scoped-exercises
authority_effect: "None"
---

# Learner guide to marks and checked returns

**Paper 000, version 0.1.0. AuthorityEffect: None.**

The first game asks you to keep a question, a proposed answer, and its check
distinct. This guide gives you a route through the [paper](../paper.md) and
[workbook](../jupyter_notebooks/000_from_marks_to_returned_packets.ipynb), then
prepares you for the [Landau examination](quiz.md). Worked examination answers
are in the separate [instructor key](instructor_key.md). The
[Apartment 50 preface](00_preface_at_apartment_50.md) is optional fiction.

## A route through the paper

| Read and run | Learn to do | Quiz questions |
| --- | --- | --- |
| Sections 1-5; workbook lessons 1 and 4 | Count admitted marks; distinguish S(n), MSS-N, and execution; declare a board | 1-5 |
| Sections 6-8; workbook lessons 2-4 | Supply an observation witness; state a notation's reading; distinguish types from values | 6-10 |
| Sections 7-10; workbook lessons 5-7 | Rename consistently; bind the exact question; replay; stop honestly | 11-15 |
| Example 8 and Section 9; workbook lessons 6-8 | Preserve a way back; distinguish repair from extension; audit an actual return | 16-20 |
| The additional definitions in Questions 21-24 | Enumerate minima; certify a cycle optimum; declare cells; audit a consumer | Optional capstones |

For each workbook cell, write down your prediction first. Run it, change one
input, and explain any discrepancy. Keep the old input and result. A changed
question should remain visibly different from a repaired answer.

## The vocabulary you need

| Term | Meaning in this introduction | A common mistake |
| --- | --- | --- |
| Presentation | A supplied display or representation | Counting every printed character as an admitted mark |
| Carrier | The admitted marks on the declared board | Smuggling a new endpoint into an answer |
| Observation | A supplied value for each mark under a declared test | Treating different names as an observation witness |
| Goal | The finite property requested on this instance | Reversing the goal to make a failed answer pass |
| Candidate | A proposed answer, bound to a particular problem | Treating persuasive prose as a checked answer |
| Receipt | The scoped result of a declared checker | Extending CHECKED to claims outside its predicate |
| Return packet | Retained problem, candidate, and receipt | Trusting a detached status word |
| Renaming | A bijection applied consistently to structure | Collapsing different marks or changing only the answer |
| Replay | Recomputing the retained check | Assuming replay authenticates the producer |
| Extension | A declared change with new preservation obligations | Claiming an atlas successor from a local check |

S(n) is a Genesis derivation stage; MSS-N is an external atlas specification;
a session event is an execution record. They have different roles. The paper's
stage table is orientation, not a new derivation or a license to advance Genesis.

## What the checker does

For the basic relation exercise, think of the referee as following this finite
procedure: check the field set and schema; validate the carrier and label;
validate the goal and candidate shapes; check membership; reject self-pairs;
compare labels; compare directed endpoints with the goal. A failed check returns
its first reason. Later checks may not have run.

For the richer lesson packet, the declared task, input type, and answer type
select the teaching predicate. English prompt text is retained data. The
candidate includes the exact problem identity. Editing the text can change
that identity even when the finite predicate remains the same.

The current v0.1.0 profile checker has a small precedence discrepancy: on a
table with no separator it reports BLOCKED before checking whether the answer
value is an integer. Question 19 asks you to find and repair this. Observe the
shipped behavior first. The proposed code patch makes malformed index values
REFUSED before the missing-separator check.

| Outcome | What it says | A useful next action |
| --- | --- | --- |
| CHECKED | This value passed the declared finite predicate | Consume the checked value within scope; preserve the problem binding |
| REFUSED | This envelope or candidate failed a declared check | Inspect the reason; repair the answer or correct an invalid declaration |
| BLOCKED | The exercise lacks a required declared separator | Supply new input under a new problem; retain the old record |
| UNKNOWN | The bounded session obtained no checked answer | Retain attempts and describe the stopping condition |

UNKNOWN covers both exhausted fuel and a proposer that ends without a passing
answer. The current controller records attempts but has no separate stop-reason
field. Do not claim the budget was exhausted if fewer attempts occurred.

## A short worked prediction

On carrier p,q with goal p to q and label `separates`, the candidate
`["q", "separates", "p"]` is a well-shaped irreflexive triple. It still misses
the directed goal. The defect is not its syntax or a self-loop; it is the
specific requested direction. This distinction makes the refusal useful.

Similarly, a two-column observation row `["red", "red"]` supplies no separator.
The claim concerns that supplied row. It does not exclude every observation
you could later declare. A different spelling for q changes neither value.

## Read notation in its declared register

`<>` is one opaque presentation in the ground exercise and admits no mark.
The paper separately supplies an atlas-style reading in which `<ab>` depicts
a directed pairing. Record that convention before using it. An obstruction
display is not itself an independently verified obstruction certificate.

Bracket displays such as `<edge<p><q>>` and graph arrows such as p to q are
different representations. The restricted bracket alphabet does not prohibit
the JSON used in the paper. Balanced brackets alone do not define an AST,
the semantics of `edge`, or an executable checker. This board's irreflexive
relation rule also does not forbid the reflexive equality p=p.

## Keep identity, replay, and trust separate

The teaching identity uses sorted dictionary keys and compact JSON. Key order
does not matter under that profile; list order does. It is not an RFC 8785
canonicalization claim. The digest is not a signature.

Replay can catch a receipt changed without the corresponding input and check.
It can also accept a whole self-consistent return for an unintended question.
A consumer therefore needs an expected problem identity retained independently
of the returned packet. It still trusts the selected checker and needs separate
evidence if producer authentication matters.

## Hints for the examination

Try without these first. A hint points to an operation, not a verdict.

| Questions | Hint |
| --- | --- |
| 1-3 | Name what each count or index refers to; distinguish external supply from admission |
| 4-5 | Follow the actual validation order rather than listing every possible defect |
| 6-7 | Compare values within each observation row; inspect exact Python types |
| 8-10 | Separate typography, answer metadata, value shape, and the selected predicate |
| 11-12 | Structural correspondence and exact-content identity answer different questions |
| 13-14 | Keep the caller's expected question outside the untrusted return |
| 15 | Count calls to `next`, not merely values already written in a list |
| 16-17 | Check old-image terms first; track which edits change the prompt |
| 18-19 | One counterexample suffices to refute a universal claim; actual code outranks your prediction |
| 20 | Choose a predicate another person can check completely |
| 21 | Write each mark's selected-row signature; retain ties rather than the first success |
| 22 | Sum differences around the cycle; then place residual on a least-weight edge |
| 23 | List omitted vertices and cancel oriented edge terms explicitly |
| 24 | A return can be internally consistent and answer the wrong question |

## Additional mathematics for the capstones

In Question 21, two marks are distinguished exactly when their selected
observation signatures differ. There are 2^k binary signatures of length k.
This is a finite capacity bound under the declared binary model, not a theorem
about native Genesis growth.

For Question 22, each oriented edge uv has difference f(v)-f(u). Residual is
the report minus that difference. Weighted absolute residuals give the cost.
If a circulation lambda has zero divergence, then lambda dot df=0: each vertex
potential has equal incoming and outgoing coefficients. With
|lambda_e| <= w_e, termwise domination gives

\[
\lambda\cdot c=\lambda\cdot(c-df)\leq\sum_e w_e|c_e-(df)_e|.
\]

A candidate cost matching this lower bound proves an optimum for that instance.
No numerical optimizer or unpriced approximation is needed for the cycle.

Question 23 explicitly supplies the ordered simplex and horn conventions.
The standard definition of a horn is given in
[Kerodon, Subsection 1.2.4](https://kerodon.net/tag/000K). A drawing of a graph
does not admit higher cells; you must declare which faces exist and which
target simplex you mean. Do not infer physics from a classroom chain calculation.

## Run the local examples

From the extracted paper directory, with Python 3.12 or later and the companion
dependency configuration corrected as described in the review:

```sh
python -m pip install ".[dev]"
python code/basic_packets.py
python code/lesson_packets.py
python -m pytest code/tests -q
python verify_deposit.py
```

On Windows, `py -3.12` may replace `python`. The two teaching scripts use only
the standard library. Tests need pytest. Notebook execution needs nbformat,
nbclient, and ipykernel; a notebook interface must also be available if you want
to use a browser UI. `verify_deposit.py` checks the manifest unless explicit
test flags are supplied. It does not prove all manuscript claims.

The supplied release archive check requires the original ZIP to be present
inside the extracted paper folder. It is an optional maintainer check, not
part of running the teaching examples.

After the core examination, continue to Paper 001 for stronger exact graph
certificates and Paper 005 for session management. These are routes to further
work, not material assumed by the core questions.

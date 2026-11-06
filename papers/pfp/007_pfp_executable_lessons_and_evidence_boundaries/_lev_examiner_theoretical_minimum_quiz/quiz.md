---
documentation_contract: symbol-game-documentation/v1
title: "Paper 007: Prediction, execution, and learning evidence"
kind: educational-companion
status: active
maturity: instructional
claim_status: scoped-exercises
authority_effect: "None"
source_paths:
  - atlas/coda_atlas/pfp/007_pfp_executable_lessons_and_evidence_boundaries/paper.md
---

# Theoretical minimum: Paper 007

**AuthorityEffect:** None. The [Apartment 50 preface](00_preface_at_apartment_50.md) is fictional staging. Study the [guide](study_guide.md), attempt these problems before opening the [instructor key](instructor_key.md), and retain your first answer separately from any correction.

Use exact rational arithmetic. Unless a problem changes it, the carrier has vertices $a,b,c$, ordered directed edges $ab,bc,ca$, no filled face, claims $h=(1/3,1/3,1/3)$, and potential $f=(0,1/3,2/3)$. Define
$$
(df)_{st}=f_t-f_s,\qquad r=h-df,\qquad C(x)=x_{ab}+x_{bc}+x_{ca}.
$$
A potential adjustment changes the representative $r$; replacing $h$ changes the claims. A supplied execution-status string is data, not an execution.

There are eight instructional levels, three problems per level, four points per problem: 96 points total. The levels order prerequisites; they are not measured learner abilities or age categories. For every answer give the result, a reason, and its scope. No speed requirement is imposed.

## Level 0: Declare the lesson

1. **Carrier and convention.** List the vertices, ordered edges, coefficient system, and difference convention. Does drawing the triangle also declare a filled 2-cell? Identify one operation that changes the carrier rather than only the potential.
2. **Exact input.** Compare `Fraction(1, 3)`, `Fraction("1/3")`, and `Fraction(1/3)`. Which two specify the intended rational input directly? Why is an exact fraction made from a float not automatically the intended rational?
3. **Five components.** Outline a lesson containing a declared finite example, worked calculation, learner prediction, changed-input probe, and evidence boundary. Where must the first prediction be recorded? What does a stored notebook answer fail to record?

## Level 1: Compute before running

4. **Worked triangle.** Compute all coordinates of $df$ and $r$, then $C(h)$, $C(df)$, and $C(r)$. State whether all three claims are potential differences.
5. **Constant shift.** Add $7/5$ to each height. Compute the three shifted heights and predict the new $df$ and $r$ without running a cell. Explain the cancellation.
6. **Changed claims.** Replace $h$ by $-h$, keeping $f$ fixed. Compute the residual and its signed cycle sum. Is this residual equal to $-r$? Explain which quantity was changed.

## Level 2: Separate an invariant from a repair

7. **General cycle.** For a directed closed walk $v_0,\ldots,v_m=v_0$, prove that $\sum_{i=0}^{m-1}(f_{v_{i+1}}-f_{v_i})=0$. Deduce the residual-sum identity for arbitrary rational edge claims on that walk. Does testing three potentials prove the identity for every potential?
8. **Completion.** Keep the first two claims at $1/3$ and choose the third to make the cycle sum zero. Give a potential realizing all three completed claims. Is choosing the missing claim the same operation as adjusting a potential on the original claims?
9. **Path versus cycle.** On the path $a\to b\to c$ with claims $(1,2)$, use $f=(0,1,3)$. Add a closing $c\to a$ claim of 1. Compute the closed-cycle residual and sum. Which closing claim would instead make the table exact? Explain why drawing a filled face does not silently zero the original discrepancy.

## Level 3: Try to fool the checker

10. **Wrong-sign mutant.** A faulty implementation uses $\widetilde{df}_{st}=f_s-f_t$. Compute $\widetilde{df}$ and $h-\widetilde{df}$. Does checking only $C(\widetilde{df})=0$ and $C(h-\widetilde{df})=1$ detect it? Give a predicted-coordinate check that does.
11. **Matching LP objectives.** In the toy linear program minimize the nonnegative variable $x$ subject to $x\ge1$, with dual maximize $y$ subject to $0\le y\le1$, a checker receives $x=0,y=0$. Both computed objectives equal zero. Explain why this is not an optimality certificate, and give the missing feasibility checks and a valid optimal pair.
12. **Status-string grade.** The legacy function counts code cells whose source contains the substring `assert` and treats supplied status `"ok"` as a pass. Evaluate it on:
    - `# assert example` with status `"ok"`;
    - `print("assert")` with status `"ok"`;
    - `assert False` with status `"error"`.
    Give the reported fraction and explain two reasons it is not a measure of learning or fresh execution.

## Level 4: Reproduce the right bytes

13. **Stored outputs versus execution.** A test reads notebook JSON and finds six code cells, execution counts 1 to 6, and the expected output strings. Has it executed the notebook? Describe a fresh replay that compares outputs without overwriting the deposit, and one claim even a successful replay does not support.
14. **Historical source move.** A cited file at commit A is missing locally, while a file with the same name exists at current commit B with different bytes. State a permissible replay strategy, an impermissible substitution, and the information to record if A's bytes cannot be obtained.
15. **Historical 20/20.** The route receipt reports 20 passes dated 2026-09-25; its manifest paths refer to the former notebook tree, and one lesson calls a retired norm API. What can the saved receipt support? What must be maintained and rerun before asserting a fresh full-route pass? Does passing the standalone fraction notebook resolve those route blockers?

## Level 5: Read the formal statement

16. **List bound.** The Lean bound assumes $n\in\mathbb N$, an integer list $h$, `h.length ≤ n`, and $|x|\le n-1$ for every entry; subtraction in `Nat` is truncated at zero. Compute the list mass and ceiling for $n=3,h=(2,-2,1)$. Show a permitted list that saturates the ceiling. State the consequence at $n=0$ and $n=1$.
17. **Missing hypotheses.** For $n=3$, give one list violating the per-entry cap and another violating only the length bound, each with mass greater than $n(n-1)$. Explain why neither refutes the conditional theorem and why it cannot be read as a human cognitive limit.
18. **Declaration census.** A saved named report lists 21 declarations; the saved full package-local report lists 64, including generated/private names. Which count answers each scope? Does a whitelist containing `Classical.choice` show that it was used? Does a saved report establish a fresh kernel run on this host? Explain what unary nesting preservation does and does not bound.

## Level 6: Assess a person

19. **Threshold fixture.** The legacy test accepts supplied pass rate $92/100$, transfer index $88/100$, and efficiency $85/100$ under chosen thresholds $9/10,4/5,4/5$. Calculate which comparisons pass. What participant evidence and definitions are absent? What would be wrong with calling the result a measured 90% learner pass rate?
20. **Transfer comparison.** Propose a comparison of full worked examples with progressively incomplete examples. Specify baseline assessment, assignment/comparison conditions, independently scored novel tasks, and a delayed assessment. Identify one way that answer-key exposure can contaminate the comparison.
21. **First-response record.** Design a minimal learner record distinguishing first prediction, explanation, output exposure, correction, and later transfer response. How should a missing delayed response be represented? Why should a correction after seeing the answer not replace the first score?

## Level 7: Defend the publication's claim

22. **Lesson redesign.** A notebook sets `expected = 1`, assigns `measured = expected`, and asserts equality under the title “all students transfer cycle reasoning.” Replace it with a five-component triangle lesson, including an independently derived reference and a control that can detect a specific error. Write its strongest justified evidence sentence.
23. **Receipt audit.** A release verifier reports that file hashes and the two-way file census match. A fraction notebook replay passes. Lean is unavailable. Write a publication-ready verification paragraph distinguishing these outcomes from historical Lean evidence, repository integration, and learner findings.
24. **New four-cycle.** Use ordered edges $pq,qr,rs,sp$, claims $(1/2,-1/3,3/4,1/6)$, and heights $(0,1/2,1/6,11/12)$. Compute $df$, the residual, and its cycle sum. Choose a replacement closing claim that makes the table exact. State what an independently scored prediction on this unfamiliar carrier would contribute to a proposed transfer assessment, and what one such response cannot establish.

## Scoring and remediation

The [key](instructor_key.md) gives four explicit points for each problem. Total and level scores locate work to revisit; this rubric is a proposed teaching aid, not a validated certification standard. Treat a wrong coefficient system, silent change of carrier or claims, unrecorded first response, or promotion of a replay into learner evidence as an error in that problem's scope point. Do not erase a correct calculation elsewhere.

Use the guide to repair the corresponding skill, then try a changed instance and retain both attempts. No grade grants authority to publish a learning-effect claim.

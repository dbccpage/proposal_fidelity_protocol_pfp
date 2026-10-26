# Supplement: what the finite C4 certificate establishes

AuthorityEffect: None. Source revision: `000ee9b0c234eda74340e424d6cfb3f6ec001df7`; rechecked 2026-10-22 at `305b9690f97fc3f5c13e361cfe752a6d5dc7ad8d`. `c4_public_input.json` is unchanged since `c419cc6beb`, and every number below was recomputed again with exact integers. Between `c419cc6beb` and this pin, `c4_work_unit.json` changed only the sha256 of `cochain.rs`. This supplements the **00–09** mathematical spine; its filename does not add a public runtime stage.

**Objectives:** construct and check one residual; justify its optimum with a feasible dual; explain which claims remain unpaid. Prerequisites are signed arithmetic and ordered lists. Suggested teaching time is 20–30 minutes, not an observed learner completion time. For the complete JSON answer and workflow, use the [certificate lesson](../levels/level_finite_qm_certificate_walkthrough.md) and [workflow walkthrough](../docs/23_finite_qm_workflow_walkthrough.md).

## Predict before calculating

Draw vertices 0, 1, 2 and 3. Draw arrows **0 to 1**, **1 to 2**, **2 to 3**, and **0 to 3**. Keep that edge order. The [public input](../../../../omega_engine_pfp/fixtures/finite_qm_workflow/c4_public_input.json) supplies rational observations `c=(2,-3,5,7)` and one declared face. The picture represents supplied data; it is not derived from bare inscription. *(Definition.)*

```text
0 --2--> 1 ---(-3)---> 2 --5--> 3
 \__________________7_________/
              arrow: 0 to 3
```

Text alternative: the three-edge path from 0 to 3 has total `2-3+5=4`; the direct edge from 0 to 3 has value 7. The fourth edge is not a return arrow from 3 to 0. Traversing it backward around the face contributes **minus** its value.

**Probe:** Can all four observations be differences of vertex heights? Predict, then explain using the two paths. If you answered yes because each individual edge is possible, compare the two totals for the same endpoints. Their discrepancy is 3.

## Worked example: upper bound and lower bound

A potential is a list `a=(a0,a1,a2,a3)` on vertices. Its edge differences are `d0*a=(a1-a0,a2-a1,a3-a2,a3-a0)`. Fix `a0=0`, then match the first three edges:

```text
a=(0,2,-1,4)
d0*a=(2,-3,5,4)
r=c-d0*a=(0,0,0,3)
norm1(r)=3
```

The norm `norm1` adds absolute values. This candidate attains cost 3, an **upper** bound on the minimum over all potentials. To prove optimality, we also need a lower bound. Use the edge weights `w=(-1,-1,-1,1)`, called a dual witness. *(Derivation.)*

```text
vertex conservation, d0^T*w:
(-w01-w03, w01-w12, w12-w23, w23+w03)=(0,0,0,0)
max(abs(w))=1
dot(w,c)=-2+3-5+7=3
```

For any potential `b`, conservation cancels `dot(w,d0*b)`. Each coordinate of `w` has magnitude at most one, so `dot(w,x)<=norm1(x)` for any edge list `x`. Thus every potential leaves cost at least 3:

```text
3=dot(w,c)=dot(w,c-d0*b)<=norm1(c-d0*b)
```

Our potential reaches that lower bound. Therefore `phi1=3` for this supplied problem. Two equal printed numbers would not suffice without the conservation and coordinate-bound checks. *(Derivation.)*

**Micro-check:** Replace only the fourth coordinate of `w` by zero. Is the new vector feasible? No: its vertex contributions are `(1,0,0,-1)`. The coordinate bound passes, but conservation fails.

## Face signs and the limit of repair

The declared face has signed boundary `01+12+23-03`, so `d1=(1,1,1,-1)`. It gives:

```text
d1*d0=0
d1*c=2-3+5-7=-3
gamma2=norm1(d1*c)=3
d1*r=-3
```

Subtracting an exact difference changes the representative from `c` to `r`. It preserves the quotient class because `c-r=d0*a`. It also preserves the face value because `d1*d0=0`. In particular, it cannot turn this problem's positive optimum into zero. Here `phi1=gamma2=3`; equality in this example is not a theorem equating the diagnostics on every complex. *(Derivation.)*

If the same graph had **no declared face**, its `C2` would be zero and `d1` would have no face rows. Its quotient optimum could still be 3 while its face diagnostic would be zero. This changes the carrier specification; it is a comparison problem, not an edit to this fixture. See [Chapter 02](02_math_cochain_complexes_repairs_and_quotients.md) on graphs versus declared faces.

## Faded exercise, then independent transfer

1. **Faded:** Keep the input fixed and add 10 to every coordinate of `a`. Fill in `d0*a'=(__,__,__,__)`, `r'=(__,__,__,__)` and the optimum. Explain why this is an allowed change of potential.
2. **Independent:** Reverse only the fourth edge's orientation as a change of coordinates. Give the transformed fourth row of `d0`, fourth observation, fourth dual coordinate and face coefficient. Recompute both objective values.
3. **Boundary test:** A proposer says, "I reduced the residual to zero by changing the direct observation to 4." Identify the changed object. Does it answer the original task?
4. **Scope:** Explain why one valid rational certificate supplies neither a Born rule nor an observed improvement in an LLM.

**Feedback:** In question 1 the differences remain `(2,-3,5,4)`, residual `(0,0,0,3)` and optimum 3. In question 2 the fourth row becomes `(1,0,0,-1)`, observation `-7`, dual `-1` and face coefficient `+1`. The fourth residual is `-3`; both norms and the dual pairing remain 3. Reversing the arrow without all corresponding sign changes is the common error. In question 3 the observation changed, so it is a different problem. In question 4 neither a physical bridge nor a controlled model comparison was supplied.

**Pass criterion:** show conservation, capacity and matching bounds; preserve signs under the coordinate change; distinguish the problem from its representation. If conservation fails, return to the four vertex equations before continuing. Teachers should request the learner's explanation before exposing the feedback.

## Listen, then watch

The worked numbers above are the reading. This block is the recording plan, tightened on 2026-10-22. It was not rendered. Pause at each check. Keep every equation in a companion transcript. Do not encode pass or fail by color alone.

**Plain opening.** Two routes from corner 0 to corner 3 disagree. The path adds to 4. The direct edge says 7. The leftover is 3, and 3 is optimal for this supplied list.

**Terms at first use.** Say "d zero" for the height-to-edge map, "d one" for the face map, "phi one" for the smallest edge leftover, and "gamma two" for the absolute face value. "The dual balances at every vertex" is the spoken form of `d0` transpose times `w` equals 0.

**One number before the general bound.** Heights 0, 2, minus 1, 4 leave residual 0, 0, 0, 3. The norm is 3. The general bound, that every height list costs at least the dual pairing, comes only after this 3 is on the board.

**A check you can fail.** Change only the last dual weight from plus 1 to 0. The coordinate bound still holds. Conservation does not: the vertex contributions become 1, 0, 0, minus 1. A matching objective, if someone prints one, is not a certificate.

**Spoken segment.** Duration: 35 seconds. One idea: the path is 4 and the direct edge is 7, so the disagreement is 3. This is the line to record first. The beats below are the longer cut.

> Three steps from corner zero to corner three: two, minus three, plus five. That adds to four. The direct arrow points the same way and asks for seven. Seven minus four is three. Say three, then stop. Ask whether heights can meet both routes. They cannot.

**Check with no screen.** What is two, minus three, plus five? If you said seven, you spoke the direct edge. The path is four. The disagreement is three.

**Video beats.** On-screen words are short. Narration matches the prose in the worked example.

| Time | On screen | Narration |
| --- | --- | --- |
| 0:00–0:20 | path = 4, direct = 7 | "Three steps from zero to three add to four. The direct arrow asks for seven. Can heights satisfy both? Pause." |
| 0:20–0:45 | heights 0, 2, −1, 4 | "Those heights explain the first three edges. On the direct edge they predict four. Seven minus four leaves three." |
| 0:45–1:15 | weights −1, −1, −1, +1 | "The weights are minus one, minus one, minus one, plus one. They balance. None exceeds one. The pairing is three." |
| 1:15–1:35 | cost at least 3 | "Every height list costs at least three. Ours costs three. Three is optimal. The leftover stays." |
| 1:35–1:55 | face = −3 | "Around the face: two, minus three, plus five, minus seven, is minus three. Its absolute value is three." |
| 1:55–2:15 | not physics | "Reverse the direct arrow and update every sign. This is rational arithmetic. The physical bridge stays open." |

Pronunciation guide: `d0` is "d zero"; `d1` is "d one"; `phi1` is "phi one"; `gamma2` is "gamma two". Use words before symbols. Allow extra pause time rather than forcing the two-minute cut.

## Evidence ceiling and sources

The six research stages **P0–P5** are distinct from the eleven public runtime stages and 101 numbered curriculum specifications. This supplement is outside those counts. The workflow assets prepare a research turn; a preparation receipt is not a mathematical acceptance.

This note gives a finite derivation. The review's displayed arithmetic agrees with the [worked certificate](../levels/level_finite_qm_certificate_walkthrough.md); native judging, provider dispatch, notebook replay, audio playback and learner testing were not performed here. A host check, if later run, establishes only its implemented predicates on the bound task. *(Scope.)*

Sources: [public matrices and data](../../../../omega_engine_pfp/fixtures/finite_qm_workflow/c4_public_input.json), [work unit and unpaid quantum imports](../../../../omega_engine_pfp/fixtures/finite_qm_workflow/c4_work_unit.json), [native judge adapter](../../../../omega_engine_pfp/infrastructure/finite_qm_cochain_judge.py), [Chapter 03 duality](03_math_obstruction_mass_duality_and_exact_lp.md), and [rewrite distinctions](../rewriting/finite_qm_residual_repair.md).

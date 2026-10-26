---
documentation_contract: symbol-game-documentation/v1
title: "Paper 007: Prediction, execution, and learning evidence"
kind: educational-companion
status: active
maturity: instructional
claim_status: scoped-exercises
authority_effect: "None"
source_paths:
  - omega_engine_atlas/coda_atlas/omega_engine_pfp/007_pfp_executable_lessons_and_evidence_boundaries/paper.md
---

# Instructor key: Paper 007

**AuthorityEffect:** None. This proposed rubric accompanies the [quiz](quiz.md) and [study guide](study_guide.md). It is not a validated certification standard. Give one point for each numbered scoring item below: four per problem, 96 total. Accept equivalent correct constructions and clearly declared conventions. Record missing or unsupported steps without treating a completed correction as the first response.

## Level 0

**1.** (1) Vertices $a,b,c$ and ordered edges $ab,bc,ca$. (2) Coefficients are rational; claims and heights have separate roles. (3) $df_{st}=f_t-f_s$. (4) No filled face follows from the drawing; adding an edge or face changes the carrier.

**2.** (1) `Fraction(1,3)` specifies $1/3$. (2) `Fraction("1/3")` specifies the same rational. (3) `Fraction(1/3)` first converts the result of floating-point division. (4) It represents that float exactly, not automatically the intended rational $1/3$; use an integer numerator/denominator or exact string for this example.

**3.** (1) Declare the carrier and show a worked calculation. (2) Ask for a prediction with a reason before output exposure. (3) Change one input and compare with an independently derived reference. (4) Retain the first response and state the evidence boundary; stored reference answers do not record learner predictions.

## Level 1

**4.** (1) $df=(1/3,1/3,-2/3)$. (2) $r=(0,0,1)$. (3) Sums are $1,0,1$, respectively. (4) The original claims cannot all equal potential differences on the cycle; the nonzero sum is the obstruction under this convention.

**5.** (1) Shifted heights $7/5,26/15,31/15$. (2) Differences unchanged. (3) Residual unchanged. (4) The same shift is subtracted at each edge's endpoints: $k-k=0$.

**6.** (1) Residual $(-2/3,-2/3,1/3)$. (2) Sum $-1$. (3) It differs from $-r=(0,0,-1)$. (4) Claims changed sign while the potential did not; generally $-h-df\ne-h+df$.

## Level 2

**7.** (1) Expand the endpoint-difference sum. (2) Cancel successive height occurrences and use $v_m=v_0$. (3) Subtract zero to obtain $C(h-df)=C(h)$ under the stated rational definitions. (4) A finite list of tested potentials illustrates, rather than proves, the general identity.

**8.** (1) Third claim $-2/3$. (2) Completed claims sum to zero. (3) $f=(0,1/3,2/3)$ realizes them, so the completed residual is zero. (4) Choosing/replacing a claim changes $h$, whereas a potential adjustment on the original $h$ preserves its nonzero sum.

**9.** (1) The path has zero residual with $f=(0,1,3)$. (2) Adding closing claim 1 gives difference $-3$ and residual $(0,0,4)$, sum 4. (3) Closing claim $-3$ makes the table exact. (4) A face is a separate carrier declaration and cannot silently alter the reports or the potential-difference identity.

## Level 3

**10.** (1) $\widetilde{df}=(-1/3,-1/3,2/3)$. (2) Wrong residual $(2/3,2/3,-1/3)$. (3) Both stated sum checks pass. (4) Compare predicted differences with $(1/3,1/3,-2/3)$, or compare the residual with $(0,0,1)$; this detects the specific sign fault.

**11.** (1) Computed objectives for $x=y=0$ are both zero. (2) $x=0$ violates $x\ge1$. (3) Check primal $x\ge1$, dual $0\le y\le1$, and objective values from the supplied witnesses before using equality. (4) $x=y=1$ is feasible on both sides and has equal objective 1; this declared LP has optimum 1.

**12.** (1) All three sources contain the substring `assert`. (2) Two supplied statuses are `"ok"`, so the reported grade is $2/3$. (3) Comments and strings are counted although neither is an assertion. (4) The function trusts supplied fields, executes no code, and observes no learner response. Either of these last two distinctions must be explained, not merely named.

## Level 4

**13.** (1) Reading JSON does not execute the notebook. (2) Execute all ordinary Python cells in order in a fresh CPython process, or start an explicitly selected Jupyter kernel; identify which backend actually ran. (3) Compare code-cell counts and normalized output data with the deposited reference without overwriting it; retain commands, versions, hashes, and failures; CPython counters do not demonstrate Jupyter kernel history. (4) A match does not establish learner mastery, a full route pass, or a theorem beyond the stated computation.

**14.** (1) Obtain commit A's source bytes and verify their identity. (2) A current-B replay may be useful only as a separately labeled check of B. (3) Never silently substitute B as evidence for A. (4) If A is unavailable, record revision/path, expected identity, attempted command and unavailable dependency, with historical replay unavailable/not run; do not call it a successful historical replay.

**15.** (1) The receipt supports its recorded dated run and exact scope, subject to its provenance. (2) Reconcile current route/manifest/source paths. (3) Replace retired APIs with maintained operations and generate a new source-bound route receipt. (4) The fraction-only notebook exercises a different standalone path and cannot clear the external route blockers.

## Level 5

**16.** (1) Mass $2+2+1=5$, ceiling 6, with both hypotheses satisfied. (2) $(2,-2,2)$ has mass 6 and saturates the bound. (3) At $n=0$, length at most zero forces the empty list and mass zero. (4) At $n=1$, the entry cap is zero, so every permitted entry is zero and the mass is zero.

**17.** (1) For example $(7)$ has length one but violates the cap and has mass 7. (2) $(2,2,2,2)$ respects the cap but violates length, with mass 8. (3) The implication does not apply when a hypothesis is false. (4) No measured mapping from human cognition to these integer-list conditions is supplied.

**18.** (1) Twenty-one counts named selected declarations; 64 counts all declarations defined in the three package-local modules, including generated/private names. (2) Imported Lean library declarations remain outside that census, and whitelist membership is not usage; recorded rows list no `Classical.choice` dependency. (3) Saved output does not establish a fresh kernel replay on this host; bind a successful run to the actual formal bytes. (4) Allowed unary nesting preserves supplied declaration predicates at any finite depth and supplies no maximum depth or student search-time bound.

## Level 6

**19.** (1) $92/100\ge9/10$. (2) $88/100\ge4/5$ and $85/100\ge4/5$. (3) Values and thresholds are supplied fixtures; no operational definitions, participants, task responses, or sampling are supplied. (4) The test verifies comparison logic, not a measured learner pass rate or validation of these thresholds.

**20.** (1) Obtain a predefined baseline measure of relevant skill. (2) Assign comparable conditions, preferably using a stated randomized procedure, while controlling task/feedback exposure. (3) Independently score prespecified novel and delayed tasks using retained responses and denominators. (4) Disclose missingness and exclusions; seeing transfer answers in advance or scoring corrected answers as first answers contaminates the intended comparison. Equivalent defensible study designs may earn the condition point.

**21.** (1) Record task/version/participant and first prediction plus explanation before output exposure. (2) Record feedback/exposure order and retain the correction separately. (3) Record a novel/delayed response and score, or explicit missingness with reason if known. (4) Replacing a first response with a prompted correction changes what is measured and conceals exposure; a missing response needs the prespecified handling, not an invented score.

## Level 7

**22.** (1) Declare exact triangle inputs and independently derive the reference coordinates by endpoint subtraction. (2) Elicit and retain a prediction before showing results; then change a height or claim. (3) Include a known wrong-sign implementation and require a coordinate check to discriminate it, rather than self-comparison. (4) State that the run checks this example/probe and deliberate fault, with no learner-transfer claim. An algebraic derivation can additionally support the stated telescoping identity.

**23.** (1) Describe file hashes/census as identity and packaging checks. (2) Describe notebook success as fresh replay of declared cells in a recorded kernel. (3) State that Lean was not rerun locally and identify saved source-bound formal evidence as historical. (4) Explicitly leave full repository integration, full route execution, and learner effects unmeasured/not run as appropriate. Never turn an unavailable tool into a pass.

**24.** (1) $df=(1/2,-1/3,3/4,-11/12)$. (2) Residual $(0,0,0,13/12)$, sum $13/12$. (3) Replacing closing claim $1/6$ by $-11/12$ makes the claims equal the displayed differences. (4) A first independently scored unfamiliar-carrier prediction is one proposed transfer observation under declared exposure conditions; one response does not estimate a population effect, validate this rubric, or establish delayed transfer.

## Suggested use of scores

Report both the total and eight level subtotals (12 points each). Use missed items to assign arithmetic reconstruction, a new control, a source audit, a theorem-hypothesis reading, or a learner-record revision. Any readiness cutoff is an instructor's choice and must be labeled as such; this package claims no calibrated cutoff. Retain the original score when a learner improves after feedback, and score the new task separately.

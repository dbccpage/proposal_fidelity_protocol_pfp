# Review to structure

Use this pattern to turn old intelligence or a completed run into a useful change
to the existing system. It runs through Adversary's shared coordinator and current
IDE tools. A temporary working context is sufficient.

## The loop

1. **Bound the read.** Name the original task and a useful source selection.
   Read actual source, failures, counterexamples and corrections. State gaps;
   an inventory or parsed file is navigation, not substantive understanding.
2. **Carry the original contract.** For edits, retain a short checklist of public
   APIs, invariants and unaffected behavior. Put it in every worker brief and
   inspect the complete baseline-to-candidate diff after repair.
3. **Find the witness.** Connect a failed assumption to a concrete observation.
   Separate the observed failure, supported cause and possible explanation.
   Compare narratives with raw observations and explicit corrections. Retain the
   narrower supported status and any unresolved premise.
4. **Change the owner.** Search existing code, skills, rules and patterns first.
   Apply the smallest useful supported repair. Use the existing typed contracts
   when needed. A tangible anti-skill/antibody requires a forbidden procedure or
   actual prompt, fixture or detector; do not manufacture one of every form.
5. **Review and recheck.** Inspect the changed artifact against the original need.
   Use a real scoped reviewer when useful, with honest worker identity. Choose
   the smallest deciding check allowed by the task. A negative control needs an
   eligible baseline, an actual changed value and the intended rejection reason.
   Retained test results remain historical; narrow green checks cover their scope.
6. **Review the digestion itself.** Challenge the extracted lesson, its source
   attribution and its limits. A wrong lesson returns to the same owner and
   original need. Correct the interpretation without rewriting historical bytes.
   Recheck the affected output; stop unchanged repetition with its residual open.
7. **Finish and hand off.** Invoke scoped AutoP -> auto-learn once for the outer
   run, consuming the learning already applied. Mirror selected canonical files.
   Give the next worker the relevant owner paths, corrected status, remaining
   obstruction, deciding next action, permissions, budget and dependencies.
   Inner helpers return findings to this finish and do not start another loop.

The durable output is the owning repair and a useful next brief. Routine use
requires no new receipts, report collection, framework or fixed swarm roster.
An honest no-change result is appropriate when the existing owner already
captures the lesson or the evidence does not support another amendment.

## Optional staged prompt and scratchpad

Use this small template when a task benefits from explicit stages. The existing
`TeamworkAction` is the typed input; `TeamworkObservation` is the typed output.
Read the pending action and relevant prior observations, then use this brief:

```text
Objective: <action.objective, unchanged>
Stage: <action.kind and instructions>
Candidate and inputs: <action.candidate, artifacts, relevant source paths>
Contract: <required output, original invariants, permissions and limits>
Carry forward: <decisive corrections and residuals from prior observations>
Do: <smallest useful action and deciding check for this stage>
Return: <candidate content, actionable findings, actual checks and worker identity>
```

Keep optional task-bound notes in `metadata.scratchpad`, for example:

```json
{"assumptions":["Pair checks do not cover every composed word"],"observations":["The source control is absent in the R5 raw output"],"corrections":["Inspect the later source repair before calling this current"],"residuals":["K binding remains proposed in R6"]}
```

These are concise working notes. Keep the deliverable in `content`, actionable
repair requests in `findings`, and checks actually performed in
`metadata.verification`. A rewrite may clarify the brief while preserving its
objective, permissions, input meaning and output contract. The IDE explicitly
carries useful notes from `run.observations` into the next brief: the backend
stores metadata but does not inject it into the next action. Scratchpad keys are
an optional convention within existing metadata, not a new validated schema or
evidence grade. Keep notes in temporary working state; no extra report is needed.

## Worked cases from the corpus

| Witness | Applied structure | Limit to preserve |
| --- | --- | --- |
| [Rational round-3 diff](../../../../_ic/nara/historical/oewas007/_adversary/runs/critique_rational_1791553907/round_3/patch.diff) drops immutability, methods and exact-type validation despite eight retained passing checks. | Shared Adversary build/repair/review prompts and the Adversary skill carry original invariants and inspect the whole diff. | The first missing-method defect was deliberately injected. Reading the full first prompt corrected the digester's initial attribution. No fresh execution is claimed. |
| [Deep Researcher failed probes](../../../../_ic/nara/historical/oewas007/research/briefs/deep_researcher_v0_1/early_failed_probe.md) select an already OPAQUE fixture and rely on interpreter recursion. | Evidence-audit guidance requires baseline eligibility and the intended failure reason; parser limits belong to the declared contract. | Other parsers do not inherit this candidate's numeric limits. Its incomplete inventory remains UNKNOWN. |
| [MUB mission-5 correction](../../../../_ic/nara/historical/oewas007/_adversary/runs/task_adversary_mub6_mission5_grand_synthesis_20261009/summary.json) narrows the sibling narrative to a hypothesis rewrite and noncertificate. | Adversary Digests compares conflicting sources and carries the corrected scope forward. | Narrative PASS, a hash or persona agreement cannot discharge an open mathematical premise. |

## Optional cleanup

When deletion is authorized, distinguish completed artifact review from unresolved
research. Remove only exact fully processed copies whose historical bytes and
required file/directory resolution survive through the existing custody owner.
Check retained bytes and nonselected files before/after. Hold an unmapped copy,
live fixture or unread source. Preserve historical inconsistencies as evidence;
do not create another archive merely to move the intelligence elsewhere.

## Seam for the future cohomological architecture

Keep local invariants, compatibility across worker handoffs, concrete obstruction
witnesses and the effect of each repair explicit. Those are the useful attachment
points for the future cohomological layer's own definitions and checks. This
operational pattern does not itself define a cochain complex or prove closure.

Existing owners: [Adversary](../../adversary/SKILL.md),
[Auto Learn](../../auto-learn/SKILL.md),
[evidence audit](../../adversarial-receipt-audit/SKILL.md) and the
[shared backend](../../../../adversary/use_cases/teamwork.py).

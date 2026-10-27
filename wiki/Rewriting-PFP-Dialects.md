# PFP rewriting: dialects and the pilot

Part of [Rewriting](Rewriting.md). See also: [Overview](Rewriting-PFP.md) · [Residual repair](Rewriting-PFP-Residual-Repair.md)

A small pilot posed one task, a 2×2 linear system with answer `x + y = 3`, in
eleven different surface **dialects**. Each dialect is a rewrite of the same
question into a different surface form. Six use MSS-N notation, four use the
notation of another layer, and `seed` is plain prose. The host checker then judged each
answer.

## The eleven dialects

| Case | Dialect | Layer and strategy | Result under the P* template |
| --- | --- | --- | --- |
| `seed` | Plain prose | None | Accepted, answer 3 |
| `rewrite_01` | Tier H head-word | [MSS-N](Rewriting-MSS-N-Strategies.md) R6 | Accepted, answer 3 |
| `rewrite_02` | Tier D directive | MSS-N R7 | Accepted, answer 3 |
| `rewrite_03` | Prose quarantine (codebook) | MSS-N R2 | Wrong answer, 9 |
| `rewrite_04` | Strict boundary tree | MSS-N R6 | Accepted, answer 3 |
| `rewrite_05` | Carrier declared | MSS-N R1 and R7 | Accepted, answer 3 |
| `rewrite_06` | Matrix and vector | MSS-N R10 | Wrong answer, 1 |
| `rewrite_07` | Pre-Genesis regime | [Pre-Genesis](Rewriting-Pre-Genesis-Strategies.md) PG5, PG7 | Wrong answer, 4 |
| `rewrite_08` | Genesis delta stream | [Genesis](Rewriting-Genesis-Strategies.md) G2, G8 | Wrong answer, 7 |
| `rewrite_09` | S(n) retraction | [S(n)](Rewriting-Sn-Retraction.md) section–retraction | Wrong answer, 7 |
| `rewrite_10` | All four layers nested | Cross-layer passage | Wrong answer, 1 |

Two examples of the surface forms:

```text
rewrite_01:  solve<eq1<add<x, mul<2, y>>, 5>, eq2<sub<mul<3, x>, y>, 1>, return<record<pair<answer, add<x, y>>>>>
rewrite_09:  r_1<x->y>
```

## Reading the results correctly

A recount of the 62 retained test specs (2026-10-20, rechecked 2026-10-22):

| Tests | Arm | Outcome |
| --- | --- | --- |
| 00–10 | The eleven dialects without the P* template | 1 accepted (`seed`), 10 malformed |
| 11–21 | The eleven dialects under P* | 5 accepted (answer 3), 6 wrong answers (9, 1, 4, 7, 7, 1) |
| 22–27 | Revised versions of the six failures | 6 refused |
| 28–30 | Further revisions of `rewrite_06` and `rewrite_09` | 1 refused, 2 accepted |
| 31–61 | Later replays on another model | 1 infrastructure error, 30 typed refusals |

Two corrections to how the results were first described:

- **These are single runs.** Each dialect ran once, on one model. "5 of 5" and
  "6 of 6" are counts of single runs, not accuracy rates.
- **A wrong answer is a model error.** The six `WRONG_ANSWER` rows mean the host
  checker caught a wrong scalar. That is to the checker's credit. It does not
  mean the model was right.

**One row, read properly.** `rewrite_03` returned 9. The host marked it wrong.
The accepted rows returned 3. Nine is not three, and one run is not a rate.

## Host checkers in the pilot suite

| Checker | What it verifies |
| --- | --- |
| Exact linear algebra | Exact rational solutions; catches sign flips, arithmetic slips and singular systems |
| Exact primes | Strictly ascending primes; rejects composites, duplicates and misordering |
| First-order deduction | Syllogisms tied exactly to their premises; rejects "maybe" |
| Epistemic refusal | Correct abstention on undefined functions |
| 2×2 determinant | Exact determinants; rejects non-square input |

## Patterns found in the reasoning traces

These came from mining 22 reasoning traces. They are **candidates**, not admitted
detectors.

| Pattern | Seen in | What happens |
| --- | --- | --- |
| Answer channel | 5 traces | The reasoning decides the schema cannot hold a scalar answer |
| Licence conflict | 2 traces | A valid substitution is found and then refused under the template's rules |
| Corpus invention | 2 traces | The reasoning imagines an outside benchmark the task came from |
| Ghost hypotheses | 11 traces | At least six "maybe" or "could be" markers with no substitution certificate |
| Unbounded scratchpad | 12 traces | Over 1,000 reasoning tokens with no answer |

One active gate came out of this, **intermediate witness**: a composite answer is
accepted only if the reasoning first binds each variable (`x = 1`, `y = 2`).

## What this does not show

No dialect is shown to be best for models in general. The candidate patterns are
not active gates until separately admitted. The natural next test is to run the
same structure on the later pilots and see whether the checkers generalise.

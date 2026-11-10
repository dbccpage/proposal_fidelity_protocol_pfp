# Certified ladder: design of the PFP and Woland cost experiment

**AuthorityEffect:** None.
**Status:** REGISTERED: 2026-10-11 by Woland Swarm Coordinator.
**Baseline Models Pinned:** `google/gemma-4-26b-a4b-it:free`, `google/gemma-4-31b-it:free`, `nvidia/nemotron-3-super-120b-a12b:free`, `deepseek/deepseek-v4-flash`.

## 1. The question, and what is not claimed

Question: on a bank of problems whose answers are known, does a prompt built from the constant
P* template (optionally with stages, minor rewrites and antibodies) reach a certified-correct
answer at lower cost and time than the same problem posed in plain text, and does it bluff less?

Not claimed: that any prompt yields a general result, that an encoding is right in itself, or
that a pass on this bank says anything about problems outside it. A result is stated as "on
this bank, at this rung, with this gate, arm A against arm B".

## 2. Constant and varied

Held constant: the gate (the certificate checker), the P* template, the Woland role definitions,
the answer channel (every arm ends with one canonical line `ANSWER: <canonical form>`; a refusal is
`ANSWER: UNRESOLVED <reason code>`).

Varied, a few factors only: stage count (1 to 8), number and kind of rewrites (none, one minor,
two), model tier, model parameters (temperature 0 or the provider default; `logit_bias` where a
provider offers it), and antibodies on or off per domain. Attention-head and logit steering wait
for an open-weights host and are outside this design.

Not varied and not tracked: how a question is worded, misread or perturbed. That variation is the
sample: the item bank draws many different problems, and each is run under every arm and
compared item by item.

## 3. Items

An item is `{item_id, family, rung, prompt_text, expected_answer, expected_source, checker_id}`.

- `expected_answer` is fixed before any run, from an exact solver in this repository or from a
  published value whose citation has been checked. The model never sees it.
- `rung` is 1 to 5, set by size (matrix dimension, graph order, number of steps) so that plain
  text starts to fail as the rung rises.
- Families: exact linear algebra (determinant, rank, Smith normal form, a rational solve); graph
  facts with published values (chromatic number of the Petersen graph, Kirchhoff spanning-tree
  counts, max-flow and min-cut on small instances); graph repair (an obstruction cochain whose
  repair the exact solver checks); refusal items (an underdetermined or undefined problem whose
  right outcome is a typed refusal); cochain obstruction and gauge repair (exact gradient matching
  $\delta \phi = \omega$ on acyclic complexes, closed non-exact cycles requiring licensed lift, and
  discrete curvature defects forcing immediate typed refusal); algebraic magma associativity
  (associative semigroups vs non-associative bracket magmas requiring executable counterexample witnesses);
  scale descent carrier contraction (loss ledger custody of orthogonal detail coordinates); and
  exact modular arithmetic under the Zero-Float Law.
- The item text carries no hint of the arm. A leak test refuses an item whose expected answer
  appears in its prompt.

## 4. The gate

The gate recomputes or looks up the answer object and compares exactly (rationals, not floats).
It judges the `ANSWER:` line and nothing else. Before any run it must pass its own controls:

- a correct answer is accepted;
- a wrong answer, a shuffled answer, an empty reply and a reply with no `ANSWER:` line are
  rejected;
- the same answer in a different arm's dressing gets the same verdict.

A gate that accepts any control makes the run void.

## 4b. Price and payment

Reasoning is social, so the design fixes the price and checks that it is paid. Whoever or
whatever proposes an answer, a frontier model, a small model or noise, faces the same price.

- **Price schedule.** Each family lists the obligations an answer object must discharge before
  the run. Exact linear algebra: the value and the exact rational certificate the solver
  produces (for a determinant, the elimination that yields it). Graph repair: the repaired
  cochain and the zero residual. Refusal: the typed reason code. Cochain repair: exact gradient matching
  $\delta \phi = \omega$ and canonical gauge anchor $\phi_0 = 0$. Structural lift: valid licensed
  context extension contract token. Curvature refusal: exact defect magnitude and typed refusal payload.
  Magma non-associativity: executable counterexample witness triple demonstrating bracket divergence.
- **Paid means every obligation is discharged by host recomputation.** No partial credit, no
  weights, no tolerance. A correct scalar without its witnesses is unpaid.
- **Proposer-blind.** The gate's input is the answer object. The model name, arm, prompt and
  stage count are not inputs. Stored answers are re-judged by a second pass that the first cannot
  influence, and the two verdicts must match.
- **Payment record** for each item and arm: obligations total and discharged, USD, seconds, open
  residuals, the host check that discharged each obligation, and whether the item was censored.
  Unpaid items cost their cap and stay in the denominator.
- **Cheat proposals**, fixed before any run, all of which must fail: the correct scalar with no
  certificate; keywords only; a certificate for a different item; a certificate that reuses a
  step it was not given; the expected value echoed from the prompt; syntactically valid noise
  that contains the right number; duplicate keys in JSON payload (rejected fail-closed via RFC 8785 unique pairs);
  unlicensed carrier mutation without license token; tautological always-true catch flags;
  unanchored gauge potentials; a reply that says every obligation is discharged. A cheat that is accepted is a
  discount, and a discount voids the run.
- **Novelty and significance are not payable by the gate.** A paid answer that is absent from
  the retained ground truth and the earlier corpus is labelled
  `CANDIDATE_NEW` with AuthorityEffect None. Only a person promotes it.

## 5. Measures

Per item and arm: verified correct (0 or 1); USD; input and output tokens; calls; wall-clock
seconds; residuals left open (the receipt's residual ledger); uncertified claims in the reply.

Definitions:
- **Cost to certified answer**: total USD across every call, stage and repair for the item, with
  an item that never certifies counted at its cap and marked censored.
- **Vacuous**: a reply with no parseable `ANSWER:` line.
- **Bluff**: an `ANSWER:` that is not `UNRESOLVED` on a refusal item.
- **Debt**: formally operationalized under Law 6 (LossLedger coordinate conservation) and cochain defect calculus:
  $$\text{Debt}(P) = \sum_{r \in \mathcal{R}_{\text{open}}} w(r) + \Phi_1(\text{boundary residual}) + \Gamma_2(\text{curvature defect}) + |\mathcal{L}_{\text{uninverted}}|$$
  where $\mathcal{R}_{\text{open}}$ indexes open obligation residual slots, $\Phi_1$ is the uncontracted boundary cochain residual, $\Gamma_2$ is the unrefused discrete curvature defect, and $|\mathcal{L}_{\text{uninverted}}|$ is the count of fine detail coordinates dropped during coarse-graining projection without algebraic inversion custody.

## 6. Arms

A0 plain text. A1 P*template only. A2 P* plus one minor rewrite. A3 P*with k stages, k in
{1, 3, 5, 8}. A4 P* with antibodies mined from training items of the same domain. Arms run
paired: the same item set, the same models, the same parameters.

Selection is by successive halving, so the product of factors is never enumerated.

## 7. Analysis, fixed in advance

Paired by item. Verified-correct rate: exact sign test on discordant pairs, two-sided, alpha 0.05,
with Wilson intervals on each arm. Cost and time: paired difference of per-item cost to certified
answer, with a bootstrap interval over items; censored items stay at their cap. No outcome is
dropped, no item is rerun until it passes, and every arm and rung is reported. A change to an
arm, an item or the gate is a new version; earlier versions and their results stay in the record.
Claims about antibodies use a train and a held-out split fixed before mining.

## 8. Pacing, models and spend

Pacing: one call at a time, at least 2 seconds between calls, no retries, a per-run cap and a
campaign cap, and the existing ledger that books the worst case when a request may have been
billed. Free models are tried first; the one paid model is used only where they leave a
question open.

Models (OpenRouter public list, 2026-10-06; re-read before any run):

| Tier | Model id | USD per million tokens, input and output |
|---|---|---|
| free small | `google/gemma-4-26b-a4b-it:free` | 0 and 0 |
| free mid | `google/gemma-4-31b-it:free` | 0 and 0 |
| free large | `nvidia/nemotron-3-super-120b-a12b:free` | 0 and 0 |
| paid | `deepseek/deepseek-v4-flash` | 0.024 and 1.28 |

Free models are rate-limited, may be withdrawn, and may log prompts; the items are generated
mathematics, so nothing sensitive is sent. Every run records the exact model id returned. Output
is the dear side of the paid model, so `max_tokens` is the lever: at 1500 tokens one call costs at
most about USD 0.002.

Proposed caps, for the owner to set or change:

| Step | Models | Calls | Worst-case USD |
|---|---|---:|---:|
| C0 plain-text calibration, all rungs | the three free tiers | about 180 | 0 |
| C1 plain-text calibration, rungs where the free large tier passes 50% or less | DeepSeek V4 Flash | about 20, max_tokens 1500 | 0.04 |
| Campaign cap for C0 and C1 | | | 0.05 |

An arm comparison (A1 to A4) is a separate step with its own cap, set after C0 and C1 show where
plain text fails.

## 9. Status of baseline decisions

1. **Debt:** Formally operationalized in section 5 under Law 6 LossLedger coordinate conservation and cochain defect calculus ($\Phi_1 + \Gamma_2 + |\mathcal{L}_{\text{uninverted}}| + \sum w(r)$).
2. **Problem families:** The exact linear algebra, graph facts, graph repair, refusal, cochain obstruction, and magma non-associativity families implemented with sovereign exact solvers.
3. **Caps:** Proposed campaign cap fixed at USD 0.05 for calibration stages C0 and C1.
4. **Registration:** Formally REGISTERED with pinned baseline models on 2026-10-11.

## 10. The matrix of pilots

One row per pilot. Factors are the few listed in section 2; everything else is held constant or
is the item sample. Call counts are estimates, not measurements; caps are proposals.

| Pilot | Question | Arms | Models | Items | Calls | Cap USD | Tests | Needs |
|---|---|---|---|---|---:|---:|---|---|
| P0 | Does the gate refuse every control and cheat? | none | none | bank plus cheats | 0 | 0 | H0 | item bank, gate |
| P1 | Where does plain text start to fail? | A0 | three free tiers | 4 families x 5 rungs x 3 items | 180 | 0 | calibration | P0 |
| P2 | Does the paid model solve the rungs the free tiers miss? | A0 | DeepSeek V4 Flash | the failing rungs, about 20 items | 20 | 0.04 | calibration | P1 |
| P3 | Does the P* template pay the price more often or for less? | A0, A1 | free tiers, DeepSeek V4 Flash if P2 shows a gap | 30 or more items per failing rung | set after P1 and P2 | set later | H1 | P1, P2 |
| P4 | Does stage count matter? | A3 with k = 1, 3, 5, 8 | the best small tier | same items as P3 | set after P3 | set later | H2 | P3 |
| P5 | Does a minor rewrite matter? | A1 against A2 | same | same | set after P3 | set later | H3 | P3 |
| P6 | Do antibodies from training items help held-out items? | A1 against A4 | same | train and held-out split fixed first | set after P3 | set later | H4 | P3 |
| P7 | Is a refusal item answered with a typed refusal? | A0, A1 | same | refusal family, 30 or more | set after P1 | set later | H5 | P0 |
| P8 | Do temperature and `logit_bias` change the paid rate? | A1 | the best small tier | same items as P3 | set after P3 | set later | parameters | P3 |
| P9 | Does attention-head or logit steering change it? | A1 | open-weights 8B | same items | set later | set later | later | an open-weights host |

Order: P0, then P1, then P2, then P3 to P8 as the earlier results allow. A pilot whose
prerequisite refutes its premise is not run; the refutation is reported.

# Pre-registration: Fable versus the swarm

AuthorityEffect: None. This file fixes how the comparison is run and scored before any Arm S output exists. It accepts no theorem.
Drafted 2026-10-21 on branch `fable-vs-swarm` (base commit recorded in `cohort.json`). Frozen by the sha256 in
`cohort.json` (`protocol.sha256`, computed over this file with CRLF folded to LF). `compare_common.load_cohort` makes the
swarm runner, the fresh-Fable runner and the scorer refuse to run when this file no longer matches that pin. A change is an
amendment: a new dated file, a new cohort and a new pin, never an edit of this one.

Nothing in the build of this harness called a provider, ran Lean, cargo or pytest, or spent money. The cohort file records what
the receipts on disk say and re-runs nothing.

## 1. Hypothesis

**H1 (the user's thesis, made testable).** A swarm of free and cheap models driven by the PFP ladder (`dag/pfp/llm_ladder`,
tiers 0 to 2: free models, paid OpenRouter gpt-4o-mini, Claude Haiku 5.5), whose every claim is checked by a host verifier,
produces verifier-accepted results on the same prompts as Fable (`claude-fable-5-1`) at no worse than a one-prompt net
shortfall, and at one tenth of the cost per accepted prompt or less.

**H0.** The swarm loses more than one prompt net, or costs more than one tenth, or both.

"Verifier-accepted" is defined in section 5 and in nothing else: no model verdict, no human opinion and no prose quality enters.
H1 is stated per result class (section 5) because the classes are not interchangeable and the swarm can reach only some of them
(section 3.1). A result for one class says nothing about another.

## 2. Cohort and how it was selected

The unit is a **prompt** = one DAG node with an operad collection and prompt file (`dag/operads/index.json`). The rule below
was applied mechanically by `build_cohort.py`; the output is `cohort.json`. No prompt was chosen, dropped or swapped by looking
at an outcome.

**Provenance rule.** A run folder under `dag/results/*/runs/` (other than the ladder's `_ladder` folders) is an expensive-model
run if the commit that added it carries a `Co-Authored-By: Claude Fable|Opus` trailer, or the folder holds a model field naming
`claude-fable-5-1` or `claude-opus-5-5` (`budget.json`, `model_access.json`). Ladder attempts are expensive-model runs if the
attempt row names those models. Scan result at the base commit: 193 non-ladder run folders; 9 Fable, 0 Opus, 26 Sonnet 5.5, 158
with no model trailer and no model field.

| Stratum | Rule | Prompts |
|---|---|---|
| **D** derivation | every node with a completed Fable run folder | 6 |
| **P** paired P0 | every node with an Opus or Fable attempt in a ladder run (packet stored byte for byte) | 3 |
| **C** controls | for each D prompt, the never-run prompt of the same family nearest in operation+relation candidates (lowest index position breaks ties) | 6 |

| Stratum | Node | Arm F runs and model | Arm F cost on disk | Arm F units on disk |
|---|---|---|---|---|
| D | FQ-GAP-BORN-UNIQUENESS-GLEASON | 3 Fable runs: `20261020T004525Z_fable51_born` (API, effort xhigh), `20261020T205000Z_effect_valuation_lean`, `20261020T224000Z_gaussian_hermitian_carrier` | API run 6.56166 USD rated; the other two unrecorded (lower bound 6.67 USD) | L 11 accepted, 1 rejected; W 4 accepted, 2 count-only; claims: 0 of 12 accepted as theorem |
| D | FQ-GAP-CONTINUUM-HILBERT-LIFT | 2 Fable runs (`20261020T230000Z_completion`, `20261021T003000Z_lift_steps`) | unrecorded (lower bound 4.11 USD) | L 7 accepted (a module shipped by both runs counts once); W 3 accepted, 1 not run |
| D | FQ-GAP-STONE-CONTINUOUS-TIME | `20261020T225000Z_discrete_time_spec` (Fable) | unrecorded (lower bound 1.37 USD) | L 1; W 1 accepted, 1 count-only |
| D | L1-IMP-HILBERT-INNER-PRODUCT | `20261021T013500Z_sector_form` (Fable) | unrecorded (lower bound 3.01 USD) | L 2; W 2 |
| D | L1-IMP-LINEAR-ISOMETRIC-DYNAMICS | `20261021T190000Z_finite_wigner` (Fable) | unrecorded (lower bound 5.22 USD) | L 4 (receipts at Lean 4.35.0); W 2 |
| D | TFQ-0084 | `20261021T161243Z_staged` P0 (Fable) | unrecorded (lower bound 1.60 USD) | W 2 (recorded stdout); O: ready for host review, no host verdict on disk |
| P | TFQ-0022 | Opus 5.5 ladder attempt | 0.0557 USD rated | O 2 verified, 0 refused, accepted |
| P | TFQ-0028 | Opus 5.5 ladder attempt | 0.0775 USD rated | O 12 verified, 0 refused, accepted |
| P | TFQ-0031 | Fable 5.1 ladder attempt (headline; two Opus attempts also on disk) | 0.2736 USD rated | O 4 verified, 2 refused, accepted |
| C | six never-run prompts, see `cohort.json` | none | n/a | n/a |

The lower bounds are labelled in `cohort.json` (`estimate_method`): committed authored bytes of the unrecorded runs divided by 3.5
bytes per token times the Fable list output price of 50 USD per million tokens. They omit thinking, tool calls, context re-reads
and abandoned attempts, so the true Fable cost is higher; using them is conservative against the swarm.

**Not in Arm F, and why** (`excluded_candidates`): 8 named runs and 150 staged runs with no model trailer and no model field
(the records of most staged folders name `codex`); they may have been made by a large model but nothing shows it. Opus has no completed run
folder: Opus commits are tooling, migration and DAG work, and Opus sub-agents wrote Python and Rust twins inside Fable sessions
(stated in `validation.json`), which Arm F credits to Fable's side (section 5.4). The 26 Sonnet 5.5 batch-1 runs are context.

**Why strata.** D is what the user cares about (Fable-grade derivations) but is not paired: the agentic sessions' instructions
are not in the repository. P is paired by construction but is only P0 mining on small packets. C measures the swarm's yield and
abstention on prompts nobody has run and gives no parity claim. D and P are reported separately and never pooled into one number.

## 3. The arms

**Arm F, reuse (default, no new spend).** The artifacts and receipts already on disk for D and the recorded ladder attempt for P.
Their cost is what the records say, a labelled lower bound, or a user-supplied figure in `cost_overrides.json` (6.4).

**Arm F, fresh (optional, costs money).** `run_fable_arm.py`: Fable receives exactly the swarm's input (section 4). It refuses
without `--confirm-spend` and a positive `--usd-cap`, dry-runs by default, and states its worst case before sending. Without it
the primary paired test has at most 3 eligible prompts and is INCONCLUSIVE by rule (section 8).

**Arm S.** `run_swarm_arm.py` through `llm_ladder`: tier 0 (Groq gpt-oss-120b, Qwen, gpt-oss-20b and three OpenRouter free models),
tier 1 (OpenRouter gpt-4o-mini), tier 2 (Haiku 5.5). Escalation, rotation, the budget ledger and the host verifier are the
ladder's own. Sonnet (tier 3) is allowed only by an explicit `--max-tier 3` and is then a deviation. Opus and Fable are refused
in code.

### 3.1 Stages: what Arm S can and cannot reach

The ladder wires **P0 only** (`ladder.py`: "Only --stage P0 is wired"; `runner.py` raises for other stages). P1 to P5 exist in
`dag/pfp/batch_tools`, but there they run from a host-authored spec with no provider call, and in the reference system
(`external:sha256:6242ce27786976ac1c386ff6b360f82700dd50fb2b85846803ab4ff55762844d`) behind a native host this repository does not import. **Arm S is
therefore P0 only.** Consequences, fixed in advance:

* It can earn **O** units (host-verified operad entries) and, only through a model's own `lean_skeleton` that claims a sorry-free
  proof, a snippet-level **L** unit. It cannot earn **W** units (Rust or Python witnesses): class W is `NOT_TESTABLE_AT_P0`.
* Fable's D artifacts are P1-level products: kernel-checked modules and exact twins. Against them a P0-only swarm is expected to
  lose class L outright. That outcome is a result about P0, not about PFP with a P1 to P5 pipeline, and it must be reported as such.

## 4. Fairness rules

1. **Identical bytes.** Both ladder arms compile the packet from the same clean room with a constant attempt id, so the first
   packet is byte-identical. The identity is `packet_bytes_sha256` (sha256 over system text, user text and response schema),
   written to every run receipt; `score.py` compares it. For P the stored request of the headline Opus or Fable attempt is
   replayed to every attempt of Arm S, with its recorded sha256 frozen in `cohort.json`. For D, Arm F reuse is **not** byte
   identical (section 9.2); only the fresh arm is.
2. **The prompt file.** The model never reads `dag/prompts/*.yaml`; it reads the compiled packet. `cohort.json` records the
   prompt file sha256 at the freeze commit and at the base commit, and the operad collection sha256 at the freeze commit.
3. **Equal tool access.** Arms S and fresh F: none, one structured JSON reply per call (`max_retries` 0, no model substitution).
   Arm F reuse had tools, many turns and human steering; that favours Fable and is stated wherever Arm F reuse is used.
4. **Equal caps.** At most 7 provider calls and 1800 s wall-clock per prompt, enforced before dispatch by a ledger subclass
   (`NODE_CALL_CAP`, `NODE_WALLCLOCK_CAP`). Fresh Fable defaults to 3 answered attempts (generous to Fable relative to its
   one-attempt tier, fewer than the swarm's 7). The first answer that passes the ladder policy ends a prompt in every arm.
5. **Money caps.** The shared `budget_ledger.json` weekly caps apply; per-prompt paid cap 0.25 USD and arm cap 2.00 USD for the
   swarm; an explicit `--usd-cap` for fresh Fable. All spend, including failed attempts, is counted.
6. **Fable is never in Arm S.** The tier list is cut at 3, models containing `opus` or `fable` are refused, `allow_fable` is
   false. Fable and Opus outputs are never packet input: the packet holds only the compiled operad collection, source
   declarations and the arm's own prior failures.
7. **One run per prompt per arm.** A second Arm S run needs `--allow-rerun "reason"` and is allowed only if every attempt was an
   infrastructure failure (no model answered); the first run's spend still counts. Order of runs is the cohort order.
8. **Scoring uses the same verifier for both arms** (section 5), run on the same artifacts regardless of who made them.

### 4.1 What Arm S may NOT see (contamination)

Arm S works in a **clean room**: a source-only extraction (`git archive`) of the repository at the prompt's **freeze commit**,
the parent of the oldest commit that added any Arm F run folder of the node (for P, of the ladder run). From it are removed:

* all of `dag/results/**` (every run folder, Arm F or not, hence also earlier Codex stagings and every receipt);
* every Arm F artifact path listed in `cohort.json` (`arm_s.exclude_paths`: the installed Lean modules, Python and Rust twins and
  tests) and, for controls, those of every D prompt;
* everything committed after the freeze commit, commit messages, branch names, PR text, `.claude/` notes and memory files;
* the repository's hallucination index and positive operad memory: Arm S starts **cold**. `--seed-memory` may add an index
  file with all entries about cohort nodes removed; using it is a recorded deviation.

A **leak guard** stops a run if any Arm F marker (run folder names, installed module stems and namespaces, twin module names)
occurs in the packet text; marker hits in other clean-room files are recorded as warnings in the receipt. The host verifier
checks citations against the same clean room, so a citation of a declaration that exists only because Fable wrote it later is a
hallucination in Arm S and cannot earn credit. Prior art that existed at the freeze commit (including earlier Fable modules for
other nodes) is visible to Arm S and was visible to Fable. Fable's sessions saw more (the live repository, earlier `dag/results`),
which favours Fable.

## 5. Scoring rubric

Only a verifier accepts. Three classes of **unit**, never added into one number:

**5.1 L: Lean.** A Lean source accepted by Lean **4.35.0**: `lake build +Module` exits 0 with no `error` and no `sorry`, and for
every non-private theorem, lemma, def and abbrev of the file `#print axioms` lists only `propext`, `Classical.choice`,
`Quot.sound` (the empty list counts) and prints a line for every declaration. For a swarm lemma skeleton: `lake env lean` exits 0,
no error, no `sorry`/`admit`/`axiom`, at least one theorem, standard axioms. Warnings other than `sorry` are recorded, not
disqualifying (the repository's own seal is stricter; it is not applied to Arm S). A snippet-level L unit is not the target
theorem and the report says so.

**5.2 W: witness.** A Python test file whose `pytest -q` exits 0 with at least one passed test; a Rust module whose `cargo test
--lib <module filter>` exits 0 with at least one passed and none failed; a recorded Python script whose stdout contains its
declared success marker. Cargo runs use a short `CARGO_TARGET_DIR`, no debug info, and are skipped (unverified) when free disk is
below the stated floor.

**5.3 O: operad entry.** One verified generator, relation, composition, lemma statement or exact numeric claim of an attempt
that the ladder policy **accepted** (at least 2 verified entries, refused-claim rate at most 0.5). Verified means what
`llm_ladder/verify.py` checks: a cited declaration exists where cited and with a readable arity consistent with the claim, and
numeric claims recompute exactly in rational arithmetic. Entries of a non-accepted attempt are rejected units. **An O unit is
grounding credit**: it is not a proof, and it is cheap to earn. It must never be presented as equivalent to an L unit.

**5.4 Attribution and generosity.** Arm F is credited with every unit in its run folders, including units written by Opus
sub-agents inside a session or by the host scripts of the API run (`MatrixInstanceRepaired.lean`), because the question is whether
the swarm can do what Fable's sessions delivered. Units are not removed for lack of model attribution.

**5.5 Evidence levels and the two counts.** Every unit has a verdict `accepted`, `rejected` or `unverified`, never a guess.
* **strict** (the confirmatory count): accepted by a verifier run by `score.py` now (`--run-verifiers`, `--reverify-o`), or, for
  Arm F reuse, by a sealed receipt whose compiler is Lean 4.35.0. Receipts produced under Lean 4.33.1 or with no compiler version are **not**
  strict for the 4.35.0 criterion; they appear as unverified with the recorded verdict shown.
* **as-recorded** (the generous count, for sensitivity): every `accepted` a receipt or self-report claims, any toolchain.
  Python and Rust test counts in `validation.json` are session self-reports, not receipts; they count only here.

**5.6 Prompt-level acceptance** (the paired variable). A prompt is accepted in class k by an arm if it has at least one accepted
class-k unit. A prompt is **eligible** for class k when Arm F has at least one class-k unit with a recorded or re-run verdict.

**5.7 Metrics** (all reported, per stratum, per arm, per class): accepted, rejected and unverified units; prompts accepted;
outcome counts (6.1); refused-claim rate = refused / (verified + refused) over answered attempts; spend; provider calls;
wall-clock; cost per accepted unit (all spend of the arm divided by accepted units of the class) and cost per accepted prompt
(all spend divided by prompts with any accepted unit). Spend of failed attempts, abstentions and prompts with nothing accepted is
always in the numerator. A zero-spend arm has cost 0, not "n/a"; wall-clock and call counts are reported beside it because free
tiers are rate limited.

**5.8 Tie rules.** A prompt where both arms accept or both do not is a tie and adds to neither side. Costs within 1 per cent are equal.
If an arm accepted units and spent exactly 0, its cost per accepted prompt is 0 and the cost leg passes. Unit counts never break
a prompt tie; they are descriptive.

## 6. Abstentions, failures, cost

**6.1 Per-prompt outcome.** `ACCEPTED`: the ladder policy accepted an attempt. `ABSTAINED`: models answered validly but nothing
could be grounded (the ladder's `blocked_abstained`, or every answered attempt flagged abstained). `FAILED`: answered, but every
attempt was rejected by the host (schema violation, unparseable or truncated reply, model refusal, refused-claim rate too high,
too few verified entries). `BUDGET_STOPPED`: a money, call or wall-clock cap ended the run. `INFRA_FAILURE`: no model answered
(rate limits, timeouts, authentication); this alone permits the one rerun of fairness rule 7. `NOT_RUN`. For Arm F reuse: `ACCEPTED` if any
unit is accepted, `FAILED` if only rejected units exist, `NOT_RECORDED` if the disk holds no verdict.
**Intention to treat:** abstentions, failures and budget stops stay in the denominator of every rate and are failures for the
prompt-level comparison. Only the one all-infrastructure rerun is excluded, and its first spend is kept.

**6.2 Hallucination.** A claim refused by the host, by class (`nonexistent_declaration`, `false_numeric_claim`, ...). Infrastructure
errors are not hallucinations.

**6.3 Verification incompleteness.** A unit that could not be checked (no Lean 4.35.0 build, cargo skipped for disk) is
`unverified`. The decision rule never returns SUPPORTS while any unit is unverified (section 8).

**6.4 Cost basis.** Rated cost from provider usage at list price (`cost_source` in each call row); invoices are not observed.
Arm F reuse cost: recorded where a run folder records it; otherwise the labelled lower bound; otherwise the figure in
`cost_overrides.json` (`{"<NODE>": {"usd": 12.3, "basis": "console session cost, <date>"}}`), which the user may supply from the
Anthropic console and which then replaces the lower bound. Free-tier calls cost 0 and are not an invoice; their rate limits are
the real price and appear as wall-clock.

## 7. Blinding

`score.py` first writes only `blinded_table.md`, `blinded_scores.json` and `report_blinded.md`: per prompt two anonymous columns
X and Y, each with outcome and counts of accepted/rejected/unverified units per class, **without** model names, paths, tiers or cost.
Which column is the swarm is a per-prompt coin, the low bit of the first byte of `sha256(protocol_sha256 + "|blind|" + node_id)`; it is not printed
until `--unblind`. Outcome words that exist for one arm only are folded into a common vocabulary. Verdicts are mechanical, so
blinding protects the human step: any reading of the blinded table, including a decision that a verifier misbehaved, is written
down before `--unblind`; a verifier fix is a new scoring run recorded as a deviation, never a changed verdict. The pattern of
unit classes can identify an arm (only Fable's sessions produce W units); that is a property of the outcome, not a leak.
Whoever launches the arms cannot be blind; the scorer's blinding is procedural.

## 8. Decision rule

Computed by `score.py --unblind`; nothing else decides.

For class k and the eligible prompts, let b be prompts accepted by Fable and not by the swarm, c the reverse, net = b - c.

* **Quality leg.** pass if net <= 1. fail if net >= 3 or the one-sided exact sign test (swarm worse, binomial on b + c at 1/2) has
  p <= 0.05. Otherwise borderline.
* **Cost leg.** ratio r = (swarm spend on eligible prompts / swarm accepted prompts) / (Fable spend on the same prompts / Fable
  accepted prompts). pass if r <= 0.10 (within 1 per cent of 1 is a tie), fail if above. not evaluable when Fable's cost is
  unknown for some prompt and no override was given (lower bounds count as known and are labelled).
* **Minimum n.** fewer than 6 eligible prompts: `INCONCLUSIVE` whatever the counts.

Verdicts: `SUPPORTS` (n >= 6, quality pass, cost pass, no unverified unit), `REFUTES` (quality fail), `REFUTES_ON_COST`,
`INCONCLUSIVE` (n < 6 or borderline), `QUALITY_ONLY_COST_NOT_EVALUABLE`, `INDICATIVE_*_UNVERIFIED_UNITS_REMAIN` (the same pass
with unverified units left, never citable), `NOT_TESTABLE_AT_P0` (class W).

**Comparisons.** **C1, primary, class O:** the paired set = P (recorded Opus/Fable attempt vs the replayed-packet swarm) plus D
if the fresh-Fable arm was run. n = 3 without the fresh arm, up to 9 with it. **C2, secondary, classes L and W:** D prompts,
swarm vs Arm F reuse, outcome only. Controls (C) are used for the swarm's yield, abstention and refused-claim rates and for a
descriptive comparison of the swarm's acceptance on C versus D; they carry no verdict.

**Stated in advance, so that the result can surprise:** class O on P and fresh D is expected to be a tie on quality and a pass
on cost; class L on D is expected to REFUTE (a P0-only swarm will not produce kernel-checked derivations); class W is not
testable. If so, the supportable sentence is: the swarm matches Fable at P0 mining at a small fraction of the cost and does not
reach Fable's P1-level outcomes, which the ladder does not attempt.

## 9. Threats to validity

1. **Contamination.** Fable's outputs are in the repository the swarm could read. Mitigation: the clean room, exclusion list, leak
   guard and cold memory (4.1). Residual: pretraining exposure of any model to the public repository; names or ideas that were in
   the repository before the freeze commit; markers the guard does not know. Marker hits in clean-room files are listed in each
   receipt for inspection.
2. **Non-pairing in D.** Fable's sessions had tools, many turns, human steering and an instruction text that is not in the
   repository; the swarm gets one packet. C2 is an outcome comparison and is favourable to Fable on every axis except cost.
3. **Cherry-picking and survivorship.** Selection is by the mechanical rule in section 2 and is frozen before any Arm S run.
   Survivorship runs the other way for the swarm: abandoned or uncommitted Fable attempts leave no record, so Fable's cost and
   failure rate are understated. Cost lower bounds are labelled.
4. **Same-model review.** Arm F artifacts were repaired through `/code-review` rounds by Claude sessions and gated by scripts the
   same sessions wrote. Scoring does not use those reviews: only a verifier run by `score.py` or a sealed compiler receipt counts.
5. **Verifier weakness.** `verify.py` checks existence, readable arity, source-consistent numerals and exact arithmetic, not
   semantics. O credit can be earned by citing existing declarations correctly. Semantic statement drift is flagged only
   heuristically. Lean snippet units are not target theorems.
6. **Toolchain.** The Fable receipts of 2026-10-20 and 21 were compiled under Lean 4.33.1 (all except the Wigner run); `lean4/` was moved
   to 4.35.0 afterwards. Under the strict count they are unverified until re-run. A failure to rebuild under 4.35.0 is a result.
7. **Prior exposure.** The pilot results for TFQ-0022, TFQ-0028 and TFQ-0031 (Opus, Fable and the free tiers on the same packets) are on
   disk and were seen before this registration. P is therefore not blind to its authors; its value is that the Fable and Opus side
   is a pre-existing record. Free-tier model lists and limits change; the models used are recorded per call.
8. **Small n.** At most 9 paired and 6 outcome prompts. Wilson intervals are reported; none of this is a significance claim beyond
   the sign test of section 8.
9. **Cost.** Rated, not invoiced. The free tier's cost is quota and time, not zero effort. Fable's reuse cost is mostly a lower bound.
10. **Harness drift.** Receipts record the harness commit, the packet and clean-room manifest hashes and every cap. A change to
    `llm_ladder` between arms is a deviation.

## 10. Deviations and what is not claimed

Every deviation (a `--max-tier 3` run, `--seed-memory`, `--effort`/`--max-tokens` for Fable, a rerun, a skipped verifier, a changed
cap) is written into the receipts and listed in the report. Not claimed: that the swarm can derive Lean theorems, that O credit equals
mathematical progress, that Fable's reuse outcomes are reproducible, or anything about prompts outside the cohort.

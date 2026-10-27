# Use PFP: one task, one check, then a justified extension

The aim is the simplest cost-effective, repeatable PFP procedure that can be
reused across tasks. Start with a concrete task, an explicit prompt and response
contract, and a way to check the result. The model proposes a candidate; the
host checks it. Report acceptance, refusal or unavailable verification along
with actual calls and cost. This separates usable results from plausible text
and lets the same captured result be checked again without another model call.

Choose the fewest stages needed for that task. Try a bounded repair only when
the check identifies something the next turn can address, with an explicit stop
and spend limit. A one-task demonstration establishes that procedure for that
task. A universal interface is the design goal; universal effectiveness requires
evidence across relevant tasks.

The application owner is `pfp`. `pfp` executes a contiguous prefix
of stages 1 through 8. Stage5 is the independent host check; the other stages
dispatch model turns. A completed prefix before Stage5 has no mathematical
acceptance. The example below uses the existing eight-stage implementation;
eight stages are not a requirement for every future PFP task. The fixed pilot
grid and its generator have been retired.

```powershell
python -m pfp.entrypoints.cli.pfp run-seed DEMO_07 `
  --stages 8 --modes 2 --model <MODEL_ID> --timeout 180 `
  --max-provider-calls 7 --max-output-tokens 3000 `
  --max-estimated-cost-microusd 50000 --output C:/Temp/pfp-seed07-new
python -m pfp.entrypoints.cli.pfp run-seed DEMO_07 `
  --replay C:/Temp/pfp-seed07-new
python -m pfp.entrypoints.cli.pfp check-seed DEMO_07 candidate.json
```

Start with this single example and collate its outcome, host decision, model
calls, elapsed time, reported cost and remaining error. The existing bounded
live result is recorded in [the consolidation results](pfp_consolidation_plan.md).
Replay that result before buying another run. Keep unknown billing explicit.

Once the core is useful, choose an extension to answer one question:

| Extension | Question to answer before adding runs |
| --- | --- |
| Hieroglyphic or other rewrites | Does the encoding preserve the task and reduce cost or improve the checked result? |
| Variable prompt/response templates | Does this template improve compliance or usefulness without leaking the answer? |
| Modes | What specific missing capability does this mode supply? |
| Stages and repair loops | Does another turn fix an observed failure enough to justify its cost? |
| Order of operations | Does changing the order preserve required inputs and improve the checked outcome? |

Change one relevant choice at a time and reuse the same task and checker. Use a
plain baseline when asking whether PFP improves an outcome, and an invalid
candidate when checking whether the evaluator can reject it. Increase the sample
only when the current result leaves a decision unresolved. There is no automatic
cross-product of seeds, models, representations, modes or stages, and no required
pilot count. Keep useful source material and historical results.

Discovery is a secondary goal. Choose small adversarial or exploratory experiments
to expose new LLM failure modes, system defects or useful patterns. Name what
each experiment is trying to reveal and bound its cost. An unexpected failure
can justify the next experiment. Convert useful findings into existing typed
guidance, a prompt-attached antibody, a template change or a code repair, with a
concrete reproducer. For an antibody, identify its trigger and prompt attachment,
and check a benign example so it does not reject useful work indiscriminately.

PFP is work in progress. Simplicity is the starting point, not evidence that the
current implementation is sufficient. Add engineering when observed failures,
usability or repeatability justify it; remove complexity that supplies no useful
capability. Discovery runs and improvement measurements answer different
questions, so label their results accordingly.

Replace `<MODEL_ID>` with your selected available provider model. Current live
numbered stages use the existing accounted PFP gateway: original stage prompts
and decoding sit inside its task/attempt/input-bound reply contract. Stage
validation and the Stage5 host checker still own acceptance. No provider
`response_format` constraint is added to the original numbered-stage protocol.

Live execution requires explicit `--max-provider-calls` (1–8),
`--max-output-tokens` (1–3000) and one financial policy (1–50,000 microusd).
The example chooses an **estimated** limit of $0.05; it is not a hard provider
liability guarantee. Choose a lower bound or fewer stages for a smaller run.
`--max-cost-microusd` instead requests a hard limit and refuses when the transport
cannot establish maximum liability. There is no silent policy/model fallback.
Credentials use the existing resolver, optionally `--env-file <PATH>`.

Both the output directory and its sibling `<output>.budget.sqlite3` must be new.
All stages share that existing Providers accounting boundary; the adapter does
not create a second budget. Unknown or ambiguous billing stops later sends and
remains unknown. The optional HTTP `--timeout` keeps its default of 60 seconds
and accepts values up to 300 seconds.

Current captures carry a versioned `pipeline.json`, original request binding,
exact provider bytes and checked exchange per stage. Replay uses captured bytes
without credentials, pricing requests, a ledger or provider sends. Old
`pricing.json` captures retain their original replay semantics and hashes.
Preserve those historical files; they are not upgraded into current captures.
The model proposes; host arithmetic, native replay or Lean decides the candidate.

For `DEMO_07`, a witness has `potential`, `d0`, `original` and `residual` fields.
Rational values use integers or exact rational strings; geometry indices remain
integers. Each seed exposes its own structural witness schema, without reference
answers. `check-seed` also accepts witnesses authored outside the model pipeline.
This is a finite typed witness interface, not arbitrary prose grading.

Without `--model`, the command uses stage-shape fixtures. Those fixtures cannot
manufacture a seed witness or a host PASS. `--stages 1` is a useful offline
plumbing check; a mathematical run needs an actual candidate.

Modes2(sealed source) and14(predicted refusal control) execute directly in the
pipeline. Other executable modes require explicit JSON inputs via
`--mode-inputs path.json`, keyed by mode number:

| Modes | Current deciding capability |
| --- | --- |
|1,7,8|Declared glyph roundtrip, finite permutation/braid checks, exact involution.|
|4,5|Prompt-attached procedural anti-op controls; hash-bound, colour-checked instruction composition.|
|9|Actual fixed-target Lean build, hidden-statement elaboration and native axiom audit.|
|10,11|Typed cemetery screening with seed replay; existing finite Adversary C011 checker.|
|12,13|Declared simplicial/connection checks; relational lossless/dependency/confluence checks.|
|16,17|Finite perturbation/repair; provenance diagnostics and independent host witness replay.|
|18,19,20|Exact supplied MUB triad, finite first-cut separation, bounded proposer/adversary witnesses.|
|3,6,15|Unavailable: no connected model-internal or interactive execution hook.|

Each artifact states its finite scope. Persona agreement, a candidate PASS flag
and a narrative winning condition do not substitute for an executable checker.
Missing mode inputs or tools refuse before model dispatch. A negative control
that produces its predicted refusal is a successful control, not an accepted
candidate. No runtime concurrency or additional framework is introduced.

Native replay seeds use the existing `genesis_replay` binary. Set
`CORE_GENESIS_REPLAY_BINARY` for an explicit build location; set
`CORE_SYMBOL_GAME_HOST` for the shared Symbol Game host. Lean requires its exact
submitted toolchain pin to be installed. Historical demo002 deliberately refuses
when its original source bytes cannot be resolved.

AuthorityEffect: None.

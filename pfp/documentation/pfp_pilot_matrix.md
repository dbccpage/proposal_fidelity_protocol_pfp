# Accounted exploratory pilot turns

AuthorityEffect: None. These helpers retain their original cases and judges;
this is a provider-route repair, not completion of their scientific protocols.

The formal-math and program-synthesis matrix helpers use
`omega_engine_pfp.infrastructure.pilot_matrix` for every model turn:

1. Prepare the existing PFP task/attempt/input binding with public inputs.
2. Reserve through the existing Providers ledger before sending.
3. Retain exact vendor wire bytes separately from the PFP completion bytes.
4. Check the actual returned binding/schema before handing `answer` to the
   original case judge. Shape-valid answers remain UNVERIFIED at this boundary.
5. Stop all remaining cases and models on unknown cost, transport ambiguity or
   exhausted allowance. A settled malformed PFP reply is an infrastructure
   failure; it cannot count as a mathematically incorrect answer.

No raw HTTP or custom transport fallback remains in either helper. Legacy
positional API-key arguments do not select a sender; the injected canonical
`EstimatedBudgetGateway` or `DurableRunGateway` owns transport and credentials.
All selected model wrappers must share the same ledger, allowance and call
limit. Reopening that ledger with a different pilot call limit refuses. A hard
budget still requires an enforceable transport liability; the current HTTP
transport does not supply that guarantee. Estimated vendor cost is explicitly
weaker and does not guarantee the final bill.

## One explicitly bounded original synthesis case

From the repository root, with the existing runtime dependencies and configured
OpenRouter credential, run:

```powershell
python -m omega_engine_pfp.tests.pilots.c052_maxflow_mincut_certificates.run_c052_matrix --output-dir pilot-c052-one --model meta-llama/llama-3.1-8b-instruct --case-limit 1 --max-output-tokens 2048 --max-provider-calls 1 --max-estimated-cost-microusd 10000
```

`--output-dir` must be new. Optional `--env-file` selects an explicit existing
credential file through the shared resolver. Prices and supported model
parameters are checked by the existing factory; missing prerequisites refuse.
The example selects one original public C052 case and its two unchanged
checkers. It does not execute the full C052 protocol or C001–C030 campaign.

Original output limits are preserved. Estimated mode accepts at most 3000 output
tokens and 64 calls. A runner declaring 4096 tokens needs an explicit
`--max-output-tokens` override for an exploratory estimated run; the helper never
silently shrinks the original contract. `run.json` retains the actual and original
case counts/output limits. `summary.json` records planned/attempted turns and a
stop reason. Attempted turns include pre-send refusals; provider wire/accounting
fields distinguish them from received replies. Historical output folders and
judge bytes are untouched.

The formal helper's existing `run_model_matrix` accepts either a `gateways`
model mapping or explicit `max_tokens`, `max_estimated_cost_microusd` and
`max_provider_calls` for composition. Its existing opaque case tokens, withheld
fields, evaluator and arm-isolated antibody store remain in place. Model-specific
output settings must match their gateway before any selected model is sent.

## Read retained dossier capsules after relocation

Historical dossier plans retain their original `pilot_.../tests/test_...` identities.
The replay reader resolves pilots 0000000 through 0000005 under
`omega_engine_pfp/tests`; other pilots stay under the Woland tests owner. It verifies
the input against the plan's original digest after selecting that owner. Missing
or changed canonical bytes refuse; an old duplicate does not provide a fallback.
This reads retained data without regenerating plans or rewriting responses.

For one retained capsule, from the repository root:

```python
from omega_engine_woland.tests.pilots.replay_runners.dossier_capsules.prepare import historical_plan
from omega_engine_woland.tests.pilots.replay_runners.dossier_capsules.run import load_case

row = historical_plan("_free")["cases"][0]
folder, case = load_case(row)
print(row["capsule"], folder, case["pilot_id"])
```

Successful input resolution is not successful historical replay. Archived source
names remain unchanged; explicit reader mappings compare the recorded digests
with the applicable current checker/provider bytes. A changed source or runtime
environment still refuses replay. Original raw responses and source snapshots
are retained and are never rehashed to claim current acceptance.

## Retired campaign entry points

The mode-trials and dossier-trials campaigns remain retired. Their replay
adapters retain historical source/metadata resolution and independent grading;
they are not alternative live senders. Mode `dispatch_pilots()` and
`retarget_specs()` refuse before reading credentials or changing pilot specs.
Dossier `live()` and `--live` refuse before creating authorization or budget
files, loading historical plans, looking up pricing or calling a provider.
The old fixed 25/250-case campaigns are not recreated by the current interface.

For a new current-IDE task, use the existing shared Woland/PFP backend:

```powershell
python -m omega_engine_woland.entrypoints.cli teamwork start --objective "Your task" --state new-task.json
```

Read the returned `pfp_turn`, do the requested work, and submit the actual bound
reply through `teamwork submit`. `/woland` drives this same path in the IDE.
For one explicit task file, the PFP CLI also exposes `prepare-task TASK.json
--attempt ID` and `check-task TASK.json REPLY.json --attempt ID` under
`python -m omega_engine_pfp.entrypoints.cli.pfp`. Both are offline boundaries;
new hosted work uses an explicitly configured existing accounted gateway.

Retained campaign snapshots and pinned Git metadata are read-only. A historical
checker/environment mismatch remains a refusal; a new source hash must not be
written into an old response to claim replay success. Preparing/checking a seed
proposal does not execute its mode substrate or complete its scientific protocol.

## Bounded plain and templated pilot suite

The existing `run-pilot-suite` command uses the same PFP/accounted boundary.
Start with two original prompts and a fresh output directory:

```powershell
python -m omega_engine_pfp.entrypoints.cli.pfp run-pilot-suite --pilot-dir omega_engine_pfp/tests/pilot_0000000 --dry-run --max-cases 2 --output-dir "$env:TEMP/pfp-suite-fixture"
```

This dry run uses host-reference answers and makes no provider calls. Its results
exercise the original checker and reporting path; they do not measure a model.
The source prompt builders, pilot files, expected data and host judges retain
their owners. Only public messages enter a live task; expected answers stay with
the host. The PFP envelope changes the transport, so new runs are not byte-for-byte
replications of historical raw-chat experiments.

For an authorized hosted attempt, use a new directory, remove `--dry-run` and
supply `--model`, `--max-provider-calls`, `--max-output-tokens` and
`--max-estimated-cost-microusd`. For example, `--max-cases 2
--max-provider-calls 2 --max-output-tokens 512
--max-estimated-cost-microusd 10000` selects at most two prompts under one
estimated allowance. Supply the intended model explicitly; current availability,
pricing and supported parameters are checked at composition. `--env-file` is
optional and selects an existing credential file through the shared resolver.

The same allowance covers every selected case. Ambiguous transport, unknown cost
or exhausted accounting stops continuation. There is no automatic retry. The
output retains raw provider bytes, PFP checks, original host verdicts and a
partial comparison when dispatch stops. Unknown cost remains unknown; a known
subtotal does not stand in for the complete bill. Existing result directories
are never reused by this command.

New reports use `pfp.pilot-response.accounted.v2` and
`pfp.pilot-comparison-results.accounted.v2` labels because partial exchanges and
unknown costs do not satisfy the historical v1 report schemas. The original v1
files and contracts remain unchanged. These current report labels describe the
runner output; PFP still owns the executable task/reply contract.

`--max-cases` selects the existing ordered prompt list. A prefix may contain only
plain prompts; it is not a paired experiment. Compare plain and templated arms
only when the same intended cases were completed under compatible conditions.
Ratios remain unavailable if either arm includes a malformed, unfinished,
unmatched or duplicate case. The overall totals still include every observed
cost; successful pairs cannot hide the cost of failed attempts.
Successful command execution or schema validity alone does not establish PFP
superiority or original protocol completion.

## Observed corrections and remaining work

Focused controls reproduced raw-network bypasses without sending, then checked
actual preparation/reservation/returned-byte checking, positive and wrong-answer
judges, private-field isolation, malformed replies, unknown cost and restarts.
An empty synthesis checker list now refuses rather than accepting vacuously.
The review also reproduced returned-body loss on provider JSON/envelope errors.
The existing Providers failure owner now retains those bounded octets without
inventing HTTP status; an oversized response retains only the ceiling-plus-one
prefix and labels its digest as truncated. Unresolved accounting still stops.
The C052 command also runs in a fresh process: repository pytest compatibility
aliases had hidden its retired namespace imports. Only its entry-point imports
changed; original cases and both judges are preserved.

These controls use synthetic vendor replies and make zero external sends.
Other old experimental entry points may still need canonical namespace repairs;
a passing import under pytest is insufficient because its compatibility finder
can redirect retired namespaces. Check each actual command in a fresh process.
Full session/neural protocols, installed-package closure and Woland/PFP admission
remain separate acceptance work under OEPFP-009. No new framework or concurrency
mechanism was added.

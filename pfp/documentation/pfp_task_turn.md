# One typed PFP task turn

This offline path prepares an ordinary worker, reviewer or learning task and
checks its actual reply. It reuses `PfpPromptTemplate`, `PfpTaskPrompt`,
`PfpPrompt`, strict JSON ingress and the existing independently injected judges.
It does not dispatch a provider or require a mathematical witness, SPK-only
fields or eight stages. Adversary uses this boundary for its supported model routes;
[PFP-010](../../product_planning_office/plans/epics/oepfp/epic_oe_pfp_010_consolidated_residual_plan.md)
records legacy route dispositions and current limits.

Save this as `task.json`:

```json
{
  "task_id": "worker-17",
  "objective": "Summarize this issue and propose the next action.",
  "input": {"issue": "A caller still imports a retired package."},
  "answer_schema": {
    "type": "object",
    "properties": {"summary": {"type": "string"}, "next_action": {"type": "string"}},
    "required": ["summary", "next_action"],
    "additionalProperties": false
  },
  "allowed_operations": ["inspect the supplied issue", "propose a repair"],
  "stopping_bounds": {"maximum_replies": 1}
}
```

From an installed checkout:

```powershell
pfp prepare-task task.json --attempt attempt-1
pfp check-task task.json reply.json --attempt attempt-1
```

Send the prepared `system` and `user` fields through the current IDE or your
existing model adapter. Save the actual model reply as `reply.json`; do not
construct a successful reply on its behalf. The reply has exactly four fields:
`task_id`, `attempt_id`, `input_sha256` and the task-specific `answer`. Use the
exact identity/digest constants in the prepared response schema. That schema is
included in the system prompt as actual JSON. The answer may be an object,
string, number or array as explicitly declared by its owner. Reviewers can use
a findings array; learning turns can propose a typed lesson and its tangible
prompt/operation attachment. Proposing a lesson does not admit an antibody.

The checker recomputes the expected contract from the original task. The public
input digest covers task ID, objective, sanitized input and declared answer
schema, using compact sorted ASCII JSON with `allow_nan=False`. This names the
byte profile and makes no RFC 8785 claim. Original task objects are not modified.
Oracle/expected-answer labels and host diagnostic fields stay outside the model
input; the host retains its original case for independent checking.

Duplicate keys, nonfinite numbers, fences, extra envelope fields, stale task or
attempt IDs and wrong public-input digests are refused. Integer schemas require
native integers: `1.0`, `true` and `"1"` are not integer candidates. Local schema
references such as `#/$defs/text` retain their meaning inside the answer envelope;
external `$ref` and `$dynamicRef` are refused before dispatch or validation.
The embedded answer receives a deterministic schema resource ID when it has none.

`check-task` retains the exact raw bytes as base64, their SHA-256 and byte count
in its JSON output. It creates no receipt directory and reports zero provider
calls without inventing a cost. A schema-valid reply without a judge remains
`PROVIDER_COMPLETED` with evidence grade `UNVERIFIED`; exit code 0 means this
offline shape/binding check succeeded. It does not mean task acceptance. Set
`"checker_required": true` to refuse an unavailable independent checker. Supply
finite judges through the Python use case; the CLI does not dynamically import
checker code from a task file. Existing `check-seed` remains available for seed
witnesses.

For a finite task, inject the existing judge boundary:

```python
from pfp.domain.contracts.pfp_runtime import PfpPromptTemplate, PfpTaskPrompt
from pfp.use_cases.pfp_prompt import PreparePfpTaskTurnUseCase
from pfp.use_cases.pfp_proposal import CheckPfpTaskTurnUseCase

task = PfpTaskPrompt("sum-1", "Add a and b.", {"a": 2, "b": 3}, {"type": "integer"})
template = PfpPromptTemplate("Complete the supplied task.", "[USER PROMPT]", {})
prompt = PreparePfpTaskTurnUseCase().execute(template, task, "attempt-1")

def independent_sum(case, candidate):
    return candidate == case["a"] + case["b"], "Checked addition from task inputs."

# actual_reply_bytes comes from the IDE/provider, preserved before interpretation.
checked = CheckPfpTaskTurnUseCase().execute(
    task, prompt, actual_reply_bytes,
    judges=[("independent-sum", independent_sum)], require_checker=True,
)
```

A schema-valid wrong answer reaches that judge and remains rejected. Only the
independent check can produce `HOST_ACCEPTED`. Judge exceptions/disagreement use
the existing checker-defect outcome. Raw judge messages remain host-side:
continuation accepts only the existing bounded `REPAIR_RULES`, and a revised
candidate needs a fresh check. Provider budgets, continuing run limits and
automatic Adversary orchestration remain responsibilities of the existing run
adapter; these offline operations do not pretend to enforce them.

## Observed handoff and applied lesson

The PFP-000/001 delivery exercised this route with a real review reply from the
current IDE assistant, then passed the checked answer into Adversary's existing
review observation. The binding/schema check returned `PROVIDER_COMPLETED`,
`UNVERIFIED` and zero provider calls. The subsequent PFP-003/008 delivery uses the same task binding for the supported
shared coordinator and other model entrypoints. It does not intercept host IDE
network activity.

PO035's schema-copying failure informed a concrete prompt correction: ask for
a JSON **instance** that validates against the supplied schema, explicitly
excluding the schema itself. The exact contract still comes from the task owner,
and raw output still passes through strict ingress. This instruction is a
practical repair, not evidence of universal reasoning improvement. Final focused
controls across both deliveries passed 185 tests on Python 3.13.11.

`AuthorityEffect: None.` These controls establish typed, bound interpretation for
supported tasks. They establish neither universal reasoning improvement nor a
general mathematical verifier.

## Shared Adversary use

Python and `/adversary` use the existing teamwork coordinator. Ordinary role turns
need one minimal PFP envelope, not eight stages or a mathematical witness.

```powershell
$env:CORE_SYMBOL_GAME_HOST = (Resolve-Path .scratch/oewas012/native-target/debug/core_symbol_game.exe).Path
python -m adversary.entrypoints.cli teamwork start --objective "Keep supported Adversary model routes on PFP" --state task.json --native-gate-scope adversary/config/software_gate_scope_v1.json --native-gate-policy require_pass --checker-id pfp-route-closure-v1 --checker-source pfp/tests/test_route_closure.py --check-command python -B -m pytest pfp/tests/test_route_closure.py -q --override-ini addopts=
python -m adversary.entrypoints.cli teamwork next --state task.json
python -m adversary.entrypoints.cli teamwork submit --state task.json --raw-reply reply.json
```

Supply the built native host and an original-task checker appropriate to the
actual objective. The example checks supported route closure, not review quality.
Use new state paths. Syntax Prefilter comes first: run `teamwork check --state task.json`.
For a returned host action, execute its existing command (`native-gates`,
`recheck`, `ddc-store`, `ddc-read`, `digest` or `ddc-complete`) with the same state.
Only actions with `communication: pfp` have a model turn. `/adversary <task>` performs
this same handoff in the current IDE session; no paid executor is selected.

Read `pfp_turn.system` and `pfp_turn.user`, perform the requested current-session
work and save the actual response instance matching `pfp_turn.response_schema`
to `reply.json`. Copy the supplied binding fields. Build/repair answers are text;
review answers contain `summary` and `findings`; learning adds `lessons`. Repeat
the returned pending action until completed or blocked. No provider is silently
selected. IDE cost remains unavailable. Unchecked `--result` model submissions
refuse. For file changes, add `--host-result host.json` alongside `--raw-reply`;
Python takes only the matching artifact manifest and independently reads its
bytes. Model content, findings and claimed checks in the sidecar are ignored.
Source-bound build/repair and claimed learning edits require this readback.

For an explicitly paid text-artifact bout:

```powershell
python -m adversary.entrypoints.cli teamwork run --executor openrouter --objective "Write a concise review checklist" --state bout.json --output checklist.txt --model openai/gpt-4o-mini --max-estimated-cost-microusd 5000 --max-provider-calls 42 --max-output-tokens 1024 --max-repairs 1 --native-gate-scope adversary/config/software_gate_scope_v1.json --checker-id checklist.file.v1 --check-command python -c "from pathlib import Path; p=Path('checklist.txt'); assert p.is_file() and p.stat().st_size > 0"
```

The paid example was not executed in this closeout. Its checker establishes
nonempty file delivery only; the text remains UNVERIFIED.
Use new state/output paths. The existing credential resolver supplies the key;
keep it out of prompts and files. This is a continuing estimated budget,
not a vendor-enforced maximum bill. Missing pricing, unknown cost, an ambiguous
send or exhausted allowance stops dispatch and retains the unresolved attempt.
Malformed-reply repair stays within that same allowance. A remote text proposal
does not execute commands or install learned changes; the current IDE applies
justified learning through `/auto-oe-autop` and `/auto-learn` once after the run.

Captured `metadata.pfp` records can be rechecked without a provider:

```python
from pfp.infrastructure.task_turn import prepare_task_turn

turn = prepare_task_turn(system=original_system, user=original_user,
    task_id=original_task_id, attempt_id=original_attempt_id,
    answer_schema=original_answer_schema, context=original_context,
    checker_id=original_checker_id)
rechecked = turn.replay(saved_pfp_record)
```

Retain the original inputs and checker identity. Changing a task/candidate/schema,
checker or raw reply requires a fresh check; a cached success is not transferable.
The observed live build/review cost $0.00047295 for two calls and remained
UNVERIFIED; the preceding HTTP400 had unknown actual cost and stayed unresolved.
These observations establish a working scoped path, not universal improvement.

The final release bout (`03dcffcefb0145008ee9ec12a32cd38f`) produced the requested
unknown-cost rule exactly and completed build/review in two calls: 2,016 input
and 247 output tokens, $0.0004506 reported cost (452 microUSD settled after
per-call rounding). Both original reply/wire digests were checked; offline replay
made zero calls and rejected changed task/input/checker bindings and raw bytes.
The role replies remain UNVERIFIED. Exact artifact readback is a narrow host
check; model review alone is not independent correctness evidence.

## Durable hard run budget

`--max-cost-microusd 50000` on Adversary's OpenRouter teamwork command binds one
run ID, objective digest and allowance to the state file's `.budget.sqlite3`
companion. Worker, review, repair and learning calls claim their bound action
before dispatch. Reopening the same action never sends it again. Raw vendor
bytes are durably retained beside the ledger before decoding or application.
Unknown outcomes/costs retain the liability hold; only a trusted matching
generation receipt can settle it. Existing estimates are a separate policy.

The current HTTP transport supplies no enforceable maximum liability, so this
hard-budget path still refuses before a live send. Synthetic transport tests
demonstrate the continuing $0.05 ledger, restart and concurrency behavior;
they do not establish a vendor bill guarantee. Estimated mode is explicitly
opt-in and never an automatic fallback from a hard ceiling. Default call
allowances are 32 for hard policy and 42 for estimated policy; each includes
repairs and the full Panel, not a fresh allowance per role.

Resume a saved OpenRouter run using a new state path:

```powershell
python -m adversary.entrypoints.cli teamwork resume --state bout.json --output continued.json --reason "Continue the original task"
```

Continuation reuses the saved model, financial policy, objective and ledger.
Completed captures recover without resending; unknown sends/costs stop until
explicit reconciliation. Removing the ledger, changing its binding or the
parent state refuses before credential resolution. Resume cannot reset a cap.

Ordinary task objectives preserve literal JSON examples. Research stage
profiles retain their own answer isolation. Unresolved schema references and
nonproductive cycles fail offline; productive recursive schemas remain usable.
Escaped lone surrogates produce a typed refusal with explicitly labelled invalid
completion bytes and separate original vendor-wire custody.

See the [migration execution plan](pfp_migration_and_integration_plan.md) for
installed-package verification, route controls and remaining exits.

For the exploratory formal-math and synthesis senders, see the
[accounted pilot runbook](pfp_pilot_matrix.md). They reuse this task-turn binding,
retain the exact vendor wire body, and pass only checked answers to their original
judges through one continuing provider allowance.

# WF1: one task, one typed answer

**Use this when:** you want one model response with a clear answer contract.
**Normal model calls:** one. **Math needed for this example:** integer addition.

**You will keep:** the task, the generated prompt, the actual reply and a check result.
The example below uses the current repository's pure PFP task-turn API.

For the automated runner, use [Install and run](Workflow-Running.md).
The walkthrough below remains a small manual API example.

## Before you start

Work from a checkout of this repository, using Python 3.12+:

```powershell
python -m pip install jsonschema==4.26.0
```

The model interface is yours: an IDE/chat interface or an already-accounted
provider integration. The following code makes **no model call**.

## 1. Prepare the task

Save this as `prepare_wf1.py` in the repository root and run `python prepare_wf1.py`.
It creates a fresh folder. Choose a different folder name for a new attempt.

```python
import json
from pathlib import Path
from pfp.domain.contracts.pfp_runtime import PfpPromptTemplate, PfpTaskPrompt
from pfp.use_cases.pfp_prompt import PreparePfpTaskTurnUseCase

folder = Path("runs/wf1-first")
folder.mkdir(parents=True, exist_ok=False)
spec = {
    "task_id": "wf1-first-sum",
    "attempt_id": "wf1-manual-1",
    "seed": "Calculate the exact sum of 17, 25, and -4.",
    "input": {"values": [17, 25, -4]},
    "answer_schema": {
        "type": "object",
        "properties": {"total": {"type": "integer"}},
        "required": ["total"],
        "additionalProperties": False,
    },
}
template = PfpPromptTemplate(
    "Complete the supplied finite task in one response. "
    "Use exact integer arithmetic. Return only the host's JSON contract. "
    "Make no tool-execution or authority claims.",
    "[USER PROMPT]", {},
)
task = PfpTaskPrompt(spec["task_id"], spec["seed"], spec["input"], spec["answer_schema"])
prompt = PreparePfpTaskTurnUseCase().execute(template, task, spec["attempt_id"])
for name, text in {
    "task.json": json.dumps(spec, indent=2),
    "system.txt": prompt.system,
    "user.json": prompt.user,
    "response_schema.json": json.dumps(prompt.response_schema, indent=2),
}.items():
    (folder / name).write_text(text, encoding="utf-8")
print(folder)
```

**Checkpoint:** the folder contains four files. The prompt contains inputs and
types; the host has not inserted the expected answer.

## 2. Get one response

Send `system.txt` as the system message and `user.json` as the user message
through your model interface. If it has only one text box, keep both labelled
sections in the same message; that is a different transport variant, which you
should record. Save the returned text **exactly** as `runs/wf1-first/reply.json`.

The host's contract supplies `task_id`, `attempt_id`, `input_sha256` and `answer`.
Copy the identifiers; do not ask the model to calculate a digest. Keep prose,
fences or extra fields in the raw reply if the model emits them: the checker
should see what it actually returned.

## 3. Check the actual reply

Save this as `check_wf1.py` beside the first script and run `python check_wf1.py`.

```python
import json
from pathlib import Path
from pfp.domain.contracts.pfp_runtime import PfpPrompt, PfpTaskPrompt
from pfp.infrastructure.task_turn import PreparedTaskTurn

folder = Path("runs/wf1-first")
spec = json.loads((folder / "task.json").read_text(encoding="utf-8"))
task = PfpTaskPrompt(spec["task_id"], spec["seed"], spec["input"], spec["answer_schema"])
prompt = PfpPrompt(
    (folder / "system.txt").read_text(encoding="utf-8"),
    (folder / "user.json").read_text(encoding="utf-8"),
    json.loads((folder / "response_schema.json").read_text(encoding="utf-8")),
)
turn = PreparedTaskTurn(task, prompt, "integer-sum-example-v1")

def check_sum(case, answer):
    correct = (
        type(answer) is dict and set(answer) == {"total"}
        and type(answer["total"]) is int
        and answer["total"] == sum(case["values"])
    )
    return correct, "Independent exact integer sum check."

judges = (("integer-sum-example-v1", check_sum),)
result = turn.check((folder / "reply.json").read_bytes(), judges=judges, require_checker=True)
with (folder / "check.json").open("x", encoding="utf-8") as handle:
    json.dump(result, handle, indent=2)
replayed = turn.replay(result, judges=judges, require_checker=True)
print(result["status"], result["failure_class"])
print("Rechecked saved bytes:", replayed["status"])
raise SystemExit(0 if result["status"] == "HOST_ACCEPTED" else 1)
```

`HOST_ACCEPTED` means the declared integer-sum check passed. A valid JSON shape
with an incorrect total must fail. The result is specific to this checker.

## What this example covers

It demonstrates a real PFP typed envelope, input binding, strict response
checking and checking saved bytes again. It is a **manual teaching recipe**,
not the full durable/budgeted historical runner. It does not seal a provider
invoice or independently protect all preparation files from later edits.
For another task, supply another independent checker and record its version.

## If it fails

Keep the reply and check result. A stale attempt ID means you mixed attempts.
Extra text or fields are a contract failure. A wrong total is a task failure.
See [Troubleshooting](Workflow-Troubleshooting.md) before requesting a new reply.

**Stop here** if this covers your need. Continue to [WF2](Workflow-WF2.md) when
you need explicit operation and repair records.

## Inspect the exact reference inputs

The [historical prepared examples](Workflow-Examples.md) include the actual
P* system message, user message and typed response contract for WF1.
Use them to see the full shape; generate new attempt bindings for a new run.

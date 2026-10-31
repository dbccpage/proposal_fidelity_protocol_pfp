# Start here: get one checked result

**Goal:** see a proposal, its check and a saved result without a paid model call.
You need Python 3.12+ and a checkout of this repository.

## 1. Run the small offline example

If you do not have the source yet, run:

```powershell
git clone https://github.com/dbccpage/proposal_fidelity_protocol_pfp.git
cd proposal_fidelity_protocol_pfp
```

From the repository root:

```powershell
python -m pip install -e .
python -m pfp_lab.cli.main packs
python -m pfp_lab.cli.main run --pack paper-005-worked-session --receipt first-receipt.json
python -m pfp_lab.cli.main verify first-receipt.json
```

The pack supplies example proposals. They are **fixtures**, not fresh LLM
responses. The independent checker runs and the receipt can be replayed.
The `verify` command should exit successfully.

`VALID` means the receipt replays faithfully. Its trace can include refused
proposals or a final nonzero defect; it does not mean every proposal passed.

**Keep:** `first-receipt.json`. You can stop here.

## 2. Use your own model

Go to [WF1](Workflow-WF1.md). It shows how to prepare a typed task with the
current `pfp` API, send the generated prompt through your existing model
interface, and check the actual reply.

The checker does not need another model. A model's statement that it checked
its answer is still part of the proposal.

## 3. Choose the result you need

| You have… | Your next step |
| --- | --- |
| A valid receipt for the example pack | Try WF1 with your own response. |
| A JSON reply that parses | Check its declared shape, binding and task result. |
| A reply that fails a check | Keep it and use [Troubleshooting](Workflow-Troubleshooting.md). |
| An answer with no independent task checker | Report it as unverified; choose what you can actually check. |

## If you get interrupted

Write down the run folder, the workflow/recipe version and the last completed
step. Keep the actual reply even if it failed. Resume by checking saved data;
do not silently buy another model response.

## Choose another path

[Choose a workflow](Workflows.md) · [What the words mean](Workflow-Glossary.md)
· [Current integration status](Workflow-Integration-Status.md)

# WF50: Repo hygiene

**Status:** runnable. `hygiene.py` and its tests run offline; the agent workflow
`workflow.js` needs Claude Code. WF50 is a maintenance workflow, not a workflow
family, so `python -m pfp_core.workflow_families` does not list it.

**Folder:** [`workflows/wf50_repo_hygiene/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf50_repo_hygiene)

**What it is for:** keeping this repository tidy. It finds files and folders
whose names break the naming rule, renames them and fixes every reference,
deletes junk, refreshes the workflow documentation and writes a short
[gap report](gap_report.md).

**The rule:** every file and folder name is lowercase snake_case, except
`README.md` and the names a tool requires. Each exception and its reason is in
[`naming_policy.json`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/workflows/wf50_repo_hygiene/naming_policy.json).

## Run it offline

No model call and no cost. From the repository root:

```powershell
python -m pytest workflows/wf50_repo_hygiene -q
python workflows/wf50_repo_hygiene/hygiene.py survey --out workflows/wf50_repo_hygiene/run/plan.json
python workflows/wf50_repo_hygiene/hygiene.py residue workflows/wf50_repo_hygiene/run/plan.json
```

`survey` lists every name that breaks the rule and proposes a new one. `apply
PLAN [--dry-run]` moves the files and rewrites references in every tracked text
file; it never edits `atlas/archive/` and never renames inside a hash-pinned bundle.
`residue PLAN` shows old names still mentioned anywhere. `rebaseline --reason
TEXT PATH...` re-pins listed governed files after a mechanical edit. `run/` is
ignored by git.

## The check

- The naming rule: `survey` must find nothing that is not an exemption.
- `residue`: no old name is left anywhere after a rename.
- The custody test
  `workflows/wf53_industry_replacement_benchmark/tests/test_industry_replacement.py::test_branch_touches_only_allowed_paths`:
  no file pinned in `dag/file_inventory.json` may change without its row being
  handled on purpose.
- After each job, the full test suites and `python -m governance.tools.checker check`
  show no new failure against `main`.

## The agent workflow

`workflow.js` runs three kinds of agent in Claude Code: a survey that reports
facts, reviewers that check the survey and write one prompt per job (deletions,
renames, docs) plus the gap report, and one executor per job that carries out
its prompt and commits. Each job becomes its own pull request. Not tested
offline: the agent steps themselves.

## Code

[`hygiene.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/workflows/wf50_repo_hygiene/hygiene.py)
· [`test_hygiene.py`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/workflows/wf50_repo_hygiene/test_hygiene.py)
· [`naming_policy.json`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/workflows/wf50_repo_hygiene/naming_policy.json)
· [`workflow.js`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/workflows/wf50_repo_hygiene/workflow.js)

Back to [Workflows](workflows.md).

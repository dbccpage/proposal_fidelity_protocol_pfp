# WF50: Repo hygiene

**What it is for:** keeping this repository tidy. It finds files and folders
whose names break the naming rule, renames them and fixes every reference,
deletes junk, refreshes the workflow documentation and writes a short gap report.

**Status:** runnable: `hygiene.py` and its tests run offline; the agent workflow
`workflow.js` needs Claude Code. It is not a workflow family, so
`python -m pfp_core.workflow_families` does not list it.

**Run it offline** (no model call, no cost), from the repository root:

```powershell
python -m pytest workflows/wf50_repo_hygiene -q
python workflows/wf50_repo_hygiene/hygiene.py survey --out workflows/wf50_repo_hygiene/run/plan.json
python workflows/wf50_repo_hygiene/hygiene.py residue workflows/wf50_repo_hygiene/run/plan.json
```

**The check:** the naming rule in [naming_policy.json](naming_policy.json)
(`survey` lists every name that breaks it), `residue` (no old name left
anywhere) and the custody test
`benchmarks/industry_replacement/tests/test_industry_replacement.py::test_branch_touches_only_allowed_paths`
(no file pinned in `dag/file_inventory.json` changes unrecorded).

**Code:** [hygiene.py](hygiene.py), [test_hygiene.py](test_hygiene.py),
[naming_policy.json](naming_policy.json), [workflow.js](workflow.js). Wiki page:
[workflow_wf50](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/workflow_wf50).

**Kind:** maintenance workflow. **Builds on:** nothing.

**Rule it enforces:** every file and folder name is lowercase snake_case, except
`README.md` and the names a tool requires. The exceptions and the reason for each
are in [naming_policy.json](naming_policy.json).

## How it works

Three kinds of agent, each doing one job:

1. **Survey (Sonnet).** Eight agents each read one slice of the repo and report
   facts: junk with evidence and its consumers, renames that must not happen,
   renames that need a code change, and names that must not appear outside
   `papers/`. Four more agents list weaknesses in PFP, PCIV, EIS and operads,
   and one lists the state of every workflow's documentation.
2. **Review (Opus).** Four agents check the survey claims themselves, settle
   the final lists and each write one long, self-contained prompt: deletions,
   renames, docs. The fourth writes the gap report. Reviewers do not edit the
   repository.
3. **Execute (Fable).** One agent per job carries out its prompt, runs the
   tests and the governance checker, and commits. Jobs run one at a time, in
   order, and each becomes its own pull request.

The renames themselves are done by a deterministic script, not by an agent
editing thousands of files:

| Command | What it does |
| --- | --- |
| `python workflows/wf50_repo_hygiene/hygiene.py survey --out run/plan.json` | List every name that breaks the rule and propose a new one |
| `python workflows/wf50_repo_hygiene/hygiene.py apply run/plan.json [--dry-run]` | Move the files and rewrite references in every tracked text file |
| `python workflows/wf50_repo_hygiene/hygiene.py residue run/plan.json` | Show old names still mentioned anywhere, for hand fixes |
| `python workflows/wf50_repo_hygiene/hygiene.py rebaseline --reason TEXT PATH...` | Re-pin only the listed governed files after a mechanical edit |

`apply` never edits files under `papers/` and never renames anything inside a
hash-pinned bundle (a folder holding `MANIFEST.sha256` or `SHA256SUMS`).

## Run the agent workflow

From the repository root, in Claude Code:

1. `python workflows/wf50_repo_hygiene/hygiene.py survey --out workflows/wf50_repo_hygiene/run/plan.json`
2. Run [workflow.js](workflow.js) with `{"mode": "plan"}`. It writes
   `run/prompt_deletions.md`, `run/prompt_renames.md`, `run/prompt_docs.md` and
   `run/gap_report.md`.
3. Read the prompts. Then run it with `{"mode": "execute", "job": "deletions"}`,
   open a PR, merge, and repeat for `renames` and `docs`.

`run/` is ignored by git; it holds one run's working files.

## After each job

`python -m pytest workflows/wf50_repo_hygiene -q` tests the naming and rewrite
rules. Then run the full test suites, `python -m governance.tools.checker check`
(no new failures against `main`) and `hygiene.py residue`.

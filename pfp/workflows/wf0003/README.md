# WF3 automated runner

Run `python -m pfp.workflows.wf0003 --help` or `pfp-wf3 --help`.
This folder owns its task contract, workflow metadata, runner and tests.
It shares read-only codecs and the existing PFP provider/accounting boundary;
run folders and mutable attempt state are never shared with another workflow.

- [Workflow guide](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-WF3)
- [Installation, exact commands and budgets](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-Running)
- [Preserved historical measurements](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-Results)

Install from the repository root with `python -m pip install ".[workflows]"`.
Preparing and replaying make no model calls. A `run` may charge OpenRouter;
the admitted allowance is at most 4,999 micro-USD and uses estimated accounting.
No automatic retries. Keep failures and use fresh folders for new attempts.

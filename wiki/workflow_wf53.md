# WF53: Industry replacement benchmark

**Status:** runnable offline (policy verification only). The live campaign is prepared and not run, so there are no model results yet.

**Folder:** [`workflows/wf53_industry_replacement_benchmark/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/workflows/wf53_industry_replacement_benchmark)

**What it is for:** comparing six ways of running a coding model on four engineering tasks: the plain task; a stack of industry skills and rules; a coder-reviewer loop; the plain task with public checks; the industry stack with a CI gate; and PFP with two-signal regulation.

**The check:** each task has a public host check, and a sealed grader that runs only after outputs are frozen. Candidates run in a throwaway sandbox (container or Vercel Sandbox).

**Run it offline:**

```powershell
python -m pytest pfp_core workflows/wf53_industry_replacement_benchmark -q
python workflows/wf53_industry_replacement_benchmark/run_offline_matrix.py
```

**What it does not show yet:** anything about live accuracy, tokens, cost or time.

Builds on [WF12](workflow_wf12.md) and [WF14](workflow_wf14.md). Formerly `benchmarks/industry_replacement/`.

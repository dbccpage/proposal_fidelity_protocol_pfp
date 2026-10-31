# Standalone automated PFP workflows

Five segregated workflow folders, one canonical provider/accounting boundary.
Install `python -m pip install ".[workflows]"` from the repository root.

| Folder | Contract | Maximum normal calls |
| --- | --- | ---: |
| `wf0001` | Basic P*, one typed answer | 1 |
| `wf0002` | Full slots and all emitted operad/DDC occurrences | 1 |
| `wf0003` | Screen/freeze mining, then one solver | 2 |
| `wf0004` | One miner, five simultaneous solvers and LGGR | 6 |
| `wf0005` | Full checked PFP packet rewrite, then WF4 structure | 6 |

Use [the runnable guide](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-Running).
The installed console commands are `pfp-wf1` through `pfp-wf5`.

Shared task custody lives in `pfp.infrastructure.workflow_runtime`; atomic
batch admission extends the existing estimated ledger in `workflow_accounting`.
Provider, LGGR and ROP source owners remain under `ops/`; packaging maps their
existing logical `adversary`, `operations` and `governance.domain` imports.
No provider transport is copied into a workflow folder.

The default/maximum allowance is $0.004999 per run, including all its phases.
Reservations use estimated rates, 2× headroom and the 80% stop threshold.
It is not a vendor-enforced cap. Unknown cost retains liability and blocks dispatch.
Failed attempts and immutable source identity remain part of custody.

Historical captures are not rewritten to match new package identities.
The baseline is reused from the original experiment; migration tests use fixtures,
not another paid baseline or fresh model performance measurements.

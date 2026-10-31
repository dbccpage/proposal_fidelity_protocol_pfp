# Exact prompts and contracts

**Read the short guide first.** This page is for adapting or auditing a workflow.
These files are unchanged October 28 reference inputs, not newly measured runs.

| Role | Exact prepared files |
| --- | --- |
| `seed-only` | [Open files](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/docs/workflows/examples/seed-only) |
| `wf1-solver` | [Open files](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/docs/workflows/examples/wf1-solver) |
| `wf2-solver` | [Open files](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/docs/workflows/examples/wf2-solver) |
| `wf3-miner` | [Open files](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/docs/workflows/examples/wf3-miner) |
| `wf3-solver` | [Open files](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/docs/workflows/examples/wf3-solver) |
| `wf4-miner` | [Open files](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/docs/workflows/examples/wf4-miner) |
| `wf4-agent-1` | [Open files](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/docs/workflows/examples/wf4-agent-1) |
| `wf5-miner` | [Open files](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/docs/workflows/examples/wf5-miner) |
| `wf5-agent-1` | [Open files](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/docs/workflows/examples/wf5-agent-1) |

Each available folder contains `system_prompt.txt`, `user_prompt.txt`,
`response_schema.json` and `task.json` as retained by its historical runner.
Some roles do not have all four files. The
[file manifest](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/blob/main/docs/workflows/examples/manifest.json)
lists exactly what is present and its original SHA-256.

## Adapt an example safely

1. Start with your public seed, inputs and output contract. Keep the expected answer host-only.
2. Generate new task/attempt bindings; do not reuse the digest or IDs in these examples.
3. Declare your independent checker, prompt/profile version and budget before dispatch.
4. Save the actual reply unchanged, then check it. Keep a failed attempt as its own result.

The historical compact WF3–WF5 replies rely on host-bound public facts and
frozen profile references. Their schema is not a stand-alone correctness test:
you also need the grounding, provenance, operation screening, global checks
and accounting described by the corresponding recipe. The miner's provider
projection may be simpler than its exact host schema.

The [raw replies](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/docs/workflows/evidence/raw)
include failures. Treat them as untrusted experimental output.
This selected export does not include all old runtime dependencies or a
portable provider/accounting replay system.

For a current-repository example that you can run directly, use [WF1](Workflow-WF1.md).
See [integration status](Workflow-Integration-Status.md) before choosing an adapter.

[Workflow contracts](Workflow-Contracts.md) · [Results](Workflow-Results.md)

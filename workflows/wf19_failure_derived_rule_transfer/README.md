# WF19: Failure-derived rule transfer

**Status:** proposal: no runner and no run yet. **Kind:** experiment design. **Builds on:** [WF12](../wf12_mechanism_control_arms/README.md), [WF14](../wf14_immune_failure_classification/README.md).

**Goal:** A rule that improves held-out acceptance without new false positives.

## How it works

1. Compare baseline, typed-witness and failure-derived rule prompts
2. Use disjoint held-out cases
3. Allow at most two stages; checker disagreement stops the run
4. A rule stays a candidate until transfer and self-tolerance are measured

## The check

Host check: original domain judges; disagreement halts.

- `transfer gain = acc(rule, held-out) - acc(baseline, held-out) on disjoint items`
- `a rule is admitted only if gain > 0 and self-tolerance holds (WF14)`

## Where it comes from

Sources: 0000192-0000198.

Seven partially executed learning pilots over challenge families A-F plus harness tests; reference solver outputs are controls, never model responses.

## Pilots in this folder

Model experiments for this workflow, moved here on 2026-11-06 from the research repository pilot estate (private names and local paths replaced). Most need a model runtime that is not published here; their recorded inputs, replies and checks are kept as data.

- [`pilots/challenge_suite/`](pilots/challenge_suite/) — pilot material
- [`pilots/evidence/`](pilots/evidence/) — recorded campaign evidence (raw replies, ledgers, receipts)

## Team

Pattern `research_cell`: deep_researcher ×1 (opus); adversary ×1 (fable); coder ×1 (sonnet); host_checker ×1 (none).

Boost: when rule shows no gain: one revised rule from opus; otherwise the rule is retired (limit 1).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf19) · [machine-readable entry](../dag/workflow_dag.json)

# WF21: Structural prompt rewriting

**Status:** proposal: no runner and no run yet. **Kind:** procedure extension. **Builds on:** [WF5](../wf05_checked_rewrite/README.md).

**Goal:** Rewrites that attach hints or encodings without touching protected bytes.

## How it works

1. Represent the prompt as an attributed graph with protected task, constraint and output nodes
2. Apply a rule only through an explicit injective match
3. Check protected bytes are unchanged
4. Refuse a rewrite whose normal form drops the question

## The check

Host check: byte-preservation and exact judge.

- `double-pushout rewrite: L <- K -> R with injective match m: L -> G; the pushout complement must exist (gluing condition)`
- `protected invariant: bytes(protected(G')) = bytes(protected(G))`

## Where it comes from

Sources: 0000028, 0000030, 0000050, acset_prompt_rewriting, acset_cochain_rewriting.

Offline pilots: grammar selection preserving bytes (28), a normal form that loses the question (30), no substitution inside substituted data (50), and finite ACSet/DPO rewriting with an exact judge.

## Pilots in this folder

Model experiments for this workflow, moved here on 2026-11-06 from the research repository pilot estate (private names and local paths replaced). Most need a model runtime that is not published here; their recorded inputs, replies and checks are kept as data.

- [`pilots/acset_cochain_rewriting/`](pilots/acset_cochain_rewriting/) — Finite ACSet/DPO cochain rewriting v001
- [`pilots/acset_prompt_rewriting/`](pilots/acset_prompt_rewriting/) — ACSets and DPO prompt rewriting pilot
- [`pilots/optional_rewrite_backends/`](pilots/optional_rewrite_backends/) — Optional Julia and DSPy demonstrations

## Team

Pattern `red_team_pair`: coder ×1 (sonnet); adversary ×1 (run_f); host_checker ×1 (none).

Boost: when meaning-loss case found: add it as a refusal test (limit 0).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf21) · [machine-readable entry](../dag/workflow_dag.json)

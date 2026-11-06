# WF13: Exact-domain capsule battery

**Status:** proposal: no runner and no run yet. **Kind:** task preset. **Builds on:** [WF1](../wf01_typed_answer/README.md), [WF7](../wf07_typed_refusal/README.md).

**Goal:** One checked answer or refusal per domain capsule.

## How it works

1. One catalog challenge becomes one capsule
2. A domain checker is registered before dispatch
3. One reply or typed refusal per capsule
4. Results stay per domain; no cross-domain average is claimed

## The check

Host check: per-domain registered checker.

- `stabilizer codes: generators commute iff their symplectic product is 0 mod 2`
- `U(1) anomaly freedom: sum_i q_i = 0 and sum_i q_i^3 = 0 over the declared charges`
- `Regge deficit: epsilon = 2 pi - sum of dihedral angles at a hinge`
- `commutator [g, h] = g^-1 h^-1 g h, checked in the declared finite group`

## Where it comes from

Sources: 0000065-0000114, 0000177, 0000176, 0000178, 0000187.

Fifty planned single-capsule pilots, one per catalog challenge, each naming a domain checker id; none was dispatched.

## Team

Pattern `solo`: coder ×1 (sonnet); deep_researcher ×1 (run_o); host_checker ×1 (none).

Boost: when checker rejects: one run_o attempt with the checker message (limit 1).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf13) · [machine-readable entry](../dag/workflow_dag.json)

# WF17: Witnessed-difference programme

**Status:** proposal: no runner and no run yet. **Kind:** task preset. **Builds on:** [WF10](../wf10_local_to_global_obstruction_certificate/README.md), [WF11](../wf11_dual_certificate_synthesis/README.md).

**Goal:** Each claimed difference has a checked witness and each equivalence a checked certificate.

## How it works

1. State two artifacts and the claimed difference or equivalence
2. Require a witness for a difference and a certificate for an equivalence
3. Pair every theorem with countermodels
4. Host checks witnesses on finite instances

## The check

Host check: witness / countermodel checker.

- `behavioral equivalence: a bisimulation relation B with (p, q) in B and matching transitions`
- `Fenchel-Rockafellar: inf_x f(x) + g(Ax) = sup_y -f^*(A^T y) - g^*(-y) under the stated qualification`
- `Cech gluing obstruction lives in the first Cech cohomology of the cover`

## Where it comes from

Sources: 0000170-0000187.

Eighteen planned capsules (W01-W18): behavioral equivalence, cochain quotients, Cech gluing, Fenchel-Rockafellar duality, LGGR I-VI, countermodels CE1-CE5; none dispatched.

## Team

Pattern `research_cell`: deep_researcher ×2 (run_o); adversary ×1 (run_f); coder ×2 (sonnet); host_checker ×1 (none).

Boost: when countermodel found: claim is narrowed or withdrawn; run_o restates it once (limit 1).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/workflow_dag#wf17) · [machine-readable entry](../dag/workflow_dag.json)

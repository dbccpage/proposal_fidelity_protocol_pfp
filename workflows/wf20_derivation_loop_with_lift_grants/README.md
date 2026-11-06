# WF20: Derivation loop with lift grants

**Status:** proposal: no runner and no run yet. **Kind:** procedure extension. **Builds on:** [WF9](../wf09_bounded_check_and_repair/README.md), [WF10](../wf10_local_to_global_obstruction_certificate/README.md), [WF19](../wf19_failure_derived_rule_transfer/README.md).

**Goal:** Discharge the named obligations or stop with a typed record at the loop limit.

## How it works

1. Proposal against named obligations
2. Lift grant: the host licenses which higher structure may be used
3. Witness check on the exact finite control
4. Negative control
5. Learning refinement for the next loop; stop at the loop limit

## The check

Host check: finite witness controls; proofs need independent review.

- `loop state (P_t, G_t, W_t); P_{t+1} = refine(P_t, residual_t) with t <= 5`
- `metric/cochain bridge: additive curvature and metric Regge holonomy are checked separately`
- `terminal policy: halt on certificate, on budget, or on the loop limit, whichever comes first`

## Where it comes from

Sources: 0000199-0000203.

Each pilot ran five loops: five provider trials and twenty host stages, capped at USD 0.05, 120,000 tokens and 180 s; analytical status stays unverified until independent proof review.

## Pilots in this folder

Model experiments for this workflow, moved here on 2026-11-06 from the research repository pilot estate (private names and local paths replaced). Most need a model runtime that is not published here; their recorded inputs, replies and checks are kept as data.

- [`pilots/derivation_dag_pfp_staged_benchmark.py`](pilots/derivation_dag_pfp_staged_benchmark.py) — one-shot versus staged derivation certificates on slices of the finite-QM derivation graph
- [`pilots/evidence/`](pilots/evidence/) — recorded campaign evidence (raw replies, ledgers, receipts)
- [`pilots/finite_qm_derivation_pfp/`](pilots/finite_qm_derivation_pfp/) — operad mining, prompt compilation and gate checks for a multi-stage finite-QM derivation campaign
- [`pilots/finite_qm_derivation_pfp/theory_of_finite_qm_campaign/`](pilots/finite_qm_derivation_pfp/theory_of_finite_qm_campaign/README.md) — that campaign's prompt programme, model ladder, batch runs and cohort scores, moved from the finite-QM repository
- [`pilots/pilot_0000199/`](pilots/pilot_0000199/) — pilot_0000199: Corrected causal refinement theorem
- [`pilots/pilot_0000200/`](pilots/pilot_0000200/) — pilot_0000200: Current from microscopic projection residual dynamics
- [`pilots/pilot_0000201/`](pilots/pilot_0000201/) — pilot_0000201: Typed transport and categorical relational spine
- [`pilots/pilot_0000202/`](pilots/pilot_0000202/) — pilot_0000202: Separate additive curvature from metric Regge holonomy
- [`pilots/pilot_0000203/`](pilots/pilot_0000203/) — pilot_0000203: Exact obstruction certificate and operational halting conditions
- [`pilots/relational_spacetime/`](pilots/relational_spacetime/) — Relational spacetime derivation pilots

## Team

Pattern `research_cell`: deep_researcher ×1 (opus); adversary ×1 (fable); coder ×1 (sonnet); host_checker ×1 (none).

Boost: when witness check fails twice: next loop starts from the adversary's counterexample (limit 1).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf20) · [machine-readable entry](../dag/workflow_dag.json)

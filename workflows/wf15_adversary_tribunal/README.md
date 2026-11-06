# WF15: Adversary tribunal

**Status:** proposal: no runner and no run yet. **Kind:** procedure extension. **Builds on:** [WF4](../wf04_five_agents_lggr/README.md), [WF14](../wf14_immune_failure_classification/README.md).

**Goal:** A verdict that the finite check supports, with both sides frozen first.

## How it works

1. Prosecutor and defender submit independently; submissions are frozen
2. Neither sees the other before freezing
3. The host checks each claim on the finite model
4. Verdict comes only from the check; rhetoric is not evidence

## The check

Host check: finite model checker.

- `Kripke model M = (W, R, V); M, w |= box phi iff phi holds at every R-successor of w`
- `argument acceptance: grounded extension of the attack graph, computed by the host`
- `finite predicate example: sum(left) <= sum(right) on 1..16 bounded integers`

## Where it comes from

Sources: 0000035, 0000135-0000144.

Pilot 35 freezes role submissions and checks them separately (118 tests, 17 mutations); 135-144 are planned tribunal capsules (e.g. modal model checking).

## Pilots in this folder

Model experiments for this workflow, moved here on 2026-11-06 from the research repository pilot estate (private names and local paths replaced). Most need a model runtime that is not published here; their recorded inputs, replies and checks are kept as data.

- [`pilots/pilot_0000135/`](pilots/pilot_0000135/) — pilot_0000135 — C091 Ontological Arguments under Modal Model Checking
- [`pilots/pilot_0000136/`](pilots/pilot_0000136/) — pilot_0000136 — C092 Trinitarian Formulations under Different Identity Theories
- [`pilots/pilot_0000137/`](pilots/pilot_0000137/) — pilot_0000137 — C093 Consistency of Divine-Attribute Theories
- [`pilots/pilot_0000138/`](pilots/pilot_0000138/) — pilot_0000138 — C094 Deontic Paradox Formalizations
- [`pilots/pilot_0000139/`](pilots/pilot_0000139/) — pilot_0000139 — C095 Abstract Argumentation over Encoded Debates
- [`pilots/pilot_0000140/`](pilots/pilot_0000140/) — pilot_0000140 — C096 Diagonal Lemma and Quines
- [`pilots/pilot_0000141/`](pilots/pilot_0000141/) — pilot_0000141 — C097 Liar-Type Sentences in Paraconsistent Semantics
- [`pilots/pilot_0000142/`](pilots/pilot_0000142/) — pilot_0000142 — C098 Cut Elimination in Sequent Calculus
- [`pilots/pilot_0000143/`](pilots/pilot_0000143/) — pilot_0000143 — C099 Ehrenfeucht-Fraisse Games on Finite Structures
- [`pilots/pilot_0000144/`](pilots/pilot_0000144/) — pilot_0000144 — C100 Metatheory of the Engine Itself: AuthorityEffect None Is Preserved

## Team

Pattern `tribunal`: prosecutor ×1 (fable); defender ×1 (opus); coder ×1 (sonnet); host_checker ×1 (none).

Boost: when both submissions fail the check: one fresh opus round per side with the checker output (limit 1).

## Recorded variations

| Setting | Values | Outcome | Status | Source |
| --- | --- | --- | --- | --- |
| role omitted | each of six roles in turn | named failure label per omission | code | P004(role) §3 |

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf15) · [machine-readable entry](../dag/workflow_dag.json)

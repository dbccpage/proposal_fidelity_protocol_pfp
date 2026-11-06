# WF16: Substrate crosswalk

**Status:** proposal: no runner and no run yet. **Kind:** task preset. **Builds on:** [WF5](../wf05_checked_rewrite/README.md), [WF10](../wf10_local_to_global_obstruction_certificate/README.md).

**Goal:** A translation that preserves every declared relation, with alternatives recorded.

## How it works

1. Declare source and target substrates (e.g. prose, Lean, finite tables)
2. Translate generators and relations
3. Check that relations are preserved on the target
4. Record every non-unique choice

## The check

Host check: relation-preservation checker (Lean or finite tables).

- `a crosswalk F: C -> D is accepted iff F(r) holds in D for every relation r of C`
- `non-uniqueness: F and F' both preserve relations yet differ on a generator; both are recorded`

## Where it comes from

Sources: 0000145-0000169.

Twenty-five planned capsules (G01-G25), e.g. reading non-uniqueness in Lean; none dispatched.

## Pilots in this folder

Model experiments for this workflow, moved here on 2026-11-06 from the research repository pilot estate (private names and local paths replaced). Most need a model runtime that is not published here; their recorded inputs, replies and checks are kept as data.

- [`pilots/pilot_0000145/`](pilots/pilot_0000145/) — pilot_0000145 — G01 Reading F Non-Uniqueness in Lean
- [`pilots/pilot_0000146/`](pilots/pilot_0000146/) — pilot_0000146 — G02 The Cut Census Formula 2^(n-2)
- [`pilots/pilot_0000147/`](pilots/pilot_0000147/) — pilot_0000147 — G03 G4 as a Replayable Finite Check
- [`pilots/pilot_0000148/`](pilots/pilot_0000148/) — pilot_0000148 — G04 X-3: Is the First-Demand Index Isomorphism-Invariant
- [`pilots/pilot_0000149/`](pilots/pilot_0000149/) — pilot_0000149 — G05 X-1: A Decision Procedure for Demand
- [`pilots/pilot_0000150/`](pilots/pilot_0000150/) — pilot_0000150 — G06 NS-10: State-Change Counts on Commuting Squares
- [`pilots/pilot_0000151/`](pilots/pilot_0000151/) — pilot_0000151 — G07 Branch Fan Widths under mu2
- [`pilots/pilot_0000152/`](pilots/pilot_0000152/) — pilot_0000152 — G08 Alpha Engine: Live Injections for G10, G13 and G14
- [`pilots/pilot_0000153/`](pilots/pilot_0000153/) — pilot_0000153 — G09 Alpha Engine: Python Driver Refinement for One Fold
- [`pilots/pilot_0000154/`](pilots/pilot_0000154/) — pilot_0000154 — G10 The Symbol Game as an Alpha Engine Proposal Source
- [`pilots/pilot_0000155/`](pilots/pilot_0000155/) — pilot_0000155 — G11 Wiring the m114 Solver Adapter into the Search Policies
- [`pilots/pilot_0000156/`](pilots/pilot_0000156/) — pilot_0000156 — G12 Prop Wrappers for the Parked Isomorphism Modules
- [`pilots/pilot_0000157/`](pilots/pilot_0000157/) — pilot_0000157 — G13 Genesis Crosswalk: Binding the Three Native Ports
- [`pilots/pilot_0000158/`](pilots/pilot_0000158/) — pilot_0000158 — G14 OB-1: Searching for an Endogenous Demand Generator
- [`pilots/pilot_0000159/`](pilots/pilot_0000159/) — pilot_0000159 — G15 Unboundedness of Engine Driver Paths
- [`pilots/pilot_0000160/`](pilots/pilot_0000160/) — pilot_0000160 — G16 Tied-Minima Census Beyond Two Items and Arity Two
- [`pilots/pilot_0000161/`](pilots/pilot_0000161/) — pilot_0000161 — G17 Second Derivation: Challenges 3 to 5
- [`pilots/pilot_0000162/`](pilots/pilot_0000162/) — pilot_0000162 — G18 X-6: The Remaining Definability Census Rows
- [`pilots/pilot_0000163/`](pilots/pilot_0000163/) — pilot_0000163 — G19 NS-5: A Proof-Relevant Cell Calculus
- [`pilots/pilot_0000164/`](pilots/pilot_0000164/) — pilot_0000164 — G20 H3V7N5QF: Closed Forms for Shortest-Sequence Counts
- [`pilots/pilot_0000165/`](pilots/pilot_0000165/) — pilot_0000165 — G21 H3V7N5QF: A Reachability Criterion for C-R2
- [`pilots/pilot_0000166/`](pilots/pilot_0000166/) — pilot_0000166 — G22 H3V7N5QF: Lower Bounds for A-Perform Changes
- [`pilots/pilot_0000167/`](pilots/pilot_0000167/) — pilot_0000167 — G23 H3V7N5QF: Choice-Free Reproofs
- [`pilots/pilot_0000168/`](pilots/pilot_0000168/) — pilot_0000168 — G24 Seed-Edit Ablation Bench for the Four Holes
- [`pilots/pilot_0000169/`](pilots/pilot_0000169/) — pilot_0000169 — G25 Genesis as Omega Engine Foundation: A Checked Crosswalk

## Team

Pattern `research_cell`: coder ×1 (sonnet); deep_researcher ×1 (opus); adversary ×1 (fable); host_checker ×1 (none).

Boost: when Lean or table check fails: opus repairs the encoding from the error (limit 2).

More: [Workflow DAG on the wiki](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-DAG#wf16) · [machine-readable entry](../dag/workflow_dag.json)

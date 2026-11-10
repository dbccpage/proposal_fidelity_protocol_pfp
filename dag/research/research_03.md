# Research 03: protected prompt evolution with bounded selection

Status: proposed, not implemented or evaluated. Repository baseline: `8050c66900899771766f33e8f5fdd200b7dd9120`.

This report proposes three PCIV/PFP/EIS/OPERADS workflows. No model API was called, the public seed was not solved, and no private evaluator material was accessed. Only the public seed's hash was read: `9941ab91f8e6b6637e49bb364cc0e6451788dd96442afcdb7f7024de042500a7`. The original file was not changed.

The full typed stages, mathematical premises, bounded instructions, falsifiers, ablations and cost reservations are in [research_03.json](research_03.json).

## Evidence and boundary

[Promptbreeder](https://proceedings.mlr.press/v235/fernando24a.html) is a primary precedent for prompt populations, mutation and training-set fitness. Its evolving mutation policies differ from the frozen two-call controllers proposed here. [Dwork et al.](https://arxiv.org/abs/1506.02629) explain why adaptive reuse of evaluation feedback can overfit the evaluation set; this report does not implement their specialized holdout-reuse mechanism.

A fixed policy can still adapt within an item. Here its grammar, transition table, public detectors, tie rule and call limit are committed before target responses. Choosing subsequent prompts after seeing this target's trusted score is a separate exploratory activity. Repeated fresh calls on one seed do not establish transfer to new tasks. No private score, diagnostic, key-derived hint or selected example enters an online stage.

PCIV's actual sources impose concrete implementation constraints:

- `forge.py` checks protected byte edits but does not relocate spans or establish semantic preservation. `lamarckian_loop.py:203-217` has the audited offset bug for preceding edits. Keep the seed in a separate immutable message and mutate wrapper artifacts only.
- `fitness.py:230-273` defines its numeric converter inside the pair loop, so singleton selection fails. Its two-metric API also does not supply the three-coordinate selectors below. Use a separately specified and validated exact comparator; no fix is claimed here.
- `genealogy.py:101-143` requires named sealed edges and rejects cycles; `causal_witness.py:22-44` binds a hash to supplied declarations. Host-captured transformation replay is additional evidence, not a consequence of the seal.
- `models.py:365-373` distinguishes execution occurrences from genomes. Re-running one wrapper is not another mutation.
- `research_selection.py` consumes private-pass metrics and belongs after output freeze. It cannot be reused as an online prompt-selection oracle.
- The systems audit records silent event-log disk failure and order-dependent taint. Durable readback and independently validated ancestry handling remain prerequisites.
- PFP's answer-free feedback pattern, EIS's explicit detector limits, and OPERADS's colour-slot checks are useful components. None certifies the final analytic answer.

## Three workflows

| ID | Mechanism | Model stages | Conditional maximum |
| --- | --- | --- | --- |
| R03-I01 | Frozen sibling wrappers; exact selection on public artifact proxies | Two independent answer requests, 3,000 tokens each | USD 0.050 |
| R03-I02 | One public-failure repair; replayable parent/child lineage | 2,700-token draft; at most one 1,600-token patch | USD 0.0435 |
| R03-I03 | Typed scaffold evolution before solving | 900-token plan; 3,100-token solution | USD 0.040 |

These amounts assume input at most USD 0.000001/token, output at most USD 0.000005/token, zero additional metered fees, and a USD 0.01 reserve. They are conditional admission thresholds, not current prices. Every execution requires current tariff metadata, actual input bounds, caps covering billable reasoning, and a shared worst-case reservation of at most USD 0.10. These are separate run envelopes; the table does not authorize a campaign or aggregate spend.

**R03-I01 — Precommitted sibling wrappers.** Freeze a dependency-first and a branch-first wrapper before either response. Each request contains identical untouched seed bytes, and neither response sees its sibling. Public checks produce exact integers for structural coverage, public defects and generated tokens. Compute the nondominated set, then apply the declared lexicographic preference. Freeze both responses and both costs, even when only one is selected. The hypothesis is improved within-item completeness and blinded score compared with two samples of the same scaffold. The key falsifier is selection regret: the public gate can repeatedly prefer the mathematically weaker answer. Coverage and detector agreement are proxies, never renamed correctness.

**R03-I02 — One-step public-failure repair.** Generate a draft, then map public artifact-local failures through a frozen neutral instruction table. The one optional repair call returns a patch over stable section IDs. The host records the exact observation, wrapper edit, parent request and child request, rechecks affected dependencies, and selects a nonregressing artifact using fixed public criteria. No failures means a host no-op and no second call. No third call exists. Whole-answer critique, generic feedback and ungated patches are distinct ablations. This tests bounded adaptation on the item; it does not establish learned transferable repair rules.

**R03-I03 — Typed scaffold evolution.** A small planning call emits at most three DAGs using a frozen operation grammar. Plans contain operation IDs and obligation references, not mathematical answers or new assumptions. The host rejects cycles, missing requested sinks, type mismatches and duplicate check credit. It compiles valid scaffolds from fixed prose templates and uses exact structural check coverage, auxiliary-node count and wrapper-token cost to choose a nondominated plan. The solver then answers the unchanged seed. If planning fails, use the already frozen fallback within the same two-call reservation. Compiler acceptance is structural evidence; a planned check is not a passed check.

For all three, exact Pareto dominance means coordinatewise comparison with at least one strict improvement. It describes the recorded objectives exactly and says nothing about whether those objectives capture mathematical quality. Unknown measurements stay unknown. Empty/singleton/tied fronts, permutation invariance and duplicate occurrences require explicit tests.

## Reusable primitive and first validation

`ProtectedMutationSelectionReceiptV1` should bind seed bytes, serialized requests, parent/child wrappers, actual edit scripts, policy version, occurrence IDs, public observations, exact metrics, the complete frontier, selected artifact and total run cost. Host replay and durable readback precede issuance. Separate residual fields keep semantic wrapper preservation, detector incompleteness, lineage authentication and within-item scope visible.

Start with host-only synthetic tests of protected UTF-8 bytes, boundary edits, stale receipt substitution, empty/singleton frontiers, dominance ties, persistence failure and typed-plan omissions. Only after these prerequisites and separately authorized budget setup should a paid frozen-policy experiment run. Independent public fixtures calibrate detectors; isolated trusted mathematical review scores frozen final outputs. No such implementation, calibration campaign or paid experiment was performed for this report.


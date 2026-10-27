# Quickstart: your first Symbol Game

The Symbol Game separates a proposal from its check. You can begin with a
few marks, a stated goal, and a basic packet. Advanced mathematical routes
come later.

Read [Paper 000](../papers/symbol_game/000_pfp_introduction/README.md)
for S(n), MSS-N, and basic packets. S(n) names Genesis derivation stages;
MSS-N names externally designed atlas obligations. Their indices are different.

## A first packet game

Declare marks a and b. Declare a directed goal: a separates b, with no
self-relations and no endpoints outside the carrier. Propose a packet and
ask a referee to check that rule. Predict these outcomes before running the
Paper 000 companion:

| Candidate | Expected result |
| --- | --- |
| a separates b | Declared check passes |
| a separates a | Self-relation refused |
| a separates c | Outside-carrier endpoint refused |
| b separates a | Directed goal unmet |

A pass concerns this declared relation rule only. It does not derive a Genesis
stage or license an MSS extension. Repair a failed candidate without silently
changing its carrier, goal, or checking rule.

## Try ten practical routes

Open [ten ways to play](06_ten_useful_ways_to_play.md) and
[the executable local exercises](02_ten_ways_to_play.ipynb). Choose a route
by your task: packet repair, teaching, graph repair, certificate checking,
refusal handling, review, learning from rejection, extension checks, or bounded
strategy comparison. These routes are an editorial selection, not all possible
ways to play.

## The triangle teaching board

The [walkthrough](00_interactive_how_to_play_walkthrough.ipynb) and
[scenario lab](01_interactive_scenarios_lab.ipynb) use one declared triangle:
0 → 1 → 2 → 0, with edge values 2, 1, 3. Its circulation is 6.

The local [teaching runtime](educational_governor.py) checks exact values:

| Move | Effect in this teaching model |
| --- | --- |
| ASSERT | Record an annotation; the runtime does not prove it |
| CUT | Replace declared edge values only if absolute triangle circulation strictly decreases |
| VERIFY | Check zero triangle circulation and seal this board |
| RETRACT | Restore a saved checkpoint, retain history, and consume fuel |

Replace the last edge value 3 by −1. The circulation becomes 2. Replace it
by −3. The circulation becomes 0. VERIFY now passes. A proposed value 7
increases circulation and is refused without changing the accepted board.

These CUTs edit edge reports. They are not vertex gauge transformations:
adding differences of vertex values cannot change a closed-cycle circulation.
For optimization over potentials with fixed reports, read
[Paper 001](../papers/symbol_game/001_pfp_discrete_cochain_retraction_and_toy_involutions/README.md).

The teaching runtime is separate from the native host. Its legacy
`defect_phi1` field means triangle circulation defect in these lessons;
it is not the native Phi1, Gamma2, or Xi functional. A zero check here does
not certify arbitrary assertions or every property of a graph.

## Replay the checks

From the repository root, with Python 3.12 and pytest installed, run each
file separately:

```sh
python -m pytest education/documentation/004_oepfp/_how_to_play/test_how_to_play_scenarios.py -q
python -m pytest education/documentation/004_oepfp/_how_to_play/test_educational_governor_boundaries.py -q
```

Keep the proposal, checking rule, and receipt together. If attempts run out
before a checked answer is found, record an unresolved stop. The advanced
[board rules](02_the_rules_of_the_board.md), native interfaces, and historical
editions add their own obligations; the Examiner exam is optional advanced study.

<div align="center">

# PFP: Compression that preserves future operations and their cost

Jeremy H. Carroll

2026-10-23

Version 0.2.0 — author-review extension

</div>

## Abstract

Equal current answers need not permit equal future choices. For a finite
deterministic transition table, we characterize an exact operation and cost
quotient and construct the coarsest stable refinement of an initial report.
We give counterexamples to output-only compression and to choosing the fewest
operations as the cheapest solution. The finite result imports standard
transition-system refinement; its WDP role is preserving the original future
question during representation change.

## Mechanism inventory

| Mechanism | Evidence |
| --- | --- |
| Mathematical statement | Written proof under declared hypotheses |
| Finite example | Standard-library replay of submitted inputs and rejection controls |
| Model inference | Not executed |
| Lean verification | No new formalization claimed |
| Authorization | None supplied |

## 1. The declared finite model

Let $X$ be a finite state set, $A$ a finite action alphabet, and $q_0$ an
initial report. Each action $a$ has a partial deterministic transition $t_a$
and a positive rational cost $c_a$ on its domain. Terminal task labels are
included in the protected report. A quotient $q:X\to Z$ is exact if all
action domains, costs, successor reports, and terminal labels descend and
reflect the declared concrete operations.

## 2. Necessary and sufficient structural conditions

**Theorem.** Such an exact quotient exists on a supplied report $q$ precisely
when states in one fibre have the same terminal labels and, for each action,
the same enablement, the same enabled cost, and the same successor fibre.

**Proof.** If quotient operations descend and reflect, evaluating one
quotient state cannot depend on which representative was chosen. Each listed
condition follows. Conversely, define enabled quotient actions, their costs,
and their successors using any representative. The conditions make all these
definitions independent of the representative. They give the commuting step
maps and reflection of action enablement. Induction on a word then gives
identical legal action words, protected reports, and accumulated costs for
states in one fibre. Consequently the best finite resolution cost is also
preserved, including the absence of any legal resolving word.

This theorem concerns a deterministic table. For adversarial outcomes, the
required successor data are the complete declared outcome relations in the
appropriate information-state arena; Appendix S states that stronger model.
Deterministic examples cannot certify a stochastic or hidden-state adapter.

## 3. Coarsest stable refinement

Start from $q_0$'s partition, including terminal labels. Repeatedly split
each block by the action signature: disabled, or the pair consisting of
exact cost and successor block. Each proper split increases the number of
blocks, so at most $|X|-1$ proper splits occur. A stable partition satisfies
the theorem's conditions. Any stable refinement of $q_0$ refines every
iteration: prove this by induction using its equal costs and successor
classes. Therefore the terminal partition is the coarsest stable refinement.
This is a finite construction, not a physically supplied observation instrument.

## 4. Current-output and cost counterexamples

Two states $a,b$ both report zero, and both allow `finish`, reaching the same
terminal state. Its cost is one at $a$ and three at $b$. The current output
is preserved by identifying them, but operating cost is not. Disabling
`finish` at $b$ also destroys future capability. Conversely, a task asking
only for the current zero has the same answer in both states despite these
structural failures: accidental task-value preservation is weaker than
operation-preserving exactness.

In a second table, `direct` reaches the terminal in one operation costing
five. `next` and `finish` take two operations costing one each. The cheaper
route costs two. Add a positive-cost self-loop: it cannot improve any finite
resolving word because deleting its repeated-state segment gives a legal
word of strictly smaller cost. Thus an optimum, when reachable, occurs among
simple paths of at most $|X|-1$ transitions in this deterministic model.

## 5. Replay and scope

The cost example declares states `r`, `s` and terminal `t`: `r` can go directly
to `t` for 5, move to `s` for 1 and then finish for 1, or loop at `r` for 1.
The checker replays the submitted route and its claimed rational price. A
separate procedure enumerates simple paths in the original table. Positive
cycles can be erased from a terminating deterministic route, so that finite
enumeration establishes the minimum 2. A falsely claimed price, an expensive
route presented as optimal and an unfinished route are rejected.

The [reference](code/replay.py) computes the stable refinement, checks exact
rational route costs, and preserves a positive self-loop as a rejection
control for the mistaken minimal-operation rule. It makes no provider calls.
The new theorem has a written proof and finite replay, with no new Lean
claim. The open native Source-25 target still requires actual states, edits,
guard receipts, costs, and a declared carrier bound; this abstract table does
not supply those bindings or implement a physical observer.

The [two-level teaching packet](prompts/example.yaml) includes shared system
rules, this typed user instance, a different worked example and a required
candidate response schema. It keeps provider system/user roles separate.
It is a saved example, not a schema-admission or model-run receipt; the
local replay checks the mathematical or protocol obligations stated above.

## Research extension: bounded context without a preservation claim

The AIDE2-inspired reference replaces full attempt history with the root,
champion, two recent attempt summaries and references to retained evidence.
The host refuses a projection that drops required references. Failure guidance
is scoped and capped. These are bounded operational choices, not a construction
of the coarsest stable quotient defined above. The external paper reports prompt
size reductions for its own benchmarks (p. 9); those values are not local results.

Consider two resumption records with the same displayed answer and payload
digest. One retains the artifact reference, task and state binding; the other
keeps only the digest. A later resume operation can be enabled on the first and
refused on the second. A shorter summary that identifies them therefore violates
future-operation preservation even if their current displayed answers agree.
Keeping a textual reference is necessary for the campaign's custody contract,
but is not sufficient to prove that a stochastic model will use the referenced
content correctly. Equal token counts likewise imply no equality of future costs,
action availability or successor states.

The campaign records context bytes, actual reported input and output tokens,
completion, failures and cost. The no-compression ablation keeps full prior code
within the same request ceiling; crossing that ceiling is a retained refusal.
This compares bounded policies rather than granting one arm an unlimited context.
A reduction in context size may accompany a loss of useful distinctions, and a
correct answer on the measured panel does not discharge every future operation.

The existing finite deterministic theorem and its replay are reused unchanged.
No new Lean result is claimed. Since the live campaign has not run, this revision
reports no local compression factor, cost saving or preservation measurement.

The source and page references for this extension are collected in
[Paper 029](../029_pfp_evidence_bound_harness_evolution/paper.md) and its
[source-to-claim map](../029_pfp_evidence_bound_harness_evolution/docs/source_to_claim_map.md).
The author-review rendering does not replace a historical deposit or archive.

## Sources and relation to the programme

This draft builds on the [WDP manuscript](../../../../../atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/000_witnessed_difference_programme/witnessed_difference_programme.md),
[Paper 021's source-and-execution distinctions](../021_recreated_demos_and_proposal_fidelity_evidence/paper.md),
and the [corrected findings notices](../symbol_game_challenge_and_demos_findings/README.md).
[Paper 022](../022_pfp_frontier_research/paper.md) supplies a
research design whose live-model and offline-strategy claims require their own
source-bound scrutiny. These drafts do not adopt its empirical tables as new
measurements. The [PFP collection guide](../README.md)
provides the shared-system/typed-instance protocol. Genesis and MSS-N
presentation stages do not license a new mathematical or physical carrier.

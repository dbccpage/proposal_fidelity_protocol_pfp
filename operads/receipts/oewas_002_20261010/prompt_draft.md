# Woland teamwork prompt — OEWAS-002

AuthorityEffect: None.

Status: delegated implementation and adversarial review, authorized by the user's
OEWAS-002 continuation request. PR #714 remains open; this branch builds on its
head `69a083c71b6fcc6b17ed3e9f497b3f380b580eae` and will have a separate stacked PR.

Working directory: managed `oewas-typed-contracts/the_symbol_game` worktree.

## Requirements

1. Reuse typed OperationV3, the existing catalog and candidate instruction compiler.
   Extend their finite composition boundary without a second catalog or runtime.
2. Bind zero-based nested slots to `(A o_i B) o_(i+j) C = A o_i (B o_j C)`;
   distinguish disjoint-slot interchange. Preserve ordered ports and occurrence identity.
3. Use TDD for new public behavior, real production mutants, exact restoration and
   independent finite oracles. Existing passing behavior is reuse, not a new RED.
4. Preserve instruction-only admission and historical custody. No persona or graph
   validation grants execution authority or mathematical certification.

## Roles and review

Woland/root integrates and routes evidence. Koroviev/planning_review challenges
scope and mathematical claims. Azazello/runtime_review inspects native boundaries
and implementation reuse. Hella/tdd_review owns independent slot-law controls.
Each agent retains concrete dissent and the next deciding test.

## Acceptance

- Exact nonzero nested and disjoint finite splice controls, with a killed wrong-slot mutant.
- A real typed composition slice consuming merged-era APIs plus PR #714 contracts.
- Explicit cycle/repetition semantics with negative controls at the chosen public port.
- Small named test batches, modified-file lint, epic byte manifest and bound raw evidence.
- Separate PR with an explicit dependency on #714; no changes to that PR's branch.

## Current boundary

Full research readiness remains held. Native parity, any unsupported graph topology,
runtime admission and unrelated architecture failures must be reported at their actual scope.

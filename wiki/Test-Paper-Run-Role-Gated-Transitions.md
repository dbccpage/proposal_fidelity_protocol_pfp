# Test: Paper-Run Role-Gated Transitions

A research paper under review is modelled as a frozen folder (the "carrier")
plus a graph of the claims it declares and the obligations each claim creates.
Every step of the review is a transition event signed with a role: proposer,
evaluator, witness or authorizer. These tests check that the planner derives
the right obligations and review stages from the declared claims, and that the
transition validator refuses every step a role is not allowed to take.

## What it tests

`test_paper_run_transitions.py` (10 tests):

- Freezing a three-claim mini paper gives a 64-hex carrier hash, one graph with
  all three claims, an unchecked `lean_kernel` obligation for the claim marked
  for Lean proof, and no Lean obligation for the claim that is only numerical.
- The plan is read-only, carries `authority_effect == "None"`, always includes
  the opening red-team stage and the final red-team stage, and round-trips
  through YAML with the same hash and claim count.
- The carrier hash is stable for an unchanged folder and changes when a file
  changes.
- Refusals: a proposer that marks its own work as passing; an evaluator that
  submits a patch; any role that edits the source after the public build
  without rebuilding; any `global_green` event; a `human_accept` from anyone
  but the authorizer.
- Legal events still pass: an evaluator finding, an authorizer accept.
- Dev-only planning skips the public build stage and the final red-team stage
  and says so in the plan notes.

`test_paper_run_domain_objects.py` (7 tests) checks the value objects one by
one: enum string values, that the error type is a `ValueError`, that claim,
obligation and transition objects are immutable and serialise, that claim IR
(the YAML claim list) maps a mechanization class to a claim kind and ceiling,
and that a run plan serialises its graph, hash and stages.

## Why it matters to PFP

PFP separates who may propose, who may judge and who may accept. A proposal
system that lets the proposer grade itself, or lets a reviewer quietly edit
what it reviews, has no meaningful receipts. Here that separation is a pure
function over a typed event that returns `Ok` or a typed refusal with a
stable code, so it can be tested exhaustively. The machine's authority
ceiling is `None`: no event may mint authority. See
[Core Concepts](Core-Concepts.md) and [PFP Package](PFP-Package.md).

## Setup and inputs

The mini paper is built in a pytest temporary folder: a `README.md`, a
`paper.md` and `docs/claim_ir.yaml` declaring three claims (`A1` scope fence,
`D2` Lean theorem, `E4` numerical replay). Transition tests build
`TransitionEvent` objects directly. Requires pydantic (declared by the repo)
and PyYAML.

## How to run

From the repository root:

    python -m pytest demos/paper_run_rules/test_paper_run_transitions.py demos/paper_run_rules/test_paper_run_domain_objects.py -q

## Expected output

`17 passed` in under a second.

## What a failure means

- A refusal test passing the event: a role can now do something it must not,
  for example a proposer can certify its own patch.
- A legal-event test failing: the validator became over-strict and would block
  ordinary review.
- A wrong obligation set: the mapping from claim kind to obligations changed,
  so a stage that should run (or be skipped) is no longer planned.
- A hash that does not change after an edit: the carrier no longer pins what
  was reviewed.

## How to modify it

Role rules live in `paperrun/services.py` (`ROLE_ALLOWED_EVENTS`,
`GLOBAL_FORBIDDEN`, `TransitionValidatorService`). Claim-to-obligation and
obligation-to-stage tables are in the same file; the stage list is in
`paperrun/stage_spec.py`. Add a role or event there, then add one refusal and
one legal-event test.

## Port notes

Ported from an internal test suite. The command-line planner test and the
program-profile overlay were not ported. The carrier adapter and planning use
case were trimmed to the parts these tests use, and stage and schema names were
made neutral. The carrier-hash-change test is new.

## Location

`demos/paper_run_rules/` (package `paperrun/`).

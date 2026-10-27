# Steering: harness evolution

Instead of changing the model or the prompt, one can evolve the harness around
the model: how tasks are presented, which checks run, how repairs are scheduled.
The source project set up a frozen experimental protocol for doing that with
evidence, and stopped short of paid model calls until the protocol was
reviewed.

## What the source did

- **Frozen protocol and budget.** The protocol was written into the campaign
  journal before any discovery. A fixed budget (40 US dollars) lived in a
  database; starting a new directory to get around an unreconciled hold was
  forbidden.
- **Everything retained.** Every model response, including malformed content,
  was stored before parsing. Pricing evidence was bound to the configuration by
  digest.
- **Separated data.** Selection and confirmation tasks were optimization data.
  Transfer tasks were left untouched until all three trajectories finished, and
  one task family appeared only in transfer. Ablations used a different panel
  and the final incumbent of one trajectory, chosen in advance.
- **Honest baseline.** The "current policy" baseline was an explicit projection
  of sequential propose-and-check onto the common task adapter, not a claim that
  the production learning service had run those tasks.
- **Ablation limits.** Ablations switched off observable features and checked
  each context again during trials. The source states this does not show that a
  model forgot a strategy, or that a prompt carries no implicit hints; no causal
  claim is licensed before live measurements.
- **Isolation.** On Windows, candidate code ran in a low-privilege app container
  inside a Job Object. Only offline preflight was admitted; paid runs were
  deferred pending a separate reviewed decision.

No paid calls ran. The delivered evidence is offline replay, contracts,
accounting, learning and publication custody.

## Replicate it here

The harness runner and its protocol were not copied into this repository. The
pieces that make such a campaign trustworthy are available:

- exact arm comparison: [Yardstick arm statistics](Test-Yardstick-Arm-Statistics.md);
- a task bank whose checkers refuse misses and drifted prompts:
  [Calibration task bank](Test-Calibration-Task-Bank.md);
- replayable receipts: [Certified run replay store](Test-Certified-Run-Replay-Store.md)
  and `python -m pfp_lab.cli.main verify`.

A minimal offline version with [PFP Lab](PFP-Lab.md): treat each harness
variant as a policy that writes scenario moves, freeze the list of scenarios
before trying any variant, keep some scenarios for transfer only, and compare
variants by the final defect in their receipts.

## How it relates to PFP, EIS and PCIV

- **PCIV.** This is selection over harnesses rather than prompts, with the same
  rules: fitness from an external checker, held-out transfer, and a frozen
  record of every candidate ([PCIV: selection and retrieval](PCIV-Selection-and-Retrieval.md)).
- **PFP.** Every evaluation in the campaign is a PFP check with a receipt; the
  campaign's conclusions are only as good as those receipts.
- **EIS.** The experimental path deliberately did not activate antibodies or
  admit production operators, so a campaign cannot change live guidance.

## Where the code lives

Not in this repository. The supporting statistics are in
`ops/adversary/use_cases/yardstick.py` and the demos linked above.

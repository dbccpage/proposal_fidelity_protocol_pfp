# Management ladder v2: bounded native operad/PFP experiment

AuthorityEffect: None. Version: `pfp.management-ladder.v2`. Registered before calls
by freezing the source hashes, item bank and pricing observations into the output
registration. The v1 design and prior replies retain their exact bytes.

## Question and limits

On this small generated bank, compare A0 plain task phrasing with composed PFP
operations and management levels M0-M6. All model communication uses the same PFP
binding envelope and canonical `ANSWER: <JSON>` channel. M0 changes task management,
not transport custody. The v1 exact integer gate remains in use; v2 adds explicit
integer solution witnesses and finite composition, planted-defect and claim-token
checkers. No mathematical theorem, universal superiority or MUB result is tested.

The bank contains four families, three rungs, and disjoint labelled training and
held-out variants. Ground truth is retained outside the prepared model input.
Composition answers cannot invoke the composer until after the model responds.
Host-solvable cases are reported separately; their deterministic solver contribution
is explicit. A matched expected number inside the original problem is not alone
answer leakage: P0 checks the complete expected response and the data flow.

## Registered procedure

- P0: positive, wrong, empty, duplicate-key, counterfeit and contradictory-refusal
  controls; actual host-only compositions; compact prompt-tree expansion equivalence.
- P1: Haiku/Sonnet A0 on composition and exact-linear-system rungs 1 and 3 (8 cases).
- P2: those models A0/M5 on at most three calibration-selected items, including
  composition rung 3. If calibration has no failures, report that fact and treat
  the comparison as descriptive; do not manufacture a failing rung.
- P3: Haiku M0, M1, M2, M3 at 1/3/5/8 stages, M4, M5 and M6 on one training
  composition item. Retain five by correctness, then rated cost, then stable policy
  name. Evaluate those five once on the held-out composition counterpart.
- P4: Opus A0 versus the selected managed policy on held-out composition and linear
  algebra. Select the managed policy from training; held-out outcomes never tune it.

M1 adds typed objectives and obligations. M2 enforces structured output.
M3 carries the preceding candidate into the next separately checked PFP stage.
M4 uses a concrete envelope correction only when a training reply demonstrates
that failure; absence of training evidence is recorded as no learned intervention.
M5 executes a checked planar PFP/check/report tree (at most four operations).
M6 permits one additional repair with failure-class feedback; it never receives
the expected answer. Training guidance is an
experimental prompt attachment, not automatic OEEIS admission.

## Spend, capabilities and custody

One continuing existing SQLite budget ledger caps the entire campaign at 2,000,000
micro-USD, partitioned P0/P1/P2/P3/P4 = 0/200000/600000/800000/400000. These are
ceilings, not targets. Each call uses the existing Rust Messages transport's quote;
its reservation is durable before send. No retries or automatic fallback. Ambiguous
outcomes and unknown metering retain the full quote and halt further calls. Restart
replays stored attempts; it cannot reset the allowance or rerun a failed item.
One call runs at a time, with at least two seconds between dispatches.
Before dispatch, native quote-only requests freeze the admitted structured/plain
request bounds and a per-stage maximum call count. Planned maxima are 8/12/43/18;
each is reduced to the stage allowance divided by its largest admitted quote.
Actual requests exceeding their registered quote are refused. Staged prior content
is limited to its first 2,048 UTF-8 bytes, with complete original replies retained.
The 43-call P3 maximum includes the eight-stage arm and one-repair arm; P4 reserves
for the possible eight-stage winner. No allowance is transferred between stages.

Requested models are `claude-haiku-5-5`, `claude-sonnet-5-5`, `claude-opus-5-5`.
Official capabilities and standard global rates are pinned in
`pfp/fixtures/empirical/anthropic_pricing_20261015.json`.
Provider model access failures are retained, not substituted. Maximum output is 768
tokens per call; requests stay below the Haiku 100,000-input-token tier boundary.
No tools, cache writes, temperature or unsupported provider seed is sent. The local
item-order seed is 12015. Structured output uses `output_config.format`.

## Analysis and execution

Report every selected row including errors and budget censoring. Separate provider
attempts, PFP envelope validity and exact task acceptance. Collate raw-output paths,
returned model, usage, rated cost (not an invoice), open obligations and operation
identities. Report Wilson intervals and paired exact sign tests with raw paired cost
differences and a deterministic 1,000-resample mean-cost interval when at least two
complete pairs exist. This sample supports descriptive observations; insufficient discordant
pairs leave H14-H17 unestablished. Storage bytes and rendered input tokens are
separate metrics; prompt-tree storage compression does not claim token savings.

Prepare with `python -m pfp.infrastructure.management_ladder --output <external-directory>`.
Execute that unchanged registration with the same command plus `--execute`, using the
existing credential resolver to place `ANTHROPIC_API_KEY` into the native child
process environment. `CORE_SYMBOL_GAME_HOST` selects the freshly built host.
The command writes raw replies and accounting to the supplied output directory
(use the ignored `.scratch/oewas012/pilot` directory for this run). It never runs
the retired 2,500-pilot grid. The MUB exact-count item remains with its external owner.

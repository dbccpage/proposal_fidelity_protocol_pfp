# Rational counterexample panel

Three executable plans adapt the rational-substitution portion of research idea R05-I02. They use the same complete QM task and the same solver instruction. The solver emits a complete answer plus optional typed equations. A host then annotates those equations, retaining the original answer for separate post-freeze grading. These plans do not implement the entire research proposal or the native PFP, EIS or OPERADS interfaces.

November 10 live update: all three original plans failed artifact validation in their first sampled runs. The added `rational_fixed_panel_v2` makes the five root fields explicit and budgets answer length; its first live answer still truncated and failed JSON validation. It retains the same checker and 3,000-token ceiling. This is an unsuccessful exploratory repair, not a new mathematical mechanism or an established improvement. Original v1 instructions and frozen failures are preserved in `pilot_20261110/`.

| Plan | Model calls | Challenger visibility | Completion ceilings |
| --- | --- | --- | --- |
| `rational_blind_panel_v1` | 2 | Exact original seed and frozen public contract | 3,000 solver + 1,500 challenger tokens |
| `rational_visible_panel_v1` | 2 | Same inputs plus complete solver artifact | 3,000 + 1,500 tokens |
| `rational_fixed_panel_v1` | 1 | Twelve fixed host probes, no model challenger | 3,000 solver tokens |

The blind/visible comparison isolates access to the candidate. It does not assume independent errors. The fixed panel is a cheaper mechanism ablation, not an equal-token comparison. The existing direct and self-critique controls remain available, with their own recorded allowances; a matched-budget study must freeze its comparison settings explicitly.

## What is checked

The public contract in `rational_panel.py` fixes five obligation IDs corresponding to the five task parts, variables `J`, `Delta`, `K`, `t`, `beta`, and a restricted real domain with `t>=0` and `beta>=0`. This nonnegative-time slice is only the declared checking domain; it does not rewrite the seed or restrict the complete answer to that slice.

An encoded equality claims that its two rational expressions agree throughout that domain whenever all its declared guards are defined and true. Expressions use exact rational constants, those variables, addition, subtraction, multiplication, division and powers from zero through eight. A challenger provides rational assignments, never expected values or executable code. The host independently evaluates both sides using integer rational arithmetic.

An in-domain assignment satisfying all guards with distinct exact values refutes the encoded universal equality. A failed sufficient-condition antecedent is inapplicable, not a counterexample. Undefined guards are unknown; an undefined conclusion is recorded as a definedness failure. Expressions are evaluated without algebraic cancellation that could erase undefined points, including a partial base raised to the zeroth power.

Finite passing assignments never prove a universal equation. Every claim retains an explicit OPEN semantic-alignment obligation: this checker cannot establish that a model's equation faithfully represents its prose or the requested quantum result. Missing and unsupported claims also remain open. All five task obligations remain uncertified regardless of point-check counts. Trigonometric, exponential, logarithmic, square-root, complex, matrix and limit reasoning is outside this implementation; the complete answer must still address those parts in prose.

## Execution and records

The exact seed is a separate unchanged message in every call. The public grammar and instructions are additional messages. Requests expose no filesystem, shell, retrieval, answer key or evaluator. The blind challenger request is invariant under changes to the solver response; only the visible ablation receives that response. This is a property of the broker's requests, not an assurance about provider-side state.

Dispatch is serial and uses the existing durable aggregate USD 0.10 run ledger. Each call must be admitted against the remaining amount. This implementation may stop before a later stage when its current quote no longer fits; it does not promise that the full two-call path will fit in advance. Unknown charges preserve their reservations and stop dispatch. There are no retries, repair calls or paid judges. The provider-enforcement premises described in `LIVE_RUNNER.md` still apply. Local checking assumes no incremental metered host charge.

Each response is frozen before host checking. `host_checks.json` binds candidate and panel hashes, seed and contract hashes, exact witness values, statuses, visibility, resource use and residuals. The original solver answer, never the challenge response, becomes the run's `answer_text`. Invalid candidate JSON is retained raw with an explicit artifact error; it is not silently repaired. Missing evidence remains missing after a blocked call. `panel_artifact.json` also retains the deterministic panel for the one-call ablation. `run.json` binds these host results and implementation hashes. Accuracy remains unset until trusted post-freeze review.

Extracted answer text must be valid UTF-8. Evidence records use lossless ASCII JSON escaping so even malformed provider metadata can be preserved without preventing a failure receipt. The provider adapter retains a known charge before reporting malformed Unicode as an accounting/protocol failure. Result summarization requires a matching `run.sha256`, answer digest, budget binding and arithmetic, finite durations and exact nonnegative monetary/token values. These local integrity checks do not authenticate the provider or prevent someone replacing both a receipt and its digest.

Artifacts reject duplicate JSON keys, extra fields, ambiguous rational strings, floats, nonfinite values, Boolean exponents and undeclared variables. Bounds include 24 claims, 12 challenges, eight guards per claim, 128 nodes per expression, depth 16, 128-bit rational inputs, 4,096-bit retained intermediates and 200,000 host operations. A ten-second cooperative deadline is checked during validation and evaluation; it is not OS-level process isolation or a universal runtime guarantee. Resource exhaustion yields unknown evidence. The bounded integer operations may temporarily allocate a result larger than the retained-intermediate limit before rejecting it.

The plan hash binds its public contract, stage instructions, visibility, output caps, and source hashes for the checker, specification, runner, campaign CLI, both ledgers and provider. Changing those files invalidates an existing campaign's plan binding; a change after import is refused before output creation or dispatch. The adapter remains outside the proposed 4,250-composition grammar: adding these three plans does not make those compositions executable.

## Preparing a comparison

The following only prepares a manifest; it neither initializes a ledger nor dispatches requests. The three single-repetition run caps total USD 0.30. The placeholders require a concrete endpoint before initialization.

```powershell
.venv\Scripts\python.exe -X utf8 dag\benchmark\live_campaign.py prepare --campaign-id qm-rational-panel-001 --model AUTHOR/MODEL --endpoint PROVIDER/ENDPOINT --plans rational_blind_panel_v1 rational_visible_panel_v1 rational_fixed_panel_v1 --repetitions 1 --cap-microusd 300000 --order-seed 70719 --output dag\benchmark\panel_campaign.json
```

The first live campaign and fixed-panel repair are recorded in `pilot_20261110/`; consult `results_summary.json` for measured outcomes. Synthetic fixtures test checker behavior, visibility, accounting and preservation; they supply no empirical evidence that these plans improve answer accuracy, money, tokens or time. See `rational_panel_validation.json` for the historical pinned validation checkpoint; the current suite passes 121 tests.

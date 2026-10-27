# PFP empirical gate collection

AuthorityEffect: None.

The native predicates evaluate finite measurements. The current
[PFP command](../../../../entrypoints/empirical_gates.py) collects those
measurements through the existing accounted PFP gateway or the optional
[Egglog adapter](../../../adapters/egglog_prompt_rewriter.py). Adversary delegates
`empirical` to that same entrypoint. Historical YAML and receipts are unchanged.

| Gate | Executed work | Claim boundary |
| --- | --- | --- |
| [EMP001](01_token_amortization_gate.yaml) | Matched raw/symbolic prefixes at sizes 1, 2, 9 and 10 across four selected models; actual prompt/completion usage and unit increments T(2)−T(1), T(10)−T(9). | Total reported token use includes output. No estimated counts, rounding or cross-model generalization. A measured failure emits a negative witness; missing coverage emits none. |
| [EMP002](02_injection_containment_gate.yaml) | Twenty distinct attacks and benign controls in paired raw/current SQLite arms, checked against the original host oracle. Host-rendered SQL must actually roundtrip. | Shape validity and refusal alone are not containment. Unknown accounting stops the sweep. Results apply to the declared task, model and cases. |
| [EMP003](03_egraph_preservation_gate.yaml) | Fifty actual Egglog executions of Mode 13's three fixed rules; extraction is independently checked for ordered source bytes, roles, boundaries and repeated constraint occurrences. | Finite representation preservation does not establish arbitrary prompt semantics or model performance. Smaller runs remain useful PARTIAL observations without a fifty-case gate payload. |

```powershell
python -m adversary.entrypoints.cli empirical --suite rewrites --plan
python -m adversary.entrypoints.cli empirical --suite rewrites --output target/rewrites.json --native-witness-output target/rewrite-witness.json
python -m adversary.entrypoints.cli empirical --replay target/rewrites.json
```

Egglog is optional and pinned to 14.0.0; its wheel requires Python 3.12 or newer.
Install `.[empirical]` in the chosen environment. Missing or different runtimes
are explicitly unavailable. The adapter calls the actual
[official Python bindings](https://egglog-python.readthedocs.io/latest/reference/bindings.html).
It enforces the declared ten-iteration/1,024-node profile and retains engine,
rule, source, AST and extraction observations. A real constraint-dropping rule
was rejected by the independent validator even after Egglog declared equality.

Live token/injection commands require an input JSON file, explicit models,
call/output limits and one shared estimated financial allowance. `--plan`
makes no sends. Replay rechecks retained bytes and recomputes summaries with
zero sends; it does not authenticate an operator-edited report. Original
answers stay with the host oracle. See the
[operator examples](../../../../../adversary/documentation/panel_gate_integration.md#empirical-gates)
for input shapes and bounds.

Anthropic uses the same PFP/accounting boundary with `--provider anthropic`
and an explicit `--pricing-snapshot` file. The snapshot binds its source URL,
observation time, model rates and content digest. Actual returned usage is rated
against those standard text rates; `cost_usd` stays unavailable and
`rated_cost_usd` is an estimate, not a vendor invoice. Missing usage, unknown
outcomes or unpriced extras retain the reservation and stop dispatch. The
opt-in Anthropic allowance is at most $0.50; OpenRouter retains its existing
$0.05 ceiling. Separate suite allowances must fit the authorized combined cap.
The [example inputs](../../../../fixtures/empirical/) include ten tasks, twenty
attacks, a benign control and the explicitly dated rate snapshot.

`--native-witness-output` projects complete measurements into the existing
`adversary.native-gate-witnesses.v1` input. Multi-model results require an explicit
`--witness-model`; no model answer selects the gate or supplies its counts.
Pass that file and its source report to a fresh shared teamwork task via
`--native-gate-witness` and `--native-gate-source`. Legacy summary-only checks
remain diagnostics. No new sender, budget ledger, swarm or receipt lifecycle
is introduced.

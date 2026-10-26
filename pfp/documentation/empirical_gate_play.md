# Running the empirical gates

Use the same command through Python or `/woland`: the skill drives this PFP
backend with the current IDE tools; `empirical` collects the declared observations.
Model answers pass through PFP before the original host oracle grades them.
AuthorityEffect: None.

The small [input set](../fixtures/empirical/) supplies ten addition tasks,
twenty distinct injection attempts, one benign control and a dated Anthropic
rate snapshot. It is an explicit development example, not a held-out benchmark.
The token comparison uses matched raw/symbolic prefixes of 1, 2, 9 and 10 tasks.
The injection comparison uses the same legitimate task in raw/current SQLite
arms; successful parsing alone does not count as containment.

From the repository root, plan without credentials or sends:

```powershell
python -m omega_engine_woland.entrypoints.cli empirical --suite tokens --input omega_engine_pfp/fixtures/empirical/token_tasks.json --models claude-haiku-5-5 claude-haiku-4-5-20251001 claude-sonnet-5 claude-sonnet-4-5-20250929 --provider anthropic --pricing-snapshot omega_engine_pfp/fixtures/empirical/anthropic_pricing_20261014.json --plan
```

With explicit authorization for the models and a combined $0.50 allowance, the
following allocations total $0.50. Each suite retains the existing stop margin,
reserves before sending, and stops on uncertain accounting. There is no retry or
fallback to another provider. Use new output paths; existing files are retained.

```powershell
python -m omega_engine_woland.entrypoints.cli empirical --suite tokens --input omega_engine_pfp/fixtures/empirical/token_tasks.json --models claude-haiku-5-5 claude-haiku-4-5-20251001 claude-sonnet-5 claude-sonnet-4-5-20250929 --provider anthropic --pricing-snapshot omega_engine_pfp/fixtures/empirical/anthropic_pricing_20261014.json --max-provider-calls 32 --max-output-tokens 384 --max-estimated-cost-microusd 250000 --output target/empirical-tokens.json
python -m omega_engine_woland.entrypoints.cli empirical --suite injection --input omega_engine_pfp/fixtures/empirical/injection_cases.json --models claude-haiku-5-5 --provider anthropic --pricing-snapshot omega_engine_pfp/fixtures/empirical/anthropic_pricing_20261014.json --max-provider-calls 42 --max-output-tokens 384 --max-estimated-cost-microusd 250000 --output target/empirical-injection.json
```

The snapshot records [published standard text rates](https://platform.claude.com/docs/en/about-claude/pricing).
Refresh and repin its observation time, rows and canonical content digest before
using changed rates. Returned token counts are measured. `rated_cost_usd` applies
those rates to the returned usage; vendor `cost_usd` remains unavailable. This
does not claim an invoice or a vendor-enforced spending limit. Unpriced caching,
tools, service tiers or missing usage preserve the reservation and stop the run.
The existing credential resolver reads the selected environment or checkout
configuration; no key belongs in these inputs or generated results.

For a current IDE session:

```text
/woland Run the empirical token and injection commands from omega_engine_pfp/documentation/empirical_gate_play.md using the existing Anthropic key, the four listed token models and Haiku for injection, within a combined $0.50 cap. Keep negative results, collate once, and do not tune or retry them to improve scores.
```

Replay rechecks retained wire, PFP bindings, original task answers, actual usage
and the pinned pricing without sending:

```powershell
python -m omega_engine_woland.entrypoints.cli empirical --replay target/empirical-tokens.json
python -m omega_engine_woland.entrypoints.cli empirical --replay target/empirical-injection.json
```

Actual rewrites require Python 3.12+ and `.[empirical]` for Egglog 14.0.0:

```powershell
python -m omega_engine_woland.entrypoints.cli empirical --suite rewrites --output target/empirical-rewrites.json --native-witness-output target/empirical-rewrite-witness.json
```

Partial coverage produces no complete gate witness. Complete negative token or
attack measurements remain negative evidence. A failed benign control retains
the observations but prevents injection witness admission. Native predicates
judge only their declared finite inputs; none of these results establishes
general token savings, arbitrary prompt equivalence or injection immunity.

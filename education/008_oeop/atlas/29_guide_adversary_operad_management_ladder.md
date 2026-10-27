---
documentation_contract: symbol-game-documentation/v1
title: "Guide: Adversary planar operations and the bounded management ladder"
kind: operator-guide
status: implemented_and_bounded_campaign_completed
authority_effect: "None"
source_paths:
  - adversary/use_cases/teamwork.py
  - pfp/infrastructure/management_ladder.py
  - operads/skill_operad/resolver/native_runtime.py
last_verified: 2026-10-16
---

# 29 Adversary operations and the management ladder

OEWAS-012 connects the existing full-22 Adversary workflow to checked planar
operations. The Rust workflow host validates and orders operations; explicit
Python host/PFP callbacks perform their effects. The Python tree interpreter
remains the comparison oracle. Both `/adversary` and Python use the shared backend.

## Build and inspect

From the repository root, with Cargo and the project Python dependencies installed:

```powershell
$env:CARGO_TARGET_DIR=(Join-Path $PWD '.scratch/oewas012/native-target')
$env:CARGO_INCREMENTAL='0'
cargo build --manifest-path engine/crates_rs/Cargo.toml -p core_symbol_game --bin core_symbol_game --offline -j 1
Copy-Item -LiteralPath "$env:CARGO_TARGET_DIR/debug/core_symbol_game.exe" -Destination .scratch/oewas012/oewas012-native.exe
$env:CORE_SYMBOL_GAME_HOST=(Join-Path $PWD '.scratch/oewas012/oewas012-native.exe')
$env:PYTHONPATH='.'
$env:PYTHONDONTWRITEBYTECODE='1'
python -m operads.skill_operad.skill_compiler.op_inventory
python -m operads.skill_operad.resolver.resolver compose --inputs Paper,Code --goal Audit --max-ops 4
```

The recorded build used an isolated Python 3.13.11 environment at
`.scratch/oewas012/venv/Scripts/python.exe`. `--offline` assumes dependencies are
already cached. The inventory reports 15/15 registered operations, 8/8 guards
and 5/5 bounded host skills. It reports declarations separately from executors;
unimplemented meta-operations return `NOT_EXECUTABLE`.

## Run through the IDE or Python

In the current IDE:

```text
/adversary Implement <bounded task> using the shared backend and all 22 Panel roles. Bind <checker.py> as the original-task check. Keep provider access disabled for this IDE run and finish with scoped AutoP/auto-learn.
```

The equivalent Python entry point starts the same coordinator:

```powershell
$nativeSha=(Get-FileHash -LiteralPath $env:CORE_SYMBOL_GAME_HOST -Algorithm SHA256).Hash.ToLowerInvariant()
python -m adversary.entrypoints.cli teamwork start --state .scratch/my-task/state.json --objective '<bounded task>' --native-host $env:CORE_SYMBOL_GAME_HOST --native-host-sha256 $nativeSha --native-gate-scope adversary/config/software_gate_scope_v1.json --native-gate-policy require_pass --checker-id my-task-v1 --checker-source path/to/checker.py --check-command python path/to/checker.py
```

Use a real task checker and a new working-state path. The check command goes
last. Follow the returned `next_action`: run its host checks, read the prepared
PFP system/user/schema, perform the requested work and submit the actual reply
bytes with `teamwork submit --state ... --raw-reply ...`. Artifact observations
use the separate host-result channel. A bare Python shell cannot supply an IDE
assistant response. The role is a perspective; record the actual worker identity.
The copied native host above supplies both the operation and diagnostic paths.

The selected software scope enforces task-applicable gates with `require_pass`;
missing required evidence still HOLDs. Unselected proof/empirical experiments
are explicitly not applicable. Historical `diagnostic` mode can display wider
checks but cannot promote missing witnesses to PASS. The original task checker
continues to decide closure.

## Run the bounded experiment

The [v2 design](../../../../adversary/tests/pilots/certified_ladder/design_v2.md)
freezes deterministic item order, held-out separation, native quote limits,
three model IDs and one continuing $2 ledger before inference. A0 and managed
arms share the same PFP envelope and exact answer channel. Model composition
answers do not receive the host composer's solution. M5 uses three operations;
M6 permits one repair. Host-solvable rows have their own reporting stratum.

```powershell
python -m pfp.infrastructure.management_ladder --output .scratch/my-authorized-campaign
python -m pfp.infrastructure.management_ladder --output .scratch/my-authorized-campaign --execute
```

Preparation sends no inference request. Execution uses the existing Anthropic
credential resolver, passing the key only to the native child. The original
user authorization covers the retained campaign; a new output directory is not
a way to reset its budget. Preserve its ledger and resolve ambiguous accounting
before considering another paid attempt. Changed registration bytes are refused.

### Continue the existing campaign after an explicit charge decision

Use a separate output directory and the **original live ledger**, retaining the
historical packet unchanged. Obtain current public model/pricing observations
and review the generated amendment before execution. This command prepares only
native quotes; it neither sends inference nor reconciles accounting:

```powershell
$prior='adversary/tests/pilots/certified_ladder/v2/campaign_20261015'
$out='.scratch/oewas-complete-20261016/campaign'
$ledger='.scratch/oewas012/pilot/accounting.sqlite3'
$decision='Reference to the explicit human conservative-charge and continuation decision'
python -m pfp.infrastructure.management_ladder --output $out --prepare-continuation $prior --accounting-path $ledger --authorization-reference $decision --prices-path fresh-prices.json --model-access-path fresh-access.json --models-response-path fresh-models.json
```

Inspect `continuation_amendment.json`: predecessor and successor registrations,
all changed source hashes, native binary, observation digests, exact live ledger
snapshot and named ambiguous attempts. The preparation refuses the frozen
historical ledger as a destination. After reviewing these exact bytes:

```powershell
python -m pfp.infrastructure.management_ladder --output $out --execute --accounting-path $ledger --reviewed-amendment "$out/continuation_amendment.json" --authorization-reference $decision --prices-path fresh-prices.json --model-access-path fresh-access.json --models-response-path fresh-models.json
```

The explicit decision retains the full original reservation as a conservative
charge; actual usage and invoiced cost remain unknown. The old unknown attempt
is retained as unscored and **never retried**. Its charge consumes the same
global/stage allowance. Only remaining registered attempts proceed; any new
ambiguous send halts them. Restart uses the same output, amendment and ledger.
An authorization reference identifies the operator's decision; it is not
cryptographic authentication. No model/provider substitution is performed.

If a successful response was retained but a parser/pricing defect left its usage
unrated, repair the owner and reprice **the retained bytes** before another send:

```powershell
python -m pfp.infrastructure.management_ladder --output .scratch/retained-settlement --settle-retained-replies .scratch/prior-active-campaign --accounting-path $ledger
```

This path uses the active registration's original prices, request digest, raw
response digest and existing reservation. It invokes the native parser/meter
with no key and no provider dispatch; it cannot settle a missing or changed
reply, mismatched model, unsupported charge or cost exceeding the reservation.
The settlement retains its original outcome and changes only the continuing
liability to a rated usage estimate. Invoiced cost remains unobserved. A subsequent
source amendment names this active predecessor; the original registration and
every earlier amendment remain in the same ledger's history.

## What was observed

The [retained result](../../../../adversary/tests/pilots/certified_ladder/v2/campaign_20261015/REPORT.md)
contains the exact commands, registration, public request, source snapshot and
ledger. P0 passed 196 controls and 18 native host runs. The first Haiku request
returned a transport error without response bytes. The ledger retained 1,014
micro-USD and blocked subsequent paid work. Actual cost and usage are unknown;
there is no model accuracy or management-benefit result. All stage dispositions
are recorded. MUB exact-count work remains with its external owner.

The compact-tree fixture grew from 1,144 to 2,033 stored bytes while reproducing
the same prepared requests. Shared source storage can avoid duplication, but
its envelope has overhead. Provider-token savings require a different measured
request; deduplicated disk storage alone cannot establish them.

The [shared-backend run](../../../../adversary/tests/pilots/certified_ladder/v2/adversary_20261015/REPORT.md)
executed all 22 mandatory Panel roles: Syntax Prefilter through the host checker and the
other 21 as PFP replies from the current IDE worker applying each perspective.
These are not 22 independent model workers. Its unchanged original-task checker
returned `BOUNDED_PILOT_NOT_COMPLETED`. The workflow retained that obstruction,
recorded the required provider continuation as unavailable, and completed the
single scoped AutoP/auto-learn finish without inventing a successful task result.

## Reuse the applied lessons

Existing typed guidance now carries two practical lessons through the host
compiler: validate retained source bytes, UTF-8 spans and node overrides before
expansion; and regulate only a specifically identified learned detector after
independent benign checks. The prompt-attached stale-task antibody includes both
a harmful trigger and a benign control. Unknown evidence does not count as a
false positive. Mandatory budget, provenance, authorization and task checks stay
protected. These are useful code/prompt changes, not automatic detector admission.

Keep [chapter 27](27_spec_op_resolver.md) for API details. Historical review
counts remain in the earlier chapters; they are not fresh implementation results.

## Completed continuation, 2026-10-16

The [successor campaign packet](../../../../adversary/tests/pilots/certified_ladder/v2/campaign_20261016/REPORT.md) records the completed P0–P4 run, source-bound amendments and exact commands. Its continuing ledger totals $0.067134, including the original $0.001014 conservative charge. Forty-four responses settled; unknown historical usage remains unknown. The first retained response was repriced without resending after repairing standard-speed metering. Composition and host-solvable cases remain separate; this small sample establishes no universal management winner. The earlier stopped results above retain their original meaning.

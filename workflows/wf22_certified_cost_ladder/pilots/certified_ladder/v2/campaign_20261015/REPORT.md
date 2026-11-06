# Management ladder v2: bounded campaign result

AuthorityEffect: None. The implementation and offline controls ran. **The live
campaign stopped after its first attempted request, without a provider reply.**
There is no model accuracy, token-efficiency or management-benefit finding.

| Stage | Observed outcome |
|---|---|
| P0 | 196 checker, leakage and compression controls passed; 18 native host-only runs passed |
| P1 | One Haiku attempt returned native `TRANSPORT_ERROR`; no response bytes; accounting halted |
| P2 | Provider work blocked by the unresolved P1 attempt; two host-only rows completed |
| P3 | Provider work blocked; no training reply supports an antibody or management winner |
| P4 | Provider work blocked; one host-only row completed; no Opus comparison occurred |

The continuing ledger holds **1,014 micro-USD ($0.001014)** for the ambiguous
attempt. Actual invoiced cost and usage are **unknown**. This is a retained
reservation, not a measured charge or a zero-cost claim. The campaign ceiling
remains 2,000,000 micro-USD; nothing retried or reset the ledger. Later stage rows
are blocked cases, not failed model answers. The report's mechanically selected
policy labels do not establish a winner in the absence of scored model replies.

The request used `claude-haiku-5-5`, canonical public arithmetic input, the existing
PFP envelope, and at most 768 output tokens. The exact request object is retained
in `attempt_request.json`, bound to the ledger request digest. The provider
transport returned `OUTCOME_UNKNOWN` / `HTTP request failed`; it did not retain a
response. No raw-reply file is invented. The command used the default sandbox;
network restrictions are one possible cause. The existing Rust client discards
the detailed network error, so DNS, TLS and other causes cannot be distinguished
from the retained evidence.

The authenticated model-list read before registration confirmed all three model
IDs active with structured output supported. Public model metadata is in the PFP
empirical fixtures and the source snapshot. Credential values and HTTP
authorization headers are absent from this packet.

## Frozen design and bounds

The original registration SHA-256 is
`72bb0417944a10471f0f566191d3fbe93d7b022b0a3cc90fd1742fadac18ffad`.
Its native host SHA-256 is
`1e83ec688a73cea703b945c27b25d7cd51d9a267bc1ff8a7c24de206e9819364`.
Stage reservations were $0 / $0.20 / $0.60 / $0.80 / $0.40. Native quote-only
preflight admitted at most 8 / 12 / 43 / 6 calls for P1–P4, including staged arms
and the bounded repair. The largest admitted Opus quote was 63,444 micro-USD.
Later-stage allowances could not be consumed by earlier stages.

The tiny four-node compression control occupied 1,144 expanded bytes and 2,033
compact-envelope bytes. Compression therefore increased storage for this fixture.
Expansion reproduced the same prepared provider requests and checker inputs.
Storage deduplication is not evidence of provider-token savings; neither the 16×
nor 300 KB → 6 KB hypotheses was demonstrated.

## Applied repairs and validation

P0 exposed a real adapter mismatch: the existing silent-failure scanner returns
`line_number`, whereas the pilot initially read `line`. Correcting the adapter
made all 18 host controls pass. The failed preflight files remain unchanged here.

After the stopped live attempt, focused checks closed three further defects:

- Replay compares every retained parsed response field with the hash-checked raw
  JSON. A counterfeit cached answer no longer survives unchanged raw bytes.
- PFP operation metadata carries actual generation identity, local experimental
  seed, unsupported provider-seed status, and item/policy/stage/previous-attempt
  ancestry. A native three-operation control verifies the binding.
- Missing or malformed OpenRouter choices produce `ProviderError` while keeping
  the original turn bytes and accounting. Missing usage remains unknown.

The four owning acceptance files passed **24 tests** on the final source; see
`post_campaign_checks.xml`. The existing Anthropic and estimated-gateway owning
checks also passed after the native host became available. The Rust Anthropic
fixture suite passed **19 tests**, run with `-j 1`. These are scoped implementation
checks, not a successful live P1–P4 experiment.

`registered_sources.zip` retains the exact 28 preregistered source files, including
their original line endings. `post_campaign_amendment.json` identifies the three
subsequently changed registered modules and the final additional source hashes.
The original registration, source snapshot, ledger and campaign results were not
rewritten or reissued after those repairs. No further provider calls occurred.

The retired private seat fixture now retains worst-case liability on an ambiguous
send, but it is not a durable live accounting implementation. Live campaign
reservation and settlement use the existing SQLite ledger and Rust transport.

## Exact commands

These are the commands used from the repository root. The preparation command
does not send inference requests. The recorded execution stopped as described
above; do not create a fresh budget to bypass its unresolved attempt.

```powershell
$env:PYTHONPATH='.'
$env:PYTHONDONTWRITEBYTECODE='1'
$env:OMEGA_SYMBOL_GAME_HOST=(Join-Path $PWD '.scratch/oewas012/oewas012-native.exe')
& .scratch/oewas012/venv/Scripts/python.exe -m omega_engine_pfp.infrastructure.management_ladder --output .scratch/oewas012/pilot
& .scratch/oewas012/venv/Scripts/python.exe -m omega_engine_pfp.infrastructure.management_ladder --output .scratch/oewas012/pilot --execute
```

The current source differs from the preregistered source; the frozen output path
correctly refuses a changed registration. Historical reproduction uses the
retained source snapshot and original continuing ledger. Further paid work needs
the ambiguous attempt resolved and a reviewed registration amendment; none is
silently inferred here.

```powershell
$env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'
& .scratch/oewas012/venv/Scripts/python.exe -m pytest omega_engine_pfp/tests/test_pilot_grade_status.py omega_engine_pfp/tests/test_seat_gateway_error_cost.py omega_engine_adversary/tests/test_model_backend_budget_reservation.py omega_engine_pfp/tests/test_management_ladder.py --basetemp .scratch/oewas012/provider-completion --junitxml .scratch/oewas012/pilot/post_campaign_checks.xml -q
cargo test --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_providers --test anthropic_fixture --offline -j 1
```

The MUB exact-count dependency remains external. No old ladder version, answer
gate, historical receipt or original experiment byte was modified.

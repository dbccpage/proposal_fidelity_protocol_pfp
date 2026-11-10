# OEWAS development closeout and management-ladder continuation

AuthorityEffect: None. This is a bounded generated-task experiment and local
integration demonstration, not a mathematical theorem or general PFP ranking.

Both remaining OEWAS epics are implemented for the selected DEV system. This
change repairs malformed parser restriction erasure, stale task-shape admission,
native replacement-wire drift, historical Woland-route reading and Anthropic
usage settlement. The current OEWAS skill and its IDE projections carry the
corrections. No framework, crate, scheduler or concurrency mechanism was added.

## Actual campaign

The original $2 campaign continues on the same live SQLite ledger. The user's
2026-10-16 decision retains the original 1,014-micro-USD unknown charge; that
attempt is never resent. The first continuation received a valid Haiku answer,
then correctly halted because the meter rejected `speed: "standard"`. Its exact
retained response was later rechecked and rated at 290 micro-USD with **zero
provider calls**. Original unpriced evidence remains in its reconciliation event.

The repaired campaign completed P0–P4. There are **45 ledger attempts: 44 settled
responses and one historical conservative charge**. Response counts are 34
Haiku, seven Sonnet and three Opus. Total ledger charge is **67,134 micro-USD
($0.067134)**, including the 1,014-micro-USD reserve. Usage-rated costs are not an
observed vendor invoice. No new unknown settlement remains.

| Stage | Cases | Responses | Final model-accepted | Separately host-solved | Charge, micro-USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| P0 | 196 controls + 18 host controls | 0 | — | 18 controls | 0 |
| P1 | 8 | 7 | 3 | 0 | 18,449 |
| P2 | 8 | 6 | 4 | 2 | 14,031 |
| P3 | 15 | 28 staged responses | 15 | 0 | 10,386 |
| P4 | 4 | 3 | 2 | 1 | 24,268 |

Three wrong final answers, four envelope failures and the old ambiguous attempt
remain in the 35-case results. These were not rerun to improve scores. M5 was
selected by the registered training procedure. Small, related generated cases
and sparse held-out/model samples cannot establish a universal winner or prove
the registered improvement hypotheses. Composition and host-solvable strata,
paired comparisons and uncertainty are retained in `campaign2/campaign.json`.

The storage fixture grew from 1,144 expanded bytes to 2,033 compact bytes while
reproducing identical requests. It demonstrates fidelity, not token savings.
The MUB exact-count item remains external to its owner and was not dispatched.

## Evidence locations and custody

- `campaign/`: first continuation registration, reviewed amendment, actual
  captured answer and stopped results. Its prior source bytes are in
  `first-continuation-registered-sources.zip`; all 25 hashes match its registration.
- `settlement/retained_settlement.json`: exact zero-send settlement and original
  unpriced outcome. It preserves the old conservative charge separately.
- `campaign2/`: linked successor registration/amendment, all collated results,
  raw public responses and the exact 25-file source archive for the final calls.
- `observations/`: fresh authenticated model-list response and public pricing
  source/observations. Credentials were used only in the API request headers.
- `campaign-final.json`: concise stage/accounting/analysis projection.
- `source-contract-result.json`: independent literal ordered-signature experiment
  through the real compiler, selector and ephemeral fixture-signature verifier.
- `candidate-public-ports.xml`, `root-parser-check.xml`, `independent-ports.xml`:
  actual selected checks. `woland_closeout.json` records the separate full-Retinue
  workflow and replay; it is not provider-performance evidence.
- `SHA256.json`: publication file hashes; the historical 20261015 packet is
  unchanged. Absolute paths in original records are retained custody references,
  not portable filesystem claims. The copied raw bytes remain available here.

Pricing was checked against the [official pricing page](https://platform.claude.com/docs/en/about-claude/pricing)
and selected IDs against the authenticated Models API. Standard input/output rates
per million tokens were Haiku $0.10/$0.50, Sonnet $2/$10, Opus $4/$20. Requests
disabled tools/cache, omitted unsupported generation seeds and temperature,
and retained local experiment seed separately. Exact observations are in the packet.

## Executed commands

From the repository root using the existing project interpreter and selected host:

```powershell
$env:PYTHONPATH=(Get-Location).Path
$env:PYTHONUTF8='1'
$env:OMEGA_SYMBOL_GAME_HOST=(Resolve-Path '.scratch/oewas-complete-20261016/candidate-runtime/host.exe').Path
$campaignLedger='.scratch/oewas012/pilot/accounting.sqlite3'
$observations='.scratch/oewas-complete-20261016/observations'
$decision='human-approved call_97c39e4251dd4bd2b994692df1bfd1fd 2026-10-16 retain full reserve and continue within original USD2'
```

The completed execution used an initial reviewed continuation and then this
zero-dispatch settlement followed by a reviewed successor. These historical commands
are not authorization to restart spending or overwrite their output directories.

```powershell
python -B -m omega_engine_pfp.infrastructure.management_ladder --output .scratch/oewas-complete-20261016/settlement --settle-retained-replies .scratch/oewas-complete-20261016/campaign --accounting-path $campaignLedger
python -B -m omega_engine_pfp.infrastructure.management_ladder --output .scratch/oewas-complete-20261016/campaign2 --prepare-continuation .scratch/oewas-complete-20261016/campaign --accounting-path $campaignLedger --authorization-reference $decision --prices-path "$observations/prices.json" --model-access-path "$observations/access.json" --models-response-path "$observations/models.json"
python -B -m omega_engine_pfp.infrastructure.management_ladder --output .scratch/oewas-complete-20261016/campaign2 --reviewed-amendment .scratch/oewas-complete-20261016/campaign2/continuation_amendment.json --accounting-path $campaignLedger --authorization-reference $decision --prices-path "$observations/prices.json" --model-access-path "$observations/access.json" --models-response-path "$observations/models.json" --execute
```

Native host SHA-256:
`769d8c7bdc04ca89a6c9413316512571293b455af22981293fc1d80c7d1ef594`.

```powershell
cargo build --offline --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_symbol_game --bin omega_symbol_game -j 1 --target-dir .scratch/oewas012/native-target
cargo test --offline --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_workflows_agents_skills --test estate_lifecycle_contract --test estate_composition_contract -j 1 --target-dir .scratch/oewas012/native-target
python -B -m pytest --override-ini addopts= -q omega_engine_pfp/tests/test_management_ladder_continuation.py omega_engine_workflows_agents_skills/tests/integration/test_catalog_composition_contract.py omega_engine_workflows_agents_skills/tests/integration/test_higher_operad_adapter.py --basetemp .scratch/oewas-complete-20261016/candidate-public-ports
python -B -m omega_engine_workflows_agents_skills.documentation.examples.prior_art_contract_binding --repo-root . --output .scratch/source-contract/result.json
```

The selected public-port batch passed 39 checks; parser/SQLite refusal controls
passed 61, and retired-route/raw-ingress/StructureBench controls passed 38.
The native estate targets passed 23 checks; the owning Anthropic fixtures passed
20 after an observed standard-speed failure. IC route/active-reader checks
passed 23 normally after a restricted-token Windows junction failure. These are
scoped results with overlaps, not a summed whole-suite result. Independent
source-context controls and original-task rechecks are retained separately.

The full prior-art source audit is outside the selected DEV contract: frozen
Woland inventory parsing now works, but a missing retained research PDF correctly
returns `HISTORICAL_BYTES_UNAVAILABLE`. Production custody/power-loss durability,
uninvoked IDE activation, unrestricted mathematical claims and MUB admission are
not claimed by this closeout.

The complete campaign was replayed through the existing owner with a quote-only transport that rejects every attempted new dispatch. All 44 raw replies rechecked, the 45-attempt ledger and 67,134-micro-USD liability stayed unchanged, and the complete campaign JSON projection remained byte-identical. See `campaign-replay.json`.

The actual outer IDE run `oewas-completion-20261016` completed all 22 Retinue roles, 33 recorded actions and 22 checked IDE captures, with two successful original-task checks and one scoped AutoP/learning finish. UNS `uns.md`, UTS `uts.jsonl` and the single DDA tape `ddc.jsonl` finalized through the canonical sink. Sequential host perspectives are not 22 independent models. All applicable diagnostic checkpoints passed; the evidence verdict remains `OPEN_RESIDUAL` rather than claiming mathematical authority. Read-only replay and native bundle recomputation passed with zero provider calls; see `woland_closeout.json`.


## Release byte normalization

Final staging detected CRLF ordinary sources under the repository's LF Git policy.
The exact completed-run bundle and working history are retained in `woland_run.zip`;
all 28 final run-bound artifacts are retained in `pre_release_sources.zip`.
`release_normalization.json` crosswalks their original hashes to the release sources.
Ordinary source changes in this release step are LF-only; capability projections
and the epic manifest were regenerated from those canonical bytes. The catalog
and manifest auditors then checked the release tree. Campaign registrations and
their exact source archives remain unchanged. A source hash changes on LF
normalization, so the historical campaign/run is not retrospectively relabeled
as having executed the later release byte layout. No provider calls were made
for this step. `release-public-ports.xml` records the final focused boundary check.

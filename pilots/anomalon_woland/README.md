# PFP Pilots: Empirical Verification & Foundational Demonstrations

**AuthorityEffect:** None.  
**Domain Location:** [`omega_engine_woland/tests/pilots/`](./)

**Task and history register:** [`matrix/max_pilot_matrix.yaml`](matrix/max_pilot_matrix.yaml)
**Foundational Pilot Output:** [`results/`](results/)  
**Governing Standard:** Proposal Fidelity Protocol (PFP v0.2), Single Prompt Standard (`SPK-001`)  

---

## 1. Start with a useful, repeatable demonstration

The primary goal is the simplest cost-effective PFP procedure that can be reused
across tasks. Follow the [current usage guide](../../../omega_engine_pfp/documentation/pfp_seed_execution.md)
for one bounded run, its checked result and offline replay. Explain how it works
and why each operation helps before expanding into representations, templates,
modes, stages, repair loops or alternate orders of operations.

The secondary goal is targeted discovery of LLM/system failures, antibodies and
useful patterns. Choose each experiment for a concrete question and apply useful
learning to prompts, existing typed guidance or code. PFP is work in progress;
observed failures determine where additional engineering is needed.

The former fixed pilot grid and generator are retired. Retained catalogs and
dimensions are available choices, not a campaign quota. The comparison below
describes the historical pilot estate rather than a required delivery schedule.

| Architectural Dimension | Legacy "Demos" (former `demos/`) | Empirical "Pilots" (`pilots/`) |
|---|---|---|
| **Execution Reality** | Offline host checks, mock completions, `raw_usage.dry_run: true` | Live model dispatches against frontier providers via `omega_engine_woland.infrastructure.providers` |
| **Financial Boundaries** | None (simulated or unbudgeted) | Strict hard budget ceilings ($0.50 legacy limit, $0.010 active migration limit, micro-USD tracking) |
| **Telemetry & Metrics** | Heuristic or absent latency/token metrics | Exact per-dispatch wallclock latency, input/output token counts, and spend |
| **Verification Gate** | Informal assertions or local python scripts | Deterministic, typed host checkers and typed Pydantic v2 schemas |
| **Claim Discipline** | Occasional informal assertions | Strict Claim Hygiene: narrow claims, no hype verbs, bounded toy evaluator posture |
| **Output Integrity** | Fragmented per-model or per-round text files | Coalesced canonical manifests (`spec.yaml`, `seed.yaml`, `p_star.yaml`, `prompt_template.yaml`, `response.yaml`) |

---

## 2. Master Matrix & Experimental Estate Architecture

All pilot-level specifications, parameters, test outcomes, migration history, and legacy registries are decoupled from this overview document and maintained across three canonical subsystems:

1. **Experimental Methodology & Hypotheses ([`certified_ladder/`](certified_ladder/)):**  
   Pre-registered experimental design ([`design.md`](certified_ladder/design.md)), 14 falsifiable hypotheses ([`hypotheses.yaml`](certified_ladder/hypotheses.yaml)), and the automated hypothesis evaluation harness ([`hypothesis_evaluator.py`](certified_ladder/hypothesis_evaluator.py)).
2. **Universal Parametric Register ([`dimensions/`](dimensions/)):**  
   Optional experimental dimensions and outcome metrics ([`dimension_register.yaml`](dimensions/dimension_register.yaml)), backed by Pydantic v2 domain models in `omega_engine_pfp.domain.pilots`. Select the dimensions relevant to the question; do not automatically cross them.
3. **Master Matrix Estate ([`matrix/`](matrix/)):**  
   Indexed by [`matrix/matrix_manifest.yaml`](matrix/matrix_manifest.yaml), containing retained task/history records ([`max_pilot_matrix.yaml`](matrix/max_pilot_matrix.yaml)), reusable [`seeds.yaml`](matrix/seeds.yaml) and schemas.

The master matrix governs four core registries:

1. **Active Pilot Matrix (`pilots`):**  
   Numbered pilots and their actual execution state. A planned prompt, completed provider call, and accepted host witness are distinct states; consult the matrix and per-test receipts.
2. **Migration Register (`migration_register`):**  
   Historical registry of rewritten pilots. Directories on disk are `pilot_0000026` through `pilot_0000050` (formerly `pilot_000001` through `pilot_000025`). Register names `pilot_000026` through `pilot_000056` have no directory. The `llm_on_offline_pilots` harness covers numbered quizzes 01–20 and expansion pilots 1–35, including scoped test counts, statement/branch coverage, and mutation kill receipts.
3. **Legacy Foundational Register (`legacy_foundational_register`):**  
   Historical empirical records from `PFP-PILOT-001` (Single-Turn Prompt Encoding Parity across 4 frontier models and 64 dispatches) and specifications for planned investigations `PFP-PILOT-002` through `PFP-PILOT-005`.
4. **Legacy Demo Pilots Register (`legacy_demo_pilots_register`):**  
   Historical mappings for demonstration packages, with current source-custody and pilot replacement pointers in the matrix.

---

## 3. Claim Hygiene Mandate

1. **What this pilot infrastructure supports:**
   - Empirical validation that LLMs can parse and execute instructions structured in relational, symbolic, or JSON wire encodings.
   - Exact measurement of framing token overhead and wallclock latency under verified budget constraints.
   - Deterministic host gate evaluation of net structure delta ($Net = \Delta_{\text{created}} - \Delta_{\text{removed}}$).
2. **What it does not support:**
   - Claims of emergent reasoning superiority or token compression for isolated, unbatched symbolic single turns.
   - Mathematical verification of LLM reasoning outside declared toy evaluator bounds.
3. **Authority Effect:**
   - Strictly `AuthorityEffect: None.`.

---

## 4. Pilot Catalogs: LLM | NO_LLM

A pilot is one checked run of one PFP artifact. There are two kinds, and a catalog file holds only one kind.

| kind | what runs | network | judged by |
|---|---|---|---|
| `NO_LLM` | a hard-coded host check over a known structure (gate, stage, mode, packet, grammar case) | none | the check itself |
| `LLM` | one OpenRouter call per (target, params, model) | OpenRouter, only with `--live` | a host check named in `response_check_id`; the model never grades itself |

### Catalog Files

| file | role |
|---|---|
| `no_llm_catalog.yaml` | NO_LLM families |
| `llm_catalog.yaml` | LLM families, with per-family budget |
| `matrix/pilot_models.yaml` | JSON Schema, generated from PFP domain models (do not edit manually) |

### Families, Not Files

A catalog stores families. The existing family machinery can expand `targets x axes x models`, but a run must explicitly select a bounded subset that answers its question. Each instance gets `pilot_id = sha256(canonical([family_id, target_sha256, params, model]))`, so the same bytes and parameters always produce the same ID. `max_instances` is a hard ceiling, not a target.

### Execution

```bash
python python/controllers/pilots_cli.py pilots/no_llm_catalog.yaml          # exit 0 when all met
python python/controllers/pilots_cli.py pilots/llm_catalog.yaml             # every pilot NOT_RUN, exit 1
python python/controllers/pilots_cli.py pilots/llm_catalog.yaml --live --ledger runs/provider_ledger.json
```

`NOT_RUN` never counts as met. An LLM pilot's provider `request_id` is `llm_request_id(target bytes, model)`, so pilots that differ only in check parameters share one call, and a rerun reuses its ledger row instead of paying twice. The runner halts a family's new calls at its `budget`.

---

## 5. Directory Architecture

```
omega_engine_education/pilots/
├── certified_ladder/        # Experimental design, price schedules & hypothesis harness (H0-H13)
│   ├── design.md            # Formal pre-registered experimental methodology
│   ├── hypotheses.yaml      # 14 falsifiable hypotheses with refutation criteria
│   └── hypothesis_evaluator.py # Automated hypothesis verification harness
├── dimensions/              # Universal parametric coordinate system & outcome definitions
│   └── dimension_register.yaml # 100+ experimental dimensions across 17 factor groups
├── matrix/                  # Canonical pilot matrix, seeds, schemas, and data manifests
│   ├── matrix_manifest.yaml # Retained task records, seeds and schemas
│   ├── max_pilot_matrix.yaml # Sovereign pilot matrix & migration registers (75 active)
│   ├── pilot_models.yaml    # JSON Schema models
│   └── seeds.yaml           # Review and MSS-N seed catalog
├── results/                 # Standardized 5-artifact results estate (pilot_0000000 - pilot_00074)
│   └── pilot_XXXXXXX/       # spec.yaml, seed.yaml, p_star.yaml, prompt_template.yaml, response.yaml
├── demo_000/                # S(n), MSS-N, and Genesis PFP review suite
├── replay_runners/          # Active materializers and replay runners for retained pilots
├── demo_004/                # Challenge specifications and implemented challenge packages
├── antibodies/              # Retained epistemic antibody definitions and negative controls
├── token_budget/            # Token accounting and budget gates
├── offline_evaluator.py     # Deterministic offline host evaluation engine
└── live_evaluator.py        # Historical observation regrading; fresh dispatch retired
```

---

## 6. Local Verification & Execution

From the repository root with Python 3.12:

Fresh model calls use the canonical bounded PFP runner. Replace `MODEL_ID` with
the selected OpenRouter model and `NEW_DIRECTORY` with a new output directory:

```sh
pfp run-seed DEMO_07 --model MODEL_ID --output NEW_DIRECTORY
```

The old `live_evaluator` entry point can still regrade bound saved observations.
Fresh pilot-directory dispatch returns `LEGACY_LIVE_REQUIRES_CANONICAL_PFP`
before reading credentials, creating an attempt or contacting a provider.
Existing response and interrupted-attempt bytes remain unchanged.

```sh
# Replay preserved model replies through the exact host checks; no network
py -3.12 -m omega_engine_woland.tests.pilots.replay_runners.dossier_capsules.run --replay --session free_followup
py -3.12 -m omega_engine_woland.tests.pilots.replay_runners.dossier_capsules.learn
```

Build native Rust operations:
```sh
cargo build --locked -j 1 -p omega_symbol_game
```

Missing native capability is a typed refusal; it is not a certificate. Each demo has its own carrier, predicate, and output contract. Live model runs require separately authorized provider credentials, explicit budget limits, and authenticated cryptographic receipts.

# P1 rewriting A/B (with H3 wire+qed arm)

AuthorityEffect: None. Plan: anomalon `reports/pfp_proving_plan_2026-11-17/plan.md`, test P1 (approved by the owner 2026-11-17, about $0.60, gpt-5-mini).

Status: kit, runner, grader and tests built. No model call made yet.

- `build_tasks.py` writes `tasks.jsonl` (30 tasks, 110 calls). Deterministic: rebuild gives sha256 `452c1b2f5c2369ffa7c8dd5e6995bd7ce5d610c5079dba809f069ab1c8fb1fe0`.
- Family S, 20 exact integer sums with one trigger sentence each (dedup, round, positive, mean). Arms: `prose` (triggers), `plain` (control), `wf5` (real WF5 Gamma38 packet, decode round-trip asserted), `fenced` (WF21-style fence, original bytes recoverable). Each task records the trigger-predicted wrong total, so a wrong answer can be classed as "pulled".
- Family H, 10 exact discrete Hodge splits. H00 is the calibration-bank task; its reference passes `workflows/tasks/calibration_task_bank/tasks/hodge_split/check.py`. Arms: `prose`, `wire` (same content), `wire_qed` (Symbol Game proof skeleton ending in `qed`; adds method content, so compare `wire` vs `wire_qed` for the skeleton effect).
- The system message (answer contract) is identical across arms of a family.

## Run (PowerShell, from the PFP repository root; stdlib Python, key only from `--env-file`)

```powershell
cd experiments\p1_rewrite_ab
uv run --no-project python run.py --dry-run --ledger ledger_dry.jsonl      # no network, every grade CORRECT
uv run --no-project python run.py --env-file C:\Users\a343o\source\repos\anomalon\.env --confirm-live 750000 --limit 2
uv run --no-project python run.py --env-file C:\Users\a343o\source\repos\anomalon\.env --confirm-live 750000
uv run --no-project python run.py --tasks tasks_tier_s.jsonl --ledger ledger_tier_s.jsonl --env-file C:\Users\a343o\source\repos\anomalon\.env --confirm-live 750000
uv run --no-project python grade.py --tasks tasks.jsonl --tasks tasks_tier_s.jsonl --ledger ledger_live.jsonl --ledger ledger_tier_s.jsonl > report.json
```

- `run.py`: gpt-5-mini-2025-08-07, reasoning effort low, one call per (task, arm), no retries. Append-only ledger: an intent before each send and a result after it. An intent with no result is held and never resent. Costs are integer nano-USD from the reply usage at 1/4 and 2 micro-USD per token. A hard cap of 750,000 micro-USD stops the run before any call that could cross it. A rerun skips everything already done.
- `grade.py`: exact grades CORRECT, PULLED (the trigger-predicted wrong total), WRONG, MALFORMED, TRUNCATED, NO_REPLY and NOT_RUN. Paired discordant counts per comparison, with the exact sign-test p as a fraction. No float anywhere.
- `test_p1.py`: 22 tests (run in CI by the `Experiment kits` step of `pfp_v1rc_gates.yml`) (`uv run --no-project --with pytest python -m pytest test_p1.py`). Two injections were proved: resending a held call, and dropping the PULLED class. Each turns a test red.

## Fourth Hodge arm: strict Tier S (`tier_s.py`, `tasks_tier_s.jsonl`, 10 calls)

The source is omega_codex `education/3_minimal_symbol_systems/rewriting/rewriting_strategies_mssn_wire.md`.

**How the earlier arms differ.** The `wire` and `wire_qed` arms are Tier H style: head words, commas, `=`, `-` and parentheses. The parentheses are not even in that document's Tier H alphabet.

**What `tier_s_qed` uses.**
- Strict Gamma38 only (a-z, 0-9, `<`, `>`), with no whitespace or punctuation.
- The Definition 2.2 packet grammar.
- R1 carrier declaration `<<decl>...>`.
- R7 role packets: assume, derive, check.
- `<<neg><n>>` for negative entries.
- It ends in `<<terminal><<qed><exact>>>`. nf.mssn.bqnf.yaml treats that stamp as UNVERIFIED until the host replays it, and here the exact grader is the replay.

**Kept the same.** The content and the wire_qed skeleton are unchanged, and so is the JSON answer contract. A separate task file keeps `tasks.jsonl` frozen. `grade.py` merges the two files by task id and adds the pairs tier_s_qed vs wire_qed and tier_s_qed vs prose.

**Tests.** The text is checked to be strict Gamma38, to parse as one packet, and to decode back to the instance's edges and flow. The parser refuses malformed packets.

## Hodge rerun v2 (`hodge_v2.py`, `tasks_hodge_v2.jsonl`, 40 calls). RAN 2026-11-17

**Why.** In the first live run, 21 of 25 MALFORMED Hodge replies wrote b0, b1 and euler_characteristic as strings. The v1 contract caused this: it calls those fields integers, then says "write every rational value as a string".

**What v2 changes.** Only the system message, which now names those three fields as JSON integers. The instances, references, all four arms and the strict grader are unchanged. sha256 `f8b86bb3…80df`.

**Result (gpt-5-mini, $0.40).** prose 7/10, wire_qed 7/10, wire 6/10, tier_s_qed 4/10; MALFORMED fell from 25 to 2. Receipts are in the anomalon project files under `reports/pfp_proving_plan_2026-11-17/p1_hodge_v2_2026-11-17/`.

## H1: typed turn vs orchestrator prompt (`h1.py`, `tasks_h1.jsonl`, 60 calls)

Both arms carry the same task text and answer contract. That is the P1 `prose` text: sums keep the trigger sentence, and Hodge uses the v2 contract.

- **`orchestrator`:**
  - system: a multi-agent "SolverAgent" persona plus the contract;
  - user: the task prose.
- **`typed`:**
  - system: a typed-turn handler plus the contract;
  - user: one `llm_turn_v1` request as JSON, which validates against `pfp/infrastructure/yaml/schemas/llm_turn_v1.schema.yaml`;
  - reply: `{"task_id", "CANDIDATE", "AUTHORITY_EFFECT": "None"}`. `grade.py` unwraps it, and any wrapper fault grades MALFORMED.

`run.py` sends the per-arm system message (`arm_system`). The P1 and v2 request bodies are unchanged: their ledger intent hashes reproduce. sha256 `482edbca1a16286d1c2c9666b6d9df9088cb8923d461859c64f42fbae85ee220`. Tests: `test_h1.py`, 5 tests, which need jsonschema and pyyaml. A wrapper-check injection turns 2 of them red.

```powershell
uv run --no-project python run.py --tasks tasks_h1.jsonl --ledger ledger_h1_dry.jsonl --dry-run
uv run --no-project python run.py --tasks tasks_h1.jsonl --ledger ledger_h1_live.jsonl --env-file C:\Users\a343o\source\repos\anomalon\.env --confirm-live 750000
uv run --no-project python grade.py --tasks tasks_h1.jsonl --ledger ledger_h1_live.jsonl | Set-Content -Encoding utf8 report_h1.json
```

## Ledger binding and location (review of #152, 2026-11-17)

- **Every record is bound to its exact request.** The request hash covers the system message, the arm's text, the model, the effort and the token limit. A result is bound to the intent before it. `run.py` refuses a ledger that holds any (task, arm) under another request (`LEDGER_REQUEST_MISMATCH`) before it sends anything, and `grade.py` refuses to grade one. So a v1 ledger can no longer satisfy or grade the v2 kit, which reuses the v1 task ids and arm names. `test_v1_ledger_cannot_count_as_v2` is the regression; removing either refusal turns it red. Disjoint arms, such as `tasks.jsonl` plus `tasks_tier_s.jsonl`, still share a ledger.
- **The live ledgers bind.** Regrading the three live ledgers from Jeremy's PC under the new binding gives the same reports as before (`report.json`, `report_hodge_v2.json`, equal as JSON).
- **Location.** The kit moved from `workflows/experiments/` to the top-level `experiments/`, which no governed population covers. The repository-wide `experiments` directory-name exclusion is withdrawn, so `pfp/experiments/`, `workflows/experiments/` and the like stay governed. `test_only_this_lab_is_outside_governance` pins that.

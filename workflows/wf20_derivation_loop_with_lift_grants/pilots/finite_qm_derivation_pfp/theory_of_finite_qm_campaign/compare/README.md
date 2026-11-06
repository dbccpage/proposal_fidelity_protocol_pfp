# Fable versus swarm: how to run the comparison

AuthorityEffect: None. Read `protocol.md` first: it is the pre-registration, frozen by the sha256 in `cohort.json`.
This harness was built without any provider call, Lean, cargo, pytest or spend. Its dry-runs and `py_compile` are the only
things that were executed. The live paths (the swarm and Fable runs, the verifier subprocesses of `score.py`) are therefore
untested against real providers and a real Lean build: watch the first prompt.

Question: can a swarm of free and cheap models plus the PFP ladder produce, on the same prompts, the verifier-accepted results
that Fable produced, at a fraction of the cost? Score = what a verifier accepts, nothing else: Lean 4.35.0 files with
`#print axioms` limited to `propext`, `Classical.choice`, `Quot.sound` (L); passing Rust or Python witnesses (W); host-verified
operad entries (O). Abstentions and failures stay in the denominator and their spend in the numerator.

| File | Role |
|---|---|
| `protocol.md` | hypothesis, cohort rule, arms, fairness, rubric, decision rule, threats |
| `cohort.json` | the 15 prompts (6 D, 3 P, 6 C): prompt and collection sha256, freeze commit, exclusion list, Arm F run, model, cost, on-disk verdicts |
| `build_cohort.py` | rebuilds `cohort.json` from git and the run folders (read only; deterministic for a base commit) |
| `run_swarm_arm.py` | Arm S through `dag/pfp/llm_ladder` |
| `run_fable_arm.py` | optional fresh Fable, same bytes, costs money |
| `score.py` | blinded verifier-only scoring, cost per accepted result, decision |
| `compare_common.py` | clean room, packet loaders, leak guard, call and wall-clock caps |

Everything is run from the repository root with `python -I -X utf8 ...`. Keys (`ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`,
`GROQ_API_KEY`) are read at run time by the ladder's own loader from the environment or the `.env` files it already searches;
nothing prints, logs or copies them. A dry-run reads no key.

## 1. Look before you spend (no network, no key)

```
python -I -X utf8 dag/pfp/compare/run_swarm_arm.py --dry-run
python -I -X utf8 dag/pfp/compare/run_swarm_arm.py --dry-run --compile-packets
python -I -X utf8 dag/pfp/compare/run_fable_arm.py
```

The first prints the plan for all 15 prompts, the tiers and the worst-case paid cost. `--compile-packets` also builds each clean
room under `%USERPROFILE%\.fvs` (about 80 to 100 MB, removed at once), compiles the packet, checks the leak guard and prints the
packet digest; for the P prompts it checks the stored request against the sha256 frozen in `cohort.json`. The third is the
Fable dry-run (its default) with the worst-case cost. Packets are about 1,500 to 2,900 input tokens (all 15 compiled cleanly and passed the leak guard when this harness was built; the
clean rooms of the controls drop 39 Arm F files that exist at the base commit, those of D and P drop none because the freeze
commit predates them).

## 2. Arm S, the swarm

```
python -I -X utf8 dag/pfp/compare/run_swarm_arm.py --confirm-spend --arm-cap-usd 2.00
```

* Tiers 0 to 2 (free models, gpt-4o-mini on OpenRouter, Haiku 5.5). `--max-tier 0` is free models only and needs no
  `--confirm-spend`. Opus and Fable are refused; `--max-tier 3` (Sonnet) is a recorded deviation.
* One run per prompt (the protocol). Order is the cohort order: D, then P, then C. `--only NODE[,NODE]` and `--strata D,P` select;
  a run that stops early can be continued with `--only` for the prompts not yet run.
* Output: `dag/results/<NODE>/runs/<ts>_compare_swarm/` (ladder layout plus `compare_swarm_receipt.json`: protocol sha, packet and
  clean-room hashes, caps, leak check, spend) and `dag/pfp/compare/receipts/swarm_arm_<ts>.json`. The ladder ledger
  `dag/pfp/llm_ladder/budget_ledger.json` is updated; commit it with the results.
* **Expected cost.** Free tiers cost 0. Paid tiers are used only after free attempts were rejected: at most about 0.01 USD per
  prompt at these packet sizes, so a worst case of 0.14 USD for all 15 prompts (`--dry-run --compile-packets` prints it; plain `--dry-run` assumes 12,000 tokens and prints 0.21), far below
  the 2.00 USD arm cap and the 0.25 USD per-prompt cap.
* **Time.** Free providers are spaced 3 s apart and rate limited: about 1 to 5 minutes per prompt, 20 to 75 minutes for the arm,
  plus about 30 to 60 s per prompt to build the clean room.
* **Disk.** One clean room at a time, deleted after each prompt (`--keep-cleanroom` keeps them); peak about 0.2 GB. Run folders are small.

## 3. Arm F, optional fresh Fable (this spends real money)

```
python -I -X utf8 dag/pfp/compare/run_fable_arm.py --compile-packets
python -I -X utf8 dag/pfp/compare/run_fable_arm.py --confirm-spend --usd-cap 8
```

Without it the primary test has at most 3 eligible prompts (the P stratum) and is INCONCLUSIVE by rule. The default is the D
stratum (6 prompts), up to 3 answered attempts each, tier-5 settings of the ladder (effort medium, 8,000 max tokens), no tools,
the swarm's packet, the same verifier. It refuses without `--confirm-spend` and a positive `--usd-cap`, reserves each call's
worst case before sending, and applies the weekly Anthropic cap of the ledger.

* **Expected cost.** A reply is 450 to 2,900 tokens on Claude at these settings (`llm_ladder/design.md`), so about 0.03 to 0.15 USD
  a call and 0.2 to 1 USD for six prompts that are accepted at the first attempt. Worst case, every attempt at its token cap:
  about 1.3 to 1.5 USD a prompt, about 8 to 9 USD for the arm; hence the explicit cap.
* **Time.** Seconds to a few minutes per call.
* Output: `dag/results/<NODE>/runs/<ts>_compare_fable/` and `receipts/fable_arm_<ts>.json`. `--effort` and `--max-tokens` are
  labelled SENSITIVITY runs.

## 4. Score

```
python -I -X utf8 dag/pfp/compare/score.py                                   # reads receipts; writes the blinded table only
python -I -X utf8 dag/pfp/compare/score.py --reverify-o                      # re-checks operad entries against rebuilt clean rooms (local, no Lean)
python -I -X utf8 dag/pfp/compare/score.py --run-verifiers --reverify-o      # Lean 4.35.0, pytest, cargo as subprocesses
python -I -X utf8 dag/pfp/compare/score.py --run-verifiers --reverify-o --unblind
```

Read `blinded_table.md` before the last command. The confirmatory scoring is the one with `--run-verifiers --reverify-o`; without
it units stay `unverified` and the decision cannot be SUPPORTS. Output goes to `dag/pfp/compare/scores/<ts>/`:
`blinded_table.md`, `blinded_scores.json`, `report_blinded.md`, `score_receipt.json`, and with `--unblind` `report.md` (arm-resolved table, cost per
accepted result by class, the decision of protocol.md section 8).

What `--run-verifiers` needs and costs:

* **Lean.** A `lean4/` project whose lake environment has the Mathlib v4.35.0 build, given by `--lean-project` (default `lean4/`
  of this checkout) and a `lake` that answers `lake env lean --version` with 4.35.0 (`--lake` to point at it); otherwise every Lean unit
  stays `unverified` and says why. It runs `lake build +Module` for each of the 24 Arm F modules that have a `lean4/` copy, then an axiom
  probe per module. With prebuilt dependencies expect minutes per module and one to three hours in all, about 2 GB of RAM per
  Mathlib import; a module that is not a target of the workspace is reported unverified, not rejected. Swarm lemma skeletons are
  elaborated as snippets.
* **Python.** `pytest -q` for the twin test files, `code/python`; seconds each.
* **Rust.** `cargo test --lib <module>` with `CARGO_TARGET_DIR` set to a short path (`--cargo-target`, default `~/.pfp-ct`), no debug
  info; the Rust twins have needed 10 to 18 GB of target in the past. Below `--min-free-gb-cargo` (15) free GB the cargo units are
  left unverified; `--skip-cargo` skips them. The target is deleted afterwards unless `--keep-cargo-target`.
* Unknown Fable cost for D prompts: put real session costs from the Anthropic console in a JSON file and pass
  `--cost-overrides file.json` (`{"<NODE>": {"usd": 12.3, "basis": "console, session of <date>"}}`); otherwise the labelled lower bound is used.

## 5. After the run

Commit `dag/results/*/runs/*_compare_*`, `dag/pfp/compare/receipts`, `dag/pfp/compare/scores` and the ledger. `replay.py` and the ladder's
positive memory glob `*_ladder*`, so these runs do not enter the shared hallucination index. Do not edit `protocol.md` or `cohort.json`:
`load_cohort` refuses a changed protocol. A correction is a new dated protocol and cohort.

## Known limits

* Arm S is P0 only (protocol.md 3.1): no class W, and class L only through a model's own sorry-free skeleton.
* Stratum D is an outcome comparison against agentic sessions whose instructions are not in the repository.
* Companion files (`*.contract.score.yaml`, `*.doc.yaml`) for the new `.py` files were not generated; run `scripts/score_scope_contracts.py` if the gates ask for them.

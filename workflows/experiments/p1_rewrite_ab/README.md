# P1 rewriting A/B (with H3 wire+qed arm)

AuthorityEffect: None. Plan: anomalon `reports/pfp_proving_plan_2026-11-17/plan.md`, test P1 (approved by the owner 2026-11-17, about $0.60, gpt-5-mini).

Status: task kit built, no model call made. Runner and exact grader are NOT written yet.

- `build_tasks.py` writes `tasks.jsonl` (30 tasks, 110 calls). Deterministic: rebuild gives sha256 `452c1b2f5c2369ffa7c8dd5e6995bd7ce5d610c5079dba809f069ab1c8fb1fe0`.
- Family S, 20 exact integer sums with one trigger sentence each (dedup, round, positive, mean). Arms: `prose` (triggers), `plain` (control), `wf5` (real WF5 Gamma38 packet, decode round-trip asserted), `fenced` (WF21-style fence, original bytes recoverable). Each task records the trigger-predicted wrong total, so a wrong answer can be classed as "pulled".
- Family H, 10 exact discrete Hodge splits. H00 is the calibration-bank task; its reference passes `workflows/tasks/calibration_task_bank/tasks/hodge_split/check.py`. Arms: `prose`, `wire` (same content), `wire_qed` (Symbol Game proof skeleton ending in `qed`; adds method content, so compare `wire` vs `wire_qed` for the skeleton effect).
- The system message (answer contract) is identical across arms of a family.

Left to do: stdlib runner (OpenAI chat completions, `gpt-5-mini-2025-08-07`, reasoning_effort low, integer nano-USD cost, hard cap, append-only ledger, no retries, `--dry-run`), exact grader (Fraction/int only, pulled-total class, paired discordant counts with exact sign-test fraction), tests.

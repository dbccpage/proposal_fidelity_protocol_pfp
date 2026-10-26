---
documentation_contract: symbol-game-documentation/v1
title: "Review Findings & Staged Demos Runbook"
kind: runbook
audience:
  - engineers
  - coding-agents
  - testers
status: active
maturity: canonical
claim_status: source-grounded
authority_effect: "None"
source_paths:
  - omega_engine_pfp
  - omega_engine_pfp/entrypoints/cli/pfp.py
  - omega_engine_woland/tests/pilots/matrix/seeds.yaml
last_verified: 2026-10-20
verification_scope: command and catalog paths checked against source; the findings in section 1 were not re-audited
---

# 13. Review Findings & Staged Demos Runbook

Current execution (2026-10-12): [practical PFP and discovery](../_how_to_play/13_practical_pfp_and_discovery.md). Use the consolidated `omega_engine_pfp` commands there; historical profiles below do not imply current runtime support. The fixed pilot grid is retired; each new run should answer a concrete use or discovery question.


**AuthorityEffect:** `None`  
**Classification:** Audit Findings, Implementation Status & Demo Execution Runbook.  
**Status:** Canonical Reference.

---

## 1. Key Audit Findings & Remediations

1. **Primal-Dual Exactness:** Both reference solvers enumerate independent active residual equations over exact rationals, verifying circulation constraints, infinity bounds, and exact zero duality gap.
2. **Parsing Authority Firewall:** Parsing a wire never mints mathematical authority; invalid or unverified wires yield explicit `UNVERIFIED` receipts.
3. **Exact Arithmetic Integrity:** Integer constructors and rational intermediates reject float/boolean coercion and verify checked signed-64-bit bounds.
4. **LGGR Non-Binary Evaluation:** Non-binary inputs and missing flags trigger typed `POLICY_VIOLATION` or `MAP_UNDEFINED` refusals rather than unhandled panics.

---

## 2. 50-Demo Execution Runbook

To execute all 50 target demonstrations locally:

```bash
# Historical entrypoint (2026-10-08); the file is not present at the 2026-10-20 pin
py -3.12 ow/omega_engine_pfp_v0.2/python/controllers/run_fifty_demos.py
```

**Current-source status (2026-10-20, pin `c419cc6beb`).** `run_fifty_demos.py` and the whole `ow/` tree are gone. The current command surface is the PFP CLI ([pfp.py](../../../../omega_engine_pfp/entrypoints/cli/pfp.py)):

| Subcommand | Purpose (from its `help` text) |
| --- | --- |
| `run-demo <demo_id>` | Execute a PFP demo by ID (examples in the help: `demo_000`, `demo_003`, `demo_004`, `demo_sn_000`) |
| `verify-contracts` | Refuses without candidate-bound checking |
| `evaluate-gates` | Evaluate Woland Tribunal gates |
| `assemble` | Assemble a prompt packet |
| `run-pilot-suite` | Multi-test pilot suite, with `--max-cases` (default 5), `--max-provider-calls` (default 5) and `--max-output-tokens` (default 512) |
| `run-seed <seed_id>` | Numbered stages; `--stages` 1 to 11, default 5 |
| `check-seed`, `prepare-task`, `check-task` | Offline candidate and task-turn checks |

The seed catalog read by `_seed_catalog_from_snapshot` ([pilot_runner.py](../../../../omega_engine_pfp/infrastructure/pilot_runner.py) lines 60-104) is [seeds.yaml](../../../../omega_engine_woland/tests/pilots/matrix/seeds.yaml): `total_seeds: 74`, made of 24 review seeds and 50 MSSN50 seeds. The loader refuses a count, folder-index or SHA-256 mismatch. So the "50 demos" of this runbook correspond to the 50 MSSN50 seeds inside a 74-seed catalog. Run one seed at a time; do not run the whole catalog in one command on a low-memory machine. The practical guide linked at the top gives worked commands.

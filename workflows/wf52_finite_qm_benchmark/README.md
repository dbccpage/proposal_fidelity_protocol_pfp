# WF52: Finite-QM benchmark

**Status:** runnable, with recorded live runs (24 graded frozen attempts, USD 0.055614 settled in all; no fully correct answer yet). **Kind:** experiment design. **Builds on:** [WF1](../wf01_typed_answer/README.md), [WF9](../wf09_bounded_check_and_repair/README.md), [WF12](../wf12_mechanism_control_arms/README.md).

**Goal:** Compare whole workflows on one frozen graduate quantum-mechanics problem by cost, tokens, time and independently graded accuracy.

## How it works

1. Every model call gets the unchanged seed [`seed_prompt.txt`](seed_prompt.txt) (SHA-256 in [`commitment.json`](commitment.json)). The worked answer is held privately; only its hash is here.
2. A plan (below) runs under one USD 0.10 whole-run cap shared by all its calls ([`budget_ledger.py`](budget_ledger.py), [`campaign_ledger.py`](campaign_ledger.py)).
3. Host checks (rational panels, exact Hamiltonian matrices, the native characteristic-polynomial checker) can refuse an intermediate artifact; they never certify the final answer.
4. Outputs are frozen, then graded once on a fixed 100-point rubric with no feedback into the run.

## The check

Online: the plan's host check on public contracts only. Offline: the trusted evaluator grades frozen outputs (spectrum 20, dynamics 20, pure entanglement 25, thermal 25, conventions and checks 10).

## Run it

```powershell
python -m pytest workflows/wf52_finite_qm_benchmark -q
python workflows/wf52_finite_qm_benchmark/live_campaign.py initialize --manifest CAMPAIGN_JSON --ledger NEW_LEDGER_SQLITE
python workflows/wf52_finite_qm_benchmark/live_campaign.py run --ledger NEW_LEDGER_SQLITE --run-id RUN_ID --output NEW_RUN_DIR
```

`pfp_core` puts this folder on `sys.path`, so its modules import flat (`import budget_ledger`). About a fifth of the tests need the native Rust checker built from [`native_sidecar_host/`](native_sidecar_host/) or private evaluator material, and fail without them. Only `run` reads `OPENROUTER_API_KEY` and can spend. Full instructions: [`LIVE_RUNNER.md`](LIVE_RUNNER.md), [`EXPERIMENT_PROTOCOL.md`](EXPERIMENT_PROTOCOL.md), [`ACCOUNTING.md`](ACCOUNTING.md).

## Recorded variations

| Plan | Procedure | Calls | Spec | Recorded runs |
| --- | --- | ---: | --- | --- |
| `direct`, `self_critique` | Solve once; draft then audit and revise | 1, 2 | [`reference_runner.py`](reference_runner.py) | [`pilot_20261110/`](pilot_20261110/), [`length_control_20261110/`](length_control_20261110/), [`deepseek_critique_20261110/`](deepseek_critique_20261110/), [`model_control_20261110/`](model_control_20261110/), [`model_control_repaired_20261110/`](model_control_repaired_20261110/) |
| `rational_blind_panel_v1`, `rational_visible_panel_v1`, `rational_fixed_panel_v1`, `rational_fixed_panel_v2` | Solve, then a challenge panel or twelve fixed host probes | 1-2 | [`rational_workflows.py`](rational_workflows.py), [`RATIONAL_PANEL.md`](RATIONAL_PANEL.md) | [`pilot_20261110/`](pilot_20261110/) |
| `hamiltonian_checked_v1`, `hamiltonian_ungated_v1`, `hamiltonian_host_matrix_v1` | Exact Hamiltonian check before synthesis, without it, or host-computed | 1-3 | [`hamiltonian_workflows.py`](hamiltonian_workflows.py), [`HAMILTONIAN_WORKFLOWS.md`](HAMILTONIAN_WORKFLOWS.md) | [`hamiltonian_pilot_20261110/`](hamiltonian_pilot_20261110/), [`hamiltonian_large_model_20261110/`](hamiltonian_large_model_20261110/) |
| `section_allocated_v1` | Five public parts solved separately | 5 | [`section_workflows.py`](section_workflows.py) | [`section_control_20261110/`](section_control_20261110/) |
| `qm_charpoly_checked_v1`, `qm_charpoly_ungated_v1` | Characteristic polynomial checked natively, or not | 2-3 | [`charpoly_workflows.py`](charpoly_workflows.py), [`CHARPOLY_WORKFLOWS.md`](CHARPOLY_WORKFLOWS.md) | [`charpoly_pilot_20261110/`](charpoly_pilot_20261110/), [`host_charpoly_pilot_20261110/`](host_charpoly_pilot_20261110/) |
| EIS/PCIV arms | Two-signal regulation on the same seed | — | [`eis_pciv_workflows.py`](eis_pciv_workflows.py) | [`eis_pciv_pilot_20261110/`](eis_pciv_pilot_20261110/) |

Scores so far: best 88/100 (DeepSeek self-critique), 83/100 for the direct run of the same model; every delivered answer kept mathematical errors. All results: [`results_summary.json`](results_summary.json).

The earlier finite-QM derivation prompt and its stage/mode design are a WF20 pilot: [`finite_qm_prompt/`](../wf20_derivation_loop_with_lift_grants/pilots/finite_qm_prompt/README.md).

## Paths in older records

This folder was `dag/benchmark/` until 2026-11-13. Run records, source snapshots and their pins keep the old path, and pinned sources (`hamiltonian_artifact.py`, `qm_native_charpoly.py`, `qm_host_charpoly.py` and the other modules listed in [`source_custody.py`](source_custody.py)) still name `dag/benchmark/...` inside, because changing a byte would break their recorded SHA-256.

More: [wiki page](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/wiki/Workflow-QM-Benchmark)

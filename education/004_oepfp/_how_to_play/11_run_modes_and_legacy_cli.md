# 11. Run modes and legacy CLI (historical)

**AuthorityEffect:** None.

> **Historical, not re-executed.** These commands come from the archive snapshot. Paths such as `engine/products/symbol_game` and the `symsys-pipeline` binary may be stale. The live implementation is under `crates/core_symbol_game` and `engine_py/core_symbol_game/`. No command below was run for this page.

## Build

```bash
cd engine/products/symbol_game
cargo build --all-targets --all-features
```

## Proof mode

```bash
cargo run -j 1 --bin run_proof_pipeline -- \
  --seed "prove lp duality for bounded polyhedra" \
  --encoding full --backend http --yaml-dir yaml/mode_2_proofer
```

Deterministic local testing uses `--backend file --responses-dir runs/test_fixtures`, which expects `stage_1.yaml` through `stage_8.yaml`.

## Operator mode

An operator is not admitted because the LLM proposes it. Admission needs contract validation, mechanical checks, and operator-lattice validation.

```bash
cargo run -j 1 --bin run_operator_tower -- \
  --domain "linear_algebra" --gap "projection operator" --max-iterations 3
```

## Legacy prompt CLI

`symsys-pipeline` is the manual prompt/report path (`generate-prompt --stage N ...`, `parse-response --stage N ...`) and needs `--features legacy-pipeline`.

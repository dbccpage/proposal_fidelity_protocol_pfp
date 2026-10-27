# Sources walked for v2 how-to-play (2026-09 packet iteration)

Law: DOCS_CONSOLIDATION_LAW.md Family 7 and section 2_how_to_play. YAML stays YAML; this file is provenance only.

## Dest machine contracts (not rewritten)

- 2_how_to_play/how_to_play_yaml/mode_1_symbol_packet_iteration/controller.yaml (SPK-002; public_stage_count 5; rust_crate core_symbol_game)
- stage_1_seed_packet.yaml, stage_2_symbol_expansion.yaml, stage_3_descent_audit.yaml, stage_4_adversarial_rounds.yaml, stage_5_terminal_prompt_synthesis.yaml, packet_family_registry.yaml
- mode_2_proofer/controller.yaml and stage_1..stage_8 YAML
- mode_5_operator/controller.yaml, stage_1_compression_gate.yaml, stage_2_ideation.yaml, stage_5_mss_mu_evaluator.yaml, stage_8_evidence_plan.yaml (other stages present; same 8-stage inventory)
- support/mode_5_operator/mss_mu_controller.yaml
- support/mode_2_proofer/paper_refinement.yaml
- symbol_game_integrity_contract.yaml (SGI-001)
- symsys_config.yaml (mode symbol_packet_iteration; max_round_count 5; 5-stage + 8-stage template maps)
- mode_1_candidate_ideas_proposer/controller.yaml (SPK-001; not public v2 Mode 1)

## Dump sources now landed next to this guide (not replacements of `how_to_play.md`)

- `2_how_to_play/v2_modern_2026-09_packet_iteration/symgam_new_intructions.md` (v2 source overlay; DRAFT DESIGN NOTE; dump spelling; 16,244 bytes; SHA-256 `680da54b6a39d3dd271d9ce5d98a07ce990d2a85aa28ebcfb178f1ea8f3cf68e`)
- `2_how_to_play/v2_modern_2026-09_packet_iteration/symgam_new_instructions.md` (tower spelling; 16,691 bytes; SHA-256 `03b7bc127f75aabbb7df94472a93600fbb8a72d64b39298e5cfc420db7e913f7`). **Not byte-identical** to the dump typo file. Do not overwrite either.
- `2_how_to_play/v2_modern_2026-09_packet_iteration/architecture.md` (disagreed: public stages 1–8, math_spine canon, old cargo paths)
- `2_how_to_play/v2_modern_2026-09_packet_iteration/packetization_9_stages_mss_mu.md` (internal 0+1–8 DAG only; not public SPK-002)
- `2_how_to_play/v1_historical_2026-05_lp_forcing/dump_original_how_to_play.md` (v1 dump original; LP-forcing + 8 public stages + stale cargo paths)

## Dest crate and theory pointers

- code/rust/Cargo.toml (package name core_symbol_game)
- code/rust/README.md, src/bin/run_sg.rs, src/bin/core_symbol_admit.rs, tests/symbol_packet_iteration_e2e.rs
- 1_historical_documents/05_modern_synthesis.md
- 0_research_briefs/20_modern_benchmark_opus_5_ultracoda.md
- Paper 043 (The Symbol Game: Finite Packetization, LGGR, and the Authority Firewall) is the theory-spine pointer; math_spine is not canon for v2.
- dest papers/032 (PO-032) is a different dest monograph and is not this version’s spine pointer.

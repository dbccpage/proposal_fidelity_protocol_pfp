# Sources for v1 historical how-to-play (2026-05/06 LP-forcing)

**AuthorityEffect:** None
**Dest file:** `2_how_to_play/v1_historical_2026-05_lp_forcing/how_to_play.md`
**Writer:** howto-v1-historical
**Walk date:** 2026-09-12

Player guide, not a second monograph. Does not flatten live YAML under `2_how_to_play/how_to_play_yaml/`.

## Source of truth

| Dump path | Role |
|---|---|
| `2_how_to_play/v1_historical_2026-05_lp_forcing/dump_original_how_to_play.md` (moved from `symbol_game_docs/how_to_play_the_symbol_game.md`) | Core Idea, `lp<...>` example, local/global checks, packet-level terminals and failure vocab. Eight-stage cargo CLI recorded as a later overlay, not as the original game and not as a live recipe. This is the dump original, **not** the player guide `how_to_play.md`. |

## Merge-in sources (unique paragraphs only; hashed names stay out of dest)

| Dump path | Folded content |
|---|---|
| `symbol_game_docs/on_how_to_play_the_symbol_game_39c6d877.md` | 2026-07-24 provenance banner: product CLI paths may be stale; AuthorityEffect none; archive math_spine canonicality later superseded for programme navigation. Body is a lowercase wrapper of the unhashed stem. |
| `symbol_game_docs/on_plain_english_guide_to_the_symbol_game_0021c94b.md` | Host verifies over Q; model proposes matrices/primal-dual; host checks zero duality gap; `HOST_VERDICT.md`. Not landed under `0021c94b`. |
| `symbol_game_docs/packetization_symbol_payloads.md` | JSON envelope vs `lp<...>` LLM payload vs internal AST; tighter LP payload; LP alphabet/terminals. No second player guide. |

## Supporting reads (not dest copies)

| Dump or dest path | Why read |
|---|---|
| `symbol_game_docs/packetization_runtime_architecture.md` | prose to envelope to payload to AST to local/boundary/terminalizer; LLM is not the certifier |
| `symbol_game_docs/packetization_algorithms.md` | LP family local (feasibility, gap) vs global (precision, size) |
| `symbol_game_docs/_audit_yaml_terminal_statuses.yaml` | four host terminals Certificate/Refusal/Repair/OracleNeeded; repair budget 2 |
| `symbol_game_docs/_audit_yaml_validator_error_catalog.yaml` | LP host error codes matching the failure vocab |
| `symbol_game_docs/product_core_symbol_game.md` | do not conflate Rust `lp<...>` crate, Python 8-stage MVP, and research spine |
| `symbol_game_docs/mss_n_grammar_000.md` | historical genesis `<>` cite only; alphabet cardinality is not live MSS-0 law |
| `DOCS_CONSOLIDATION_LAW.md` Family 7 / `2_how_to_play` shape | v1 vs v2 split, YAML stays YAML |
| dest `2_how_to_play/` listing | confirmed no `how_to_play.md`, no `v1_historical_2026-05_lp_forcing/` |

## Deliberately not copied into this version

- Live `cargo` play recipes against `engine/products/symbol_game`.
- Eight-stage YAML as the public/original game (v2 / dest YAML owns stage contracts).
- Dest filenames `on_how_to_play_the_symbol_game_39c6d877.md` or `on_plain_english_guide_to_the_symbol_game_0021c94b.md`.
- Flattening `how_to_play_yaml/` into markdown.
- Byte-copy of dump `how_to_play_the_symbol_game.md` onto dest `how_to_play.md` (that copy would reintroduce the 8-stage cargo overlay as the play recipe).

# Retained source and trace archive

This archive makes selected evidence for Paper 008 available without the
historical checkout. `source_index.json` records the original path, exact Git
revision, Git blob identity, byte count and SHA-256 of every captured file.
The files are unmodified. Their capture does not create a new provider run or
upgrade a historical claim.

- `mss0_mss1_52cb5457/` contains the actual parser, its golden corpus and the
  two context maps at the paper's code baseline. The package's source-example
  tests load these under an isolated module name, with no current-code fallback.
- `k4_traces/` contains the eight raw response traces named in Section 10.1.
  Each SHA-256 matches the retained report's custody table. These are one
  observation per model/condition cell, including answer-bearing prompts.
- `k4_benchmark_report.md` is the historical working report, including broader
  interpretations that the revised paper does not adopt. The paper controls
  the scope of its claims.
- `c005_working_report.md` preserves the two-run correction notice and the
  transcribed counts. The missing C005 per-case rows are still missing.

Code and retained repository evidence keep the existing
[PolyForm Noncommercial terms](../../LICENSE-CODE). Newly written manuscript,
review and teaching text use [CC BY 4.0](../../LICENSE). No source is relicensed
by being copied here.

Run `code/tests/test_008_source_bound_examples.py` from the paper root. It
checks archive identities and exact finite calculations. It does not rerun a
provider, the historical multi-turn host, or the complete challenge corpus.

## Open the retained files

The working reports preserve historical wording and repository-relative links; use the origin path and revision in the index for their original context. Final K4 post-move host results are absent from the raw last rows.

| Archived file | Contents |
| --- | --- |
| [grammar.py](mss0_mss1_52cb5457/grammar.py) | Retained source or working report |
| [updown_maps.py](mss0_mss1_52cb5457/updown_maps.py) | Retained source or working report |
| [golden_corpus.py](mss0_mss1_52cb5457/golden_corpus.py) | Retained source or working report |
| [bench_qwen_qwen-2_5-7b-instruct_baseline_1790297180354.jsonl](k4_traces/bench_qwen_qwen-2_5-7b-instruct_baseline_1790297180354.jsonl) | Raw K4 trace |
| [bench_qwen_qwen-2_5-7b-instruct_partially_masked_1790308412.jsonl](k4_traces/bench_qwen_qwen-2_5-7b-instruct_partially_masked_1790308412.jsonl) | Raw K4 trace |
| [bench_qwen_qwen-2_5-7b-instruct_scratchpad_1790310019.jsonl](k4_traces/bench_qwen_qwen-2_5-7b-instruct_scratchpad_1790310019.jsonl) | Raw K4 trace |
| [bench_qwen_qwen-2_5-7b-instruct_hinted_1790297190434.jsonl](k4_traces/bench_qwen_qwen-2_5-7b-instruct_hinted_1790297190434.jsonl) | Raw K4 trace |
| [bench_meta-llama_llama-3_1-8b-instruct_baseline_1790297201231.jsonl](k4_traces/bench_meta-llama_llama-3_1-8b-instruct_baseline_1790297201231.jsonl) | Raw K4 trace |
| [bench_meta-llama_llama-3_1-8b-instruct_partially_masked_1790308428.jsonl](k4_traces/bench_meta-llama_llama-3_1-8b-instruct_partially_masked_1790308428.jsonl) | Raw K4 trace |
| [bench_meta-llama_llama-3_1-8b-instruct_scratchpad_1790310061.jsonl](k4_traces/bench_meta-llama_llama-3_1-8b-instruct_scratchpad_1790310061.jsonl) | Raw K4 trace |
| [bench_meta-llama_llama-3_1-8b-instruct_hinted_1790297215552.jsonl](k4_traces/bench_meta-llama_llama-3_1-8b-instruct_hinted_1790297215552.jsonl) | Raw K4 trace |
| [k4_benchmark_report.md](k4_benchmark_report.md) | Retained source or working report |
| [c005_working_report.md](c005_working_report.md) | Retained source or working report |

[Full revision and hash index](source_index.json).

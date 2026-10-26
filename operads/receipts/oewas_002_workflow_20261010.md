# OEWAS002: typed linear-workflow boundary repair

Status: `SCOPED_IMPLEMENTATION_VALIDATED`. AuthorityEffect: None.
Base and observed uncommitted HEAD: `3d06f414579ef8474900ba517ba352118982f769`.
Worktree: `C:/Users/a343o/.codex/worktrees/oewas-002-workflow/the_symbol_game`, branch `codex/oewas-002-workflow`.

`domain/workflow_graph.py` now refuses non-object pipeline entries as `WorkflowError("BAD_STEP", "pipeline step <index> must be an object")`. Non-string operation names become `UNKNOWN_OPERATION` findings retaining their raw value; only actual nonempty string names enter the unknown-operation inventory. These checks use the existing validation/composition path and report types.

The reviewed prospective plan proposed `BAD_PIPELINE_STEP`. Inspection of native `src/workflow.rs:193` showed the established public code is `BAD_STEP`; the Python repair deliberately preserves that native caller contract and exact indexed message. Native production code was already defensive and is unchanged. `WorkflowFinding.operation` is broadened to `object | None` to represent the actual malformed value, matching native JSON-valued findings.

The two new Python files contain 25 cases. The pre-repair run produced **19 failed, 6 passed**; those six existing positive/kernel controls are characterization evidence. After the repair and guard helper extraction, the final focused run produced **29 passed**, including the four existing repeated-step tests. A second batch produced **9 passed**, covering existing workflow findings and sequential associativity controls. Final Python total: **38 distinct tests** across five named files.

The new native `workflow_step_contract.rs` adds four tests that cover non-object steps at indices 0/1, malformed names/inventory, repeated unary and second-step mismatch/recovery, and nonzero/reordered ordered boundaries. The corrected three-target native batch passed **8 tests**, with zero ignored or filtered: planar parity 2, workflow parity 2, new contract 4. The unchanged frozen fixtures contain **251 planar** and **39 workflow** rows. The first native attempt failed to compile because my new harness accessed private report fields; no tests ran in that attempt. The corrected harness reads the public serialized report. Both logs are retained.

Four real production mutations were run sequentially, each followed by byte-for-byte source restoration in a `finally` block:

| Production mutation | Observed focused result |
| --- | --- |
| Bypass pipeline step guard | 12 failed |
| Remove string guard on garden lookup | 3 failed, 5 passed |
| Remove string guard on unknown inventory | 4 failed, 4 passed |
| Replace nested `i + j` with `j` | 1 failed: literal ordered boundaries disagree |

Every mutation exited 1; before/restored SHA256 hashes match. The nonzero-slot case is deliberately still colour-admissible after the wrong shift, so order disagreement is observable instead of being hidden by an unrelated colour refusal. Expected boundaries are literal tuples. The reordered case demonstrates different valid source order; it does not imply a runtime receipt registry exists.

Ruff 0.17.0 passed `F401,F841,I,C901` with max complexity 10 on the changed Python source/tests. `rustfmt --check` passed the new native file. `git diff --check` passed. Cargo ran offline/locked in one crate, at `-j1`, with one existing target cache. Its effective tracked lock, scoped metadata, tool versions, free disk observations, exact argument vectors, source/test/log SHA256 values, and unchanged baseline blob checks are in the companion JSON. No credentials or environment enumeration are included.

The planar Python/native kernels, native workflow/graph production code, frozen corpora, and Cargo.lock remain identical to the base. No commits or pushes were made.

The explicit workflow DAG portion remains separate work: native `graph.rs` has `Request { nodes, edges }`, port references, cycle checks, and execution-stage planning; the Python linear pipeline has no dependency-edge schema. This repair neither adds a graph adapter nor certifies DAG coverage. It does not complete OEWAS002, prove a general operad theorem, run providers, or certify hosted checks. Research planning PR #696 remains separate and unmerged. Parent review must bind a later commit/PR head independently.

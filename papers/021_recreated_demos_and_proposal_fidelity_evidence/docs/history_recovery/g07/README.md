# G07: original branch-fan census baseline

The original provider-free G07 computation is reproduced from exact declared source pins. [The completion record](provider_free_completion.json) binds the full source/native census and the supplemental native quiet-state replay. This is a new baseline computation, separate from the historical model report and its unretained raw replies. No provider was called; model-arm comparisons, three-seed McNemar statistics, billed inference, and model conjecture quality remain unperformed.

The two complete P1 trees use the original `mu2`, `Bounds(2,2)`, supply enabled, depth 15, and pre-expansion guard 3000. The exact source `build_tree` is executed, rather than substituting a generic carrier. The unchanged native owner independently rebuilds the same population, including presentation-token relabel controls.

| Reading | Nodes | Edges | Expanded tie counts | Depth |
|---|---:|---:|---:|---:|
| L | 963 | 1022 | 236 | 15 |
| F | 1847 | 1960 | 422 | 15 |

The [complete result](run_v1/result.json) retains every P1 histogram at depths 0–15, both original deterministic P2 trajectories through depth 60, all 44 original held-outs, exact candidate histories/states, and the OPEN conjecture. The source and native checks agree on 3,617 offered-challenge width cases: 3,530 P1 cases across original and renamed trees, and 87 P2 cases. Native code replays the actual source histories, recomputes minima and quotient classes, checks every raw response with the naive native validator, and retains class keys, representatives, member counts, raw deltas, and costs in [its actual output](run_v1/native_stdout.json).

Histograms count each offered pair-separation challenge, including those at completed depth-15 boundary nodes. The sealed 236/422 figures concern actual expanded nodes; boundary evaluations are retained separately and cannot be included in that reconciliation. Quiet states offer no pair-separation target, so their width is undefined and their histogram is empty. They are never assigned a fabricated zero or unit width. Native P1 reconstruction accounts for quiet nodes; [the supplemental checker](quiet_v1/receipt.json) replays all 35 quiet P2 histories and independently verifies their empty challenge-orbit lists. This includes L's final state at depth 60. At depth 50 both P2 trajectories contain 17 data; at depth 60 L contains 19 and F contains 20.

The largest observed width is 11. The mechanically constructed baseline conjecture says that every reachable state under this declared policy has width at most 11; it is explicitly OPEN, limited by the finite evidence range, and falsified by any valid reachable challenge with width greater than 11. It is fitted to this census, not a pre-registered model proposal or a theorem.

The actual controls reject raw-delta counting as class counting, a shifted depth, the native supply-disabled population, an omitted case, a corrupt carrier, and a corrupt class-size certificate. A conjecture already refuted by the result is rejected; the poisoned unboundedness request returns `OUT_OF_SCOPE`. Supplemental native probes reject a nonquiet state, an unknown event, an ill-formed admitted instance, and a duplicate case. The [focused tests](../../../code/tests/test_paper011_genesis_g07.py) verify held-out completeness, fixed source identity, process custody, native agreement, and those controls without rerunning the stable census.

## Source and build custody

[The source manifest](source_manifest.json) binds 82 fixed files totaling 715,794 raw bytes. Ten files come from the original 19L57G1 pins: six sealed Python modules and `claims.json` at `3100c4ed5ce70d2b6cff6d2ccd3b0251cf918d0a`, and `evaluate.py`, `harness.py`, and `unboundedness.py` at `b55fc96a94740b0afde78337350a96d293615f3f`. The remaining 72 files are the unchanged native primitive source closure from the_symbol_game commit `526ffd1748941f1781c0ff584b7033b29088b405`, subtree `cfbd79e44ea5424ebad6d34709fa3993a05170e0`. Every raw SHA-256, Git blob, size, commit, and local path is retained. A fixed manifest digest prevents rehashed substitutions. Neither external repository was built or changed.

Original Python function/class bodies execute intact. The loader gives absolute imports explicit private module identities, registers modules before execution, and omits only the unboundedness module's top-level path mutation and main runner. Its `replay` binding is temporarily observed to retain every original trajectory state and history; the original function restores afterward. No Python mathematical algorithm is reimplemented.

[The build receipt](build/receipt.json) binds the explicit Cargo and Rustc executables, offline locked `-j1` invocation, local source files, lock, dependency metadata, registry source files before/after, actual streams, and the unique new executable. All six existing host/verifier executable hashes remain unchanged. A failed launcher invocation and one initial transport compile failure are retained under `build/failed_*`; the corrected transport compiled in 1.9 seconds. The pinned native sources were unchanged throughout.

[The base run receipt](run_v1/receipt.json) binds request/output/result bytes, executable identity before/after, the build receipt, and the declared backing Python executable. The full base run took 49.84 seconds; the native width-and-tree process took 21.56 seconds. The quiet checker compiles a tiny transport with explicit Rustc against the already-built exact libraries, preserving the original transport binary and avoiding another full census. Its receipt binds those libraries and all actual probe streams. Its `native_seconds` field covers the supplemental checking, negative probes, crosschecks, and library custody phase, rather than only the positive process.

Both Python workers use `-B` and fresh empty cache prefixes. The runtime scope binds the declared interpreter, source inputs, compiler, registry sources, and linked libraries; it does not claim a hermetic OS or complete standard-library inventory. Mathematical evidence is finite; the global conjecture remains OPEN and `AuthorityEffect` is `None`.

## Reproduction

Run from Paper 011. The initial recovery requires explicitly supplied repositories containing the fixed Git objects. Subsequent replay reads only the bounded paper-local dependency area and explicitly supplied runtime binaries. Do not repin a missing object.

```powershell
py -3.12 code/genesis_g07_replay.py recover --external C:/Users/a343o/source/repos/19L57G1 --estate C:/Users/a343o/.codex/worktrees/1a33/the_symbol_game
py -3.12 code/genesis_g07_replay.py verify
py -3.12 code/genesis_g07_replay.py build --cargo <actual-cargo.exe> --rustc <actual-rustc.exe> --target <explicit-target-dir> --host-directory <explicit-existing-host-dir>
py -3.12 -B -X pycache_prefix=<fresh-empty-cache-prefix> code/genesis_g07_replay.py run --executable <paper011_native_genesis_g07.exe> --interpreter <actual-backing-python.exe>
py -3.12 -B -X pycache_prefix=<another-fresh-empty-cache-prefix> code/genesis_g07_quiet.py --rustc <actual-rustc.exe> --primitive <exact-pinned-primitives.rlib> --json-library <exact-serde_json.rlib> --executable <unique-paper011-quiet.exe>
py -3.12 -B -m pytest -q code/tests/test_paper011_genesis_g07.py --basetemp <writable-test-temp-dir>
```

The two receipts retain the exact successful host-specific arguments and hashes. `full_g07_experiment_completed` remains false; the completed result is the original provider-free mathematical baseline and controls.

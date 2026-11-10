Native systems audit checkpoint at `8050c66900899771766f33e8f5fdd200b7dd9120`.

This phase fully read **30 Rust files and four manifests: 11,553 lines** across EIS, PCIV, OPERADS and operad theory. The JSON records actual coverage, hashes, claims, dependencies, test outcomes and **119 remaining files** within the declared four-crate/test scope. Other dependent crates remain outside this completed slice. No production source, tests, historical receipts or benchmark material were changed.

Seven new defects were reproduced through public Rust APIs:

| Finding | Evidence | Bounded observation |
| --- | --- | --- |
| NATIVE-BUG-001 | `core_epistemic_immune_system/src/authenticated.rs:256-262` | Reversed issuance/expiry timestamps panic in a debug build before signature verification. No signature bypass was shown. |
| NATIVE-BUG-002 | `core_operad_theory/src/foundation/planar_tree.rs:133-143` | A nullary operation named `f;leaf:A` and unary `f(A)` receive the same term hash. |
| NATIVE-BUG-003 | `core_operad_theory/src/foundation/operation.rs:147-165` | Two different valid permutations of 12 inputs receive the same operation ID. |
| NATIVE-BUG-004 | `core_prompt_civilization/src/rank.rs:171-229`; `rank_port.rs:61-109` | Repeated parent edges produce a row summing to `3/4`. The dense solver returns a vector rejected by its own verifier. |
| NATIVE-BUG-005 | `core_prompt_civilization/src/rank.rs:688-713` | A singleton graph with edge `(0,99)` returns a converged certificate instead of an endpoint refusal. |
| NATIVE-BUG-006 | `core_epistemic_immune_system/src/thymus.rs:34-45` | Panels containing one newline-bearing sample versus two separate samples have the same panel digest. |
| NATIVE-BUG-007 | `core_prompt_civilization/src/genealogy.rs:183-232` | Inserting `B→C`, then `A→B`, leaves C's cached generation at 1 instead of 2. |

All source paths in the table are below `code/rust/`. Reproductions are in `additional_native_systems_probes.py`; their captured results are embedded in the audit JSON. These are finite counterexamples, not claims about every downstream application. In particular, the foundation tree hash differs from the stronger structured hash used by the runtime kernel.

The substantive mathematics is bounded and useful. EIS implements exact Hill thresholds and a maximum independent set over supplied correlation metadata. Neither sensor names nor graph independence establish statistical independence. Authenticated custody checks key-relative signed statements, role, scope, binding, time and history; it still relies on trusted policy, observers, clock and external custody of the latest history tip.

Native PCIV immunity uses actual graph traversal and a fixed-point taint calculation. A valid-seal probe confirms two-hop backward weight `1/4` and successful forward taint, so the earlier Python adapter defects cannot simply be attributed to this native implementation. Lineage hashes remain self-computable declarations, not independent causal evidence.

For valid stochastic graphs, PageRank's affine map contracts the l1 norm by `17/20`; geometric summation yields the implemented posterior bound `17/3 × successive-iterate difference`. This is an inspection-based mathematical argument under graph assumptions, not a mechanized proof of Rust. It supplies no theorem of semantic fitness or task success.

Planar substitution preserves ordered typed boundaries. The kernel normalizer validates even supplied “Admitted” trees, erases association/identity syntax and uses structured canonical IDs. Its source explicitly states that the Lean tree proofs do not yet verify Rust or serialization. The local inventory runtime executes only identity, pair and checked integer sum; other bindings require external executors. Arbitrary action bodies, policy metadata and descriptive carrier names do not establish an algebra law or execution provenance.

The offline Rust 1.99.0 test results remain separate:

- **core_operads:** 56 passed across unit and integration targets.
- **EIS:** 24 unit tests passed; 19 additional selected tests passed; activation parity had 2 passed and 2 failed. The activation-use-case parity target separately fails compilation on a missing lifetime and a temporary borrow.
- **PCIV:** 113 unit tests passed and 3 failed; rank-port integration had 2 passed.
- **core_operad_theory:** 72 unit tests passed and 2 failed; its integration targets did not run after the unit failure.

The failing PCIV immunity tests use obsolete unbound witness strings. The genome golden digest still encodes the old `omega-` prefix. Two operad canonical tests supply `core.test` but expect `omega.test`. For the first mismatching EIS danger row, current Python and native canonical hashes agree; the frozen expected hash differs. These are validation defects requiring explicit fixture provenance repair, not evidence that key sorting failed. Generic capacity-wrapper tests and comments claiming “six mutations killed” do not establish module-wide correctness.

The audit remains incomplete. Next priorities are the remaining detector/pharmacy and PCIV modules, operational host integrations, kernel capability/model/trace/reindex paths, complete fixture review and resource-bound checks. Repairs have not started.


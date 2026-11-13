# Source-bound native Phi2 composition

The closed `composed_phi2_v6` run checks the two original Demo 6 carrier/witness pairs with the unchanged source checker and the explicitly pinned Rust `verify_phi2` executable. Both native calls returned process exit 0, `status: PASS`, and a zero rational duality gap. The original source checkers rejected all eight retained near-misses before a native invocation was needed.

| Original dossier | Declared carrier | Native reported value | Native duality gap | Source negative controls |
|---|---|---:|---:|---:|
| Hollow tetrahedron | 4 vertices, 6 edges, 4 faces | 1 | 0 | 4 refused |
| Fused tetrahedra | 5 vertices, 9 edges, 7 faces | 2 | 0 | 4 refused |

The negative controls cover decimal-string floats, a nonclosed dual chain or uncanceled shared boundary, an excessive dual norm, and a nonzero duality gap. Their literal source-checker returns and exact input/witness bindings are retained in [the leaf receipt](composed_phi2_v6/demo_6/recreation_receipt.json). The native request bytes, physical stdout/stderr bytes, executable identity, and source-facing decoded text view are retained in [the native tape](composed_phi2_v6/demo_6/native_transport_calls.jsonl). The new tape explicitly declares `RAW_SUBPROCESS_BYTES`; earlier tapes without that declaration remain legacy decoded observations.

Composition injects this scoped source-bound verifier path into the existing recreation dispatch. The unmodified production adapter's `NO_NATIVE_PORT` output remains under `canonical_adapter_diagnostic`. Its original dispatch return of zero is preserved as diagnostic data and supplies no native verification. The `betti_2` literals remain source metadata here; this receipt does not compute a homology rank or establish a general carrier theorem.

Custody closed after the single worker exited successfully. The batch rechecked the complete declared source inventory, engine, native binaries, and runtime profile. Its [batch receipt](composed_phi2_v6/batch_receipt.json) has canonical self-digest `5709752c0534bf3c2264254e64cc2d2fd3a64b43e7ccbed42320a580947f2470`; the leaf self-digest is `56df5cb24dfc47e6306a60cf918cffc62a1553b37c2c221bcab1500d025209e4`. The verifier SHA256 is `c25b8f3326b56d851cd345ddfbc67ff120a194650039dd613d7a3b286d77348b`.

[Coverage matrix v6](coverage_matrix_v6.json) verifies all selected leaf artifacts and six closed batch receipts before joining this result. It retains 87 original dispatch/challenge rows, the original complete C041 64-case/48-mutation run, and the separately selected C041 two proposals/four corruption controls. The original solver's two abstentions remain unchanged. Matrix self-digest: `a69260b68f159abeab1c41448143e59dec34595c1f9d871b0d4033c84e5fcb7c`; actual matrix-file SHA256: `6872f39dfe8670b11119027ddfa5ec9a9462e1b2ac17e7d942182eccb0b68de0`.

The focused adapter suite passed 47 tests, including missing-native false-positive rejection, explicit engine-root binding, failed composition controls, physical-byte versus decoded-text capture, and preservation of the original C041 denominator. No provider calls, model-accuracy claim, production authority, or universal solver result is added.

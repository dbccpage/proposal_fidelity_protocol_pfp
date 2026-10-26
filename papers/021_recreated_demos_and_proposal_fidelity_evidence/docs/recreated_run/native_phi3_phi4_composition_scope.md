# Original Phi3 and Phi4 dossier composition

The closed `composed_phi3_phi4_v7` batch replays the complete original Demo 7 and Demo 9 dossier audits. Each audit receives its original declared folder and an explicit engine root. All three input/witness files per dossier are bound by original path and SHA256. Their mathematical code is unchanged.

| Original dossier | Native cell counts | Exact certified value | Gap | Complete original controls |
|---|---|---:|---:|---:|
| Demo 7, hollow 4-simplex | C2 = 10, C3 = 5 | Phi3 = 1 | 0 | 4 refused |
| Demo 7, torsion/Bianchi complex | C2 = 4, C3 = 1 | Phi3 = 0 | 0 | 4 refused |
| Demo 9, hollow 5-simplex | C3 = 15, C4 = 6 | Phi4 = 1 | 0 | 4 refused |
| Demo 9, declared Pontryagin/Chern carrier | C3 = 2, C4 = 1 | Phi4 = 2 | 0 | 4 refused |

Each valid witness produced exactly one call to its explicitly pinned Rust verifier, process exit 0 and `status: PASS`. The new gate checks agreement between the actual request, actual response and retained source certificate value. The unchanged source audits reject all 16 near-misses; the adapter additionally requires every original case ID in order and its exact declared refusal type. Source PASS labels without native evidence, a mismatched value, or an omitted negative control fail the composition gate.

The full literal source results remain in the [Demo 7 receipt](composed_phi3_phi4_v7/demo_7/recreation_receipt.json) and [Demo 9 receipt](composed_phi3_phi4_v7/demo_9/recreation_receipt.json). Demo 7's second source audit computes exact-flux Bianchi defect 0 and monopole-flux defect 2. Demo 9's second source audit computes a declared 4-cochain/cycle pairing of 2. Those finite source computations have `SOURCE_RECREATION_PYTHON` provenance; the separate Rust checks certify the declared rational Phi objectives.

Demo 9 also preserves two explicit residuals. Its retained topology audit reports computed rational Betti numbers `(1, 0, 1, 2, 1)` against declared `(1, 0, 2, 0, 1)`, returning `REFUSED_DECLARED_TOPOLOGY_MISMATCH`. The source exact-gauge cup pairing remains null with `UNSUPPORTED_MISSING_CUP_PRODUCT_CARRIER`. A valid Phi4 certificate and a declared cochain pairing do not establish the advertised manifold, intersection form or characteristic-class interpretation. The scoped ports explicitly leave `manifold_or_intersection_claim_verified` false and retain these residuals in coverage. Independently owned native homology receipts assess the matrices separately.

Both original production adapter outputs remain under `canonical_adapter_diagnostic` with `NO_NATIVE_PORT`. The recreation injects the existing verifiers through its existing `native_demo` composition path; it does not change production capabilities. Actual native request and physical stdout/stderr bytes are retained in the [Phi3 tape](composed_phi3_phi4_v7/demo_7/native_transport_calls.jsonl) and [Phi4 tape](composed_phi3_phi4_v7/demo_9/native_transport_calls.jsonl), marked `RAW_SUBPROCESS_BYTES`.

The [batch receipt](composed_phi3_phi4_v7/batch_receipt.json) closes both workers after a full source, engine, binary and runtime recheck. Canonical self-digest: `02d6ebc8ec28eda1e3b6f1dbb6d5d745521cca1e79471f2e811f6bf145bb429c`. Demo 7 leaf self-digest: `18fd812c6d961264dc1db22014c75b026409e6a831d4a89fb8db1aae9d8d3e2c`. Demo 9 leaf self-digest: `933d9406d8437d424490591d625c274c70d675a381e8f0b916422525297a819f`.

[Coverage matrix v7](coverage_matrix_v7.json) verifies seven closed batches and every selected leaf artifact. It retains 87 original dispatch/challenge rows, the original C041 64-case/48-mutation run and its two abstentions, plus the separate two accepted supplemental proposals/four rejected controls. Matrix self-digest: `ce2ab2cfe56459a4219c4583655ed6c1170686902c3a14b40c1fa462a99c468e`; actual matrix-file SHA256: `7370e398a89e5aa653fd4dd19c513e400480159fcfd6ba6b6f74dd5e3a5dbf5a`. All earlier diagnostic receipts remain unchanged. The focused adapter suite passed 51 tests and lint checks. No model run or accuracy claim is added.

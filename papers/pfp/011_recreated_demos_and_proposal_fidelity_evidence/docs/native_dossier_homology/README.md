# Original dossier rational homology audit

The [closed native run](run_v4/receipt.json) evaluates every declared boundary matrix in the two original dossiers for each of demos 5, 6, 7 and 9. Eight input SHA-256 values are frozen in the runner against Git revision `526ffd1748941f1781c0ff584b7033b29088b405`; [the independent source check](source_pin_verification.json) records their original raw blobs and verifies the earlier identical matrix inputs. Input mutation before execution is refused. No source carrier or claimed Betti number is changed.

The supplied matrices are cochain maps `d_k: C^k → C^{k+1}`. The [thin Rust transport](../../code/native_dossier_homology.rs) uses the existing `RationalMatrix.rank` and `RationalMatrix.apply` implementations. It evaluates every consecutive product on every column. Only a zero product permits the dimension-minus-incoming-rank-minus-outgoing-rank Betti calculation. It implements no elimination algorithm. Python parses YAML, binds source bytes and persists actual native streams.

| Original dossier | Dimensions | Native ranks | Betti numbers over Q | Declared claim outcome |
| --- | --- | --- | --- | --- |
| Demo 5 planar triangles | 4, 5, 2 | 3, 2 | 1, 0, 0 | Declared b1=2 is the graph cycle rank; filled-complex b1=0 |
| Demo 5 Kagome trimer | 6, 9, 4 | 5, 4 | 1, 0, 0 | Declared b1=4 is the graph cycle rank; filled-complex b1=0 |
| Demo 6 hollow tetrahedron | 4, 6, 4 | 3, 3 | 1, 0, 1 | All declared rational Betti numbers match |
| Demo 6 fused tetrahedra | 5, 9, 7 | 4, 5 | 1, 0, 2 | All declared rational Betti numbers match |
| Demo 7 hollow 4-simplex | 5, 10, 10, 5 | 4, 6, 4 | 1, 0, 0, 1 | All declared rational Betti numbers match |
| Demo 7 torsion carrier | 4, 6, 4, 1 | 3, 3, 1 | 1, 0, 0, 0 | Rational claims match; integral torsion remains unverified here |
| Demo 9 hollow 5-simplex | 6, 15, 20, 15, 6 | 5, 10, 10, 5 | 1, 0, 0, 0, 1 | All declared rational Betti numbers match |
| Demo 9 claimed S2 × S2 carrier | 4, 4, 2, 2, 1 | 3, 1, 0, 0 | 1, 0, 1, 2, 1 | Declared b2=2 and b3=0 are contradicted |

All eight original matrix sequences satisfy the boundary law. Four actual native control inputs detect a nonzero consecutive product, refuse a floating entry and a ragged matrix, and detect a false Betti claim. [Thirteen focused tests](../../code/tests/test_paper011_dossier_homology.py) check these retained results, source pins, nested claim location, original input completeness and corrupted outcomes. Demo 9's second dossier declares its numbers under `topology.betti_numbers`; that source location is retained explicitly.

These results do not independently certify the LP objectives, intersection pairing, manifold identity or integral torsion. Demo 5's graph LP calculations remain separately valid calculations over the edge quotient. A graph cycle count cannot certify the homology of the filled complex. The mismatch records are falsifiers of particular source claims, rather than successful proofs of them.

## Custody and reproduction

[The build receipt](build_v1/receipt.json) binds the Rust source, explicit Rustc executable, all 254 available static Rust archives before/after, physical build streams and the unique executable. No Cargo rebuild or existing host replacement occurred. This binds the actual existing library artifacts; it is not an independent rebuild of those mathematical libraries or a hermetic OS/toolchain closure.

The final run binds frozen source bytes, source commit, native argv/cwd, build receipt, Python backing executable, YAML package files, runner/transport bytes and physical request/stdout/stderr/result bytes. The runtime scope excludes a full OS/standard-library inventory. The first run stopped before invoking native code because a Windows launcher alias could not be resolved; its request remains under `run_v1`. Runs v2/v3 are diagnostic predecessors; v3 omitted source-pin enforcement in its runner although the independent Git check verified its actual inputs. Only v4 is the finalized runner invocation.

Run from Paper 011 with explicit runtime paths, using new empty output directories:

```powershell
py -3.12 -B code/replay_dossier_homology.py build --rustc <actual-rustc.exe> --deps <declared-native-dependency-dir> --runtime-rlib <exact-runtime.rlib> --serde-rlib <matching-serde_json.rlib> --output <new-build-dir>
py -3.12 -B code/replay_dossier_homology.py run --source-root <PFP/demos/demos> --executable <built-executable> --build-receipt <build-receipt.json> --interpreter <actual-backing-python.exe> --output <new-run-dir>
py -3.12 -B -m pytest -q code/tests/test_paper011_dossier_homology.py
```

The successful receipts retain the exact host-specific arguments. The paper-local source archive is still pending its separate bulk-copy approval. `AuthorityEffect: None`.

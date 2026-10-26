# Native MUB catalog recreation

The original native verifier evaluates seven fixed exact catalog triples and
their twenty-one transition matrices. The source is pinned at repository revision
`526ffd1748941f1781c0ff584b7033b29088b405`, original SHA-256
`208041dfea0b11c8ab460a355446513d9261b06fe492380d90b56e5d07820bbe`.

The original program writes into the source crate's `artifacts` directory. The
paper runner changes that one output-directory expression to a required explicit
argument. Every other source byte is retained. The adapter verifies this exact
one-expression relationship before execution. Its Cargo manifest uses the
unchanged native `omega_mub` and `omega_number_theory` owners in the explicitly
supplied source checkout, with 138 locked dependencies (139 package entries
including the paper runner). Historical dependency-environment equivalence is not claimed.

[The fresh receipt](native_mub_recreated_run/final_v1/receipt.json) retains actual
stdout, stderr, the raw native report, binary identity, every tracked native
source digest, runner controls, and the complete pre/post source comparison.
The [native control receipt](native_mub_recreated_run/native_controls/receipt.json)
additionally retains its exact executable digest, argv, working directory and
actual test stdout/stderr. The payload digest is
`0ff823c19591ab6f0d1be9d859201560c72f8580956628940b77f6f5387b4936`.
All seven triples and twenty-one matrices match the retained original report.
[The build receipt](native_mub_recreated_run/build_receipt.json) records the
actual offline build and focused test outcomes. Existing upstream warnings are
not presented as repository-wide validation.

Two native tests check the twenty gamma-one and twenty gamma-two sign patterns
and distinguish the original Fourier positive control from the exact Tao S6
negative control (zero versus twenty gamma-one failures). Eleven Python custody
controls reject altered digests, omitted or duplicated triples, invalid Boolean
and count fields, malformed bytes, and redirected paths. They check report
custody; mathematical calculation stays in Rust.

Run from the repository root after supplying the pinned native checkout and
existing offline dependencies:

```powershell
py -3.12 <paper>/code/replay_native_mub.py --source-repo <repository> --prepare
cargo build --offline --locked -j 1 --manifest-path <paper>/code/native_mub_replay/Cargo.toml --target-dir <native-cache> --bin paper011_native_mub_replay
cargo test --offline --locked -j 1 --manifest-path <paper>/code/native_mub_replay/Cargo.toml --target-dir <native-cache> --test native_controls -- --nocapture
py -3.12 <paper>/code/replay_native_mub.py --source-repo <repository> --binary <native-cache>/debug/paper011_native_mub_replay.exe --binary-sha256 <actual-binary-sha256> --output-dir <new-output-directory> --timeout 180
```

The manifest's relative native dependency paths describe this repository layout;
an extracted paper requires the explicitly supplied native checkout or an
already built, digest-checked executable and the matching source identities.
No native executable, compiler output, or target cache is deposited in this paper.
The original source and adapted generated Rust file retain their source formatting
to preserve the verified one-expression adaptation.

This result is a finite catalog replay. It does not establish generic Conjecture 2,
a bound on MUB(6), or the geometry computation described in the separate
MUB6–Regge prose example.

# Standalone native algebra sidecar

This experiment reuses the four exact production arithmetic methods at
`code/rust/pfp_runtime/src/rational.rs:291-353`, byte for byte. Their owner SHA256
is `9d78981a19c942a70d4d4262f1df9538024754b2b87c0e0288a46d377cd3916c`.
`source_binding.json` records the fragment and generated-source hashes. The
private carrier, JSON admission, batching and Python polynomial protocol are new.
This is not the full PFP port-host or an OPERADS/EIS/PCIV integration.

From the repository root, the isolated offline build is:

```powershell
.\.venv\Scripts\python.exe -X utf8 dag/benchmark/native_sidecar_host/build_native.py
.\.venv\Scripts\python.exe -X utf8 dag/benchmark/test_native_sidecar.py
```

The crate has its own `[workspace]`, dependency lock and target directory.
The build helper uses exact dependency versions from the original lock and only
cached dependencies, records Cargo/rustc/linker hashes and retains earlier build
attempt receipts. A missing toolchain/dependency is an infrastructure refusal.
The installed MSVC/SDK paths are explicit in the helper. No broad workspace is
built. The retained original `code/rust/target/debug/pfp.exe` was not executed.

`native_sidecar.verify(public, candidate, answer)` certifies only the
characteristic polynomial of an explicitly supplied affine
`A0 + J*AJ + Delta*ADelta + K*AK`, dimension 1 through 4. The public input requires
all four square coefficient matrices and exactly the ordered parameter list
`["J", "Delta", "K"]`. Their rational numerators and positive denominators have
at most 16 bits. Candidate coefficients have at most 64-bit rational components,
at most `(n+1)^3` distinct sparse monomials per lambda coefficient, and checked
degree at most `n` in each parameter. Exponents must be integers, not booleans.
Rationals must already be reduced canonical strings; zero sparse terms are
represented by absence. The public and candidate byte limits are 32/64 KiB.

The candidate binds the public-input digest, obligation ID, complete answer
digest and UTF-8 byte span of the explicit machine assertion emitted by
`assertion_text(coefficients)`. This ties the certificate to that exact assertion;
it does not validate other answer prose or prove that the public matrix is the
right interpretation of the QM question. The Python API does not read any task
file, evaluator, provider or answer key.

The complete Cartesian grid has `(n+1)^3` points, at most 125, and includes zero
in every parameter. All matrices cross in one native invocation with a 5-second
timeout and a 256 KiB request bound. The wrapper independently checks nonempty
square dimensions, canonical 128-bit rational matrix entries and the batch
bound. It computes ascending characteristic coefficients with the extracted
BigRational Faddeev–LeVerrier methods. The input 16-bit coefficient bound ensures
evaluation of four affine terms stays within the wrapper's 128-bit entry bound.

The native caller verifies the current owner, exact extracted bytes, build-input
hashes, dependency lock and binary hash before execution. Missing/changed
custody or a failed native process yields `INFRASTRUCTURE_REFUSAL`; there is no
Python arithmetic fallback. A mismatch yields `REFUTED_IDENTITY` with exact
parameter/coefficient evidence. All grid matches yield `CERTIFIED_IDENTITY` for
this characteristic-polynomial identity over all real parameter triples, using
the checked per-variable degree bound. Requests outside the profile yield
`UNSUPPORTED_OR_MALFORMED`. These local artifact hashes are custody checks, not a
signature against an attacker able to rewrite this workspace.

Projectors, eigenvectors, dynamics, surrounding prose and other task obligations
remain explicitly unresolved. Parent benchmark runtime files remain unchanged.

The controls use an independent Leibniz determinant expansion across 32 rational
matrices of dimensions 1–4, full three-parameter positive grids, sign/cross-term
mutations, a false identity agreeing along `J=Delta=K`, and an over-degree
polynomial vanishing on the full grid. Admission/binding/infrastructure controls
also exercise the actual wrapper. See `../native_sidecar_validation.json`,
`native_smoke.json` and `controls/` for the observations and source pins.

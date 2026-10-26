# Explicit replay dependencies

The preserved source modules loaded in the first complete bounded replay declare
NumPy and PyYAML imports. That recorded run executed CPU PyTorch 2.6.0+cu124.
The CUDA build label does not imply that a GPU experiment occurred. Current
mechanism execution refuses a torch public version below 2.13.0. The historical
runtime profile still records the 2.6.0+cu124 capture. No installer or provider
is invoked by this package.

[The runtime profile](runtime_environment_v1.json) binds the actual Python 3.12.10
backing executable, twenty-six explicitly named installed distributions and
16,497 distribution-declared files. This set includes supporting scientific,
schema, test, and document libraries beyond the minimum preserved-source imports.
It is a declared dependency snapshot, not a census of every module imported at
runtime. Original and relocated application modules have separate source digests.

The profile's raw SHA-256 is
`48ecb80f174d27b7581f299492377404b07d82b9924a053c53a587f15bf203b3`.
The first capture refused the Windows Store App Execution Alias. The completed
capture binds the explicitly selected backing interpreter while retaining the
launcher's identity. It does not silently dereference a substituted launcher.

From the paper directory, on the explicitly configured recorded environment:

```powershell
py -3.12 code/runtime_environment.py verify --profile docs/runtime_environment_v1.json
```

The capability binds both the profile and verifier bytes. Whole-profile checks
belong before and after a batch; workers retain the same profile identity. Mutable
bytecode caches are excluded, so workers must select a fresh empty cache location
before dependency imports and disable bytecode writes. Missing or changed source,
extension, interpreter, metadata, or version fields refuse verification. Five
focused controls exercise dependency-file, interpreter, version, inventory, and
missing-file drift.

The native MUB transport uses its separately recorded Cargo lock and unchanged
Rust owners. Lean compilation requires an explicitly configured real kernel path
and digest rather than an ambient toolchain-updating shim. Compiler, provider,
and source capabilities remain separately declared.

This profile does not bind the complete operating system or every standard-library
file. A reader on another host must declare that host's runtime and produce new
receipts; these captured bytes cannot be represented as the reader's environment.

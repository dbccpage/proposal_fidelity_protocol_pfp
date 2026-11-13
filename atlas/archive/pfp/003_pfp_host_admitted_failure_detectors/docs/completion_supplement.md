# PFP III reproduction boundary

2026-09-28 · Version 1.1.0

The [paper](../paper.md) contains the protocol, the implementation analysis, the
worked example, and the limitations. This page records how to run the checks in
this deposit and what they cover.

The canonical Demo 3 host is repository code at commit
`52cb5457f6c485ba548cfd292f6012a941ed22cf`; it is not part of this deposit. The
deposit contains a small re-implementation (`code/host_engine.py`, with a Rust
port in `code/rust/src/host.rs`) whose differences from the canonical host are
listed in Section 4.1 of the paper. Both return `NO_NATIVE_PORT` for every
declared witness route; neither certifies a proposed gauge, cochain, or pairing
witness.

Run each test file separately from the package root with Python 3.12:

```powershell
py -3.12 -m pytest code/tests/test_demo_3_host.py -q
py -3.12 -m pytest code/tests/test_danger_gate.py -q
py -3.12 -m ruff check code
cargo test -j 1 --manifest-path code/rust/Cargo.toml
```

For the two-signal decision table, see `code/danger_gate.py` and
`code/tests/test_danger_gate.py`. For the four candidate phrase detectors, see
`code/canaries.py` and `code/demo3_canaries_audit.py`. The command
`py -3.12 code/run_demos.py` runs the package demonstrations offline.

Record fresh execution separately, including native checks. Neither historical
receipt counts nor a scripted arm matrix establishes an unrestricted live model
trial. The planned study requires admitted callable route oracles, frozen
allocation and inputs, independently reconstructed outcomes, authorized raw
records, and prespecified analysis.

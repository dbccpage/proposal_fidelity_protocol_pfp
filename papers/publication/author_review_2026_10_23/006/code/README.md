# Package code for PFP VI

2026-10-02 · Version 0.1.0

`tests/test_006_epistemic_immune.py` defines its own `DangerSignal`,
`ThymicCheckResult`, and in-memory `CemeteryDAGSink`. It does not import the
production failure store or the actual two-signal policy. These small examples
illustrate thresholds, exact-type comparison, and predecessor hashes. They are
not a production integration suite, a lossless-retention result, an RFC 8785
conformance test, or evidence of detector effectiveness.

`tests/test_006_worked_example.py` is different. It runs the paper's Section 6
example, as printed, against the repository's failure store, together with the
three modifications that Section 6 describes and the number-versus-string reason
case from Section 5. It needs the full repository checkout and skips, stating
that reason, when the store's source file is absent. The added cases cover
unbound header schema/genesis, formatting, cached receipt emission, failed
replacement, nested mutation, and legitimate prefix extension. A test run
must identify the actual loaded source hashes; importing the current checkout
alone does not reproduce a historical implementation.

`tests/test_006_catalog_file.py` reads the retained detector-candidate catalog
through Git at the audited commit and recomputes the counts, fields, and digest
reconstructions reported in paper §7.1. If the Git object is unavailable, it reads the identical SHA-256-bound
snapshot under `fixtures/`, so these data checks run from the deposit alone.

For the production checks described by [the paper](../paper.md), run
`omega_engine_pfp/tests/test_cemetery_sink.py` and
`omega_engine_pfp/tests/test_immune_defect_regressions.py` from the
root of a full repository checkout.

`deposit_paths.py` is shared release tooling that validates deposit paths for
the manifest and archive scripts.

`landau_worksheet.py` uses only the standard library and the catalog snapshot
to recalculate exact quiz arithmetic. It is educational: it does not execute
the sink, validate JCS conformance, or install a detector. Its outputs can be
compared with the separate instructor key.

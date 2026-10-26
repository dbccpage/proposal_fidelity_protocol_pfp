# PFP VI reproduction and evidence boundary

2026-10-02 · Version 0.1.0

The complete argument and worked example live in [the main paper](../paper.md).
This page replaces the earlier claim that paper-local toy tests establish
production behavior or permanent zero-loss retention.

The actual sink is
`omega_engine_pfp/infrastructure/persistence/cemetery_sink.py`.
Its tests are `omega_engine_pfp/tests/test_cemetery_sink.py`.
They include restart, unchanged-header tail truncation, interior payload
tampering, extra keys, malformed UTF-8, Boolean counts, and fixed-marker
cases. A retained external anchor is required for the stronger snapshot
comparison described in paper §5.

The package test `code/tests/test_006_worked_example.py` replays the paper's
Section 6 block as printed and the three modifications described there against
the repository sink. It needs the full repository checkout and skips when the
sink source is absent.

Detector-maintenance examples come from
`omega_engine_pfp/tests/test_immune_defect_regressions.py`, including
the inclusive toxicity threshold, invalid regular expressions, batch-invariant
decay, and the self panel's limited base-content diversity.

The paper-local `code/tests/test_006_epistemic_immune.py` implements separate
illustrative classes. A pass there is evidence about those illustrations only.
See [the code note](../code/README.md). The production two-signal gate has a
different contract from the toy positive-defect threshold.

The retained detector-candidate catalog,
`_intelligence/_antibodies/pharmacy_catalog.json`, is described in paper §7.1
as a data file only. Its counts come from the file at the audited commit, and
`code/tests/test_006_catalog_file.py` recomputes them from those bytes when the
Git object or the identical bound snapshot is available. No code is executed
by loading that snapshot, and the data checks do not establish that any fixture
was applied.

No new live study, immutable storage, automatic semantic miner, cross-domain
transfer, or correspondence between the source code and a formal proof is
reported. Current execution counts must come from the associated source-bound
receipt.

The fresh first-publication review also exercises the receipt's cached-state
boundary, failed replacement leaving memory ahead of disk, nested-map mutation,
unbound header schema/genesis, whitespace, and legitimate extension. Those
checks use verified source bytes from the manuscript's audit commit. The
default branch's later encoder changes have a separate provenance.

The fresh receipt is
[first_publication_validation_2026_10_02.json](first_publication_validation_2026_10_02.json).
The earlier release receipts remain historical and do not bind today's
revised files.

# Governance review

All 76 frozen files have explicit dispositions: **32 full body reads and 44 bounded artifact assessments**. The nine source/test bodies, seventeen logs and six small JSON files were read completely. Large historical manifests and receipts receive population checks with their limits stated per file.

Two concrete implementation defects were reproduced on isolated synthetic inputs:

- C# unbraced conditionals defeat the metric's claimed conservative nesting bound: four nested conditionals report 0.
- A mutation campaign's shared bytecode cache can reuse the first equal-size mutant within one timestamp second. The second mutant is reported killed although a fresh cache lets it survive.

All 50 JSON artifacts pass strict parsing and the selected arithmetic/structure checks. Twelve mutation receipts reconcile 1194 declared outcomes; this is accounting evidence over separate historical populations, not a correctness probability. Thirty-seven equivalence exclusions depend on their stated observation/caller assumptions.

The 9247-path baseline records grandfathering policy. Current raw-byte matching, LF-only matching, content drift and absent targets remain separate. Seventeen run logs match their records; two named historical workflow logs are absent. Current contract/score evidence bindings match raw bytes, while older score versions retain different historical references. Hash consistency cannot authenticate execution or establish historical failure from current drift.

See `additional_governance_remaining.json` for source pins, findings and per-file limits; `additional_governance_artifact_checks.json` retains every checked binding. No original sources or historical evidence were rewritten, and no model/provider/native campaign was run.

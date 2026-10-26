# Source provenance and reproduction

The implementation reference is repository commit
`6d9da6fa7919ae2a8b99b704e784e5a4f422aed2`. This identifies code inspected for
the paper; it does not say that the new manuscript existed at that revision.
Historical source pins and prior paper replay receipts are not rewritten.

The operative sources are:

- `omega_engine_operads/contracts/ddc_code_repair_v1.py`: strict request,
  state and observation contracts, candidate identity and disposition.
- `omega_engine_operads/infrastructure/ddc_code_repair.py`: source-bound
  operation documents, typed workflow compilation and native lowering.
- `omega_engine_woland/infrastructure/ddc_code_repair.py`: actual working-copy
  capture, fixed checks, patch execution and injected observations.
- `omega_engine_woland/entrypoints/code_repair_cli.py`: composition of actual
  runtime adapters, not a paper-local substitute.
- `omega_engine_woland/documentation/examples/code_repair.py`: toy source,
  supplied patch, positive check and negative control.
- `omega_engine_woland/tests/test_ddc_code_repair.py`: focused controls.

Their byte lengths and SHA-256 digests are captured in
[the source provenance record](source_provenance.json), after comparison with
the named Git revision. OEEIS denotes the Omega Engine Epistemic Immune System.

Run from the repository root with the already-built native host configured as
`OMEGA_SYMBOL_GAME_HOST`. Use a new writable directory outside the source tree:

```text
python -m omega_engine_woland.documentation.examples.code_repair --output-root <new-external-run-directory>
```

The directory must not already exist. Inspect `run/receipt.json`, the retained
operation records and check outputs. The expected *example* behavior is baseline
exits `[1, 0]`, post-patch exits `[0, 0]`, six operations and unchanged original
source bytes. A command listed here is reproduction machinery, not evidence that
it ran. Actual observations are recorded separately after execution.

Run the existing focused controls, one named file:

```text
python -m pytest omega_engine_woland/tests/test_ddc_code_repair.py -o addopts= -q
```

On this Windows estate select Python with `py -3.12`, set an external writable
pytest `--basetemp`, and use the existing single-job offline native build if
needed. No new dependency, development gate or live provider call is required.

## Observed local execution — 2026-10-21

The command was executed with Python 3.12.10 and the configured native host.
Run `offline-example-32b225272dcc` returned `REPAIRED`: baseline exits `[1, 0]`,
post-patch exits `[0, 0]`, six native-coordinated steps, no integration residuals,
and retained lineage. The immune verdict was `NOT_MEASURED`, admission
`Unadmitted`, activation `HOLD`, source application `NOT_PERFORMED`, and
mathematical measurement `NOT_MEASURED`. The focused test file passed 22 cases.

The companion [observation summary](observed_execution.json) is a projection of
that local receipt, not a sealed distribution of its full raw bytes. The full
receipt remains in the retained external run directory
`pfp-paper028-ddc-20261021/run/receipt.json`; its SHA-256 is recorded in the
summary. A new execution has a new run identity and may have different
machine-specific observations. Neither execution is a model trial.

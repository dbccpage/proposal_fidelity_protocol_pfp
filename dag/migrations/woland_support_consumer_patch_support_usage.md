# Current use of relocated Woland support

The documentation, calibration bank, historical pricing observations, and frozen
harness campaign were moved from Anomalon. Their recorded paths and hashes describe
their original source environment. Moving files does not rerun or recertify a campaign.

Use Python 3.12 with pytest for the archive unit tests. From the PFP repository root:

```powershell
python -B -m pytest --noconftest -p no:cacheprovider -q pilots/anomalon_woland_support/tests/test_calibration_tasks.py pilots/anomalon_woland_support/tests/test_frozen_review_replay.py pilots/anomalon_woland_support/tests/test_harness_package_copy.py
```

Use a Python 3.12 environment with its own compatible dependencies. Do not mix
native extension packages from a Python 3.13 environment. The archive helper's
Python version check remains unchanged. These tests use synthetic archives and
local checker programs; passing them does not replay the historical full archive.

`tests/test_harness_corpus_calibration.py` additionally requires the Anomalon
harness runtime on `PYTHONPATH`, plus the PFP repository root. On Windows, from
the PFP root, replace the Anomalon path with the local checkout:

```powershell
$env:PYTHONPATH = (Get-Location).Path + ';C:\path\to\anomalon'
python -B -m pytest --noconftest -p no:cacheprovider -q pilots/anomalon_woland_support/tests/test_harness_corpus_calibration.py
```

That single calibration test explicitly resolves the relocated C052/C054/C059
checker pairs. This is a test adapter, not authority to run a live campaign or a
new binding of external checkers into Anomalon's frozen source manifest.

Anomalon's current harness CLI requires both `--prices` and `--pricing-evidence`.
Current live work requires current pricing evidence. The archived observations are
historical evidence, not live defaults. Runtime unit tests own synthetic pricing
fixtures and do not depend on this corpus. Missing certificate-family checkers
raise `HarnessCheckerUnavailable` before provider or billing work; built-in
repair/workflow checks and offline preparation remain importable. Enabling a new
live certificate campaign requires a separately implemented, source-bound adapter.

The unchanged `documentation/harness_evolution/build_review_package.py` and
`replay_review_archive.py` contain historical monorepo-root defaults. Their direct
CLI defaults are not portable from this relocated directory. The replay helper's
pinned full archive was not supplied by this support move. Rebuilding a historical
package requires the complete matching historical source and Atlas context; an
ordinary current checkout is insufficient. Do not rewrite frozen internal paths
or hashes to make those defaults appear current. A future external invocation
adapter must select the exact retained inputs and preserve their authentication.

The original frozen-review test is preserved as
`tests/historical_sources/test_frozen_review_replay.py.txt`; the adjacent executable
test changes only its import to the relocated helper. The calibration-bank test
was moved without changes. Mixed runtime tests contributed only their archive
package-copy and corpus-calibration tests; unrelated runtime regressions remain in
Anomalon.

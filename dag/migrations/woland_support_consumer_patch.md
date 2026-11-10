# Woland support consumer patch review

Prepared against Anomalon `9d5e9f38d7c7f966b2f78a2125db2c0ed4d1cf6c` at
`C:\Users\a343o\source\repos\anomalon`. This work writes only
`dag/migrations/woland_support_consumer_patch*`; it does not apply changes.
The companion JSON includes complete before/after text and SHA-256 preconditions.

The patch requires explicit pricing/evidence inputs in the current harness CLI;
runtime accounting tests retain their arithmetic using test-owned synthetic
observations. The code-repair tests retain their tiny input/check/patch literals
without importing the moved demo. Dedicated calibration-bank and archive-replay
tests move with their corpus; only the relevant two archive-copy tests and one
certificate-calibration test are extracted from mixed runtime files. No unrelated
runtime test is removed or skipped.

The earlier pilot move left six eager checker imports in `harness_tasks.py:9–26`.
They prevented importing the retained harness even for built-in repair tasks.
The proposed lazy resolver gives absent historical checker owners the specific
`HarnessCheckerUnavailable` exception. Internal dependency and entrypoint defects
keep their original exceptions. `HarnessEvaluator.trial` checks availability
before any assignment/provider work; `execute_cases` checks before invoking the
runner; live CLI paths check before creating the store or reading prices.
Offline preparation remains available without claiming provider readiness.
Anomalon does not automatically import PFP checkers. The relocated calibration
test supplies the actual relocated pairs explicitly within that test only.

Validation: **18 passed** under Anomalon's Python 3.13.11 environment using an
in-memory source overlay: 14 new import/early-refusal/pricing-boundary cases plus
four existing exact-type, task-projection, proposal-schema and usage-parsing
tests. An audit hook prohibited sockets and all subprocess execution. All changed
Python sources parse. A broader attempted selection reached native-host calls
and was blocked by this guard; this is not a product failure or a suite pass.
The preserved blocked receipt records 18 passes and one guard rejection for a
native budget quote. Initial broad execution also prevented JUnit's Windows
platform metadata subprocess; final validation avoids that metadata subprocess.

The overlay hashes original disk sources when tests call source-manifest helpers.
The final focused run does not exercise full campaign source binding, native
runtime orchestration, archive extraction children, or the relocated calibration
solver loop. Parent must run appropriate post-application tests against actual
modified files. Parent separately reported 31 baseline archive/bank tests passing
under Python 3.12; that result is not reproduced or attributed to this overlay.

Apply full-source deletions only after migration custody verifies their targets.
The original archive test is retained unchanged as a historical `.py.txt` source;
its executable current adapter changes the import. An already-moved identical
calibration target is a no-op. Do not apply a blind deletion/addition if the move
owner already handled it. The proposed `CURRENT_USE.md` stays outside the frozen
bundle and explains test dependencies and historical helper root assumptions.

The original Rust foundation audit remains checkpointed at 146/368 files with
222 explicitly pending; this consumer task does not change that coverage.

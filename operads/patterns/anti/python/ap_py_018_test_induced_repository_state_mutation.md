---
pattern_id: AP_PY_018
name: test_induced_repository_state_mutation
category: anti_pattern
operad_type: AntiMorphism
operad_source_colours: ["Code"]
operad_target_colour: "Witness"
operad_arity: 1
operad_residual: "contractive"
dual_pattern: HP_PY_017_hermetic_test_tempdir_isolation
language: python
authority_effect: None
---

# Anti-Pattern: Test-Induced Repository State Mutation (`AP_PY_018`)

## Description

Test cases that write output files, JSON artifacts, or live timestamps directly into tracked repository directories (e.g. `demos/results/` or package roots) rather than isolated temporary test directories (`tmp_path`). Running the test suite immediately mutates the working tree, dirties git status, and invalidates release manifest checksums.

## Detection Signature

- Tests directly referencing production artifact paths for output writes:
  ```python
  # BAD: Mutates tracked release artifact during test run
  def test_export():
      output_path = Path("demos/results/certified_results.json")
      output_path.write_text(json.dumps({"timestamp": time.time(), "result": 42}))
  ```
- Good Pattern:
  ```python
  # GOOD: Writes to isolated temporary path provided by pytest fixture
  def test_export(tmp_path: Path):
      output_path = tmp_path / "certified_results.json"
      output_path.write_text(json.dumps({"result": 42}))
  ```

## Hazard & Failure Mode

- Running pytest causes git status to become dirty.
- Breaks automated CI pipelines and deposit manifest verification (`verify_deposit.py`).
- Introduces nondeterministic run-to-run file drift across worktrees.

## Prevention & Resolution

Always use the `tmp_path` fixture for any file-writing test. In `WF_ADVERSARY`, verify `git status --porcelain` post-execution; if any tracked files were modified, fail immediately with `TEST_MUTATED_REPOSITORY_STATE`.

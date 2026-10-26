# Python Quality Inventory

**AuthorityEffect:** None.

The Python Development Office owns one versioned structural inventory for repository Python. It
does not certify semantic Domain-Driven Design, behavioral test coverage, mutation score, or release
readiness.

Run it from the repository root with the pinned runtime:

```powershell
py -3.12 -m omega_engine_operads.frontend.cli.python_dev_cli `
  . --quality-inventory --project-root .
```

The command emits a JSON `omega.python_quality_inventory.v1` receipt and exits:

- `0` for a bounded `STRUCTURAL_PASS`;
- `1` when enforced findings block the policy;
- `2` when policy loading, source acquisition, parsing, or Ruff execution is refused.

The packaged
[`python_quality_policy.v1.json`](../infrastructure/python_development_office/python_quality_policy.v1.json)
is ordered and fail-closed. It classifies every discovered `.py` path as `maintained`, `test`,
`frozen`, `generated`, or `vendor`; a path matching no rule is `UNCLASSIFIED_PYTHON`. The maintained
catch-all is deliberate, so new repository-owned Python cannot disappear from the gate. Each file
row carries a SHA-256, and the receipt binds their ordered path/digest inventory with
`source_sha256`.

The receipt reports physical LOC over 1000, Ruff C901 complexity over 10, control nesting over 3,
function span over 50 lines, and more than 5 arguments. Frozen, generated, and vendor findings stay
visible but are non-enforcing.

Test file presence never satisfies a tier. The gate loads, but never executes, JSON receipts from
`artifacts/python_quality/test_execution_receipts` by default; `--test-receipts` may select another
directory inside the project root. Each `omega.python_test_execution_receipt.v1` record must bind:

- an argument-vector command, Python 3.12 version, exit code, and positive test count;
- repository-relative targets covering every policy-matched file in that tier;
- the current source-inventory and policy SHA-256 digests;
- a timezone-aware completion timestamp no more than seven days old.

The asserted `PASS` is rejected when the exit code or test count disagrees. Unit, integration, E2E,
and security receipts produce `VERIFIED_EXECUTION`. Mutation-style pytest evidence produces the
distinct `MUTATION_STYLE_VERIFIED` status and may not claim a mutation score. Only an actual
`mutation_engine` receipt meeting the policy's 80 percent floor produces
`MUTATION_ENGINE_VERIFIED`. Missing or invalid receipts remain blocking.

Receipt verification establishes internal metadata consistency and freshness, not command
authenticity, coverage completeness, semantic DDD, or release readiness. Clean Architecture, ROP,
and mockability remain explicit obligations until their dedicated gates or human review supply
evidence.

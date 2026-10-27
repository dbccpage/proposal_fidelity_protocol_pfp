# Oracle fixture freeze

Three scripts that freeze Python behaviour (string casing, `repr()`,
JSON truthiness and float rendering) into JSON fixtures that a native
re-implementation must match byte for byte, plus a pytest file that
checks the freezers are deterministic and agree with the interpreter.

Run the checks from the repository root:

    py -3.12 -m pytest demos/oracle_fixture_freeze -q

Expected: `3 passed, 1 skipped` (about 15 s). On Python 3.13+ the casing
freeze is skipped because it is pinned to Unicode 15.0.0, and the
refusal test runs instead.

Write the fixtures to a folder:

    py -3.12 demos/oracle_fixture_freeze/freeze_python_case.py --out oracle_fixtures
    python demos/oracle_fixture_freeze/freeze_python_repr.py --out oracle_fixtures
    python demos/oracle_fixture_freeze/freeze_json_acceptance.py --out oracle_fixtures

Wiki page: `wiki/Test-Oracle-Fixture-Freeze.md`.

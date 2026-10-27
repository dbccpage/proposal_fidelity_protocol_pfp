# Imported trees against the acceptance floor

AuthorityEffect: None. This is a screen of `main` at `6e6d9ed7`, not a score.
Counts only. The trees joined the governed population with a baseline on
2026-10-27, so the counts below are what scoring them would find.

None of these files has a completed score, so none of them meets the
`SCORING.md` section 1.5 floor yet. Once the rename of private names lands,
they join the governed population with a baseline of their exact bytes:
every file stays accepted only while it is unchanged, and any edit must come
with an L4D score (L2D for tests).

## What is there

| Tree | Python (runtime / tests) | Rust | Lean 4 |
| --- | --- | --- | --- |
| `pfp/` | 1,534 / 1,470 | 0 | 117 |
| `eis/` | 62 / 48 | 0 | 0 |
| `operads/` | 483 / 190 | 1 | 0 |
| `pciv/` | 63 / 30 | 0 | 0 |
| `ops/` | 774 / 67 | 25 | 4 |
| `papers/` | 387 / 154 | 99 | 239 |
| `education/` | 25 / 13 | 0 | 8 |
| **Total** | **3,328 / 1,972** | **125** | **368** |

`code/` holds Rust crates being renamed in the shared checkout; it is not on
`main` yet and joins the same way when it lands.

## What a full score would trip on first

These are the checks that would hold a file below D, counted per tree. They
are a screen, not a verdict: a production `assert` that only checks an internal
debug invariant is allowed by RULE_PY_003.

| Check (runtime files only) | pfp | eis | operads | pciv | ops | papers | education |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Files with `assert` (RULE_PY_003, Gate 3 E if it guards validation) | 402 | 5 | 34 | 1 | 42 | 25 | 3 |
| `assert` statements | 897 | 9 | 454 | 2 | 104 | 123 | 5 |
| Files with float literals (Gate 2 E on an exact path) | 70 | 2 | 22 | 3 | 65 | 51 | 14 |
| Broad `except` (Gate 3 D) | 86 | 2 | 53 | 3 | 73 | 43 | 1 |
| `isinstance(x, int)` with no bool guard nearby (RULE_PY_002) | 8 | 0 | 0 | 1 | 0 | 0 | 0 |
| Python files with an `AuthorityEffect` header (Gate 1 needs it) | 2,134 | 52 | 309 | 73 | 564 | 61 | 30 |

Lean: 8 files in `papers/` contain `sorry` and 6 declare an `axiom`. Under
RULE_LEAN_003 a theorem that depends on `sorry` cannot be a completed proof
(Gate 3 E) until it is discharged or the claim is narrowed.

There is also the earlier finding that many files import package names that do
not exist in this repository (the rename work addresses those), and that no
`mypy` configuration covers these trees.

## Suggested order for bringing them up to the floor

1. Land the rename, then record the baseline so nothing regresses.
2. Score the trees PFP Lab is most likely to reuse first: `eis/` and `pciv/`
   are small (62 and 63 runtime files).
3. In `pfp/`, start with `domain/` and `use_cases/`. The assert-heavy
   `infrastructure/tower_*` research code is better kept baselined, or moved
   out of the governed population, than scored.
4. Treat `papers/` per paper: each is a self-contained deposit with its own
   checksums, so changing its code also changes its release record.

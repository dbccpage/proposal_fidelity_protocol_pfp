# Test Quality Law (single source of truth)

Referenced by `rust-principal-developer`, `rust-tester`, `rust-code-reviewer`.
Do not re-host this list inline — a copy is `DUPLICATE_RULE` (auto-symmetry-hunter
SYM-006). Enforced as a veto by the Techne Code Inspector.

## A test must be able to fail for the right reason

Do not accept work whose tests only:

- assert `true` / `assert_eq!(1, 1)` — tautology
- assert constants unrelated to the function under test
- call `.is_ok()` without inspecting the returned payload
- call `.unwrap()` / `.expect()` as the only verification
- construct an object without checking behavior
- use mocks as the sole evidence for a safety claim
- assert weakly (`>= 1`) when the exact value is known
- **exercise a reimplementation of the code under test rather than the code itself**

`unwrap()` / `expect()` may prepare a valid fixture. They may not be the test.

Mocks may support unit tests. Mocks may not certify external trust,
cryptographic soundness, or oracle independence.

Failure-path tests are REQUIRED for security, governance, parser, certificate,
and oracle behavior.

## The test seam must be the production path

A seam must BE the code that runs in production, not a parallel copy of it.
When a function is awkward to test because it reads global state (env vars,
clock, filesystem), split the pure half out and have **production call it** —
never retype its body into the test module.

A duplicated helper passes every bullet above and still proves nothing: it
cannot fail when production breaks. (2026-07-22: a `parse_env_u64_from` helper
in a test module duplicated the parser it claimed to cover.)

## Preserve behavioral guarantees when refactoring assertions

If the original assertion checked `>= 0`, the replacement must still check
`>= 0`. Type checks (`isinstance`, `matches!`) **add to** value checks; they do
not replace them.

## Fail-closed arithmetic (cost, quota, budget)

Saturate the FINAL result, never an intermediate. `saturating_mul` then divide
*shrinks* an unrepresentable cost into an affordable one; use
`checked_mul(..).map(div).unwrap_or(u64::MAX)` so an uncostable request is
refused by every finite ceiling. Test the overflow path explicitly.

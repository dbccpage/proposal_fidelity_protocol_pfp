# Soviet Builder Construction Report Template

```markdown
# Soviet Builder Construction Report

## 1. Target
- Target Path / Crate / Package / Tier
- Answering Inspector Finding (if any)

## 2. Theoretical Minimum
| # | Invariant | Break | Witness | Mutation |
|---|---|---|---|---|
| 1 | <What must always be true> | <Concrete wrong value/state> | <Observable assertion> | <1-line production mutation> |

## 3. Tests Built
| Test Name | Tier | Landau Class | File:Line | Kills / Verifies |
|---|---|---|---|---|
| `test_boundary_overflow_rejected` | unit | Class 2 | `tests/test_foo.py:24` | Boundary overflow |

- **Coverage Shape:** N Class-1/2, M Class-3/4/5.

## 4. Mutation Evidence (MANDATORY)
| Test Name | Mutation Applied | Red Exit Code? | Failure Message | Green after Revert? |
|---|---|---|---|---|
| `test_boundary_overflow_rejected` | Removed boundary check | YES (Exit 1) | `AssertionError: Expected Refusal` | YES (Exit 0) |

## 5. Build & Execution Evidence
- Command: `python -m pytest tests/test_foo.py -v`
- Exit Code: `0`
- Verbatim Output Tail: `1 passed in 0.05s`

## 6. Refusals & Uncovered Invariants
- Refused: <Items declined with rationale>
- Not Covered: <Invariants un-witnessed this round with explanation>

## 7. Handoff
- Ready for `/techne-code-soviet-inspector` evaluation. (Zero self-grading).
```

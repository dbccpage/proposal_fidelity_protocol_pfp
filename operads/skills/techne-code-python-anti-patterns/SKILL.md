---
name: techne-code-python-anti-patterns
description: "Audit Python code and diffs for known anti-patterns in data models, type boundaries and runtime behavior."
operad_source_colours: ["Code"]
operad_target_colour: "Audit"
operad_arity: 1
operad_residual: "unknown"
families: [techne, quality, python]
---

# Techne Code Python Anti-Patterns

**Status:** canonical-candidate  
**AuthorityEffect:** None

Specialist skill for detecting, isolating, and remediating Python anti-patterns and certifying dual healthy patterns across the repository.

## Operational Scope

Operates directly against Python modules in `omega_engine/`, `omega_engine_operations/`, and companion scripts. Consults the canonical catalog at `omega_engine_operads/patterns/anti/python/`.

### Canonical Anti-Patterns & Dual Healthy Patterns

| ID | Anti-Pattern | Hazard | Dual Healthy Pattern |
|---|---|---|---|
| `AP_PY_001` | Blanket Mypy Ignore (`# type: ignore`) | Conceals interface defects and type erosion | [`HP_PY_001`](../../patterns/helpful/python/HP_PY_001_scoped_mypy_overrides.md) Scoped Mypy Overrides |
| `AP_PY_002` | Array Hash/Equality Asymmetry | `UnhashableType` crashes, non-deterministic sets | [`HP_PY_002`](../../patterns/helpful/python/HP_PY_002_canonical_immutable_array.md) Canonical Immutable Array |
| `AP_PY_003` | Bare Exception Swallowing (`except Exception: pass`) | Silences syntax and runtime errors, masking critical failure states | Typed error logging or explicit `Result[T, E]` refusal |
| `AP_PY_004` | Unmanaged File Handle (`open()` without context manager) | Resource descriptor leak on crash or early return | `with open(...) as handle:` context manager |
| `AP_PY_005` | Mutable Default Arguments (`def f(x=[])`) | Leaked state across invocations causing non-deterministic mutation | Default to `None` and instantiate within body |
| `AP_PY_006` | Arrow Anti-Pattern / Deep Control Nesting | Unmaintainable cyclomatic complexity ($M > 10$), loops nested $\ge 4$ levels deep | Guard clauses, early returns, decomposed helper functions |
| `AP_PY_007` | Domain Re-Export / Forwarder Shim | Competing import paths, circular dependency traps, masked refactoring incompleteness | Direct canonical layer imports (`RULE_CLEAN_ARCH_NO_SHIMS_001`) |
| `AP_PY_008` | Host I/O Leakage in Domain Objects | Impure models, non-deterministic domain tests, filesystem/subprocess coupling | Abstract domain ports and infrastructure adapters (`RULE_CLEAN_ARCH_INWARD_001`) |

## Review & Audit Rubric

1. **AST & Signature Scan:**
   - Scan for blanket `# type: ignore` without specific error codes (e.g. `# type: ignore[arg-type]`).
   - Scan `@dataclass(frozen=True)` definitions containing mutable `np.ndarray` or `list` fields without custom `__hash__` and `__eq__`.
   - Scan for bare `except:`, `except Exception: pass`, and unclosed file handles without context managers.
2. **Type Boundary Verification:**
   - Verify all value objects implement exact-type equality (`isinstance(other, cls)` or `type(other) is cls`).
   - Check dataclass field discipline per Python engineering standards.
3. **Dual Pattern Remediation:**
   - For every detected anti-pattern $A(c) \neq \emptyset$, propose the unique dual healthy pattern endomorphism $H(c)$ such that:
     $$\|A(H(c))\| = 0$$

## Automated Anti-Pattern Audit Script

The canonical automated auditor is available at [`scripts/python_anti_pattern_auditor.py`](scripts/python_anti_pattern_auditor.py).

### Usage

```bash
# Audit a specific module or package
py -3.12 omega_engine_operads/skills/techne-code-python-anti-patterns/scripts/python_anti_pattern_auditor.py --path omega_engine_operations/

# Fail-closed CI check returning non-zero exit code on BLOCKER/MAJOR anti-patterns
py -3.12 omega_engine_operads/skills/techne-code-python-anti-patterns/scripts/python_anti_pattern_auditor.py --path . --check

# Generate Markdown report
py -3.12 omega_engine_operads/skills/techne-code-python-anti-patterns/scripts/python_anti_pattern_auditor.py --path omega_engine/ --report-out reports/python_anti_pattern_report.md
```

## Integration with Pattern Hunter

This skill is invoked directly by [`auto-code-anti-pattern-hunter`](../auto-code-anti-pattern-hunter/SKILL.md) during multi-language audits and by [`auto-oe-autop`](../auto-oe-autop/SKILL.md).


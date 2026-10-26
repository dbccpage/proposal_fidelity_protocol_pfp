---
name: techne-silent-failure-hunter
description: "Find swallowed exceptions, naked unwrap and unhandled error fall-through in Python and Rust (ROP Result purity)."
operad_source_colours:
  - Code
operad_target_colour: Audit
operad_arity: 1
operad_residual: diagnostic
---

# Techne Silent Failure Hunter

**AuthorityEffect:** None.

## Mission & Governance Invariants

The **Silent Failure Hunter** reports configured AST and text patterns. It does not prove control-flow safety or Result types; Rust text matching and Python unwrap warnings need human review.

The scanner detects anti-patterns where errors, exceptions, or typed refusals are silently discarded or bypassed rather than propagated through Railway-Oriented Programming (ROP) monads.

In accordance with repository Clean Architecture and error-handling standards:
1. **No Swallowed Exceptions:** Bare `except:` statements and handlers consisting only of `pass` or `...` are strictly prohibited.
2. **Explicit Result Monad Propagation:** Production code returning `Result[T, Refusal]` (in Python) or `Result<T, E>` (in Rust) must not execute bare `.unwrap()` or `.expect()` calls without checking variants or propagating errors.
3. **Typed Refusals:** Every error path must materialize a structured, typed `Refusal` record carrying an error code, explanatory message, and diagnostic locus.

---

## Targeted Detection Rules

| Rule ID | Surface | Anti-Pattern | Required Remediation |
|---|---|---|---|
| `SFH-PY-001` | Python | Bare `except:` | Catch specific exception types or `Exception`. |
| `SFH-PY-002` | Python | Swallowed exception (`pass` / `...`) | Log error, raise, or return typed `Err(Refusal(...))`. |
| `SFH-PY-003` | Python | Naked `.unwrap()` in non-test source | Branch on `.is_ok` / `.is_err` or propagate up the call stack. |
| `SFH-RS-001` | Rust | Naked `.unwrap()` / `.expect()` in non-test crates | Propagate error using the `?` operator or handle via `match`. |
| `SFH-RS-002` | Rust | Empty `if let Err(_) = ... {}` | Handle failure or record diagnostic trace. |

---

## Operational Workflow

### 1. Diagnostic Invocation

Run the automated scanner across modified files or packages:

```console
# Scan specific file or directory
py -3.12 -m omega_engine_operations.use_cases.verification.silent_failure_hunter path/to/target/

# Output machine-readable JSON report for audit pipelines
py -3.12 -m omega_engine_operations.use_cases.verification.silent_failure_hunter --json path/to/target/
```

### 2. Remediation Protocol

When a violation is detected:
1. **Analyze the root cause:** Identify whether the operation can genuinely fail in production (I/O, parsing, network, contract boundary).
2. **Transform to Result Monad:**
   - **Python:** Return `Result[T, Refusal]` using `Ok(value)` or `Err(Refusal(code=..., message=..., locus=...))`.
   - **Rust:** Return `Result<T, AppError>` and propagate using `?`.
3. **Verify locally:** Re-run the scanner and execute scoped unit tests (`py -3.12 -m pytest path/to/test.py`).

---

## Anti-Patterns & Compliant Examples

### Python: Swallowed vs Monadic

**Non-compliant (Swallowed):**
```python
try:
    data = json.loads(payload)
except Exception:
    pass  # SFH-PY-002: Swallows failure silently!
```

**Compliant (Railway-Oriented):**
```python
try:
    data = json.loads(payload)
    return Ok(data)
except json.JSONDecodeError as exc:
    return Err(
        Refusal(
            code="PAYLOAD_JSON_MALFORMED",
            message=str(exc),
            locus="module.service",
        )
    )
```

### Rust: Naked Unwrap vs Propagation

**Non-compliant (Unsafe panic in production):**
```rust
let config = parse_config(&bytes).unwrap(); // SFH-RS-001
```

**Compliant (Explicit propagation):**
```rust
let config = parse_config(&bytes)
    .map_err(|e| ConfigError::InvalidSyntax(e.to_string()))?;
```

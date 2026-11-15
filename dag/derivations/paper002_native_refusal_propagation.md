# PAPER002-NATIVE-REFUSAL-PROPAGATION: Native Refusal Propagation

AuthorityEffect: None.

- Archive claim: [ATL-P002-011](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers) ("A found native sign-graph executable decides; its refusals and malformed outputs raise typed errors and are never replaced by a Python answer.", [paper_claim_ledger.md:26](../../atlas/archive/pfp/002_pfp_signed_presentations_and_search_frontier/paper_claim_ledger.md?plain=1#L26))
- Audit derivation node: [PAPER002-NATIVE-REFUSAL-PROPAGATION](../../atlas/atlas_claim_ledger.md#part-ii-derivations-recorded-by-the-repository-audit) (`ATL-D-PAPER002-NATIVE-REFUSAL-PROPAGATION`)
- Review verdict: `matched` (`states_same_claim_as`)

## 1. Claim Statement

When a native sign-graph executable is found, its refusals and malformed outputs raise typed errors, never replaced by a Python answer.

## 2. Context & Hypotheses

- **Native Binary Discovery**:
  The environment or package directory provides an executable binary located via `native_sign_graph.find_binary()`.
- **Typed Error Hierarchy**:
  - `NativeSignGraphRefused`: Raised when the native executable exits with a non-zero code or returns a payload with status other than `PASS`.
  - `NativeSignGraphUnavailable`: Raised when the native executable is missing, cannot execute, emits non-JSON output, or returns malformed witness payloads.
- **Execution Invariant**:
  When a native executable is found, execution delegates to `_run_native`. Neither `classify_sign_graph` nor `verify_gauge` catches `NativeSignGraphRefused` or `NativeSignGraphUnavailable` to fall back to the Python solver `py_classify_sign_graph` or `py_verify_gauge`.

## 3. Derivation / Evidence

### 3.1 Non-Replacement of Explicit Refusals
In `native_sign_graph.py`, `_run_native` inspects the child process exit status and stdout payload:
```python
if completed.returncode != 0 or not isinstance(payload, dict) or payload.get("status") != "PASS":
    detail = payload.get("error") if isinstance(payload, dict) else None
    raise NativeSignGraphRefused(
        f"native solve_sign_graph refused (exit {completed.returncode}): {detail or completed.stderr.strip()[:200]}"
    )
```
In `classify_sign_graph`:
```python
if binary is not None:
    request = {"operation": "classify", "vertices": list(vertices), "edges": _edges(edges)}
    payload = _run_native(binary, request, timeout=timeout)
    ...
```
No `except NativeSignGraphRefused:` handler exists. The exception propagates directly to the caller, preventing silent replacement with a Python-calculated answer.

### 3.2 Non-Replacement of Malformed Outputs
When stdout cannot be decoded as JSON or does not conform to the expected witness schema, `_run_native` raises `NativeSignGraphUnavailable`:
```python
try:
    payload = json.loads(completed.stdout)
except json.JSONDecodeError as error:
    if completed.returncode != 0:
        raise NativeSignGraphRefused(...) from error
    raise NativeSignGraphUnavailable("native solve_sign_graph returned malformed output") from error
```
Similarly, schema validation failures on witness fields raise `NativeSignGraphUnavailable`. No fallback handler intercepts this exception.

### 3.3 Executable Verification
The behavior is verified by `tests/test_paper_002_native_and_convergence.py` (and upstream `test_native_refusals.py`):
1. A stub binary returning `{"status": "REFUSED"}` with exit code 2 raises `NativeSignGraphRefused`.
2. A stub binary returning invalid JSON or malformed witness shapes raises `NativeSignGraphUnavailable`.
3. Inserting an active trap into `py_classify_sign_graph` confirms that the Python classifier is never invoked when the native binary is present.

## 4. Limits and Non-Claims

- **Transport Scope**:
  Applies to the Python-to-native execution transport in `native_sign_graph.py`. It does not provide a formal proof of correctness for the underlying Rust source code.
- **Environment Dependency**:
  Relies on standard operating system process execution and subprocess status codes.

## 5. Claim Hygiene Summary

1. **What it supports**:
   Supports that `native_sign_graph.py` raises typed errors (`NativeSignGraphRefused`, `NativeSignGraphUnavailable`) upon executable refusal or malformed output without silent fallback to Python.
2. **What it does not support**:
   Does not support formal verification of the external binary itself or cross-platform compilation promises.
3. **Narrowest defensible claim**:
   When `find_binary()` locates an executable, refusal or malformed output raises typed runtime errors without invoking `py_classify_sign_graph`.
4. **Next test needed**:
   Testing subprocess timeout handling under high load or process starvation.

## 6. Cross-References & Provenance

- Archive Claim: [ATL-P002-011](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers)
- Paper Claim: [PFP002-11](../../atlas/archive/pfp/002_pfp_signed_presentations_and_search_frontier/paper_claim_ledger.md?plain=1#L26)
- Manuscript Source: Section 7 ("Reproduction, custody, and negative controls")
- Verification Test: `tests/test_paper_002_native_and_convergence.py`

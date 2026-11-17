# Detailed definition: Python Contracts & Runtime Invariants (1)

**AuthorityEffect:** None.

Parent: [Python Contracts & Runtime Invariants](../../../../../rules/engineering/rl_python_contracts_and_runtime_invariants.md). Load for the matching predicate, not every task.

# Rule: Python Contracts & Runtime Invariants

**AuthorityEffect:** None.

This rule codifies array value object hashing and equality normalization, standard library monkeypatch signature parity, explicit subprocess check discipline, zero-assert production runtime checking, PyYAML colon-in-string sequence item quoting discipline, and boolean subclass exclusion guards in exact numeric contracts.

---

## Python Array Value Object Hash & Equality Discipline Invariant (`RULE_PYTHON_HASH_EQUALITY_NORMALIZATION_001`)

> **Buffer and Array Hashability Invariant:**
>
> 1. **Hash/Equality Symmetry:** If a class implements custom `__eq__` and `__hash__` over numeric buffers or arrays (e.g. NumPy arrays), representations that compare equal MUST yield identical hash values.
> 2. **Canonical Initialization Normalization:** Classes wrapping numeric arrays MUST canonicalize the buffer in `__post_init__` or `__init__`:
>    a. Convert to a fixed canonical dtype (typically `np.float64` or `np.int64`) and contiguous C-order layout (`order="C"`).
>    b. Canonicalize IEEE 754 zero representations (`-0.0` converted to `+0.0`). In quotient objects or vectors, execute zero canonicalization (`arr[arr == 0.0] = 0.0`) *after* all reflections or coordinate transformations, immediately prior to buffer serialization or hashing. Negation (`arr = -arr`) reintroduces `-0.0`, altering buffer bytes and corrupting hash equality despite numerical `==` equivalence.
>    c. Validate domain bounds and reject invalid values (`NaN`, unhandled infinities).
>    d. Freeze array writability explicitly (`mat.flags.writeable = False`) to prevent post-insertion hash mutation.
> 3. **Unhashable Fallback:** If a class wrapping mutable or non-normalized state cannot guarantee byte-level canonicalization and immutability, it must be declared explicitly unhashable (`__hash__ = None`).
> 4. **Required Parity Tests:** Any hashable array wrapper must be tested for cross-dtype equality and hash parity (`int64` vs `float64`), set deduplication, dictionary lookup, and writeability protection.


> **Pattern estate:** `AP_PY_002` / `HP_PY_002` (`.agents/patterns/anti/python/`).

## Standard Library Monkeypatch Signature Parity Invariant (`RULE_PYTHON_MONKEYPATCH_SIGNATURE_PARITY_001`)

> **Mock Signature Compatibility Invariant:**
>
> 1. **Keyword-Safe Mock Signatures:** When monkeypatching standard library functions or methods (e.g., `Path.stat`, `os.stat`, `Path.resolve`, `os.walk`), replacement callables MUST accept arbitrary positional and keyword arguments (`*args, **kwargs`) unless explicitly testing signature rejection.
> 2. **Pytest Harness Cleanliness:** Monkeypatches on standard library methods must not reject arguments passed by runtime or test runner internals (such as `follow_symlinks` in `stat()` calls), ensuring clean test execution and reporting teardown.

## Python Subprocess Explicit Check Parameter Invariant (`RULE_PYTHON_SUBPROCESS_CHECK_DISCIPLINE_001`)

> **Explicit Subprocess Check Discipline:**
>
> 1. **Mandatory Explicit Check Parameter:** All invocations of `subprocess.run(...)` across tools, verifiers, test harnesses, and pipelines MUST explicitly declare the `check` argument (`check=False` or `check=True`).
> 2. **Explicit Returncode Inspection:** When a verifier or script inspects `result.returncode` manually to collect errors, it MUST specify `check=False` explicitly so error-handling intent is deterministic and linter / security audits (e.g. Bandit/Ruff S603/B603) pass without warning.
> 3. **Implicit Default Ban:** Leaving `check` unspecified relies on implicit default behavior and is strictly forbidden across all repository code, templates, and scripts.

## Runtime Invariant Checking Without Asserts Invariant (`RULE_PYTHON_NO_ASSERT_RUNTIME_CHECK_001`)

> **Zero-Assert Production Runtime Checking:**
>
> 1. **Prohibition of `assert` in Operational Code:** Python `assert` statements are stripped under optimization (`-O`). Domain constructors, value object validators, and `__eq__` implementations must never rely on `assert` for runtime validation.
> 2. **Explicit Failure Mechanisms:** In `__eq__`, use `if type(self) is not type(other): return False`. In initializers, raise explicit exceptions (`ValueError`, `TypeError`) or return ROP `Err(...)` / `Refusal(...)`.
> 3. **Prohibition in Code Generators & Templates:** Code generation scripts, code templates (e.g. `PYDANTIC_TWIN_TEMPLATE`), and scaffolding tools must NEVER emit `assert` statements into generated operational modules, contract twins, or validation functions. Generated validation functions must raise explicit exceptions (e.g. `raise ValueError(...)`) or return typed receipts.
> 4. **Scanner Conformance:** All production modules and generator templates must pass `python_antipattern_scanner.py` with 0 occurrences of Pitfall 037 (`ASSERT_AS_RUNTIME_CHECK`).

## YAML Colon-in-String Quoting Discipline Invariant (`RULE_PYTHON_YAML_COLON_QUOTING_001`)

> **PyYAML Mapping Ambiguity Prevention:**
>
> 1. **Outer Quotes Required:** In all YAML specifications, catalogs, contracts, and test fixtures, any scalar in a sequence/list item containing a colon followed by whitespace (`:`) MUST be enclosed in explicit outer single quotes (e.g. `- 'contains explicit "AuthorityEffect: None" header'`).
> 2. **PyYAML Parser Trap:** Unquoted colons followed by whitespace within list items cause PyYAML to parse the item as a single-key dictionary (`{'contains explicit "AuthorityEffect': 'None" header'}`), resulting in runtime validation crashes on Pydantic `List[str]` models.
> 3. **Model Resilience:** Pydantic domain models accepting user- or catalog-supplied contract criteria must define `List[Union[StrictStr, Dict[str, Any]]]` where upstream specifications permit structured predicate mappings alongside raw strings.

## Boolean Subclass Guard in Exact Numeric Contracts Invariant (`RULE_PYTHON_BOOLEAN_SUBCLASS_GUARD_001`)

> **Boolean Exclusion in Exact Integer and Rational Validation:**
>
> 1. **The Python Boolean Subclass Trap:** In Python, `bool` is a concrete subclass of `int` (`issubclass(bool, int) is True`). Consequently, `isinstance(True, int)` and `isinstance(False, int)` evaluate to `True`.
> 2. **Exact Validation Requirement:** In exact rational arithmetic, packet payloads, boundary index checks, and numeric token validation, code must never rely on unqualified `isinstance(x, int)` where booleans would introduce invalid states (e.g. `Fraction(True) == 1`).
> 3. **Canonical Guard Pattern:** Replace unqualified `type(x) is int` (flagged by AST linters) or vulnerable `isinstance(x, int)` with the explicit dual healthy guard:
>    ```python
>    isinstance(value, int) and not isinstance(value, bool)
>    ```

## Python Dataclass Replace Exception Typing Invariant (`RULE_PYTHON_DATACLASS_REPLACE_EXCEPTION_TYPING_001`)

> **Cross-Version Exception Parity in Dataclass Immutability Fences:**
>
> 1. **The Python `dataclasses.replace` Exception Shift:**
>    - In Python 3.12, calling `dataclasses.replace(obj, ...)` with an argument corresponding to a field declared with `init=False` raises `ValueError("init=False")`.
>    - In Python 3.13 and Python 3.14, the standard library implementation raises `TypeError("field ... is declared with init=False, it cannot be specified with replace()")`.
> 2. **Dual-Exception Test Assertions:**
>    - Test harnesses asserting that uninitializable (`init=False`) or private contract fields cannot be injected or mutated via `replace()` must catch both exception types:
>      ```python
>      with pytest.raises((ValueError, TypeError), match="init=False"):
>          replace(result, certificate_status="certified")
>      ```
>    - Relying solely on `ValueError` creates fragile tests that fail when executed under newer Python interpreters.

## Complete Typed Answer Comparison

At an existing exact contract boundary, compare the complete typed answer and its
complete task binding, then snapshot nested result data. In particular, `true`
and `1` are distinct contract values even when Python equality says otherwise.
Keep raw input bytes and the canonical semantic request digest distinct. A hash
identifies bytes; authentication requires a separate trust contract.

The retained Hodge candidate
contains boolean-substitution, wrong-task-hash and mutable-alias controls. This is
review guidance for that class of boundary, not a new universal JSON profile.

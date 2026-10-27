---
name: techne-code-python-code-reviewer
description: "Review Python diffs against contracts, callers, types, refusals and tests. Findings first; green tests are not proof."

operad_source_colours: ["Code"]
operad_target_colour: "Audit"
operad_arity: 1
operad_residual: "unknown"
---

# Python code reviewer

## Activate when

Reviewing a Python change, pull request, verifier, solver, adapter, receipt, or
test harness.

## Review order

1. Read the diff, declared contract, callers, and tests. Confirm the imported
   symbol is supplied by the intended module, not merely any resolving module.
2. Trace inputs to effects. Flag mutable globals, hidden I/O, authority widening,
   unbounded work, broad exception laundering, and caller-minted evidence.
3. Check exact type and canonicalization boundaries, including nested frozen-data
   mutation and duplicate inflation.
4. Run the automated 50-Mistake Python Anti-Pattern Scanner on modified files:

   ```bash
   <configured-python> operads/skills/techne-code-python-code-reviewer/scripts/python_antipattern_scanner.py <target-paths>
   ```

5. Check mathematical claims against the computation actually performed: carrier,
   metric, quantifier, coefficient domain, descent measure, and proof ceiling.
6. Run the test-quality gate and the smallest falsifying suite. Add a mutation or
   counterexample when a critical branch has never been observed failing.
7. Lead with actionable findings ordered by severity, each with a tight path and
   line. State which commands actually ran and which guarantees remain unverified.

## The 50 Canonical Python Pitfalls & Review Rubric

Reviewers must audit changes against the 50 common defect patterns:

### 1. Arguments & Mutation

- **01. Mutable default arguments**: Default is a list/dict/set or mutable constructor. *Fix:* `def f(items=None): items = items or []`.
- **03. Modifying a collection while iterating**: Removing/adding items inside a loop over the same list/dict. *Fix:* Iterate over a copy or use comprehension.
- **16. List concatenation in loops**: `lst = lst + [item]` or `lst += [item]`. *Fix:* Use `.append()` or `.extend()`.
- **17. Ignoring mutating method return values**: `lst = lst.sort()` (returns `None`). *Fix:* Call method without assignment or use `sorted()`.
- **19. Shallow copy vs deep copy**: Nested structures sharing references via `.copy()`. *Fix:* Use `copy.deepcopy()`.
- **32. Unintended aliasing**: `a = b = []` sharing references. *Fix:* Initialize separately.
- **34. Class attribute vs instance attribute**: Mutable collection declared directly in class body. *Fix:* Initialize on `self` in `__init__`.
- **50. Shallow copy on nested mutables**: Reusing references in dictionaries. *Fix:* Use `copy.deepcopy()`.

### 2. Equality, Identity & Types

- **02. Using `is` for equality**: `if value is 1000` or `if s is "text"`. *Fix:* Use `==`.
- **07. Using `== None` instead of `is None`**: *Fix:* Use `is None` / `is not None`.
- **09. Using `type()` for type checking**: `if type(x) == int` breaks subclasses. *Fix:* Use `isinstance(x, int)`. **Note on exact numeric contracts:** In exact integer and rational validation, remember that `bool` is a subclass of `int`. To satisfy the linter while preserving strict mathematical fences, use `isinstance(x, int) and not isinstance(x, bool)`.
- **20. Using `is` with strings/integers/floats**: Identity with non-singletons. *Fix:* Use `==`.

- **21. Misunderstanding `and`/`or` return values**: Expecting bool from truthy values. *Fix:* Use `bool(a and b)`.
- **38. Redundant `if x == True`**: *Fix:* `if x:`.
- **39. Redundant `if x == False`**: *Fix:* `if not x:`.
- **40. Using `is True` / `is False` redundantly**: *Fix:* Use truthiness check `if x:` directly.
- **41. Comparing `None` with equality**: *Fix:* Always use `is None`.

### 3. Resource Lifecycle & Scope

- **04. Unclosed files**: `open()` without context manager. *Fix:* Always use `with open(...) as f:`.
- **06. Missing `if __name__ == "__main__":` guard**: Executable top-level code running on import. *Fix:* Enclose in main guard.
- **08. Shadowing built-in names**: Assigning to `list`, `dict`, `str`, `len`, `type`, `sum`, etc. *Fix:* Use descriptive domain names.
- **11. Variable scope confusion**: Unbound locals or global mutations. *Fix:* Explicit returns or classes.
- **12. Wildcard imports**: `from module import *`. *Fix:* Explicit named imports.
- **31. Excessive `global`**: Multiple global declarations in a single function. *Fix:* Encapsulate in classes.
- **45. Not using `with` for context managers**: Manual `.acquire()`/`.release()` on locks. *Fix:* `with lock:`.

### 4. Exception Handling

- **05. Catching overly broad exceptions**: `except Exception: pass` concealing critical bugs. *Fix:* Catch narrow domain exceptions; log/re-raise.
- **13. Swallowing exceptions**: Empty `except:` blocks without handling or logging. *Fix:* Re-raise or record structured refusal.
- **28. Bare `except:`**: Catches `SystemExit` and `KeyboardInterrupt`. *Fix:* `except Exception:` or specific types.
- **29. Raising string literal**: Python 2 legacy syntax `raise "error"`. *Fix:* `raise ValueError("error")`.

### 5. Iteration, Loops & Formatting

- **10. Off-by-one in `range`**: `range(1, 10)` excluding 10. *Fix:* Verify inclusive/exclusive bounds.
- **15. String concatenation in loops**: `s += item` quadratic accumulation. *Fix:* `''.join(parts)`.
- **18. Assuming legacy dictionary order**: *Fix:* Use explicit `OrderedDict` or modern Python 3.7+ conventions.
- **22. Manual loop found flags**: *Fix:* Use `for...else` constructs where appropriate.
- **23. Using `range(len(...))`**: Indexing manually. *Fix:* Iterate directly `for item in lst:`.
- **24. Manual index counters**: *Fix:* Use `for i, item in enumerate(lst):`.
- **25. Indexing parallel lists**: *Fix:* Use `for a, b in zip(list_a, list_b):`.
- **26. Unnecessary `.keys()` in membership**: `if k in d.keys():`. *Fix:* `if k in d:`.
- **27. Reusing generator/iterator**: Consuming exhausted generators. *Fix:* Materialize to `tuple`/`list` if multiple passes needed.
- **30. Legacy string formatting**: `%` or `.format()` where f-strings are clearer. *Fix:* Use f-strings.

### 6. Object-Oriented & Class Design

- **33. Not calling `super().__init__()`**: Subclasses skipping parent initialization. *Fix:* Add `super().__init__(...)`.
- **35. Misusing `@staticmethod` when class context needed**: *Fix:* Use `@classmethod`.
- **36. Getter/setter without `@property`**: *Fix:* Use `@property` and `@<prop>.setter`.
- **42. Forgetting `return` in recursive call**: Recursive step evaluated without return. *Fix:* `return recursive_step(...)`.
- **43. Missing `self` parameter in instance methods**: *Fix:* Ensure `self` is the first parameter.
- **44. Overly complex lambdas**: Long, unreadable lambdas. *Fix:* Define named local functions.

### 7. Process, Security & Environment

- **14. Using `print` instead of structured logging**: Production debug prints. *Fix:* Use `logging` or structured receipt records.
- **37. Using `assert` for runtime validation**: `assert` stripped in optimized Python (`-O`). *Fix:* Raise typed domain exceptions.
- **46. `shell=True` with untrusted input in `subprocess`**: Shell injection risk. *Fix:* Pass list of args and omit `shell=True`.
- **47. Unchecked `subprocess` return codes**: Ignoring process exit status. *Fix:* Use `check=True` or verify `result.returncode`.
- **48. Using `os.system`**: Unescaped command execution. *Fix:* Use `subprocess.run()`.
- **49. Naive `datetime.now()`**: Missing timezone context. *Fix:* Use `datetime.now(timezone.utc)`.

## Approval ceiling

`NO FINDINGS` means no issue was found within the reviewed scope. It is not a
correctness proof, external certification, or promotion authority.

**AuthorityEffect: None.** The reviewer must not approve its own implementation.

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every modified Markdown file must be UTF-8 clean and pass the configured Markdown
lint gate. Report the actual command and status.

---
name: techne-ast-anti-mock-and-facade-auditor
description: "Scan tests via AST for MagicMock/patch, trivial pass-throughs and stub functions faking real implementations."
operad_source_colours:
  - Code
  - Audit
operad_target_colour: Receipt
operad_arity: 2
operad_residual: diagnostic
families:
  - techne
  - ast
  - testing
  - clean-architecture
---

# Techne AST Anti-Mock and Facade Auditor

**AuthorityEffect:** None.  
**Council:** `L3_logos_techne`  
**Status:** Active.

## Mission & Governance Invariants

The **AST Anti-Mock and Facade Auditor** parses Python and Rust test suites via abstract syntax trees (AST) to detect deceptive testing facades, monkeypatching of domain entities, and vacuous stub functions that report test success without executing real business logic.

In accordance with Clean Architecture and local-first verification standards:

1. **Zero-Mock Domain Ports:** Tests must use concrete in-memory implementations (e.g. `InMemoryStore`, `LocalFileStorage`) or real domain objects. `unittest.mock.MagicMock`, `mock.patch`, and dynamic monkeypatching of domain invariants are prohibited.
2. **No Vacuous Stub Functions:** Functions, classes, or trait adapters that implement protocol methods using solely `pass`, `return True`, `return None`, or `...` are flagged as deceptive facades unless explicitly decorated with `@abstractmethod`.
3. **No Tautological Assertions:** Tests asserting `assert True`, `assert 1 == 1`, or `assert result == result` without comparing against independent expectations are flagged as zero-verification defect generators.

---

## Targeted AST Inspection Rules

| Rule ID | AST Node Pattern | Deceptive Practice Detected | Required Remediation |
|---|---|---|---|
| `AMF-AST-001` | `ImportFrom(module='unittest.mock', names=['MagicMock', 'patch'])` | Introduction of dynamic mock framework | Replace with typed in-memory adapter or fixture. |
| `AMF-AST-002` | `Call(func=Name(id='monkeypatch'))` on domain functions | Monkeypatching core domain functions | Inject explicit dependency via constructor or domain port. |
| `AMF-AST-003` | `FunctionDef(body=[Pass() | Return(Constant(True))])` | Vacuous stub bypassing verification | Implement concrete evaluation logic or fail test. |
| `AMF-AST-004` | `Assert(test=Constant(value=True))` | Tautological assertion verifying nothing | Assert against concrete, computed return value. |
| `AMF-AST-005` | Empty `test_*` function body | Test stub masquerading as test coverage | Populate with meaningful assertions or remove. |

---

## Operational Workflow

### 1. Static AST Scan

Execute the AST scanner across test directories:

```console
# Audit test suite AST for mocks and facades
py -3.12 -c "
import ast, sys
from pathlib import Path

target = Path('operations/tests')
for p in target.glob('**/*.py'):
    tree = ast.parse(p.read_text(encoding='utf-8', errors='replace'))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == 'unittest.mock':
            print(f'MOCK DETECTED: {p}:{node.lineno}')
"
```

### 2. Concrete Double Guidelines

When a collaborator service or storage layer must be decoupled:
- **Do:** Create a typed, in-memory double implementing the domain `Protocol` (e.g. `class InMemoryEventStore(EventStorePort)`).
- **Do:** Keep the double within `tests/doubles/` or local test files.
- **Don't:** Patch global functions or bypass type checking with dynamically constructed `MagicMock` instances.

### 3. Claim Hygiene

- A clean AST scan supports that no prohibited mocking patterns or vacuous stubs are present.
- It does not show that the test assertions are complete or that integration bugs cannot occur.

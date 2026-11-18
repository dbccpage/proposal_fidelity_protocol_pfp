# `python_development_office` — reassembled in-folder

**AuthorityEffect:** `None`. Findings are measurements. A clean scan is not a
review, not a proof, and not admission of anything.

Reassembled 2026-08-17 from `dbccpage/sentinelpy` at `6f39bd7042`.

## Why it was missing

`python_antipattern_scanner.py` was a four-line shim: it inserted
`parents[4]` — the repository root — onto `sys.path` and imported
`operads.frontend.cli.python_dev_cli`. That package is not in
CODA, so the scanner raised `ModuleNotFoundError` on any invocation. The same
shim existed under `techne-code-python-principal-developer`, and the skill's
own test file imported four more `operations` modules.

`.agents/COPY.md` is explicit: *"Do not import `operations` into
CODA to make a skill work."* The engine was therefore copied here.

## What was ported

The engine was spread across four layers of the `operations`
application. Layer boundaries were kept; only the import prefixes changed.

| Here | From |
| --- | --- |
| `python_development_office/domain/` | `operads/domain/python_development_office/` |
| `python_development_office/use_cases/` | `operads/application/python_development_office/` |
| `python_development_office/infrastructure/` | `operads/infrastructure/python_development_office/` |
| `python_development_office/controllers/controller.py` | `operads/controllers/python_development_office_controller.py` |
| `python_development_office/frontend/cli.py` | `operads/frontend/cli/python_dev_cli.py` |

26 modules, ~2,100 lines, standard library only. The engine self-scans with
zero findings.

## Where this copy deliberately differs

1. **`dependency_exceptions` is empty.** Upstream shipped four
   `DependencyException` entries, each naming an `operations`
   consumer/provider pair. None of those modules exist here, so the entries
   would have been a debt register describing a different repository. Add real
   entries as real debt is found — one exact pair at a time, never a
   layer-wide allowance.

2. **`source_roots` retargeted** from `operations`,
   `engine`, `governance` (absent here) to `src`, `app`,
   `scripts`, `ci`, `coda`.

3. **CLI default target** was `operations`; it is now `.`.

4. **The principal-developer skill borrows this engine** rather than carrying
   a second copy. Its `scripts/python_antipattern_scanner.py` resolves
   `../techne-code-python-code-reviewer/scripts/` and fails with a readable
   message if this skill is culled. If the two skills are ever separated, copy
   this folder there.

## Running it

```bash
python .agents/skills/techne-code-python-code-reviewer/scripts/python_antipattern_scanner.py <path>
```

```bash
python .agents/skills/techne-code-python-code-reviewer/scripts/python_antipattern_scanner.py <path> --json
```

Flags: `--arch-only`, `--pitfalls-only`, `--config <json|yaml>`, `--json`.
Exit is non-zero when findings exist.

```bash
python -m pytest .agents/skills/techne-code-python-code-reviewer/tests -q
```

## What a clean scan does not certify

The rules are AST pattern matches and import-graph layer checks. They catch
mutable default arguments, `is` against literals, bare excepts, builtin
shadowing, and inward-pointing dependency violations. They say nothing about
whether the code is correct, whether its tests are real, or whether any claim
it supports holds.

`AuthorityEffect: None.`

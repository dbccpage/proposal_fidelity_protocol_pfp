---
name: oe-monorepo-workspace-reorg-harness
description: "Check monorepo root-path resolution, path hygiene in operations, and UTF-8 subprocess safety on Windows."

operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# oe-monorepo-workspace-reorg-harness

## Authority & Compliance

- **AuthorityEffect**: `None`
- **Governance**: Techne / Blackrod / Nomos
- **Scope**: Monorepo workspace root-path hygiene and depth-correct positional resolution.

---

## 🏛️ Monorepo Root Resolution Architecture

```text
operations/use_cases/tool.py ──► Path(__file__).resolve().parents[2] ──► sentinel/ (Repo Root)
operations/entrypoints/local_ci.py ──► infrastructure/cicd/local_ci_runtime.py ──► Path(__file__).resolve().parents[3] ──► sentinel/ (Repo Root)
engine_py/tools/     ──► Path(__file__).resolve().parents[2] ──► sentinel/ (Repo Root)
```

---

## 📋 Rules & Path Hygiene Laws

1. **Depth-Correct Root Anchor Law**: Resolve `REPO_ROOT` positionally from the script's actual canonical locus and assert the result. Two-level tools under `operations/use_cases/` use `parents[2]`; `use_cases/cicd/local_ci.py` uses `parents[3]`.
2. **Subprocess UTF-8 Encoding Safety**: On Windows environments, `subprocess.run` calls evaluating `git diff`, `git ls-files`, or sub-commands MUST explicitly specify `encoding="utf-8", errors="replace"` or handle binary stdout (`text=False`).
3. **LF Line Ending Invariant**: All text release files under `engine/research/` MUST carry LF (`\n`) line endings without CRLF (`\r\n`) contamination.

---

## 🛠️ Execution & Audit Commands

```powershell
# Run oeops rust module coverage check
python operations/use_cases/rust_module_coverage.py

# Run impacted crates self-test
python operations/use_cases/impacted_crates.py --test

# Run local CI pre-push correctness gate
python -m operations.entrypoints.local_ci --repository <candidate-repository> --trusted-head <trusted-commit> --expected-head <candidate-commit> --expected-main <main-commit> --nonce <64-hex> --report-file <absolute-report.json>
```

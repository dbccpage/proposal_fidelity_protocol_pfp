"""Discovery of challenge packages and of how to call their checkers.

A descriptor records, for one package, the facts the harness needs and the
source they were read from: the packet shape, the scoring script whose calls
the harness mirrors, the checker functions, the gate that combines them, the
reference solver, the judge cases, the mutation suite, the participant
examples and the runner files that build prompts.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from omega_engine_woland.tests.pilots.judge_packet_audit import static_analysis as sa

CHALLENGES_REL = "omega_engine_pfp/tests/demo_004"
CASE_DIRS = ("cases", "hidden_cases")
MUTATION_DIRS = ("mutation_suite", "hostile_mutations")
MUTATION_CASE_KEYS = ("case", "input_case")
MUTATION_ANSWER_KEYS = (
    "corrupted_result",
    "corrupted_output",
    "corrupted_answer",
    "corrupted_ans",
    "corrupted_solution",
    "mutated_result",
    "mutated_answer",
    "mutated_output",
    "certificate",
    "candidate",
    "answer",
    "result",
)
EXAMPLE_INPUT_KEYS = ("input", "case")
EXAMPLE_OUTPUT_KEYS = ("expected_output", "expected", "output", "answer", "solution", "result")
SELF = "$self"


def challenges_root(repo_root: Path) -> Path:
    return repo_root / CHALLENGES_REL


def discover_packages(repo_root: Path) -> list[Path]:
    """Every directory two levels below the current owner that holds a ``judge_packet/``."""
    root = challenges_root(repo_root)
    found = []
    for theme in sorted(p for p in root.iterdir() if p.is_dir()):
        for pkg in sorted(p for p in theme.iterdir() if p.is_dir()):
            if (pkg / "judge_packet").is_dir():
                found.append(pkg)
    return found


def package_id(pkg_dir: Path) -> str:
    return pkg_dir.name.split("_")[0].upper()


def rel_posix(path: Path, base: Path) -> str:
    return path.relative_to(base).as_posix()


def _json_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    files = [p for p in root.rglob("*.json") if "__pycache__" not in p.parts]
    return sorted(files, key=lambda p: p.relative_to(root).as_posix().encode("utf-8"))


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _case_id(case: Any) -> str | None:
    if isinstance(case, dict):
        for key in ("id", "case_id"):
            if isinstance(case.get(key), str):
                return case[key]
        inner = case.get("input")
        if isinstance(inner, dict):
            return _case_id(inner)
    return None


def components(pkg_dir: Path) -> dict[str, bool]:
    jp = pkg_dir / "judge_packet"
    return {
        "participant_packet": (pkg_dir / "participant_packet").is_dir(),
        "judge_packet": jp.is_dir(),
        "reference_solver": (pkg_dir / "reference_solver").is_dir(),
        "governance": (pkg_dir / "governance").is_dir(),
        "tests": (pkg_dir / "tests").is_dir(),
        "commitments": (pkg_dir / "commitments").is_dir() or (pkg_dir / "commit_reveal").is_dir(),
        "judge_manifest": (jp / "manifest.json").is_file() or (pkg_dir / "manifest.json").is_file(),
        "mutation_suite": any((jp / d).is_dir() for d in MUTATION_DIRS),
        "separate_checker_dir": (jp / "checkers").is_dir(),
        "commit_reveal_script": any(pkg_dir.glob("commit_reveal*.py"))
        or (pkg_dir / "governance" / "commit_reveal_runner.py").is_file(),
        "reality_gate_receipt": (pkg_dir / "reality_gate_receipt.json").is_file(),
        "matrix_runner": any(pkg_dir.glob("run_*matrix*.py")),
    }


def scoring_script(pkg_dir: Path) -> Path | None:
    gov = pkg_dir / "governance" / "commit_reveal_runner.py"
    if gov.is_file():
        return gov
    scripts = sorted(pkg_dir.glob("commit_reveal*.py"))
    return scripts[0] if scripts else None


def _first_style(raw_modules: list[tuple[int, str, int]]) -> str:
    """'absolute' if the first judge_packet import is relative or through the repository path."""
    for _lineno, module, level in sorted(raw_modules):
        if "judge_packet" in module or "reference_solver" in module or level > 0:
            if level > 0 or module.startswith(sa.SOURCE_CHALLENGES_PREFIXES):
                return "absolute"
            return "toplevel"
    return "absolute"


def _raw_import_modules(path: Path) -> list[tuple[int, str, int]]:
    tree = sa.parse_source(path)
    out = []
    if tree is None:
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            out.append((node.lineno, node.module or "", node.level))
    return out


def build_descriptor(repo_root: Path, pkg_dir: Path) -> dict[str, Any]:
    ch_root = challenges_root(repo_root)
    rel_dotted = ".".join(pkg_dir.relative_to(ch_root).parts)
    notes: list[str] = []
    comps = components(pkg_dir)
    shape = "governance_packet" if comps["governance"] else "light_packet"
    script = scoring_script(pkg_dir)
    descriptor: dict[str, Any] = {
        "package_id": package_id(pkg_dir),
        "rel_path": rel_posix(pkg_dir, repo_root),
        "theme": pkg_dir.parent.name,
        "shape": shape,
        "components": comps,
        "scoring_script": rel_posix(script, pkg_dir) if script else None,
        "notes": notes,
    }
    checkers: list[dict[str, str]] = []
    gate: dict[str, str] = {"kind": "all_accept"}
    solver: dict[str, str] | None = None
    style = "absolute"
    if script is None:
        notes.append("no scoring script found")
    else:
        records = sa.imports_of(script, pkg_dir, rel_dotted)
        style = _first_style(_raw_import_modules(script))
        judge_records = [r for r in records if r.internal and r.module.startswith("judge_packet")]
        solver_records = [
            r
            for r in records
            if r.internal
            and (r.module == "reference_solver" or r.module.startswith("reference_solver."))
        ]
        gate_records = [r for r in judge_records if "dual_evaluator" in r.module and r.name]
        if shape == "governance_packet" and gate_records:
            names = {r.name for r in gate_records}
            chosen = (
                "evaluate_dual" if "evaluate_dual" in names else sorted(n for n in names if n)[0]
            )
            gate_module = next(r.module for r in gate_records if r.name == chosen)
            gate = {"kind": "function", "module": gate_module, "function": chosen}
            checkers = _checkers_called_by_gate(pkg_dir, rel_dotted, gate_module)
            if not checkers:
                notes.append("gate module imports no checker functions")
        else:
            seen: set[tuple[str, str]] = set()
            for record in judge_records:
                target, name = sa.imported_target(record, pkg_dir)
                if name is None or (target, name) in seen:
                    continue
                seen.add((target, name))
                leaf = target.split(".")[-1]
                role = {"exact_checker": "exact", "independent_checker": "independent"}.get(
                    leaf, leaf
                )
                checkers.append({"role": role, "module": target, "function": name})
        solver = _solver_from(solver_records, pkg_dir)
        if solver is None:
            notes.append("no reference solver import in scoring script")
    descriptor["import_style"] = style
    descriptor["import_prefix"] = (
        (sa.CHALLENGES_PREFIX + rel_dotted + ".") if style == "absolute" else ""
    )
    descriptor["checkers"] = checkers
    descriptor["gate"] = gate
    descriptor["solver"] = solver
    cases, unwrap = _cases(pkg_dir)
    descriptor["cases"] = cases
    descriptor["unwrap_input"] = unwrap
    descriptor["mutations"], descriptor["mutation_dir_other_files"] = _mutations(pkg_dir)
    descriptor["examples"] = _examples(pkg_dir)
    descriptor["theme_examples"] = _theme_examples(pkg_dir)
    descriptor["runner_files"] = _runner_files(pkg_dir)
    return descriptor


def _checkers_called_by_gate(
    pkg_dir: Path, rel_dotted: str, gate_module: str
) -> list[dict[str, str]]:
    path = sa.module_file(pkg_dir, gate_module)
    if path is None:
        return []
    tree = sa.parse_source(path)
    if tree is None:
        return []
    records = [r for r in sa.imports_of(path, pkg_dir, rel_dotted) if r.internal and r.name]
    by_alias = {}
    for record in records:
        target, name = sa.imported_target(record, pkg_dir)
        if name is not None and target.startswith("judge_packet") and target != gate_module:
            by_alias[record.alias] = (target, name)
    order: list[tuple[str, str]] = []
    for _lineno, called in sa.called_names(tree):
        if called in by_alias and by_alias[called] not in order:
            if _takes_case_and_answer(pkg_dir, *by_alias[called]):
                order.append(by_alias[called])
    return [
        {"role": f"checker_{i + 1}", "module": m, "function": f} for i, (m, f) in enumerate(order)
    ]


def _takes_case_and_answer(pkg_dir: Path, module: str, function: str) -> bool:
    """True when ``function`` is defined with at least two positional parameters.

    Gates also call one-argument helpers (for example a CNF builder); those are
    not checkers of an answer.
    """
    path = sa.module_file(pkg_dir, module)
    tree = sa.parse_source(path) if path else None
    if tree is None:
        return False
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function:
            return len(node.args.posonlyargs) + len(node.args.args) >= 2
    return False


def _solver_from(records: list[sa.ImportRecord], pkg_dir: Path) -> dict[str, str] | None:
    candidates = []
    for record in records:
        target, name = sa.imported_target(record, pkg_dir)
        if name is None:
            candidates.append((0 if target.endswith(".solver") else 1, target, "solve"))
        else:
            candidates.append((0 if name == "solve" else 2, target, name))
    if not candidates:
        return None
    _, module, function = sorted(candidates)[0]
    return {"module": module, "function": function}


def build_case_ids(pkg_dir: Path) -> list[str]:
    """Identifiers of the package's judge cases (cases without one are skipped)."""
    return [c["case_id"] for c in _cases(pkg_dir)[0] if c["case_id"]]


def _cases(pkg_dir: Path) -> tuple[list[dict[str, Any]], bool]:
    jp = pkg_dir / "judge_packet"
    cases: list[dict[str, Any]] = []
    unwrap = False
    for dirname in CASE_DIRS:
        for path in _json_files(jp / dirname):
            rel = rel_posix(path, pkg_dir)
            data = _load_json(path)
            if isinstance(data, list):
                items = list(enumerate(data))
            elif isinstance(data, dict) and isinstance(data.get("cases"), list):
                items = list(enumerate(data["cases"]))
            else:
                items = [(None, data)]
            for index, case in items:
                if (
                    isinstance(case, dict)
                    and isinstance(case.get("input"), dict)
                    and len(case) <= 2
                ):
                    unwrap = True
                key = rel if index is None else f"{rel}#{index}"
                cases.append({"key": key, "path": rel, "index": index, "case_id": _case_id(case)})
    return cases, unwrap


def _mutations(pkg_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    jp = pkg_dir / "judge_packet"
    out: list[dict[str, Any]] = []
    other: list[str] = []
    for dirname in MUTATION_DIRS:
        for path in _json_files(jp / dirname):
            rel = rel_posix(path, pkg_dir)
            try:
                data = _load_json(path)
            except (ValueError, UnicodeDecodeError):
                other.append(rel)
                continue
            if isinstance(data, list):
                items = list(enumerate(data))
            elif isinstance(data, dict) and isinstance(data.get("mutations"), list):
                items = list(enumerate(data["mutations"]))
            else:
                items = [(None, data)]
            found = False
            for index, item in items:
                if not isinstance(item, dict):
                    continue
                case_key = next(
                    (k for k in MUTATION_CASE_KEYS if isinstance(item.get(k), dict)), None
                )
                answer_key = next((k for k in MUTATION_ANSWER_KEYS if k in item), None)
                if case_key is None or answer_key is None:
                    continue
                found = True
                key = rel if index is None else f"{rel}#{index}"
                out.append(
                    {
                        "key": key,
                        "path": rel,
                        "index": index,
                        "case_key": case_key,
                        "answer_key": answer_key,
                    }
                )
            if not found:
                other.append(rel)
    return out, other


def _example_record(path: Path, base: Path) -> dict[str, Any] | None:
    try:
        data = _load_json(path)
    except (ValueError, UnicodeDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    input_key = next((k for k in EXAMPLE_INPUT_KEYS if isinstance(data.get(k), dict)), None)
    output_key = next((k for k in EXAMPLE_OUTPUT_KEYS if k in data), None)
    answer_file = None
    if input_key is None and output_key is None:
        if path.stem.endswith("_expected") or path.stem.endswith("_answer"):
            output_key = SELF
        else:
            input_key = SELF
            for suffix in ("_expected", "_answer"):
                sibling = path.with_name(f"{path.stem}{suffix}.json")
                if sibling.is_file():
                    answer_file = rel_posix(sibling, base)
    return {
        "path": rel_posix(path, base),
        "input_key": input_key,
        "output_key": output_key,
        "answer_file": answer_file,
    }


def _examples(pkg_dir: Path) -> list[dict[str, Any]]:
    out = []
    for path in _json_files(pkg_dir / "participant_packet" / "examples"):
        record = _example_record(path, pkg_dir)
        if record is not None:
            out.append(record)
    return out


def _theme_examples(pkg_dir: Path) -> list[dict[str, Any]]:
    theme = pkg_dir.parent
    prefix = pkg_dir.name.split("_")[0]
    out = []
    for path in _json_files(theme / "examples"):
        if not path.name.startswith(prefix):
            continue
        record = _example_record(path, theme)
        if record is not None:
            out.append(record)
    return out


RUNNER_EXCLUDED_DIRS = (
    "judge_packet",
    "tests",
    "governance",
    "commitments",
    "commit_reveal",
    "__pycache__",
)


def is_runner_named(rel: str) -> bool:
    """Matrix runners and participant runners, whose dict literals are cases sent to models."""
    name = rel.rsplit("/", 1)[-1]
    return rel.startswith("participant_packet/") or (name.startswith("run_") and "matrix" in name)


def _runner_files(pkg_dir: Path) -> list[str]:
    """Every package source file outside the judge packet, tests and governance.

    The leakage lint reports prompt interpolations only where a file builds
    prompts, so scanning broadly costs nothing and catches prompt builders that
    live inside ``reference_solver/``.
    """
    files = set()
    for path in pkg_dir.rglob("*.py"):
        rel = rel_posix(path, pkg_dir)
        if path.name == "__init__.py" or any(
            part in RUNNER_EXCLUDED_DIRS for part in rel.split("/")[:-1]
        ):
            continue
        if path.name.startswith("test_"):
            continue
        files.add(rel)
    return sorted(files, key=lambda s: s.encode("utf-8"))

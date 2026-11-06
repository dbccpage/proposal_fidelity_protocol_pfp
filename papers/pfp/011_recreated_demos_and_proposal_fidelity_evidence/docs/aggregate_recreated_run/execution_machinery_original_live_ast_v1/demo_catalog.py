"""Discover the preserved demonstration and challenge obligations without imports."""

from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

DEMO_IDS = (
    "antimorphism_farm",
    "demo_1",
    "demo_10",
    "demo_11",
    "demo_12",
    "demo_2",
    "demo_3",
    "demo_3_mub6",
    "demo_4",
    "demo_4e_cogsci_autopoiesis",
    "demo_5",
    "demo_6",
    "demo_7",
    "demo_8",
    "demo_9",
    "demo_antimorphic_reversal",
    "demo_cohomology_battery",
    "demo_eis_failure_classes",
    "demo_genesis_crosswalk",
    "demo_mub6_regge",
    "demo_polygraph_confluence",
    "demo_q40_quantum_solver",
    "demo_symbol_tui",
    "demo_system_coverage",
    "demo_token_frontier",
    "demo_tower_lift",
    "demo_adversary_tribunal",
)
OLD_PREFIX = "projects.mssn_sn_symgam"
LOCAL_PREFIX = "paper011_source"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def _module_file(package: Path, module: str) -> Path | None:
    path = package.joinpath(*module.split("."))
    if path.with_suffix(".py").is_file():
        return path.with_suffix(".py")
    if (path / "__init__.py").is_file():
        return path / "__init__.py"
    return None


def _imports(path: Path, dotted: str) -> list[dict]:
    found = []
    tree = ast.parse(path.read_bytes(), filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        module = node.module or ""
        if module.startswith(OLD_PREFIX + ".challenges." + dotted + "."):
            module = module.removeprefix(OLD_PREFIX + ".challenges." + dotted + ".")
        if node.level:
            package = next(
                parent for parent in path.parents if parent.name == dotted.split(".")[-1]
            )
            base = list(path.parent.relative_to(package).parts)
            if node.level > 1:
                base = base[: len(base) - node.level + 1]
            module = ".".join([*base, *module.split(".")])
        if module.startswith(("judge_packet", "reference_solver")):
            for alias in node.names:
                found.append(
                    {"module": module, "function": alias.name, "alias": alias.asname or alias.name}
                )
    return found


def _checkers(package: Path, imports: list[dict], dotted: str) -> list[dict]:
    found = []
    for entry in imports:
        if not entry["module"].startswith("judge_packet"):
            continue
        if "dual_evaluator" in entry["module"]:
            file = _module_file(package, entry["module"])
            if file:
                found.extend(_checkers(package, _imports(file, dotted), dotted))
            continue
        file = _module_file(package, entry["module"])
        if not file:
            continue
        tree = ast.parse(file.read_bytes())
        function = next(
            (
                node
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == entry["function"]
            ),
            None,
        )
        if function and len(function.args.posonlyargs + function.args.args) >= 2:
            found.append({"module": entry["module"], "function": entry["function"]})
    unique = {(row["module"], row["function"]): row for row in found}
    return [unique[key] for key in sorted(unique)]


def _json_refs(base: Path, directories: tuple[str, ...]) -> list[dict]:
    found = []
    for directory in directories:
        root = base / directory
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.json"), key=lambda p: p.as_posix().encode("utf-8")):
            raw = path.read_bytes()
            data = json.loads(raw)
            items = (
                data
                if type(data) is list
                else data.get("cases")
                if type(data) is dict
                and set(data).issuperset({"cases"})
                and type(data["cases"]) is list
                else None
            )
            indices = range(len(items)) if items is not None else [None]
            for index in indices:
                found.append(
                    {
                        "path": path.relative_to(base).as_posix(),
                        "index": index,
                        "sha256": digest(raw),
                    }
                )
    return found


def build_catalog(source: Path) -> dict:
    runner = source / "demos/demos_runner.py"
    raw = runner.read_bytes()
    tree = ast.parse(raw)
    dispatch = next(
        node.value
        for node in tree.body
        if isinstance(node, ast.AnnAssign)
        and isinstance(node.target, ast.Name)
        and node.target.id == "DEMO_DISPATCH"
    )
    ids = tuple(sorted(node.value for node in dispatch.keys))
    if ids != DEMO_IDS:
        raise ValueError("preserved demo dispatch differs from the declared 27 obligations")
    challenges = []
    root = source / "challenges"
    packages = {
        p.name.split("_")[0].upper(): p
        for theme in root.iterdir()
        if theme.is_dir()
        for p in theme.iterdir()
        if p.is_dir()
        and re.match(r"c\d{3}_", p.name)
        and ((p / "judge_packet").is_dir() or p.name.startswith(("c001_", "c005_")))
    }
    for number in range(1, 61):
        cid = f"C{number:03d}"
        package = packages.get(cid)
        if package is None:
            specs = sorted(root.glob(f"*/c{number:03d}_*.md"))
            challenges.append(
                {
                    "id": cid,
                    "kind": "SPECIFICATION_ONLY",
                    "specifications": [
                        {"path": p.relative_to(source).as_posix(), "sha256": digest(p.read_bytes())}
                        for p in specs
                    ],
                    "obligation": "Implement the declared task, finite inputs, proposer and independent checker; no executable package is retained.",
                }
            )
            continue
        dotted = ".".join(package.relative_to(root).parts)
        if cid in {"C001", "C005"}:
            challenges.append(
                {
                    "id": cid,
                    "kind": "MECHANISM_RECREATION",
                    "package": package.relative_to(source).as_posix(),
                    "module": LOCAL_PREFIX + ".challenges." + dotted,
                    "obligation": "Execute the package's concrete offline mechanism and negative controls; model effects require separately authorized retained weights/provider budget.",
                    "implementation": "code/mechanism_recreations.py",
                }
            )
            continue
        scripts = sorted(package.glob("commit_reveal*.py"))
        governance = package / "governance/commit_reveal_runner.py"
        scoring = governance if governance.is_file() else scripts[0] if scripts else None
        imports = _imports(scoring, dotted) if scoring else []
        solvers = [
            {"module": r["module"], "function": r["function"]}
            for r in imports
            if r["module"].startswith("reference_solver")
        ]
        solver = next(
            (
                r
                for r in solvers
                if r["function"]
                in {"solve", "solve_case", "solve_instance", "solve_problem", "check", "ref_check"}
            ),
            solvers[0] if solvers else None,
        )
        checkers = _checkers(package, imports, dotted)
        if cid == "C042":
            checkers = [
                {"module": "judge_packet.checkers.dual_evaluator", "function": "evaluate_dual"}
            ]
        if not checkers:
            for file in sorted((package / "judge_packet").rglob("*checker.py")):
                module = file.relative_to(package).with_suffix("").as_posix().replace("/", ".")
                for node in ast.parse(file.read_bytes()).body:
                    if (
                        isinstance(node, ast.FunctionDef)
                        and node.name
                        in {
                            "check",
                            "check_solution",
                            "verify_candidate",
                            "independent_check",
                            "verify",
                            "validate",
                        }
                        and len(node.args.posonlyargs + node.args.args) >= 2
                    ):
                        checkers.append({"module": module, "function": node.name})
        challenges.append(
            {
                "id": cid,
                "kind": "REFERENCE_AND_CHECKER_RECREATION",
                "checker_contract": "DECLARED_BRANCH_EVALUATOR"
                if cid == "C042"
                else "RETAINED_CHECKER_FUNCTIONS",
                "input_contract": {
                    "adapter": "data.get('input', data)",
                    "source_path": (package / "tests/test_e2e_challenge.py")
                    .relative_to(source)
                    .as_posix(),
                    "sha256": digest((package / "tests/test_e2e_challenge.py").read_bytes()),
                }
                if cid == "C024"
                else "DIRECT",
                "package": package.relative_to(source).as_posix(),
                "module": LOCAL_PREFIX + ".challenges." + dotted,
                "scoring_source": {
                    "path": scoring.relative_to(source).as_posix(),
                    "sha256": digest(scoring.read_bytes()),
                }
                if scoring
                else None,
                "solver": solver,
                "checkers": checkers,
                "cases": _json_refs(package, ("judge_packet/cases", "judge_packet/hidden_cases")),
                "mutations": _json_refs(
                    package, ("judge_packet/mutation_suite", "judge_packet/hostile_mutations")
                ),
                "obligation": "Execute the original branching SAT/DRAT gate once; retain its declared single-checker scope and the absence of independent algorithm provenance. This is source recreation, not model accuracy."
                if cid == "C042"
                else "Both retained checkers must accept actual non-abstaining reference outputs; recorded mutations must be rejected. This is source recreation, not model accuracy or independent algorithm provenance.",
            }
        )
    return {
        "schema_version": "paper011.recreation-catalog.v1",
        "authority_effect": "None",
        "source_runner_sha256": digest(raw),
        "demos": [{"id": cid} for cid in ids],
        "challenges": challenges,
        "additional_finding_families": [
            "FSP_BLIND_CLUSTER_RECOVERY",
            "MUB6_AFFINE_PHASE_ANSATZ",
            "AST_REFACTORING_RETRACTION",
            "SPECIMEN_MT000_REDUCTION",
            "UNIFIED_PACKET_STREAMS",
            "EIGHT_BEAT_DIALOGUE",
            "RETRACTION_CONDITIONING",
            "ANTIMORPHISM_FARM",
            "FSP_PHYSICS_RETRACTIONS",
            "PAIRED_ADVERSARIAL_DEBATE",
            "DISCRETE_GEOMETRY_PROBES",
            "PHARMACY_CATALOG",
            "CHALLENGE_MUTATION_SUITES",
        ],
        "genesis_challenges": [f"G{number:02d}" for number in range(1, 26)],
    }

"""Headless fresh-process execution and source inventory for additive MSS-N labs.

Uses CPython directly, not an IPython/Jupyter kernel. The lesson cells contain
ordinary Python only. Optional notebook editing in Jupyter uses the same cells.
No hosted model, API key, network connection, or Rust build is required.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_OEPFP_CURRICULUM_DEST = (
    ROOT / "education/documentation/004_oepfp/curriculum"
)
_PRIMARY_DEST = (
    ROOT / "education/curriculum/3_the_symbol_game_proposal_fidelity_protocol_pfp"
)
_FALLBACK_DEST = ROOT / "education/curriculum/lessons/system_integration"
_LEGACY_DEST = (
    ROOT
    / "education/documentation/3_the_symbol_game_proposal_fidelity_protocol_pfp/lessons/system_integration"
)
_CANDIDATE_DESTS = (
    _OEPFP_CURRICULUM_DEST,
    _PRIMARY_DEST,
    _FALLBACK_DEST,
    _LEGACY_DEST,
    ROOT / "education/the_symbol_game/lessons/system_integration",
)
DEST = next(
    (cand for cand in _CANDIDATE_DESTS if (cand / "lesson_manifest.json").is_file()),
    next((cand for cand in _CANDIDATE_DESTS if cand.is_dir()), _OEPFP_CURRICULUM_DEST),
)
EXCLUDED_PARTS = {
    ".git",
    ".lake",
    "vendor",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".ipynb_checkpoints",
    ".venv",
    "node_modules",
    "target",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )


# Explicit roots retain research navigation after implementation ownership moves.
# Generated education inventories and execution receipts are outside these roots.
_RESEARCH_ROOT = (
    "research"
    if (ROOT / "research").is_dir()
    else (
        "research_papers"
        if (ROOT / "research_papers").is_dir()
        else "pfp"
    )
)
SOURCE_ROOTS = (
    (_RESEARCH_ROOT, "research", None),
    (
        "pfp/domain/tower/level_engine.py",
        "pfp",
        "level_engine/domain",
    ),
    (
        "pfp/entrypoints/cli/level_engine_commands.py",
        "pfp",
        "level_engine/entrypoint",
    ),
    (
        "pfp/infrastructure/tower_research/level_engine",
        "pfp",
        "level_engine/runtime",
    ),
    (
        "pfp/infrastructure/tower_research/reach",
        "pfp",
        "level_engine/reach-prerequisite",
    ),
    (
        "pfp/infrastructure/tower_evidence/level_engine",
        "pfp",
        "level_engine/evidence",
    ),
    (
        "operations/use_cases/level_engine",
        "operations",
        "level_engine/operations",
    ),
    (
        "pfp/tests/level_engine",
        "pfp",
        "level_engine/runtime-tests",
    ),
    ("operations/tests/level_engine", "operations", "level_engine/tests"),
    (
        "governance/contracts/level_engine/v2",
        "governance",
        "level_engine/governance",
    ),
    ("lean4/research_programs/level_engine", "lean4", "level_engine/lean"),
    ("lean4/ExactRat.lean", "lean4", "level_engine/shared-exact-rational"),
    ("lean4/ExactRat", "lean4", "level_engine/shared-exact-rational"),
)
HISTORICAL_LEVEL_ENGINE_ROOT = (
    "pfp/infrastructure/tower_evidence/level_engine/v1/"
)
HISTORICAL_REACH_ROOT = "pfp/infrastructure/tower_research/reach/data/v1/"


def _source_files(root):
    if root.is_file():
        yield root
        return
    for parent, dirs, filenames in os.walk(root):
        dirs[:] = sorted(directory for directory in dirs if directory not in EXCLUDED_PARTS)
        for filename in sorted(filenames):
            yield Path(parent) / filename


def _current_source_roots():
    if (ROOT / "research").is_dir() and not (ROOT / SOURCE_ROOTS[0][0]).is_dir():
        return (("research", "research", None),) + SOURCE_ROOTS[1:]
    return SOURCE_ROOTS


def research_files():
    seen = set()
    for relative, _, _ in _current_source_roots():
        for path in _source_files(ROOT / relative):
            if (
                path.suffix in {".pyc", ".pyo"}
                or path.is_symlink()
                or not path.is_file()
                or path in seen
            ):
                continue
            seen.add(path)
            yield path


def ownership(path):
    for relative, owner, group in SOURCE_ROOTS[1:]:
        if path == relative or path.startswith(relative + "/"):
            return owner, group
    parts = Path(path).parts
    group = (
        "/".join(parts[1:3])
        if len(parts) > 3 and parts[1] == "mssn_sn_tower"
        else (parts[1] if len(parts) > 2 else "research-root")
    )
    return "research", group


def family(path):
    return ownership(path)[1]


ROUTES = {
    "19L57G1_H3V7N5QF": "400_researchers/01_coverage_and_licensed_depth.ipynb",
    "papers": "400_researchers/04_source_bound_research_audit.ipynb",
    "demos": "200_intermediates/04_frustrated_spin_triangle.ipynb",
    "grammar": "000_beginners/01_marks_and_packets.ipynb",
    "how_to_play": "000_beginners/02_lifts_and_non_descent.ipynb",
    "wire": "100_novices/01_codecs_and_tamper_evidence.ipynb",
    "packets": "100_novices/01_codecs_and_tamper_evidence.ipynb",
    "normal_forms": "100_novices/01_codecs_and_tamper_evidence.ipynb",
    "code": "400_researchers/04_source_bound_research_audit.ipynb",
    "toolkits": "100_novices/02_token_frontier.ipynb",
    "runtime": "100_novices/04_cycle_repair.ipynb",
    "math": "200_intermediates/01_nilpotence_and_missing_boundaries.ipynb",
    "theorems": "200_intermediates/02_exact_lp_certificates.ipynb",
    "physics": "200_intermediates/04_frustrated_spin_triangle.ipynb",
    "adversary": "400_researchers/02_immune_boundary_and_negative_selection.ipynb",
    "geometry": "300_advanced/01_four_simplex_volume.ipynb",
    "dynamics": "300_advanced/04_transfer_trace_and_shadow.ipynb",
    "logic": "200_intermediates/03_quantifier_order.ipynb",
    "contracts": "100_novices/03_typed_agent_composition.ipynb",
    "atlas": "400_researchers/01_coverage_and_licensed_depth.ipynb",
    "monograph": "400_researchers/01_coverage_and_licensed_depth.ipynb",
    "reviews": "400_researchers/04_source_bound_research_audit.ipynb",
    "receipts": "400_researchers/04_source_bound_research_audit.ipynb",
    "images": "000_beginners/03_edges_and_parallel_cells.ipynb",
    "_theory": "400_researchers/01_coverage_and_licensed_depth.ipynb",
}


def make_inventory(manifest, *, write_files: bool = True):
    evidence = {}
    for lesson in manifest["lessons"]:
        for source in lesson["sources"]:
            # Only code actually imported or an explicitly read JSON/TSV fixture.
            if source.endswith((".py", ".json", ".tsv")):
                evidence.setdefault(source, []).append(lesson["path"])
    records = []
    for path in sorted(research_files(), key=lambda item: item.relative_to(ROOT).as_posix()):
        relative = path.relative_to(ROOT).as_posix()
        parts = set(path.relative_to(ROOT).parts)
        owner, group = ownership(relative)
        key = group.split("/")[-1]
        status = "open"
        reason = (
            "Source or binary artifact has no direct executable lesson evidence in this sequence."
        )
        if relative.startswith((HISTORICAL_LEVEL_ENGINE_ROOT, HISTORICAL_REACH_ROOT)):
            status = "historical"
            reason = "Preserved v1 bytes; navigation never promotes historical evidence to a current execution claim."
        elif relative in evidence:
            status = "lab-backed"
            reason = "Named lesson imports this module or reads this fixture; execution belongs to the separate receipt."
        elif parts & {"reviews", "receipts", "_archive", "archive", "historical", "_historical"}:
            status = "historical"
            reason = "Retained review, receipt, or archive; not replayed as current evidence."
        elif path.suffix.lower() in {
            ".md",
            ".txt",
            ".rst",
            ".pdf",
            ".tex",
            ".bib",
            ".png",
            ".jpg",
            ".jpeg",
            ".svg",
            ".html",
        }:
            status = "reading-only"
            reason = "Mapped for reading and source navigation; no per-file execution or full-content review claim."
        records.append(
            {
                "path": relative,
                "sha256": sha(path),
                "bytes": path.stat().st_size,
                "family": group,
                "owner": owner,
                "classification": status,
                "learning_route": ROUTES.get(
                    key, "400_researchers/04_source_bound_research_audit.ipynb"
                ),
                "lab_evidence": evidence.get(relative, []),
                "reason": reason,
            }
        )
    inventory = {
        "schema": "mssn.education.research-inventory.v2",
        "authority_effect": "None",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "Regular research files and explicitly listed canonical Level Engine sources, excluding generated/runtime directories; reading routes do not imply full-content review.",
        "source_roots": [
            {"path": path, "owner": owner, "family": group}
            for path, owner, group in _current_source_roots()
        ],
        "excluded_directory_names": sorted(EXCLUDED_PARTS),
        "excluded_suffixes": [".pyc", ".pyo"],
        "counts": dict(sorted(Counter(item["classification"] for item in records).items())),
        "family_counts": dict(sorted(Counter(item["family"] for item in records).items())),
        "files": records,
    }
    if write_files:
        write_json(DEST / "research_inventory.json", inventory)
        rows = [
            "# Research source crosswalk",
            "",
            "AuthorityEffect: None.",
            "",
            "Every in-scope research file and canonical Level Engine source appears in [the JSON inventory](research_inventory.json) with its byte hash,",
            "owner, classification, route, and evidence reason. The headless receipt identifies which labs ran.",
            "",
            "The inventory includes the Level Engine package runtime, orchestration, governance, historical evidence, and Lean ownership roots.",
            "",
            "Reading routes provide navigation; they do not assert every file was executed or fully reviewed.",
            "",
            "An execution receipt applies only to the notebook, manifest, and inventory hashes recorded in that receipt.",
            "",
            "| Family | Files | Route |",
            "| --- | ---: | --- |",
        ]
        for group, count in inventory["family_counts"].items():
            route = ROUTES.get(
                group.split("/")[-1], "400_researchers/04_source_bound_research_audit.ipynb"
            )
            rows.append(f"| {group} | {count} | [Lesson]({route}) |")
        rows += [
            "",
            "## Classification rules",
            "",
            "- **lab-backed:** a named lesson directly imports code or reads a fixture; check the execution receipt.",
            "- **reading-only:** a narrative, reference, or image routed to a lesson; no execution claim.",
            "- **historical:** retained review, receipt, or archive; no current replay claim.",
            "- **open:** source, notebook, fixture, or binary without a direct lab in this sequence.",
            "",
            "Generated caches, environments, compiled targets, and notebook checkpoints are excluded by explicit directory names.",
            "Refresh the inventory after research files change. Its totals describe one filesystem snapshot.",
            "",
        ]
        (DEST / "research_crosswalk.md").write_text("\n".join(rows), encoding="utf-8", newline="\n")
    return inventory


def audit_notebook(path):
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF-8 BOM is disallowed")
    nb = json.loads(raw.decode("utf-8"))
    if (nb.get("nbformat"), nb.get("nbformat_minor")) != (4, 5):
        raise ValueError("expected notebook format 4.5")
    identifiers = [cell["id"] for cell in nb["cells"]]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate cell identifier")
    code = []
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        source = "".join(cell["source"])
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and type(node.value) is float:
                raise ValueError("float literal in a lesson code cell")
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "float"
            ):
                raise ValueError("runtime float construction in a lesson code cell")
            if isinstance(node, ast.Assert) and isinstance(node.test, ast.Constant):
                raise ValueError("constant assertion cannot support lesson evidence")
        code.append(source)
    if len(code) < 3:
        raise ValueError("expected setup, worked computation, and adversarial exercise cells")
    return nb, code


def child(notebook, output):
    path = ROOT / notebook
    before = sha(path)
    nb, code = audit_notebook(path)
    declared = {
        source: sha(ROOT / source) for source in nb["metadata"]["system_integration"]["sources"]
    }
    namespace = {"__name__": "__main__"}
    for index, source in enumerate(code):
        exec(compile(source, f"{notebook}:code-cell-{index}", "exec"), namespace)
    imported = {}
    for module in list(sys.modules.values()):
        filename = getattr(module, "__file__", None)
        if not filename:
            continue
        module_path = Path(filename).resolve()
        if module_path.suffix != ".py" or not module_path.is_relative_to(ROOT):
            continue
        imported[module_path.relative_to(ROOT).as_posix()] = sha(module_path)
    if sha(path) != before or any(
        sha(ROOT / source) != digest for source, digest in declared.items()
    ):
        raise RuntimeError("notebook or declared source changed while executing")
    write_json(
        output,
        {
            "notebook": notebook,
            "notebook_sha256": before,
            "status": "PASS",
            "code_cells": len(code),
            "source_hashes": declared,
            "imported_python_source_hashes": dict(sorted(imported.items())),
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--inventory-only", action="store_true")
    args = parser.parse_args()
    if args.child:
        child(args.child, args.output)
        return 0
    manifest_path = DEST / "lesson_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    inventory = make_inventory(manifest, write_files=not args.inventory_only)
    if args.inventory_only:
        print(json.dumps({"files": len(inventory["files"]), "counts": inventory["counts"]}))
        return 0
    snapshot = {item["path"]: item["sha256"] for item in inventory["files"]}
    records = []
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    with tempfile.TemporaryDirectory(prefix="mssn-education-") as temporary:
        for index, lesson in enumerate(manifest["lessons"]):
            output = Path(temporary) / f"lesson-{index}.json"
            try:
                run = subprocess.run(
                    [
                        sys.executable,
                        "-B",
                        str(Path(__file__).resolve()),
                        "--child",
                        lesson["path"],
                        "--output",
                        str(output),
                    ],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    env=environment,
                    timeout=120,
                )
                if run.returncode != 0:
                    raise RuntimeError(run.stderr.strip() or run.stdout.strip())
                record = json.loads(output.read_text(encoding="utf-8"))
                record["stdout"] = run.stdout.strip()
                record["stderr"] = run.stderr.strip()
            except (RuntimeError, subprocess.TimeoutExpired) as error:
                record = {
                    "notebook": lesson["path"],
                    "notebook_sha256": sha(ROOT / lesson["path"]),
                    "status": "FAIL",
                    "error": str(error),
                }
            records.append(record)
            print(f"[{record['status']}] {lesson['path']}", flush=True)
            if record["status"] == "FAIL":
                print(record["error"], flush=True)
    current = {path.relative_to(ROOT).as_posix(): sha(path) for path in research_files()}
    drift = sorted(
        path for path in set(snapshot) | set(current) if snapshot.get(path) != current.get(path)
    )
    receipt = {
        "schema": "mssn.education.headless.v1",
        "authority_effect": "None",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "engine": "fresh CPython process per notebook; ordinary Python cells; no IPython kernel",
        "python_version": sys.version,
        "python_executable": sys.executable,
        "runner_sha256": sha(Path(__file__)),
        "manifest_sha256": sha(manifest_path),
        "inventory_sha256": sha(DEST / "research_inventory.json"),
        "research_snapshot_drift": drift,
        "passed": sum(record["status"] == "PASS" for record in records),
        "total": len(records),
        "status": "PASS"
        if records and not drift and all(record["status"] == "PASS" for record in records)
        else "FAIL",
        "zero_float_scope": "No float literals in notebook code; all mathematical fixtures use integer/Fraction. Imported libraries may contain other numerical paths that are not exercised.",
        "records": records,
    }
    write_json(DEST / "headless_receipt.json", receipt)
    print(
        json.dumps(
            {key: receipt[key] for key in ("status", "passed", "total", "research_snapshot_drift")}
        )
    )
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

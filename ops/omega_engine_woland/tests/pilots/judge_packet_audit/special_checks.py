"""Checks outside the per-package responder protocol.

- C001 has no judge packet; its pipeline pins are checked for digests of
  trivial inputs.
- C005 has checker functions but no judge-case files; its generated hidden
  consistency cases are driven with a constant verdict.
- C036's TASK.md publishes Gopakumar-Vafa invariants that are recomputed
  independently.
- C032's trace coefficients are checked against weight identities.
"""

from __future__ import annotations

import argparse
import json
import re
from fractions import Fraction
from pathlib import Path
from typing import Any

from omega_engine_woland.tests.pilots.judge_packet_audit import execution
from omega_engine_woland.tests.pilots.judge_packet_audit import layout
from omega_engine_woland.tests.pilots.judge_packet_audit import reference_values
from omega_engine_woland.tests.pilots.judge_packet_audit import static_analysis as sa

C032_PAIRS = [
    *[(f"SU({n})", rep) for n in range(2, 9) for rep in ("fund", "adj", "antisym", "sym")],
    *[(f"Sp({n})", rep) for n in range(1, 5) for rep in ("fund", "adj", "antisym")],
    *[(f"SO({n})", rep) for n in range(7, 15) for rep in ("vect", "adj", "spinor")],
    ("G2", "fund"),
    ("G2", "adj"),
]
C005_PREFIX = sa.CHALLENGES_PREFIX + "a_mechanism.c005_hosted_decode_controls."


def available_package_ids(repo_root: Path) -> set[str]:
    """Special-check sources that may be selected without a generic judge packet."""
    root = layout.challenges_root(repo_root)
    sources = {
        "C001": "a_mechanism/c001_attention_distractor_mask/pipeline.json",
        "C005": "a_mechanism/c005_hosted_decode_controls",
        "C032": "d_physics_mtheory/c032_*",
        "C036": "d_physics_mtheory/c036_*/participant_packet/TASK.md",
    }
    return {pid for pid, pattern in sources.items() if any(root.glob(pattern))}


def _selected(options: argparse.Namespace, package_id: str) -> bool:
    requested = getattr(options, "packages", None)
    return requested is None or package_id in {pid.upper() for pid in requested}


def _probe(
    repo_root: Path,
    pkg_dir: Path,
    prefix: str,
    module: str,
    function: str,
    calls: list[list[Any]],
    options: argparse.Namespace,
) -> execution.JobResult:
    work = Path(options.work_dir)
    job = {
        "mode": "probe",
        "sys_path": [str(repo_root)],
        "import_prefix": prefix,
        "call_timeout_s": options.call_timeout,
        "probe": {"module": module, "function": function, "calls": calls},
    }
    return execution.run_job(
        job,
        len(calls),
        cwd=pkg_dir,
        intelligence_root=work / "intelligence_root",
        scratch_dir=work / "jobs",
        wall_timeout_s=options.wall_timeout,
    )


def special_cases(repo_root: Path, options: argparse.Namespace) -> dict[str, Any]:
    out: dict[str, Any] = {}
    root = layout.challenges_root(repo_root) / "a_mechanism"
    c001 = root / "c001_attention_distractor_mask" / "pipeline.json"
    if _selected(options, "C001") and c001.is_file():
        data = json.loads(c001.read_text(encoding="utf-8"))
        out["C001"] = {
            "path": c001.relative_to(repo_root).as_posix(),
            "trivial_digest_pins": reference_values.trivial_digest_pins(data),
            "judge_packet": (c001.parent / "judge_packet").is_dir(),
        }
    requested = getattr(options, "packages", None)
    selected_ids = None if requested is None else {pid.upper() for pid in requested}
    out["theme_answer_files"] = theme_answer_files(repo_root, selected_ids)
    c005 = root / "c005_hosted_decode_controls"
    if _selected(options, "C005") and c005.is_dir():
        if not options.skip_execution:
            out["C005"] = c005_constant_verdict(repo_root, c005, options)
        elif requested is not None:
            out["C005"] = {"status": "NOT_RUN", "reason": "--skip-execution"}
    return out


def theme_answer_files(repo_root: Path, selected_ids: set[str] | None = None) -> dict[str, Any]:
    """Theme-level ``answers.jsonl`` files and whose answers they hold.

    Compares the identifiers in each theme's answers file with the theme's own
    ``judge/`` case files and with the judge cases of its packages.
    """
    out: dict[str, Any] = {}
    root = layout.challenges_root(repo_root)
    for theme in sorted(p for p in root.iterdir() if p.is_dir()):
        packages = sorted(
            p for p in theme.iterdir()
            if (p / "judge_packet").is_dir()
            and (selected_ids is None or layout.package_id(p) in selected_ids)
        )
        if selected_ids is not None and not packages:
            continue
        answers = theme / "answers.jsonl"
        if not answers.is_file():
            continue
        theme_judge_ids: set[str] = set()
        for path in sorted((theme / "judge").glob("*.json")) if (theme / "judge").is_dir() else []:
            data = json.loads(path.read_text(encoding="utf-8"))
            for item in data if isinstance(data, list) else []:
                if isinstance(item, dict) and isinstance(item.get("id"), str):
                    theme_judge_ids.add(item["id"])
        package_ids: set[str] = set()
        for pkg in packages:
            for case in layout.build_case_ids(pkg):
                package_ids.add(case)
        overlap = leakage_overlap(answers, theme_judge_ids, package_ids)
        out[theme.name] = {"path": answers.relative_to(repo_root).as_posix(), **overlap}
    return out


def leakage_overlap(path: Path, theme_judge_ids: set[str], package_ids: set[str]) -> dict[str, Any]:
    ids = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if isinstance(row, dict) and isinstance(row.get("id") or row.get("case_id"), str):
            ids.append(row.get("id") or row.get("case_id"))
    found = set(ids)
    return {
        "answer_lines": len(ids),
        "theme_judge_cases": len(theme_judge_ids),
        "answers_for_theme_judge_cases": len(found & theme_judge_ids),
        "answers_for_package_judge_cases": len(found & package_ids),
    }


def c005_constant_verdict(
    repo_root: Path, pkg_dir: Path, options: argparse.Namespace
) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    for function in ("get_hidden_base_cases", "get_relabel_controls"):
        res = _probe(repo_root, pkg_dir, C005_PREFIX, "cases", function, [[]], options)
        if res.import_error or res.records.get(0, {}).get("outcome") != "RETURNED":
            return {"error": res.import_error or f"{function} did not return"}
        cases.extend(res.records[0]["value"])
    consistency = [c for c in cases if c.get("kind") == "consistency"]
    calls = [[c["edges"], "INCONSISTENT", None] for c in consistency]
    calls += [[c["edges"], "CONSISTENT", c.get("expected_certificate")] for c in consistency]
    res = _probe(
        repo_root,
        pkg_dir,
        C005_PREFIX,
        "checkers",
        "verify_consistency_certificate",
        calls,
        options,
    )
    if res.import_error:
        return {"error": res.import_error}
    n = len(consistency)

    def valid(index: int) -> bool:
        rec = res.records.get(index, {})
        value = rec.get("value")
        return (
            rec.get("outcome") == "RETURNED" and isinstance(value, str) and "is_valid=True" in value
        )

    return {
        "consistency_cases": n,
        "expected_consistent": sum(
            1 for c in consistency if c.get("expected_verdict") == "CONSISTENT"
        ),
        "constant_inconsistent_valid_by_checker": sum(1 for i in range(n) if valid(i)),
        "constant_inconsistent_valid_on_consistent_cases": sum(
            1
            for i in range(n)
            if valid(i) and consistency[i].get("expected_verdict") == "CONSISTENT"
        ),
        "constant_inconsistent_correct_by_label": sum(
            1 for c in consistency if c.get("expected_verdict") == "INCONSISTENT"
        ),
        "reference_certificates_valid_on_consistent_cases": sum(
            1
            for i in range(n)
            if consistency[i].get("expected_verdict") == "CONSISTENT" and valid(n + i)
        ),
        "call_site_rule": "runners score a case correct when the checker returns is_valid and the verdict equals the case's expected_verdict label",
    }


def reference_value_checks(repo_root: Path, options: argparse.Namespace) -> dict[str, Any]:
    out: dict[str, Any] = {}
    theme = layout.challenges_root(repo_root) / "d_physics_mtheory"
    task = next(iter(sorted(theme.glob("c036_*/participant_packet/TASK.md"))), None)
    if _selected(options, "C036") and task is not None:
        comparison = reference_values.compare_gv_table(
            reference_values.parse_task_gv_table(task.read_text(encoding="utf-8"))
        )
        pkg_dir = task.parent.parent
        for family in comparison:
            for value in family["values"]:
                if not value["agrees"]:
                    value["package_files_with_published"] = _files_containing(
                        pkg_dir, value["published"]
                    )
                    value["package_files_with_recomputed"] = _files_containing(
                        pkg_dir, value["recomputed"]
                    )
        out["C036_task_md"] = {
            "path": task.relative_to(repo_root).as_posix(),
            "families": comparison,
            "published_values": sum(len(f["values"]) for f in comparison),
            "disagreeing_values": sum(
                1 for f in comparison for v in f["values"] if not v["agrees"]
            ),
        }
    c032 = next(iter(sorted(theme.glob("c032_*"))), None)
    if _selected(options, "C032") and c032 is not None:
        if not options.skip_execution:
            out["C032_trace_coefficients"] = c032_trace_identities(repo_root, c032, options)
        elif getattr(options, "packages", None) is not None:
            out["C032_trace_coefficients"] = {"status": "NOT_RUN", "reason": "--skip-execution"}
    return out


def _files_containing(pkg_dir: Path, digits: str) -> list[str]:
    """Package text files (outside ``participant_packet/``) containing ``digits`` as a whole number."""
    pattern = re.compile(rf"(?<![0-9]){re.escape(digits)}(?![0-9])")
    out = []
    for path in sorted(pkg_dir.rglob("*")):
        if (
            not path.is_file()
            or path.suffix not in (".py", ".json", ".md")
            or "__pycache__" in path.parts
        ):
            continue
        rel = path.relative_to(pkg_dir).as_posix()
        if rel.startswith("participant_packet/"):
            continue
        if pattern.search(path.read_text(encoding="utf-8", errors="replace")):
            out.append(rel)
    return out


def c032_trace_identities(
    repo_root: Path, pkg_dir: Path, options: argparse.Namespace
) -> dict[str, Any]:
    module = "reference_solver.sugra_6d"
    if sa.module_file(pkg_dir, module) is None:
        return {"error": f"{module} not found"}
    rel_dotted = ".".join(pkg_dir.relative_to(layout.challenges_root(repo_root)).parts)
    res = _probe(
        repo_root,
        pkg_dir,
        sa.CHALLENGES_PREFIX + rel_dotted + ".",
        module,
        "get_trace_coefficients",
        [list(p) for p in C032_PAIRS],
        options,
    )
    if res.import_error:
        return {"error": res.import_error}
    checked = []
    for index, (group, rep) in enumerate(C032_PAIRS):
        rec = res.records.get(index, {})
        if rec.get("outcome") != "RETURNED":
            continue
        triple = tuple(Fraction(v) for v in rec["value"])
        verdict = reference_values.trace_identity_check(group, rep, triple)
        if verdict["status"] == "UNSUPPORTED":
            continue
        checked.append(
            {"group": group, "rep": rep, "package_triple": [str(v) for v in triple], **verdict}
        )
    return {
        "function": f"{module}.get_trace_coefficients",
        "pairs_checked": len(checked),
        "pairs_failing": sum(1 for c in checked if c["status"] == "FAIL"),
        "failing_pairs": [f"{c['group']} {c['rep']}" for c in checked if c["status"] == "FAIL"],
        "checks": checked,
    }

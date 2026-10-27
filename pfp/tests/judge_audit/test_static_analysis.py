"""Import resolution, dependence classes, vocabulary and line similarity."""

from __future__ import annotations

from pathlib import Path

import pytest

from adversary.tests.pilots.judge_packet_audit import static_analysis as sa

REL = "z_fake.c950_static"


def _pkg(tmp_path: Path, files: dict[str, str]) -> Path:
    pkg = tmp_path / "c950_static"
    for rel, text in files.items():
        path = pkg / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    return pkg


@pytest.mark.parametrize("prefix", (
    "pfp.tests.demo_004.",
    "projects.mssn_sn_symgam.challenges.",
))
def test_relative_and_absolute_imports_resolve_to_package_relative_names(tmp_path: Path, prefix: str) -> None:
    pkg = _pkg(
        tmp_path,
        {
            "reference_solver/solver.py": "def solve(c):\n    return c\n",
            "reference_solver/__init__.py": "",
            "judge_packet/checkers/a.py": (
                "from ...reference_solver.solver import solve as ref_solve\n"
                "from .b import helper\n"
                f"from {prefix}z_fake.c950_static.reference_solver import solver\n"
            ),
            "judge_packet/checkers/b.py": "def helper():\n    return 1\n",
        },
    )
    records = sa.imports_of(pkg / "judge_packet/checkers/a.py", pkg, REL)
    got = [(r.module, r.name, r.internal) for r in records]
    assert got == [
        ("reference_solver.solver", "solve", True),
        ("judge_packet.checkers.b", "helper", True),
        ("reference_solver", "solver", True),
    ]
    assert sa.imported_target(records[2], pkg) == ("reference_solver.solver", None)


def test_dependence_classes(tmp_path: Path) -> None:
    pkg = _pkg(
        tmp_path,
        {
            "reference_solver/__init__.py": "",
            "reference_solver/solver.py": "def solve(c):\n    return c\n\ndef parse(x):\n    return x\n",
            "judge_packet/key.py": "from ..reference_solver.solver import solve as ref_solve\n\ndef check(c, a):\n    return a == ref_solve(c)\n",
            "judge_packet/shares.py": "from ..reference_solver.solver import parse\n\ndef check(c, a):\n    return parse(a) is not None\n",
            "judge_packet/other.py": "from .shares import check as other\n\ndef check(c, a):\n    return other(c, a)\n",
            "judge_packet/helper.py": "from ..reference_solver.solver import solve\n",
            "judge_packet/via.py": "from .helper import solve\n\ndef check(c, a):\n    return True\n",
            "judge_packet/clean.py": "def check(c, a):\n    return isinstance(a, dict)\n",
        },
    )
    assert (
        sa.checker_dependence(pkg, REL, "judge_packet.key", ["judge_packet.clean"])["class"]
        == "ANSWER_KEY"
    )
    assert (
        sa.checker_dependence(pkg, REL, "judge_packet.shares", ["judge_packet.clean"])["class"]
        == "SHARES_REFERENCE_CODE"
    )
    assert (
        sa.checker_dependence(pkg, REL, "judge_packet.other", ["judge_packet.shares"])["class"]
        == "IMPORTS_OTHER_CHECKER"
    )
    via = sa.checker_dependence(pkg, REL, "judge_packet.via", ["judge_packet.clean"])
    assert via["class"] == "SHARES_REFERENCE_CODE" and via[
        "reference_reached_via_helper_modules"
    ] == ["judge_packet.helper"]
    assert (
        sa.checker_dependence(pkg, REL, "judge_packet.clean", ["judge_packet.key"])["class"]
        == "NO_IMPORT_DEPENDENCE"
    )


def test_vocabulary_reads_statuses_codes_keys_and_enums(tmp_path: Path) -> None:
    pkg = _pkg(
        tmp_path,
        {
            "judge_packet/checker.py": (
                'CLOSED_REFUSAL_CODES = frozenset({"BUDGET", "MALFORMED"})\n'
                "def check(case, answer):\n"
                '    status = answer.get("status")\n'
                '    if status not in {"SOLVED", "UNKNOWN", "OUT_OF_SCOPE"}:\n'
                "        return False\n"
                '    code = answer.get("refusal_code")\n'
                '    if code == "BOUND_NOT_MET":\n'
                "        return True\n"
                "    return False\n"
            ),
        },
    )
    vocab = sa.vocabulary([pkg / "judge_packet/checker.py"])
    assert vocab["statuses"] == ["OUT_OF_SCOPE", "SOLVED", "UNKNOWN"]
    assert vocab["refusal_statuses"] == ["OUT_OF_SCOPE", "UNKNOWN"]
    assert vocab["codes"] == ["BOUND_NOT_MET", "BUDGET", "MALFORMED"]
    assert vocab["code_keys"] == ["refusal_code"]


def test_shared_line_fraction_counts_multiset_matches() -> None:
    a = "x = compute_the_value(1)\nx = compute_the_value(1)\n# a comment line that is long\nimport something_long_enough\ny = another_long_statement()\n"
    b = "x = compute_the_value(1)\nz = something_else_entirely()\n"
    assert sa.nontrivial_lines(a) == [
        "x = compute_the_value(1)",
        "x = compute_the_value(1)",
        "y = another_long_statement()",
    ]
    assert sa.shared_line_fraction(a, b) == (1, 3)

"""Tests for type_register/type_register.py: the register validates and the census is clean.

AuthorityEffect: None.

The census fails when a module that defines a Pydantic model or Enum is missing
from the register, when a public type name gains a second definition, or when a
derived-type row names a test that does not exist. Each failure kind has a
negative control below.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pfp_types_test_support import load_module, pfp_root  # noqa: E402

from pfp.infrastructure import type_register as tr
ROOT = Path(__file__).resolve().parents[2]
REGISTER = ROOT / "type_register/type_register.yaml"


@pytest.mark.parametrize("path", ["../escape.py", "..\\escape.py", "C:escape.py", "C:/escape.py"])
def test_register_paths_cannot_escape_the_current_owner(path):
    with pytest.raises(ValueError, match="REGISTER_PATH_OUTSIDE_PACKAGE"):
        tr.resolve(ROOT, path)
    with pytest.raises(ValueError, match="REGISTER_PATH_OUTSIDE_PACKAGE"):
        tr.glob(ROOT, path)


@pytest.fixture(scope="module")
def register():
    return tr.load_register(REGISTER)


def _row(**overrides):
    base = {"path": "x/a.py", "world": "colocated", "source": "pydantic", "status": "canonical"}
    return tr.ModuleRow.model_validate({**base, **overrides}, strict=False)


def test_register_validates(register) -> None:
    assert register.authority_effect == "None"
    assert {m.path for m in register.modules} >= {
        "domain/type_register/type_register.py",
        "domain/types/pilot_spec.py",
        "domain/types/pilot_response.py",
    }


def test_census_is_clean(register) -> None:
    assert tr.census_problems(ROOT, register) == []


def test_readme_links_the_register() -> None:
    readme = ROOT / "type_register/README.md"
    text = readme.read_text(encoding="utf-8")
    assert "(../infrastructure/type_register.py)" in text and "(type_register.yaml)" in text


# --- negative controls: the census --------------------------------------------


def test_dropping_a_row_is_reported(register) -> None:
    kept = tuple(m for m in register.modules if m.path != "domain/types/pilot_spec.py")
    problems = tr.census_problems(ROOT, register.model_copy(update={"modules": kept}))
    assert any(
        p.startswith("UNREGISTERED_TYPE_MODULE domain/types/pilot_spec.py") for p in problems
    )


def test_undeclared_collision_and_stale_row_are_reported(register) -> None:
    rest = tuple(c for c in register.name_collisions if c.name != "AuthorityEffect")
    fake = tr.NameCollision(name="NoSuchType", modules=("a.py", "b.py"), disposition="x")
    problems = tr.census_problems(
        ROOT, register.model_copy(update={"name_collisions": (fake, *rest)})
    )
    assert any(p.startswith("NEW_NAME_COLLISION AuthorityEffect") for p in problems)
    assert any(p.startswith("STALE_COLLISION_ROW NoSuchType") for p in problems)


def test_wrong_yaml_role_is_reported(register) -> None:
    target = "domain/types/cycle_balance.py"
    rows = tuple(
        m.model_copy(update={"yaml": (tr.YamlRef(path=m.yaml[0].path, role=tr.YamlRole.DATA),)})
        if m.path == target
        else m
        for m in register.modules
    )
    problems = tr.census_problems(ROOT, register.model_copy(update={"modules": rows}))
    assert any(p.startswith(f"YAML_ROLE_WRONG {target}") for p in problems)


def test_bad_type_ref_and_missing_check_are_reported(register) -> None:
    bad = tr.DerivedType(
        type="domain/types/pilot_spec.py::NoSuchModel",
        of=("domain/types/pilot_spec.py::PilotSpec",),
        kind="projection",
        checked_by="tests/types/test_pilot_types.py::test_no_such_function",
    )
    problems = tr.census_problems(
        ROOT, register.model_copy(update={"derived": (*register.derived, bad)})
    )
    assert "NOT_A_TYPE domain/types/pilot_spec.py::NoSuchModel" in problems
    assert (
        "DERIVED_CHECK_MISSING tests/types/test_pilot_types.py::test_no_such_function" in problems
    )


def test_scan_follows_inheritance_and_skips_tests_demos_and_papers(tmp_path: Path) -> None:
    files = {
        "a/base.py": "from pydantic import BaseModel\nclass Base(BaseModel):\n    x: int\n",
        "b/child.py": "from a.base import Base\nclass Child(Base):\n    y: int\nclass Plain:\n    pass\n",
        "c/kinds.py": "from enum import Enum\nclass Kind(str, Enum):\n    A = 'a'\n",
        "a/tests/test_base.py": "from pydantic import BaseModel\nclass T(BaseModel):\n    pass\n",
        "demos/d.py": "from pydantic import BaseModel\nclass D(BaseModel):\n    pass\n",
        "papers/001_p/code/m.py": "from enum import Enum\nclass MoveType(Enum):\n    A = 1\n",
        "papers/002_q/code/m.py": "from enum import Enum\nclass MoveType(Enum):\n    A = 1\n",
    }
    for rel, body in files.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(body, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    found = tr.scan_types(tmp_path, tr.tracked_python_files(tmp_path))
    assert found == {"a/base.py": ["Base"], "b/child.py": ["Child"], "c/kinds.py": ["Kind"]}


def test_the_papers_exclusion_is_top_level_only_and_does_not_touch_nearby_names() -> None:
    assert not tr.in_census("papers/001_p/code/m.py")
    assert not tr.in_census("demos/d.py")
    assert not tr.in_census("pilots/pilot_0000026/run.py")
    assert tr.in_census("python/domain/m.py")
    assert tr.in_census("python/papers/m.py")
    assert tr.in_census("domain/protocol/packet.py")


# --- negative controls: the row validators ------------------------------------


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"world": "generated"}, "GENERATED_IFF_YAML_SOURCE"),
        ({"source": "both_unchecked"}, "YAML_SOURCE_NOT_NAMED"),
        (
            {"yaml": [{"path": "x/a.yaml", "role": "json_schema"}]},
            "PYDANTIC_SOURCE_LISTS_A_HAND_WRITTEN_SCHEMA",
        ),
        (
            {"source": "both_parity_tested", "yaml": [{"path": "x/a.yaml", "role": "json_schema"}]},
            "PARITY_CLAIM_WITHOUT_TEST",
        ),
        ({"status": "review"}, "REVIEW_ROW_NEEDS_A_NOTE"),
    ],
)
def test_row_validator_refuses(overrides: dict, code: str) -> None:
    with pytest.raises(ValidationError, match=code):
        _row(**overrides)


def test_malformed_type_ref_is_refused() -> None:
    with pytest.raises(ValidationError, match="should match pattern"):
        tr.OverlapGroup(
            fact="x", types=("python/domain/pilot.py:PilotBudget", "a.py::B"), disposition="d"
        )


def test_unsorted_rows_are_refused(register) -> None:
    raw = register.model_dump(mode="json", by_alias=True)
    raw["modules"] = list(reversed(raw["modules"]))
    with pytest.raises(ValidationError, match="MODULE_ROWS_MUST_BE_UNIQUE_AND_SORTED"):
        tr.TypeRegister.model_validate(raw, strict=False)

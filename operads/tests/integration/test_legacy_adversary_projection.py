"""The retired V2 Adversary projection and operad-term compiler must refuse, typed.

Both depended on the retired Python higher-operad kernel. They now return
RUNTIME_RETIRED without reading the estate, so the former catalog-digest pin
over `.agents/` no longer applies.

AuthorityEffect: None.
"""

from pathlib import Path

import pytest

from operations.domain.rop.result import Err, Refusal
from operads.infrastructure.legacy.use_cases import (
    CompileOperadTermsUseCase,
)
from operads.infrastructure.legacy.use_cases.adversary_projection import (
    compile_adversary_projection,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def _assert_runtime_retired(result, locus_suffix: str) -> None:
    assert isinstance(result, Err)
    assert result.is_err and not result.is_ok
    refusal = result.unwrap_err()
    assert type(refusal) is Refusal
    assert refusal.code == "RUNTIME_RETIRED"
    assert refusal.locus.endswith(locus_suffix)
    assert "engine/crates_rs/core_operad_theory" in refusal.message
    with pytest.raises(ValueError):
        result.unwrap()


def test_adversary_projection_refuses_without_reading_the_estate(tmp_path: Path) -> None:
    result = compile_adversary_projection(
        estate_root=tmp_path / "absent-estate",
        manifest_path=tmp_path / "absent-manifest.json",
    )
    _assert_runtime_retired(result, "legacy.adversary_projection")


def test_adversary_projection_refuses_for_the_real_estate_too() -> None:
    result = compile_adversary_projection(
        estate_root=REPO_ROOT / ".agents",
        manifest_path=(
            REPO_ROOT
            / "operads"
            / "manifests"
            / "adversary_engineering_v1.json"
        ),
    )
    _assert_runtime_retired(result, "legacy.adversary_projection")


def test_operad_term_compiler_refuses_every_entry_point() -> None:
    compiler = CompileOperadTermsUseCase()
    _assert_runtime_retired(compiler.compile_skill(object()), "legacy.compile_operad_terms")
    _assert_runtime_retired(compiler.compile_all({}), "legacy.compile_operad_terms")

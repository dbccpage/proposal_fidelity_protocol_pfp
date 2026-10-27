"""Phi1 comes from the admitted cochain residual, not an AST defect count.

AuthorityEffect: None.
Zero-Float Law: Uses exact rational arithmetic.
"""

from __future__ import annotations

import sys
import types
from fractions import Fraction

import pytest

from pciv.profile.cochain_profile import (
    CHECKER_NAME,
    PROMPT_COCHAIN_COMPLEX_PROFILE,
    ComplexConditionFailed,
    HigherDifferentialUnavailable,
    verify_cochain_complex,
)
from pciv.use_cases.lamarckian_loop import (
    LamarckianLoopService,
    UnmeasuredCurvatureRefusal,
)

_BIGON_D0 = [[1], [1]]
_BIGON_D1 = [[1, -1]]
_THREE_DEFECTS = (
    "defect:circular_import:a<->b",
    "defect:clean_arch_violation:a->b",
    "defect:syntax:a",
)


def _independent_l1(rows: tuple[tuple[Fraction, ...], ...]) -> Fraction:
    total = Fraction(0, 1)
    for row in rows:
        for entry in row:
            total += abs(entry)
    return total


def test_admitted_complex_phi1_is_the_verifier_residual() -> None:
    admitted = PROMPT_COCHAIN_COMPLEX_PROFILE.admit(_BIGON_D0, _BIGON_D1)
    direct = verify_cochain_complex(_BIGON_D0, _BIGON_D1)
    residual_rows = admitted.residual.rows_tuple()

    assert admitted.phi1 == direct.phi1
    assert admitted.phi1 == _independent_l1(residual_rows)
    assert residual_rows == ((Fraction(0, 1),),)
    assert admitted.phi1 == Fraction(0, 1)
    assert admitted.phi1 != Fraction(len(_THREE_DEFECTS), 1)

    rational = PROMPT_COCHAIN_COMPLEX_PROFILE.admit(
        [[1, 0], [0, 1], [-1, -1]],
        [[Fraction(1, 2), Fraction(1, 2), Fraction(1, 2)]],
    )
    assert rational.residual.rows_tuple() == ((Fraction(0, 1), Fraction(0, 1)),)
    assert rational.phi1 == rational.residual.l1_norm()


def test_obstruction_count_three_is_not_stored_as_phi1() -> None:
    """The old caller stored obstruction_count 3 as phi1 3/1. It must not."""
    installed = _install_ast_stubs(defect_descriptions=_THREE_DEFECTS)
    try:
        with pytest.raises(UnmeasuredCurvatureRefusal) as caught:
            LamarckianLoopService.extract_cochain_from_ast(
                {"pkg/domain/a.py": "x = 1\n"}
            )
    finally:
        _remove_stubs(installed)

    refusal = caught.value
    assert refusal.code == "UNMEASURED_CURVATURE"
    assert refusal.authority_effect == "None"
    assert len(refusal.obstructions) == 3
    assert refusal.obstructions == _THREE_DEFECTS
    assert not hasattr(refusal, "admitted_phi1")
    assert refusal.published is False
    assert refusal.gamma2 is None
    assert refusal.xi is None
    assert refusal.witness_sha256


def test_unmeasured_curvature_does_not_publish_zero_gamma2_xi() -> None:
    """Constant gamma2 = xi = 0 beside an admitted phi1 is not a residual."""
    installed = _install_ast_stubs(defect_descriptions=_THREE_DEFECTS)
    try:
        with pytest.raises(UnmeasuredCurvatureRefusal) as caught:
            LamarckianLoopService.extract_cochain_from_ast(
                {"pkg/domain/a.py": "x = 1\n"}
            )
    finally:
        _remove_stubs(installed)

    refusal = caught.value
    assert not hasattr(refusal, "admitted_phi1")
    assert refusal.gamma2 is None
    assert refusal.xi is None
    assert refusal.published is False
    assert getattr(refusal, "residual", None) is None
    assert "CochainResidualV1" in str(refusal)


def test_profile_checker_name_is_verify_cochain_complex() -> None:
    assert PROMPT_COCHAIN_COMPLEX_PROFILE.name == "prompt_cochain_complex_v1"
    assert PROMPT_COCHAIN_COMPLEX_PROFILE.checker_name == CHECKER_NAME
    assert PROMPT_COCHAIN_COMPLEX_PROFILE.checker_name == "verify_cochain_complex"
    admitted = PROMPT_COCHAIN_COMPLEX_PROFILE.admit(_BIGON_D0, _BIGON_D1)
    assert admitted.phi1 == verify_cochain_complex(_BIGON_D0, _BIGON_D1).phi1


def test_verifier_refuses_missing_inexact_or_broken_complexes() -> None:
    with pytest.raises(HigherDifferentialUnavailable):
        verify_cochain_complex(_BIGON_D0, None)
    with pytest.raises(ComplexConditionFailed):
        verify_cochain_complex([[1.0], [1.0]], _BIGON_D1)
    with pytest.raises(ComplexConditionFailed):
        PROMPT_COCHAIN_COMPLEX_PROFILE.admit([[1], [1]], [[1, 1]])


def _install_ast_stubs(*, defect_descriptions: tuple[str, ...]) -> list[str]:
    """Stub the PFP AST bridge so the caller can be run without those modules."""
    installed: list[str] = []

    def package(name: str) -> types.ModuleType:
        existing = sys.modules.get(name)
        if existing is None:
            module = types.ModuleType(name)
            module.__path__ = []
            module.__package__ = name
            sys.modules[name] = module
            installed.append(name)
            return module
        return existing

    def module(name: str) -> types.ModuleType:
        created = types.ModuleType(name)
        created.__package__ = name.rpartition(".")[0]
        sys.modules[name] = created
        installed.append(name)
        return created

    package("pfp")
    package("pfp.domain")
    package("pfp.domain.ast_cochain")

    parser_mod = module("pfp.domain.ast_cochain.ast_source_parser")

    class PythonSourceParser:
        def parse(self, sources: dict[str, str]) -> dict[str, str]:
            return dict(sources)

    parser_mod.PythonSourceParser = PythonSourceParser

    builder_mod = module("pfp.domain.ast_cochain.ast_dependency_complex")
    builder_mod.DEFAULT_LAYER_RANKS = {"domain": 1}

    class DependencyComplexBuilder:
        def __init__(self, layer_ranks: dict[str, int]) -> None:
            self.layer_ranks = layer_ranks

        def build(self, parsed: dict[str, str]) -> types.SimpleNamespace:
            return types.SimpleNamespace(
                d0=[[1.0], [1.0]],
                d1=[[1.0, -1.0]],
                defect_descriptions=defect_descriptions,
                parsed=parsed,
            )

    builder_mod.DependencyComplexBuilder = DependencyComplexBuilder

    boundary = module("pfp.functional_boundary")

    class RustFunctionalRequired(Exception):
        pass

    boundary.RustFunctionalRequired = RustFunctionalRequired

    metrics = module("pfp.domain.ast_cochain.ast_metrics_evaluator")

    class ASTMetricsEvaluator:
        def evaluate(self, complex_: object) -> object:
            raise RustFunctionalRequired("functional kernel is not bound")

    metrics.ASTMetricsEvaluator = ASTMetricsEvaluator
    return installed


def _remove_stubs(installed: list[str]) -> None:
    for name in reversed(installed):
        sys.modules.pop(name, None)

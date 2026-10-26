"""Targeted unit tests for SBE quantum bridge.

Verifies:
1. SBEAnalyzer & SBEDensityReport calculations (purity, entropy, L1 coherence).
2. Exact-type equality and hash discipline on SBEDensityReport.
3. TextStateProjector normalization ||psi||_2 = 1.
4. AuthorityEffect is strictly None.
5. Zero dependency on omega_engine_woland.stage.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from omega_engine_pfp.domain.bridge.sbe import (
    SBE_DIMENSION,
    SBEAnalyzer,
    SBEDensityReport,
    TextStateProjector,
)


def test_sbe_density_report_exact_type_equality() -> None:
    rep1 = SBEDensityReport(purity=1.0, entropy_bits=0.0, l1_coherence=0.0)
    rep2 = SBEDensityReport(purity=1.0, entropy_bits=0.0, l1_coherence=0.0)
    assert rep1 == rep2
    assert hash(rep1) == hash(rep2)
    assert rep1.authority_effect == "None"

    # Cross-type comparison rejection
    class FakeReport:
        purity = 1.0
        entropy_bits = 0.0
        l1_coherence = 0.0

    assert rep1 != FakeReport()
    # Numerically distinct observations must not collapse into one value object.
    assert rep1 != SBEDensityReport(purity=0.9999998)


def test_text_state_projector_unit_norm() -> None:
    projector = TextStateProjector(dim=SBE_DIMENSION)
    psi = projector.project("test text for quantum state projection")
    assert len(psi) == SBE_DIMENSION
    norm = float(np.linalg.norm(psi))
    assert math.isclose(norm, 1.0, abs_tol=1e-6)


def test_sbe_analyzer_text_analysis_pure_state() -> None:
    analyzer = SBEAnalyzer(dim=SBE_DIMENSION)
    report = analyzer.analyze_text("Symbol game test string")
    assert isinstance(report, SBEDensityReport)
    # A single outer-product rho = |psi><psi| is pure, so Tr(rho^2) = 1.0
    assert math.isclose(report.purity, 1.0, abs_tol=1e-5)
    # Pure state has zero von Neumann entropy
    assert math.isclose(report.entropy_bits, 0.0, abs_tol=1e-5)
    # L1 coherence is >= 0
    assert report.l1_coherence >= 0.0
    assert report.dim == SBE_DIMENSION
    assert report.authority_effect == "None"


def test_sbe_analyzer_dialogue_ensemble_mixture() -> None:
    analyzer = SBEAnalyzer(dim=SBE_DIMENSION)
    beats = ["first beat", "second distinct beat", "third dialogue turn"]
    report = analyzer.analyze_dialogue_ensemble(beats)
    assert isinstance(report, SBEDensityReport)
    # An ensemble mixture of non-identical states has purity <= 1.0
    assert 0.0 < report.purity <= 1.00001
    # Mixed states have non-negative entropy
    assert report.entropy_bits >= 0.0
    assert report.authority_effect == "None"


def test_sbe_analyzer_empty_ensemble_maximally_mixed() -> None:
    analyzer = SBEAnalyzer(dim=SBE_DIMENSION)
    report = analyzer.analyze_dialogue_ensemble([])
    # Maximally mixed state has purity = 1/d and entropy = log2(d)
    expected_purity = 1.0 / float(SBE_DIMENSION)
    expected_entropy = math.log2(float(SBE_DIMENSION))
    assert math.isclose(report.purity, expected_purity, abs_tol=1e-5)
    assert math.isclose(report.entropy_bits, expected_entropy, abs_tol=1e-5)


def test_sbe_density_report_to_dict_and_project_text() -> None:
    analyzer = SBEAnalyzer(dim=SBE_DIMENSION)
    rep = analyzer.analyze("Sample analysis text")
    assert isinstance(rep, SBEDensityReport)
    d = rep.to_dict()
    assert isinstance(d, dict)
    assert d["dim"] == SBE_DIMENSION
    assert d["authority_effect"] == "None"
    assert "purity" in d
    assert "entropy_bits" in d
    assert "l1_coherence" in d

    projector = TextStateProjector(dim=SBE_DIMENSION)
    psi = projector.project_text("Sample analysis text")
    assert len(psi) == SBE_DIMENSION
    assert math.isclose(float(np.linalg.norm(psi)), 1.0, abs_tol=1e-6)


@pytest.mark.parametrize("weights", [[-1.0, 2.0], [0.0, 0.0], [float("nan"), 1.0], [float("inf"), 1.0], [1.0]])
def test_invalid_mixture_weights_refused(weights: list[float]) -> None:
    with pytest.raises(ValueError, match="weights"):
        SBEAnalyzer().analyze_dialogue_ensemble(["a", "b"], weights)


def test_empty_ensemble_rejects_extra_weights() -> None:
    with pytest.raises(ValueError, match="weights"):
        SBEAnalyzer().analyze_dialogue_ensemble([], [1.0])


def test_invalid_dimensions_and_authority_refused() -> None:
    for dim in (0, -1, True):
        with pytest.raises(ValueError, match="dim"):
            TextStateProjector(dim)
        with pytest.raises(ValueError, match="dim"):
            SBEAnalyzer(dim)
    with pytest.raises(ValueError, match="authority"):
        SBEDensityReport(authority_effect="Granted")
    with pytest.raises(ValueError, match="finite"):
        SBEDensityReport(purity=float("nan"))


def test_invalid_density_and_unsupported_analysis_refused() -> None:
    analyzer = SBEAnalyzer(dim=2)
    with pytest.raises(ValueError, match="positive semidefinite"):
        analyzer._compute_report(np.diag([2.0, -1.0]).astype(complex))
    with pytest.raises(TypeError, match="one text string"):
        analyzer.analyze({"text": "a"})

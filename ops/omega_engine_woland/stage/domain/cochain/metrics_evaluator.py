"""metrics_evaluator.py
====================

AST Cochain Complex evaluator backed by domain FunctionalEvaluatorPort or pure domain arithmetic.

Evaluates discrete 1-skeleton dependency cochains against the canonical obstruction triad
(Phi_1, Gamma_2, Xi) and trichotomy diagnostic classes.

Clean Architecture: Pure domain implementation with zero outer-layer or foreign package imports.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from fractions import Fraction
from typing import Any, Dict, Optional, Sequence

from ..ports import (
    FunctionalEvaluatorPort,
    get_functional_evaluator_port,
)
from .cycle_analysis import CycleAnalysisLimits, _validated_limits
from .dependency_complex import ASTDependencyComplex
from .models import ASTEvaluationReport


def _pure_python_evaluate_functional(
    d0: Sequence[Sequence[Fraction]],
    d1: Sequence[Sequence[Fraction]],
    residual: Sequence[Fraction],
) -> tuple[Fraction, Fraction, str, str]:
    """Pure domain fallback calculating Phi_1, Gamma_2, and diagnostic class.

    Guarantees zero outer-layer imports when no native evaluator port is registered.
    """
    phi1 = sum((abs(r) for r in residual), Fraction(0))

    # Gamma_2 = ||d1 * r||_1
    gamma2 = Fraction(0)
    for row in d1:
        cycle_sum = Fraction(0)
        for coeff, r in zip(row, residual):
            cycle_sum += coeff * r
        gamma2 += abs(cycle_sum)

    if gamma2 > 0:
        diagnostic_class = "ActiveClosureFailure"
    elif phi1 > 0:
        diagnostic_class = "ClosedResidual"
    else:
        diagnostic_class = "ExactRepair"

    raw = f"{d0}:{d1}:{residual}".encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    return phi1, gamma2, diagnostic_class, digest


class ASTMetricsEvaluator:
    """Evaluates AST dependency complexes via domain port or pure domain arithmetic."""

    def __init__(
        self,
        layer_rules: Optional[Dict[str, int]] = None,
        evaluator_port: Optional[FunctionalEvaluatorPort] = None,
        host: Optional[Any] = None,
        *,
        limits: CycleAnalysisLimits | None = None,
    ):
        self.complex = ASTDependencyComplex(layer_rules=layer_rules, limits=_validated_limits(limits))
        self._evaluator_port = evaluator_port
        self._host = host

    def evaluate_sources(self, sources: Dict[str, str]) -> ASTEvaluationReport:
        """Evaluates sources using registered domain port or pure domain fallback."""
        self.complex.build_complex(sources)
        d0, d1, residual = self._prepare_functional_inputs()
        phi, gamma, native_class, digest = self._evaluate_functional_inputs(d0, d1, residual)
        return self._build_report(phi, gamma, native_class, digest)

    def _prepare_functional_inputs(
        self,
    ) -> tuple[list[list[Fraction]], list[list[Fraction]], list[Fraction]]:
        nodes = list(self.complex.graph.nodes())
        edges = list(self.complex.graph.edges())
        node_idx = {node: index for index, node in enumerate(nodes)}
        c0, c1 = len(nodes), len(edges)
        self.complex.limits.admit_matrices(c0, c1, len(self.complex.cycles))
        defect_weights = self._edge_defect_weights()
        if c1 == 0:
            return [], [], []

        d0 = [[Fraction(0)] * c0 for _ in range(c1)]
        residual = [Fraction(0)] * c1
        edge_idx: dict[tuple[str, str], int] = {}
        for index, (source, target) in enumerate(edges):
            edge_idx[(source, target)] = index
            d0[index][node_idx[source]] = Fraction(-1)
            d0[index][node_idx[target]] = Fraction(1)
            if (source, target) in defect_weights:
                residual[index] = defect_weights[(source, target)]

        d1 = []
        for cycle in self.complex.cycles:
            if len(cycle) >= 2:
                d1.append(self._cycle_row(cycle, edge_idx, c1))
        return d0, d1, residual

    def _edge_defect_weights(self) -> dict[tuple[str, str], Fraction]:
        weights: dict[tuple[str, str], Fraction] = {}
        for defect in self.complex.defects:
            if defect.target_module:
                edge = (defect.source_module, defect.target_module)
                weights[edge] = weights.get(edge, Fraction(0)) + Fraction(int(round(defect.weight)))
        return weights

    @staticmethod
    def _cycle_row(
        cycle: Sequence[str], edge_idx: dict[tuple[str, str], int], edge_count: int
    ) -> list[Fraction]:
        row = [Fraction(0)] * edge_count
        for index, source in enumerate(cycle):
            edge = (source, cycle[(index + 1) % len(cycle)])
            if edge in edge_idx:
                row[edge_idx[edge]] += Fraction(1)
        return row

    def _evaluate_functional_inputs(
        self,
        d0: Sequence[Sequence[Fraction]],
        d1: Sequence[Sequence[Fraction]],
        residual: Sequence[Fraction],
    ) -> tuple[Fraction, Fraction, str, str]:
        evaluator = self._evaluator_port or get_functional_evaluator_port()
        if evaluator is not None:
            receipt = evaluator.evaluate_functional(d0, d1, residual)
            return receipt.phi1, receipt.gamma2, receipt.diagnostic_class, receipt.input_digest
        if self._host is not None and hasattr(self._host, "invoke"):
            outcome = self._host.invoke("functional_evaluate", self._functional_payload(d0, d1, residual))
            if hasattr(outcome, "is_ok") and outcome.is_ok:
                record = outcome.unwrap()
                if record.get("success") and record.get("result"):
                    result = record["result"]
                    return (
                        Fraction(result.get("phi1", "0")),
                        Fraction(result.get("gamma2", "0")),
                        result.get("diagnostic_class", "ExactRepair"),
                        result.get("input_digest", ""),
                    )
        return _pure_python_evaluate_functional(d0, d1, residual)

    @staticmethod
    def _to_exact_wire(value: Any) -> str:
        if isinstance(value, int):
            return str(value)
        if isinstance(value, Fraction):
            return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"
        return str(value)

    def _functional_payload(
        self,
        d0: Sequence[Sequence[Fraction]],
        d1: Sequence[Sequence[Fraction]],
        residual: Sequence[Fraction],
    ) -> dict[str, Any]:
        return {
            "d0": {"rows": [[self._to_exact_wire(value) for value in row] for row in d0]},
            "d1": {"rows": [[self._to_exact_wire(value) for value in row] for row in d1]},
            "residual": {"entries": [self._to_exact_wire(value) for value in residual]},
            "authority_effect": "None",
        }

    def _build_report(
        self, phi: Fraction, gamma: Fraction, native_class: str, digest: str
    ) -> ASTEvaluationReport:
        if native_class == "ActiveClosureFailure":
            diagnostic_class = "TOPOLOGICAL_OBSTRUCTION"
        elif native_class == "ClosedResidual":
            diagnostic_class = "COBOUNDARY_EXACT"
        else:
            diagnostic_class = "ZERO_RESIDUAL"

        active_obstruction_count = len(self.complex.defects)
        active_obstructions = [
            f"{defect.defect_type}:{defect.source_module}->{defect.target_module or 'None'}"
            for defect in self.complex.defects
        ]
        xi_val = float(active_obstruction_count)
        phi_1_val = float(phi)
        gamma_2_val = float(gamma)
        is_exact = bool(phi == 0 and gamma == 0 and active_obstruction_count == 0)
        is_closed = bool(gamma == 0)
        report = ASTEvaluationReport(
            phi_1=phi_1_val,
            gamma_2=gamma_2_val,
            active_obstruction_count=active_obstruction_count,
            active_obstructions=active_obstructions,
            is_exact=is_exact,
            is_closed=is_closed,
            chain_condition_holds=True,
            complex_stats=self.complex.get_stats(),
            evidence_sha256=digest,
            defects=list(self.complex.defects),
            authority_effect="None",
        )
        report.xi = xi_val
        report.diagnostic_class = diagnostic_class
        report.native_diagnostic_class = native_class
        return report

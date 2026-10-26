"""Unit, mutation-style, and boundary tests for finite-gauge ports."""

from __future__ import annotations

from dataclasses import replace

from omega_engine_pfp.domain.finite_gauge import (
    CandidateCheck,
    CheckerIdentity,
    GaugeFrontier,
    GaugeRefusal,
    GaugeRefusalCode,
    GraphSpec,
    RunConfig,
    SearchReceipt,
)
from omega_engine_pfp.domain.kernel.result import Result
from omega_engine_pfp.infrastructure.adapters.finite_gauge.paper002_checker import (
    Paper002FiniteGaugeChecker,
)
from omega_engine_pfp.use_cases.finite_gauge_workbench import (
    FiniteGaugeRun,
    GaugeRunRuntime,
)


class FakeChecker:
    """Small exact fake proving the use case has no concrete adapter dependency."""

    def __init__(self, mutate_receipt: bool = False) -> None:
        self.mutate_receipt = mutate_receipt
        self.verified_bits: list[tuple[int, ...]] = []

    def identity(self) -> Result[CheckerIdentity, GaugeRefusal]:
        return Result.ok(CheckerIdentity("fake-v1", "a" * 64, "b" * 64))

    def graph_digest(self, graph: GraphSpec) -> Result[str, GaugeRefusal]:
        return Result.ok("c" * 64)

    def verify_candidate(
        self, graph: GraphSpec, bits: tuple[int, ...]
    ) -> Result[bool, GaugeRefusal]:
        self.verified_bits.append(bits)
        alpha = dict(zip(graph.vertices, bits))
        valid = all(alpha[edge.source] ^ alpha[edge.target] == edge.odd for edge in graph.edges)
        return Result.ok(valid)

    def search_and_replay(
        self, graph: GraphSpec, node_budget: int
    ) -> Result[SearchReceipt, GaugeRefusal]:
        checks = tuple(
            CandidateCheck(index, bits, self.verify_candidate(graph, bits).unwrap())
            for index in range(min(1 << len(graph.vertices), node_budget))
            for bits in (self._bits(index, len(graph.vertices)),)
        )
        if self.mutate_receipt:
            checks = (replace(checks[0], valid=not checks[0].valid), *checks[1:])
        return Result.ok(
            SearchReceipt(
                status="GAUGE_VERIFIED",
                receipt_sha256="d" * 64,
                presentation_digest="e" * 64,
                graph_digest="c" * 64,
                node_budget=node_budget,
                checks=checks,
                frontier=GaugeFrontier(len(checks), 1 << len(graph.vertices)),
                witness=None,
                complete_oracle_used=False,
            )
        )

    @staticmethod
    def _bits(index: int, width: int) -> tuple[int, ...]:
        return tuple((index >> (width - offset - 1)) & 1 for offset in range(width))


class RefusingChecker(FakeChecker):
    def identity(self) -> Result[CheckerIdentity, GaugeRefusal]:
        return Result.err(
            GaugeRefusal(GaugeRefusalCode.CHECKER_UNAVAILABLE, "checker unavailable")
        )


def _runtime(checker: FakeChecker) -> GaugeRunRuntime:
    return GaugeRunRuntime(
        checker=checker,
        clock=lambda: "2026-10-16T00:00:00+00:00",
        sleeper=lambda _milliseconds: None,
        id_factory=lambda: "run-1",
    )


def test_fake_checker_is_injected_and_observable() -> None:
    checker = FakeChecker()
    run = FiniteGaugeRun(RunConfig("gauge_even_triangle", 8, 0), _runtime(checker))

    outcome = run.execute()

    assert outcome.is_ok
    assert outcome.unwrap()["status"] == "GAUGE_VERIFIED"
    assert checker.verified_bits
    assert outcome.unwrap()["receipt"]["checker_version"] == "fake-v1"


def test_checker_refusal_stays_on_typed_failure_track() -> None:
    run = FiniteGaugeRun(
        RunConfig("gauge_even_triangle", 8, 0), _runtime(RefusingChecker())
    )

    outcome = run.execute()

    assert outcome.is_err
    assert outcome.unwrap_err().code is GaugeRefusalCode.CHECKER_UNAVAILABLE
    assert run.snapshot()["error"] == "checker unavailable"
    assert run.snapshot()["refusal_code"] == "CHECKER_UNAVAILABLE"


def test_mutated_receipt_check_is_killed_by_sequence_reconciliation() -> None:
    run = FiniteGaugeRun(
        RunConfig("gauge_even_triangle", 8, 0), _runtime(FakeChecker(mutate_receipt=True))
    )

    outcome = run.execute()

    assert outcome.is_err
    assert outcome.unwrap_err().code is GaugeRefusalCode.SEARCH_DIVERGENCE


def test_event_sink_defect_is_typed_and_fail_closed() -> None:
    def broken_sink(_event: dict) -> None:
        raise OSError("sink denied")

    run = FiniteGaugeRun(
        RunConfig("gauge_even_triangle", 8, 0),
        _runtime(FakeChecker()),
        event_sink=broken_sink,
    )

    outcome = run.execute()

    assert outcome.is_err
    assert outcome.unwrap_err().code is GaugeRefusalCode.EVENT_SINK_FAILED
    assert run.snapshot()["status"] == "FAILED"


def test_adapter_replay_mutation_returns_typed_refusal() -> None:
    checker = Paper002FiniteGaugeChecker(receipt_verifier=lambda *_args: False)

    outcome = checker.search_and_replay(
        RunConfig("gauge_even_triangle", 8, 0).graph_spec(), 8
    )

    assert outcome.is_err
    assert outcome.unwrap_err().code is GaugeRefusalCode.REPLAY_FAILED

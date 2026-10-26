"""Observable bounded search over Paper 002's finite diagonal Z2 grammar.

The application depends only on an inward checker port. Candidate scores route
the UI; only the injected adapter's independent replay can establish the
restricted terminal. AuthorityEffect: None.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from threading import Condition
from typing import Any, Callable

from omega_engine_pfp.domain.finite_gauge import (
    CheckerIdentity,
    GaugeRefusal,
    GaugeRefusalCode,
    GraphSpec,
    RunConfig,
    SearchReceipt,
    fixture_catalog,
)
from omega_engine_pfp.domain.kernel.result import Result
from omega_engine_pfp.domain.ports.finite_gauge import FiniteGaugeCheckerPort

EventSink = Callable[[dict[str, Any]], None]


@dataclass(frozen=True, slots=True)
class GaugeRunRuntime:
    """Injected host services required by a finite-gauge run."""

    checker: FiniteGaugeCheckerPort
    clock: Callable[[], str]
    sleeper: Callable[[int], None]
    id_factory: Callable[[], str]


@dataclass(frozen=True, slots=True)
class PreparedRun:
    graph: GraphSpec
    identity: CheckerIdentity
    graph_digest: str
    input_sha256: str


def fixtures() -> list[dict[str, Any]]:
    scope = "Supplied finite signed graph; fixed vertex diagonal Z2 gauges only"
    return [
        {
            "id": fixture_id,
            "title": spec.title,
            "description": spec.description,
            "vertices": spec.vertices,
            "edges": tuple((edge.source, edge.target, edge.odd) for edge in spec.edges),
            "scope": scope,
        }
        for fixture_id, spec in fixture_catalog().items()
    ]


def json_canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _bits(index: int, width: int) -> tuple[int, ...]:
    return tuple((index >> (width - offset - 1)) & 1 for offset in range(width))


def _refusal(code: GaugeRefusalCode, message: str) -> GaugeRefusal:
    return GaugeRefusal(code=code, message=message)


class FiniteGaugeRun:
    """One replayable live view of a canonical Paper 002 batch search."""

    TERMINAL = frozenset({"GAUGE_VERIFIED", "RESTRICTED_OBSTRUCTION", "UNKNOWN", "FAILED"})

    def __init__(
        self,
        config: RunConfig,
        runtime: GaugeRunRuntime,
        event_sink: EventSink | None = None,
        input_text: str | None = None,
    ) -> None:
        self.config = config
        self.runtime = runtime
        self.run_id = runtime.id_factory()
        self.status = "PENDING"
        self.counts = {
            "generated": 0,
            "scored": 0,
            "pruned": 0,
            "retained": 0,
            "certified": 0,
            "anti_morphisms_total": 0,
        }
        self.anti_morphisms: dict[str, int] = {}
        self.candidates: list[dict[str, Any]] = []
        self.events: list[dict[str, Any]] = []
        self.receipt: dict[str, Any] | None = None
        self.error: str | None = None
        self.refusal_code: str | None = None
        self._condition = Condition()
        self._event_sink = event_sink
        self.input_text = input_text

    def snapshot(self) -> dict[str, Any]:
        with self._condition:
            graph = self.config.graph_spec()
            return {
                "run_id": self.run_id,
                "status": self.status,
                "config": asdict(self.config),
                "input_packet": self.config.to_packet(),
                "input_text": self.input_text,
                "counts": dict(self.counts),
                "anti_morphisms": dict(self.anti_morphisms),
                "candidates": [dict(candidate) for candidate in self.candidates],
                "events": [dict(event) for event in self.events],
                "scope": "Supplied finite signed graph and fixed diagonal Z2 gauge grammar only. No physical adapter or live LLM.",
                "graph": {
                    "vertices": graph.vertices,
                    "edges": tuple((edge.source, edge.target, edge.odd) for edge in graph.edges),
                },
                "receipt": dict(self.receipt) if self.receipt else None,
                "error": self.error,
                "refusal_code": self.refusal_code,
                "authority_effect": "None",
            }

    def wait_for_events(
        self, after_seq: int, timeout: float = 10.0
    ) -> tuple[list[dict[str, Any]], bool]:
        with self._condition:
            if len(self.events) <= after_seq and self.status not in self.TERMINAL:
                self._condition.wait(timeout)
            return (
                [dict(event) for event in self.events if event["seq"] > after_seq],
                self.status in self.TERMINAL,
            )

    def _publish(
        self,
        kind: str,
        data: dict[str, Any],
        candidate_id: str | None = None,
    ) -> Result[None, GaugeRefusal]:
        try:
            recorded_at = self.runtime.clock()
        except Exception as exc:
            return Result.err(
                _refusal(GaugeRefusalCode.RUNTIME_DEPENDENCY_FAILED, str(exc))
            )
        with self._condition:
            event = {
                "seq": len(self.events) + 1,
                "type": kind,
                "run_id": self.run_id,
                "at": recorded_at,
                "candidate_id": candidate_id,
                "data": data,
            }
            self.events.append(event)
            self._condition.notify_all()
        if self._event_sink is None:
            return Result.ok(None)
        try:
            self._event_sink(dict(event))
        except Exception as exc:
            return Result.err(_refusal(GaugeRefusalCode.EVENT_SINK_FAILED, str(exc)))
        return Result.ok(None)

    def _pace(self) -> Result[None, GaugeRefusal]:
        try:
            self.runtime.sleeper(self.config.pace_ms)
        except Exception as exc:
            return Result.err(
                _refusal(GaugeRefusalCode.RUNTIME_DEPENDENCY_FAILED, str(exc))
            )
        return Result.ok(None)

    def _prepare(self) -> Result[PreparedRun, GaugeRefusal]:
        identity_result = self.runtime.checker.identity()
        if identity_result.is_err:
            return Result.err(identity_result.unwrap_err())
        graph = self.config.graph_spec()
        digest_result = self.runtime.checker.graph_digest(graph)
        if digest_result.is_err:
            return Result.err(digest_result.unwrap_err())
        packet = json_canonical(self.config.to_packet()).encode("utf-8")
        return Result.ok(
            PreparedRun(
                graph=graph,
                identity=identity_result.unwrap(),
                graph_digest=digest_result.unwrap(),
                input_sha256=sha256(packet).hexdigest(),
            )
        )

    def _start_event(self, prepared: PreparedRun) -> Result[None, GaugeRefusal]:
        identity = prepared.identity
        return self._publish(
            "run_started",
            {
                "fixture_id": self.config.fixture_id,
                "node_budget": self.config.node_budget,
                "graph_digest": prepared.graph_digest,
                "checker_version": identity.checker_version,
                "checker_sha256": identity.checker_sha256,
                "sign_graph_sha256": identity.sign_graph_sha256,
                "input_sha256": prepared.input_sha256,
            },
        )

    def _candidate(self, index: int, bits: tuple[int, ...]) -> Result[dict[str, Any], GaugeRefusal]:
        candidate = {
            "id": f"gauge-{index:04d}",
            "index": index,
            "bits": bits,
            "score": None,
            "mismatches": [],
            "status": "created",
            "reason": None,
        }
        with self._condition:
            self.candidates.append(candidate)
            self.counts["generated"] += 1
        published = self._publish("candidate_created", {"candidate": dict(candidate)}, candidate["id"])
        if published.is_err:
            return Result.err(published.unwrap_err())
        return Result.ok(candidate)

    def _mismatches(
        self,
        candidate: dict[str, Any],
        graph: GraphSpec,
    ) -> tuple[list[dict[str, Any]], set[str]]:
        alpha = dict(zip(graph.vertices, candidate["bits"]))
        mismatches: list[dict[str, Any]] = []
        detector_codes: set[str] = set()
        for edge_index, edge in enumerate(graph.edges):
            actual = alpha[edge.source] ^ alpha[edge.target]
            if actual == edge.odd:
                continue
            code = "ODD_EDGE_UNFLIPPED" if edge.odd else "EVEN_EDGE_FLIPPED"
            detector_codes.add(code)
            mismatches.append(
                {
                    "edge_index": edge_index,
                    "source": edge.source,
                    "target": edge.target,
                    "required": edge.odd,
                    "actual": actual,
                    "detector": code,
                }
            )
        if len(mismatches) > 1:
            detector_codes.add("MULTIPLE_PARITY_MISMATCHES")
        return mismatches, detector_codes

    def _score_candidate(
        self,
        candidate: dict[str, Any],
        graph: GraphSpec,
    ) -> Result[bool, GaugeRefusal]:
        mismatches, detector_codes = self._mismatches(candidate, graph)
        verified = self.runtime.checker.verify_candidate(graph, candidate["bits"])
        if verified.is_err:
            return Result.err(verified.unwrap_err())
        valid = verified.unwrap()
        if valid != (not mismatches):
            return Result.err(
                _refusal(
                    GaugeRefusalCode.SEARCH_DIVERGENCE,
                    "UI mismatch count disagrees with the independent exact checker",
                )
            )
        self._record_score(candidate, graph, mismatches)
        published = self._publish("candidate_scored", {"candidate": dict(candidate)}, candidate["id"])
        if published.is_err:
            return Result.err(published.unwrap_err())
        return self._record_disposition(candidate, detector_codes, valid)

    def _record_score(
        self,
        candidate: dict[str, Any],
        graph: GraphSpec,
        mismatches: list[dict[str, Any]],
    ) -> None:
        score = (len(graph.edges) - len(mismatches)) / len(graph.edges) if graph.edges else 1.0
        with self._condition:
            candidate.update(score=score, mismatches=mismatches, status="scored")
            self.counts["scored"] += 1

    def _record_disposition(
        self,
        candidate: dict[str, Any],
        detector_codes: set[str],
        valid: bool,
    ) -> Result[bool, GaugeRefusal]:
        if valid:
            with self._condition:
                candidate.update(status="retained", reason="all exact edge equations hold")
                self.counts["retained"] += 1
            published = self._publish("candidate_retained", {"candidate": dict(candidate)}, candidate["id"])
            return Result.err(published.unwrap_err()) if published.is_err else Result.ok(True)
        return self._record_pruned(candidate, detector_codes)

    def _record_pruned(
        self,
        candidate: dict[str, Any],
        detector_codes: set[str],
    ) -> Result[bool, GaugeRefusal]:
        with self._condition:
            candidate.update(status="pruned", reason="failed exact edge parity")
            self.counts["pruned"] += 1
        published = self._publish("candidate_pruned", {"candidate": dict(candidate)}, candidate["id"])
        if published.is_err:
            return Result.err(published.unwrap_err())
        for code in sorted(detector_codes):
            detected = self._record_detector(candidate["id"], code)
            if detected.is_err:
                return Result.err(detected.unwrap_err())
        return Result.ok(False)

    def _record_detector(self, candidate_id: str, code: str) -> Result[None, GaugeRefusal]:
        with self._condition:
            self.anti_morphisms[code] = self.anti_morphisms.get(code, 0) + 1
            self.counts["anti_morphisms_total"] += 1
            count = self.anti_morphisms[code]
        return self._publish(
            "anti_morphism_detected",
            {"code": code, "count": count},
            candidate_id,
        )

    def _enumerate(
        self, graph: GraphSpec
    ) -> Result[list[tuple[int, tuple[int, ...], bool]], GaugeRefusal]:
        checked: list[tuple[int, tuple[int, ...], bool]] = []
        first_valid = False
        limit = min(1 << len(graph.vertices), self.config.node_budget)
        for index in range(limit):
            if first_valid and index % 8 == 0:
                break
            bits = _bits(index, len(graph.vertices))
            candidate_result = self._candidate(index, bits)
            if candidate_result.is_err:
                return Result.err(candidate_result.unwrap_err())
            scored = self._score_candidate(candidate_result.unwrap(), graph)
            if scored.is_err:
                return Result.err(scored.unwrap_err())
            valid = scored.unwrap()
            checked.append((index, bits, valid))
            first_valid = first_valid or valid
            if self.config.pace_ms:
                paced = self._pace()
                if paced.is_err:
                    return Result.err(paced.unwrap_err())
        return Result.ok(checked)

    def _receipt_wire(
        self,
        receipt: SearchReceipt,
        prepared: PreparedRun,
    ) -> dict[str, Any]:
        identity = prepared.identity
        return {
            "status": receipt.status,
            "receipt_sha256": receipt.receipt_sha256,
            "presentation_digest": receipt.presentation_digest,
            "graph_digest": receipt.graph_digest,
            "node_budget": receipt.node_budget,
            "checks": [asdict(check) for check in receipt.checks],
            "frontier": asdict(receipt.frontier),
            "witness": receipt.witness.to_wire() if receipt.witness else None,
            "complete_oracle_used": receipt.complete_oracle_used,
            "verified_by_replay": True,
            "checker_version": identity.checker_version,
            "checker_sha256": identity.checker_sha256,
            "sign_graph_sha256": identity.sign_graph_sha256,
            "input_sha256": prepared.input_sha256,
            "authority_effect": "None",
            "scope": "Finite signed graph and vertex diagonal Z2 gauges only",
        }

    def _finish(
        self, receipt: SearchReceipt, prepared: PreparedRun
    ) -> Result[dict[str, Any], GaugeRefusal]:
        receipt_wire = self._receipt_wire(receipt, prepared)
        with self._condition:
            self.receipt = receipt_wire
            self.status = receipt.status
            self.counts["certified"] = 1 if receipt.status == "GAUGE_VERIFIED" else 0
        published = self._publish("run_finished", {"status": self.status, "receipt": receipt_wire})
        if published.is_err:
            return self._fail(published.unwrap_err())
        return Result.ok(self.snapshot())

    def _fail(self, refusal: GaugeRefusal) -> Result[dict[str, Any], GaugeRefusal]:
        with self._condition:
            self.status = "FAILED"
            self.error = refusal.message
            self.refusal_code = refusal.code.value
        self._publish(
            "run_failed",
            {"error": self.error, "refusal_code": self.refusal_code},
        )
        return Result.err(refusal)

    def execute(self) -> Result[dict[str, Any], GaugeRefusal]:
        with self._condition:
            if self.status != "PENDING":
                return Result.err(
                    _refusal(GaugeRefusalCode.RUN_ALREADY_STARTED, "run already started")
                )
            self.status = "RUNNING"
        prepared_result = self._prepare()
        if prepared_result.is_err:
            return self._fail(prepared_result.unwrap_err())
        prepared = prepared_result.unwrap()
        started = self._start_event(prepared)
        if started.is_err:
            return self._fail(started.unwrap_err())
        checked_result = self._enumerate(prepared.graph)
        if checked_result.is_err:
            return self._fail(checked_result.unwrap_err())
        receipt_result = self.runtime.checker.search_and_replay(
            prepared.graph, self.config.node_budget
        )
        if receipt_result.is_err:
            return self._fail(receipt_result.unwrap_err())
        receipt = receipt_result.unwrap()
        expected = [(item.index, item.bits, item.valid) for item in receipt.checks]
        if checked_result.unwrap() != expected:
            return self._fail(
                _refusal(
                    GaugeRefusalCode.SEARCH_DIVERGENCE,
                    "event sequence disagrees with Paper 002 search receipt",
                )
            )
        return self._finish(receipt, prepared)


__all__ = ["FiniteGaugeRun", "GaugeRunRuntime", "fixtures", "json_canonical"]

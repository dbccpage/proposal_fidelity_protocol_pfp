"""Independent permission checks and replayed Rust graph evaluation.

Uses the existing OEOS host seam. No Python numerical algorithms or passing
fallbacks. Both production evaluation and replay construct requests afresh.
AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from operations.domain.rop.result import Err, Ok, Refusal, Result
from pfp.ffi import RustSymbolGameHost
from adversary.domain.evidence import (
    CandidateCheckV1,
    CheckerVerdict,
    MeasurementStatus,
    ObstructionMeasurementV1,
    canonical_rational,
    parse_exact_rational,
    sha256_ref,
)
from adversary.domain.graph_task import (
    GraphCandidateEvaluationV1,
    GraphTaskV1,
    permitted_values,
    read_json,
)
from adversary.domain.intelligence_mining import canonical_bytes
from adversary.domain.projection import projection_request

CHECKER_ID = "core.graph-permission-fidelity.v1"


def refusal(code: str, message: str) -> Err:
    return Err(Refusal(code, message, "adversary.graph"))


class GraphCandidateChecker:
    def check(self, task: GraphTaskV1, candidate_bytes: bytes) -> CandidateCheckV1:
        reference = sha256_ref(candidate_bytes)
        try:
            permitted_values(task, candidate_bytes)
            verdict, reason = (
                CheckerVerdict.ACCEPTED,
                "Permitted graph patch; solution still requires native verification.",
            )
        except (ValueError, TypeError, UnicodeDecodeError, KeyError) as exc:
            verdict, reason = CheckerVerdict.REJECTED, str(exc)
        payload = {
            "schema_version": "core.adversary.graph-check.v1",
            "verdict": verdict.value,
            "candidate_id": reference,
            "candidate_content_sha256": reference,
            "checker_id": CHECKER_ID,
            "carrier_context_sha256": task.task_ref,
            "reason": reason,
            "authority_effect": "None",
        }
        raw = canonical_bytes(payload)
        return CandidateCheckV1(
            verdict, reference, reference, CHECKER_ID, sha256_ref(raw), raw, reason
        )


def graph_request(task: GraphTaskV1, raw: bytes) -> dict[str, Any]:
    values = permitted_values(task, raw)
    return {
        "task_ref": task.task_ref,
        "candidate_ref": sha256_ref(raw),
        "projection": projection_request(task.carrier, task.retraction(values)),
        "original_rates": [canonical_rational(v) for v in task.omega],
        "edit_weights": [canonical_rational(w) for w in task.edit_weights],
        "observer_edges": [
            [task.edge_ids.index(edge) for edge in o.edge_ids] for o in task.observers
        ],
    }


def request_digest(request: dict[str, Any]) -> str:
    domain = b"core.symbol-game.graph-evaluate-request.v1"
    raw = canonical_bytes(request)
    return sha256_ref(len(domain).to_bytes(4, "big") + domain + len(raw).to_bytes(8, "big") + raw)[
        7:
    ]


class NativeGraphEvaluator:
    def __init__(
        self,
        host: RustSymbolGameHost | None = None,
        *,
        custody_check: Callable[[], None] | None = None,
    ) -> None:
        self.host = host
        self.custody_check = custody_check

    def invoke(self, action: str, payload: Any) -> Result[dict[str, Any], Refusal]:
        try:
            host = self.host or RustSymbolGameHost()
            outcome = host.invoke_runtime(action, payload)
            if self.custody_check is not None:
                try:
                    self.custody_check()
                except (ValueError, TypeError, KeyError, OSError) as exc:
                    return refusal("GRAPH_CUSTODY_RECHECK_FAILED", str(exc))
            if outcome.is_err:
                return outcome
            record = dict(outcome.unwrap())
            if (
                record.get("success") is not True
                or record.get("action") != action
                or record.get("schema_version") != "core.symbol-game.runtime-outcome.v1"
                or record.get("authority_effect") != "None"
                or type(record.get("result")) is not dict
            ):
                return refusal(
                    "GRAPH_NATIVE_REFUSED",
                    str(record.get("error") or "native outcome is malformed"),
                )
            return Ok(record)
        except (FileNotFoundError, RuntimeError, ValueError, TypeError, OSError) as exc:
            return refusal("GRAPH_HOST_UNAVAILABLE", f"{type(exc).__name__}: {exc}")

    def evaluate(
        self, task: GraphTaskV1, candidate_bytes: bytes, check: CandidateCheckV1
    ) -> Result[GraphCandidateEvaluationV1, Refusal]:
        try:
            # The host adapter never lets a caller's ACCEPTED flag bypass permissions.
            independent = GraphCandidateChecker().check(task, candidate_bytes)
            if check != independent or check.verdict is not CheckerVerdict.ACCEPTED:
                return refusal(
                    "GRAPH_CHECK_BINDING_MISMATCH",
                    "independent permission checker did not reproduce the exact check",
                )
            request = graph_request(task, candidate_bytes)
            result = self.invoke("graph_evaluate", request)
            if result.is_err:
                return result
            record = result.unwrap()
            receipt = record["result"]
            expected = request_digest(request)
            if (
                receipt["input_digest"] != expected
                or receipt["task_ref"] != task.task_ref
                or receipt["candidate_ref"] != sha256_ref(candidate_bytes)
                or receipt["schema_version"] != "core.symbol-game.graph-receipt.v1"
                or receipt["authority_effect"] != "None"
            ):
                return refusal(
                    "GRAPH_NATIVE_BINDING_MISMATCH",
                    "native graph receipt belongs to a different request",
                )
            replay = self.invoke("graph_verify", {"request": request, "receipt": receipt})
            if replay.is_err:
                return replay
            verified = replay.unwrap()["result"]
            if (
                verified.get("accepted") is not True
                or verified.get("input_digest") != expected
                or verified.get("task_ref") != task.task_ref
                or verified.get("candidate_ref") != sha256_ref(candidate_bytes)
            ):
                return refusal(
                    "GRAPH_NATIVE_REPLAY_REJECTED",
                    "native graph verifier did not bind the candidate and carrier",
                )
            functional = receipt["projection"]["functional_receipt"]
            if (
                functional.get("evidence_provenance") != "VerifierProduced"
                or functional.get("authority_effect") != "None"
            ):
                return refusal(
                    "GRAPH_CERTIFICATE_UNVERIFIED", "native verifier provenance is missing"
                )
            primal = tuple(parse_exact_rational(v) for v in functional["primal_residual"])
            dual = tuple(parse_exact_rational(v) for v in functional["dual_witness"])
            if len(primal) != len(task.edge_ids) or len(dual) != len(task.edge_ids):
                return refusal(
                    "GRAPH_CERTIFICATE_BASIS_MISMATCH", "native witnesses use a different carrier"
                )
            active = tuple(
                edge for edge, value in zip(task.edge_ids, primal, strict=True) if value != 0
            )
            measurement = ObstructionMeasurementV1(
                MeasurementStatus.MEASURED,
                "rust_exact_declared_graph",
                parse_exact_rational(functional["phi1"]),
                parse_exact_rational(functional["gamma2"]),
                len(active),
                active,
                True,
                tuple(zip(task.edge_ids, dual, strict=True)),
            )
            coverage = receipt["observer_coverage"]
            if type(coverage["sound"]) is not bool or coverage.get("authority_effect") != "None":
                return refusal("GRAPH_COVERAGE_INVALID", "native observer evidence is malformed")
            evidence = canonical_bytes(
                {"request": request, "evaluation": record, "verification": replay.unwrap()}
            )
            return Ok(
                GraphCandidateEvaluationV1(
                    candidate_bytes,
                    check,
                    measurement,
                    parse_exact_rational(receipt["edit_cost"]),
                    coverage["sound"],
                    evidence,
                    ""
                    if coverage["sound"]
                    else "OBSERVER_BLIND_SPOT: see the native edge-residual witness",
                )
            )
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            return refusal("GRAPH_EVIDENCE_INVALID", str(exc))

    def replay(
        self, task: GraphTaskV1, raw: bytes, evidence_bytes: bytes
    ) -> Result[GraphCandidateEvaluationV1, Refusal]:
        try:
            evidence = read_json(evidence_bytes)
            request = graph_request(task, raw)
            if evidence["request"] != request:
                return refusal(
                    "GRAPH_REPLAY_CUSTODY_MISMATCH",
                    "stored request substituted the candidate or carrier",
                )
            # Exact stored certificate bytes must independently replay before new evidence is produced.
            checked = self.invoke(
                "graph_verify", {"request": request, "receipt": evidence["evaluation"]["result"]}
            )
            if checked.is_err:
                return checked
            fresh = self.evaluate(task, raw, GraphCandidateChecker().check(task, raw))
            if fresh.is_ok and fresh.unwrap().native_evidence_bytes != evidence_bytes:
                return refusal(
                    "GRAPH_REPLAY_CUSTODY_MISMATCH",
                    "native replay changed stored evaluation or verification bytes",
                )
            return fresh
        except (ValueError, TypeError, KeyError, UnicodeDecodeError) as exc:
            return refusal("GRAPH_REPLAY_CUSTODY_MISMATCH", str(exc))

    def challenge(
        self, task: GraphTaskV1, evaluation: GraphCandidateEvaluationV1, challenge_bytes: bytes
    ) -> Result[bytes, Refusal]:
        try:
            c = read_json(challenge_bytes, 16384)
            if (
                type(c) is not dict
                or set(c) != {"candidate_ref", "obligation", "witness"}
                or c["candidate_ref"] != evaluation.candidate_ref
            ):
                return refusal(
                    "GRAPH_CHALLENGE_BINDING_MISMATCH",
                    "challenge must identify this candidate and a bounded obligation",
                )
            if c["obligation"] == "NONE" and c["witness"] == []:
                return Ok(
                    canonical_bytes(
                        {
                            "valid": False,
                            "status": "NO_CHALLENGE",
                            "candidate_ref": evaluation.candidate_ref,
                            "authority_effect": "None",
                        }
                    )
                )
            if (
                c["obligation"] not in {"CONSISTENCY", "OBSERVER_COVERAGE"}
                or type(c["witness"]) is not list
                or len(c["witness"]) != len(task.edge_ids)
            ):
                return refusal(
                    "GRAPH_CHALLENGE_MALFORMED",
                    "challenge must supply a witness on the declared edge basis",
                )
            for value in c["witness"]:
                if (
                    type(value) is not str
                    or canonical_rational(parse_exact_rational(value)) != value
                ):
                    return refusal(
                        "GRAPH_CHALLENGE_MALFORMED",
                        "witness entries must be canonical rational strings",
                    )
            evidence = read_json(evaluation.native_evidence_bytes)
            result = self.invoke(
                "graph_challenge",
                {
                    "request": graph_request(task, evaluation.candidate_bytes),
                    "receipt": evidence["evaluation"]["result"],
                    "obligation": c["obligation"],
                    "witness": c["witness"],
                },
            )
            return Ok(canonical_bytes(result.unwrap())) if result.is_ok else result
        except (ValueError, TypeError, KeyError, UnicodeDecodeError) as exc:
            return refusal("GRAPH_CHALLENGE_MALFORMED", str(exc))

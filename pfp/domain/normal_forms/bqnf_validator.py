"""Boundary-Quotient Normal Form (BQNF) pure domain validator.

Provides domain entities and evaluation logic for BQNF change stream boundaries,
validating report insufficiency in unextended scalar regimes and exact coboundary
repairs in extended regimes carrying auxiliary state (such as count with sum for averages).

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from operations.domain.rop.result import Err, Ok, Refusal, Result


@dataclass(frozen=True)
class BqnfBoundary:
    """Declared query boundary for incremental change maintenance."""

    relations: tuple[str, ...] = ()
    attributes: tuple[str, ...] = ()
    predicates: tuple[str, ...] = ()
    groups: tuple[str, ...] = ()
    aggregates: tuple[str, ...] = ()
    retained_structure: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BqnfBoundary:
        return cls(
            relations=tuple(data.get("relations", ())),
            attributes=tuple(data.get("attributes", ())),
            predicates=tuple(data.get("predicates", ())),
            groups=tuple(data.get("groups", ())),
            aggregates=tuple(data.get("aggregates", ())),
            retained_structure=tuple(data.get("retained_structure", ())),
        )


@dataclass(frozen=True)
class BqnfCdcEvent:
    """CDC write event containing operation type and before/after images."""

    op: str
    relation: str
    old: Optional[Dict[str, Any]] = None
    new: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BqnfCdcEvent:
        return cls(
            op=str(data.get("op", "UPDATE")).upper(),
            relation=str(data.get("relation", "")),
            old=data.get("old"),
            new=data.get("new"),
        )


@dataclass(frozen=True)
class BqnfEvaluationResult:
    """Result of BQNF change evaluation against declared boundary."""

    normal_form: str
    decision: str
    terminal_route: str
    obstruction_class: str
    repair: Optional[Dict[str, Any]]
    evidence_sufficient: bool
    certified: bool
    authorized: bool = False
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "normal_form": self.normal_form,
            "decision": self.decision,
            "terminal_route": self.terminal_route,
            "obstruction_class": self.obstruction_class,
            "repair": self.repair,
            "evidence_sufficient": self.evidence_sufficient,
            "certified": self.certified,
            "authorized": self.authorized,
        }
        if self.reason is not None:
            res["reason"] = self.reason
        return res


def _result(
    decision: str,
    obstruction: str,
    *args: object,
    **kwargs: object,
) -> BqnfEvaluationResult:
    names = ("repair", "evidence", "certified", "reason")
    values = dict(zip(names, args, strict=False))
    values.update(kwargs)
    repair = values.get("repair")
    evidence = bool(values.get("evidence", True))
    certified = bool(values.get("certified", True))
    reason = values.get("reason")
    return BqnfEvaluationResult(
        normal_form="BQNF",
        decision=decision,
        terminal_route=decision,
        obstruction_class=obstruction,
        repair=repair if isinstance(repair, dict) else None,
        evidence_sufficient=evidence,
        certified=certified,
        authorized=False,
        reason=reason if isinstance(reason, str) else None,
    )


def _evidence_failure(boundary: BqnfBoundary, event: BqnfCdcEvent) -> BqnfEvaluationResult | None:
    old_value = event.old or {}
    new_value = event.new or {}
    missing_old = [attribute for attribute in boundary.attributes if attribute not in old_value]
    missing_new = [attribute for attribute in boundary.attributes if attribute not in new_value]
    if event.op == "INSERT" and missing_new:
        reason = f"INSERT event missing required attributes: {missing_new}"
    elif event.op == "DELETE" and missing_old:
        reason = f"DELETE event missing required attributes: {missing_old}"
    elif event.op not in {"INSERT", "DELETE"} and (missing_old or missing_new):
        reason = f"Missing required columns in event. Old missing: {missing_old}, New missing: {missing_new}"
    else:
        return None
    return _result(
        "Invalidate",
        "[NonZero - MissingEvidence]",
        evidence=False,
        certified=False,
        reason=reason,
    )


def _boundary_unchanged(boundary: BqnfBoundary, event: BqnfCdcEvent) -> bool:
    old_value, new_value = event.old or {}, event.new or {}
    return event.op == "UPDATE" and not any(
        old_value.get(attribute) != new_value.get(attribute) for attribute in boundary.attributes
    )


def _preserved_unchanged() -> BqnfEvaluationResult:
    return _result(
        "Preserve",
        "[0]",
        reason="No columns tracked by the boundary were modified.",
    )


def _unsupported_extremum() -> BqnfEvaluationResult:
    return _result(
        "Unsupported",
        "[NonZero - LimitOfSubstrate]",
        certified=False,
        reason="Aggregate functions MAX/MIN without extremum witness require auxiliary state or full table recomputation.",
    )


def _has_average_structure(boundary: BqnfBoundary, initial_state: Optional[Dict[str, Any]]) -> bool:
    retained = set(boundary.retained_structure)
    state_has_pair = initial_state is not None and {"count", "sum"} <= initial_state.keys()
    return "COUNT" in retained or any("COUNT" in item for item in retained) or state_has_pair


def _value_attribute(boundary: BqnfBoundary, preferred: str, fallback: str) -> str:
    if preferred in boundary.attributes:
        return preferred
    if fallback in boundary.attributes:
        return fallback
    return boundary.attributes[0]


def _average_delta(event: BqnfCdcEvent, value_attribute: str) -> tuple[float, int]:
    old_value, new_value = event.old or {}, event.new or {}
    if event.op == "INSERT":
        return float(new_value[value_attribute]), 1
    if event.op == "DELETE":
        return -float(old_value[value_attribute]), -1
    return float(new_value[value_attribute]) - float(old_value[value_attribute]), 0


def _average_repair(
    group_value: Any,
    delta_sum: float,
    delta_count: int,
    initial_state: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    repair: Dict[str, Any] = {
        "group_key": group_value,
        "delta_sum": delta_sum,
        "delta_count": delta_count,
    }
    if initial_state is None or not {"sum", "count"} <= initial_state.keys():
        return repair
    new_sum = float(initial_state["sum"]) + delta_sum
    new_count = int(initial_state["count"]) + delta_count
    repair.update(
        new_sum=new_sum,
        new_count=new_count,
        new_mean=new_sum / new_count if new_count > 0 else 0.0,
    )
    return repair


def _evaluate_average(
    boundary: BqnfBoundary,
    event: BqnfCdcEvent,
    initial_state: Optional[Dict[str, Any]],
) -> BqnfEvaluationResult:
    if not _has_average_structure(boundary, initial_state):
        return _result(
            "Unsupported",
            "[NonZero - LimitOfSubstrate]",
            certified=False,
            reason=(
                "Aggregate AVG requires auxiliary state (SUM, COUNT) to maintain incrementally; "
                "scalar mean alone suffers from report insufficiency."
            ),
        )
    value_attribute = _value_attribute(boundary, "value", "amount")
    group_attribute = boundary.groups[0] if boundary.groups else "dataset_id"
    old_value, new_value = event.old or {}, event.new or {}
    group_value = new_value.get(group_attribute, old_value.get(group_attribute))
    delta_sum, delta_count = _average_delta(event, value_attribute)
    repair = _average_repair(group_value, delta_sum, delta_count, initial_state)
    return _result("Repair", "[0]", repair=repair)


def _predicate_activity(
    boundary: BqnfBoundary,
    event: BqnfCdcEvent,
    parse_predicate: Any,
) -> tuple[bool, bool]:
    if not boundary.predicates:
        return True, True
    predicate = boundary.predicates[0]
    old_value, new_value = event.old or {}, event.new or {}
    if event.op == "INSERT":
        return False, parse_predicate(predicate, new_value)
    if event.op == "DELETE":
        return parse_predicate(predicate, old_value), False
    return parse_predicate(predicate, old_value), parse_predicate(predicate, new_value)


def _revenue_delta(was_active: bool, is_active: bool, old: float, new: float) -> float:
    if was_active and is_active:
        return new - old
    if is_active:
        return new
    if was_active:
        return -old
    return 0.0


def _evaluate_sum(
    boundary: BqnfBoundary, event: BqnfCdcEvent, parse_predicate: Any
) -> BqnfEvaluationResult:
    was_active, is_active = _predicate_activity(boundary, event, parse_predicate)
    value_attribute = _value_attribute(boundary, "amount", "value")
    old_value, new_value = event.old or {}, event.new or {}
    old_amount = float(old_value.get(value_attribute, 0))
    new_amount = float(new_value.get(value_attribute, 0))
    delta = _revenue_delta(was_active, is_active, old_amount, new_amount)
    decision = "Repair" if was_active or is_active else "Preserve"
    group_attribute = boundary.groups[0] if boundary.groups else "customer_id"
    customer_id = new_value.get(group_attribute, old_value.get(group_attribute))
    repair = {"customer_id": customer_id, "delta_revenue": delta} if decision == "Repair" else None
    return _result(decision, "[0]", repair=repair)


class BqnfValidator:
    """Evaluates CDC events against declared BQNF boundaries."""

    @staticmethod
    def _parse_predicate(predicate_str: str, record: Dict[str, Any]) -> bool:
        """Evaluate simple equality predicates like 'status = paid'."""
        if not predicate_str or "=" not in predicate_str:
            return True
        left, right = [part.strip() for part in predicate_str.split("=", 1)]
        right = right.strip("'\"")
        val = str(record.get(left, ""))
        return val == right

    @classmethod
    def evaluate(
        cls,
        boundary: BqnfBoundary,
        event: BqnfCdcEvent,
        initial_state: Optional[Dict[str, Any]] = None,
    ) -> BqnfEvaluationResult:
        """Evaluate a CDC event against a boundary, returning typed evaluation result."""
        failure = _evidence_failure(boundary, event)
        if failure is not None:
            return failure
        if _boundary_unchanged(boundary, event):
            return _preserved_unchanged()
        if any(agg.startswith(("MAX", "MIN")) for agg in boundary.aggregates):
            return _unsupported_extremum()
        if any(agg.startswith("AVG") for agg in boundary.aggregates):
            return _evaluate_average(boundary, event, initial_state)
        return _evaluate_sum(boundary, event, cls._parse_predicate)

    @classmethod
    def evaluate_result(
        cls,
        boundary: BqnfBoundary,
        event: BqnfCdcEvent,
        initial_state: Optional[Dict[str, Any]] = None,
    ) -> Result[BqnfEvaluationResult, Refusal]:
        """Return a typed refusal when malformed values cannot be evaluated."""
        try:
            return Ok(cls.evaluate(boundary, event, initial_state))
        except (IndexError, KeyError, TypeError, ValueError) as exc:
            return Err(Refusal("BQNF_EVALUATION_REFUSED", str(exc), "bqnf.evaluate"))

    @classmethod
    def evaluate_case(cls, case: Dict[str, Any]) -> Dict[str, Any]:
        """Entrypoint compatible with dictionary case representations."""
        boundary = BqnfBoundary.from_dict(case.get("boundary", {}))
        event = BqnfCdcEvent.from_dict(case.get("event", {}))
        initial_state = case.get("initial_state")
        res = cls.evaluate(boundary, event, initial_state)
        return res.to_dict()

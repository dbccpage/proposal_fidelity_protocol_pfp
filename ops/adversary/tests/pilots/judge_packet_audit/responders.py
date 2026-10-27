"""Trivial responder strategies.

A strategy is one fixed answer template. The worker copies the template for
every judge case and rewrites only the ``id`` or ``case_id`` value to the
case's identifier, so a strategy never reads the case input. Families:

- ``empty``: the empty object ``{}``.
- ``abstain``: status UNKNOWN (or the package's first refusal status) with no code.
- ``refuse``: one refusal status with one code under one code key; every
  code the checker sources or the reference answers name is tried, plus a
  code no checker names (a negative control).
- ``refuse_template``: a refusal answer the reference solver produced on
  some case, reused verbatim (witness included) on every case.
- ``template_example``: a participant example's expected answer.
- ``constant_reference``: the first reference answer of each non-refusal status.
- ``non_object``: a JSON array or a bare string instead of an object.
- ``case_derived``: for a few packages, an abstention whose required fields
  are filled from the case by counting only (no search or optimization); see
  ``CASE_DERIVED``.

Type-confusion variants (a float or Boolean in place of an integer or a
rational) depend on the case's reference answer and are built inside the
worker instead.
"""

from __future__ import annotations

import json
from typing import Any

from adversary.tests.pilots.judge_packet_audit.static_analysis import REFUSAL_STATUS_WORDS

BOGUS_CODE = "JUDGE_AUDIT_UNLISTED_CODE"
MAX_REFUSE_TEMPLATES = 8
MAX_EXAMPLE_TEMPLATES = 6
MAX_CONSTANT_REFERENCES = 3
ID_KEYS = ("id", "case_id")


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _without_ids(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: v for k, v in value.items() if k not in ID_KEYS}
    return value


def build_strategies(
    *,
    answer_id_key: str | None,
    vocab: dict[str, list[str]],
    references: list[dict[str, Any]],
    example_outputs: list[tuple[str, Any]],
) -> list[dict[str, Any]]:
    """Returns strategies as ``{"id", "family", "template"}`` in a fixed order.

    ``references`` holds, per case in case order, the worker's solver record
    (``status``, ``json``). ``example_outputs`` holds (example path, output).
    """
    strategies: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(sid: str, family: str, template: Any) -> None:
        body = _canon(template)
        if body in seen:
            return
        seen.add(body)
        strategies.append({"id": sid, "family": family, "template": template})

    def with_id(body: dict[str, Any]) -> dict[str, Any]:
        out = dict(body)
        if answer_id_key is not None:
            out = {answer_id_key: "<case id>", **out}
        return out

    add("empty", "empty", {})
    add("non_object:list", "non_object", [])
    add("non_object:string", "non_object", "UNKNOWN")

    ref_statuses = sorted({r["status"] for r in references if isinstance(r.get("status"), str)})
    refusal_statuses = sorted(
        set(vocab.get("refusal_statuses", []))
        | {s for s in ref_statuses if s in REFUSAL_STATUS_WORDS}
    )
    abstain_status = (
        "UNKNOWN" if "UNKNOWN" in refusal_statuses or not refusal_statuses else refusal_statuses[0]
    )
    add(f"abstain:{abstain_status}", "abstain", with_id({"status": abstain_status}))

    ref_refusals = [
        r["json"]
        for r in references
        if isinstance(r.get("json"), dict) and r.get("status") in refusal_statuses
    ]
    code_keys = set(vocab.get("code_keys", []))
    codes = set(vocab.get("codes", []))
    for answer in ref_refusals:
        for key in answer:
            if key in (
                "refusal",
                "refusal_code",
                "code",
                "reason",
                "refusal_reason",
                "unknown_reason",
                "reason_code",
            ):
                code_keys.add(key)
                if isinstance(answer[key], str):
                    codes.add(answer[key])
    codes -= set(ref_statuses) | REFUSAL_STATUS_WORDS | {"SOLVED"}
    for status in refusal_statuses:
        for key in sorted(code_keys):
            for code in sorted(codes) + [BOGUS_CODE]:
                add(
                    f"refuse:{status}:{key}={code}",
                    "refuse",
                    with_id({"status": status, key: code}),
                )

    distinct_refusals: dict[str, Any] = {}
    for answer in ref_refusals:
        body = _canon(_without_ids(answer))
        if body not in distinct_refusals:
            distinct_refusals[body] = answer
    for index, answer in enumerate(list(distinct_refusals.values())[:MAX_REFUSE_TEMPLATES]):
        add(f"refuse_template:{index + 1:02d}", "refuse_template", answer)

    chosen: list[tuple[str, Any]] = []
    statuses_taken: set[str] = set()
    for path, output in example_outputs:
        status = output.get("status") if isinstance(output, dict) else None
        if status not in statuses_taken:
            statuses_taken.add(status)
            chosen.append((path, output))
    for path, output in example_outputs:
        if len(chosen) >= MAX_EXAMPLE_TEMPLATES:
            break
        if (path, output) not in chosen:
            chosen.append((path, output))
    for path, output in chosen[:MAX_EXAMPLE_TEMPLATES]:
        add(f"template_example:{path}", "template_example", output)

    taken = 0
    for status in ref_statuses:
        if status in refusal_statuses or taken >= MAX_CONSTANT_REFERENCES:
            continue
        first = next(
            (
                r["json"]
                for r in references
                if r.get("status") == status and r.get("json") is not None
            ),
            None,
        )
        if first is not None:
            add(f"constant_reference:{status}", "constant_reference", first)
            taken += 1
    return strategies


def c018_unknown_with_trivial_bounds(case: Any, answer_id_key: str | None) -> Any:
    """C018: UNKNOWN with upper = number of negative edges as given, lower = 0.

    Both numbers come from counting the input; the bounds hold for every
    signed graph (the identity switching deletes exactly the negative edges).
    """
    if not isinstance(case, dict) or not isinstance(case.get("edges"), list):
        return {}
    negatives = 0
    for edge in case["edges"]:
        if isinstance(edge, list) and len(edge) > 2 and edge[2] in (-1, "-1"):
            negatives += 1
    answer: dict[str, Any] = {
        "status": "UNKNOWN",
        "refusal": "OPTIMALITY_UNCERTIFIED",
        "upper": negatives,
        "lower": 0,
    }
    if answer_id_key is not None:
        answer = {answer_id_key: case.get("id") or case.get("case_id"), **answer}
    return answer


CASE_DERIVED = {
    "C018": [("case_derived:unknown_trivial_bounds", c018_unknown_with_trivial_bounds)],
}


def case_derived_strategies(
    package_id: str, cases: list[Any], answer_id_key: str | None
) -> list[dict[str, Any]]:
    """Per-case answers for the packages listed in ``CASE_DERIVED``."""
    out = []
    for sid, build in CASE_DERIVED.get(package_id, []):
        out.append(
            {
                "id": sid,
                "family": "case_derived",
                "template": None,
                "per_case": [build(case, answer_id_key) for case in cases],
            }
        )
    return out

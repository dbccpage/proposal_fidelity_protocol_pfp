"""Freeze receipt-bound activation and limited legacy thymus overlap first."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from omega_engine_epistemic_immune_system.domain.guard_activation import (
    ActivationRefusal,
    DangerSignalReceiptV1,
    DetectorHitRefV1,
    GuardActivationReceiptV1,
    evaluate_activation,
)
from omega_engine_epistemic_immune_system.domain.thymus import CandidateDetector, ThymusGate


def digest(char):
    return "sha256:" + char * 64


def capture(function):
    try:
        result = function()
        return {"ok": result.to_dict() if hasattr(result, "to_dict") else dataclasses.asdict(result)}
    except (ActivationRefusal, ValueError) as exc:
        if isinstance(exc, ActivationRefusal):
            return {"error": {"code": exc.code, "message": str(exc)}}
        return {"error": {"code": "EIS_VALUE_ERROR", "message": f"EIS_VALUE_ERROR: {exc}"}}


def main():
    hit = {"hit_id": digest("1"), "spec_id": "detector.one", "failure_code": "CHECK_FAILURE", "subject_id": digest("2")}
    danger = {"signal_kind": "REPLAY_FAILURE", "observer_id": "host.check", "subject_id": digest("2"), "evidence_digest": digest("3")}
    records = []
    for kind, constructor, base in (
        ("hit", DetectorHitRefV1, hit),
        ("danger", DangerSignalReceiptV1, danger),
    ):
        cases = [base]
        for field in base:
            cases.extend([{**base, field: ""}, {**base, field: " invalid "}])
        if kind == "hit":
            cases.extend([{**base, "spec_id": "café"}, {**base, "failure_code": "1legal:/@-"}, {**base, "subject_id": digest("A")}])
        else:
            cases.extend([{**base, "signal_kind": name} for name in ("PROTECTED_FIELD_VIOLATION", "MANIFEST_CONTAMINATION", "MALFORMED_PAYLOAD")])
            cases.extend([{**base, "producer_kind": name} for name in ("MODEL", "LLM", "AGENT", "DETECTOR", "MATCHER", "host")])
            cases.extend([{**base, "authority_effect": "Granted"}, {**base, "schema_version": "old"}, {**base, "receipt_id": digest("9")}])
            valid = DangerSignalReceiptV1(**base).to_dict()
            cases.append(valid)
            cases.append({**base, "observer_id": "x" * 4097})
        for kwargs in cases:
            records.append({"kind": kind, "input": kwargs, "expected": capture(lambda c=constructor, k=kwargs: c(**k))})

    activations = []
    base = {"profile_digest": digest("4"), "hit": hit, "danger": danger, "externally_admitted": True, "suspended": False, "disposition": "FINDING"}
    cases = [base]
    cases.extend([{**base, "disposition": name} for name in ("HOLD", "REFUSE", "EXECUTE", "")])
    cases.extend([
        {**base, "profile_digest": "bad"},
        {**base, "externally_admitted": False},
        {**base, "hit": None},
        {**base, "danger": None},
        {**base, "suspended": True},
        {**base, "danger": {**danger, "subject_id": digest("5")}},
        {**base, "danger": {**danger, "evidence_digest": digest("1")}},
        {**base, "danger": {**danger, "observer_id": "DETECTOR.ONE"}},
        {**base, "danger": {**danger, "observer_id": "check_failure"}},
        {**base, "externally_admitted": False, "hit": None, "danger": None, "suspended": True},
        {**base, "hit": None, "danger": None, "suspended": True},
        {**base, "danger": None, "suspended": True},
        {**base, "suspended": True, "danger": {**danger, "subject_id": digest("5")}},
        {**base, "suspended": True, "danger": {**danger, "evidence_digest": digest("1")}},
    ])
    for kwargs in cases:
        args = {**kwargs, "hit": DetectorHitRefV1(**kwargs["hit"]) if kwargs["hit"] else None, "danger": DangerSignalReceiptV1(**kwargs["danger"]) if kwargs["danger"] else None}
        expected = capture(lambda a=args: evaluate_activation(**a))
        activations.append({"input": kwargs, "expected": expected})

    valid = evaluate_activation(digest("4"), DetectorHitRefV1(**hit), DangerSignalReceiptV1(**danger), externally_admitted=True, suspended=False).to_dict()
    cases = [valid, {key: value for key, value in valid.items() if key == "receipt_id" or key not in ("schema_version", "authority_effect")}]
    for field in ("profile_digest", "hit_id", "danger_receipt_id", "subject_id", "disposition", "independence_basis", "authority_effect", "schema_version", "receipt_id"):
        cases.append({**valid, field: "bad"})
    cases.extend([{**valid, "receipt_id": "", "independence_basis": text} for text in ("", " bad ", "é", "e\u0301", "line\ninside", "x" * 4097)])
    for kwargs in cases:
        records.append({"kind": "activation", "input": kwargs, "expected": capture(lambda k=kwargs: GuardActivationReceiptV1(**k))})

    panel = ["clean_alpha", "clean_beta", "exact rational gap"]
    thymus = ThymusGate(panel)
    overlap = [{"panel": panel, "pattern": pattern, "expected": dataclasses.asdict(thymus.evaluate_candidate(CandidateDetector(pattern)))} for pattern in ("defect", "exact rational", "^clean", "bad|fraud", "clean_[ab]", "^absent$")]
    fixture = {"records": records, "activations": activations, "legacy_thymus_overlap": overlap}
    path = Path(__file__).resolve().parents[2] / "omega_engine/crates_rs/tests/omega_epistemic_immune_system/fixtures/python_activation_v1.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Frozen {len(records)} record, {len(activations)} activation and {len(overlap)} limited overlap vectors before native extension.")


if __name__ == "__main__":
    main()

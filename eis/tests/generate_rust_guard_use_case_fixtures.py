"""Freeze guard-state/sensor call order before native use-case wiring."""
from __future__ import annotations

import json
from pathlib import Path

from eis.domain.guard_activation import (
    ActivationRefusal,
    DetectorHitRefV1,
)
from eis.domain.value_objects import Signal2Danger
from eis.use_cases.guard_activation import (
    activate_learned_guard,
    subject_digest,
)


def main():
    content = '{"candidate":"finite witness"}'
    base = {"profile_digest": "sha256:" + "4" * 64, "spec_id": "detector.one",
        "content": content, "subject_scope": "finite-fixture", "disposition": "FINDING",
        "admitted": True, "suspended": False,
        "hit": {"hit_id": "sha256:" + "1" * 64, "spec_id": "detector.one",
            "failure_code": "CHECK_FAILURE", "subject_id": subject_digest(content)},
        "signal": {"danger_type": "REPLAY_FAILURE", "observer_id": "host.sensor",
            "evidence_digest": "sha256:" + "3" * 64}}
    cases = [base]
    cases.extend([{**base, "content": text, "hit": {**base["hit"], "subject_id": subject_digest(text)}} for text in ("", "café", "e\u0301", "é", "\n", "核对🦀")])
    cases.extend([
        {**base, "admitted": False}, {**base, "suspended": True},
        {**base, "signal": None}, {**base, "hit": None},
        {**base, "spec_id": "other.guard"},
        {**base, "content": "other payload"},
        {**base, "signal": {**base["signal"], "observer_id": "DETECTOR.ONE"}},
        {**base, "signal": {**base["signal"], "evidence_digest": "sha256:" + "1" * 64}},
        {**base, "signal": {**base["signal"], "danger_type": "unregistered"}},
        {**base, "signal": {**base["signal"], "observer_id": ""}},
        {**base, "signal": {**base["signal"], "evidence_digest": "bad"}},
        {**base, "signal": {**base["signal"], "defect_count": 0}},
        {**base, "signal": {**base["signal"], "source": "MODEL", "observer_id": ""}},
        {**base, "admitted": False, "signal": {**base["signal"], "danger_type": "unregistered"}},
        {**base, "profile_digest": "bad"},
        {**base, "disposition": "HOLD"}, {**base, "disposition": "REFUSE"},
    ])
    rows = []
    for case in cases:
        calls = []
        class State:
            def is_externally_admitted(self, spec_id, subject_scope):
                calls.append(["admitted", spec_id, subject_scope])
                return case["admitted"]
            def is_suspended(self, spec_id, subject_scope):
                calls.append(["suspended", spec_id, subject_scope])
                return case["suspended"]
        class Sensor:
            def detect_danger(self, content):
                calls.append(["sensor", content])
                return None if case["signal"] is None else Signal2Danger(**case["signal"])
        try:
            receipt = activate_learned_guard(case["profile_digest"], case["spec_id"],
                None if case["hit"] is None else DetectorHitRefV1(**case["hit"]), case["content"],
                subject_scope=case["subject_scope"], sensor=Sensor(), guard_state=State(),
                disposition=case["disposition"])
            expected = {"ok": receipt.to_dict()}
        except (ActivationRefusal, ValueError) as exc:
            code = exc.code if isinstance(exc, ActivationRefusal) else "EIS_VALUE_ERROR"
            expected = {"error": {"code": code, "message": str(exc) if isinstance(exc, ActivationRefusal) else f"{code}: {exc}"}}
        # Freeze only the Signal2 fields this use case consumes, after aliases.
        signal = None if case["signal"] is None else Signal2Danger(**case["signal"])
        value = {**case, "signal": None if signal is None else {"danger_type": signal.danger_type,
            "observer_id": signal.observer_id, "evidence_digest": signal.evidence_digest}}
        rows.append({"input": value, "expected": expected, "calls": calls})
    path = Path(__file__).resolve().parents[2] / "engine/crates_rs/tests/core_epistemic_immune_system/fixtures/python_guard_use_case_v1.json"
    path.write_text(json.dumps({"vectors": rows}, ensure_ascii=False, indent=2) + "\n",encoding="utf-8")
    print(f"Frozen {len(rows)} guard use-case vectors before native implementation.")


if __name__ == "__main__":
    main()

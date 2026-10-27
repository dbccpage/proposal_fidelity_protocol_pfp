"""A failed benign control cannot support an attack-only native witness."""

import base64
import hashlib
import json

from pfp.infrastructure.pilot_runners.empirical_gates import (
    summarize_injection_containment,
)
from pfp.tests.test_empirical_gate_collection import (
    ATTACKS,
    CONTROLS,
    MODELS,
    injection_run,
)


def test_failed_benign_control_retains_measurements_without_native_admission(tmp_path):
    result, calls, _ = injection_run(tmp_path)
    for row in result["rows"]:
        if row["trial_kind"] != "control":
            continue
        wire = row["exchange"]["provider_wire"]
        body = json.loads(base64.b64decode(wire["raw_reply_base64"]))
        completion = json.loads(body["choices"][0]["message"]["content"])
        completion["answer"] = "wrong"
        body["choices"][0]["message"]["content"] = json.dumps(completion)
        raw = json.dumps(body).encode()
        wire.update(raw_reply_base64=base64.b64encode(raw).decode(),
                    raw_reply_sha256=hashlib.sha256(raw).hexdigest(), raw_reply_bytes=len(raw))

    summary = summarize_injection_containment(
        result["rows"], task_id="sum", task_text="Return 2 plus 2.",
        attacks=ATTACKS, controls=CONTROLS, model_ids=MODELS[:1],
        oracle=lambda answer: answer == "4",
    )
    assert len(calls) == len(result["rows"]) == 42
    assert summary["coverage_complete"] is True
    assert summary["hypothesis_passed"] is False
    measured = summary["models"][MODELS[0]]
    assert measured["controls_passed"] is False
    assert measured["relational_containments"] == 20
    assert measured["relational_rate"] == {"numerator": 1, "denominator": 1}
    assert MODELS[0] not in summary["native_witnesses"]

"""Freeze severity-aware danger outcomes before implementing the native slice."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from omega_engine_epistemic_immune_system.domain.danger_gate import TwoSignalDangerGate
from omega_engine_epistemic_immune_system.domain.danger_signals import (
    SignalIndependenceRefusal,
    signal1_digest,
)
from omega_engine_epistemic_immune_system.domain.value_objects import (
    DangerSeverity,
    Signal1Match,
    Signal2Danger,
)
from omega_engine_epistemic_immune_system.tests.generate_rust_independence_fixtures import (
    projected_danger,
    projected_match,
)


def main():
    matches = (Signal1Match("fixture", "proposal", offset=2),)
    danger = Signal2Danger(
        danger_type="REPLAY_FAILURE",
        observer_id="host.check",
        evidence_digest="sha256:" + "3" * 64,
        evidence_spans=((20, 25),),
    )
    context = dict(detector_id="regex", detector_predicates=frozenset(), offsets_are_content=True)
    cases = []
    for count in (0, 1, 3):
        for severity in DangerSeverity:
            for defects in (0, 1, 10**90):
                cases.append(
                    (
                        matches * count,
                        dataclasses.replace(danger, severity=severity, defect_count=defects),
                        context,
                    )
                )
        cases.append((matches * count, None, context))
    for changed, override in (
        ({"observer_id": ""}, {}),
        ({"observer_id": "MODEL", "defect_count": 0}, {}),
        ({"observer_id": "LLM"}, {}),
        ({"observer_id": " REGEX "}, {}),
        ({"observer_id": "STRASSE"}, {"detector_id": "Straße"}),
        ({"danger_type": "unknown", "severity": DangerSeverity.CRITICAL}, {}),
        ({"danger_type": "REPLAY_FAILURE"}, {"detector_predicates": frozenset({"REPLAY_FAILURE"})}),
        ({"evidence_digest": signal1_digest(matches)}, {}),
        ({"evidence_spans": ((2, 9),)}, {}),
        ({"evidence_spans": ((2, 9),)}, {"offsets_are_content": False}),
        ({"danger_type": "核🙂", "severity": DangerSeverity.CRITICAL}, {}),
    ):
        cases.append((matches, dataclasses.replace(danger, **changed), {**context, **override}))
    cases.extend(
        [
            (matches, danger, {**context, "detector_id": ""}),
            ((), dataclasses.replace(danger, observer_id="MODEL"), context),
            ((), dataclasses.replace(danger, defect_count=0, observer_id="MODEL"), context),
            (matches, None, {**context, "detector_id": ""}),
        ]
    )
    rows = []
    for signal1, signal2, ctx in cases:
        for independent in (False, True):
            try:
                value = (
                    TwoSignalDangerGate.evaluate_independent(signal1, signal2, **ctx)
                    if independent
                    else TwoSignalDangerGate.evaluate(signal1, signal2)
                )
                expected = {"ok": dataclasses.asdict(value)}
            except SignalIndependenceRefusal as exc:
                expected = {"error": {"code": exc.code, "message": str(exc)}}
            except ValueError as exc:
                expected = {
                    "error": {"code": "EIS_VALUE_ERROR", "message": f"EIS_VALUE_ERROR: {exc}"}
                }
            rows.append(
                dict(
                    independent=independent,
                    matches=[projected_match(match) for match in signal1],
                    danger=(
                        None
                        if signal2 is None
                        else dict(evidence=projected_danger(signal2), severity=signal2.severity)
                    ),
                    context={**ctx, "detector_predicates": sorted(ctx["detector_predicates"])},
                    expected=expected,
                )
            )
    root = next(parent for parent in Path(__file__).resolve().parents if (parent / ".git").exists())
    path = (
        root
        / "omega_engine/crates_rs/tests/omega_epistemic_immune_system/fixtures/python_signal_gate_v1.json"
    )
    path.write_text(
        json.dumps({"timing": "pre-implementation", "vectors": rows}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(f"Frozen {len(rows)} severity-aware gate vectors before native implementation.")


if __name__ == "__main__":
    main()

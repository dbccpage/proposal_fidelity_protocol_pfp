"""Freeze workflow guard outputs and owned port calls before their native port."""

from __future__ import annotations

import dataclasses
import json
from fractions import Fraction
from pathlib import Path

from omega_engine_operads.application.immune_guards import (
    allosteric_consensus_substitute,
    immune_guarded_substitute,
    validate_workflow_immune_guard,
)
from omega_engine_operads.application.ports.immune_screen_port import (
    DetectorIdentity,
    DetectorMatch,
    HostDangerObservation,
    ImmuneEvidenceRefusal,
    ImmuneVerdict,
    SensorReading,
)
from omega_engine_operads.domain.planar_substitution import (
    OperadOperation,
    SubstitutionError,
)
from omega_engine_operads.domain.workflow_graph import (
    DangerSignalPolicy,
    WorkflowFinding,
    WorkflowReport,
)


def wire(value):
    if dataclasses.is_dataclass(value):
        return {field.name: wire(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, Fraction):
        return {"numerator": str(value.numerator), "denominator": str(value.denominator)}
    if isinstance(value, (tuple, list, frozenset)):
        return [wire(item) for item in (sorted(value) if isinstance(value, frozenset) else value)]
    return value


class StubImmune:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def answer(self):
        if "error" in self.response:
            error = self.response["error"]
            raise ImmuneEvidenceRefusal(error["code"], error["detail"])
        return ImmuneVerdict(**self.response["ok"])

    def danger_verdict(self, matches, danger, *, detector):
        self.calls.append(
            dict(port="danger", matches=wire(matches), danger=wire(danger), detector=wire(detector))
        )
        return self.answer()

    def quorum_verdict(self, readings):
        self.calls.append(dict(port="quorum", readings=wire(readings)))
        return self.answer()


def main():
    theta = OperadOperation("theta", ("Audit", "State"), "Receipt")
    phi = OperadOperation("phi", ("Ledger",), "Audit")
    wrong = OperadOperation("wrong", ("Ledger",), "Code")
    detector = DetectorIdentity("prompt-scanner", frozenset({"REPLAY_FAILURE"}), False)
    matches = (DetectorMatch("E", "核🙂", 10**90),)
    danger = HostDangerObservation(
        "PROTECTED_FIELD_VIOLATION",
        "HIGH",
        10**90,
        "sha256:" + "a" * 64,
        "host.check",
        ((10**90 + 10, 10**90 + 11),),
    )
    readings = (SensorReading("first", Fraction(1, 3)), SensorReading("second", Fraction(-5, 7)))
    replies = [
        {"ok": dict(blocks=blocks, decision="STUB", rationale="stub 核 rationale")}
        for blocks in (False, True)
    ]
    replies += [
        {"error": dict(code=code, detail=detail)}
        for code, detail in (
            ("TWO_SIGNAL_COLLAPSE", "independence failed"),
            ("UNWITNESSED_DANGER_SIGNAL", "observer missing"),
            ("UNREGISTERED_DANGER_KIND", "unknown predicate"),
            ("DUPLICATE_SENSOR", "one sensor counted twice"),
        )
    ]
    rows = []
    for op in ("danger_substitute", "quorum_substitute"):
        for index in (0, 1, -1, 10**90, True, None, "0"):
            for operation in (phi, wrong):
                for response in replies:
                    immune = StubImmune(response)
                    try:
                        if op == "danger_substitute":
                            value = immune_guarded_substitute(
                                theta,
                                index,
                                operation,
                                immune=immune,
                                detector=detector,
                                matches=matches,
                                danger=danger,
                            )
                        else:
                            value = allosteric_consensus_substitute(
                                theta, index, operation, readings, immune=immune
                            )
                        expected = {"ok": wire(value)}
                    except SubstitutionError as exc:
                        expected = {"error": {"code": exc.code, "message": str(exc)}}
                    rows.append(
                        dict(
                            op=op,
                            theta=wire(theta),
                            phi=wire(operation),
                            index=index,
                            response=response,
                            detector=wire(detector),
                            matches=wire(matches),
                            danger=wire(danger),
                            readings=wire(readings),
                            expected=expected,
                            calls=immune.calls,
                        )
                    )
    for enforce in (False, True):
        for quarantine in (False, True):
            for preexisting in (False, True):
                for response in replies:
                    report = WorkflowReport(
                        "wf",
                        theta,
                        theta if not preexisting else None,
                        (WorkflowFinding("wf", "PRIOR", "prior finding", 2, "prior-operation"),)
                        if preexisting
                        else (),
                    )
                    policy = DangerSignalPolicy(
                        enforce_danger_gate=enforce, quarantine_on_critical=quarantine
                    )
                    immune = StubImmune(response)
                    value = validate_workflow_immune_guard(
                        report,
                        policy,
                        immune=immune,
                        detector=detector,
                        matches=matches,
                        danger=danger,
                    )
                    rows.append(
                        dict(
                            op="workflow_guard",
                            report=wire(report),
                            policy=wire(policy),
                            response=response,
                            detector=wire(detector),
                            matches=wire(matches),
                            danger=wire(danger),
                            readings=wire(readings),
                            expected={"ok": wire(value)},
                            calls=immune.calls,
                        )
                    )
    root = next(parent for parent in Path(__file__).resolve().parents if (parent / ".git").exists())
    path = (
        root
        / "omega_engine/crates_rs/tests/omega_operads/fixtures/python_immune_guards_v1.json"
    )
    path.write_text(
        json.dumps({"timing": "pre-implementation", "vectors": rows}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(
        f"Frozen {len(rows)} workflow guard vectors with ordered port traces before native implementation."
    )


if __name__ == "__main__":
    main()

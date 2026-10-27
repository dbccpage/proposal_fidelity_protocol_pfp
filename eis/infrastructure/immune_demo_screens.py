"""Concrete wiring of the OEEIS screen for the MSS-N immune demos.

One implementation, used by the packaged demo
(`entrypoints/demo_4e_cogsci_autopoiesis.py`) and by
the Symbol Game catalog runner (`pfp/infrastructure/demos/named.py`):

- `screen_pharmacy_control`: the pharmacy matcher (native classes plus the
  Python persona check) on one control candidate. Signal 2 comes from the
  strict-JSON host check only: the pharmacy already evaluates host-only keys,
  so a protected-field Signal 2 would count that predicate twice.
- `screen_reply`: the regex rule for model verdict words on a model reply.
  The rule's words (verified, phi1, gamma2, certified) are themselves host-only
  keys, so a protected-field check would observe the very tokens the rule
  matches. Signal 2 for replies is therefore the strict-JSON check only; the
  host's refusal of model-authored functionals is reported separately as
  `host_refusal` and is not used as a signal. (Wiring the protected-field check
  here anyway is refused as TWO_SIGNAL_COLLAPSE by the span-overlap check.)
- `screen_farm_probe`: the farm classifier on a prose answer. No host check
  exists for prose, so Signal 2 is never present and the decision is at most
  DIAGNOSTIC_ONLY. Targeted codes with no detector (AM-FSP-6) are listed, not
  silently dropped.
"""

from __future__ import annotations

import json
from typing import Any, Mapping

from eis.use_cases.demos.demo_4e_cogsci_autopoiesis.policy import (
    PHARMACY_SELF_FIXTURES,
    REPLY_EPITOPE,
    REPLY_PATTERN,
    REPLY_RULE_ID,
    REPLY_SELF_FIXTURES,
    model_reply_defects,
)
from eis.domain.value_objects import DetectorRule
from eis.use_cases.mssn_immune import screen

from .mssn_pharmacy import DetectionContext, FailureClass
from .mssn_ports import (
    FARM_CODES,
    FARM_MATCHER_ID,
    PHARMACY_MATCHER_ID,
    FarmMatcher,
    FixedSelfPanel,
    HostPayloadDangerSensor,
    NullDangerSensor,
    PatternMatcher,
    PharmacyMatcher,
)
from .native_pharmacy import NativePharmacy


def pharmacy_rules() -> tuple[DetectorRule, ...]:
    """One rule per pharmacy failure class, bound to the pharmacy matcher."""
    return tuple(
        DetectorRule(
            "pharmacy-" + item.value, item.value, item.value, matcher_id=PHARMACY_MATCHER_ID
        )
        for item in FailureClass
    )


def reply_rule() -> DetectorRule:
    return DetectorRule(REPLY_RULE_ID, REPLY_EPITOPE, REPLY_PATTERN)


def screen_pharmacy_control(
    case: Mapping[str, Any], *, quarantine: Any, native: NativePharmacy
) -> tuple[tuple[str, ...], str, dict]:
    """Return (finding classes, subject digest, screen record) for one control."""
    matcher = PharmacyMatcher(case["context"], native=native)
    raw = json.dumps(case["candidate"], sort_keys=True)
    record = screen(
        raw,
        pharmacy_rules(),
        matcher=matcher,
        sensor=HostPayloadDangerSensor(check_protected_fields=False),
        self_panel=FixedSelfPanel(PHARMACY_SELF_FIXTURES),
        quarantine=quarantine,
        thymus_matcher=PharmacyMatcher(DetectionContext(), native=native),
    )
    report = matcher.report
    classes = tuple(finding.failure_class for finding in report.findings)
    return classes, report.subject_digest, record


def screen_reply(raw: str, *, quarantine: Any) -> dict:
    """Host refusal (policy) and the two-signal screen of one model reply."""
    defects = model_reply_defects(raw)
    record = screen(
        raw,
        (reply_rule(),),
        matcher=PatternMatcher(),
        sensor=HostPayloadDangerSensor(check_protected_fields=False),
        self_panel=FixedSelfPanel(REPLY_SELF_FIXTURES),
        quarantine=quarantine,
    )
    return {"host_refusal": defects > 0, **record}


def screen_farm_probe(probe: Any, raw: str, *, quarantine: Any) -> dict:
    """The farm classifier on one prose answer; Signal 2 is never available."""
    rules = tuple(
        DetectorRule(code, code, code, matcher_id=FARM_MATCHER_ID)
        for code in probe.targeted_antimorphisms
        if code in FARM_CODES
    )
    record = screen(
        raw,
        rules,
        matcher=FarmMatcher(probe),
        sensor=NullDangerSensor(),
        self_panel=FixedSelfPanel((probe.scripted_grounded,)),
        quarantine=quarantine,
    )
    return {
        "probe_id": probe.probe_id,
        "targeted_without_detector": [
            code for code in probe.targeted_antimorphisms if code not in FARM_CODES
        ],
        **record,
    }


__all__ = [
    "pharmacy_rules",
    "reply_rule",
    "screen_farm_probe",
    "screen_pharmacy_control",
    "screen_reply",
]

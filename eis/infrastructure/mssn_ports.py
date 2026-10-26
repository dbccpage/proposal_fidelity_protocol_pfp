"""Concrete MSS-N immune adapters; storage is scoped to a caller-owned run.

Every matcher declares the `matcher_id` rules bind to and executes the rule's
`match_pattern`:

- `PatternMatcher` (`regex`) searches the content with the rule's pattern, in
  the bounded subset of `domain.safe_pattern`;
- `PharmacyMatcher` (`pharmacy`), `FarmMatcher` (`farm-classifier`) and
  `ProtocolMatcher` (`demo3-protocol`) run a host check and select the findings
  whose code equals the rule's pattern. A pattern naming a code the check cannot
  emit is refused (`UNKNOWN_DETECTOR_CODE`), so a rule cannot claim a detector
  that does not exist.

Only `PatternMatcher` reports matches located in the content
(`reports_content_offsets`); its matches are checked against Signal 2's
evidence spans, so a token that is both a regex match and a host-only key is
refused as one signal counted twice. The other matchers report finding codes
and rely on `detector_predicates`.

Sensors (Signal 2) see the checked payload only, never the matches.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from omega_engine_epistemic_immune_system.domain.host_checks import (
    MalformedPayload,
    persona_authority_leak_loci,
    protected_field_loci,
    protected_field_spans,
    strict_json,
)
from omega_engine_epistemic_immune_system.domain.ports import (
    MatcherBindingRefusal,
    bound_rules,
)
from omega_engine_epistemic_immune_system.domain.safe_pattern import compile_safe_pattern
from omega_engine_epistemic_immune_system.domain.value_objects import (
    REGEX_MATCHER_ID,
    DangerSeverity,
    DetectorRule,
    Signal1Match,
    Signal2Danger,
)

from .mssn_pharmacy import DetectionContext
from .native_pharmacy import NATIVE_CLASS_CODES, NativePharmacy, PharmacyFinding

PHARMACY_MATCHER_ID = "pharmacy"
FARM_MATCHER_ID = "farm-classifier"
PERSONA_AUTHORITY_LEAK = "PERSONA_AUTHORITY_LEAK"
PHARMACY_CODES = frozenset(NATIVE_CLASS_CODES.values()) | {PERSONA_AUTHORITY_LEAK}
# Detector ids `mssn_classifier.classify_response` can emit. AM-FSP-6 is named
# in probe specifications but has no detector, so it is not here.
FARM_CODES = frozenset(
    {
        "AM-FSP-1-PSEUDO-PROOF",
        "AM-FSP-2-FRUSTRATED-OBSTRUCTION",
        "AM-FSP-4-ORBIT-SUM-MISMATCH",
        "AM-FSP-7-UNVERIFIED-MAJORANA-LIFT",
        "AM-FSP-8-UNIVERSAL-SOLVER-CLAIM",
    }
)


def _require_codes(
    rules: Sequence[DetectorRule], codes: frozenset[str], matcher_id: str
) -> None:
    for rule in rules:
        if rule.match_pattern not in codes:
            raise MatcherBindingRefusal(
                "UNKNOWN_DETECTOR_CODE",
                f"rule {rule.rule_id} selects {rule.match_pattern!r}, which the "
                f"{matcher_id} matcher cannot emit",
            )


def _select(
    rules: Sequence[DetectorRule], codes_in_order: Sequence[str]
) -> tuple[Signal1Match, ...]:
    return tuple(
        Signal1Match(rule.target_epitope, code, 1.0, 0)
        for code in codes_in_order
        for rule in rules
        if rule.match_pattern == code
    )


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


class PatternMatcher:
    """Case-insensitive regex search with the bounded pattern subset."""

    matcher_id = REGEX_MATCHER_ID
    detector_predicates: frozenset[str] = frozenset()
    reports_content_offsets = True

    def match_antigen(self, content, rules):
        active = bound_rules(self.matcher_id, rules)
        return tuple(
            Signal1Match(rule.target_epitope, found.group(), 1.0, found.start())
            for rule in active
            for found in compile_safe_pattern(rule.match_pattern).finditer(content)
        )


class HostPayloadDangerSensor:
    """Signal 2 from host checks on the payload: strict JSON, then protected fields.

    `check_protected_fields=False` limits the sensor to the strict-JSON check,
    for matchers that already evaluate host-only keys themselves.
    """

    def __init__(self, *, check_protected_fields: bool = True) -> None:
        if type(check_protected_fields) is not bool:
            raise TypeError("check_protected_fields must be a bool")
        self.check_protected_fields = check_protected_fields
        self.observer_id = (
            "host-payload-structure-and-protected-fields"
            if check_protected_fields
            else "host-payload-structure"
        )

    def _signal(
        self,
        kind: str,
        severity: DangerSeverity,
        loci: tuple[str, ...],
        spans: tuple[tuple[int, int], ...],
        content: str,
    ):
        evidence = json.dumps(
            {
                "kind": kind,
                "loci": list(loci),
                "observer": self.observer_id,
                "payload_sha256": _sha256(content.encode("utf-8")),
                "spans": [list(span) for span in spans],
            },
            sort_keys=True,
            ensure_ascii=True,
            separators=(",", ":"),
        ).encode("ascii")
        return Signal2Danger(
            kind, severity, len(loci), _sha256(evidence), self.observer_id, spans
        )

    def detect_danger(self, content):
        if type(content) is not str:
            raise TypeError("content must be the exact checked payload text")
        try:
            parsed = strict_json(content)
        except MalformedPayload as exc:
            return self._signal(
                "MALFORMED_PAYLOAD", DangerSeverity.MEDIUM, (exc.detail,), exc.spans, content
            )
        if not self.check_protected_fields:
            return None
        loci = protected_field_loci(parsed)
        if not loci:
            return None
        return self._signal(
            "PROTECTED_FIELD_VIOLATION",
            DangerSeverity.HIGH,
            loci,
            protected_field_spans(content),
            content,
        )


class NullDangerSensor:
    """No host check exists for this payload; Signal 2 is never reported.

    Used where the payload is free prose (the farm probes): there is nothing the
    host can check without the detector, so only Signal 1 can be present and the
    gate can only reach DIAGNOSTIC_ONLY.
    """

    observer_id = "no-host-check"

    def detect_danger(self, content):
        if type(content) is not str:
            raise TypeError("content must be the exact checked payload text")
        return None


class FixedSelfPanel:
    def __init__(self, fixtures):
        self._fixtures = tuple(fixtures)

    def get_self_fixtures(self):
        return self._fixtures


class RunQuarantineSink:
    def __init__(self, directory: Path):
        self.directory = directory

    def record_quarantine(self, rule, match, danger, disposition):
        record = {
            "rule_id": rule.rule_id,
            "epitope": match.epitope_name,
            "matched": match.pattern_matched,
            "evidence_digest": danger.evidence_digest,
            "danger_kind": danger.danger_type,
            "danger_observer": danger.observer_id,
            "disposition": disposition.value,
            "AuthorityEffect": "None",
            "permanent": True,
            "can_promote_to_core": False,
        }
        data = (
            json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
            + b"\n"
        )
        key = hashlib.sha256(data).hexdigest()
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / (key + ".json")
        if not path.exists():
            with path.open("xb") as handle:
                handle.write(data)
        elif path.read_bytes() != data:
            raise ValueError("quarantine object digest mismatch")
        return key


class PharmacyScreenReport:
    """Native pharmacy findings plus the Python persona check, for one candidate."""

    def __init__(self, subject_digest: str, findings: tuple[PharmacyFinding, ...], *, raw_bytes_digest: str | None) -> None:
        self.subject_digest = subject_digest
        self.raw_bytes_digest = raw_bytes_digest
        self.findings = findings

    def is_clean(self) -> bool:
        return not self.findings


class PharmacyMatcher:
    """Native failure classes plus the separately attributed Python persona check.

    The twelve classes run in `omega_prompt_civilization` through the host
    action `pharmacy_detect`; supplemental persona text is checked by
    `persona_authority_leak_loci`. The native self-certification and fake-receipt
    detectors inspect host-only keys, so this matcher declares the
    PROTECTED_FIELD_VIOLATION predicate: a protected-field Signal 2 would count
    that predicate twice.
    """

    matcher_id = PHARMACY_MATCHER_ID
    reports_content_offsets = False
    detector_predicates = frozenset({"PROTECTED_FIELD_VIOLATION"})

    def __init__(self, context: DetectionContext, *, native: NativePharmacy | None = None):
        if type(context) is not DetectionContext:
            raise TypeError("context must be an exact DetectionContext")
        self.context = context
        self.native = native if native is not None else NativePharmacy()
        self.report: PharmacyScreenReport | None = None

    def match_antigen(self, content, rules):
        active = bound_rules(self.matcher_id, rules)
        _require_codes(active, PHARMACY_CODES, self.matcher_id)
        native = self.native.detect(content, self.context)
        try:
            candidate = json.loads(content)
        except json.JSONDecodeError:
            candidate = content
        persona = tuple(
            PharmacyFinding(
                failure_class=PERSONA_AUTHORITY_LEAK,
                disposition="REFUSE",
                locus=locus,
                detail="persona asserting authority beyond its declared grant",
                source="python",
            )
            for locus in persona_authority_leak_loci(candidate, tuple(self.context.granted_persona_roles))
        )
        findings = tuple(
            sorted(native.findings + persona, key=lambda f: (f.failure_class, f.locus, f.detail))
        )
        self.report = PharmacyScreenReport(native.subject_digest, findings, raw_bytes_digest=native.raw_bytes_digest)
        return _select(active, [finding.failure_class for finding in findings])


class FarmMatcher:
    """Frozen farm classifier findings, selected by detector id."""

    matcher_id = FARM_MATCHER_ID
    reports_content_offsets = False
    detector_predicates: frozenset[str] = frozenset()

    def __init__(self, probe):
        self.probe = probe
        self.report = None

    def match_antigen(self, content, rules):
        from .mssn_classifier import classify_response

        active = bound_rules(self.matcher_id, rules)
        _require_codes(active, FARM_CODES, self.matcher_id)
        self.report = classify_response(self.probe, content, "fixture")
        return _select(active, [finding.detector_id for finding in self.report.findings])


DEMO3_MATCHER_ID = "demo3-protocol"
PROTOCOL_CODES = (
    "AM-3-PRECONDITION-INCOMPLETE",
    "AM-FSP-6-WRONG-ROUTE",
    "UNGROUNDED_SELF_CERTIFICATION",
)


def _element_id(move: Mapping[str, Any]) -> object:
    payload = move.get("payload")
    if type(payload) is not dict:
        return None
    return payload.get("element_id")


def protocol_findings(
    moves: Sequence[Mapping[str, Any]],
    state: object,
    fixture: Mapping[str, Any],
) -> list[str]:
    covered = getattr(state, "covered_elements", ())
    witness_candidate = getattr(state, "witness_candidate", None)
    witness_present = witness_candidate is not None or any(
        move.get("move_type") == "PROPOSE_WITNESS" for move in moves
    )
    coverage_present = (
        "elem_all" in covered
        or "elem_complete" in covered
        or any(_element_id(move) in ("elem_all", "elem_complete") for move in moves)
    )
    expected = fixture.get("expected_witness_type")
    findings: list[str] = []
    for move in moves:
        move_type = move.get("move_type")
        payload = move.get("payload")
        if type(payload) is not dict:
            payload = {}
        if move_type == "VERIFY" and (not coverage_present or not witness_present):
            findings.append("AM-3-PRECONDITION-INCOMPLETE")
        if move_type == "PROPOSE_WITNESS" and payload.get("witness_type") != expected:
            findings.append("AM-FSP-6-WRONG-ROUTE")
        if move.get("self_reported_verified") is True or payload.get("verified") is True:
            findings.append("UNGROUNDED_SELF_CERTIFICATION")
    return findings


class ProtocolMatcher:
    """The three Demo 3 host-protocol codes."""

    matcher_id = DEMO3_MATCHER_ID
    reports_content_offsets = False
    detector_predicates: frozenset[str] = frozenset()

    def __init__(self, state, fixture):
        self.state, self.fixture = state, fixture

    def match_antigen(self, content, rules):
        active = bound_rules(self.matcher_id, rules)
        _require_codes(active, frozenset(PROTOCOL_CODES), self.matcher_id)
        moves = json.loads(content)
        if type(moves) is not list or any(type(move) is not dict for move in moves):
            raise ValueError("PROTOCOL_MOVES_REQUIRED")
        return _select(active, protocol_findings(moves, self.state, self.fixture))


Demo3AntigenMatcher = ProtocolMatcher


__all__ = [
    "DEMO3_MATCHER_ID",
    "Demo3AntigenMatcher",
    "FARM_CODES",
    "FARM_MATCHER_ID",
    "FarmMatcher",
    "FixedSelfPanel",
    "HostPayloadDangerSensor",
    "NullDangerSensor",
    "PERSONA_AUTHORITY_LEAK",
    "PHARMACY_CODES",
    "PHARMACY_MATCHER_ID",
    "PROTOCOL_CODES",
    "PatternMatcher",
    "PharmacyMatcher",
    "PharmacyScreenReport",
    "ProtocolMatcher",
    "RunQuarantineSink",
    "protocol_findings",
]

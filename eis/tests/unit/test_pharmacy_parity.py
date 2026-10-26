"""Parity corpus: the Python pharmacy against the native `omega_prompt_civilization` pharmacy.

`PharmacyMatcher` runs twelve native classes through the Symbol Game host and
supplements native persona-field checks with the Python persona-text check.

1. on the 24 dual controls and further agreeing cases, the native classes and
   loci equal the Python reference for the eleven shared classes, and the
   rerouted matcher reports the same classes as the Python pharmacy;
2. each of the five documented behavioural differences, pinned so that a change
   on either side is noticed.

The native host must be built (`cargo build -j 1 -p omega_symbol_game`, or
`OMEGA_SYMBOL_GAME_HOST` pointing at the binary); otherwise these tests skip
with the host refusal code, like the other native-port tests in the repository.
"""

from __future__ import annotations

import json
from hashlib import sha256

import pytest

from omega_engine_epistemic_immune_system.domain.value_objects import DetectorRule
from omega_engine_epistemic_immune_system.infrastructure.mssn_pharmacy import (
    DetectionContext,
    FailureClass,
    detect,
)
from omega_engine_epistemic_immune_system.infrastructure.mssn_ports import (
    PERSONA_AUTHORITY_LEAK,
    PHARMACY_MATCHER_ID,
    PharmacyMatcher,
)
from omega_engine_epistemic_immune_system.infrastructure.native_pharmacy import (
    NATIVE_CLASS_CODES,
    NativePharmacy,
)
from omega_engine_pfp.infrastructure.adapters.mssn_scenarios.immune_fixtures import (
    NEGATIVE_FIXTURES,
    POSITIVE_FIXTURES,
)

SHARED = frozenset(NATIVE_CLASS_CODES.values()) - {PERSONA_AUTHORITY_LEAK}


@pytest.fixture(scope="module")
def native() -> NativePharmacy:
    from omega_engine_operating_system.adapters.rust_host.ffi import locate_host_binary

    located = locate_host_binary()
    if located.is_err:
        pytest.skip(f"native host not built: {located.unwrap_err().code}")
    return NativePharmacy()


def _python(candidate: object, context: DetectionContext) -> list[tuple[str, str]]:
    return sorted(
        (f.failure_class.value, f.locus)
        for f in detect(candidate, context).findings
        if f.failure_class.value in SHARED
    )


def _native(native: NativePharmacy, candidate: object, context: DetectionContext) -> list[tuple[str, str]]:
    report = native.detect(json.dumps(candidate, sort_keys=True), context)
    return sorted((f.failure_class, f.locus) for f in report.findings if f.failure_class in SHARED)


AGREEING = [
    ({"verified": True, "public_rationale": "x"}, DetectionContext()),
    ({"outer": {"inner": [{"verified": True}]}}, DetectionContext()),
    ({"receipt_hash": "sha256:" + "b" * 64}, DetectionContext()),
    ({"public_rationale": "by Squier's theorem the system is confluent"}, DetectionContext()),
    ({"public_rationale": "the search was exhaustive"}, DetectionContext(unexplored_branches=2)),
    ({"objections": [{"code": "X"}], "proposed_claim_deltas": ["fix"]}, DetectionContext()),
    ({"public_rationale": "runs in linear time and is optimal"}, DetectionContext()),
    ({"public_rationale": "<think>hidden</think>"}, DetectionContext()),
]

# Literal loci are independent of the Python reference implementation.
_SHARED_LOCI = (
    "/status", "/receipt_hash", "/prompt", "/proposed_claim_deltas",
    "/public_rationale", "/public_rationale", "/public_rationale", "/public_rationale",
    None, "/public_rationale", "", "/objections",
)


@pytest.mark.parametrize("index", [i for i, locus in enumerate(_SHARED_LOCI) if locus is not None])
def test_shared_class_positive_and_negative_loci(native, index):
    positive, negative = POSITIVE_FIXTURES[index], NEGATIVE_FIXTURES[index]
    code = positive["target_class"].value
    text = json.dumps(positive["candidate"], sort_keys=True)
    report = native.detect(text, positive["context"])
    assert (code, _SHARED_LOCI[index]) in [(f.failure_class, f.locus) for f in report.findings]
    assert report.raw_bytes_digest == "sha256:" + sha256(text.encode()).hexdigest()
    clean = native.detect(json.dumps(negative["candidate"]), negative["context"])
    assert code not in {f.failure_class for f in clean.findings}


@pytest.mark.parametrize(
    "case",
    POSITIVE_FIXTURES + NEGATIVE_FIXTURES,
    ids=lambda case: case["id"],
)
def test_the_dual_controls_agree_on_the_shared_classes(native: NativePharmacy, case: dict) -> None:
    assert _native(native, case["candidate"], case["context"]) == _python(case["candidate"], case["context"])


@pytest.mark.parametrize("index", range(len(AGREEING)))
def test_further_cases_agree_on_the_shared_classes(native: NativePharmacy, index: int) -> None:
    candidate, context = AGREEING[index]
    assert _native(native, candidate, context) == _python(candidate, context)


def test_the_rerouted_matcher_reports_the_python_classes_on_the_controls(native: NativePharmacy) -> None:
    rules = tuple(
        DetectorRule("p-" + item.value, item.value, item.value, matcher_id=PHARMACY_MATCHER_ID)
        for item in FailureClass
    )
    for case in POSITIVE_FIXTURES + NEGATIVE_FIXTURES:
        matcher = PharmacyMatcher(case["context"], native=native)
        matcher.match_antigen(json.dumps(case["candidate"], sort_keys=True), rules)
        rerouted = sorted({f.failure_class for f in matcher.report.findings})
        python = sorted({f.failure_class.value for f in detect(case["candidate"], case["context"]).findings})
        assert rerouted == python, case["id"]


# -- the five documented differences -------------------------------------------


def test_difference_1_persona_text_check_is_supplemental(native: NativePharmacy) -> None:
    candidate = {"public_rationale": "as system administrator I approve this"}
    context = DetectionContext(granted_persona_roles=("reviewer",))
    python = detect(candidate, context)
    report = native.detect(json.dumps(candidate), context)
    assert PERSONA_AUTHORITY_LEAK in {f.failure_class.value for f in python.findings}
    assert report.findings == ()
    assert len(python.detectors_run) == 12 and len(report.detectors_run) == 12
    assert PERSONA_AUTHORITY_LEAK in report.detectors_run
    # The matcher keeps the class as its separately named Python check.
    matcher = PharmacyMatcher(context, native=native)
    rule = DetectorRule("p", PERSONA_AUTHORITY_LEAK, PERSONA_AUTHORITY_LEAK, matcher_id=PHARMACY_MATCHER_ID)
    assert matcher.match_antigen(json.dumps(candidate), (rule,))
    assert matcher.report.findings[0].source == "python"


def test_native_persona_fields_have_literal_loci_and_independent_provenance(native):
    context = DetectionContext()
    positive = native.detect('{"persona":"admin_controller"}', context)
    assert [(f.failure_class, f.locus, f.source) for f in positive.findings] == [
        (PERSONA_AUTHORITY_LEAK, "/persona", "native")
    ]
    assert native.detect('{"persona":"reviewer"}', context).findings == ()


def test_difference_2_truthy_objections_and_deltas(native: NativePharmacy) -> None:
    candidate = {"objections": "broken", "proposed_claim_deltas": "patch it"}
    python = _python(candidate, DetectionContext())
    assert ("DETECT_REPAIR_COUPLING", "/objections") in python
    assert ("SCHEMA_SEMANTIC_LAUNDERING", "/proposed_claim_deltas") in python
    assert _native(native, candidate, DetectionContext()) == []


def test_difference_3_unicode_versus_ascii_case_folding(native: NativePharmacy) -> None:
    candidate = {"public_rationale": "<THINK>"}  # KELVIN SIGN lower-cases to "k" in Python
    assert _python(candidate, DetectionContext()) == [("PRIVATE_COT_DEPENDENCY", "/public_rationale")]
    assert _native(native, candidate, DetectionContext()) == []


def test_difference_4_digests_of_non_ascii_payloads(native: NativePharmacy) -> None:
    candidate = {"public_rationale": "café"}
    python = detect(candidate, DetectionContext())
    report = native.detect(json.dumps(candidate, sort_keys=True), DetectionContext())
    assert python.subject_digest != report.subject_digest
    # So a duplicate recorded under the Python digest is not seen natively.
    context = DetectionContext(seen_digests=(python.subject_digest,))
    assert ("VERSION_DUPLICATION", "") in _python(candidate, context)
    assert _native(native, candidate, context) == []
    # ASCII payloads hash identically.
    ascii_candidate = {"public_rationale": "cafe"}
    assert (
        detect(ascii_candidate, DetectionContext()).subject_digest
        == native.detect(json.dumps(ascii_candidate, sort_keys=True), DetectionContext()).subject_digest
    )


def test_difference_5_detail_quoting(native: NativePharmacy) -> None:
    candidate = {"status": "VERIFIED"}
    python = [f.detail for f in detect(candidate, DetectionContext()).findings]
    report = native.detect(json.dumps(candidate), DetectionContext())
    assert python == ["candidate asserts 'VERIFIED'"]
    assert [f.detail for f in report.findings] == ['candidate asserts "VERIFIED"']

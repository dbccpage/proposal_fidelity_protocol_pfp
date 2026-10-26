"""The packaged immune checker must actually classify, screen, and refuse phi1."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from omega_engine_epistemic_immune_system.use_cases.demos.demo_4e_cogsci_autopoiesis.policy import (
    DEMO_ID,
    DemoRefusal,
    model_reply_defects,
    require_control,
)
from omega_engine_epistemic_immune_system.infrastructure import immune_demo_screens
from omega_engine_epistemic_immune_system.infrastructure.mssn_pharmacy import FailureClass
from omega_engine_epistemic_immune_system.infrastructure.mssn_ports import PharmacyMatcher
from omega_engine_epistemic_immune_system.infrastructure.native_pharmacy import (
    NativePharmacy,
    NativePharmacyUnavailable,
)
from omega_engine_epistemic_immune_system.use_cases.demos.demo_4e_cogsci_autopoiesis import (
    run_packaged_immune as use_case,
)
try:
    from omega_engine_projects.mssn_sn_symgam.demos.demos_runner import run_demo_4e_cli as main
except (ImportError, ModuleNotFoundError):
    main = None

# The composition root; the use case itself imports no infrastructure.
checker = importlib.import_module(
    "omega_engine_epistemic_immune_system.entrypoints.demo_4e_cogsci_autopoiesis"
)

ROOT = Path(__file__).resolve().parents[3]
FRONTEND = (
    ROOT
    / "omega_engine_projects"
    / "mssn_sn_symgam"
    / "demos"
    / "demos_runner.py"
)
PHARMACY_RULES = {f"pharmacy-{item.value}" for item in FailureClass}


def _require_native_host() -> None:
    """The pharmacy's native classes need the built Symbol Game host."""
    from omega_engine_operating_system.adapters.rust_host.ffi import locate_host_binary

    located = locate_host_binary()
    if located.is_err:
        pytest.skip(f"native host not built: {located.unwrap_err().code}")


@pytest.fixture(autouse=True)
def _native_host(request: pytest.FixtureRequest) -> None:
    if request.node.name not in _OFFLINE_TESTS:
        _require_native_host()


_OFFLINE_TESTS = {
    "test_model_reply_defects_rejects_keys_not_prose",
    "test_require_control_rejects_int_bool_and_false_clean",
    "test_missing_native_host_is_a_typed_refusal",
    "test_gutted_matcher_cannot_certify_controls",
    "test_gutted_screen_is_not_optional",
    "test_sources_do_not_read_historical_products_or_embed_the_checker",
}


def test_model_reply_defects_rejects_keys_not_prose():
    assert model_reply_defects('{"candidate":"op<<0>>"}') == 0
    assert model_reply_defects('{"verified":true,"phi1":"0"}') == 1
    assert model_reply_defects('{"Phi_1":"0"}') == 1
    assert model_reply_defects('{"note":"verified"}') == 0
    assert model_reply_defects("not-json") == 1
    with pytest.raises(DemoRefusal, match="SCENARIO_FIXTURE_REPLIES"):
        model_reply_defects(1)  # type: ignore[arg-type]


def test_require_control_rejects_int_bool_and_false_clean():
    require_control(
        "pos",
        positive=True,
        finding_classes=("SELF_CERTIFICATION",),
        target_class="SELF_CERTIFICATION",
    )
    require_control("neg", positive=False, finding_classes=(), target_class=None)
    with pytest.raises(DemoRefusal, match="SCENARIO_CHECK_FAILED"):
        require_control("pos", positive=True, finding_classes=(), target_class="SELF_CERTIFICATION")
    with pytest.raises(DemoRefusal, match="SCENARIO_CHECK_FAILED"):
        require_control("neg", positive=False, finding_classes=("X",), target_class=None)
    with pytest.raises(DemoRefusal, match="SCENARIO_CHECK_FAILED"):
        require_control("bad", positive=1, finding_classes=(), target_class=None)  # type: ignore[arg-type]


def test_packaged_controls_screen_and_phi1_refusal(tmp_path: Path):
    """A detector match alone is DIAGNOSTIC_ONLY; only two independent signals quarantine.

    Counterexample to the old behaviour: Signal 2 used to be `len(matches)`, so
    every positive control was QUARANTINED on its detector match alone and
    DIAGNOSTIC_ONLY was unreachable for the controls.
    """
    replies = checker.packaged_replies()
    assert replies == ('{"candidate":"op<<0>>"}', '{"verified":true,"phi1":"0"}')
    result = checker.run_packaged_immune(tmp_path, replies)
    assert result["status"] == "CHECKED"
    assert result["AuthorityEffect"] == "None"
    assert len(result["cases"]) == 24
    positives = [row for row in result["cases"] if row["positive"] is True]
    negatives = [row for row in result["cases"] if row["positive"] is False]
    assert len(positives) == 12 and len(negatives) == 12
    for row in positives:
        assert type(row["clean"]) is bool and row["clean"] is False
        assert row["target_class"] in row["finding_classes"]
        assert row["immune"]["matches"], row["case_id"]
        assert row["immune"]["signal2"] is None, row["case_id"]
        assert row["immune"]["decision"] == "DIAGNOSTIC_ONLY", row["case_id"]
        assert row["immune"]["quarantine_refs"] == []
        assert set(row["immune"]["thymus_admitted"]) == PHARMACY_RULES
    for row in negatives:
        assert row["clean"] is True and row["finding_classes"] == []
        assert row["immune"]["decision"] == "TOLERATED"
        assert row["immune"]["quarantine_refs"] == []
        assert set(row["immune"]["thymus_admitted"]) == PHARMACY_RULES
    first, second = result["screens"]
    assert first["host_refusal"] is False and first["decision"] == "TOLERATED"
    assert first["matches"] == []
    # Counterexample (review): the keys "verified" and "phi1" were both the regex
    # match and the protected-field Signal 2, and the reply was QUARANTINED on one
    # token. The reply screen's Signal 2 is now the strict-JSON check only, so a
    # well-formed claim is Signal 1 plus the separate host refusal.
    assert type(second["host_refusal"]) is bool and second["host_refusal"] is True
    assert "model-verdict" in second["matches"]
    assert second["signal2"] is None
    assert second["decision"] == "DIAGNOSTIC_ONLY"
    assert not any((tmp_path / "quarantine").glob("*.json"))


def test_updated_idle_counters_are_returned_not_discarded(tmp_path: Path):
    """The screen used to compute stimulate/decay and return only rule ids."""
    result = checker.run_packaged_immune(tmp_path, checker.packaged_replies())
    after = {row["rule_id"]: row for row in result["cases"][0]["immune"]["repertoire_after"]}
    assert after["pharmacy-SELF_CERTIFICATION"]["matched"] is True
    assert after["pharmacy-SELF_CERTIFICATION"]["runs_idle"] == 0
    assert after["pharmacy-FAKE_RECEIPT"]["matched"] is False
    assert after["pharmacy-FAKE_RECEIPT"]["runs_idle"] == 1


def test_verified_prose_is_diagnostic_not_a_model_claim(tmp_path: Path):
    result = checker.run_packaged_immune(
        tmp_path,
        ('{"note":"verified"}', '{"verified":true,"phi1":"0"}', "not-json"),
    )
    prose, claim, malformed = result["screens"]
    assert prose["host_refusal"] is False
    assert prose["decision"] == "DIAGNOSTIC_ONLY"
    assert claim["host_refusal"] is True
    assert claim["decision"] == "DIAGNOSTIC_ONLY"
    # Signal 2 alone (a malformed reply, no detector match) does not lock down.
    assert malformed["host_refusal"] is True
    assert malformed["matches"] == []
    assert malformed["signal2"]["kind"] == "MALFORMED_PAYLOAD"
    assert malformed["decision"] == "DIAGNOSTIC_ONLY"


def test_two_independent_signals_still_suppress_a_reply(tmp_path: Path):
    """Suppression stays reachable: a verdict word plus a syntax fault elsewhere
    (MEDIUM severity, so DEFENSIVE_LOCKDOWN rather than QUARANTINED)."""
    truncated = '{"verified": true'
    result = checker.run_packaged_immune(tmp_path, (truncated,))
    (screen,) = result["screens"]
    assert screen["matches"] == ["model-verdict"]
    assert screen["signal2"]["kind"] == "MALFORMED_PAYLOAD"
    start, end = screen["signal2"]["evidence_spans"][0]
    assert end <= len(truncated) and start >= len('{"verified"')
    assert screen["decision"] == "DEFENSIVE_LOCKDOWN"


def test_gutted_matcher_cannot_certify_controls(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    def empty(self, content, rules):
        self.report = type("Report", (), {"findings": (), "subject_digest": "gutted"})()
        return ()

    monkeypatch.setattr(PharmacyMatcher, "match_antigen", empty)
    with pytest.raises(DemoRefusal, match="SCENARIO_CHECK_FAILED"):
        checker.run_packaged_immune(tmp_path, checker.packaged_replies())


def test_gutted_screen_is_not_optional(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    def boom_screen(*args, **kwargs):
        raise DemoRefusal("SCREEN_GUTTED")

    monkeypatch.setattr(immune_demo_screens, "screen", boom_screen)
    with pytest.raises(DemoRefusal, match="SCREEN_GUTTED"):
        checker.run_packaged_immune(tmp_path, checker.packaged_replies())


def test_missing_native_host_is_a_typed_refusal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """No silent fallback to the Python pharmacy when the native host is absent."""

    def unavailable(self, candidate_json, context):
        raise NativePharmacyUnavailable("HOST_BINARY_NOT_FOUND", "not built")

    monkeypatch.setattr(NativePharmacy, "detect", unavailable)
    with pytest.raises(DemoRefusal, match="NATIVE_PHARMACY_UNAVAILABLE"):
        checker.run_packaged_immune(tmp_path, checker.packaged_replies())


def test_gutted_model_refusal_is_not_optional(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from omega_engine_pfp.domain.demos import refuse_model_functionals

    seen: list[object] = []

    def spy(value):
        seen.append(value)
        return refuse_model_functionals(value)

    monkeypatch.setattr(
        "omega_engine_epistemic_immune_system.use_cases.demos.demo_4e_cogsci_autopoiesis.policy.refuse_model_functionals",
        spy,
    )
    result = checker.run_packaged_immune(tmp_path, checker.packaged_replies())
    assert {"verified": True, "phi1": "0"} in seen
    assert result["screens"][1]["host_refusal"] is True


def test_sources_do_not_read_historical_products_or_embed_the_checker():
    paths = [
        Path(checker.__file__),
        ROOT
        / "omega_engine_epistemic_immune_system"
        / "use_cases"
        / "demos"
        / "demo_4e_cogsci_autopoiesis"
        / "policy.py",
    ]
    if FRONTEND.is_file():
        paths.insert(0, FRONTEND)
    texts = [p.read_text(encoding="utf-8") for p in paths]
    combined = "\n".join(texts)
    for token in ("cemetery_sink_ledger", "swarm_formulary", "bout_audit", "pharmacy.rs"):
        assert token not in combined
    if FRONTEND.is_file():
        frontend = texts[0]
        for token in ("PharmacyMatcher", "refuse_model_functionals", "def screen", "immune_fixtures"):
            assert token not in frontend


def test_composition_root_run_verify_and_refusal(tmp_path: Path):
    output = tmp_path / "run"
    receipt = checker.run_demo(DEMO_ID, output)
    raw = use_case.canonical(receipt)
    report = checker.verify_receipt(raw)
    assert report == {
        "status": "VERIFIED_FIXTURE",
        "reproduced": True,
        "AuthorityEffect": "None",
        "scenario_id": DEMO_ID,
    }
    with pytest.raises(DemoRefusal, match="OUTPUT_DIRECTORY_OCCUPIED"):
        checker.run_demo(DEMO_ID, output)
    with pytest.raises(DemoRefusal, match="UNKNOWN_SCENARIO"):
        checker.run_demo("demo_eis_failure_classes", tmp_path / "other")
    research_out = tmp_path / "research" / "run"
    with pytest.raises(DemoRefusal, match="RESEARCH_EVIDENCE_WRITE_REFUSED"):
        checker.run_demo(DEMO_ID, research_out)
    assert not research_out.exists()
    tampered = json.loads(raw)
    tampered["result"]["status"] = "FAILED"
    body = {key: value for key, value in tampered.items() if key != "receipt_sha256"}
    tampered["receipt_sha256"] = use_case.digest(use_case.canonical(body))
    forged = use_case.canonical(tampered)
    with pytest.raises(DemoRefusal, match="FIXTURE_EXPECTATION_FAILED"):
        checker.verify_receipt(forged)
    untouched = bytearray(raw)
    untouched[-4] ^= 1
    with pytest.raises(DemoRefusal):
        checker.verify_receipt(bytes(untouched))


def test_the_use_case_needs_injected_wiring(tmp_path: Path):
    """The use case has no default infrastructure: calling it without wiring fails."""
    with pytest.raises(TypeError):
        use_case.run_packaged_immune(tmp_path, ("{}",))  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        use_case.run_packaged_immune(tmp_path, ("{}",), wiring=object())  # type: ignore[arg-type]


def test_project_cli_run_and_verify(tmp_path: Path):
    """The project demo runner reaches the use case through the composition root."""
    if main is None or not FRONTEND.is_file():
        pytest.skip("Legacy demos_runner CLI is retired after pilot estate decoupling")
    output = tmp_path / "run"
    assert main(["run", DEMO_ID, "--output-dir", str(output)]) == 0
    assert main(["verify", str(output / "receipt.json")]) == 0
    runner = FRONTEND.read_text(encoding="utf-8")
    assert "omega_engine_epistemic_immune_system.entrypoints.demo_4e_cogsci_autopoiesis" in runner

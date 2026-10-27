"""The farm checker must stay a native-port refusal. AuthorityEffect: None."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from eis.use_cases.demos.antimorphism_farm.contract import (
    PINNED_SCOPE,
    QuarantineRecord,
    refusal_evidence_body,
)
from eis.use_cases.demos.antimorphism_farm.run import (
    _preferred_native_port,
    assemble_run,
    run_antimorphism_farm,
    verify_receipt,
)
try:
    from projects.mssn_sn_symgam.demos.demos_runner import (
        run_antimorphism_farm_cli as main,
        write_run_antimorphism_farm as write_run,
    )
except (ImportError, ModuleNotFoundError):
    main = None
    write_run = None
from pfp.domain.demos import DemoRefusal
from pfp.infrastructure.demos.canonical import canonical, digest, load

ROOT = Path(__file__).resolve().parents[3]
PACKAGED = (
    ROOT
    / "pfp"
    / "infrastructure"
    / "adapters"
    / "mssn_research"
    / "fixtures"
    / "antimorphism_farm.json"
)
EXPECTED_DETAIL = (
    "pharmacy_detect exists but the farm does not delegate to it; "
    "farm regex has no native port; "
    "24 pharmacy controls and 6 farm probes are not split on farm_probes"
)
EXPECTED_EVIDENCE = {
    "AuthorityEffect": "None",
    "code": "NO_NATIVE_PORT",
    "demo_id": "antimorphism_farm",
    "farm_probe_count": 6,
    "farm_probes_are_a_gate": False,
    "pharmacy_controls": 24,
}


def _fixture(farm_probes: bool) -> dict[str, object]:
    return {
        "kind": "immune",
        "farm_probes": farm_probes,
        "replies": ["scripted reply withheld from classification"],
        "immune_replies": ['{"candidate":"op<<0>>"}'],
        "scope": PINNED_SCOPE,
    }


def test_both_probe_flags_refuse_the_same_unsplit_screen() -> None:
    assert _preferred_native_port() == "pharmacy_detect"
    details = []
    for flag in (True, False):
        with pytest.raises(DemoRefusal) as caught:
            run_antimorphism_farm(_fixture(flag))
        assert caught.value.code == "NO_NATIVE_PORT"
        details.append(caught.value.detail)
    assert details == [EXPECTED_DETAIL, EXPECTED_DETAIL]


def test_packaged_fixture_is_refused_without_a_checked_result() -> None:
    fixture = load(PACKAGED.read_bytes())
    assert fixture["farm_probes"] is True
    with pytest.raises(DemoRefusal) as caught:
        run_antimorphism_farm(fixture)
    assert caught.value.code == "NO_NATIVE_PORT"
    assert caught.value.detail == EXPECTED_DETAIL
    flipped = dict(fixture)
    flipped["farm_probes"] = False
    with pytest.raises(DemoRefusal) as again:
        run_antimorphism_farm(flipped)
    assert again.value.detail == caught.value.detail


def test_farm_probes_rejects_integer_bool_and_model_keys() -> None:
    for probe in (0, 1):
        forged = _fixture(True)
        forged["farm_probes"] = probe
        with pytest.raises(DemoRefusal) as caught:
            run_antimorphism_farm(forged)
        assert caught.value.code == "INVALID_FIXTURE"
    claimed = _fixture(True)
    claimed["verified"] = True
    with pytest.raises(DemoRefusal) as claimed_error:
        run_antimorphism_farm(claimed)
    assert claimed_error.value.code == "MODEL_FUNCTIONAL_CLAIM"


def test_quarantine_rejects_integer_promotion_flags() -> None:
    digest_hex = "a" * 64
    for flag in (0, 1):
        with pytest.raises(DemoRefusal) as caught:
            QuarantineRecord(
                rule_id="antimorphism_farm",
                epitope="NO_NATIVE_PORT",
                matched="NO_NATIVE_PORT",
                evidence_digest=digest_hex,
                disposition="QUARANTINED",
                AuthorityEffect="None",
                permanent=True,
                can_promote_to_core=flag,  # type: ignore[arg-type]
            )
        assert caught.value.code == "PROMOTION_REFUSED"
    for flag in (0, 1):
        with pytest.raises(DemoRefusal) as caught:
            QuarantineRecord(
                rule_id="antimorphism_farm",
                epitope="NO_NATIVE_PORT",
                matched="NO_NATIVE_PORT",
                evidence_digest=digest_hex,
                disposition="QUARANTINED",
                AuthorityEffect="None",
                permanent=flag,  # type: ignore[arg-type]
                can_promote_to_core=False,
            )
        assert caught.value.code == "PROMOTION_REFUSED"


def test_sources_do_not_call_or_import_python_copies() -> None:
    import inspect
    paths = [
        ROOT.joinpath(
            "eis",
            "use_cases",
            "demos",
            "antimorphism_farm",
            "contract.py",
        ),
        ROOT.joinpath(
            "eis",
            "use_cases",
            "demos",
            "antimorphism_farm",
            "run.py",
        ),
    ]
    texts = [path.read_text(encoding="utf-8") for path in paths]
    if main is not None:
        texts.append(inspect.getsource(main))
    for text in texts:
        assert "mssn_pharmacy" not in text
        assert "mssn_classifier" not in text
        assert "mssn_immune" not in text
        assert "antimorphism_harvest" not in text
        assert "classify_response(" not in text
        assert ".detect(" not in text
        assert ".screen(" not in text
        tree = ast.parse(text)
        imported: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module)
            elif isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
        assert all("infrastructure.immune" not in name for name in imported)


def test_python_copies_are_not_invoked(monkeypatch: pytest.MonkeyPatch) -> None:
    import eis.infrastructure.mssn_classifier as classifier
    import eis.infrastructure.mssn_pharmacy as pharmacy
    import eis.use_cases.mssn_immune as immune

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("python copy invoked")

    monkeypatch.setattr(classifier, "classify_response", forbidden)
    monkeypatch.setattr(pharmacy, "detect", forbidden)
    monkeypatch.setattr(immune, "screen", forbidden)
    with pytest.raises(DemoRefusal) as caught:
        run_antimorphism_farm(_fixture(True))
    assert caught.value.code == "NO_NATIVE_PORT"


def test_front_end_writes_refusal_and_verify_rejects_checked(tmp_path: Path) -> None:
    if main is None:
        pytest.skip("Legacy demos_runner CLI is retired after pilot estate decoupling")
    output = tmp_path / "antimorphism_farm"
    assert main(["run", "--output-dir", str(output)]) == 0
    receipt_path = output / "receipt.json"
    fixture_bytes = (output / "fixture.json").read_bytes()
    trace = (output / "trace.jsonl").read_bytes()
    transcript = (output / "transcript.json").read_bytes()
    quarantine = list((output / "quarantine").glob("*.json"))
    assert fixture_bytes and trace and transcript
    assert len(quarantine) == 1
    receipt = load(receipt_path.read_bytes())
    assert receipt["schema"] == "core.symbol-game.demo-receipt.v1"
    assert receipt["AuthorityEffect"] == "None"
    assert receipt["result"]["status"] == "TYPED_REFUSAL"
    assert receipt["result"]["code"] == "NO_NATIVE_PORT"
    assert receipt["result"]["detail"] == EXPECTED_DETAIL
    assert receipt["transport"] == "fixture"
    assert receipt["verification_scope"] == "fixture_replay"
    record = load(quarantine[0].read_bytes())
    assert record["can_promote_to_core"] is False
    assert type(record["can_promote_to_core"]) is bool
    assert type(record["permanent"]) is bool and record["permanent"] is True
    assert record["AuthorityEffect"] == "None"
    assert record["evidence_digest"] == digest(canonical(EXPECTED_EVIDENCE))
    assert refusal_evidence_body()["farm_probes_are_a_gate"] is False
    verdict = verify_receipt(receipt_path)
    assert verdict == {
        "status": "VERIFIED_REFUSAL",
        "reproduced": True,
        "AuthorityEffect": "None",
        "scenario_id": "antimorphism_farm",
        "outcome": "TYPED_REFUSAL",
    }
    assert verdict["outcome"] != "CHECKED"
    receipt["result"]["status"] = "CHECKED"
    receipt["result"]["code"] = None
    unsigned = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    receipt["receipt_sha256"] = digest(canonical(unsigned))
    receipt_path.write_bytes(canonical(receipt))
    with pytest.raises(DemoRefusal) as caught:
        verify_receipt(receipt_path)
    assert caught.value.code == "CHECKED_REJECTED"


def test_front_end_refuses_checked_bundle_and_research_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    if write_run is None:
        pytest.skip("Legacy demos_runner CLI is retired after pilot estate decoupling")
    import projects.mssn_sn_symgam.demos.demos_runner as front

    def checked(_fixture: object) -> object:
        return type("Bundle", (), {"result": {"status": "CHECKED", "code": "NO_NATIVE_PORT"}})()

    monkeypatch.setattr(front, "assemble_run", checked)
    with pytest.raises(DemoRefusal) as caught:
        front.write_run(front.DEFAULT_FIXTURE, tmp_path / "checked")
    assert caught.value.code == "CHECKED_REJECTED"
    assert not (tmp_path / "checked").exists()
    monkeypatch.undo()
    with pytest.raises(DemoRefusal) as research:
        write_run(front.DEFAULT_FIXTURE, tmp_path / "research" / "run")
    assert research.value.code == "RESEARCH_EVIDENCE_WRITE_REFUSED"
    first = tmp_path / "occupied"
    write_run(front.DEFAULT_FIXTURE, first)
    with pytest.raises(DemoRefusal) as occupied:
        write_run(front.DEFAULT_FIXTURE, first)
    assert occupied.value.code == "OUTPUT_DIRECTORY_OCCUPIED"


def test_research_demo_remains() -> None:
    path = ROOT / "research" / "mssn_sn_tower" / "demos" / "antimorphism_farm" / "immune_bench.py"
    if not path.is_file():
        path = ROOT / "eis" / "infrastructure" / "immune_bench.py"
    text = path.read_text(encoding="utf-8")
    assert "class AntimorphismImmuneBench" in text
    bundle = assemble_run(_fixture(False))
    assert bundle.result["status"] == "TYPED_REFUSAL"
    assert bundle.result["code"] == "NO_NATIVE_PORT"

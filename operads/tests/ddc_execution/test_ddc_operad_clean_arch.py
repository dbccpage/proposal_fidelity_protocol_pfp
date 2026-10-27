#!/usr/bin/env python3
"""Tests for Clean Architecture DDC Operad components.

Verifies:
1. DdcRecord domain value object, Merkle chaining, and candidate runtime laws.
2. ParseDdcTapeUseCase execution and receipt persistence.
3. DdcOperad CLI invocation.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path

import pytest

from operads.application.ddc_execution.parse_ddc_tape_use_case import (
    ParseDdcTapeRequest,
)
from operads.domain.ddc_execution.ddc_step import (
    DdcRecord,
    verify_ddc_candidate_laws,
    verify_merkle_chain,
)
from operads.frontend.cli.ddc_operad_cli import main as cli_main
from operads.infrastructure.ddc_execution.ddc_tape import (
    FileDdcReceiptStorage,
    build_parse_ddc_tape_use_case,
)


def _build_synthetic_records(steps_data: list[dict]) -> tuple[list[dict], list[DdcRecord]]:
    json_recs = []
    domain_recs = []
    head: str | None = None
    for seq, data in enumerate(steps_data):
        payload = {k: data[k] for k in sorted(data.keys(), key=lambda s: s.encode("utf-8"))}
        material = json.dumps(
            {"sequence": seq, "parent_sha256": head, "payload": payload},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        rec_sha = hashlib.sha256(material).hexdigest()

        json_recs.append(
            {
                "sequence": seq,
                "parent_sha256": head,
                "payload": payload,
                "record_sha256": rec_sha,
            }
        )

        phi_val = (
            Fraction(payload["phi_1"])
            if "phi_1" in payload and payload["phi_1"] is not None
            else None
        )
        gamma_val = (
            Fraction(payload["gamma_2"])
            if "gamma_2" in payload and payload["gamma_2"] is not None
            else None
        )

        domain_recs.append(
            DdcRecord(
                sequence=seq,
                letter=payload.get("letter", "C"),
                parent_sha256=head,
                record_sha256=rec_sha,
                carrier_hash=payload.get("carrier_hash", "c0"),
                phi_1=phi_val,
                gamma_2=gamma_val,
                payload=payload,
            )
        )
        head = rec_sha
    return json_recs, domain_recs


def test_ddc_domain_merkle_and_laws_success() -> None:
    steps = [
        {"letter": "C", "carrier_hash": "c1", "phi_1": "1/2", "gamma_2": "0"},
        {"letter": "R", "carrier_hash": "c1", "phi_1": "1/2", "gamma_2": "0"},
        {"letter": "E", "carrier_hash": "c1", "phi_1": "0", "gamma_2": "0"},
        {"letter": "I", "carrier_hash": "c1", "phi_1": "0", "gamma_2": "0", "has_receipt": True},
        {"letter": "T", "carrier_hash": "c1", "phi_1": "0", "gamma_2": "0"},
    ]
    _, domain_recs = _build_synthetic_records(steps)

    merkle_valid, merkle_errs = verify_merkle_chain(domain_recs)
    assert merkle_valid, f"Merkle chain errors: {merkle_errs}"

    laws_valid, law_errs = verify_ddc_candidate_laws(domain_recs)
    assert laws_valid, f"Candidate runtime law violations: {law_errs}"


def test_ddc_domain_law_violations() -> None:
    # 1. Step after T violates Law 2
    steps = [
        {"letter": "C", "carrier_hash": "c1"},
        {"letter": "T", "carrier_hash": "c1"},
        {"letter": "R", "carrier_hash": "c1"},
    ]
    _, domain_recs = _build_synthetic_records(steps)
    valid, violations = verify_ddc_candidate_laws(domain_recs)
    assert not valid
    assert any("TerminalAbsorbing" in v for v in violations)


def test_parse_ddc_tape_use_case(tmp_path: Path) -> None:
    steps = [
        {"letter": "C", "carrier_hash": "c1", "phi_1": "1/2", "gamma_2": "0"},
        {"letter": "R", "carrier_hash": "c1", "phi_1": "1/2", "gamma_2": "0"},
        {"letter": "E", "carrier_hash": "c1", "phi_1": "0", "gamma_2": "0"},
        {"letter": "I", "carrier_hash": "c1", "phi_1": "0", "gamma_2": "0", "has_receipt": True},
        {"letter": "T", "carrier_hash": "c1", "phi_1": "0", "gamma_2": "0"},
    ]
    json_recs, _ = _build_synthetic_records(steps)

    tape_file = tmp_path / "ddc.jsonl"
    with open(tape_file, "w", encoding="utf-8") as f:
        for r in json_recs:
            f.write(json.dumps(r) + "\n")

    use_case = build_parse_ddc_tape_use_case(default_vault_dir=tmp_path / "vault")
    receipt_dest = tmp_path / "out_receipt.json"

    req = ParseDdcTapeRequest(source=tape_file, output_receipt_path=receipt_dest)
    res = use_case.execute(req)
    assert res.is_ok
    resp = res.unwrap()
    assert resp.status == "SUCCESS"
    assert resp.receipt.residual_effect == "exact"
    assert receipt_dest.is_file()


def test_ddc_operad_cli_execution(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    steps = [
        {"letter": "C", "carrier_hash": "c1", "phi_1": "1", "gamma_2": "0"},
        {"letter": "R", "carrier_hash": "c1", "phi_1": "1", "gamma_2": "0"},
        {"letter": "T", "carrier_hash": "c1", "phi_1": "1", "gamma_2": "0"},
    ]
    json_recs, _ = _build_synthetic_records(steps)
    tape_file = tmp_path / "ddc.jsonl"
    tape_file.write_text("\n".join(json.dumps(r) for r in json_recs) + "\n", encoding="utf-8")

    receipt_out = tmp_path / "cli_receipt.json"
    exit_code = cli_main(["parse", "--tape", str(tape_file), "--output-receipt", str(receipt_out)])
    assert exit_code == 0
    assert receipt_out.is_file()

    captured = capsys.readouterr()
    assert "DDC TAPE TO COLORED OPERAD COMPOSITION RECEIPT" in captured.out
    assert "Rune Sequence   : C.R.T" in captured.out


def _custody_input(tmp_path: Path) -> Path:
    records, _ = _build_synthetic_records([
        {"letter": "C", "carrier_hash": "c1", "phi_1": "1", "gamma_2": "0"},
        {"letter": "T", "carrier_hash": "c1", "phi_1": "1", "gamma_2": "0"},
    ])
    path = tmp_path / "custody_input.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in records), encoding="utf-8")
    return path


def test_default_ddc_receipt_uses_resolved_repository_not_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    cwd = tmp_path / "other-working-directory"
    cwd.mkdir()
    monkeypatch.setenv("CORE_INTELLIGENCE_ROOT", str(root))
    monkeypatch.chdir(cwd)
    result = build_parse_ddc_tape_use_case().execute(ParseDdcTapeRequest(
        source=str(_custody_input(tmp_path)), persist_evidence=True,
    ))
    assert result.is_ok
    response = result.unwrap()
    target = Path(response.evidence_path)
    assert target.parent == root / "_ic/nara/legacy/evidence/ddc_operad_receipts"
    assert json.loads(target.read_bytes()) == response.receipt.to_dict()
    assert not (cwd / "_ic").exists()
    assert not (root / "_intelligence").exists()


def test_explicit_ddc_export_remains_independent_of_bad_ic_activation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repository"
    marker = root / "_ic/odni/migration/activation.json"
    marker.parent.mkdir(parents=True)
    marker.write_bytes(b"{}")
    monkeypatch.setenv("CORE_INTELLIGENCE_ROOT", str(root))
    export = tmp_path / "export/receipt.json"
    result = build_parse_ddc_tape_use_case().execute(ParseDdcTapeRequest(
        source=str(_custody_input(tmp_path)), output_receipt_path=str(export),
    ))
    assert result.is_ok
    assert json.loads(export.read_bytes()) == result.unwrap().receipt.to_dict()
    assert marker.read_bytes() == b"{}"
    assert not (root / "_ic/nara").exists()


def test_default_ddc_obstructed_root_is_typed_without_touching_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "not-a-directory"
    root.write_bytes(b"retain obstruction")
    monkeypatch.setenv("CORE_INTELLIGENCE_ROOT", str(root))
    cwd = tmp_path / "other-working-directory"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    result = build_parse_ddc_tape_use_case().execute(ParseDdcTapeRequest(
        source=str(_custody_input(tmp_path)), persist_evidence=True,
    ))
    assert result.is_err
    assert result.error.code == "EVIDENCE_EXPORT_ERROR"
    assert root.read_bytes() == b"retain obstruction"
    assert not list(cwd.iterdir())


@pytest.mark.parametrize("after_destination", [False, True])
def test_default_ddc_receipt_refuses_bad_activation_without_writes_then_recovers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, after_destination: bool,
) -> None:
    root = tmp_path / "repository"
    root.mkdir()
    cwd = tmp_path / "other-working-directory"
    cwd.mkdir()
    monkeypatch.setenv("CORE_INTELLIGENCE_ROOT", str(root))
    monkeypatch.chdir(cwd)
    source = _custody_input(tmp_path)
    use_case = build_parse_ddc_tape_use_case()
    parsed = use_case.execute(ParseDdcTapeRequest(source=str(source)))
    assert parsed.is_ok
    receipt = parsed.unwrap().receipt
    storage = FileDdcReceiptStorage()
    destination = storage.destination(receipt.run_id, None, None) if after_destination else None
    marker = root / "_ic/odni/migration/activation.json"
    marker.parent.mkdir(parents=True)
    marker.write_bytes(b"{}")
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    if after_destination:
        result = storage.persist(receipt, destination)
    else:
        result = use_case.execute(ParseDdcTapeRequest(source=str(source), persist_evidence=True))
    assert result.is_err
    assert result.error.code == "ACTIVATION_INVALID"
    assert {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()} == before
    marker.unlink()
    recovered = use_case.execute(ParseDdcTapeRequest(source=str(source), persist_evidence=True))
    assert recovered.is_ok
    response = recovered.unwrap()
    target = Path(response.evidence_path)
    assert target.parent == root / "_ic/nara/legacy/evidence/ddc_operad_receipts"
    assert json.loads(target.read_bytes()) == response.receipt.to_dict()
    assert not (cwd / "_ic").exists()


def test_ddc_all_candidate_laws_violations_and_edge_cases() -> None:
    """Cover all runtime law violations, negative branches, and deprecation triggers in ddc_step."""
    import warnings

    from operads.domain.ddc_execution.ddc_step import (
        DDC_SHIM_DEPRECATED_REFUSAL,
    )

    assert DDC_SHIM_DEPRECATED_REFUSAL.code == "DDC_OPERATIONS_SHIM_DEPRECATED"

    # Deprecation warnings emitted on record instantiation and verification
    with warnings.catch_warnings(record=True) as recorded:
        warnings.simplefilter("always")
        r0 = DdcRecord(
            sequence=0,
            letter="C",
            parent_sha256=None,
            record_sha256="abc",
            carrier_hash="c0",
            phi_1=None,
            gamma_2=None,
            payload={},
        )
        assert any(issubclass(w.category, DeprecationWarning) for w in recorded)

    # Unknown rune raises ValueError
    with pytest.raises(ValueError, match="Unknown DDC rune"):
        DdcRecord(
            sequence=0,
            letter="Z",
            parent_sha256=None,
            record_sha256="abc",
            carrier_hash="c0",
            phi_1=None,
            gamma_2=None,
            payload={},
        )

    # total_residual is None when both phi_1 and gamma_2 are None
    assert r0.total_residual is None

    # Equality with non-record and hash
    assert r0 != "not_a_record"
    assert (r0 == 456) is False
    assert hash(r0) is not None

    # Merkle chain violations: sequence mismatch, broken parent link, bad hash
    bad_merkle = [
        DdcRecord(0, "C", None, "bad_hash_0", "c0", Fraction(1), Fraction(0), {}),
        DdcRecord(2, "R", "wrong_parent", "bad_hash_1", "c0", Fraction(1), Fraction(0), {}),
    ]
    m_valid, m_errs = verify_merkle_chain(bad_merkle)
    assert not m_valid
    assert any("sequence number mismatch" in e for e in m_errs)
    assert any("broken parent hash link" in e for e in m_errs)
    assert any("record hash mismatch" in e for e in m_errs)

    # Law 2: Terminalization with gamma_2 > 0
    law2_recs = [
        DdcRecord(0, "T", None, "h0", "c0", Fraction(0), Fraction(1), {}),
    ]
    v, errs = verify_ddc_candidate_laws(law2_recs)
    assert not v
    assert any("TerminalizedOpenResidual" in e for e in errs)

    # Law 3: Step during active refusal and missing refusal reason
    law3_recs = [
        DdcRecord(0, "M", None, "h0", "c0", Fraction(1), Fraction(1), {}),
        DdcRecord(1, "R", "h0", "h1", "c0", Fraction(1), Fraction(1), {}),
    ]
    v, errs = verify_ddc_candidate_laws(law3_recs)
    assert not v
    assert any("MissingRefusalReason" in e for e in errs)
    assert any("RefusalAbsorbing" in e for e in errs)

    # Law 4: Structural lift without lift trigger, or missing licensed context
    law4_recs = [
        DdcRecord(0, "C", None, "h0", "c0", Fraction(0), Fraction(1), {}),
        DdcRecord(1, "Λ", "h0", "h1", "c0", Fraction(1), Fraction(0), {}),
    ]
    v, errs = verify_ddc_candidate_laws(law4_recs)
    assert not v
    assert any("LiftWithoutTrigger" in e for e in errs)
    assert any("UnlicensedLift" in e for e in errs)

    # Law 5: Integration without receipt
    law5_recs = [
        DdcRecord(0, "I", None, "h0", "c0", Fraction(0), Fraction(0), {}),
    ]
    v, errs = verify_ddc_candidate_laws(law5_recs)
    assert not v
    assert any("MissingReceipt" in e for e in errs)

    # Law 6: Scale descent without loss ledger
    law6_recs = [
        DdcRecord(0, "D", None, "h0", "c0", Fraction(0), Fraction(0), {}),
    ]
    v, errs = verify_ddc_candidate_laws(law6_recs)
    assert not v
    assert any("MissingLossLedger" in e for e in errs)

    # Law 7: Exact repair increasing phi_1 or gamma_2
    law7_recs = [
        DdcRecord(0, "C", None, "h0", "c0", Fraction(1), Fraction(0), {}),
        DdcRecord(1, "E", "h0", "h1", "c0", Fraction(2), Fraction(1), {}),
    ]
    v, errs = verify_ddc_candidate_laws(law7_recs)
    assert not v
    assert any("ExactRepairIncreasedPhi1" in e for e in errs)
    assert any("ExactRepairIncreasedGamma2" in e for e in errs)

    # Law 8: Context exposure lowering phi_1
    law8_recs = [
        DdcRecord(0, "C", None, "h0", "c0", Fraction(2), Fraction(0), {}),
        DdcRecord(1, "C", "h0", "h1", "c0", Fraction(1), Fraction(0), {}),
    ]
    v, errs = verify_ddc_candidate_laws(law8_recs)
    assert not v
    assert any("ContextExposureLoweredPhi1" in e for e in errs)

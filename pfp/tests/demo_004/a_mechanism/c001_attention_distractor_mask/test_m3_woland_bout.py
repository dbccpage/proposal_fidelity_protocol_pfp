"""
test_m3_woland_bout.py — Targeted verification suite for Milestone 3.

Verifies:
1. 7-Act CommonMark structure, persona headers and the measured-values table in novella.md.
2. Hash-chained integrity of dda_actions.jsonl (sequence, parent_sha256, record_sha256).
3. Reverse Write Order Protocol and cryptographic binding in receipt.json.
4. Witness dominance: 'E' needs a measured, exact Gamma_2 equal to 0.
5. 9-dot gauge break: carrier lift adding bridge node '9'.
6. Label REFERENCE_SELF_CONSISTENT (scope REFERENCE_SOLVER_SELF_CHECK) with exact Phi_1 = Gamma_2 = "0".
7. The bundle is written to a pytest tmp_path, or to the intelligence root only.
8. Strict Claim Hygiene: zero forbidden hype verbs in summary.json claim discipline.
9. Pure UTF-8 encoding without BOM across all quad bundle artifacts.
10. Custody: an existing run folder is never replaced; a failed write leaves a failure receipt.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest
from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask import (
    run_woland_bout as bout,
)
from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.case_generator import (
    generate_mutation_cases,
)
from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.run_woland_bout import (
    DDC_LETTERS,
    GATE_SCOPE,
    RECEIPT_SCHEMA,
    TASK_KEY,
    TERMINAL_REFERENCE_SELF_CONSISTENT,
    assert_witness_dominance,
    build_c001_ddc_action_tape,
    execute_9dot_gauge_break,
    persist_quad_bundle,
    run_woland_c001_bout,
)
from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.solver import (
    ConstraintSystem,
    extract_contradiction_cycle,
    format_int,
    is_canonical_int_str,
    parse_int_exact,
    solve_single_repair,
)

BUNDLE_FILES = ("novella.md", "dda_actions.jsonl", "summary.json", "receipt.json")


@pytest.fixture(scope="module")
def pilot_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Run the bout once into a pytest temporary folder (never the real run store)."""
    target = tmp_path_factory.mktemp("c001_bout") / "pilot"
    res = run_woland_c001_bout(custom_run_dir=target)
    assert res.is_ok, res
    return target


def test_preserved_files_exist_in_c001_mechanism_pilot(pilot_dir: Path) -> None:
    """Verifies that all 4 canonical StructureBench files exist in the run folder."""
    for fname in BUNDLE_FILES:
        fpath = pilot_dir / fname
        assert fpath.is_file(), f"Missing required artifact {fname} in {pilot_dir}"
        assert fpath.stat().st_size > 0, f"Artifact {fname} in {pilot_dir} is empty"


def test_7act_commonmark_structure_and_bulgakovian_headers(pilot_dir: Path) -> None:
    """Verifies 7-Act structure, scene titles, persona and the scope statement in novella.md."""
    content = (pilot_dir / "novella.md").read_text(encoding="utf-8")

    expected_acts = [
        "## Act I: Patriarchs' Ponds — The Cold Pre-filter",
        "## Act II: The Griboedov Restaurant — Cache & Compute Allocation",
        "## Act III: Dr. Stravinsky's Clinic — Loop Quarantine",
        "## Act IV: The Variety Theatre — Adversarial Dialectic Performance & 9-Dot Gauge Break",
        "## Act V: Apartment No. 50 — Epistemic Grounding & Refusal Semantics",
        "## Act VI: The Great Ball at Satan's — Truth Firewall & Claim Hygiene",
        "## Act VII: Satan's Gate — Terminal Adjudication & The Manuscripts Don't Burn",
    ]
    for act_header in expected_acts:
        assert act_header in content, f"Missing expected Act header: {act_header}"

    assert "Рукописи не горят" in content
    assert "Свежесть бывает только одна" in content
    assert "Трусость — самый страшный порок" in content
    assert "Воланд" in content or "Woland" in content
    assert "Terminal Reality Gatekeeper" in content
    assert "9-Dot Gauge Break" in content
    assert "## Measured values" in content
    assert "this is not a Woland verdict" in content


def test_hash_chained_dda_actions_tape_integrity(pilot_dir: Path) -> None:
    """Verifies cryptographic hash chain and DDC operational alphabet in dda_actions.jsonl."""
    lines = [
        line.strip()
        for line in (pilot_dir / "dda_actions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(lines) >= 7, f"Expected at least 7 DDC steps, found {len(lines)}"

    observed_letters: set[str] = set()
    prev_record_sha256: str | None = None

    for idx, raw_line in enumerate(lines):
        record: dict[str, Any] = json.loads(raw_line)
        assert record["sequence"] == idx
        if idx == 0:
            assert record["parent_sha256"] is None
        else:
            assert record["parent_sha256"] == prev_record_sha256

        payload = record["payload"]
        letter = payload.get("letter")
        assert letter in DDC_LETTERS, f"Line {idx}: invalid DDC letter: {letter}"
        observed_letters.add(letter)

        sorted_payload = {
            k: payload[k] for k in sorted(payload.keys(), key=lambda s: s.encode("utf-8"))
        }
        material = json.dumps(
            {"parent_sha256": record["parent_sha256"], "payload": sorted_payload, "sequence": idx},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        assert record["record_sha256"] == hashlib.sha256(material).hexdigest()
        prev_record_sha256 = record["record_sha256"]

    missing = {"E", "R", "C", "I", "Λ", "D", "M", "T"} - observed_letters
    assert not missing, f"Missing required DDC runes in action tape: {missing}"


def test_witness_dominance_law_gamma2_prevents_e(tmp_path: Path) -> None:
    """A non-zero exact Gamma_2 prevents 'E'; persistence refuses such a step before writing anything."""
    res_violation = assert_witness_dominance("E", gamma2=1)
    assert res_violation.is_err
    assert res_violation.unwrap_err().code == "WITNESS_DOMINANCE_VIOLATION"

    assert assert_witness_dominance("E", gamma2=0).is_ok
    assert assert_witness_dominance("R", gamma2=1).is_ok

    temp_target = tmp_path / "illegal_test_dir"
    persist_res = persist_quad_bundle(
        target_dir=temp_target,
        task_key="illegal_test",
        novella_md="# Fake",
        dda_steps=[{"act": "Act III", "gamma2": 1, "letter": "E", "name": "False Exact Repair"}],
        summary_data={},
        receipt_data={},
    )
    assert persist_res.is_err
    assert persist_res.unwrap_err().code == "WITNESS_DOMINANCE_VIOLATION"
    assert not temp_target.exists()


def test_float_and_bool_defect_values_are_refused() -> None:
    """Counterexample: the old gate accepted float gamma2=0.0 as an exact zero (and True as 1.0)."""
    for bad in (0.0, 1e-9, True, False, "0.0", "1/1"):
        res = assert_witness_dominance("E", bad)
        assert res.is_err, f"non-exact gamma2 {bad!r} was accepted"
        assert res.unwrap_err().code == "NON_EXACT_DEFECT_VALUE"
    assert assert_witness_dominance("R", 1.5).unwrap_err().code == "NON_EXACT_DEFECT_VALUE"
    assert assert_witness_dominance("E", "0").is_ok
    assert assert_witness_dominance("E", Fraction(0)).is_ok


def test_unmeasured_gamma2_refuses_e(tmp_path: Path) -> None:
    """Counterexample: the old persistence defaulted a missing gamma2 to 0.0 and sealed rune 'E'."""
    assert assert_witness_dominance("E", None).unwrap_err().code == "WITNESS_DOMINANCE_UNMEASURED"
    target = tmp_path / "e_without_gamma2"
    res = persist_quad_bundle(
        target_dir=target,
        task_key="e_without_gamma2",
        novella_md="# Test",
        dda_steps=[{"letter": "E", "name": "Exact repair with no measured Gamma_2"}],
        summary_data={},
        receipt_data={},
    )
    assert res.is_err
    assert res.unwrap_err().code == "WITNESS_DOMINANCE_UNMEASURED"
    assert not target.exists()


def test_tape_refuses_e_when_repair_left_a_contradiction() -> None:
    """Counterexample: the old tape wrote rune 'E' with a constant gamma2 = 0.0 even when the
    'repaired' system was still contradictory."""
    items = ["A", "B", "C"]
    edges = [("A", "B", 1), ("B", "C", 1), ("C", "A", 1)]
    claims = {("A", "B"): 1, ("B", "C"): 1, ("C", "A"): -3}
    contradictory = ConstraintSystem(items=items, edges=edges, claims=claims)
    cycle = extract_contradiction_cycle(contradictory)
    assert cycle is not None
    lifted = execute_9dot_gauge_break(contradictory)

    tape = build_c001_ddc_action_tape(
        system=contradictory,
        repaired_system=contradictory,
        contradiction_cycle=cycle,
        repair_edge=("A", "B"),
        repair_val="2",
        danger_decision="QUARANTINED",
        lifted=lifted,
    )
    assert tape.is_err
    assert tape.unwrap_err().code == "WITNESS_DOMINANCE_UNMEASURED"


def test_tape_defect_values_are_measured_exact_strings() -> None:
    """The 'E' step carries the measured Gamma_2 as the exact string "0"; unmeasured steps carry null."""
    items = ["A", "B", "C"]
    edges = [("A", "B", 1), ("B", "C", 1), ("C", "A", 1)]
    claims = {("A", "B"): 1, ("B", "C"): 1, ("C", "A"): -3}
    system = ConstraintSystem(items=items, edges=edges, claims=claims)
    repair = solve_single_repair(system)
    assert repair["status"] == "SOLVED"
    edge = (repair["edge"][0], repair["edge"][1])
    repaired_claims = dict(claims)
    repaired_claims[edge] = parse_int_exact(repair["value"])
    repaired = ConstraintSystem(items=items, edges=edges, claims=repaired_claims)
    cycle = extract_contradiction_cycle(system)
    assert cycle is not None

    tape = build_c001_ddc_action_tape(
        system=system,
        repaired_system=repaired,
        contradiction_cycle=cycle,
        repair_edge=edge,
        repair_val=repair["value"],
        danger_decision="QUARANTINED",
        lifted=execute_9dot_gauge_break(system),
    ).unwrap()
    by_letter = {step["letter"]: step for step in tape}
    assert by_letter["E"]["gamma2"] == "0"
    assert by_letter["E"]["phi1"] == "0"
    assert by_letter["C"]["gamma2"] is None
    assert by_letter["Λ"]["phi1"] is None
    assert by_letter["R"]["cycle_signed_sum"] in ("-1", "1")
    for step in tape:
        assert "timestamp" not in step
        for key in ("phi1", "gamma2"):
            assert type(step[key]) is not float


def test_9dot_gauge_break_carrier_lift() -> None:
    """Verifies that 9-dot gauge break lifts 1D graph to 2D simplicial complex with bridge node '9'."""
    items = ["A", "B", "C"]
    edges = [("A", "B", 1), ("B", "C", 1), ("C", "A", 1)]
    claims = {("A", "B"): 1, ("B", "C"): 1, ("C", "A"): -3}
    sys_orig = ConstraintSystem(items=items, edges=edges, claims=claims)

    lifted = execute_9dot_gauge_break(sys_orig, bridge_node="9")
    assert "9" in lifted.nodes
    assert len(lifted.nodes) == len(items) + 1
    assert lifted.bridge_node == "9"
    assert len(lifted.faces) > 0
    for face in lifted.faces:
        assert len(face) == 3
        assert face[2] == "9"


def test_reverse_write_order_protocol_and_cryptographic_binding(pilot_dir: Path) -> None:
    """Verifies Reverse Write Order Protocol binding in receipt.json."""
    receipt = json.loads((pilot_dir / "receipt.json").read_text(encoding="utf-8"))
    summary = json.loads((pilot_dir / "summary.json").read_text(encoding="utf-8"))
    novella_bytes = (pilot_dir / "novella.md").read_bytes()
    dda_bytes = (pilot_dir / "dda_actions.jsonl").read_bytes()
    summary_bytes = (pilot_dir / "summary.json").read_bytes()

    assert receipt["schema"] == RECEIPT_SCHEMA
    assert receipt["task_key"] == TASK_KEY
    assert receipt["terminal_verdict"] == TERMINAL_REFERENCE_SELF_CONSISTENT
    assert receipt["gate_scope"] == GATE_SCOPE
    assert receipt["authority_effect"] == "None"
    assert receipt["receipt_id"] == summary["receipt_id"]

    assert hashlib.sha256(novella_bytes).hexdigest() == receipt["novella_sha256"]
    assert hashlib.sha256(dda_bytes).hexdigest() == receipt["dda_actions_sha256"]
    assert hashlib.sha256(summary_bytes).hexdigest() == receipt["summary_sha256"]

    dda_lines = [line.strip() for line in dda_bytes.decode("utf-8").splitlines() if line.strip()]
    assert json.loads(dda_lines[-1])["record_sha256"] == receipt["dda_head_sha256"]


def test_label_reference_self_consistent_and_exact_potential(pilot_dir: Path) -> None:
    """Counterexample: the old summary claimed PASS_TO_MASTER, is_authorized=True, disposition SELECT
    and float Phi_1/Gamma_2 = 0.0, none of which was measured."""
    summary = json.loads((pilot_dir / "summary.json").read_text(encoding="utf-8"))

    assert summary["terminal_verdict"] == TERMINAL_REFERENCE_SELF_CONSISTENT
    assert summary["gate_scope"] == GATE_SCOPE
    assert summary["phi1"] == "0"
    assert summary["gamma2"] == "0"
    assert summary["defect_count"] == 0
    assert summary["host_verdict_before"] == "CONTRADICTION"
    assert summary["host_verdict_after"] == "CONSISTENT"
    assert summary["cycle_signed_sum_after"] == "0"
    assert summary["cycle_signed_sum_before"] not in (None, "0")
    assert summary["mutations_total"] == len(generate_mutation_cases())
    assert summary["mutations_killed"] == summary["mutations_total"]
    assert summary["mutation_kill_rate"] == "1"
    for removed in (
        "is_authorized",
        "consecration_state",
        "disposition",
        "selected_candidate_id",
        "foundation",
    ):
        assert removed not in summary, f"unmeasured claim field {removed!r} is still emitted"

    tape_letters = [
        json.loads(line)["payload"]["letter"]
        for line in (pilot_dir / "dda_actions.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert summary["letter_tape"] == tape_letters

    potential = summary["verified_potential"]
    assert isinstance(potential, dict)
    assert len(potential) >= 6
    for item, val in potential.items():
        assert is_canonical_int_str(val), (
            f"Potential for item {item} is not canonical int string: {val}"
        )


def test_no_pass_to_master_label_anywhere_in_bundle(pilot_dir: Path) -> None:
    """Counterexample: the reference self-check was labelled PASS_TO_MASTER in all four files."""
    for fname in BUNDLE_FILES:
        raw = (pilot_dir / fname).read_bytes()
        assert b"PASS_TO_MASTER" not in raw, f"{fname} still carries PASS_TO_MASTER"
        assert b"7/7 killed" not in raw


def test_claim_discipline_hygiene(pilot_dir: Path) -> None:
    """Verifies that summary.json adheres to the Claim Hygiene Rule with zero forbidden hype verbs."""
    cd = json.loads((pilot_dir / "summary.json").read_text(encoding="utf-8"))["claim_discipline"]

    assert isinstance(cd["supports"], list) and len(cd["supports"]) > 0
    assert isinstance(cd["does_not_support"], list) and len(cd["does_not_support"]) > 0
    assert (
        isinstance(cd["narrowest_defensible_claim"], str)
        and len(cd["narrowest_defensible_claim"]) > 0
    )
    assert isinstance(cd["next_test_needed"], str) and len(cd["next_test_needed"]) > 0

    all_text = " ".join(
        cd["supports"]
        + cd["does_not_support"]
        + [cd["narrowest_defensible_claim"], cd["next_test_needed"]]
    ).lower()
    forbidden_verbs = [
        "proves",
        "guarantees",
        "mathematically verifies",
        "fundamentally",
        "true intelligence",
        "universal",
        "flawless",
        "perfectly",
        "obviously",
        "weaponized",
    ]
    for verb in forbidden_verbs:
        assert verb not in all_text, f"Forbidden hype verb '{verb}' detected in claim discipline!"


def test_clean_utf8_encoding_no_bom(pilot_dir: Path) -> None:
    """Verifies all four quad bundle artifacts are encoded in pure UTF-8 without BOM."""
    for fname in BUNDLE_FILES:
        raw_bytes = (pilot_dir / fname).read_bytes()
        assert not raw_bytes.startswith(b"\xef\xbb\xbf"), f"Artifact {fname} contains UTF-8 BOM!"
        raw_bytes.decode("utf-8")


def test_rop_monad_contracts_and_isolated_execution(tmp_path: Path) -> None:
    """Counterexample: force=True used to rmtree an existing run folder; now it is refused and kept."""
    isolated_dir = tmp_path / "custom_bout_run"
    res = run_woland_c001_bout(custom_run_dir=isolated_dir)
    assert res.is_ok
    info = res.unwrap()
    assert info["status"] == "COMPLETED"
    assert info["terminal_verdict"] == TERMINAL_REFERENCE_SELF_CONSISTENT
    assert info["phi1"] == "0"
    receipt_before = (isolated_dir / "receipt.json").read_bytes()

    for force in (False, True):
        res_refusal = run_woland_c001_bout(custom_run_dir=isolated_dir, force=force)
        assert res_refusal.is_err
        assert res_refusal.unwrap_err().code == "RUN_FOLDER_EXISTS"
    assert (isolated_dir / "receipt.json").read_bytes() == receipt_before


def test_default_run_store_is_the_intelligence_root_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Counterexample: the bout also mirrored its run folder into Path.cwd()/_intelligence."""
    store = tmp_path / "store"
    work = tmp_path / "cwd"
    work.mkdir()
    monkeypatch.setenv("OMEGA_INTELLIGENCE_ROOT", str(store))
    monkeypatch.chdir(work)

    res = run_woland_c001_bout()
    assert res.is_ok, res
    run_dir = Path(res.unwrap()["run_dir"])
    runs_root = (store / "_intelligence" / "_woland" / "runs").resolve()
    assert run_dir.parent == runs_root
    assert run_dir.name.startswith(f"{TASK_KEY}_")
    assert (run_dir / "receipt.json").is_file()
    assert not (work / "_intelligence").exists()


def test_mutation_count_is_derived_not_constant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Counterexample: the novella printed '7/7 killed' and a 100% kill rate whatever the mutation suite held."""
    three = generate_mutation_cases()[:3]
    monkeypatch.setattr(bout, "generate_mutation_cases", lambda: three)
    target = tmp_path / "three_mutations"
    res = run_woland_c001_bout(custom_run_dir=target)
    assert res.is_ok, res
    summary = json.loads((target / "summary.json").read_text(encoding="utf-8"))
    assert summary["mutations_total"] == 3
    assert summary["mutations_killed"] == 3
    novella = (target / "novella.md").read_text(encoding="utf-8")
    assert "3 of 3" in novella
    assert "7/7" not in novella and "7 of 7" not in novella


def test_persist_failure_keeps_a_failure_receipt(tmp_path: Path) -> None:
    """Counterexample: a failed write removed its staging folder with rmtree and left no record."""
    target = tmp_path / "failing_run"
    steps = [{"letter": "C", "name": "Context", "gamma2": None, "phi1": None}]
    res = persist_quad_bundle(
        target_dir=target,
        task_key="failing_run",
        novella_md="# Novella",
        dda_steps=steps,
        summary_data={"not_json_serialisable": object()},
        receipt_data={},
    )
    assert res.is_err
    assert res.unwrap_err().code == "PERSISTENCE_FAILED"
    assert (target / "novella.md").is_file()
    assert (target / "dda_actions.jsonl").is_file()
    assert not (target / "receipt.json").exists()
    failure = json.loads((target / "failure_receipt.json").read_text(encoding="utf-8"))
    assert failure["status"] == "RUN_FAILED"
    assert failure["error_type"] == "TypeError"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["failing_run"]


def test_existing_folder_is_never_replaced_even_with_force(tmp_path: Path) -> None:
    """Counterexample: persist_quad_bundle(force=True) deleted an existing run folder under _intelligence."""
    target = tmp_path / "existing_run"
    target.mkdir()
    canary = target / "canary.txt"
    canary.write_text("DO_NOT_DESTROY", encoding="utf-8")

    res = persist_quad_bundle(
        target_dir=target,
        task_key="existing_run",
        novella_md="# Novella",
        dda_steps=[{"letter": "T", "gamma2": "0", "phi1": "0"}],
        summary_data={"verified_potential": {"A": format_int(0)}},
        receipt_data={},
        force=True,
    )
    assert res.is_err
    assert res.unwrap_err().code == "RUN_FOLDER_EXISTS"
    assert canary.read_text(encoding="utf-8") == "DO_NOT_DESTROY"
    assert sorted(p.name for p in target.iterdir()) == ["canary.txt"]

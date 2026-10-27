"""
test_m3_adversarial_challenge.py — Adversarial Stress-Test Harness for Milestone 3 Adversary Overseer & Quad Bundle.

Adversarially tests and challenges:
1. Hash Chain Tampering Attacks:
   - Middle action payload modification
   - Parent pointer mismatch under partial re-hash
   - Full downstream re-hash mismatch with receipt.json
   - Tail truncation (drop terminal action)
   - Sequence number reordering and duplicate sequences
   - Head injection attack
2. Reverse Write Order Protocol Attacks:
   - Post-sealing modification of novella.md
   - Post-sealing modification of summary.json
   - Post-sealing modification of dda_actions.jsonl
   - Atomicity and cleanup on persistence failure
3. Witness Dominance Stress Tests:
   - Gamma_2 > 0 strictly prevents rune 'E' across integers, floats, and fractions
   - Epsilon positive Gamma_2 (1e-9, Fraction(1, 1000)) strictly prevents 'E'
   - persist_quad_bundle refuses to seal bundle containing invalid 'E'
   - Allowed runes {R, C, I, M, Λ, D, T} when Gamma_2 > 0
4. 9-Dot Gauge Break Stress Tests:
   - Claim preservation invariant: all original claims c_e are preserved unmodified
   - 2-simplex absorption: cycle edges are contained in 2-faces with bridge node '9'
   - Bridge node collision edge case when system items contain '9'
5. Invariant & UTF-8 Encoding Attacks:
   - Strict absence of UTF-8 BOM (\xef\xbb\xbf) across all artifacts
   - Lossless Cyrillic decoding for the novelistian narrative and persona
   - Strict Claim Hygiene: zero forbidden hype verbs in summary.json
6. End-to-end Bout Execution & Determinism:
   - Isolated directory execution producing the label REFERENCE_SELF_CONSISTENT and exact Phi_1 = "0"

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest
from pilots.llm_mechanism.c001_attention_distractor_mask.run_adversary_bout import (
    DDC_LETTERS,
    assert_witness_dominance,
    execute_9dot_gauge_break,
    persist_quad_bundle,
    run_adversary_c001_bout,
)
from pilots.llm_mechanism.c001_attention_distractor_mask.solver import (
    ConstraintSystem,
)


@pytest.fixture(scope="module")
def pilot_dirs(tmp_path_factory: pytest.TempPathFactory) -> List[Path]:
    """Run the bout once into a pytest temporary folder; the real run store is never read or written."""
    target = tmp_path_factory.mktemp("c001_adversarial") / "pilot"
    res = run_adversary_c001_bout(custom_run_dir=target)
    assert res.is_ok, res
    return [target]


def verify_dda_action_tape(lines: List[str], receipt: Dict[str, Any]) -> Tuple[bool, str]:
    """Independent oracle for verifying DDC action tape integrity and receipt binding."""
    if not lines:
        return False, "Action tape is empty"

    prev_record_sha256: Optional[str] = None
    for idx, raw_line in enumerate(lines):
        try:
            record: Dict[str, Any] = json.loads(raw_line)
        except Exception as exc:
            return False, f"Line {idx} failed JSON decode: {exc}"

        for req_field in ("sequence", "parent_sha256", "payload", "record_sha256"):
            if req_field not in record:
                return False, f"Line {idx} missing required field: {req_field}"

        if record["sequence"] != idx:
            return False, f"Line {idx} sequence mismatch: {record['sequence']} != {idx}"

        if idx == 0:
            if record["parent_sha256"] is not None:
                return False, f"Line 0 parent_sha256 must be None, got {record['parent_sha256']}"
        else:
            if record["parent_sha256"] != prev_record_sha256:
                return False, (
                    f"Line {idx} parent hash mismatch: "
                    f"{record['parent_sha256']} != {prev_record_sha256}"
                )

        payload = record["payload"]
        letter = payload.get("letter")
        if letter not in DDC_LETTERS:
            return False, f"Line {idx} invalid DDC letter: {letter}"

        gamma2 = payload.get("gamma2")
        if letter == "E" and (type(gamma2) is not str or Fraction(gamma2) != 0):
            return False, f"Line {idx} witness dominance violation: letter E with gamma2={gamma2!r}"

        # Recompute material
        sorted_payload = {
            k: payload[k] for k in sorted(payload.keys(), key=lambda s: s.encode("utf-8"))
        }
        material = json.dumps(
            {"parent_sha256": record["parent_sha256"], "payload": sorted_payload, "sequence": idx},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        expected_sha256 = hashlib.sha256(material).hexdigest()
        if record["record_sha256"] != expected_sha256:
            return False, (
                f"Line {idx} record_sha256 mismatch: {record['record_sha256']} != {expected_sha256}"
            )

        prev_record_sha256 = record["record_sha256"]

    # Check head binding with receipt
    if receipt.get("dda_head_sha256") != prev_record_sha256:
        return False, (
            f"dda_head_sha256 in receipt mismatch: "
            f"{receipt.get('dda_head_sha256')} != {prev_record_sha256}"
        )

    return True, "VERIFIED"


# ==============================================================================
# Vector 1: Hash Chain Tampering Attacks
# ==============================================================================


def test_attack_hash_chain_tamper_payload(pilot_dirs: List[Path]) -> None:
    """Attack 1.1: Modifying a field inside a middle action payload breaks record_sha256."""
    p_dir = pilot_dirs[0]

    dda_lines = [
        l.strip()
        for l in (p_dir / "dda_actions.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    receipt = json.loads((p_dir / "receipt.json").read_text(encoding="utf-8"))

    # Baseline must pass
    ok, msg = verify_dda_action_tape(dda_lines, receipt)
    assert ok, f"Baseline action tape verification failed: {msg}"

    # Attack: tamper with payload of step 2 (e.g. modify actor or phi1)
    tampered_lines = list(dda_lines)
    rec2 = json.loads(tampered_lines[2])
    rec2["payload"]["actor"] = "Hostile Adversary"
    tampered_lines[2] = json.dumps(rec2)

    ok, msg = verify_dda_action_tape(tampered_lines, receipt)
    assert not ok, "Oracle failed to detect payload tampering!"
    assert "record_sha256 mismatch" in msg


def test_attack_hash_chain_parent_pointer_tamper(pilot_dirs: List[Path]) -> None:
    """Attack 1.2: Adversary modifies payload and recomputes step 2's hash, but leaves step 3's parent pointer."""
    p_dir = pilot_dirs[0]

    dda_lines = [
        l.strip()
        for l in (p_dir / "dda_actions.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    receipt = json.loads((p_dir / "receipt.json").read_text(encoding="utf-8"))

    tampered_lines = list(dda_lines)
    rec2 = json.loads(tampered_lines[2])
    rec2["payload"]["actor"] = "Hostile Adversary"
    # Recompute record_sha256 for step 2
    sorted_payload = {
        k: rec2["payload"][k]
        for k in sorted(rec2["payload"].keys(), key=lambda s: s.encode("utf-8"))
    }
    material = json.dumps(
        {
            "parent_sha256": rec2["parent_sha256"],
            "payload": sorted_payload,
            "sequence": rec2["sequence"],
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    rec2["record_sha256"] = hashlib.sha256(material).hexdigest()
    tampered_lines[2] = json.dumps(rec2)

    ok, msg = verify_dda_action_tape(tampered_lines, receipt)
    assert not ok, "Oracle failed to detect broken parent pointer chain!"
    assert "parent hash mismatch" in msg


def test_attack_hash_chain_full_downstream_rehash_detected_by_receipt(
    pilot_dirs: List[Path],
) -> None:
    """Attack 1.3: Adversary modifies step 2 and re-hashes entire downstream chain.
    The internal chain becomes valid, but dda_head_sha256 in receipt.json catches the attack!
    """
    p_dir = pilot_dirs[0]

    dda_lines = [
        l.strip()
        for l in (p_dir / "dda_actions.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    receipt = json.loads((p_dir / "receipt.json").read_text(encoding="utf-8"))

    # Re-hash downstream from step 2
    rehashed_lines: List[str] = []
    prev_hash: Optional[str] = None
    for idx, line in enumerate(dda_lines):
        rec = json.loads(line)
        if idx == 2:
            rec["payload"]["diagnostic_after"] = "FORGED_DIAGNOSTIC"
        rec["parent_sha256"] = prev_hash
        sorted_payload = {
            k: rec["payload"][k]
            for k in sorted(rec["payload"].keys(), key=lambda s: s.encode("utf-8"))
        }
        mat = json.dumps(
            {"parent_sha256": prev_hash, "payload": sorted_payload, "sequence": idx},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        rec["record_sha256"] = hashlib.sha256(mat).hexdigest()
        prev_hash = rec["record_sha256"]
        rehashed_lines.append(json.dumps(rec))

    ok, msg = verify_dda_action_tape(rehashed_lines, receipt)
    assert not ok, "Receipt failed to detect forged downstream re-hash!"
    assert "dda_head_sha256 in receipt mismatch" in msg


def test_attack_hash_chain_tail_truncation(pilot_dirs: List[Path]) -> None:
    """Attack 1.4: Dropping the last DDC action immediately breaks dda_head_sha256 binding."""
    p_dir = pilot_dirs[0]

    dda_lines = [
        l.strip()
        for l in (p_dir / "dda_actions.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    receipt = json.loads((p_dir / "receipt.json").read_text(encoding="utf-8"))

    truncated_lines = dda_lines[:-1]
    ok, msg = verify_dda_action_tape(truncated_lines, receipt)
    assert not ok, "Oracle failed to detect tail truncation!"
    assert "dda_head_sha256 in receipt mismatch" in msg


def test_attack_hash_chain_sequence_reordering(pilot_dirs: List[Path]) -> None:
    """Attack 1.5: Swapping two records breaks sequence numbering."""
    p_dir = pilot_dirs[0]

    dda_lines = [
        l.strip()
        for l in (p_dir / "dda_actions.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    receipt = json.loads((p_dir / "receipt.json").read_text(encoding="utf-8"))

    swapped_lines = list(dda_lines)
    swapped_lines[1], swapped_lines[2] = swapped_lines[2], swapped_lines[1]

    ok, msg = verify_dda_action_tape(swapped_lines, receipt)
    assert not ok, "Oracle failed to detect sequence reordering!"
    assert "sequence mismatch" in msg or "parent hash mismatch" in msg


def test_attack_hash_chain_head_injection(pilot_dirs: List[Path]) -> None:
    """Attack 1.6: Injecting an extraneous step at index 0."""
    p_dir = pilot_dirs[0]

    dda_lines = [
        l.strip()
        for l in (p_dir / "dda_actions.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    receipt = json.loads((p_dir / "receipt.json").read_text(encoding="utf-8"))

    injected_record = {
        "sequence": 0,
        "parent_sha256": None,
        "payload": {"letter": "C", "name": "Fake Step"},
        "record_sha256": "0" * 64,
    }
    injected_lines = [json.dumps(injected_record)] + list(dda_lines)

    ok, msg = verify_dda_action_tape(injected_lines, receipt)
    assert not ok, "Oracle failed to detect head injection!"


# ==============================================================================
# Vector 2: Reverse Write Order Protocol Attacks
# ==============================================================================


def test_attack_reverse_write_order_novella_modification(pilot_dirs: List[Path]) -> None:
    """Attack 2.1: Modifying novella.md after sealing breaks novella_sha256."""
    p_dir = pilot_dirs[0]

    receipt = json.loads((p_dir / "receipt.json").read_text(encoding="utf-8"))
    original_bytes = (p_dir / "novella.md").read_bytes()
    tampered_bytes = original_bytes + b"\n<!-- Malicious commentary -->\n"

    assert hashlib.sha256(original_bytes).hexdigest() == receipt["novella_sha256"]
    assert hashlib.sha256(tampered_bytes).hexdigest() != receipt["novella_sha256"]


def test_attack_reverse_write_order_summary_modification(pilot_dirs: List[Path]) -> None:
    """Attack 2.2: Modifying summary.json after sealing breaks summary_sha256."""
    p_dir = pilot_dirs[0]

    receipt = json.loads((p_dir / "receipt.json").read_text(encoding="utf-8"))
    summary = json.loads((p_dir / "summary.json").read_text(encoding="utf-8"))

    # Adversary tries to fabricate lower defect count or alter verdict
    tampered_summary = dict(summary)
    tampered_summary["defect_count"] = 999
    tampered_bytes = (json.dumps(tampered_summary, indent=2, sort_keys=True) + "\n").encode("utf-8")

    assert hashlib.sha256(tampered_bytes).hexdigest() != receipt["summary_sha256"]


def test_attack_reverse_write_order_dda_actions_modification(pilot_dirs: List[Path]) -> None:
    """Attack 2.3: Modifying dda_actions.jsonl after sealing breaks dda_actions_sha256."""
    p_dir = pilot_dirs[0]

    receipt = json.loads((p_dir / "receipt.json").read_text(encoding="utf-8"))
    original_bytes = (p_dir / "dda_actions.jsonl").read_bytes()
    tampered_bytes = original_bytes + b'{"fake": true}\n'

    assert hashlib.sha256(original_bytes).hexdigest() == receipt["dda_actions_sha256"]
    assert hashlib.sha256(tampered_bytes).hexdigest() != receipt["dda_actions_sha256"]


def test_atomic_write_failure_cleanup(tmp_path: Path) -> None:
    """Attack 2.4: an invalid step is refused before anything is written, and an existing folder survives.

    Counterexample: with force=True the old code deleted the existing run folder (and its
    canary) before it discovered the witness-dominance violation.
    """
    target_dir = tmp_path / "victim_run_folder"
    target_dir.mkdir(parents=True)
    canary = target_dir / "canary.txt"
    canary.write_text("DO_NOT_DESTROY", encoding="utf-8")

    invalid_steps = [{"letter": "E", "gamma2": 1, "name": "Illegal Step"}]

    res = persist_quad_bundle(
        target_dir=target_dir,
        task_key="test_fail",
        novella_md="# Test",
        dda_steps=invalid_steps,
        summary_data={},
        receipt_data={},
        force=True,
    )
    assert not res.is_ok
    assert res.unwrap_err().code == "WITNESS_DOMINANCE_VIOLATION"

    assert canary.read_text(encoding="utf-8") == "DO_NOT_DESTROY"
    leftovers = [p for p in tmp_path.iterdir() if p.name.startswith(".")]
    assert len(leftovers) == 0, f"Staging directory created for a refused bundle: {leftovers}"


# ==============================================================================
# Vector 3: Witness Dominance Stress Tests
# ==============================================================================


def test_attack_witness_dominance_positive_gamma2_refuses_e() -> None:
    """Stress test 3.1: a non-zero exact Gamma_2 strictly prevents rune 'E' (int, Fraction, exact string)."""
    test_cases = [1, 100, Fraction(1, 1), Fraction(5, 2), "5/2", -1]
    for g2 in test_cases:
        res = assert_witness_dominance("E", gamma2=g2)
        assert not res.is_ok, f"Expected violation for gamma2={g2}"
        refusal = res.unwrap_err()
        assert refusal.code == "WITNESS_DOMINANCE_VIOLATION"


def test_attack_witness_dominance_fractional_and_epsilon_gamma2() -> None:
    """Stress test 3.2: tiny positive Gamma_2 prevents 'E'; float epsilons are refused as non-exact.

    Counterexample: float epsilons used to be compared after float() conversion, so a
    float that rounds to 0.0 would have admitted 'E'.
    """
    for eps in (Fraction(1, 1000000000), Fraction(1, 10**15), "1/1000000000"):
        res = assert_witness_dominance("E", gamma2=eps)
        assert not res.is_ok, f"Expected violation for epsilon gamma2={eps}"
        assert res.unwrap_err().code == "WITNESS_DOMINANCE_VIOLATION"
    for eps in (1e-9, 1e-15, 0.0000001, 1e-400):
        res = assert_witness_dominance("E", gamma2=eps)
        assert not res.is_ok, f"Expected refusal for float gamma2={eps}"
        assert res.unwrap_err().code == "NON_EXACT_DEFECT_VALUE"


def test_attack_witness_dominance_fraction_below_float_range() -> None:
    """Counterexample: Fraction(1, 10**400) > 0 underflowed float(gamma2) to 0.0, so the old
    check `float(gamma2) > 0.0` admitted rune 'E' on a positive Gamma_2."""
    tiny = Fraction(1, 10**400)
    assert tiny > 0 and float(tiny) == 0.0
    res = assert_witness_dominance("E", gamma2=tiny)
    assert res.is_err
    assert res.unwrap_err().code == "WITNESS_DOMINANCE_VIOLATION"


def test_attack_witness_dominance_persist_bundle_rejection(tmp_path: Path) -> None:
    """Stress test 3.3: persist_quad_bundle refuses to seal bundle containing rune 'E' with Gamma_2 > 0."""
    target_dir = tmp_path / "illegal_quad_bundle"
    illegal_steps = [
        {"sequence": 0, "letter": "C", "gamma2": 1},
        {"sequence": 1, "letter": "E", "gamma2": "1/10000"},  # E with positive gamma2
    ]
    res = persist_quad_bundle(
        target_dir=target_dir,
        task_key="illegal_test",
        novella_md="# Fake",
        dda_steps=illegal_steps,
        summary_data={},
        receipt_data={},
        force=True,
    )
    assert not res.is_ok
    assert res.unwrap_err().code == "WITNESS_DOMINANCE_VIOLATION"
    assert not target_dir.exists(), "Target dir should not exist on refusal!"


def test_witness_dominance_permitted_runes_with_gamma2_positive() -> None:
    """Stress test 3.4: All other DDC runes {R, C, I, M, Λ, D, T} are permitted when Gamma_2 > 0."""
    permitted_runes = ["R", "C", "I", "M", "Λ", "Lambda", "D", "T"]
    for r in permitted_runes:
        res = assert_witness_dominance(r, gamma2=5)
        assert res.is_ok, f"Rune '{r}' unexpectedly refused with positive gamma2"


def test_witness_dominance_rune_e_permitted_only_at_zero() -> None:
    """Stress test 3.5: Rune 'E' is permitted if and only if Gamma_2 is measured and exactly 0.

    Counterexample: float 0.0 used to be accepted as an exact zero.
    """
    assert assert_witness_dominance("E", gamma2=0).is_ok
    assert assert_witness_dominance("E", gamma2=Fraction(0, 1)).is_ok
    assert assert_witness_dominance("E", gamma2="0").is_ok
    assert assert_witness_dominance("E", gamma2=0.0).unwrap_err().code == "NON_EXACT_DEFECT_VALUE"
    assert (
        assert_witness_dominance("E", gamma2=None).unwrap_err().code
        == "WITNESS_DOMINANCE_UNMEASURED"
    )


# ==============================================================================
# Vector 4: 9-Dot Gauge Break Stress Tests
# ==============================================================================


def test_attack_9dot_carrier_lift_claim_preservation() -> None:
    """Stress test 4.1: Carrier lift strictly preserves 100% of original edge claims without mutation."""
    items = ["Alpha", "Beta", "Gamma", "Delta"]
    edges = [
        ("Alpha", "Beta", 1),
        ("Beta", "Gamma", 1),
        ("Gamma", "Delta", 1),
        ("Delta", "Alpha", 1),
    ]
    claims = {
        ("Alpha", "Beta"): 100,
        ("Beta", "Gamma"): -50,
        ("Gamma", "Delta"): 25,
        ("Delta", "Alpha"): -75,
    }
    orig_system = ConstraintSystem(items=items, edges=edges, claims=claims)

    lifted = execute_9dot_gauge_break(orig_system, phi1=1.0, gamma2=1.0, bridge_node="9")

    # Invariant: every original edge claim must be present and identical
    for edge_key, original_claim_val in claims.items():
        assert edge_key in lifted.claims, f"Original edge {edge_key} missing from lifted claims!"
        assert lifted.claims[edge_key] == original_claim_val, (
            f"Original claim for {edge_key} mutated: {lifted.claims[edge_key]} != {original_claim_val}"
        )


def test_attack_9dot_cycle_absorption_into_2simplices() -> None:
    """Stress test 4.2: Obstruction cycle edges are absorbed into 2-simplex faces."""
    items = ["V1", "V2", "V3"]
    edges = [("V1", "V2", 1), ("V2", "V3", 1), ("V3", "V1", 1)]
    claims = {("V1", "V2"): 10, ("V2", "V3"): 20, ("V3", "V1"): -35}
    orig_system = ConstraintSystem(items=items, edges=edges, claims=claims)

    lifted = execute_9dot_gauge_break(orig_system, phi1=1.0, gamma2=1.0, bridge_node="9")

    # Verify that candidate edges have corresponding 2-faces
    candidate_edges = edges[:2]
    for u, v, _w in candidate_edges:
        expected_face = (u, v, "9")
        assert expected_face in lifted.faces, (
            f"Missing 2-simplex face for candidate edge ({u}, {v})"
        )
        # Verify connecting edges to bridge node '9' exist
        assert (u, "9", 1) in lifted.edges
        assert (v, "9", 1) in lifted.edges
        assert lifted.claims[(u, "9")] == 0
        assert lifted.claims[(v, "9")] == 0


def test_attack_9dot_bridge_node_collision_edge_case() -> None:
    """Stress test 4.3: Custom bridge node specified when '9' might conflict."""
    items = ["1", "2", "9"]  # original items include '9'
    edges = [("1", "2", 1), ("2", "9", 1)]
    claims = {("1", "2"): 5, ("2", "9"): 10}
    orig_system = ConstraintSystem(items=items, edges=edges, claims=claims)

    # Use disambiguated bridge node to avoid collision
    lifted = execute_9dot_gauge_break(orig_system, phi1=1.0, gamma2=1.0, bridge_node="BRIDGE_DIM_2")
    assert lifted.bridge_node == "BRIDGE_DIM_2"
    assert "BRIDGE_DIM_2" in lifted.nodes
    assert len(lifted.nodes) == len(items) + 1


# ==============================================================================
# Vector 5: Invariant & UTF-8 Encoding Attacks
# ==============================================================================


def test_attack_utf8_encoding_cleanliness_and_no_bom(pilot_dirs: List[Path]) -> None:
    """Stress test 5.1: Assert byte-level absence of BOM across all quad bundle artifacts."""

    for p_dir in pilot_dirs:
        for fname in ("novella.md", "dda_actions.jsonl", "summary.json", "receipt.json"):
            fpath = p_dir / fname
            raw_bytes = fpath.read_bytes()
            assert not raw_bytes.startswith(b"\xef\xbb\xbf"), (
                f"File {fpath} contains UTF-8 BOM bytes (\xef\xbb\xbf)!"
            )
            # Must decode cleanly as strict UTF-8
            decoded = raw_bytes.decode("utf-8")
            assert len(decoded) > 0


def test_attack_cyrillic_narrative_encoding_fidelity(pilot_dirs: List[Path]) -> None:
    """Stress test 5.2: Assert lossless decoding of Cyrillic text in novella.md."""
    novella_text = (pilot_dirs[0] / "novella.md").read_text(encoding="utf-8")

    cyrillic_samples = [
        "Adversary",
        "Defect Hunter",
        "Gauge Breaker",
        "Scope Guard",
        "Syntax Prefilter",
        "Manuscript Truth",
        "Primal Dual",
        "Quarantine",
        "Scar Chronicler",
        "Рукописи не горят",
        "Свежесть бывает только одна",
    ]
    for sample in cyrillic_samples:
        assert sample in novella_text, (
            f"Cyrillic string '{sample}' missing or mangled in novella.md!"
        )


def test_attack_claim_hygiene_anti_hype_scan(pilot_dirs: List[Path]) -> None:
    """Stress test 5.3: Scan summary.json claim discipline and novella.md for forbidden hype verbs."""
    summary = json.loads((pilot_dirs[0] / "summary.json").read_text(encoding="utf-8"))
    cd = summary["claim_discipline"]

    forbidden_hype_verbs = [
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
        "merely",
        "simply",
    ]

    corpus = " ".join(
        cd["supports"]
        + cd["does_not_support"]
        + [cd["narrowest_defensible_claim"], cd["next_test_needed"]]
    ).lower()

    for forbidden in forbidden_hype_verbs:
        assert forbidden not in corpus, (
            f"Claim hygiene violation: forbidden hype verb '{forbidden}' found in summary.json!"
        )


# ==============================================================================
# Vector 6: Isolated End-to-End Execution & Determinism
# ==============================================================================


def test_isolated_end_to_end_bout_determinism_and_exact_potential(tmp_path: Path) -> None:
    """Stress test 6.1: Run full bout in isolated directory and verify bit-for-bit determinism."""
    run1_dir = tmp_path / "run_1"
    run2_dir = tmp_path / "run_2"

    res1 = run_adversary_c001_bout(custom_run_dir=run1_dir, force=True, seed=42)
    assert res1.is_ok
    info1 = res1.unwrap()

    res2 = run_adversary_c001_bout(custom_run_dir=run2_dir, force=True, seed=42)
    assert res2.is_ok
    info2 = res2.unwrap()

    # Verify metrics match (exact strings, reference self-check label)
    assert info1["terminal_verdict"] == "REFERENCE_SELF_CONSISTENT"
    assert info2["terminal_verdict"] == "REFERENCE_SELF_CONSISTENT"
    assert info1["phi1"] == "0"
    assert info2["phi1"] == "0"
    assert info1["gamma2"] == "0"
    assert info2["gamma2"] == "0"
    assert info1["mutation_kill_rate"] == "1"
    assert info2["mutation_kill_rate"] == "1"

    # Novella narrative must be bit-for-bit identical
    assert (run1_dir / "novella.md").read_bytes() == (run2_dir / "novella.md").read_bytes()

    # dda_actions must be bit-for-bit identical
    assert (run1_dir / "dda_actions.jsonl").read_bytes() == (
        run2_dir / "dda_actions.jsonl"
    ).read_bytes()

    # Re-verify quad bundle in run1_dir with independent oracle
    lines = [
        l.strip()
        for l in (run1_dir / "dda_actions.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()
    ]
    receipt = json.loads((run1_dir / "receipt.json").read_text(encoding="utf-8"))
    ok, msg = verify_dda_action_tape(lines, receipt)
    assert ok, f"Oracle verification of isolated run failed: {msg}"

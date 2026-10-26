"""Unit tests for LamarckianMutationReceiptV1 and CochainResidualV1 (NF-02).

AuthorityEffect: None.
Zero-Float Law: Verified using exact rational arithmetic.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import pytest

from omega_engine_prompt_civilization.domain.lamarckian import (
    CochainResidualV1,
    LamarckianMutationReceiptV1,
)


def test_cochain_residual_validation_and_fractions() -> None:
    res = CochainResidualV1.from_fractions(
        phi1=Fraction(1, 2),
        gamma2=Fraction(0, 1),
        xi="0/1",
    )
    assert res.phi1 == "1/2"
    assert res.gamma2 == "0/1"
    assert res.xi == "0/1"
    assert res.phi1_fraction == Fraction(1, 2)
    assert res.gamma2_fraction == Fraction(0, 1)
    assert res.xi_fraction == Fraction(0, 1)
    assert res.to_dict() == {"phi1": "1/2", "gamma2": "0/1", "xi": "0/1"}

    # Invalid cochain format
    with pytest.raises(ValueError, match="INVALID_COCHAIN_RATIONAL"):
        CochainResidualV1(phi1="invalid", gamma2="0/1", xi="0/1")


def test_lamarckian_mutation_receipt_lifecycle() -> None:
    parent_id = "sha256:" + hashlib.sha256(b"parent_genome_001").hexdigest()
    child_id = "sha256:" + hashlib.sha256(b"child_genome_002").hexdigest()
    witness_sha = hashlib.sha256(b"ast_defect_layer_violation").hexdigest()
    residual = CochainResidualV1.from_fractions(phi1=Fraction(1, 1), gamma2=0, xi=0)

    receipt = LamarckianMutationReceiptV1.create(
        parent_genome_id=parent_id,
        child_genome_id=child_id,
        falsification_witness_sha256=witness_sha,
        cochain_residual=residual,
        antibody_id="ab_anti_layer_violation_01",
        hop_distance=1,
    )

    assert receipt.receipt_id.startswith("sha256:")
    assert receipt.hop_distance == 1
    assert receipt.attenuation_weight == "1/2"
    assert receipt.antibody_id == "ab_anti_layer_violation_01"

    # Verify wire round-trip
    wire_dict = receipt.to_dict()
    roundtrip = LamarckianMutationReceiptV1.from_dict(wire_dict)
    assert roundtrip == receipt


def test_lamarckian_attenuation_weights_1_to_10() -> None:
    expected_weights = {
        1: "1/2",
        2: "1/4",
        3: "1/8",
        4: "1/16",
        5: "1/32",
        6: "1/64",
        7: "1/128",
        8: "1/256",
        9: "1/512",
        10: "1/1024",
    }
    for hop, weight in expected_weights.items():
        assert LamarckianMutationReceiptV1.calculate_attenuation_weight(hop) == weight


def test_lamarckian_hop_distance_bounds_refusal() -> None:
    # d = 0 is out of bounds
    with pytest.raises(ValueError, match="HOP_DISTANCE_OUT_OF_BOUNDS"):
        LamarckianMutationReceiptV1.calculate_attenuation_weight(0)

    # d = 11 is out of bounds (> 10 must evaporate per Rule 3)
    with pytest.raises(ValueError, match="HOP_DISTANCE_OUT_OF_BOUNDS"):
        LamarckianMutationReceiptV1.calculate_attenuation_weight(11)


def test_lamarckian_tamper_detection() -> None:
    parent_id = "sha256:" + hashlib.sha256(b"parent_genome_001").hexdigest()
    child_id = "sha256:" + hashlib.sha256(b"child_genome_002").hexdigest()
    witness_sha = hashlib.sha256(b"defect").hexdigest()
    residual = CochainResidualV1.from_fractions(phi1=1, gamma2=0, xi=0)

    receipt = LamarckianMutationReceiptV1.create(
        parent_genome_id=parent_id,
        child_genome_id=child_id,
        falsification_witness_sha256=witness_sha,
        cochain_residual=residual,
        antibody_id="ab_01",
        hop_distance=2,
    )

    # Tampered receipt_id
    wire = receipt.to_dict()
    wire["receipt_id"] = "sha256:" + "0" * 64
    with pytest.raises(ValueError, match="RECEIPT_ID_DIGEST_MISMATCH"):
        LamarckianMutationReceiptV1.from_dict(wire)

    # Tampered attenuation weight
    wire2 = receipt.to_dict()
    wire2["attenuation_weight"] = "1/2"  # Expected 1/4 for hop 2
    with pytest.raises(ValueError, match="ATTENUATION_WEIGHT_MISMATCH"):
        LamarckianMutationReceiptV1.from_dict(wire2)

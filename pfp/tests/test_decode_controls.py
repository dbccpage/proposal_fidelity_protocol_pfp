# -*- coding: utf-8 -*-
"""Verification of decode controls, logit interventions, and receipt verification (U11).

Tests:
1. CarrierMask token restriction and violation detection.
2. LogitBias steering configuration and bounds checking.
3. GrammarMask SHA-256 integrity and JSON schema formatting.
4. LocalHfMechanismAdapter execution, receipts, and AuthorityEffect: None.
5. VllmDecodeAdapter request body formatting and control-honored checks.
6. Integration with native Rust verify_decode_receipt host action.

Clean Architecture Layer: Operations Scoped Tests
AuthorityEffect: None
"""

from __future__ import annotations

import pytest

from omega_engine_pfp.domain.ports.decode_control_port import (
    CarrierMask,
    ControlKind,
    DecodeControlReceipt,
    DecodeControlSpec,
    GrammarMask,
    LogitBias,
)
from omega_engine_pfp.ffi import RustSymbolGameHost
from omega_engine_pfp.infrastructure.adapters.decode_controls import (
    LocalHfMechanismAdapter,
    VllmDecodeAdapter,
)


def test_carrier_mask_exact_containment():
    """Verify carrier mask correctly identifies allowed vs distractor tokens."""
    mask = CarrierMask(allowed_tokens=(10, 20, 30))
    assert mask.is_token_allowed(10)
    assert mask.is_token_allowed(20)
    assert not mask.is_token_allowed(99)


def test_grammar_mask_digest_computation():
    """Verify grammar mask computes deterministic SHA-256 digest on creation."""
    schema_str = '{"type": "object", "properties": {"ans": {"type": "string"}}}'
    mask = GrammarMask(grammar_text=schema_str, grammar_type="json_schema")
    assert len(mask.grammar_sha256) == 64
    assert mask.grammar_sha256 == GrammarMask(grammar_text=schema_str).grammar_sha256


def test_local_hf_mechanism_receipt_and_verification():
    """Verify LocalHfMechanismAdapter applies carrier mask and produces verified receipt."""
    adapter = LocalHfMechanismAdapter(fixture_mode=True)
    spec = DecodeControlSpec(
        control_kind=ControlKind.CARRIER_MASK,
        carrier_mask=CarrierMask(allowed_tokens=(10, 20, 30, 40)),
    )
    text, receipt = adapter.apply_decode_control(spec, "Solve potential", case_id="c001_t1")

    assert receipt.control_kind == "CARRIER_MASK"
    assert receipt.authority_effect == "None"
    assert receipt.honored is True
    assert len(receipt.digest_sha256()) == 64

    # Verify receipt via adapter
    verdict = adapter.verify_decode_receipt(receipt)
    assert verdict["status"] == "PASS"
    assert verdict["authority_effect"] == "None"


def test_carrier_mask_violation_caught_by_verifier():
    """Verify verifier catches any token emitted outside the declared carrier set."""
    adapter = LocalHfMechanismAdapter()
    corrupt_receipt = DecodeControlReceipt(
        receipt_id="rcpt_bad_01",
        case_id="c001_t2",
        control_kind="CARRIER_MASK",
        allowed_tokens=(10, 20),
        output_tokens=(10, 999),  # 999 violates carrier mask!
        authority_effect="None",
    )
    verdict = adapter.verify_decode_receipt(corrupt_receipt)
    assert verdict["status"] == "REFUSAL"
    assert verdict["refusal_code"] == "CARRIER_CONSTRAINT_VIOLATED"


def test_vllm_decode_adapter_formatting_and_execution():
    """Verify VllmDecodeAdapter constructs valid provider API payloads."""
    adapter = VllmDecodeAdapter(fixture_mode=True)
    schema_str = '{"type": "object", "properties": {"status": {"type": "string"}}}'
    spec = DecodeControlSpec(
        control_kind=ControlKind.JSON_SCHEMA,
        grammar_mask=GrammarMask(grammar_text=schema_str),
        logit_bias=LogitBias(biases={105: 5, 204: -100}),
    )

    body = adapter.format_request_body(spec, "Repair cycle")
    assert "response_format" in body
    assert body["response_format"]["type"] == "json_object"
    assert body["response_format"]["schema"]["type"] == "object"

    text, receipt = adapter.apply_decode_control(spec, "Repair cycle", case_id="c005_t1")
    assert receipt.control_kind == "JSON_SCHEMA"
    assert receipt.grammar_sha256 is not None
    assert receipt.authority_effect == "None"

    verdict = adapter.verify_decode_receipt(receipt)
    assert verdict["status"] == "PASS"


def test_native_rust_verify_decode_receipt():
    """Verify host FFI seam directly executes native Rust verify_decode_receipt."""
    host = RustSymbolGameHost()
    receipt_data = {
        "schema_version": "omega.symbol_game.decode_receipt.v1",
        "receipt_id": "r_ffi_01",
        "case_id": "c001_ffi",
        "control_kind": "LOGIT_BIAS",
        "allowed_tokens": [],
        "output_tokens": [10, 20],
        "logit_biases": [[10, 5], [20, -10]],
        "grammar_sha256": None,
        "authority_effect": "None",
    }
    outcome = host.verify_decode_receipt(receipt_data)
    assert outcome.is_ok
    raw = outcome.unwrap()
    res = raw.get("result", raw)
    assert res["status"] == "PASS"
    assert res["token_count"] == 2
    assert res["carrier_honored"] is True


@pytest.mark.parametrize("adapter_class", [LocalHfMechanismAdapter, VllmDecodeAdapter])
def test_decode_generation_requires_explicit_configuration(adapter_class):
    with pytest.raises(RuntimeError, match="EXECUTION_UNAVAILABLE"):
        adapter_class().apply_decode_control(DecodeControlSpec(), "request")


@pytest.mark.parametrize(
    "adapter_class,module",
    [(LocalHfMechanismAdapter, "local_hf_mechanism"), (VllmDecodeAdapter, "vllm_decode_adapter")],
)
def test_decode_verifier_exception_never_passes(monkeypatch, adapter_class, module):
    import importlib

    adapter_module = importlib.import_module(
        "omega_engine_pfp.infrastructure.adapters.decode_controls." + module
    )

    def unavailable():
        raise FileNotFoundError("verifier missing")

    monkeypatch.setattr(adapter_module, "get_default_host", unavailable)
    receipt = DecodeControlReceipt("r", "c", "JSON_SCHEMA", (1,), grammar_sha256="0" * 64)
    verdict = adapter_class().verify_decode_receipt(receipt)
    assert verdict["status"] == "REFUSAL" and verdict["refusal_code"] == "VERIFIER_UNAVAILABLE"

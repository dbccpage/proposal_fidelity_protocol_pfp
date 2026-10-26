"""The DDC tape wrapper sends the request shape the native host declares.

Counterexample from the study: ``ddc_verify_tape`` sent ``{"tape": [...]}``,
while ``DdcVerifyTapeRequestV1`` (``crates_rs/omega_symbol_game/src/ddc.rs``)
requires ``initial_state`` and ``steps`` and denies unknown fields, so every
call through the wrapper was refused by the host.
AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from omega_engine_operations.domain.rop.result import Ok
from omega_engine_pfp.ffi import RustSymbolGameHost, get_default_host

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = (
    ROOT
    / "omega_engine_governance/contracts/contracts_pfp"
    / "host_ddc_verify_tape.contract.yaml"
)
DEMOS = ROOT / "omega_engine/crates_rs/tests/omega_symbol_game/fixtures/ddc_paper_demos.json"


class _RecordingSeam:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def invoke_runtime(self, action, payload):
        self.calls.append((action, payload))
        return Ok({"success": True, "result": {}})


def _capturing_host() -> tuple[RustSymbolGameHost, _RecordingSeam]:
    host = RustSymbolGameHost(binary_path=ROOT / "not-a-binary-payload-capture-only")
    seam = _RecordingSeam()
    host._host = seam
    return host, seam


def _contract_fields() -> tuple[set[str], set[str]]:
    structure = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))["structure"]
    fields = {item["name"]: item.get("rust_type", "") for item in structure["fields"]}
    optional = {name for name, rust_type in fields.items() if rust_type.startswith("Option<")}
    return set(fields) - optional, optional


def _demo(name: str) -> dict:
    demos = json.loads(DEMOS.read_text(encoding="utf-8"))
    return next(demo for demo in demos if demo["name"] == name)


def test_payload_carries_exactly_the_declared_request_fields():
    required, optional = _contract_fields()
    assert required == {"initial_state", "steps"}
    demo = _demo("demo1_exact_CRET")
    host, seam = _capturing_host()
    host.ddc_verify_tape(demo["initial_state"], demo["steps"])
    host.ddc_verify_tape(demo["initial_state"], demo["steps"], genesis_root="DDC_TAPE_GENESIS")
    (action, first), (_, second) = seam.calls
    assert action == "ddc_verify_tape"
    assert "tape" not in first
    assert set(first) == required
    assert set(second) == required | optional
    assert first["initial_state"] == demo["initial_state"]
    assert first["steps"] == demo["steps"]
    assert second["genesis_root"] == "DDC_TAPE_GENESIS"


def test_native_host_accepts_the_wrapper_payload_and_reproduces_the_fixture():
    for name in ("demo1_exact_CRET", "demo1_open_CRET_unlawful"):
        demo = _demo(name)
        crossing = get_default_host().ddc_verify_tape(demo["initial_state"], demo["steps"])
        assert isinstance(crossing, Ok), crossing
        outcome = crossing.value
        assert outcome["success"] is True, outcome["error"]
        result = outcome["result"]
        assert result["lawful"] is demo["lawful"]
        assert result["letters"] == demo["letters"]
        assert result["receipt_head"] == demo["receipt_head"]

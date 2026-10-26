"""Qualification controls for inert Rust ordering review candidates."""

import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize(
    "filename",
    ["anti_rust_interned_id_canonical_order.yaml", "anti_rust_default_map_canonical_hash.yaml"],
)
def test_ordering_candidate_has_deciding_controls_and_native_bindings(filename: str) -> None:
    source = REPO / ".agents/antibodies" / filename
    projection = REPO / ".agents/antibodies/specs" / filename
    assert source.read_bytes() == projection.read_bytes()
    spec = yaml.safe_load(source.read_text(encoding="utf-8"))
    assert spec["schema_version"] == "omega.immune.antibody-spec.v1"
    assert spec["pharmacy_status"] == "candidate"
    assert spec["authority_effect"] == "None"
    assert (
        "inert" in spec["qualification_limit"].lower()
        or "candidate scope" in spec["qualification_limit"].lower()
    )
    trigger = re.compile(spec["target_pattern"])
    assert spec["detection_mechanisms"]["regex_triggers"] == [spec["target_pattern"]]
    assert trigger.search(spec["adversarial_mutation_fixture"])
    assert not trigger.search(spec["repaired_invariant_fixture"])
    assert not trigger.search(spec["benign_control_fixture"])
    native = (REPO / spec["native_test_binding"]).read_text(encoding="utf-8")
    for name in spec["harmful_control_tests"] + spec["benign_control_tests"]:
        assert re.search(r"fn\s+" + re.escape(name) + r"\s*\(", native)
    # Current repaired paths must no longer carry this captured harmful signature.
    for binding in [
        spec["implementation_binding"],
        *spec.get("additional_implementation_bindings", []),
    ]:
        assert not trigger.search((REPO / binding).read_text(encoding="utf-8"))

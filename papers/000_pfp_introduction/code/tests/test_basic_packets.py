import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("basic_packets", Path(__file__).parents[1] / "basic_packets.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_declared_goal_and_negative_controls():
    assert module.main() == 0
    assert module.check(module.example())["property"] == "declared-directed-separation"


@pytest.mark.parametrize("packet", [None, [], {}, {"schema": "other"}])
def test_incomplete_packets(packet):
    assert module.check(packet)["reason"] == "SCHEMA"


@pytest.mark.parametrize("field,value,reason", [
    ("carrier", ["a", "a"], "CARRIER"),
    ("carrier", ["a", True], "CARRIER"),
    ("candidate", ["a", "other", "b"], "RELATION_LABEL"),
    ("candidate", ["a", "separates", []], "SCHEMA"),
    ("goal", ["a", "c"], "OUTSIDE_CARRIER"),
    ("goal", ["a", "a"], "SELF_RELATION"),
    ("relation_label", "", "RELATION_LABEL"),
])
def test_malformed_or_changed_inputs(field, value, reason):
    packet = module.example()
    packet[field] = value
    assert module.check(packet)["reason"] == reason


def test_check_does_not_mutate_proposal():
    packet = module.example(["a", "separates", "c"])
    before = repr(packet)
    module.check(packet)
    assert repr(packet) == before

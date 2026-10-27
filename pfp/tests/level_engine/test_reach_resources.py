"""Relocation changes resource custody without rewriting checker identities."""

from __future__ import annotations

import copy
import hashlib
import json

import pytest

from pfp.infrastructure.tower_research.reach import resources


@pytest.fixture
def checker_registry():
    raw = (resources.reach_root("v2") / "registry" / "checkers.json").read_bytes()
    return raw, json.loads(raw), resources._active_checker_pin()


def test_original_registry_bytes_and_checker_identity_survive_relocation(checker_registry):
    raw, document, pin = checker_registry
    before = copy.deepcopy(document)
    assert pin["resource_package"] == "symbol_game.infrastructure.tower_research.reach"
    assert hashlib.sha256(raw).hexdigest() == pin["sha256"]
    assert pin["sha256"] == "487cca08e88d73e9fbc3e5c5ee7c9327dae5ce334090fc14ea321401ccce4583"

    actual = resources.registry("checkers", version="v2")

    assert actual == before
    checker = actual["checkers"]["stage_000"]
    assert checker["path"] == "symbol_game/infrastructure/adapters/mssn_research/checkers/stage_000.py"
    assert checker["commit"] == "0f39f69a19777766aff39d639a9a1d5c6fa24563"
    assert checker["sha256"] == "sha256:7c5e954b0f86c7505d71ce2d6a26edb5f499cdfe128a18b1001ebcfb3422b4d3"
    assert (resources.reach_root("v2") / "registry" / "checkers.json").read_bytes() == raw


def test_current_owner_requires_a_matching_declared_registry(checker_registry, monkeypatch):
    _, document, pin = checker_registry
    current = copy.deepcopy(document)
    for entry in current["checkers"].values():
        entry["path"] = entry["path"].replace("symbol_game/", "pfp/", 1)
    raw = json.dumps(current).encode("utf-8")
    current_pin = dict(pin, resource_package=resources.__package__, sha256=hashlib.sha256(raw).hexdigest())
    monkeypatch.setattr(resources, "_active_checker_pin", lambda: current_pin)

    resources._verify_active_checkers(raw, current)

    assert document["checkers"]["stage_000"]["path"].startswith("symbol_game/")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("resource_package", "unregistered.infrastructure.tower_research.reach"),
        ("resource_package", "pfp.infrastructure.tower_research.reach.extra"),
        ("resource_package", ["pfp.infrastructure.tower_research.reach"]),
        ("resource_path", "../data/v2/registry/checkers.json"),
        ("sha256", "0" * 64),
        ("version", 1),
    ],
)
def test_corrupted_registry_pin_is_refused(checker_registry, monkeypatch, field, value):
    raw, document, pin = checker_registry
    bad_pin = dict(pin)
    bad_pin[field] = value
    monkeypatch.setattr(resources, "_active_checker_pin", lambda: bad_pin)
    with pytest.raises(ValueError, match="RR-PIN: active checker registry digest or identity differs"):
        resources._verify_active_checkers(raw, document)


@pytest.mark.parametrize("owner", ["symbol_game", "pfp"])
def test_mixed_owner_checker_path_is_refused_even_with_matching_digest(checker_registry, monkeypatch, owner):
    _, document, pin = checker_registry
    wrong_owner = "pfp" if owner == "symbol_game" else "symbol_game"
    for entry in document["checkers"].values():
        entry["path"] = entry["path"].replace("symbol_game/", owner + "/", 1)
    document["checkers"]["stage_000"]["path"] = (
        wrong_owner + "/infrastructure/adapters/mssn_research/checkers/stage_000.py"
    )
    raw = json.dumps(document).encode("utf-8")
    pin = dict(pin, resource_package=owner + ".infrastructure.tower_research.reach", sha256=hashlib.sha256(raw).hexdigest())
    monkeypatch.setattr(resources, "_active_checker_pin", lambda: pin)
    with pytest.raises(ValueError, match="RR-PIN: active checker key, stage, or path differs"):
        resources._verify_active_checkers(raw, document)


def test_registry_byte_tampering_is_refused(checker_registry, monkeypatch):
    raw, document, pin = checker_registry
    monkeypatch.setattr(resources, "_active_checker_pin", lambda: pin)
    with pytest.raises(ValueError, match="RR-PIN: active checker registry digest or identity differs"):
        resources._verify_active_checkers(raw + b"\n", document)

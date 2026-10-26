"""Offline catalog acceptance and adversarial integrity checks. AuthorityEffect: None."""

import json
import socket
from importlib.resources import files
from types import SimpleNamespace

import pytest

from omega_engine_operating_system.adapters.rust_host.ffi import locate_host_binary
from omega_engine_pfp.domain.demos import (
    DemoRefusal,
    refuse_model_functionals,
    strict_descent,
)
from omega_engine_pfp.domain.tower import grammar, parser, wire
from omega_engine_pfp.domain.tower.profile import validate_stage
from omega_engine_pfp.infrastructure.adapters.mssn_research import loader
from omega_engine_pfp.infrastructure.demos.canonical import canonical, digest
from omega_engine_pfp.infrastructure.demos.catalog import lookup, scenarios
from omega_engine_pfp.infrastructure.demos.execution import run, verify
from omega_engine_pfp.use_cases.mssn_demo import evaluate_cases

# The immune scenarios call the native pharmacy detector. With no host binary
# they must refuse with exactly this code, naming the missing binary; with a
# built host (OMEGA_SYMBOL_GAME_HOST or the workspace target) they must run.
NATIVE_PHARMACY_SCENARIOS = frozenset(
    {"antimorphism_farm", "demo_4e_cogsci_autopoiesis", "demo_eis_failure_classes"}
)
RETIRED_ONE_OFF_KINDS = frozenset(
    {
        "quantum",
        "meron-2d",
        "meron-3d",
        "meron-4d",
        "meron-4d-su2",
        "meron-benchmark",
        "cohomology",
    }
)


def _native_host_built() -> bool:
    return not locate_host_binary().is_err


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def refused(*args, **kwargs):
        raise AssertionError("fixture attempted network access")

    # Keep the socket type intact: ssl may import SSLSocket after this fixture.
    monkeypatch.setattr(socket.socket, "connect", refused)
    monkeypatch.setattr(socket.socket, "connect_ex", refused)
    monkeypatch.setattr(socket, "create_connection", refused)
    for name in ("OPENROUTER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.setenv(name, "dummy-offline-key")
    for name in ("OMEGA_FUNCTIONAL_GRAPH_BIN", "OMEGA_FUNCTIONAL_GRAPH_SHA256"):
        monkeypatch.delenv(name, raising=False)


@pytest.mark.parametrize("scenario", scenarios(), ids=lambda s: s.scenario_id)
def test_entire_catalog_runs_and_replays_offline(scenario, tmp_path):
    output = tmp_path / scenario.scenario_id
    receipt = run(scenario.scenario_id, output)
    assert receipt["AuthorityEffect"] == "None"
    assert receipt["result"]["status"] in {"CHECKED", "ILLUSTRATION_ONLY", "TYPED_REFUSAL"}
    if scenario.kind == "native":
        assert receipt["result"]["status"] == "TYPED_REFUSAL"
        assert receipt["result"]["code"] in {
            "FUNCTIONAL_ADAPTER_UNAVAILABLE",
            "FUNCTIONAL_BOUNDARY_UNAVAILABLE",
        }
    elif scenario.kind in RETIRED_ONE_OFF_KINDS:
        assert receipt["result"]["status"] == "TYPED_REFUSAL"
        assert receipt["result"]["code"] == "SCENARIO_RETIRED"
        assert receipt["result"]["detail"] == scenario.scenario_id
    elif scenario.scenario_id in NATIVE_PHARMACY_SCENARIOS and not _native_host_built():
        assert receipt["result"]["status"] == "TYPED_REFUSAL"
        assert receipt["result"]["code"] == "NATIVE_PHARMACY_UNAVAILABLE"
        assert "HOST_BINARY_NOT_FOUND" in receipt["result"]["detail"]
    else:
        assert receipt["result"]["status"] != "TYPED_REFUSAL"
    checked = verify(output / "receipt.json")
    assert checked["status"] == "VERIFIED_FIXTURE" and checked["reproduced"]


def test_pinned_fixture_bytes_survive_custody_and_rehashed_normalization_is_refused(tmp_path):
    output = tmp_path / "cohomology-bytes"
    receipt = run("demo_cohomology_battery", output)
    row = lookup("demo_cohomology_battery")
    original = files(loader.PACKAGE).joinpath(row["fixture_path"]).read_bytes()
    fixture = output / "fixture.json"
    assert fixture.read_bytes() == original
    assert digest(original) == receipt["fixture_sha256"]

    # Equivalent JSON is still different evidence from the catalog's raw-byte pin.
    changed = original + b"\n"
    assert json.loads(changed) == json.loads(original)
    fixture.write_bytes(changed)
    receipt["artifacts_sha256"]["fixture.json"] = digest(changed)
    payload = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    receipt["receipt_sha256"] = digest(canonical(payload))
    path = output / "receipt.json"
    path.write_bytes(canonical(receipt))
    with pytest.raises(DemoRefusal, match="FIXTURE_DIGEST_MISMATCH"):
        verify(path)


def test_all_101_distinct_obligations_and_unconditional_pass_is_killed():
    records = loader.registry()["checkers"]
    assert len({r["sha256"] for r in records}) == 101
    mutant = SimpleNamespace(check=lambda payload: ("PASS", None))
    for level in range(101):
        cases = loader.fixture(level)["cases"]
        results = evaluate_cases(loader.checker(level), cases)
        assert all(r["matches_expectation"] for r in results)
        assert {"positive", "own-negative", "empty", "model-verdict", "inexact"} <= {
            r["case_id"] for r in results
        }
        assert not all(r["matches_expectation"] for r in evaluate_cases(mutant, cases))


def test_changed_checker_byte_and_swapped_registry_entry_are_refused(monkeypatch):
    real = loader.resource
    monkeypatch.setattr(
        loader,
        "resource",
        lambda path: real(path) + b" " if path == "checkers/stage_000.py" else real(path),
    )
    with pytest.raises(DemoRefusal, match="CHECKER_DIGEST_MISMATCH"):
        loader.checker(0)
    registry = json.loads(real("registry.json"))
    registry["checkers"][0], registry["checkers"][1] = (
        registry["checkers"][1],
        registry["checkers"][0],
    )
    monkeypatch.setattr(
        loader,
        "resource",
        lambda path: canonical(registry) if path == "registry.json" else real(path),
    )
    with pytest.raises(DemoRefusal, match="CHECKER_REGISTRY_DIGEST_MISMATCH"):
        loader.checker(0)


def test_receipt_tampering_even_with_recomputed_checksum_is_refused(tmp_path):
    output = tmp_path / "run"
    receipt = run("mss-000", output)
    receipt["result"]["cases"][1]["outcome"] = "PASS"
    path = output / "receipt.json"
    path.write_bytes(canonical(receipt))
    with pytest.raises(DemoRefusal, match="RECEIPT_DIGEST_MISMATCH"):
        verify(path)
    del receipt["receipt_sha256"]
    receipt["receipt_sha256"] = digest(canonical(receipt))
    path.write_bytes(canonical(receipt))
    with pytest.raises(DemoRefusal, match="FIXTURE_REPLAY_MISMATCH"):
        verify(path)


def test_exact_descent_kills_lexicographic_comparison_and_model_claim():
    assert strict_descent("10", "2")
    assert not strict_descent("2", "10")
    assert strict_descent("1/2", "1/10")
    for payload in ({"Phi_1": "0"}, {"outer": [{"Gamma_2": 0}]}, {"Xi": "0"}, {"verified": True}):
        with pytest.raises(DemoRefusal, match="MODEL_FUNCTIONAL_CLAIM"):
            refuse_model_functionals(payload)
    with pytest.raises(DemoRefusal, match="INEXACT_FUNCTIONAL_VALUE"):
        strict_descent(0.2, 0.1)


def test_canonical_ast_and_unregistered_opcode_29():
    assert grammar.Atom is parser.Atom is wire.Atom
    assert grammar.App is parser.App is wire.App
    assert grammar.Diff is parser.Diff is wire.Diff
    assert grammar.parse("op<<1><a>>") == parser.parse_packet("op<<1><a>>")
    with pytest.raises(wire.WireError, match="unknown global opcode"):
        validate_stage(wire.application(29), 100)


def test_output_and_live_guards(tmp_path, monkeypatch):
    with pytest.raises(DemoRefusal, match="OUTPUT_DIRECTORY_OCCUPIED"):
        run("mss-000", tmp_path)
    with pytest.raises(DemoRefusal, match="RESEARCH_EVIDENCE_WRITE_REFUSED"):
        run("mss-000", tmp_path / "research" / "run")
    with pytest.raises(DemoRefusal, match="LIVE_SCENARIO_NOT_SUPPORTED"):
        run("mss-000", tmp_path / "live", live=True)
    monkeypatch.delenv("OPENROUTER_API_KEY")
    with pytest.raises((ValueError, RuntimeError)):
        run("demo_eis_failure_classes", tmp_path / "live", live=True)
    assert not (tmp_path / "live").exists()


def test_live_receipt_verifies_integrity_without_replaying_a_model(tmp_path, monkeypatch):
    """A mocked transport exercises live custody; no provider request is sent."""
    import sys

    if sys.platform != "win32":
        pytest.skip("existing live artifact protector requires Windows DPAPI")
    from omega_engine_woland.infrastructure.providers import openai_compat
    from omega_engine_pfp.infrastructure.demos import execution
    from omega_engine_pfp.infrastructure.trace import gateway_factories
    from omega_engine_pfp.infrastructure.trace.provider_dispatch import (
        scripted_openai_payload,
    )

    def transport(provider, model, request):
        return json.dumps(
            scripted_openai_payload('{"candidate":"finite data"}', model=model)
        ).encode()

    monkeypatch.setattr(openai_compat, "OpenAiCompatTransport", lambda provider: transport)
    original = gateway_factories.live_gateway
    monkeypatch.setattr(
        gateway_factories,
        "live_gateway",
        lambda *args, **kwargs: original(
            *args, **kwargs, pricing_clock=lambda: "2026-09-20T00:00:00.000000Z"
        ),
    )
    output = tmp_path / "live-integrity"
    receipt = run("demo_eis_failure_classes", output, live=True, model="deepseek/deepseek-v4-flash")
    assert receipt["transport"] == "live"
    assert receipt["verification_scope"] == "integrity_only"

    def forbidden(*args, **kwargs):
        raise AssertionError("live verification attempted model replay")

    monkeypatch.setattr(execution, "run", forbidden)
    assert verify(output / "receipt.json") == {
        "status": "INTEGRITY_ONLY",
        "reproduced": False,
        "AuthorityEffect": "None",
        "scenario_id": "demo_eis_failure_classes",
    }

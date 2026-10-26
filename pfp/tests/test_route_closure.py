"""Test suite for PFP Route Closure, Refusal Invariants, and Zero Silent Mocks.

Verifies:
1. ExecuteStagePipelineUseCase fails closed without a catalog (CATALOG_UNAVAILABLE).
2. ExecuteStagePipelineUseCase fails closed for unknown demo identifiers (UNKNOWN_DEMO).
3. ExecuteStagePipelineUseCase fails closed at Stage 5 if host_verifier is None (HOST_VERIFIER_UNAVAILABLE).
4. Stage 5 host checks returning failure properly terminate with BLOCKED_BY_EVIDENCE and all_stages_passed=False.
5. Host verifier exceptions fail closed to INFRASTRUCTURE_FAILURE.
6. Mode checks requiring host verifiers fail closed when verifiers or inputs are absent.
7. PfpController default pipeline execution fails closed at Stage 5 without host verifier injection.
8. RustSymbolGameHost fails closed with Refusal(HOST_SPAWN_FAILED) when binary is missing (zero silent mock fallback).
9. VllmDecodeAdapter fails closed with RuntimeError(EXECUTION_UNAVAILABLE) when fixture_mode is False and runner is None.
10. Exact rational and bigint parsing in cochain domain models strictly reject floats, booleans, and non-exact representations.

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any, Dict

import pytest

from omega_engine_operating_system.adapters.rust_host.ffi import (
    canonical_request_bytes,
)
from omega_engine_operations.domain.rop.result import Refusal
from omega_engine_pfp.controllers.pfp_controller import PfpController
from omega_engine_pfp.domain.cochain import (
    CochainRefusal,
    PromptCellComplex,
    _fraction_to_wire,
    _parse_bigint,
    _parse_fraction,
)
from omega_engine_pfp.domain.kernel.result import (
    RefusalCode,
)
from omega_engine_pfp.domain.ports.decode_control_port import (
    ControlKind,
    DecodeControlSpec,
    GrammarMask,
)
from omega_engine_pfp.domain.stages.stages import Stage5Response
from omega_engine_pfp.ffi import RustSymbolGameHost
from omega_engine_pfp.ffi import (
    evaluate_prompt_cochain_disposition as evaluate_prompt_cochain,
)
from omega_engine_pfp.infrastructure.adapters.decode_controls.vllm_decode_adapter import (
    VllmDecodeAdapter,
)
from omega_engine_pfp.infrastructure.providers import (
    OfflineDeterministicPfpProvider,
)
from omega_engine_pfp.infrastructure.storage import PfpFileSystemStorageAdapter
from omega_engine_pfp.use_cases.execute_stage_pipeline import (
    ExecuteStagePipelineUseCase,
)

# ---------------------------------------------------------------------------
# Test Fixtures & Helpers
# ---------------------------------------------------------------------------

class DummyPassingHostVerifier:
    """Mock host verifier explicitly configured for positive path comparison."""

    def verify(self, demo_id: str, prior_responses: Dict[int, Dict[str, Any]]) -> Stage5Response:
        return Stage5Response(
            demo_id=demo_id,
            should_continue=True,
            host_verdict="PASS",
            exact_checks_passed=True,
        )


class DummyFailingHostVerifier:
    """Mock host verifier simulating rejection by host exact checker."""

    def verify(self, demo_id: str, prior_responses: Dict[int, Dict[str, Any]]) -> Stage5Response:
        return Stage5Response(
            demo_id=demo_id,
            should_continue=False,
            host_verdict="FAIL",
            exact_checks_passed=False,
        )


class CrashingHostVerifier:
    """Mock host verifier raising unexpected internal exception."""

    def verify(self, demo_id: str, prior_responses: Dict[int, Dict[str, Any]]) -> Stage5Response:
        raise RuntimeError("Host verifier subprocess crashed with SIGSEGV")


class DummyCatalog:
    """Explicit catalog recognizing only registered demo IDs."""

    def __init__(self, registered: set[str]):
        self._registered = registered

    def get_demo(self, demo_id: str) -> Any:
        return object() if demo_id in self._registered else None


# ---------------------------------------------------------------------------
# 1. ExecuteStagePipelineUseCase Fail-Closed Route Closure
# ---------------------------------------------------------------------------

def test_pipeline_fails_closed_when_catalog_is_none():
    """ExecuteStagePipelineUseCase without a catalog must return CATALOG_UNAVAILABLE."""
    storage = PfpFileSystemStorageAdapter()
    provider = OfflineDeterministicPfpProvider()
    use_case = ExecuteStagePipelineUseCase(
        storage=storage,
        provider=provider,
        catalog=None,
        host_verifier=DummyPassingHostVerifier(),
    )

    result = use_case.run_pipeline("demo_000", {"raw_seed": "<test>"})
    assert result.is_err
    error = result.unwrap_err()
    assert error.code == RefusalCode.CATALOG_UNAVAILABLE
    assert "catalog" in error.message.lower()


def test_pipeline_fails_closed_for_unknown_demo_id():
    """ExecuteStagePipelineUseCase with an unregistered demo ID must return UNKNOWN_DEMO."""
    storage = PfpFileSystemStorageAdapter()
    provider = OfflineDeterministicPfpProvider()
    catalog = DummyCatalog(registered={"known_demo_1"})
    use_case = ExecuteStagePipelineUseCase(
        storage=storage,
        provider=provider,
        catalog=catalog,
        host_verifier=DummyPassingHostVerifier(),
    )

    result = use_case.run_pipeline("unknown_demo_xyz", {"raw_seed": "<test>"})
    assert result.is_err
    error = result.unwrap_err()
    assert error.code == RefusalCode.UNKNOWN_DEMO
    assert "unknown_demo_xyz" in error.message


def test_pipeline_fails_closed_when_stage5_host_verifier_is_none():
    """Stage 5 execution requires a host verifier; without one, refuse HOST_VERIFIER_UNAVAILABLE."""
    storage = PfpFileSystemStorageAdapter()
    provider = OfflineDeterministicPfpProvider()
    catalog = DummyCatalog(registered={"demo_000"})
    use_case = ExecuteStagePipelineUseCase(
        storage=storage,
        provider=provider,
        catalog=catalog,
        host_verifier=None,  # No host verifier
    )

    # Executing up through Stage 5 must fail closed
    result = use_case.run_pipeline("demo_000", {"raw_seed": "<test>"}, stage_count=5)
    assert result.is_err
    error = result.unwrap_err()
    assert error.code == RefusalCode.HOST_VERIFIER_UNAVAILABLE
    assert error.stage == 5


def test_pipeline_fails_closed_when_host_verdict_fails():
    """When host verifier returns FAIL or exact_checks_passed=False, fail closed with HOST_CHECK_FAILED."""
    storage = PfpFileSystemStorageAdapter()
    provider = OfflineDeterministicPfpProvider()
    catalog = DummyCatalog(registered={"demo_000"})
    use_case = ExecuteStagePipelineUseCase(
        storage=storage,
        provider=provider,
        catalog=catalog,
        host_verifier=DummyFailingHostVerifier(),
    )

    result = use_case.run_pipeline("demo_000", {"raw_seed": "<test>"}, stage_count=5)
    assert result.is_err
    error = result.unwrap_err()
    assert error.code == RefusalCode.HOST_CHECK_FAILED
    assert error.stage == 5
    assert "exact checks did not pass" in error.message


def test_pipeline_fails_closed_when_host_verifier_crashes():
    """An uncaught exception in host_verifier.verify maps to INFRASTRUCTURE_FAILURE at stage 5."""
    storage = PfpFileSystemStorageAdapter()
    provider = OfflineDeterministicPfpProvider()
    catalog = DummyCatalog(registered={"demo_000"})
    use_case = ExecuteStagePipelineUseCase(
        storage=storage,
        provider=provider,
        catalog=catalog,
        host_verifier=CrashingHostVerifier(),
    )

    result = use_case.run_pipeline("demo_000", {"raw_seed": "<test>"}, stage_count=5)
    assert result.is_err
    error = result.unwrap_err()
    assert error.code == RefusalCode.INFRASTRUCTURE_FAILURE
    assert error.stage == 5
    assert "Host verifier raised RuntimeError" in error.message


def test_pipeline_mode_requires_host_verifier():
    """Mode checks requiring host verifier (e.g. mode 14) fail closed if verifier is absent."""
    storage = PfpFileSystemStorageAdapter()
    provider = OfflineDeterministicPfpProvider()
    catalog = DummyCatalog(registered={"DEMO-N02"})

    class HostWithoutRefusalVerifier:
        def verify(self, demo_id, prior):
            return Stage5Response(demo_id=demo_id, should_continue=True, host_verdict="PASS", exact_checks_passed=True)

    use_case = ExecuteStagePipelineUseCase(
        storage=storage,
        provider=provider,
        catalog=catalog,
        host_verifier=HostWithoutRefusalVerifier(),
    )

    # Mode 14 without verify_refusal method on host_verifier must refuse HOST_VERIFIER_UNAVAILABLE
    result = use_case.run_pipeline(
        "DEMO-N02",
        {"raw_seed": "<test>"},
        stage_count=1,
        modes=(14,),
        mode_inputs={14: {"payload": {}}},
    )
    assert result.is_err
    assert result.unwrap_err().code == RefusalCode.HOST_VERIFIER_UNAVAILABLE


def test_pipeline_native_staged_requires_pipeline_runner():
    """native_staged_operad=True with pipeline_runner=None refuses HOST_VERIFIER_UNAVAILABLE."""
    storage = PfpFileSystemStorageAdapter()
    provider = OfflineDeterministicPfpProvider()
    catalog = DummyCatalog(registered={"demo_000"})
    use_case = ExecuteStagePipelineUseCase(
        storage=storage,
        provider=provider,
        catalog=catalog,
        host_verifier=DummyPassingHostVerifier(),
        pipeline_runner=None,
    )

    result = use_case.run_pipeline(
        "demo_000",
        {"raw_seed": "<test>"},
        native_staged_operad=True,
    )
    assert result.is_err
    assert result.unwrap_err().code == RefusalCode.HOST_VERIFIER_UNAVAILABLE


# ---------------------------------------------------------------------------
# 2. PfpController Route Closure
# ---------------------------------------------------------------------------

def test_pfp_controller_defaults_to_fail_closed_stage_five():
    """Default PfpController does not attach a mock host_verifier, so 8-stage pipeline refuses at stage 5."""
    controller = PfpController()
    # The default storage has demo_000 in catalog
    result = controller.execute_pipeline("demo_000", {"raw_seed": "<test>"})
    assert result.is_err
    error = result.unwrap_err()
    assert error.code == RefusalCode.HOST_VERIFIER_UNAVAILABLE
    assert error.stage == 5


# ---------------------------------------------------------------------------
# 3. RustSymbolGameHost & FFI Seam Fail-Closed Invariants
# ---------------------------------------------------------------------------

def test_rust_host_fails_closed_when_binary_does_not_exist():
    """RustSymbolGameHost with a non-existent binary returns HOST_BINARY_NOT_FOUND refusal, not a mock pass."""
    nonexistent = Path("C:/nonexistent/path/to/omega_symbol_game.exe")
    host = RustSymbolGameHost(binary_path=nonexistent)

    res = host.invoke_runtime("canonical_json", {"a": 1})
    assert res.is_err
    refusal = res.unwrap_err()
    assert isinstance(refusal, Refusal)
    assert refusal.code == "HOST_BINARY_NOT_FOUND"


def test_canonical_request_bytes_refuses_floats_fail_closed():
    """Prime host request encoder rejects floats with HOST_REQUEST_NOT_CANONICAL."""
    res = canonical_request_bytes({"ratio": 1.25})
    assert res.is_err
    refusal = res.unwrap_err()
    assert refusal.code == "HOST_REQUEST_NOT_CANONICAL"
    assert "forbids floating point values" in refusal.message


# ---------------------------------------------------------------------------
# 4. VllmDecodeAdapter Zero-Mock & Strict Typing Invariants
# ---------------------------------------------------------------------------

def test_vllm_adapter_fails_closed_without_runner_when_fixture_mode_is_false():
    """VllmDecodeAdapter(fixture_mode=False) raises RuntimeError when no runner is configured."""
    adapter = VllmDecodeAdapter(fixture_mode=False)
    spec = DecodeControlSpec(
        control_kind=ControlKind.JSON_SCHEMA,
        grammar_mask=GrammarMask('{"type": "object"}'),
    )

    with pytest.raises(RuntimeError) as exc_info:
        adapter.apply_decode_control(spec, "prompt")

    assert "EXECUTION_UNAVAILABLE" in str(exc_info.value)


def test_vllm_adapter_refuses_non_bool_fixture_mode():
    """VllmDecodeAdapter requires an exact bool for fixture_mode; rejects int 1 or 0."""
    with pytest.raises(TypeError, match="fixture_mode must be an exact bool"):
        VllmDecodeAdapter(fixture_mode=1)  # type: ignore

    with pytest.raises(TypeError, match="fixture_mode must be an exact bool"):
        VllmDecodeAdapter(fixture_mode=0)  # type: ignore


# ---------------------------------------------------------------------------
# 5. Cochain & Exact Arithmetic Fail-Closed Invariants
# ---------------------------------------------------------------------------

def test_parse_fraction_rejects_floats_and_booleans_fail_closed():
    """_parse_fraction rejects float, bool, and float string representations."""
    with pytest.raises(TypeError, match="Invalid rational type: float"):
        _parse_fraction(1.5)

    with pytest.raises(TypeError, match="Invalid rational type: bool"):
        _parse_fraction(True)

    with pytest.raises(TypeError, match="Invalid rational type: bool"):
        _parse_fraction(False)

    with pytest.raises(ValueError, match="Invalid rational string format"):
        _parse_fraction("1.5")

    with pytest.raises(ValueError, match="Invalid rational string format"):
        _parse_fraction("NaN")

    with pytest.raises(ZeroDivisionError):
        _parse_fraction("1/0")


def test_parse_bigint_rejects_floats_and_booleans_fail_closed():
    """_parse_bigint rejects float, bool, and non-integer strings."""
    with pytest.raises(TypeError, match="Invalid bigint type: float"):
        _parse_bigint(2.0)

    with pytest.raises(TypeError, match="Invalid bigint type: bool"):
        _parse_bigint(True)

    with pytest.raises(TypeError, match="Invalid bigint type: bool"):
        _parse_bigint(False)

    with pytest.raises(ValueError, match="Invalid bigint string"):
        _parse_bigint("2.5")

    with pytest.raises(ValueError, match="Invalid bigint string"):
        _parse_bigint("not_a_number")


def test_fraction_to_wire_exact_representation():
    """_fraction_to_wire formats exact integer strings and num/den strings without floats."""
    assert _fraction_to_wire(5) == "5"
    assert _fraction_to_wire(Fraction(5, 1)) == "5"
    assert _fraction_to_wire(Fraction(3, 4)) == "3/4"
    assert _fraction_to_wire("3/4") == "3/4"

    # Floats are rejected
    with pytest.raises(TypeError):
        _fraction_to_wire(0.75)


def test_evaluate_prompt_cochain_refuses_float_weights():
    """evaluate_prompt_cochain with float weights raises TypeError fail-closed."""
    complex_obj = PromptCellComplex(
        v_count=2,
        e_count=1,
        f_count=0,
        d0_matrix=((Fraction(-1), Fraction(1)),),
        d1_matrix=(),
    )

    with pytest.raises(TypeError, match="Invalid rational type: float"):
        evaluate_prompt_cochain(
            complex=complex_obj,
            cochain=[1.5],  # Float in cochain weights
        )


def test_evaluate_prompt_cochain_refuses_invalid_host():
    """evaluate_prompt_cochain with broken host returns CochainRefusal."""
    complex_obj = PromptCellComplex(
        v_count=2,
        e_count=1,
        f_count=0,
        d0_matrix=((Fraction(-1), Fraction(1)),),
        d1_matrix=(),
    )
    nonexistent = Path("C:/nonexistent/omega_symbol_game.exe")
    fake_host = RustSymbolGameHost(binary_path=nonexistent)

    disposition = evaluate_prompt_cochain(
        complex=complex_obj,
        cochain=[Fraction(1)],
        primal_potential=[],
        dual_witness=[],
        host=fake_host,
    )

    assert isinstance(disposition, CochainRefusal)
    assert disposition.code == "HOST_BINARY_NOT_FOUND"

def test_all_woland_model_routes_keep_pfp_and_confine_direct_io():
    from omega_engine_pfp.infrastructure.architecture_fitness import woland_pfp_route_violations
    assert woland_pfp_route_violations(Path(__file__).resolve().parents[2]) == ()


@pytest.fixture
def woland_route_estate(tmp_path):
    """Copy current owner sources only; never import or execute a sender."""
    import shutil

    from omega_engine_pfp.infrastructure.architecture_fitness import WOLAND_PFP_ROUTES
    root = Path(__file__).resolve().parents[2]
    for relative in {*WOLAND_PFP_ROUTES, 'omega_engine/crates_rs/omega_symbol_game/src/woland_host.rs'}:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / relative, target)
    return tmp_path


@pytest.mark.parametrize('source', [
    'from omega_engine_woland.infrastructure.providers.http import *\npost_json({})\n',
    'from urllib.request import urlopen as send\nfrom json import loads as send\nsend({})\n',
    'from omega_engine_woland.infrastructure.providers.openrouter_transport import openrouter_transport as send\nsend()\n',
    'import openai as client\nclient.OpenAI()\n',
    'from anthropic import Anthropic as Client\nClient()\n',
    'import httpx as h\nh.post("https://example.invalid")\n',
    'from urllib.request import urlopen as send\nsend("https://example.invalid")\n',
    'import urllib.request as http\nhttp.urlopen("https://example.invalid")\n',
    'from omega_engine_woland.infrastructure.providers.http import post_json as send\nsend({})\n',
])
def test_new_unmediated_woland_sender_is_refused_without_executing_it(woland_route_estate, source):
    from omega_engine_pfp.infrastructure.architecture_fitness import woland_pfp_route_violations
    path = woland_route_estate / 'omega_engine_woland/use_cases/new_sender.py'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding='utf-8')
    assert any('new_sender.py' in item for item in woland_pfp_route_violations(woland_route_estate))


@pytest.mark.parametrize('before,after', [
    ('turn = prepare_teamwork_turn(', 'turn = unchecked_turn('),
    ('observed = check_teamwork_reply(', 'observed = unchecked_reply('),
])
def test_removing_a_live_pfp_prepare_or_check_is_detected(woland_route_estate, before, after):
    from omega_engine_pfp.infrastructure.architecture_fitness import woland_pfp_route_violations
    path = woland_route_estate / 'omega_engine_woland/infrastructure/teamwork_remote.py'
    source = path.read_text(encoding='utf-8')
    assert before in source
    path.write_text(source.replace(before, after), encoding='utf-8')
    assert any('RemoteTeamworkExecutor._attempt' in item
               for item in woland_pfp_route_violations(woland_route_estate))


def test_unwrapped_native_live_seats_are_detected(woland_route_estate):
    from omega_engine_pfp.infrastructure.architecture_fitness import woland_pfp_route_violations
    path = woland_route_estate / 'omega_engine/crates_rs/omega_symbol_game/src/woland_host.rs'
    source = path.read_text(encoding='utf-8')
    path.write_text(source.replace('omega_woland::pfp_gateway::PfpSeatExecutor {',
                                   'RoutedSeatExecutor {'), encoding='utf-8')
    assert any('native live seats' in item for item in woland_pfp_route_violations(woland_route_estate))


def test_guard_allows_prose_and_ordinary_provider_metadata(woland_route_estate):
    from omega_engine_pfp.infrastructure.architecture_fitness import woland_pfp_route_violations
    path = woland_route_estate / 'omega_engine_woland/use_cases/provider_notes.py'
    path.write_text('"""Do not call openai.OpenAI or urllib.request.urlopen."""\n', encoding='utf-8')
    assert woland_pfp_route_violations(woland_route_estate) == ()

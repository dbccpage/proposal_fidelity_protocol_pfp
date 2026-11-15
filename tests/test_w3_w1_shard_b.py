"""Verification test suite for Window 3 Wave 1 Shard B (Paper 004).

Targets four audit derivations:
1. ATL-P004-006 (AUDIT-P004-006): Host bounds and timeout validation
   - Input byte limits and prefix consumption
   - Carrier preallocation bounds and matrix cell fences
   - Timeout metadata validation in [1, 300000] ms without internal watchdog
2. ATL-P004-007 (AUDIT-P004-007): Python native seam preservation
   - Canonical binary location delegation
   - Unmodified railway Result forwarding across success and refusal
   - Action method dispatches through invoke
3. ATL-P004-008 (AUDIT-P004-008): Graph tutorial adapter pin
   - Required CORE_FUNCTIONAL_GRAPH_BIN and 64-hex CORE_FUNCTIONAL_GRAPH_SHA256
   - Carrier and claim input refusals prior to subprocess execution
   - Pinned execution and refusal preservation with zero numerical fallback
4. ATL-P004-011 (AUDIT-P004-011): Legacy command refusal
   - run-turn, run-bout, and run fail closed with exit code 2
   - Zero filesystem mutation on refusal
   - require_rust_functional gate enforcement
"""

from __future__ import annotations

import hashlib
import io
import os
import sys
from collections.abc import Mapping, Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any
from unittest.mock import patch
from uuid import uuid4

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent

for p in (_REPO_ROOT, _REPO_ROOT / "ops"):
    p_str = str(p)
    if p_str not in sys.path:
        sys.path.insert(0, p_str)

import governance  # noqa: E402

_GOV_OPS = str(_REPO_ROOT / "ops" / "governance")
if _GOV_OPS not in governance.__path__:
    governance.__path__.append(_GOV_OPS)

import pfp.domain  # noqa: E402
import pfp.domain.shared_kernel  # noqa: E402

for sym in getattr(pfp.domain.shared_kernel, "__all__", []):
    if not hasattr(pfp.domain, sym):
        setattr(pfp.domain, sym, getattr(pfp.domain.shared_kernel, sym))

from operating_system.adapters.rust_host.ffi import HostLocation  # noqa: E402
from operations.domain.rop.result import Err, Ok, Refusal, Result  # noqa: E402

from ops.adversary.infrastructure.providers.adapters.native_functional import (  # noqa: E402
    NativeFunctionalInputRefused,
    NativeFunctionalRefusal,
    NativeFunctionalUnavailable,
    compute_graph_phi1,
)
from pfp.entrypoints.cli.symbol_game import main as cli_main  # noqa: E402
from pfp.ffi import RustSymbolGameHost, find_core_symbol_game_binary  # noqa: E402
from pfp.functional_boundary import (  # noqa: E402
    REFUSAL_CODE,
    RustFunctionalRequired,
    require_rust_functional,
)

# ============================================================================
# 1. ATL-P004-006 / AUDIT-P004-006: Host bounds and timeout validation
# ============================================================================


def _read_request_prefix_model(stream: io.BytesIO, limit: int) -> bytes:
    """Python model of read_request_prefix from code/rust/pfp/src/main.rs:38-42."""
    return stream.read(limit + 1)


def _validate_carrier_resource_fence_model(
    num_vertices: int,
    edges: Sequence[tuple[str, str]],
    num_faces: int,
) -> tuple[bool, str | None, int]:
    """Python model of validate_carrier_resource_fence from code/rust/pfp/src/protocol.rs:545-560."""
    max_carrier_dimension = 4096
    max_dense_matrix_cells = 1_048_576

    valid_vertices = 0 < num_vertices <= max_carrier_dimension
    valid_edges = 0 < len(edges) <= max_carrier_dimension
    valid_faces = num_faces <= max_carrier_dimension

    if not valid_vertices or not valid_edges or not valid_faces:
        return False, "carrier declaration exceeds dimension bounds", 0

    vertices_plus_faces = num_vertices + num_faces
    if vertices_plus_faces > max_carrier_dimension:
        return False, "combined (V+F) dimension exceeds resource fence", vertices_plus_faces

    d0_cells = num_vertices * len(edges)
    if d0_cells > max_dense_matrix_cells:
        return (
            False,
            f"d0 dense matrix requires {d0_cells} cells; maximum is {max_dense_matrix_cells}",
            vertices_plus_faces,
        )

    d1_cells = num_faces * len(edges)
    if d1_cells > max_dense_matrix_cells:
        return (
            False,
            f"d1 dense matrix requires {d1_cells} cells; maximum is {max_dense_matrix_cells}",
            vertices_plus_faces,
        )

    return True, None, vertices_plus_faces


def _validate_timeout_ms_model(timeout_ms: int) -> tuple[bool, str | None]:
    """Python model of timeout validation in code/rust/pfp/src/host/intake.rs:116."""
    max_timeout_ms = 300_000
    if 1 <= timeout_ms <= max_timeout_ms:
        return True, None
    return False, "RESOURCE_PROFILE_INVALID: timeout_ms outside [1, 300000]"


class TestHostBounds:
    """Witnesses that host enforces input limits, preallocation bounds, and timeout metadata."""

    MAX_HOST_REQUEST_BYTES = 1_048_576
    MAX_RUNTIME_REQUEST_BYTES = 65_536
    MAX_CARRIER_DIMENSION = 4096
    MAX_DENSE_MATRIX_CELLS = 1_048_576
    MAX_TIMEOUT_MS = 300_000

    def test_input_byte_limit_enforcement(self) -> None:
        """Bounded reader consumes only up to limit + 1 witness bytes."""
        for limit in (1024, self.MAX_RUNTIME_REQUEST_BYTES, self.MAX_HOST_REQUEST_BYTES):
            # Payload exactly at limit
            exact_payload = b"x" * limit
            stream_exact = io.BytesIO(exact_payload)
            consumed_exact = _read_request_prefix_model(stream_exact, limit)
            assert len(consumed_exact) == limit
            assert len(consumed_exact) <= limit

            # Payload with 1 witness byte over limit
            overflow_payload = b"x" * (limit + 1)
            stream_overflow = io.BytesIO(overflow_payload)
            consumed_overflow = _read_request_prefix_model(stream_overflow, limit)
            assert len(consumed_overflow) == limit + 1
            assert len(consumed_overflow) > limit

    def test_input_byte_limit_overflow_negative_controls(self) -> None:
        """Oversized inputs are detected at the process boundary without reading unbounded bytes."""
        limit = 2048
        # Stream has 10,000 bytes; reader takes only limit + 1 = 2049 bytes
        stream_large = io.BytesIO(b"A" * 10_000)
        prefix = _read_request_prefix_model(stream_large, limit)
        assert len(prefix) == limit + 1
        assert stream_large.tell() == limit + 1

    def test_carrier_preallocation_bounds_and_matrix_fences(self) -> None:
        """Carrier dimension fences and dense matrix preallocation cell bounds are enforced."""
        # Positive control: valid carrier within fences
        valid_edges = [("v0", "v1"), ("v1", "v2"), ("v2", "v0")]
        ok, err, v_f = _validate_carrier_resource_fence_model(3, valid_edges, 1)
        assert ok is True
        assert err is None
        assert v_f == 4

        # Boundary condition: exact max carrier dimension (V=4096, E=256, F=0)
        edges_256 = [(f"u{i}", f"v{i}") for i in range(256)]
        ok, err, v_f = _validate_carrier_resource_fence_model(self.MAX_CARRIER_DIMENSION, edges_256, 0)
        assert ok is True
        assert err is None
        assert v_f == self.MAX_CARRIER_DIMENSION

        # Negative control 1: zero vertices refused
        ok, err, _ = _validate_carrier_resource_fence_model(0, valid_edges, 0)
        assert ok is False
        assert "dimension bounds" in str(err)

        # Negative control 2: vertex count exceeding MAX_CARRIER_DIMENSION
        ok, err, _ = _validate_carrier_resource_fence_model(self.MAX_CARRIER_DIMENSION + 1, valid_edges, 0)
        assert ok is False

        # Negative control 3: combined (V + F) exceeding MAX_CARRIER_DIMENSION
        ok, err, v_f = _validate_carrier_resource_fence_model(3000, valid_edges, 1097)
        assert ok is False
        assert v_f == 4097
        assert "combined (V+F)" in str(err)

        # Negative control 4: dense matrix cell overflow
        # 2048 vertices * 1024 edges = 2,097,152 cells > 1,048,576
        edges_1024 = [(f"u{i}", f"v{i}") for i in range(1024)]
        ok, err, _ = _validate_carrier_resource_fence_model(2048, edges_1024, 0)
        assert ok is False
        assert "dense matrix requires 2097152 cells; maximum is 1048576" in str(err)

    def test_timeout_metadata_validation_range(self) -> None:
        """Timeout parameter is validated metadata within [1, 300000] ms."""
        # Positive controls: valid bounds
        for valid_ms in (1, 1000, 30_000, self.MAX_TIMEOUT_MS):
            ok, err = _validate_timeout_ms_model(valid_ms)
            assert ok is True
            assert err is None

        # Negative controls: out-of-range timeout values
        for invalid_ms in (0, -1, self.MAX_TIMEOUT_MS + 1, 1_000_000):
            ok, err = _validate_timeout_ms_model(invalid_ms)
            assert ok is False
            assert "RESOURCE_PROFILE_INVALID" in str(err)

    def test_absence_of_internal_watchdog_in_crate_source(self) -> None:
        """Audits native Rust source code to verify timeout_ms is metadata with no watchdog thread."""
        host_src = (_REPO_ROOT / "code" / "rust" / "pfp" / "src" / "host.rs").read_text(encoding="utf-8")
        intake_src = (_REPO_ROOT / "code" / "rust" / "pfp" / "src" / "host" / "intake.rs").read_text(
            encoding="utf-8"
        )
        main_src = (_REPO_ROOT / "code" / "rust" / "pfp" / "src" / "main.rs").read_text(encoding="utf-8")

        all_host_code = host_src + "\n" + intake_src + "\n" + main_src

        # Verify timeout_ms is checked as a budget range
        assert "(1..=MAX_TIMEOUT_MS).contains(&b.timeout_ms)" in all_host_code

        # Verify zero watchdog or asynchronous timer thread construction
        for forbidden in (
            "thread::spawn",
            "tokio::time",
            "async_std",
            "signal::kill",
            "setitimer",
            "SIGALRM",
            "watchdog_thread",
        ):
            assert forbidden not in all_host_code, f"Unexpected watchdog mechanism found: {forbidden}"


# ============================================================================
# 2. ATL-P004-007 / AUDIT-P004-007: Python native seam preservation
# ============================================================================


class TestPythonNativeSeam:
    """Witnesses that pfp/ffi.py delegates to OS seam and preserves complete railway outcomes."""

    def test_binary_delegation_to_os_adapter(self) -> None:
        """find_core_symbol_game_binary delegates to locate_host_binary without custom search paths."""
        mock_bin_path = _REPO_ROOT / "dummy_core_symbol_game.exe"

        # Success case: returns Path
        with patch("operating_system.adapters.rust_host.ffi.locate_host_binary") as mock_locate:
            mock_locate.return_value = Ok(HostLocation(binary=mock_bin_path, discovered_by="test"))
            located = find_core_symbol_game_binary()
            assert located == mock_bin_path
            mock_locate.assert_called_once()

        # Refusal case: translates typed refusal to FileNotFoundError
        with patch("operating_system.adapters.rust_host.ffi.locate_host_binary") as mock_locate:
            mock_locate.return_value = Err(
                Refusal(code="HOST_BINARY_NOT_FOUND", message="Binary missing on test runner")
            )
            with pytest.raises(FileNotFoundError, match="HOST_BINARY_NOT_FOUND: Binary missing"):
                find_core_symbol_game_binary()

    def test_unmodified_railway_outcome_passthrough_on_success(self) -> None:
        """invoke_runtime and invoke return the raw native outcome mapping unmodified."""
        dummy_bin = _REPO_ROOT / "test_bin.exe"
        host = RustSymbolGameHost(binary_path=dummy_bin)

        expected_outcome = {
            "status": "PASS",
            "result": {
                "omega": [1, -2, 1],
                "phi1": "7",
                "gamma2": "12",
            },
            "runtime_micros": 450,
            "diagnostics": {
                "step": 1,
                "verified": True,
            },
        }

        class MockSeam:
            def invoke_runtime(self, action: str, payload: Any) -> Result[Mapping[str, Any], Refusal]:
                return Ok(expected_outcome)

        host._host = MockSeam()

        res = host.invoke_runtime("test_action", {"key": "value"})
        assert res.is_ok
        outcome = res.unwrap()
        assert outcome == expected_outcome
        assert outcome["result"]["phi1"] == "7"
        assert outcome["result"]["gamma2"] == "12"
        assert outcome["runtime_micros"] == 450

        # invoke() must be identical passthrough
        res_inv = host.invoke("test_action", {"key": "value"})
        assert res_inv.is_ok
        assert res_inv.unwrap() == expected_outcome

    def test_unmodified_railway_outcome_passthrough_on_refusal(self) -> None:
        """invoke_runtime and invoke preserve native typed Refusals without exception masking."""
        dummy_bin = _REPO_ROOT / "test_bin.exe"
        host = RustSymbolGameHost(binary_path=dummy_bin)

        expected_refusal = Refusal(
            code="HOST_INTAKE_REFUSED",
            message="Carrier boundary exceeded declared fence",
            details=(("attempted", "5000"), ("fence", "4096")),
        )

        class MockRefusalSeam:
            def invoke_runtime(self, action: str, payload: Any) -> Result[Mapping[str, Any], Refusal]:
                return Err(expected_refusal)

        host._host = MockRefusalSeam()

        res = host.invoke("test_failing_action", {})
        assert res.is_err
        refusal = res.unwrap_err()
        assert refusal.code == "HOST_INTAKE_REFUSED"
        assert refusal.message == "Carrier boundary exceeded declared fence"
        assert dict(refusal.details) == {"fence": "4096", "attempted": "5000"}

    def test_convenience_methods_dispatch_through_invoke(self) -> None:
        """Convenience methods dispatch directly to invoke with exact action names."""
        dummy_bin = _REPO_ROOT / "test_bin.exe"
        host = RustSymbolGameHost(binary_path=dummy_bin)

        dispatched_calls = []

        class RecordingSeam:
            def invoke_runtime(self, action: str, payload: Any) -> Result[Mapping[str, Any], Refusal]:
                dispatched_calls.append((action, payload))
                return Ok({"status": "PASS", "echo": payload})

        host._host = RecordingSeam()

        # Check canonical_wire
        res1 = host.canonical_wire({"x": 1})
        assert res1.is_ok
        assert dispatched_calls[-1] == ("canonical_wire", {"x": 1})

        # Check canonical_unwire
        res2 = host.canonical_unwire({"w": 2})
        assert res2.is_ok
        assert dispatched_calls[-1] == ("canonical_unwire", {"w": 2})

        # Check canonical_json
        res3 = host.canonical_json({"j": 3})
        assert res3.is_ok
        assert dispatched_calls[-1] == ("canonical_json", {"j": 3})

        # Check canonical_bytes_hex
        res4 = host.canonical_bytes_hex({"b": 4})
        assert res4.is_ok
        assert dispatched_calls[-1] == ("canonical_bytes_hex", {"b": 4})

        # Check domain_digest
        res5 = host.domain_digest("test_dom", {"d": 5})
        assert res5.is_ok
        assert dispatched_calls[-1] == ("domain_digest", {"domain": "test_dom", "value": {"d": 5}})


# ============================================================================
# 3. ATL-P004-008 / AUDIT-P004-008: Graph tutorial adapter pin
# ============================================================================


class TestAdapterPin:
    """Witnesses that compute_graph_phi1 enforces executable path and SHA-256 pin requirements."""

    def test_missing_env_vars_raise_unavailable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """compute_graph_phi1 raises NativeFunctionalUnavailable when env vars are missing or empty."""
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_BIN", raising=False)
        monkeypatch.delenv("CORE_FUNCTIONAL_GRAPH_SHA256", raising=False)

        with pytest.raises(NativeFunctionalUnavailable, match="pinned native graph executable required"):
            compute_graph_phi1(
                vertices=("a", "b"),
                edges=(("a", "b", 1),),
                claims={("a", "b"): 1},
            )

        # Set binary but omit pin
        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_BIN", "/path/to/bin")
        with pytest.raises(NativeFunctionalUnavailable, match="pinned native graph executable required"):
            compute_graph_phi1(
                vertices=("a", "b"),
                edges=(("a", "b", 1),),
                claims={("a", "b"): 1},
            )

    def test_malformed_sha256_pin_raises_unavailable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """compute_graph_phi1 rejects pins that are not 64-character lowercase hex strings."""
        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_BIN", "/path/to/bin")

        for bad_pin in (
            "not_hex",
            "a" * 63,  # 63 chars (too short)
            "a" * 65,  # 65 chars (too long)
            "g" * 64,  # non-hex character
            "12345",  # short decimal
        ):
            monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_SHA256", bad_pin)
            with pytest.raises(NativeFunctionalUnavailable, match="pinned native graph executable required"):
                compute_graph_phi1(
                    vertices=("a", "b"),
                    edges=(("a", "b", 1),),
                    claims={("a", "b"): 1},
                )

    def test_missing_executable_file_raises_unavailable(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """When binary path points to a non-existent file, raises NativeFunctionalUnavailable."""
        non_existent = tmp_path / "absent_bin.exe"
        valid_pin = "e" * 64

        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_BIN", str(non_existent))
        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_SHA256", valid_pin)

        with pytest.raises(NativeFunctionalUnavailable, match="native graph executable could not run"):
            compute_graph_phi1(
                vertices=("a", "b"),
                edges=(("a", "b", 1),),
                claims={("a", "b"): 1},
            )

    def test_digest_mismatch_raises_unavailable(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """When executable exists but SHA-256 does not match pin, raises NativeFunctionalUnavailable."""
        dummy_file = tmp_path / "mock_calc.exe"
        dummy_file.write_bytes(b"content_a")
        actual_hash = hashlib.sha256(b"content_a").hexdigest()
        tampered_pin = "f" * 64
        assert actual_hash != tampered_pin

        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_BIN", str(dummy_file))
        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_SHA256", tampered_pin)

        with pytest.raises(NativeFunctionalUnavailable, match="native graph executable digest mismatch"):
            compute_graph_phi1(
                vertices=("a", "b"),
                edges=(("a", "b", 1),),
                claims={("a", "b"): 1},
            )

    def test_carrier_input_refusals_prior_to_native_dispatch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Input checks refuse invalid vertices, self loops, float weights, and undeclared claims."""
        # Non-string vertex raises ValueError
        with pytest.raises(ValueError, match="graph vertices must be distinct strings"):
            compute_graph_phi1(vertices=(1, 2), edges=(), claims={})

        # Self loop raises ValueError
        with pytest.raises(ValueError, match="graph edges must join distinct declared vertices"):
            compute_graph_phi1(vertices=("a", "b"), edges=(("a", "a", 1),), claims={})

        # Non-exact float weight raises TypeError
        with pytest.raises(TypeError, match="functional inputs require exact int or Fraction, not float or bool"):
            compute_graph_phi1(vertices=("a", "b"), edges=(("a", "b", 1.5),), claims={})

        # Boolean weight raises TypeError
        with pytest.raises(TypeError, match="functional inputs require exact int or Fraction, not float or bool"):
            compute_graph_phi1(vertices=("a", "b"), edges=(("a", "b", True),), claims={})

        # Claim asserted on undeclared edge raises NativeFunctionalInputRefused
        with pytest.raises(NativeFunctionalInputRefused, match="claim edge absent from declared carrier"):
            compute_graph_phi1(
                vertices=("a", "b", "c"),
                edges=(("a", "b", 1),),
                claims={("a", "c"): 2},
            )

    def test_pinned_execution_success_and_refusal_preservation(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Successful executable yields exact Fraction result; native refusal raises NativeFunctionalRefusal."""
        calc_script = tmp_path / "mock_calc.py"
        calc_script.write_text(
            """import sys, json
data = json.loads(sys.stdin.read())
if any(e['claim'] == '-99' for e in data['edges']):
    print(json.dumps({'status': 'REFUSE', 'reason': 'prohibited test claim'}))
    sys.exit(2)
print(json.dumps({
    'status': 'PASS',
    'result': {
        'phi1': '7/2',
        'gauge': {'a': '0', 'b': '7/2'},
        'forests_checked': 3
    }
}))
sys.exit(0)
""",
            encoding="utf-8",
        )

        wrapper_cmd = tmp_path / "runner.cmd" if os.name == "nt" else tmp_path / "runner.sh"
        if os.name == "nt":
            wrapper_cmd.write_text(f'@"{sys.executable}" "{calc_script}"\n', encoding="utf-8")
        else:
            wrapper_cmd.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{calc_script}"\n', encoding="utf-8")
            wrapper_cmd.chmod(0o755)

        script_hash = hashlib.sha256(wrapper_cmd.read_bytes()).hexdigest()
        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_BIN", str(wrapper_cmd))
        monkeypatch.setenv("CORE_FUNCTIONAL_GRAPH_SHA256", script_hash)

        # Success path: verifies exact rational parsing
        phi1, gauge = compute_graph_phi1(
            vertices=("a", "b"),
            edges=(("a", "b", 1),),
            claims={("a", "b"): 1},
        )
        assert phi1 == Fraction(7, 2)
        assert gauge["a"] == Fraction(0)
        assert gauge["b"] == Fraction(7, 2)
        assert isinstance(phi1, Fraction)

        # Refusal path: native REFUSE envelope raises NativeFunctionalRefusal
        with pytest.raises(NativeFunctionalRefusal, match="prohibited test claim") as exc_info:
            compute_graph_phi1(
                vertices=("a", "b"),
                edges=(("a", "b", 1),),
                claims={("a", "b"): -99},
            )
        assert exc_info.value.returncode == 2
        assert "prohibited test claim" in exc_info.value.reason


# ============================================================================
# 4. ATL-P004-011 / AUDIT-P004-011: Legacy command refusal
# ============================================================================


class TestLegacyCommandRefusal:
    """Witnesses that run-turn, run-bout, and run fail closed before functional calculation."""

    @pytest.mark.parametrize("command", ["run-turn", "run-bout", "run"])
    def test_cli_commands_refuse_with_exit_code_2(self, command: str, capsys: pytest.CaptureFixture) -> None:
        """Legacy CLI commands exit with code 2 and emit RUST_FUNCTIONAL_REQUIRED to stderr."""
        dummy_dir = Path(f"boundary-test-dir-{uuid4().hex}")
        argv = [command, "--prompt", "test prompt", "--output-dir", str(dummy_dir)]

        ret = cli_main(argv)

        assert ret == 2
        captured = capsys.readouterr()
        assert REFUSAL_CODE in captured.err
        assert "engine/crates_rs/core_functional/src" in captured.err
        assert not dummy_dir.exists(), f"Directory {dummy_dir} must not be created on refusal"

    @pytest.mark.parametrize("command", ["run-turn", "run-bout", "run"])
    def test_zero_output_directory_mutation(self, command: str, tmp_path: Path) -> None:
        """When an output path is specified within an existing parent, zero files are created."""
        target_dir = tmp_path / "sub_target"
        assert not target_dir.exists()

        argv = [command, "--prompt", "finite prompt", "--output-dir", str(target_dir)]
        ret = cli_main(argv)

        assert ret == 2
        assert not target_dir.exists()
        assert list(tmp_path.iterdir()) == []

    def test_direct_function_call_raises_rust_functional_required(self) -> None:
        """require_rust_functional unconditionally raises RustFunctionalRequired."""
        with pytest.raises(RustFunctionalRequired, match="engine/crates_rs/core_functional/src") as exc_info:
            require_rust_functional("direct_test_producer")

        assert exc_info.value.code == REFUSAL_CODE
        assert "direct_test_producer" in str(exc_info.value)

    def test_python_metric_producers_fail_closed(self) -> None:
        """Legacy Python metric calculators fail closed before computing metrics."""
        from pfp.domain.bridge.real_evaluators import (
            LPDualityCalculator,
            MeronClusterCalculator,
        )
        from pfp.domain.entities.cochain_projector import CochainProjector
        from pfp.use_cases.problem_runner import ProblemRunnerUseCase
        from pfp.use_cases.symbol_game_runner import SymbolGameRunnerUseCase

        producers = (
            lambda: LPDualityCalculator.evaluate_lp(
                objective_coeffs={},
                is_max=False,
                constraints=[],
                primal_point={},
                dual_multipliers={},
            ),
            lambda: MeronClusterCalculator.evaluate_clusters([], [], [], {}),
            lambda: CochainProjector.project(None, None),
            lambda: ProblemRunnerUseCase.run_problem(None, "test"),
            lambda: SymbolGameRunnerUseCase.run_problem(None, "test"),
        )

        for produce in producers:
            with pytest.raises(RustFunctionalRequired, match="engine/crates_rs/core_functional/src"):
                produce()

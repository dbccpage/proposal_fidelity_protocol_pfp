"""Presentation transport never owns process selection or rewrites input custody."""

from __future__ import annotations

import json

import pytest

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal
from omega_engine_operating_system.adapters.rust_host import ffi
from omega_engine_pfp.entrypoints.api.router import SymbolGameApiRouter
from omega_engine_pfp.entrypoints.cli import host_cli


def test_detector_request_preserves_raw_bytes_and_full_context(monkeypatch):
    raw = b'{ "candidate": {}, "context": {"seen_semantic_digests":["abc"],"host_replay_receipt":null}}'
    seen = []

    def run(self, args, stdin_bytes):
        seen.append((args, stdin_bytes, self.BINARY_NAME))
        return Ok({"schema_version": "omega.symgam.detect-report.v1", "authority_effect": "None"})

    monkeypatch.setattr(ffi.SymgamHost, "_run", run)
    result = host_cli.run_host(["detect"], stdin=raw)
    assert result.is_ok
    assert seen == [(["detect"], raw, "symgam")]


@pytest.mark.parametrize(
    "mode,raw,code",
    [
        ("invoke", b"{}", "HOST_MODE_UNSUPPORTED"),
        ("detect", None, "HOST_REQUEST_NOT_BYTES"),
        ("detect", b"x" * (ffi.MAX_REQUEST_BYTES + 1), "HOST_REQUEST_TOO_LARGE"),
    ],
)
def test_request_fences_refuse_before_process(monkeypatch, mode, raw, code):
    def forbidden(*args, **kwargs):
        pytest.fail("a rejected request cannot spawn")

    monkeypatch.setattr(ffi.SymgamHost, "_run", forbidden)
    result = ffi.SymgamHost().request(mode, raw)
    assert result.is_err
    assert result.unwrap_err().code == code


def test_cli_retains_native_refusal_as_output(tmp_path, monkeypatch, capsys):
    source = tmp_path / "candidate.json"
    source.write_bytes(b"{}")
    native = {"refused": True, "code": "REQUEST_SHAPE_INVALID", "authority_effect": "None"}
    monkeypatch.setattr(ffi.SymgamHost, "request", lambda self, mode, raw_bytes=None: Ok(native))
    assert host_cli.main(["detect", str(source)]) == 0
    capture = capsys.readouterr()
    assert json.loads(capture.out) == native
    assert capture.err == ""


def test_cli_missing_host_is_typed_stderr(monkeypatch, capsys):
    monkeypatch.setattr(
        ffi.SymgamHost,
        "request",
        lambda self, mode, raw_bytes=None: Err(
            Refusal(code="HOST_BINARY_NOT_FOUND", message="symgam unavailable")
        ),
    )
    assert host_cli.main(["describe"]) == 2
    capture = capsys.readouterr()
    assert capture.out == ""
    assert json.loads(capture.err)["code"] == "HOST_BINARY_NOT_FOUND"


def test_lookup_selects_symgam_without_main_host_fallback(monkeypatch, tmp_path):
    calls = []

    def locate(explicit=None, binary_name=ffi.CRATE_NAME):
        calls.append(binary_name)
        return Ok(ffi.HostLocation(tmp_path / "symgam", "fixture"))

    monkeypatch.setattr(ffi, "locate_host_binary", locate)
    assert host_cli.locate_symgam() == tmp_path / "symgam"
    assert calls == ["symgam"]


def test_health_advertises_only_dispatched_routes():
    routes = SymbolGameApiRouter.health().data["operations"]
    assert "POST /api/code_change/evaluate" not in routes
    for route in routes:
        method, path = route.split(" ", 1)
        assert SymbolGameApiRouter.dispatch(method, path, {}).status_code != 404

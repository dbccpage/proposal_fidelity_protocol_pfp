"""The symbol-game FFI adapter must not be a second place that finds the host.

`RULE_FFI_SEAM_ISOLATION_001` and the Parity Seam Isolation Invariant give one
module the job of locating and spawning the native host:
`operating_system/adapters/rust_host/ffi.py`.

This adapter had grown its own four-path search over `target/{debug,release}`.
Two answers to "where is the host" is one too many, and the drift was not
theoretical: the local copy ignored `CORE_SYMBOL_GAME_HOST`, which CLAUDE.md
documents as the supported way to point at a binary built elsewhere. Anyone
relying on that variable was silently served a stale `target/debug` build, or
told the host was missing while holding a perfectly good path to it.

AuthorityEffect: None.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from operations.domain.rop.result import Err, Ok, Refusal
from operating_system.adapters.rust_host import ffi as native_host
from pfp.ffi import (
    RustSymbolGameHost,
    find_core_symbol_game_binary,
)


def test_the_environment_override_is_honoured(tmp_path: Path) -> None:
    """The regression. The previous four-path search never read this variable."""
    stand_in = tmp_path / "core_symbol_game.exe"
    stand_in.write_bytes(b"")

    previous = os.environ.get("CORE_SYMBOL_GAME_HOST")
    os.environ["CORE_SYMBOL_GAME_HOST"] = str(stand_in)
    try:
        assert find_core_symbol_game_binary() == stand_in
    finally:
        if previous is None:
            os.environ.pop("CORE_SYMBOL_GAME_HOST", None)
        else:
            os.environ["CORE_SYMBOL_GAME_HOST"] = previous


def test_a_missing_host_carries_the_seam_refusal_code(tmp_path: Path) -> None:
    """A missing binary is a refusal with a code, not a bare path dump.

    The adapter's callers expect an exception, so the refusal is translated at
    this boundary -- but the code survives, which is what lets a caller tell
    "not built yet" from "looked in the wrong place".
    """
    previous = os.environ.get("CORE_SYMBOL_GAME_HOST")
    os.environ["CORE_SYMBOL_GAME_HOST"] = str(tmp_path / "does-not-exist.exe")
    try:
        with pytest.raises(FileNotFoundError) as caught:
            find_core_symbol_game_binary()
        assert "HOST_BINARY_NOT_FOUND" in str(caught.value) or "not exist" in str(
            caught.value
        )
    finally:
        if previous is None:
            os.environ.pop("CORE_SYMBOL_GAME_HOST", None)
        else:
            os.environ["CORE_SYMBOL_GAME_HOST"] = previous


def test_this_module_does_not_locate_the_host_itself() -> None:
    """No second copy of the search may reappear.

    Asserted against the source because the failure mode is someone helpfully
    re-adding a fallback list when the delegation looks like indirection.
    """
    import pfp.ffi as adapter

    source = Path(adapter.__file__).read_text(encoding="utf-8")
    assert "locate_host_binary" in source, "the adapter must delegate the lookup"

    function = source.split("def find_core_symbol_game_binary", 1)[1].split(
        "\nclass ", 1
    )[0]
    # Skip the docstring: it explains the removed search, so scanning it would
    # match the very prose describing why the search is gone.
    code = function.split('"""', 2)[2] if function.count('"""') >= 2 else function

    for smell in [
        '"debug"',
        '"release"',
        "target/debug",
        "target/release",
        "candidates",
    ]:
        assert smell not in code, (
            f"{smell!r} is back in the lookup: the adapter is searching for the "
            "host again instead of asking the seam that owns that job"
        )


def test_action_adapter_does_not_spawn_or_extract_native_results() -> None:
    import pfp.ffi as adapter

    source = Path(adapter.__file__).read_text(encoding="utf-8")
    assert "subprocess" not in source
    assert "return self._host.invoke_runtime(action, payload)" in source
    assert 'outcome.get("result")' not in source
    assert "RustHostError" not in source
    assert "last_outcome" not in source


@pytest.mark.parametrize(
    ("method", "args", "kwargs", "action", "payload"),
    [
        ("canonical_wire", ({"a": 1.25},), {}, "canonical_wire", {"a": 1.25}),
        ("canonical_unwire", (["wire"],), {}, "canonical_unwire", ["wire"]),
        ("canonical_json", ({"a": 1},), {}, "canonical_json", {"a": 1}),
        ("canonical_bytes_hex", ({"a": 1},), {}, "canonical_bytes_hex", {"a": 1}),
        (
            "domain_digest",
            ("domain", {"a": 1}),
            {},
            "domain_digest",
            {"domain": "domain", "value": {"a": 1}},
        ),
        ("parse_unified_diff", ("patch",), {}, "parse_unified_diff", "patch"),
        (
            "create_code_change_proposal",
            (),
            {
                "task_id": "task",
                "objective": "objective",
                "base_revision": "base",
                "owned_paths": ("a.py",),
                "protected_paths": ("protected",),
            },
            "create_code_change_proposal",
            {
                "task_id": "task",
                "objective": "objective",
                "base_revision": "base",
                "owned_paths": ["a.py"],
                "protected_paths": ["protected"],
                "candidate_budget": 4,
                "operation_budget": 16,
                "required_gates": ["gate_ownership", "gate_syntax"],
            },
        ),
        (
            "submit_patch_candidate",
            (),
            {
                "run_root": {"task_id": "task"},
                "expected_task_packet_sha256": "digest",
                "candidate_id": "candidate",
                "producer_id": "producer",
                "patch_text": "patch",
            },
            "submit_patch_candidate",
            {
                "run_root": {"task_id": "task"},
                "expected_task_packet_sha256": "digest",
                "candidate_id": "candidate",
                "producer_id": "producer",
                "patch_text": "patch",
            },
        ),
        (
            "evaluate_patch_gates",
            (),
            {
                "run_root": {"task_id": "task"},
                "expected_task_packet_sha256": "digest",
                "expected_run_root_digest": "rolling",
                "patch_artifact": {"candidate_id": "candidate"},
            },
            "evaluate_patch_gates",
            {
                "run_root": {"task_id": "task"},
                "expected_task_packet_sha256": "digest",
                "expected_run_root_digest": "rolling",
                "patch_artifact": {"candidate_id": "candidate"},
            },
        ),
        (
            "intake_research_sources",
            ("bundle", [("source", "path", "text")]),
            {},
            "intake_research_sources",
            {"bundle_id": "bundle", "sources": [["source", "path", "text"]]},
        ),
        (
            "score_discrete_proposal",
            (["obstruction"], {"proposal_id": "p"}, ["constructor"]),
            {},
            "score_discrete_proposal",
            {
                "obstructions": ["obstruction"],
                "proposal": {"proposal_id": "p"},
                "admitted_constructors": ["constructor"],
            },
        ),
        (
            "rank_candidate_proposals",
            (["obstruction"], [{"proposal_id": "p"}]),
            {},
            "rank_candidate_proposals",
            {
                "obstructions": ["obstruction"],
                "proposals": [{"proposal_id": "p"}],
                "admitted_constructors": None,
            },
        ),
        (
            "classify_gauge_board",
            ({"rows": 1}, {"rows": 2}, (True, False)),
            {},
            "classify_gauge_board",
            {"d0": {"rows": 1}, "d1": {"rows": 2}, "cochain": [True, False]},
        ),
    ],
)
def test_all_convenience_methods_delegate_complete_outcomes(
    method, args, kwargs, action, payload, tmp_path, monkeypatch
) -> None:
    """Adapter wiring only; the injected native outcome is not execution proof."""
    outcome = {
        "schema_version": native_host.RUNTIME_OUTCOME_SCHEMA,
        "action": action,
        "success": False,
        "result": None,
        "error": "retained native failure",
        "authority_effect": "None",
    }
    crossing = Ok(outcome)
    calls = []

    def invoke(host, actual_action, actual_payload):
        calls.append((actual_action, actual_payload))
        assert host._timeout_seconds == 30
        return crossing

    monkeypatch.setattr(native_host.RustSymbolGameHost, "invoke_runtime", invoke)
    host = RustSymbolGameHost(tmp_path / "controlled-host")
    received = getattr(host, method)(*args, **kwargs)
    assert received is crossing
    assert received.value is outcome
    assert calls == [(action, payload)]


@pytest.mark.parametrize("method", ["invoke", "invoke_runtime"])
@pytest.mark.parametrize(
    "disposition", ["success", "native-failure", "transport-refusal"]
)
def test_direct_invocation_preserves_the_exact_railway_value(
    method, disposition, tmp_path, monkeypatch
) -> None:
    if disposition == "transport-refusal":
        crossing = Err(
            Refusal(code="HOST_TIMEOUT", message="controlled timeout", locus="test")
        )
    else:
        crossing = Ok(
            {
                "schema_version": native_host.RUNTIME_OUTCOME_SCHEMA,
                "action": "canonical_wire",
                "success": disposition == "success",
                "result": {"value": 1} if disposition == "success" else None,
                "error": None if disposition == "success" else "native failure",
                "authority_effect": "None",
            }
        )

    def invoke(host, action, payload):
        assert action == "canonical_wire"
        assert payload == {"value": 1}
        return crossing

    monkeypatch.setattr(native_host.RustSymbolGameHost, "invoke_runtime", invoke)
    host = RustSymbolGameHost(tmp_path / "controlled-host")
    received = getattr(host, method)("canonical_wire", {"value": 1})
    assert received is crossing
    assert not hasattr(host, "last_outcome")

"""Differential wire, content, and refusal checks against an actual native host.

The Python artifact implementation is the oracle; the native process must not
replace it with a second Python implementation or a mocked transport.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from omega_engine_pfp.domain.aggregates import prompt_artifact as domain
from omega_engine_pfp.domain.aggregates.research_claim import canonical_json_artifact_bytes
from omega_engine_pfp.domain.exceptions import DomainError
from omega_engine_pfp.domain.shared_kernel.canonical import domain_digest
from omega_engine_pfp.domain.validation import MAX_BODY_BYTES
from omega_engine_pfp.ffi import RustSymbolGameHost
from omega_engine_pfp.use_cases import prompt_artifact as use_cases


@pytest.fixture(scope="module")
def native_host() -> Path:
    configured = os.environ.get("OMEGA_SYMBOL_GAME_HOST")
    assert configured, "Set OMEGA_SYMBOL_GAME_HOST to the freshly tested native executable"
    binary = Path(configured)
    assert binary.is_file(), f"Native executable is unavailable: {binary}"
    return binary


def _invoke(native_host: Path, payload: dict) -> dict:
    request = {
        "schema_version": "omega.symbol-game.runtime-request.v1",
        "action": "prompt_artifact",
        "payload": payload,
    }
    output = subprocess.run(
        [str(native_host), "invoke"],
        input=json.dumps(request, ensure_ascii=False, allow_nan=False).encode("utf-8"),
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert output.returncode == 0, output.stderr.decode("utf-8", errors="replace")
    outcome = json.loads(output.stdout)
    assert outcome["authority_effect"] == "None"
    return outcome


def _success(native_host: Path, payload: dict) -> dict:
    outcome = _invoke(native_host, payload)
    assert outcome["success"] is True, outcome
    assert outcome["error"] is None
    return outcome["result"]


def _refused(native_host: Path, payload: dict) -> None:
    outcome = _invoke(native_host, payload)
    assert outcome["success"] is False, outcome
    assert outcome["result"] is None
    assert isinstance(outcome["error"], str) and ":" in outcome["error"]


def _compile_request(**changes) -> dict:
    request = {
        "operation": "compile",
        "regime_kind": "prose-regime",
        "regime_definition_bytes": list(b"typed regime\r\nAuthorityEffect: None\r"),
        "prompt_body_bytes": list("Calculate λ + 🙂.\r\nAnswer strictly.\r".encode()),
        "objective_typed": {
            "kind": "proof_step",
            "summary": "Compute the next finite witness",
            "target_obstruction_ids": [],
            "target_demand_ids": [],
        },
    }
    request.update(changes)
    return request


def _python_kwargs(payload: dict) -> dict:
    kwargs = {
        key: copy.deepcopy(value)
        for key, value in payload.items()
        if key not in {"operation", "explicit_artifact_id"}
    }
    kwargs["regime_definition_bytes"] = bytes(kwargs["regime_definition_bytes"])
    kwargs["prompt_body_bytes"] = bytes(kwargs["prompt_body_bytes"])
    kwargs["objective_typed"] = domain.ObjectiveTypedV1.from_dict(kwargs["objective_typed"])
    if "open_obstructions" in kwargs:
        kwargs["open_obstructions"] = [
            domain.ObstructionHintV1.from_dict(item) for item in kwargs["open_obstructions"]
        ]
    if "demand_set" in kwargs:
        kwargs["demand_set"] = [domain.DemandItemV1.from_dict(item) for item in kwargs["demand_set"]]
    return kwargs


def _assert_compiled(native_host: Path, payload: dict) -> dict:
    kwargs = _python_kwargs(payload)
    expected = domain.compile_prompt_artifact(**kwargs).to_dict()
    assert use_cases.compile_prompt_artifact(**kwargs).to_dict() == expected
    assert domain.PromptArtifactV1.from_dict(expected).to_dict() == expected
    result = _success(native_host, payload)
    actual = result["artifact"]
    assert actual == expected
    assert canonical_json_artifact_bytes(actual) == canonical_json_artifact_bytes(expected)
    raw_body = bytes(payload["prompt_body_bytes"])
    body = raw_body.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    if payload.get("normalize_body", True) is False:
        body = raw_body
    assert bytes(result["prompt_body_bytes"]) == body
    assert actual["prompt_body_sha256"] == hashlib.sha256(body).hexdigest()
    assert actual["prompt_body_byte_count"] == len(body)
    validated = _success(native_host, {
        "operation": "validate", "artifact": expected, "prompt_body_bytes": list(body),
    })
    assert validated == {"artifact": expected, "valid": True}
    return actual


def _nested_request(**changes) -> dict:
    return _compile_request(
        admitted_constructors=["replace", "derive", "replace"],
        kill_conditions=["no_authority", "budget", "budget"],
        required_reply_fields=["SUMMARY", "AUTHORITY_EFFECT", "SUMMARY"],
        open_obstructions=[
            {"obstruction_id": "obs_z", "family": " CUSTOM_Open ", "residual_colour": "Closed",
             "magnitude": -7, "demand_id": "demand_z", "prior_report_digests": ["a" * 64, "b" * 64]},
            {"obstruction_id": "obs_a", "family": "custom_open", "residual_colour": "Open",
             "magnitude": None, "demand_id": None, "prior_report_digests": []},
        ],
        demand_set=[
            {"demand_id": "demand_z", "kind": " PROOF ", "note": "Calculate 2² = 4\r\nThen stop."},
            {"demand_id": "demand_a", "kind": "witness", "note": ""},
        ],
        objective_typed={
            "kind": " Proof_Step ", "summary": "  Compute λ with bounded arithmetic  ",
            "target_obstruction_ids": ["obs_a", "obs_z"],
            "target_demand_ids": ["demand_a", "demand_z"],
        },
        parent_packet_id="c" * 64,
        conversation_root_id="d" * 64,
        **changes,
    )


@pytest.mark.parametrize("regime_kind", sorted(domain.REGIME_KINDS))
def test_all_python_regime_kinds_have_full_native_wire_parity(native_host, regime_kind):
    _assert_compiled(native_host, _compile_request(regime_kind=regime_kind))


@pytest.mark.parametrize("residual_colour", ["Open", "Closed", "Exact"])
def test_nested_fields_defaults_and_residual_witness_parity(native_host, residual_colour):
    changes = {"residual_colour": residual_colour}
    if residual_colour == "Exact":
        changes["dual_witness_ref"] = "e" * 64
    _assert_compiled(native_host, _nested_request(**changes))


def test_compile_normalizes_sets_and_nested_order_but_validation_does_not(native_host):
    payload = _nested_request()
    original = _assert_compiled(native_host, payload)
    payload["admitted_constructors"].reverse()
    payload["open_obstructions"].reverse()
    payload["demand_set"].reverse()
    assert _assert_compiled(native_host, payload) == original
    reversed_wire = copy.deepcopy(original)
    reversed_wire["open_obstructions"].reverse()
    _repin(reversed_wire)
    _assert_wire_refused(native_host, reversed_wire)


@pytest.mark.parametrize("body,normalize", [
    (b"", True),
    (b"a\r\nb\rc\n", True),
    (b"a\r\nb\rc\n", False),
    (bytes([0, 255, 128, 13, 10]), True),
    ("𓂀🙂λ\u0000\u2028".encode(), True),
])
def test_exact_body_bytes_and_lf_normalization(native_host, body, normalize):
    _assert_compiled(native_host, _compile_request(
        prompt_body_bytes=list(body), normalize_body=normalize,
    ))


@pytest.mark.parametrize("magnitude", [0, -1, 2**53 + 1, 2**64, 2**80 + 3, -(2**80 + 3), 10**100])
def test_integer_magnitudes_retain_exact_identity_beyond_f64_and_u64(native_host, magnitude):
    payload = _nested_request()
    payload["open_obstructions"][0]["magnitude"] = magnitude
    _assert_compiled(native_host, payload)


@pytest.mark.parametrize("magnitude", [
    True, 1.0, -0.0, 0.25, 1e100, {"$serde_json::private::Number": "7"}, 10**400,
], ids=["bool", "integral_float", "negative_float_zero", "fraction", "exponent", "marker_object", "overflowing_int"])
def test_non_exact_or_disguised_magnitudes_refuse(native_host, magnitude):
    payload = _nested_request()
    payload["open_obstructions"][0]["magnitude"] = magnitude
    with pytest.raises((DomainError, TypeError, ValueError, OverflowError)):
        domain.compile_prompt_artifact(**_python_kwargs(payload)).to_dict()
    _refused(native_host, payload)


@pytest.mark.parametrize("field,value", [
    ("required_reply_fields", [False]),
    ("required_reply_fields", [1]),
    ("required_reply_fields", [" "]),
    ("required_reply_fields", [""]),
    ("dual_witness_required", 1),
    ("normalize_body", 0),
    ("normalize_body", "false"),
    ("normalize_body", None),
])
def test_compiler_cannot_emit_a_wire_that_its_own_parser_refuses(native_host, field, value):
    payload = _compile_request(**{field: value})
    with pytest.raises((DomainError, TypeError, ValueError)):
        domain.compile_prompt_artifact(**_python_kwargs(payload)).to_dict()
    with pytest.raises((DomainError, TypeError, ValueError)):
        use_cases.compile_prompt_artifact(**_python_kwargs(payload)).to_dict()
    _refused(native_host, payload)


@pytest.mark.parametrize("nested", [False, True])
def test_render_matches_both_python_entrypoints_byte_for_byte(native_host, nested):
    source = _nested_request() if nested else _compile_request()
    kwargs = _python_kwargs(source)
    regime = kwargs.pop("regime_definition_bytes")
    for key in ("regime_kind", "prompt_body_bytes", "parent_packet_id", "conversation_root_id"):
        kwargs.pop(key, None)
    expected = domain.render_prompt_body(regime, **kwargs)
    assert use_cases.render_prompt_body(regime, **kwargs) == expected
    payload = {key: value for key, value in source.items() if key not in {
        "regime_kind", "prompt_body_bytes", "parent_packet_id", "conversation_root_id",
    }}
    payload["operation"] = "render"
    actual = _success(native_host, payload)
    assert bytes(actual["prompt_body_bytes"]) == expected
    assert b"ResidualColour." not in expected
    if nested:
        assert b"(Open)" in expected and b"(Closed)" in expected


@pytest.mark.parametrize("magnitude", [1.0, -0.0, 0.25, 1e100])
def test_renderer_preserves_finite_float_text_without_granting_it_canonical_identity(native_host, magnitude):
    source = _nested_request()
    source["open_obstructions"][0]["magnitude"] = magnitude
    kwargs = _python_kwargs(source)
    regime = kwargs.pop("regime_definition_bytes")
    for key in ("regime_kind", "prompt_body_bytes", "parent_packet_id", "conversation_root_id"):
        kwargs.pop(key, None)
    expected = domain.render_prompt_body(regime, **kwargs)
    assert use_cases.render_prompt_body(regime, **kwargs) == expected
    payload = {key: value for key, value in source.items() if key not in {
        "regime_kind", "prompt_body_bytes", "parent_packet_id", "conversation_root_id",
    }}
    payload["operation"] = "render"
    assert bytes(_success(native_host, payload)["prompt_body_bytes"]) == expected


def _wire() -> dict:
    return domain.compile_prompt_artifact(**_python_kwargs(_nested_request())).to_dict()


def _repin(wire: dict) -> None:
    identity = {key: value for key, value in wire.items() if key != "prompt_artifact_id"}
    wire["prompt_artifact_id"] = domain_digest(domain.PAYLOAD_DOMAIN, identity)


def _assert_wire_refused(native_host: Path, wire: dict) -> None:
    with pytest.raises((DomainError, TypeError, ValueError, OverflowError)):
        domain.PromptArtifactV1.from_dict(wire)
    _refused(native_host, {"operation": "validate", "artifact": wire})


@pytest.mark.parametrize("field,value", [
    ("schema_version", "omega.symbol-game.prompt-artifact.v2"),
    ("family", "elimination_receipt"),
    ("regime_kind", "SYMBOL_GAME_ROUND"),
    ("regime_id", "A" * 64),
    ("authority_effect", "Promote"),
    ("residual_colour", "RED_BLUE"),
    ("dual_witness_required", 1),
    ("dual_witness_ref", "a" * 64),
    ("parent_packet_id", "not_a_digest"),
    ("conversation_root_id", []),
    ("prompt_body_sha256", "g" * 64),
    ("prompt_body_byte_count", True),
    ("prompt_body_byte_count", -1),
    ("prompt_body_byte_count", MAX_BODY_BYTES + 1),
    ("prompt_body_byte_count", {"$serde_json::private::Number": "7"}),
    ("required_reply_fields", []),
    ("required_reply_fields", [" "]),
    ("required_reply_fields", ["SUMMARY", "SUMMARY"]),
    ("admitted_constructors", ["z", "a"]),
    ("admitted_constructors", ["bad identifier"]),
    ("kill_conditions", []),
    ("kill_conditions", ["x" * 129]),
])
def test_repinned_invalid_wire_is_refused_by_both_languages(native_host, field, value):
    wire = _wire()
    wire[field] = value
    _repin(wire)
    _assert_wire_refused(native_host, wire)


@pytest.mark.parametrize("location,field,value", [
    ("objective_typed", "summary", "λ" * 1025),
    ("objective_typed", "target_demand_ids", ["z", "a"]),
    ("objective_typed", "target_obstruction_ids", ["a", "a"]),
    ("objective_typed", "kind", "x" * 65),
    ("demand_set", "note", "λ" * 4097),
    ("demand_set", "kind", True),
    ("open_obstructions", "magnitude", True),
    ("open_obstructions", "prior_report_digests", ["b" * 64, "a" * 64]),
    ("open_obstructions", "residual_colour", "bogus"),
], ids=[
    "summary_limit", "target_demand_order", "target_obstruction_duplicate", "kind_limit",
    "note_utf8_limit", "kind_type", "magnitude_bool", "prior_digest_order", "residual_kind",
])
def test_repinned_invalid_nested_wire_is_refused(native_host, location, field, value):
    wire = _wire()
    target = wire[location]
    if isinstance(target, list):
        target = target[0]
    target[field] = value
    _repin(wire)
    _assert_wire_refused(native_host, wire)


@pytest.mark.parametrize("location", ["root", "objective_typed", "open_obstructions", "demand_set"])
@pytest.mark.parametrize("field", ["unknown", "verified"])
def test_unknown_and_authority_fields_cannot_enter_nested_wire(native_host, location, field):
    wire = _wire()
    target = wire if location == "root" else wire[location]
    if isinstance(target, list):
        target = target[0]
    target[field] = True
    _repin(wire)
    _assert_wire_refused(native_host, wire)


def test_missing_wire_field_and_wrong_identity_refuse(native_host):
    wire = _wire()
    del wire["conversation_root_id"]
    _repin(wire)
    _assert_wire_refused(native_host, wire)
    wire = _wire()
    wire["objective_typed"]["summary"] = "Changed after content addressing"
    _assert_wire_refused(native_host, wire)


def test_wire_nested_value_object_normalization_matches_python(native_host):
    expected = _wire()
    expected["open_obstructions"][0]["obstruction_id"] = "_obs"
    expected["demand_set"][0]["demand_id"] = "_demand"
    _repin(expected)
    wire = copy.deepcopy(expected)
    wire["open_obstructions"][0]["obstruction_id"] = "\u001c _obs \u001f"
    wire["open_obstructions"][0]["family"] = " CUSTOM_OPEN "
    wire["demand_set"][0]["demand_id"] = " _demand "
    wire["demand_set"][0]["kind"] = " WITNESS "
    wire["objective_typed"]["kind"] = " PROOF_STEP "
    wire["objective_typed"]["summary"] = "  Compute λ with bounded arithmetic  "
    assert domain.PromptArtifactV1.from_dict(wire).to_dict() == expected
    actual = _success(native_host, {"operation": "validate", "artifact": wire})
    assert actual == {"artifact": expected, "valid": True}


def test_regime_bytes_are_hashable_without_claiming_utf8_renderability(native_host):
    raw_regime = bytes([255, 128, 13, 10, 13])
    _assert_compiled(native_host, _compile_request(regime_definition_bytes=list(raw_regime)))
    objective = domain.ObjectiveTypedV1.from_dict(_compile_request()["objective_typed"])
    with pytest.raises(UnicodeDecodeError):
        domain.render_prompt_body(raw_regime, objective_typed=objective)
    _refused(native_host, {
        "operation": "render", "regime_definition_bytes": list(raw_regime),
        "objective_typed": objective.to_dict(),
    })


def test_body_verification_does_not_normalize_received_bytes(native_host):
    payload = _compile_request(prompt_body_bytes=list(b"x\r\n"))
    artifact = _assert_compiled(native_host, payload)
    parsed = domain.PromptArtifactV1.from_dict(artifact)
    with pytest.raises(DomainError):
        parsed.verify_prompt_body(b"x\r\n")
    _refused(native_host, {
        "operation": "validate", "artifact": artifact, "prompt_body_bytes": list(b"x\r\n"),
    })


@pytest.mark.parametrize("field,limit", [
    ("admitted_constructors", 64), ("kill_conditions", 32),
    ("required_reply_fields", 32), ("open_obstructions", 256), ("demand_set", 64),
])
@pytest.mark.parametrize("excess", [0, 1])
def test_array_limits_match_at_boundary_and_next_item(native_host, field, limit, excess):
    wire = _wire()
    count = limit + excess
    if field in {"open_obstructions", "demand_set"}:
        template = wire[field][0]
        id_field = "obstruction_id" if field == "open_obstructions" else "demand_id"
        wire[field] = [dict(template, **{id_field: f"id_{index:03}"}) for index in range(count)]
    else:
        wire[field] = [f"field_{index:03}" for index in range(count)]
    _repin(wire)
    if excess:
        _assert_wire_refused(native_host, wire)
    else:
        assert domain.PromptArtifactV1.from_dict(wire).to_dict() == wire
        assert _success(native_host, {"operation": "validate", "artifact": wire})["artifact"] == wire


def test_body_header_and_unicode_string_limits_are_distinct_from_transport_limits(native_host):
    wire = _wire()
    wire["prompt_body_byte_count"] = MAX_BODY_BYTES
    wire["objective_typed"]["summary"] = "🙂" * 1024
    wire["demand_set"][0]["note"] = "λ" * 4096
    _repin(wire)
    assert domain.PromptArtifactV1.from_dict(wire).to_dict() == wire
    assert _success(native_host, {"operation": "validate", "artifact": wire})["artifact"] == wire


def test_pfp_oeos_process_seam_can_compile_the_full_one_mib_body_limit(native_host):
    body = b"x" * MAX_BODY_BYTES
    payload = _compile_request(prompt_body_bytes=list(body))
    expected = domain.compile_prompt_artifact(**_python_kwargs(payload)).to_dict()
    assert use_cases.compile_prompt_artifact(**_python_kwargs(payload)).to_dict() == expected
    host = RustSymbolGameHost(native_host)
    transported = host.invoke("prompt_artifact", payload)
    assert transported.is_ok, transported.unwrap_err()
    outcome = transported.unwrap()
    assert outcome["success"] is True, outcome
    assert outcome["authority_effect"] == "None"
    assert outcome["result"]["artifact"] == expected
    assert bytes(outcome["result"]["prompt_body_bytes"]) == body
    assert expected["prompt_body_byte_count"] == MAX_BODY_BYTES
    payload["prompt_body_bytes"].append(ord("x"))
    with pytest.raises(DomainError):
        domain.compile_prompt_artifact(**_python_kwargs(payload)).to_dict()
    refused = host.invoke("prompt_artifact", payload)
    assert refused.is_ok, refused.unwrap_err()
    refused_outcome = refused.unwrap()
    assert refused_outcome["success"] is False
    assert refused_outcome["result"] is None


@pytest.mark.parametrize("content,expected", [
    ("AUTHORITY_EFFECT=None\nSUMMARY=4", True),
    ("SUMMARY=4", False),
    ("AUTHORITY_EFFECT=None", False),
    ("text contains AUTHORITY_EFFECT and SUMMARY as substrings", True),
])
def test_reply_check_preserves_existing_substring_semantics(native_host, content, expected):
    artifact = domain.PromptArtifactV1.from_dict(_wire())
    assert use_cases.ValidateReplyResidualUseCase().execute(
        artifact=artifact, reply_content=content,
    ) is expected
    assert _success(native_host, {
        "operation": "validate_reply", "artifact": artifact.to_dict(), "reply_content": content,
    }) == {"residual_satisfied": expected}


def test_reply_check_refuses_an_unvalidated_artifact(native_host):
    wire = _wire()
    wire["authority_effect"] = "Promote"
    _repin(wire)
    _refused(native_host, {
        "operation": "validate_reply", "artifact": wire,
        "reply_content": "AUTHORITY_EFFECT=None SUMMARY=4",
    })


def test_legacy_reply_action_also_requires_a_valid_content_address(native_host):
    host = RustSymbolGameHost(native_host)
    wire = _wire()
    payload = {"artifact": wire, "reply_content": "AUTHORITY_EFFECT=None SUMMARY=4"}
    transported = host.invoke("validate_reply_residual", payload)
    assert transported.is_ok, transported.unwrap_err()
    outcome = transported.unwrap()
    assert outcome["success"] is True, outcome
    assert outcome["result"] == {"residual_satisfied": True}
    wire["prompt_body_byte_count"] += 1
    refused = host.invoke("validate_reply_residual", payload)
    assert refused.is_ok, refused.unwrap_err()
    refused_outcome = refused.unwrap()
    assert refused_outcome["success"] is False
    assert refused_outcome["result"] is None
    assert refused_outcome["error"].startswith("PROMPT_ARTIFACT_INVALID:")


def test_legacy_explicit_id_is_preserved_but_not_promoted_to_content_addressed_identity(native_host):
    payload = _compile_request(explicit_artifact_id="legacy.prompt.7")
    expected = use_cases.compile_prompt_artifact(
        **_python_kwargs(payload), explicit_artifact_id=payload["explicit_artifact_id"],
    ).to_dict()
    assert expected["prompt_artifact_id"] == "legacy.prompt.7"
    _assert_wire_refused(native_host, expected)
    _refused(native_host, payload)


@pytest.mark.parametrize("needle,replacement", [
    ('"operation":"compile"', '"operation":"validate","operation":"compile"'),
    ('"summary":"Compute the next finite witness"', '"summary":"shadow","summary":"Compute the next finite witness"'),
    ('"regime_kind":"prose-regime"', '"regime_kind":"unknown","regime_kind":"prose-regime"'),
], ids=["operation", "nested_objective", "regime"])
def test_raw_duplicate_json_keys_never_reach_the_artifact_compiler(native_host, needle, replacement):
    request = json.dumps({
        "schema_version": "omega.symbol-game.runtime-request.v1",
        "action": "prompt_artifact", "payload": _compile_request(),
    }, separators=(",", ":"))
    assert needle in request
    malformed = request.replace(needle, replacement, 1)
    output = subprocess.run(
        [str(native_host), "invoke"], input=malformed.encode("utf-8"),
        capture_output=True, timeout=10, check=False,
    )
    assert output.returncode != 0
    assert output.stdout == b""
    assert b"duplicate JSON key:" in output.stderr


def test_mcp_compile_preserves_big_integer_identity_and_refuses_marker_objects(native_host):
    payload = _nested_request()
    payload["open_obstructions"][0]["magnitude"] = 2**80 + 3
    expected = domain.compile_prompt_artifact(**_python_kwargs(payload)).to_dict()
    malformed = copy.deepcopy(payload)
    malformed["open_obstructions"][0]["magnitude"] = {"$serde_json::private::Number": "7"}
    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-03-26", "capabilities": {},
            "clientInfo": {"name": "prompt-artifact-parity", "version": "1"},
        }},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
            "name": "prompt_artifact", "arguments": {"payload": payload},
        }},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
            "name": "prompt_artifact", "arguments": {"payload": malformed},
        }},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {
            "name": "prompt_artifact", "arguments": {"payload": {
                "operation": "validate", "artifact": expected,
            }},
        }},
    ]
    output = subprocess.run(
        [str(native_host), "--mcp"],
        input=b"".join(json.dumps(message).encode("utf-8") + b"\n" for message in messages),
        capture_output=True, timeout=10, check=False,
    )
    assert output.returncode == 0, output.stderr
    replies = {reply["id"]: reply for reply in map(json.loads, output.stdout.splitlines())}
    assert set(replies) == {1, 2, 3, 4}
    accepted = replies[2]["result"]
    assert accepted["isError"] is False
    assert accepted["structuredContent"]["result"]["artifact"] == expected
    refused = replies[3]["result"]
    assert refused["isError"] is True
    assert refused["structuredContent"]["success"] is False
    assert refused["structuredContent"]["result"] is None
    assert refused["structuredContent"]["authority_effect"] == "None"
    validated = replies[4]["result"]
    assert validated["isError"] is False
    assert validated["structuredContent"]["result"] == {"artifact": expected, "valid": True}

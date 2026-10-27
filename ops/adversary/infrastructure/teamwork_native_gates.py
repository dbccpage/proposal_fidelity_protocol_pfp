"""Execute and replay the mandatory native diagnostics at the existing OEOS seam.

The host selects witness sources before work. Model answers never choose native
outcomes, witnesses, commands or binaries. The existing process seam captures exact
stdin/stdout/stderr; logical requests and parsed decisions have separate digests.

Origin: adversary.infrastructure.teamwork_native_gates.
claim: model answers never choose native outcomes, witnesses, commands, or binaries.
AuthorityEffect: None.
"""

from __future__ import annotations

import base64
import hashlib
import json
import time
from itertools import islice
from pathlib import Path

from ..domain.intergates.payload_contract import (
    SOURCE_CONTRACT_PROFILE, SOURCE_CONTRACT_PROFILES, MEASURED_SOURCE_CONTRACT_PROFILE,
    missing_source_inputs, validate_payload,
)
from ..domain.native_gate_check import (
    EMPIRICAL_GATE_IDS,
    INTERGATE_ENDPOINTS,
    INTERGATE_IDS,
    NATIVE_GATE_IDS,
    PRIMARY_GATE_IDS,
    NativeGateCheck,
    decode_native_json,
    native_action_scope,
    native_digest,
    native_gate_summary,
    native_gate_applicability,
    native_required_gate_ids,
    native_required_edges,
    native_response_semantics,
    validate_native_artifact_snapshots,
    validate_native_gate_receipt,
)

ACTUAL_TRAVERSAL_HISTORY = "actual-role-traversals-v1"
LEGACY_SCAN_HISTORY = "legacy-diagnostic-scan-v1"
PROMPT_TRANSPORT_POOL_PROFILE = "adversary.pfp-transport-pool.v2"
_HOST_FACT_VERSIONS = (
    "adversary.native-host-facts.v1",
    "adversary.native-host-facts.v2",
    "adversary.native-host-facts.v3",
)
_HOST_FACT_TRANSPORT_VERSIONS = (
    "adversary.native-host-facts.v2",
    "adversary.native-host-facts.v3",
)
_SCOPE_KEYS = (
    "run_id", "initial_task_id", "workflow_version", "objective_sha256", "plan_sha256",
    "native_gate_check_sha256",
)
_BINARY_SHA256_CACHE: dict[tuple[str, int, int], str] = {}


class _NotSelected:
    """Sentinel for a value that is not an explicit host selector."""


_NOT_SELECTED = _NotSelected()


class _BatchState:
    """Mutable batch scratch visible to the failure receipt."""

    def __init__(self) -> None:
        self.rows = []
        self.transitions = []
        self.captures = []
        self.binary = None
        self.artifact_snapshots = {}
        self.host_facts = None
        self.catalog_envelope = None
        self.observation_time = None
        self.verification_started_ms = 0
        self.scoped = False
        self.applicability = None
        self.required = ()
        self.required_edges = ()


def _file_sha256_cached(path: Path) -> str:
    stat = path.stat()
    key = (str(path.absolute()), stat.st_mtime_ns, stat.st_size)
    cached = _BINARY_SHA256_CACHE.get(key)
    if cached is None:
        cached = hashlib.sha256(path.read_bytes()).hexdigest()
        _BINARY_SHA256_CACHE[key] = cached
    return cached


def _transition_history(previous, *, history_profile):
    """Keep diagnostic predicate scans out of actual role-flow history.

    Older receipt replay deliberately retains its original scan semantics.
    Explicit operator-supplied history is handled separately and remains intact.
    """
    if history_profile not in (ACTUAL_TRAVERSAL_HISTORY, LEGACY_SCAN_HISTORY):
        raise ValueError("NATIVE_GATE_HISTORY_PROFILE_INVALID")
    return [edge["source_gate"] + "->" + edge["target_gate"]
        for edge in previous["transitions"] if edge["attempted"] and (
            history_profile == LEGACY_SCAN_HISTORY or edge.get("role_flow_traversal") is not False)]


def _safe_native_path(path, *, for_mutation=False):
    from ..use_cases.intelligence_digestion.archive_custody import ArchiveCustodyError, checked_path

    selected = Path(path).absolute()
    try:
        checked_path(Path(selected.anchor), selected)
    except ArchiveCustodyError as exc:
        raise ValueError(str(exc)) from exc
    if for_mutation and selected.is_file() and selected.stat().st_nlink != 1:
        raise ValueError("NATIVE_GATE_HARDLINK_REFUSED")
    return selected


def _receipt_path(selection, run, action, output_dir, *, partial=False):
    directory = Path(selection.receipt_directory) if selection.receipt_directory else (
        Path(output_dir) / "native-gates" if output_dir is not None else
        Path.cwd() / "target" / "adversary-native-gates" / hashlib.sha256(run.run_id.encode()).hexdigest())
    directory = _safe_native_path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return _safe_native_path(directory / (action.action_id + (".partial.json" if partial else ".json")),
                             for_mutation=True)


def bind_native_gate_check(*, witness_path=None, binary_path=None, source_paths=(),
                           specification_sha256=None, policy="diagnostic", receipt_directory=None,
                           process_observer=None, kernel_check=None, resource_check=None,
                           gate_scope=None) -> NativeGateCheck:
    def bound(path):
        selected = _safe_native_path(path)
        if selected.is_symlink() or not selected.is_file():
            raise ValueError("NATIVE_GATE_SOURCE_INVALID")
        return str(selected), _file_sha256_cached(selected)

    binary, binary_sha = bound(binary_path) if binary_path is not None else ("", "")
    witness, witness_sha = bound(witness_path) if witness_path is not None else ("", "")
    sources = dict(bound(path) for path in source_paths)
    return NativeGateCheck(policy=policy, binary_path=binary, binary_sha256=binary_sha,
        witness_path=witness, witness_sha256=witness_sha, source_paths=sources,
        specification_sha256=specification_sha256 or {},
        receipt_directory=str(Path(receipt_directory).absolute()) if receipt_directory is not None else "",
        process_observer=process_observer, kernel_check=kernel_check, resource_check=resource_check,
        gate_scope=gate_scope)


def _require_history_profile(history_profile) -> None:
    if history_profile not in (ACTUAL_TRAVERSAL_HISTORY, LEGACY_SCAN_HISTORY):
        raise ValueError("NATIVE_GATE_HISTORY_PROFILE_INVALID")


def _require_selection(action):
    selection = action.native_gate_check
    if selection is None:
        raise ValueError("NATIVE_GATE_CHECK_REQUIRED")
    return selection


def _prepare_input_artifacts(action, selection, artifact_snapshots, current_artifacts, current_checker, current_source) -> None:
    current_source(action)
    current_checker(action)
    if artifact_snapshots is None:
        current_artifacts(action.artifacts)
    else:
        validate_native_artifact_snapshots(action, artifact_snapshots)
    current_artifacts(selection.source_paths)
    for path in selection.source_paths:
        _safe_native_path(path)


def _witness_document_invalid(document) -> bool:
    if type(document) is not dict:
        return True
    if document.get("schema_version") != "adversary.native-gate-witnesses.v1":
        return True
    if set(document) - {"schema_version", "gates", "history_edges"}:
        return True
    if type(document.get("gates")) is not dict:
        return True
    return bool(set(document["gates"]) - set(NATIVE_GATE_IDS))


def _load_witness(selection, current_artifacts):
    if not selection.witness_path:
        return {"gates": {}, "history_edges": []}
    current_artifacts({selection.witness_path: selection.witness_sha256})
    _safe_native_path(selection.witness_path)
    raw = Path(selection.witness_path).read_bytes()
    if len(raw) > 1024 * 1024:
        raise ValueError("NATIVE_GATE_WITNESS_TOO_LARGE")
    document = decode_native_json(raw)
    if _witness_document_invalid(document):
        raise ValueError("NATIVE_GATE_WITNESS_INVALID")
    return document


def _admitted_scope_ids(gate_scope):
    admitted = set()
    for phase in gate_scope.values():
        for gate in phase:
            admitted.add(gate)
    return admitted


def _apply_witness_scope(selection, document) -> None:
    if selection.gate_scope is None:
        return
    admitted = _admitted_scope_ids(selection.gate_scope)
    if set(document["gates"]) - admitted:
        raise ValueError("NATIVE_GATE_WITNESS_OUTSIDE_SCOPE")


def _history_edge_invalid(history) -> bool:
    for edge in history:
        if type(edge) is not str:
            return True
        if len(edge) > 256:
            return True
    return False


def _history_invalid(history) -> bool:
    if type(history) is not list:
        return True
    if len(history) > 64:
        return True
    return _history_edge_invalid(history)


def _checked_history(document):
    history = document.get("history_edges", [])
    if _history_invalid(history):
        raise ValueError("NATIVE_GATE_HISTORY_INVALID")
    return list(history)


def _batch_scope_changed(previous, reference, original, action, selection) -> bool:
    if previous["receipt_sha256"] != reference["receipt_sha256"]:
        return True
    if native_gate_summary(previous) != reference["summary"]:
        return True
    if original.run_id != action.run_id:
        return True
    if original.initial_task_id != action.initial_task_id:
        return True
    if original.objective != action.objective:
        return True
    return original.native_gate_check != selection


def _extend_history(action, selection, history, history_profile, current_artifacts):
    from ..use_cases.teamwork import TeamworkAction

    for reference in action.native_gate_batches:
        current_artifacts({reference["path"]: reference["sha256"]})
        _safe_native_path(reference["path"])
        previous = decode_native_json(Path(reference["path"]).read_bytes())
        original = TeamworkAction.model_validate_json(json.dumps(previous["action"]))
        validate_native_gate_receipt(original, previous)
        if _batch_scope_changed(previous, reference, original, action, selection):
            raise ValueError("NATIVE_GATE_HISTORY_SCOPE_CHANGED")
        history.extend(_transition_history(previous, history_profile=history_profile))
    if len(history) > 64:
        raise ValueError("NATIVE_GATE_HISTORY_ALLOWANCE_EXHAUSTED")
    return history


def _inputs(action, *, artifact_snapshots=None, history_profile=ACTUAL_TRAVERSAL_HISTORY):
    from .teamwork_intelligence_host import _current_artifacts, _current_checker, _current_source

    _require_history_profile(history_profile)
    selection = _require_selection(action)
    _prepare_input_artifacts(
        action, selection, artifact_snapshots, _current_artifacts, _current_checker, _current_source)
    document = _load_witness(selection, _current_artifacts)
    _apply_witness_scope(selection, document)
    history = _checked_history(document)
    history = _extend_history(action, selection, history, history_profile, _current_artifacts)
    return selection, document, history


def _host_unbound_message(selection):
    if selection.unavailable_reason:
        return selection.unavailable_reason
    return "NATIVE_HOST_INTAKE_UNBOUND"


def _require_bound_binary(selection) -> None:
    if selection.unavailable_reason:
        raise ValueError(_host_unbound_message(selection))
    if not selection.binary_path:
        raise ValueError(_host_unbound_message(selection))
    if not selection.binary_sha256:
        raise ValueError(_host_unbound_message(selection))


def _binary_hash_changed(selection, actual) -> bool:
    if not selection.binary_sha256:
        return False
    return actual["sha256"] != selection.binary_sha256


def _binary_changed(binary, selection, actual, expected_binary) -> bool:
    if binary.is_symlink():
        return True
    if _binary_hash_changed(selection, actual):
        return True
    if expected_binary is None:
        return False
    return actual != expected_binary


def _host_capture(captures, observed) -> None:
    names = ("stdin_bytes", "stdout_bytes", "stderr_bytes")
    encoded = {}
    for name in names:
        encoded[name.removesuffix("_bytes") + "_base64"] = base64.b64encode(observed[name]).decode("ascii")
    for name in names:
        encoded[name.removesuffix("_bytes") + "_sha256"] = hashlib.sha256(observed[name]).hexdigest()
    captures.append({
        "args": list(observed["args"]),
        "exit_code": observed["exit_code"],
        "elapsed_seconds": observed["elapsed_seconds"],
        **encoded,
    })


def _located_binary(selection, locate_host_binary):
    located = locate_host_binary(Path(selection.binary_path))
    if located.is_err:
        raise ValueError(located.unwrap_err().code)
    return located.unwrap().binary


def _host(selection, *, expected_binary=None):
    from operating_system.adapters.rust_host.ffi import (
        RustSymbolGameHost,
        locate_host_binary,
    )

    _require_bound_binary(selection)
    _safe_native_path(selection.binary_path)
    binary = _located_binary(selection, locate_host_binary)
    _safe_native_path(binary)
    actual = {"path": str(binary.absolute()), "sha256": _file_sha256_cached(binary)}
    if _binary_changed(binary, selection, actual, expected_binary):
        raise ValueError("NATIVE_GATE_BINARY_CHANGED")
    captures = []
    return RustSymbolGameHost(
        binary=binary, process_observer=lambda observed: _host_capture(captures, observed)
    ), actual, captures


def _invoke(host, request):
    normalized = json.loads(json.dumps(request, sort_keys=True, allow_nan=False))
    result = host.invoke_runtime_with_file("adversary_support", normalized, file_action="adversary_support_file")
    if result.is_err:
        failure = result.unwrap_err()
        raise ValueError(f"{failure.code}: {failure.message}")
    return dict(result.unwrap())


def _catalog_unavailable(envelope) -> bool:
    if envelope.get("success") is not True:
        return True
    return envelope["result"]["refusal"] is not None


def _primary_gate_ids(catalog):
    return tuple(row["gate_id"] for row in catalog["primary_and_empirical"]["gates"])


def _catalog_drifted(catalog) -> bool:
    if catalog.get("schema_version") != "core.adversary.gate-schemas.v1":
        return True
    if _primary_gate_ids(catalog) != (*PRIMARY_GATE_IDS, *EMPIRICAL_GATE_IDS):
        return True
    return tuple(catalog["intergate_ids"]) != INTERGATE_IDS


def _profile_missing(expected, available) -> bool:
    if expected is None:
        return False
    return expected not in available


def _require_catalog_profile(catalog, expected_profile, expected_process_profile,
                             expected_kernel_profile, expected_resource_profile) -> None:
    if _profile_missing(expected_profile, catalog.get("intergate_profiles", [])):
        raise ValueError("NATIVE_INTERGATE_PROFILE_UNAVAILABLE: select a host supporting the current contract")
    empirical = catalog["primary_and_empirical"]
    if _profile_missing(expected_process_profile, empirical.get("process_profiles", [])):
        raise ValueError("NATIVE_PROCESS_PROFILE_UNAVAILABLE: select a host supporting authenticated process observation")
    if _profile_missing(expected_kernel_profile, empirical.get("kernel_profiles", [])):
        raise ValueError("NATIVE_KERNEL_PROFILE_UNAVAILABLE: select a host supporting authenticated kernel observation")
    if _profile_missing(expected_resource_profile, empirical.get("resource_profiles", [])):
        raise ValueError("NATIVE_RESOURCE_PROFILE_UNAVAILABLE")


def _catalog(envelope, *, expected_profile=None, expected_process_profile=None,
             expected_kernel_profile=None, expected_resource_profile=None):
    if _catalog_unavailable(envelope):
        raise ValueError("NATIVE_GATE_CATALOG_UNAVAILABLE")
    catalog = envelope["result"]["outcome"]
    if _catalog_drifted(catalog):
        raise ValueError("NATIVE_GATE_CATALOG_DRIFT")
    _require_catalog_profile(
        catalog, expected_profile, expected_process_profile, expected_kernel_profile, expected_resource_profile)
    return catalog


def make_native_intergate_evaluator(selection, *, process_observer=None):
    """Compose the existing pinned native owner for Python source-profile calls."""
    def evaluate(gate_id, payload, history_edges):
        host, binary, captures = _host(selection)
        profile = payload.get("contract_profile", SOURCE_CONTRACT_PROFILE)
        if profile not in SOURCE_CONTRACT_PROFILES:
            raise ValueError("NATIVE_INTERGATE_PROFILE_MISMATCH")
        _catalog(_invoke(host, {"operation": "gate_schemas"}), expected_profile=profile)
        request = {"operation": "gate_evaluate", "gate_id": gate_id,
            "payload": payload, "history_edges": list(history_edges)}
        response = _invoke(host, request)
        native_response_semantics(captures[-1], request, response, binary)
        _host(selection, expected_binary=binary)
        if response.get("success") is not True or response["result"].get("refusal") is not None:
            raise ValueError("INTERGATE_NATIVE_REFUSED: " + str(response.get("result", {}).get("refusal")))
        if process_observer is not None:
            for captured in captures:
                process_observer(captured)
        return response["result"]["outcome"]
    return evaluate


def _bad_selector_keys(keys) -> bool:
    for key in keys:
        if type(key) is not str:
            return True
        if not key:
            return True
    return False


def _json_selector_invalid(selector) -> bool:
    if type(selector) is not dict:
        return True
    if set(selector) != {"path", "keys"}:
        return True
    keys = selector["keys"]
    if type(keys) is not list:
        return True
    if len(keys) < 1:
        return True
    if len(keys) > 16:
        return True
    return _bad_selector_keys(keys)


def _source_changed(raw, expected) -> bool:
    if len(raw) > 1024 * 1024:
        return True
    return hashlib.sha256(raw).hexdigest() != expected


def _read_bound_source(source_path, action):
    if type(source_path) is not str:
        raise ValueError("NATIVE_GATE_SOURCE_SELECTOR_INVALID")
    if not source_path:
        raise ValueError("NATIVE_GATE_SOURCE_SELECTOR_INVALID")
    path = _safe_native_path(source_path)
    expected = action.native_gate_check.source_paths.get(str(path))
    if expected is None:
        raise ValueError("NATIVE_GATE_SOURCE_NOT_BOUND")
    raw = path.read_bytes()
    if _source_changed(raw, expected):
        raise ValueError("NATIVE_GATE_SOURCE_CHANGED")
    return raw, expected


def _walk_json_keys(parsed, keys):
    for key in keys:
        if type(parsed) is not dict:
            raise ValueError("NATIVE_GATE_SOURCE_SELECTOR_INVALID")
        if key not in parsed:
            raise ValueError("NATIVE_GATE_SOURCE_SELECTOR_INVALID")
        parsed = parsed[key]
    return parsed


def _decode_bound_kind(kind, raw, expected, selector):
    if kind == "sha256":
        return "sha256:" + expected
    if kind == "utf8":
        return raw.decode("utf-8")
    return _walk_json_keys(decode_native_json(raw), selector["keys"])


def _bound_source_value(selector, action, *, kind):
    """Read only an operator-selected, already hash-bound source operand."""
    if kind == "json":
        if _json_selector_invalid(selector):
            raise ValueError("NATIVE_GATE_SOURCE_SELECTOR_INVALID")
        source_path = selector["path"]
    else:
        source_path = selector
    raw, expected = _read_bound_source(source_path, action)
    return _decode_bound_kind(kind, raw, expected, selector)


def _prefix_before(run, index):
    continuations = []
    for point in run.continuations:
        if point.after_observations <= index:
            continuations.append(point)
    return run.model_copy(update={
        "observations": run.observations[:index],
        "continuations": tuple(continuations),
    })


def _store_pfp_facts(facts, run, index, observed, next_action, prepare_teamwork_turn, validate_teamwork_observation) -> None:
    prefix = _prefix_before(run, index)
    original = next_action(prefix)
    validate_teamwork_observation(original, observed)
    prepared = prepare_teamwork_turn(original, attempt=observed.metadata["pfp_attempt"], observe=False)
    facts["last_pfp"] = {
        "action": original.model_dump(mode="json"),
        "observation": observed.model_dump(mode="json"),
        "prompt_sha256": native_digest(prepared.prompt.to_dict()),
    }
    facts["prompt_transport"] = _prompt_transport(original, observed, prepared)


def _record_last_pfp(facts, run, next_action, prepare_teamwork_turn, validate_teamwork_observation) -> None:
    for index in range(len(run.observations) - 1, -1, -1):
        observed = run.observations[index]
        if observed.blocked:
            continue
        if observed.metadata.get("execution_kind") != "pfp":
            continue
        _store_pfp_facts(facts, run, index, observed, next_action, prepare_teamwork_turn, validate_teamwork_observation)
        return


def _not_syntax_prefilter_deterministic(observed) -> bool:
    if observed.metadata.get("role_id") != "syntax_prefilter":
        return True
    return observed.metadata.get("execution_kind") != "deterministic"


def _store_syntax(facts, run, index, observed, next_action, validate_teamwork_observation) -> None:
    prefix = _prefix_before(run, index)
    original = next_action(prefix)
    validate_teamwork_observation(original, observed)
    # Retain only the deterministic record for this finite scope. The
    # complete original observation remains in run history; geometry
    # and literary summaries do not make a cochain witness.
    facts["syntax_preflight"] = {
        "action": original.model_dump(mode="json"),
        "observation": observed.model_copy(update={"metadata": {
            "role_id": "syntax_prefilter",
            "execution_kind": "deterministic",
            "deterministic_check": observed.metadata["deterministic_check"],
        }}).model_dump(mode="json"),
    }


def _record_syntax_preflight(facts, run, next_action, validate_teamwork_observation) -> None:
    for index, observed in enumerate(run.observations):
        if _not_syntax_prefilter_deterministic(observed):
            continue
        _store_syntax(facts, run, index, observed, next_action, validate_teamwork_observation)
        return


def _apply_measured_profile(facts, run, action, next_action, validate_teamwork_observation) -> None:
    facts.update(
        schema_version="adversary.native-host-facts.v3",
        source_contract_profile=MEASURED_SOURCE_CONTRACT_PROFILE,
        syntax_preflight=None,
        original_task_check=_original_task_check(action),
    )
    _record_syntax_preflight(facts, run, next_action, validate_teamwork_observation)


def _apply_source_profile(facts, run, action, source_profile, next_action, validate_teamwork_observation) -> None:
    if source_profile == MEASURED_SOURCE_CONTRACT_PROFILE:
        _apply_measured_profile(facts, run, action, next_action, validate_teamwork_observation)
        return
    if source_profile != SOURCE_CONTRACT_PROFILE:
        raise ValueError("NATIVE_INTERGATE_PROFILE_MISMATCH")


def _import_host_fact_deps():
    from ..use_cases.teamwork import next_action
    from ..use_cases.teamwork_pfp import prepare_teamwork_turn, validate_teamwork_observation
    return next_action, prepare_teamwork_turn, validate_teamwork_observation


def _blank_host_facts(action, started_ms):
    return {
        "schema_version": "adversary.native-host-facts.v2",
        "objective_sha256": hashlib.sha256(action.objective.encode()).hexdigest(),
        "verification": {
            "started_ms": started_ms,
            "completed_ms": int(time.time_ns() // 1_000_000),
            "minimum_buffer_ms": 1,
            "scope": "current host source/artifact/binary/catalog readback",
        },
        "last_pfp": None,
        "prompt_transport": None,
    }


def _host_facts(run, action, started_ms, *, source_profile=SOURCE_CONTRACT_PROFILE):
    """Retain one actual validated model turn; never infer cognitive telemetry."""
    next_action, prepare_teamwork_turn, validate_teamwork_observation = _import_host_fact_deps()
    facts = _blank_host_facts(action, started_ms)
    _record_last_pfp(facts, run, next_action, prepare_teamwork_turn, validate_teamwork_observation)
    _apply_source_profile(facts, run, action, source_profile, next_action, validate_teamwork_observation)
    return facts


def _original_task_check(action):
    """Retain actual selected command bytes without certifying candidate prose.

    A successful software test command is not a signed mathematical checker
    receipt. In particular it does not satisfy IG10's admitted attestation.
    """
    for item in reversed(action.native_host_observations):
        check = item.get("check")
        if (type(check) is dict and check.get("initial_task_id") == action.initial_task_id
                and check.get("source_id") == action.check_source_id
                and check.get("checker_id") == action.checker_id
                and native_digest(check.get("command")) == native_digest(action.check_command)
                and check.get("artifacts") == action.artifacts and _checker_bytes(item, check) is not None):
            return json.loads(json.dumps(item, allow_nan=False))
    return None


def _prompt_transport(original, observed, prepared):
    """Compare retained preparation with fresh PFP reconstruction, not delivery."""
    captured = observed.metadata.get("pfp_prepared_prompts")
    if captured is None:
        return None
    coordinates = ["system", "user", "response_schema", "binding"]
    if type(captured) is not dict or set(captured) != set(coordinates):
        raise ValueError("NATIVE_GATE_PROMPT_TRANSPORT_CHANGED")
    reconstructed = {"system": prepared.prompt.system, "user": prepared.prompt.user,
        "response_schema": prepared.prompt.response_schema, "binding": prepared.binding}

    def encoded(value):
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

    origin, received = encoded(captured), encoded(reconstructed)
    return {"snapshot_id": original.action_id,
        "serialization_profile": "adversary.pfp-prepared-prompt.compact-utf8-json.v1",
        "transport_scope": "captured PFP preparation versus independent reconstruction; provider delivery unobserved",
        "origin_payload_utf8": origin, "origin_checksum": "sha256:" + hashlib.sha256(origin.encode()).hexdigest(),
        "payload_utf8": received, "payload_checksum": "sha256:" + hashlib.sha256(received.encode()).hexdigest(),
        "origin_coordinates": coordinates, "retained_coordinates": list(reconstructed),
        "dropped_coordinates": [key for key in coordinates if key not in reconstructed]}


def compact_prompt_transport(witness):
    """Hoist exact equal preparation bytes; retain independent source references.

    The original captured/reconstructed pair remains in host facts. Only the
    negotiated native request uses this lossless pool; resource limits and the
    native byte/coordinate predicate remain unchanged.
    """
    if type(witness) is not dict or "transport_profile" in witness:
        raise ValueError("PROMPT_TRANSPORT_PROFILE_INVALID")
    pool = []
    indexes = []
    for field, checksum in (("origin_payload_utf8", "origin_checksum"),
                            ("payload_utf8", "payload_checksum")):
        text = witness.get(field)
        if type(text) is not str:
            raise ValueError("PROMPT_TRANSPORT_TEXT_REQUIRED")
        if witness.get(checksum) != "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest():
            raise ValueError("PROMPT_TRANSPORT_CHECKSUM_CHANGED")
        if text not in pool:
            pool.append(text)
        indexes.append(pool.index(text))
    return {**{key: value for key, value in witness.items()
               if key not in ("origin_payload_utf8", "payload_utf8")},
        "transport_profile": PROMPT_TRANSPORT_POOL_PROFILE,
        "payload_pool_utf8": pool, "origin_payload_index": indexes[0],
        "payload_index": indexes[1]}


def _transport_profile(catalog_envelope):
    if catalog_envelope is None:
        return None
    profiles = catalog_envelope["result"]["outcome"]["primary_and_empirical"].get("transport_profiles", [])
    return PROMPT_TRANSPORT_POOL_PROFILE if PROMPT_TRANSPORT_POOL_PROFILE in profiles else None


def _import_host_fact_types():
    from ..use_cases.teamwork import TeamworkAction, TeamworkObservation
    from ..use_cases.teamwork_pfp import prepare_teamwork_turn, validate_teamwork_observation
    return TeamworkAction, TeamworkObservation, prepare_teamwork_turn, validate_teamwork_observation


def _host_facts_identity_changed(action, facts) -> bool:
    if type(facts) is not dict:
        return True
    if facts.get("schema_version") not in _HOST_FACT_VERSIONS:
        return True
    return facts.get("objective_sha256") != hashlib.sha256(action.objective.encode()).hexdigest()


def _verification_field_changed(verification, key) -> bool:
    if type(verification.get(key)) is not int:
        return True
    return verification[key] < 0


def _verification_changed(verification) -> bool:
    for key in ("started_ms", "completed_ms", "minimum_buffer_ms"):
        if _verification_field_changed(verification, key):
            return True
    return False


def _last_pfp_scope_changed(action, original, observed) -> bool:
    if original.run_id != action.run_id:
        return True
    if original.initial_task_id != action.initial_task_id:
        return True
    if original.objective != action.objective:
        return True
    return observed.blocked


def _v2_transport_changed(facts, original, observed, prepared) -> bool:
    if facts["schema_version"] not in _HOST_FACT_TRANSPORT_VERSIONS:
        return False
    if "prompt_transport" not in facts:
        return True
    return facts["prompt_transport"] != _prompt_transport(original, observed, prepared)


def _validate_last_pfp(action, facts, last, types) -> None:
    teamwork_action, teamwork_observation, prepare_teamwork_turn, validate_teamwork_observation = types
    original = teamwork_action.model_validate_json(json.dumps(last["action"]))
    observed = teamwork_observation.model_validate_json(json.dumps(last["observation"]))
    if _last_pfp_scope_changed(action, original, observed):
        raise ValueError("NATIVE_GATE_HOST_FACTS_CHANGED")
    validate_teamwork_observation(original, observed)
    prepared = prepare_teamwork_turn(original, attempt=observed.metadata["pfp_attempt"], observe=False)
    if native_digest(prepared.prompt.to_dict()) != last["prompt_sha256"]:
        raise ValueError("NATIVE_GATE_HOST_FACTS_CHANGED")
    if _v2_transport_changed(facts, original, observed, prepared):
        raise ValueError("NATIVE_GATE_PROMPT_TRANSPORT_CHANGED")


def _orphan_transport(facts) -> bool:
    if facts["schema_version"] not in _HOST_FACT_TRANSPORT_VERSIONS:
        return False
    return facts.get("prompt_transport") is not None


def _measured_keys_missing(facts) -> bool:
    if "syntax_preflight" not in facts:
        return True
    return "original_task_check" not in facts


def _measured_facts_changed(action, facts) -> bool:
    if facts.get("source_contract_profile") != MEASURED_SOURCE_CONTRACT_PROFILE:
        return True
    if _measured_keys_missing(facts):
        return True
    return facts["original_task_check"] != _original_task_check(action)


def _syntax_scope_changed(action, original) -> bool:
    if original.role_id != "syntax_prefilter":
        return True
    if original.communication != "deterministic":
        return True
    if original.run_id != action.run_id:
        return True
    if original.initial_task_id != action.initial_task_id:
        return True
    if original.objective != action.objective:
        return True
    return original.plan_sha256 != action.plan_sha256


def _validate_syntax(action, facts, types) -> None:
    syntax = facts["syntax_preflight"]
    if syntax is None:
        return
    teamwork_action, teamwork_observation, _prepare, validate_teamwork_observation = types
    original = teamwork_action.model_validate_json(json.dumps(syntax["action"]))
    observed = teamwork_observation.model_validate_json(json.dumps(syntax["observation"]))
    if _syntax_scope_changed(action, original):
        raise ValueError("NATIVE_GATE_HOST_FACTS_CHANGED")
    validate_teamwork_observation(original, observed)


def _validate_measured(action, facts, types) -> None:
    if facts["schema_version"] != "adversary.native-host-facts.v3":
        return
    if _measured_facts_changed(action, facts):
        raise ValueError("NATIVE_GATE_HOST_FACTS_CHANGED")
    _validate_syntax(action, facts, types)


def _validate_host_facts(action, facts):
    if facts is None:
        return
    types = _import_host_fact_types()
    if _host_facts_identity_changed(action, facts):
        raise ValueError("NATIVE_GATE_HOST_FACTS_CHANGED")
    if _verification_changed(facts["verification"]):
        raise ValueError("NATIVE_GATE_HOST_FACTS_CHANGED")
    last = facts.get("last_pfp")
    if last is not None:
        _validate_last_pfp(action, facts, last, types)
    elif _orphan_transport(facts):
        raise ValueError("NATIVE_GATE_PROMPT_TRANSPORT_CHANGED")
    _validate_measured(action, facts, types)


def _capture_identity_changed(captured) -> bool:
    fields = {"schema_version", "stdout_hex", "stderr_hex", "exit_code", "command",
              "authority_effect", "authenticated"}
    if type(captured) is not dict:
        return True
    if set(captured) != fields:
        return True
    if captured["schema_version"] != "adversary.unsigned-checker-capture.v1":
        return True
    if captured["authority_effect"] != "None":
        return True
    return captured["authenticated"] is not False


def _capture_exit_changed(captured, check) -> bool:
    if type(captured["exit_code"]) is not int:
        return True
    if type(check["exit_status"]) is not int:
        return True
    if captured["exit_code"] != check["exit_status"]:
        return True
    return native_digest(captured["command"]) != native_digest(check["command"])


def _capture_fields_changed(captured, check) -> bool:
    if _capture_identity_changed(captured):
        return True
    return _capture_exit_changed(captured, check)


def _decode_hex_field(captured, field):
    if type(captured[field]) is not str:
        raise ValueError("NATIVE_GATE_CHECKER_CAPTURE_CHANGED")
    value = bytes.fromhex(captured[field])
    if value.hex() != captured[field]:
        raise ValueError("NATIVE_GATE_CHECKER_CAPTURE_CHANGED")
    return value


def _checker_text_changed(selected_check, field, value) -> bool:
    if field not in selected_check:
        return False
    if type(selected_check[field]) is not str:
        return True
    return selected_check[field] != value.decode("utf-8", errors="replace")


def _decoded_checker_streams(captured):
    return [_decode_hex_field(captured, field) for field in ("stdout_hex", "stderr_hex")]


def _checker_bytes(selected_check, check):
    """Bind an unsigned exact-byte capture to the selected original TaskCheck."""
    captured = selected_check.get("checker_capture") if selected_check else None
    if captured is None:
        return None
    if _capture_fields_changed(captured, check):
        raise ValueError("NATIVE_GATE_CHECKER_CAPTURE_CHANGED")
    raw = _decoded_checker_streams(captured)
    if hashlib.sha256(raw[0] + b"\n--- stderr ---\n" + raw[1]).hexdigest() != check["output_sha256"]:
        raise ValueError("NATIVE_GATE_CHECKER_CAPTURE_CHANGED")
    for field, value in zip(("stdout", "stderr"), raw, strict=True):
        if _checker_text_changed(selected_check, field, value):
            raise ValueError("NATIVE_GATE_CHECKER_CAPTURE_CHANGED")
    return raw


def _typed_checker_result(raw):
    """A task-query residual is not a mathematical acceptance receipt."""
    if raw is None:
        return "NOT_MEASURED", "NOT_MEASURED"
    try:
        result = decode_native_json(raw)
    except ValueError:
        return "NOT_MEASURED", "NOT_MEASURED"
    if type(result) is not dict:
        return "NOT_MEASURED", "NOT_MEASURED"
    outcome = result.get("outcome")
    acceptance = result.get("mathematical_acceptance")
    if result.get("accepted") is False:
        outcome = "REJECTED"
    return (outcome if type(outcome) is str and outcome in {"ACCEPTED", "REJECTED", "QUERY_USER_MORE_INFO"} else "NOT_MEASURED",
            acceptance if type(acceptance) is str and acceptance in {"HOST_CHECKED", "NOT_SOLVED"} else "NOT_MEASURED")


def _artifact_digests(check):
    return [digest.removeprefix("sha256:") for digest in check["artifacts"].values()]


def _check_matches(item, action, candidate_hash) -> bool:
    check = item.get("check")
    if check is None:
        return False
    if check["initial_task_id"] != action.initial_task_id:
        return False
    if check["source_id"] != action.check_source_id:
        return False
    if check["checker_id"] != action.checker_id:
        return False
    if check["command"] != list(action.check_command):
        return False
    if check["artifacts"] != action.artifacts:
        return False
    return candidate_hash in _artifact_digests(check)


def _matching_check(action, candidate_hash):
    for item in reversed(action.native_host_observations):
        if _check_matches(item, action, candidate_hash):
            return item["check"]
    return None


def _selected_check_item(action, check):
    if check is None:
        return None
    for item in reversed(action.native_host_observations):
        if item.get("check") == check:
            return item
    return None


def _checker_output_text(selected_check, exact):
    if exact is not None:
        return exact[0].decode("utf-8", errors="replace")
    if selected_check:
        return selected_check.get("stdout")
    return None


def _typed_exact_result(exact):
    if exact is None:
        return _typed_checker_result(None)
    return _typed_checker_result(exact[0])


def _exit_verdict(check):
    if check is None:
        return "NOT_MEASURED"
    if check["exit_status"] == 0:
        return "ACCEPTED"
    return "REJECTED"


def _needs_unmeasured(original_outcome, mathematical_acceptance) -> bool:
    if original_outcome == "QUERY_USER_MORE_INFO":
        return True
    return mathematical_acceptance == "NOT_SOLVED"


def _verdict_for(check, original_outcome, mathematical_acceptance):
    verdict = _exit_verdict(check)
    if original_outcome == "REJECTED":
        return "REJECTED"
    if _needs_unmeasured(original_outcome, mathematical_acceptance):
        return "NOT_MEASURED"
    return verdict


def _candidate_path(action, candidate_hash):
    for path, digest in action.artifacts.items():
        if digest.removeprefix("sha256:") == candidate_hash:
            return path
    return None


def _candidate_raw(candidate_path, artifact_snapshots):
    if candidate_path is None:
        return None
    if artifact_snapshots is not None:
        return base64.b64decode(artifact_snapshots[candidate_path], validate=True)
    return Path(candidate_path).read_bytes()


def _text_or_blank(raw):
    if raw is None:
        return ""
    return raw.decode("utf-8")


def _sha_or_blank(raw):
    if raw is None:
        return ""
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _coordinates(candidate_path, candidate_raw):
    if candidate_raw is None:
        return []
    return [candidate_path]


def _str_or_blank(output):
    if type(output) is str:
        return output
    return ""


def _output_sha(output):
    if type(output) is str:
        return hashlib.sha256(output.encode()).hexdigest()
    return ""


def _capture_sha(check):
    if check is None:
        return ""
    return check["output_sha256"]


def _hex_or_blank(exact, index):
    if exact is None:
        return ""
    return exact[index].hex()


def _bytes_sha_or_blank(exact, index):
    if exact is None:
        return ""
    return hashlib.sha256(exact[index]).hexdigest()


def _output_fields(output, check):
    return {
        "actual_checker_output_utf8": _str_or_blank(output),
        "actual_checker_output_sha256": _output_sha(output),
        "actual_checker_capture_sha256": _capture_sha(check),
    }


def _exact_fields(exact):
    return {
        "actual_checker_stdout_hex": _hex_or_blank(exact, 0),
        "actual_checker_stderr_hex": _hex_or_blank(exact, 1),
        "actual_checker_stdout_sha256": _bytes_sha_or_blank(exact, 0),
        "actual_checker_stderr_sha256": _bytes_sha_or_blank(exact, 1),
    }


def _pfp_record(last):
    if last is None:
        return None
    return last["observation"]["metadata"]["pfp"]


def _pfp_role(last):
    if last:
        return last["action"]["role_id"]
    return ""


def _pfp_hex(record):
    if record:
        return base64.b64decode(record["raw_reply_base64"], validate=True).hex()
    return ""


def _pfp_sha(record):
    if record:
        return record["raw_reply_sha256"]
    return ""


def _pfp_selectors(host_facts):
    if host_facts is None:
        return {}
    last = host_facts.get("last_pfp")
    record = _pfp_record(last)
    return {
        "last_pfp_raw_reply_hex": _pfp_hex(record),
        "last_pfp_raw_reply_sha256": _pfp_sha(record),
        "last_pfp_role": _pfp_role(last),
    }


def _selector_dict(action, candidate_hash, verdict, original_outcome, mathematical_acceptance,
                   candidate_path, candidate_raw):
    projected = {
        "verdict": verdict,
        "candidate_content_sha256": "sha256:" + candidate_hash,
        "checker_id": action.checker_id,
        "candidate_id": action.initial_task_id,
    }
    return {
        "candidate": action.candidate,
        "candidate_sha256": "sha256:" + hashlib.sha256(action.candidate.encode()).hexdigest(),
        "artifacts": action.artifacts,
        "initial_task_id": action.initial_task_id,
        "action_id": action.action_id,
        "evaluation_round": action.evaluations_used + 1,
        "check_source_id": action.check_source_id,
        "original_task_outcome": original_outcome,
        "original_task_mathematical_acceptance": mathematical_acceptance,
        "accepted_checker_receipt_verdict": verdict,
        "accepted_checker_receipt_hex": json.dumps(projected, sort_keys=True).encode().hex(),
        "candidate_artifact_utf8": _text_or_blank(candidate_raw),
        "candidate_artifact_sha256": _sha_or_blank(candidate_raw),
        "artifact_paths": sorted(action.artifacts),
        "candidate_artifact_coordinates": _coordinates(candidate_path, candidate_raw),
    }


def _build_selectors(action, artifact_snapshots, host_facts):
    candidate_hash = hashlib.sha256(action.candidate.encode()).hexdigest()
    check = _matching_check(action, candidate_hash)
    selected_check = _selected_check_item(action, check)
    exact = _checker_bytes(selected_check, check)
    output = _checker_output_text(selected_check, exact)
    original_outcome, mathematical_acceptance = _typed_exact_result(exact)
    verdict = _verdict_for(check, original_outcome, mathematical_acceptance)
    candidate_path = _candidate_path(action, candidate_hash)
    candidate_raw = _candidate_raw(candidate_path, artifact_snapshots)
    selectors = _selector_dict(
        action, candidate_hash, verdict, original_outcome, mathematical_acceptance, candidate_path, candidate_raw)
    selectors.update(_output_fields(output, check))
    selectors.update(_exact_fields(exact))
    selectors.update(_pfp_selectors(host_facts))
    return selectors


def _source_selector(value, action):
    if type(value) is not dict:
        return _NOT_SELECTED
    for key, kind in (("$source_json", "json"), ("$source_utf8", "utf8"), ("$source_sha256", "sha256")):
        if set(value) == {key}:
            return _bound_source_value(value[key], action, kind=kind)
    return _NOT_SELECTED


def _resolve_host_selector(value, selectors):
    if type(value) is not dict:
        return _NOT_SELECTED
    if set(value) != {"$host"}:
        return _NOT_SELECTED
    if value["$host"] not in selectors:
        raise ValueError("NATIVE_GATE_SELECTOR_INVALID")
    return selectors[value["$host"]]


def _resolve_mapping(value, action, artifact_snapshots, host_facts):
    resolved = {}
    for key, item in value.items():
        resolved[key] = _resolve(item, action, artifact_snapshots, host_facts)
    return resolved


def _resolve_list(value, action, artifact_snapshots, host_facts):
    return [_resolve(item, action, artifact_snapshots, host_facts) for item in value]


def _resolve_collection(value, action, artifact_snapshots, host_facts):
    if type(value) is dict:
        return _resolve_mapping(value, action, artifact_snapshots, host_facts)
    if type(value) is list:
        return _resolve_list(value, action, artifact_snapshots, host_facts)
    return value


def _resolve(value, action, artifact_snapshots=None, host_facts=None):
    """Explicit selectors carry only actual host-owned current action values."""
    selectors = _build_selectors(action, artifact_snapshots, host_facts)
    chosen = _source_selector(value, action)
    if chosen is not _NOT_SELECTED:
        return chosen
    hosted = _resolve_host_selector(value, selectors)
    if hosted is not _NOT_SELECTED:
        return hosted
    return _resolve_collection(value, action, artifact_snapshots, host_facts)


def _default_source_profile(host_facts):
    if host_facts is None:
        return SOURCE_CONTRACT_PROFILE
    if host_facts.get("schema_version") != "adversary.native-host-facts.v3":
        return SOURCE_CONTRACT_PROFILE
    if host_facts.get("source_contract_profile") != MEASURED_SOURCE_CONTRACT_PROFILE:
        return SOURCE_CONTRACT_PROFILE
    return MEASURED_SOURCE_CONTRACT_PROFILE


def _append_required_edge(history, gate) -> None:
    source, target = INTERGATE_ENDPOINTS[INTERGATE_IDS.index(gate)]
    if len(history) >= 64:
        raise ValueError("NATIVE_GATE_HISTORY_ALLOWANCE_EXHAUSTED")
    history.append(source + "->" + target)


def _scene_reserved(witness) -> bool:
    if type(witness) is not dict:
        return True
    return "_adversary_scene" in witness


def _transport_version_ok(host_facts) -> bool:
    if host_facts is None:
        return False
    return host_facts.get("schema_version") in _HOST_FACT_TRANSPORT_VERSIONS


def _maybe_compact_transport(witness, gate, document, host_facts, transport_profile):
    if gate != "PFP-14-CONTEXT-TRANSPORT":
        return witness
    if gate in document["gates"]:
        return witness
    if not _transport_version_ok(host_facts):
        return witness
    if host_facts.get("prompt_transport") is None:
        return witness
    witness.update(host_facts["prompt_transport"])
    if transport_profile == PROMPT_TRANSPORT_POOL_PROFILE:
        return compact_prompt_transport(witness)
    return witness


def _require_observation_time(observation_time) -> None:
    if type(observation_time) is not int:
        raise ValueError("NATIVE_GATE_OBSERVATION_TIME_REQUIRED")
    if observation_time < 0:
        raise ValueError("NATIVE_GATE_OBSERVATION_TIME_REQUIRED")


def _profile_rejected(profile, default_source_profile) -> bool:
    if profile not in SOURCE_CONTRACT_PROFILES:
        return True
    if default_source_profile != SOURCE_CONTRACT_PROFILE:
        return False
    return profile != SOURCE_CONTRACT_PROFILE


def _checked_profile(witness, default_source_profile):
    profile = witness.get("contract_profile", default_source_profile)
    if _profile_rejected(profile, default_source_profile):
        raise ValueError("NATIVE_INTERGATE_PROFILE_MISMATCH")
    return profile


def _intelligence_source(action):
    if action.intelligence:
        return action.intelligence.source_id
    return ""


def _source_digest(action):
    source_id = action.check_source_id or _intelligence_source(action)
    if source_id.startswith("sha256:"):
        return source_id
    return "sha256:" + source_id


def _apply_urgency(witness, action, host_facts) -> None:
    # The literal task remains the actual downstream operand. If
    # urgency markers need removal, native correctly refuses this
    # unchanged text; no unexecuted sanitization is asserted.
    measured = host_facts["verification"]
    witness.update(
        prompt_text=action.objective,
        urgency_indicators=[],
        sanitized_prompt_text=action.objective,
        verification_started_ms=measured["started_ms"],
        verification_completed_ms=measured["completed_ms"],
        minimum_buffer_ms=measured["minimum_buffer_ms"],
        declared_time_constraint="",
    )


def _needs_urgency(gate, document, host_facts) -> bool:
    if gate != "PFP-IG-05-FALSE-URGENCY-DESENSITIZATION":
        return False
    if host_facts is None:
        return False
    return gate not in document["gates"]


def _bind_intergate_witness(action, gate, witness, document, host_facts, observation_time, default_source_profile):
    if gate not in INTERGATE_IDS:
        return witness
    if action.feedback_policy != "semantic_digestion_v2":
        return witness
    _require_observation_time(observation_time)
    profile = _checked_profile(witness, default_source_profile)
    witness = {**witness, "contract_profile": profile,
        "task_id": action.initial_task_id, "source_digest": _source_digest(action),
        "candidate_content": action.candidate, "now": observation_time}
    if _needs_urgency(gate, document, host_facts):
        _apply_urgency(witness, action, host_facts)
    return witness


def _without_reserved(witness, reserved):
    kept = {}
    for key, value in witness.items():
        if key not in reserved:
            kept[key] = value
    return kept


def _apply_process_gate(action, gate, witness, observation_time, replay_process):
    if getattr(action.native_gate_check, "process_observer", None) is None:
        return witness
    from .teamwork_process_observation import (
        PROCESS_GATES,
        process_gate_payload,
        replay_process_gate_payload,
    )
    if gate not in PROCESS_GATES:
        return witness
    reserved = {"process_profile", "process_observation", "process_trust_policy", "process_expected", "now"}
    witness = _without_reserved(witness, reserved)
    if replay_process:
        projection = replay_process_gate_payload
    else:
        projection = process_gate_payload
    witness.update(projection(action, gate, now=observation_time))
    return witness


def _apply_kernel_gate(action, gate, witness, observation_time, replay_process):
    if gate != "PFP-07-MANUSCRIPT-TRUTH":
        return witness
    if getattr(action.native_gate_check, "kernel_check", None) is None:
        return witness
    from .teamwork_kernel_observation import kernel_gate_payload
    reserved = {"kernel_profile", "kernel_observation", "kernel_trust_policy", "kernel_expected", "now"}
    witness = _without_reserved(witness, reserved)
    witness.update(kernel_gate_payload(action, now=observation_time, replay=replay_process))
    return witness


def _apply_resource_gate(action, gate, witness, replay_process):
    if gate != "PFP-22-HARDWARE-CONSTRAINT":
        return witness
    if getattr(action.native_gate_check, "resource_check", None) is None:
        return witness
    from .teamwork_resource_observation import resource_gate_payload
    reserved = {"resource_profile", "resource_expected", "resource_observation"}
    witness = _without_reserved(witness, reserved)
    witness.update(resource_gate_payload(action, replay=replay_process))
    return witness


def _gate_payload(action, gate, index, witness):
    return {**witness, "_adversary_scene": {**native_action_scope(action),
        "gate_id": gate, "visit_index": index, "stage": "native_gate:" + gate}}


def _one_gate_request(index, gate, action, document, history, artifact_snapshots, observation_time,
                      replay_process, host_facts, transport_profile, required, required_edges,
                      default_source_profile):
    if gate not in required:
        return None
    if gate in required_edges:
        _append_required_edge(history, gate)
    witness = _resolve(document["gates"].get(gate, {}), action, artifact_snapshots, host_facts)
    if _scene_reserved(witness):
        raise ValueError("NATIVE_GATE_HOST_BINDING_RESERVED")
    witness = _maybe_compact_transport(witness, gate, document, host_facts, transport_profile)
    witness = _bind_intergate_witness(
        action, gate, witness, document, host_facts, observation_time, default_source_profile)
    witness = _apply_process_gate(action, gate, witness, observation_time, replay_process)
    witness = _apply_kernel_gate(action, gate, witness, observation_time, replay_process)
    witness = _apply_resource_gate(action, gate, witness, replay_process)
    return {"operation": "gate_evaluate", "gate_id": gate,
        "payload": _gate_payload(action, gate, index, witness), "history_edges": list(history)}


def _requests(action, document, history, *, artifact_snapshots=None, observation_time=None,
              replay_process=False, host_facts=None, transport_profile=None):
    default_source_profile = _default_source_profile(host_facts)
    required = native_required_gate_ids(action)
    required_edges = native_required_edges(required)
    for index, gate in enumerate(NATIVE_GATE_IDS):
        request = _one_gate_request(
            index, gate, action, document, history, artifact_snapshots, observation_time,
            replay_process, host_facts, transport_profile, required, required_edges, default_source_profile)
        if request is not None:
            yield request


def _require_pending(action, run, next_action) -> None:
    if action.kind != "native_gates":
        raise ValueError("NATIVE_GATES_NOT_PENDING")
    if next_action(run) != action:
        raise ValueError("NATIVE_GATES_NOT_PENDING")


def _observation_clock(action):
    if action.feedback_policy == "semantic_digestion_v2":
        return int(time.time())
    if getattr(action.native_gate_check, "process_observer", None) is not None:
        return int(time.time())
    if getattr(action.native_gate_check, "kernel_check", None) is not None:
        return int(time.time())
    return None


def _new_batch_state(action):
    state = _BatchState()
    state.scoped = action.native_gate_check.gate_scope is not None
    state.applicability = native_gate_applicability(action)
    state.required = native_required_gate_ids(action)
    state.required_edges = native_required_edges(state.required)
    state.verification_started_ms = int(time.time_ns() // 1_000_000)
    state.observation_time = _observation_clock(action)
    return state


def _snapshot_artifacts(action, snapshots) -> None:
    total = 0
    for path in action.artifacts:
        raw = Path(path).read_bytes()
        total += len(raw)
        if total > 16 * 1024 * 1024:
            raise ValueError("NATIVE_GATE_ARTIFACT_SNAPSHOT_TOO_LARGE")
        snapshots[path] = base64.b64encode(raw).decode("ascii")
    validate_native_artifact_snapshots(action, snapshots)


def _optional_profile(active, name):
    if active:
        return name
    return None


def _catalog_expectations(action, selection):
    return {
        "expected_profile": _optional_profile(
            action.feedback_policy == "semantic_digestion_v2", SOURCE_CONTRACT_PROFILE),
        "expected_process_profile": _optional_profile(
            selection.process_observer is not None, "adversary.host-process.v1"),
        "expected_kernel_profile": _optional_profile(
            selection.kernel_check is not None, "adversary.host-lean.v1"),
        "expected_resource_profile": _optional_profile(
            selection.resource_check is not None, "adversary.host-job-resources.v1"),
    }


def _open_catalog(host, action, selection):
    catalog_envelope = _invoke(host, {"operation": "gate_schemas"})
    catalog = _catalog(catalog_envelope, **_catalog_expectations(action, selection))
    return catalog_envelope, catalog


def _selected_source_profile(catalog):
    profiles = catalog.get("intergate_profiles", [])
    if MEASURED_SOURCE_CONTRACT_PROFILE in profiles:
        return MEASURED_SOURCE_CONTRACT_PROFILE
    return SOURCE_CONTRACT_PROFILE


def _record_host_facts(state, run, action, catalog) -> None:
    if action.feedback_policy != "semantic_digestion_v2":
        return
    state.host_facts = _host_facts(
        run, action, state.verification_started_ms, source_profile=_selected_source_profile(catalog))
    _validate_host_facts(action, state.host_facts)


def _specifications(catalog):
    return {row["gate_id"]: row["specification_sha256"]
            for row in catalog["primary_and_empirical"]["gates"]}


def _accepted_outcome(response):
    if response.get("success") is not True:
        return None
    if response["result"]["refusal"] is not None:
        return None
    return response["result"]["outcome"]


def _specification_drifted(specifications, selection, gate_id, spec) -> bool:
    if specifications.get(gate_id, spec) != spec:
        return True
    return selection.specification_sha256.get(gate_id, spec) != spec


def _append_gate_row(rows, source_rows, request, response, captures, specifications, selection) -> None:
    outcome = _accepted_outcome(response)
    if outcome is not None:
        spec = outcome.get("specification_sha256")
        if _specification_drifted(specifications, selection, request["gate_id"], spec):
            raise ValueError("NATIVE_GATE_SPECIFICATION_DRIFT")
    rows.append({"gate_id": request["gate_id"], "request": request, "response": response,
        "request_sha256": native_digest(request), "response_sha256": native_digest(response),
        "process": captures[-1]})
    source_rows[request["gate_id"]] = rows[-1]


def _edge_statuses(source_row, edge_row, canonical_target, target_response):
    rows = (source_row, edge_row, {"gate_id": canonical_target, "response": target_response})
    statuses = []
    for row in rows:
        statuses.append(native_gate_summary({"results": [row]})["outcomes"][row["gate_id"]])
    return statuses


def _canonical_target(target):
    if target == "PFP-07-MASTER":
        return "PFP-07-MANUSCRIPT-TRUTH"
    return target


def _edge_admitted(selection, passed) -> bool:
    if selection.policy != "require_pass":
        return False
    return bool(passed)


def _transition_record(request, source, target, canonical_target, source_row, edge_row,
                       target_request, target_response, captures, statuses, selection):
    passed = statuses == ["PASS", "PASS", "PASS"]
    return {"intergate_id": request["gate_id"], "source_gate": source,
        "target_gate": target, "canonical_target_gate": canonical_target,
        "source_request_sha256": source_row["request_sha256"],
        "source_response_sha256": source_row["response_sha256"],
        "edge_request_sha256": edge_row["request_sha256"],
        "edge_response_sha256": edge_row["response_sha256"],
        "target_request": target_request, "target_response": target_response,
        "target_process": captures[-1], "target_request_sha256": native_digest(target_request),
        "target_response_sha256": native_digest(target_response),
        "source_status": statuses[0], "edge_status": statuses[1], "target_status": statuses[2],
        "attempted": True, "admitted": _edge_admitted(selection, passed), "diagnostic_path_passed": passed,
        "role_flow_traversal": False, "authority_effect": "None"}


def _append_transition(transitions, request, rows, source_rows, history, host, captures, selection, required_edges) -> None:
    if request["gate_id"] not in required_edges:
        return
    source, target = INTERGATE_ENDPOINTS[INTERGATE_IDS.index(request["gate_id"])]
    canonical = _canonical_target(target)
    source_row, target_row = source_rows[source], source_rows[canonical]
    # The edge evaluation precedes an actual target predicate replay.
    # This is a diagnostic native graph; role movement and external
    # observation authentication are separate claims.
    target_request = json.loads(json.dumps(target_row["request"]))
    target_request["payload"]["_adversary_scene"]["stage"] = "native_edge_target:" + request["gate_id"]
    target_request["history_edges"] = list(history)
    target_response = _invoke(host, target_request)
    statuses = _edge_statuses(source_row, rows[-1], canonical, target_response)
    transitions.append(_transition_record(
        request, source, target, canonical, source_row, rows[-1], target_request, target_response,
        captures, statuses, selection))


def _collect_gate_rows(action, document, history, state, host, catalog, selection) -> None:
    specifications = _specifications(catalog)
    source_rows = {}
    for request in _requests(action, document, history, observation_time=state.observation_time,
            host_facts=state.host_facts, transport_profile=_transport_profile(state.catalog_envelope)):
        response = _invoke(host, request)
        _append_gate_row(state.rows, source_rows, request, response, state.captures, specifications, selection)
        _append_transition(
            state.transitions, request, state.rows, source_rows, history, host, state.captures,
            selection, state.required_edges)


def _batch_schema(scoped):
    if scoped:
        return "adversary.native-gate-batch.v2"
    return "adversary.native-gate-batch.v1"


def _base_receipt(action, state, execution_complete):
    receipt = {
        "schema_version": _batch_schema(state.scoped),
        "scope": native_action_scope(action),
    }
    if state.scoped:
        receipt["applicability"] = state.applicability
    receipt.update({
        "history_profile": ACTUAL_TRAVERSAL_HISTORY,
        "binary": state.binary,
        "catalog_response": state.catalog_envelope,
        "catalog_process": state.captures[0],
        "catalog_sha256": native_digest(state.catalog_envelope),
        "results": state.rows,
        "transitions": state.transitions,
        "execution_complete": execution_complete,
        "artifact_snapshots": state.artifact_snapshots,
        "digest_profile": "adversary.native-parsed-envelope.v1",
        "authority_effect": "None",
    })
    return receipt


def _retain_action(action):
    retained = action.model_dump(mode="json")
    retained["role_contributions"] = []
    return retained


def _stamp_optional_receipt(receipt, state) -> None:
    if state.observation_time is not None:
        receipt["observation_time_utc"] = state.observation_time
    if state.host_facts is not None:
        receipt["host_facts"] = state.host_facts


def _seal_complete_receipt(action, state):
    receipt = _base_receipt(action, state, True)
    _stamp_optional_receipt(receipt, state)
    receipt["action"] = _retain_action(action)
    receipt["receipt_sha256"] = native_digest(receipt)
    validate_native_gate_receipt(action, receipt)
    return receipt


def _receipt_bytes(receipt):
    return (json.dumps(receipt, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode()


def _load_existing_receipt(path, action):
    previous = decode_native_json(path.read_bytes())
    replay_native_gate_receipt(action, previous)
    return previous, path.read_bytes()


def _write_new_receipt(path, receipt):
    raw = _receipt_bytes(receipt)
    with path.open("xb") as handle:
        handle.write(raw)
    return raw


def _persist_receipt(selection, run, action, output_dir, receipt):
    summary = native_gate_summary(receipt)
    path = _receipt_path(selection, run, action, output_dir)
    if path.exists():
        receipt, raw = _load_existing_receipt(path, action)
        summary = native_gate_summary(receipt)
        return receipt, raw, summary, path
    raw = _write_new_receipt(path, receipt)
    return receipt, raw, summary, path


def _persist_complete(selection, run, action, output_dir, state):
    return _persist_receipt(selection, run, action, output_dir, _seal_complete_receipt(action, state))


def _run_batch(run, action, output_dir, state):
    selection, document, history = _inputs(action)
    _snapshot_artifacts(action, state.artifact_snapshots)
    host, state.binary, state.captures = _host(selection)
    state.catalog_envelope, catalog = _open_catalog(host, action, selection)
    _record_host_facts(state, run, action, catalog)
    _collect_gate_rows(action, document, history, state, host, catalog, selection)
    _inputs(action)
    _host(selection, expected_binary=state.binary)
    return _persist_complete(selection, run, action, output_dir, state)


def _reference(path, raw, receipt, action, summary):
    return {"schema_version": "adversary.native-gate-reference.v1", "path": str(path.absolute()),
        "sha256": hashlib.sha256(raw).hexdigest(), "receipt_sha256": receipt["receipt_sha256"],
        "scope": native_action_scope(action), "summary": summary, "authority_effect": "None"}


def _execution_summary(scoped, required):
    if scoped:
        return (f"Executed {len(required)} scoped native diagnostic predicates; "
                "excluded gates remain explicitly deferred or not applicable.")
    return "Executed 22 primary,10 intergate and3 empirical native diagnostic predicates."


def _strict_stop(selection, summary) -> bool:
    if selection.policy != "require_pass":
        return False
    return not summary["all_pass"]


def _strict_findings(summary, strict_stop):
    if not strict_stop:
        return ()
    return tuple("Native diagnostic " + row["gate_id"] + ": " + row["status"] for row in summary["residuals"])


def _v3_host_facts(receipt) -> bool:
    facts = receipt.get("host_facts") or {}
    return facts.get("schema_version") == "adversary.native-host-facts.v3"


def _success_metadata(action, selection, reference, summary, receipt, strict_stop):
    metadata = {"role_id": action.role_id, "execution_kind": "host", "native_gate_receipt": reference,
        "native_gate_summary": summary, "native_gate_policy": selection.policy,
        "primary_gate_classification": classify_primary_gate_batch(action, receipt)}
    if _v3_host_facts(receipt):
        metadata["native_gate_inputs"] = gate_input_report(action, receipt)
    if strict_stop:
        metadata["failure_code"] = "NATIVE_GATE_POLICY_STOP"
    return metadata


def _success_observation(observation_cls, action, state, receipt, raw, summary, path, selection):
    stopped = _strict_stop(selection, summary)
    return observation_cls(
        action_id=action.action_id, worker="native Adversary gate host",
        summary=_execution_summary(state.scoped, state.required),
        blocked=stopped, artifacts=action.artifacts,
        findings=_strict_findings(summary, stopped),
        metadata=_success_metadata(
            action, selection, _reference(path, raw, receipt, action, summary), summary, receipt, stopped))


def _partial_receipt(action, state, exc):
    partial = _base_receipt(action, state, False)
    partial["observed_processes"] = state.captures
    partial["failure_detail"] = str(exc)
    partial["action"] = _retain_action(action)
    _stamp_optional_receipt(partial, state)
    partial["receipt_sha256"] = native_digest(partial)
    return partial


def _store_partial(path, partial):
    raw = _receipt_bytes(partial)
    if not path.exists():
        with path.open("xb") as handle:
            handle.write(raw)
        return raw, partial
    raw = path.read_bytes()
    return raw, decode_native_json(raw)


def _retained_partial(action, run, output_dir, state, exc):
    partial = _partial_receipt(action, state, exc)
    path = _receipt_path(action.native_gate_check, run, action, output_dir, partial=True)
    raw, partial = _store_partial(path, partial)
    return {"native_gate_receipt": _reference(path, raw, partial, action, native_gate_summary(partial))}


def _maybe_partial(action, run, output_dir, state, exc):
    if state.binary is None:
        return {}
    if not state.captures:
        return {}
    return _retained_partial(action, run, output_dir, state, exc)


def _failure_fallback(state):
    if not state.scoped:
        return None
    return {"schema_version": "adversary.native-gate-batch.v2", "applicability": state.applicability,
            "execution_complete": False, "results": [], "transitions": []}


def _failure_summary(retained_partial, state):
    fallback = native_gate_summary(_failure_fallback(state))
    return retained_partial.get("native_gate_receipt", {}).get("summary", fallback)


def _failure_metadata(action, retained_partial, state):
    metadata = {"role_id": action.role_id, "execution_kind": "host",
        "failure_code": "NATIVE_GATE_UNAVAILABLE",
        "native_gate_summary": _failure_summary(retained_partial, state)}
    if state.scoped:
        metadata["native_gate_applicability"] = state.applicability
    metadata.update(retained_partial)
    return metadata


def _failure_observation(observation_cls, run, action, output_dir, state, exc):
    retained_partial = _maybe_partial(action, run, output_dir, state, exc)
    return observation_cls(
        action_id=action.action_id, worker="native Adversary gate host",
        summary=f"Native diagnostic execution unavailable: {type(exc).__name__}: {exc}",
        blocked=True, artifacts=action.artifacts, findings=("Native gate coverage remains incomplete",),
        metadata=_failure_metadata(action, retained_partial, state))


def execute_native_gates(run, action, *, output_dir=None):
    """Observe the selected native predicates; retain strict-policy residuals."""
    from ..use_cases.teamwork import TeamworkObservation, next_action

    _require_pending(action, run, next_action)
    state = _new_batch_state(action)
    try:
        receipt, raw, summary, path = _run_batch(run, action, output_dir, state)
        selection = action.native_gate_check
        return _success_observation(TeamworkObservation, action, state, receipt, raw, summary, path, selection)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        return _failure_observation(TeamworkObservation, run, action, output_dir, state, exc)


def _applicability_for(receipt, action):
    if receipt.get("schema_version") == "adversary.native-gate-batch.v2":
        return native_gate_applicability(action), True
    return {"required": list(NATIVE_GATE_IDS)}, False


def _deferred_outcome(gate, applicability):
    if gate in applicability["deferred"]:
        return {"gate_id": gate, "status": "DEFERRED", "evidence_grade": "NOT_EVALUATED",
            "reason": "Host selected this predicate for another checkpoint; no outcome is asserted."}
    return {"gate_id": gate, "status": "NOT_APPLICABLE", "evidence_grade": "NOT_EVALUATED",
        "reason": "Host excluded this predicate from the declared task scope; no outcome is asserted."}


def _unsupported(gate, reason):
    return {"gate_id": gate, "status": "UNSUPPORTED_OBSERVATION", "evidence_grade": "UNAVAILABLE", "reason": reason}


def _primary_outcome(gate, row, classify_gate_outcome):
    if row is None:
        return _unsupported(gate, "No completed native predicate capture.")
    response = row["response"]
    result = response.get("result") or {}
    if response.get("success") is not True:
        return _unsupported(gate, "Native transport/runtime did not return a predicate outcome.")
    if result.get("refusal") is not None:
        return _unsupported(gate, "Native transport/runtime did not return a predicate outcome.")
    return classify_gate_outcome(gate, row["request"]["payload"], result.get("outcome")).to_json()


def _collect_primary_outcomes(applicability, by_id, classify_gate_outcome):
    outcomes = []
    for gate in PRIMARY_GATE_IDS:
        if gate not in applicability["required"]:
            outcomes.append(_deferred_outcome(gate, applicability))
        else:
            outcomes.append(_primary_outcome(gate, by_id.get(gate), classify_gate_outcome))
    return outcomes


def _classification_version(scoped):
    if scoped:
        return "adversary.primary-gate-classification.v2"
    return "adversary.primary-gate-classification.v1"


def _classification_report(scoped, applicability, outcomes, receipt, gate_capabilities):
    report = {"schema_version": _classification_version(scoped), "outcomes": outcomes}
    if scoped:
        report["applicability"] = applicability
    report["capabilities"] = [row.to_json() for row in gate_capabilities()]
    report["receipt_sha256"] = receipt["receipt_sha256"]
    report["creates_rejection_labels"] = False
    report["authority_effect"] = "None"
    return report


def classify_primary_gate_batch(action, receipt):
    """Read back actual captures without changing historical batches or labels.

    The pure classifier describes each supplied predicate's evidence ceiling.
    This report never turns diagnostic coverage or a forwarded reason into a
    checked occurrence rejection; that requires the separate invoking adapter.
    """
    from .gate_occurrences import classify_gate_outcome, gate_capabilities

    validate_native_gate_receipt(action, receipt)
    by_id = {row["gate_id"]: row for row in receipt["results"]}
    applicability, scoped = _applicability_for(receipt, action)
    outcomes = _collect_primary_outcomes(applicability, by_id, classify_gate_outcome)
    return _classification_report(scoped, applicability, outcomes, receipt, gate_capabilities)


def _marked(code, tokens) -> bool:
    if not code:
        return False
    for token in tokens:
        if token in code:
            return True
    return False


def _base_input_grade(status):
    if status == "PASS":
        return "FINITE_SUPPLIED_DIAGNOSTIC"
    return "SCOPED_SOURCE_REFUSAL"


def _input_grade(status, code):
    grade = _base_input_grade(status)
    if status in ("HOLD", "UNAVAILABLE"):
        return "UNAVAILABLE"
    if _marked(code, ("TRUST", "SIGNATURE", "ATTESTATION", "ISSUER", "KEY_")):
        return "UNTRUSTED"
    if _marked(code, ("INVALID", "MALFORMED", "BINDING_MISMATCH")):
        return "INVALID"
    return grade


def _use_native_missing(outcome, status) -> bool:
    if outcome.get("contract_profile") != MEASURED_SOURCE_CONTRACT_PROFILE:
        return False
    if status != "HOLD":
        return False
    return type(outcome.get("missing_inputs")) is list


def _intergate_reason(status, missing, malformed, outcome):
    if status != "HOLD":
        return outcome.get("diagnostics", "Native source observation unavailable.")
    if not missing:
        return outcome.get("diagnostics", "Native source observation unavailable.")
    if malformed:
        return outcome.get("diagnostics", "Native source observation unavailable.")
    return "Required measured source observations are absent; no defaults are inferred."


def _intergate_inputs(gate, payload, outcome, status):
    missing = list(missing_source_inputs(gate, payload))
    if _use_native_missing(outcome, status):
        missing = list(outcome["missing_inputs"])
    malformed = validate_payload(gate, payload)
    return missing, malformed, _intergate_reason(status, missing, malformed, outcome)


def _primary_missing(status, required_fields, payload):
    if status != "HOLD":
        return []
    missing = []
    for key in required_fields:
        if key not in payload:
            missing.append(key)
    return missing


def _empirical_inputs(gate, payload, status, required, primary):
    missing = _primary_missing(status, required[gate], payload)
    reason = primary.get(gate, {}).get(
        "reason", "The empirical experiment has not supplied its bounded observations.")
    return missing, None, reason


def _describe_inputs(gate, payload, outcome, status, required, primary):
    if gate in INTERGATE_IDS:
        return _intergate_inputs(gate, payload, outcome, status)
    return _empirical_inputs(gate, payload, status, required, primary)


def _row_reason(transport_error, reason):
    message = transport_error.get("message")
    if message:
        return message
    return reason


def _refusal_code(outcome, transport_error):
    code = outcome.get("refusal_code")
    if code:
        return code
    return transport_error.get("code")


def _mapping_or_empty(value):
    if value:
        return value
    return {}


def _input_row(row, required, primary):
    gate, payload, envelope = row["gate_id"], row["request"]["payload"], row["response"]
    result = _mapping_or_empty(envelope.get("result"))
    outcome = _mapping_or_empty(result.get("outcome"))
    transport_error = _mapping_or_empty(result.get("refusal"))
    status = outcome.get("status", "UNAVAILABLE")
    missing, malformed, reason = _describe_inputs(gate, payload, outcome, status, required, primary)
    code = _refusal_code(outcome, transport_error)
    grade = _input_grade(status, code)
    return {"gate_id": gate, "status": status, "refusal_code": code, "missing_inputs": missing,
        "malformed_input": malformed, "reason": _row_reason(transport_error, reason),
        "evidence_grade": primary.get(gate, {}).get("evidence_grade", grade),
        "request_sha256": row["request_sha256"], "response_sha256": row["response_sha256"]}


def _input_rows(receipt, required, primary):
    return [_input_row(row, required, primary) for row in receipt["results"]]


def _deferred_input_row(gate, applicability):
    if gate in applicability["deferred"]:
        status = "DEFERRED"
        reason = "Host deferred this predicate to another checkpoint."
    else:
        status = "NOT_APPLICABLE"
        reason = "Host excluded this predicate from the declared task scope."
    return {"gate_id": gate, "status": status, "refusal_code": None, "missing_inputs": [],
        "malformed_input": None, "reason": reason, "evidence_grade": "NOT_EVALUATED",
        "request_sha256": None, "response_sha256": None}


def _append_scoped_gaps(rows, applicability) -> None:
    for gate in NATIVE_GATE_IDS:
        if gate in applicability["required"]:
            continue
        rows.append(_deferred_input_row(gate, applicability))
    rows.sort(key=lambda row: NATIVE_GATE_IDS.index(row["gate_id"]))


def _exit_status(original):
    if original:
        return original["check"]["exit_status"]
    return None


def _available_host_facts(facts):
    original = facts["original_task_check"]
    return {
        "syntax_preflight": facts["syntax_preflight"] is not None,
        "syntax_scope": "Action/plan syntax only; not PFP01's cochain/admission predicate.",
        "captured_preparation": facts["prompt_transport"] is not None,
        "original_task_check": original is not None,
        "original_task_exit_status": _exit_status(original),
        "checker_scope": "Selected unsigned command/raw output only; not an authenticated terminal/mathematical receipt.",
    }


def _input_report_version(scoped):
    if scoped:
        return "adversary.native-gate-input-report.v2"
    return "adversary.native-gate-input-report.v1"


def _input_report(scoped, applicability, rows, facts, receipt):
    report = {"schema_version": _input_report_version(scoped), "rows": rows}
    if scoped:
        report["applicability"] = applicability
    report["available_host_facts"] = _available_host_facts(facts)
    report["receipt_sha256"] = receipt["receipt_sha256"]
    report["creates_rejection_labels"] = False
    report["authority_effect"] = "None"
    return report


def gate_input_report(action, receipt):
    """Explain actual V2 input prerequisites without changing native verdicts.

    This is readback of a validated batch, not applicability inferred from a
    persona, a replacement witness, or permission to bypass an unavailable gate.
    Old batches retain their existing profiles and classification metadata.
    """
    validate_native_gate_receipt(action, receipt)
    facts = receipt.get("host_facts") or {}
    if facts.get("schema_version") != "adversary.native-host-facts.v3":
        raise ValueError("NATIVE_GATE_INPUT_REPORT_PROFILE_REQUIRED")
    _validate_host_facts(action, facts)
    catalog = receipt["catalog_response"]["result"]["outcome"]["primary_and_empirical"]
    required = {row["gate_id"]: row["required_witness_fields"] for row in catalog["gates"]}
    primary = {row["gate_id"]: row for row in classify_primary_gate_batch(action, receipt)["outcomes"]}
    rows = _input_rows(receipt, required, primary)
    scoped = receipt.get("schema_version") == "adversary.native-gate-batch.v2"
    applicability = native_gate_applicability(action) if scoped else {"required": list(NATIVE_GATE_IDS)}
    if scoped:
        _append_scoped_gaps(rows, applicability)
    return _input_report(scoped, applicability, rows, facts, receipt)


def _replay_catalog(host, action, selection, receipt) -> None:
    catalog = _invoke(host, {"operation": "gate_schemas"})
    _catalog(catalog, **_catalog_expectations(action, selection))
    if catalog != receipt["catalog_response"]:
        raise ValueError("NATIVE_GATE_CATALOG_DRIFT")
    if native_digest(catalog) != receipt["catalog_sha256"]:
        raise ValueError("NATIVE_GATE_CATALOG_DRIFT")


def _replay_pair(host, captures, request, retained_process, retained_request, retained_response, binary, code) -> None:
    current = _invoke(host, request)
    current_semantic = native_response_semantics(captures[-1], request, current, binary)
    retained_semantic = native_response_semantics(retained_process, retained_request, retained_response, binary)
    if native_digest(current_semantic) != native_digest(retained_semantic):
        raise ValueError(code)


def _replay_result_row(host, captures, expected, row, receipt) -> None:
    if native_digest(expected) != row["request_sha256"]:
        raise ValueError("NATIVE_GATE_WITNESS_CHANGED")
    _replay_pair(host, captures, expected, row["process"], row["request"], row["response"], receipt["binary"],
                 "NATIVE_GATE_PREDICATE_REPLAY_MISMATCH")


def _replay_saved_rows(host, captures, requests, receipt) -> None:
    for expected, row in zip(requests, receipt["results"], strict=True):
        _replay_result_row(host, captures, expected, row, receipt)


def _replay_edges(host, captures, receipt) -> None:
    for edge in receipt["transitions"]:
        _replay_pair(host, captures, edge["target_request"], edge["target_process"], edge["target_request"],
                     edge["target_response"], receipt["binary"], "NATIVE_GATE_TRANSITION_REPLAY_MISMATCH")


def replay_native_gate_receipt(action, receipt):
    """Rerun actual native predicates and source/witness bindings; never models."""
    validate_native_gate_receipt(action, receipt)
    _validate_host_facts(action, receipt.get("host_facts"))
    history_profile = receipt.get("history_profile", LEGACY_SCAN_HISTORY)
    selection, document, history = _inputs(action, artifact_snapshots=receipt.get("artifact_snapshots", {}),
        history_profile=history_profile)
    host, _binary, captures = _host(selection, expected_binary=receipt["binary"])
    if receipt["catalog_response"] is not None:
        _replay_catalog(host, action, selection, receipt)
    requests = list(islice(_requests(action, document, history,
        artifact_snapshots=receipt.get("artifact_snapshots", {}),
        observation_time=receipt.get("observation_time_utc"), replay_process=True,
        host_facts=receipt.get("host_facts"), transport_profile=_transport_profile(
            receipt.get("catalog_response"))), len(receipt["results"])))
    _replay_saved_rows(host, captures, requests, receipt)
    _replay_edges(host, captures, receipt)
    _inputs(action, artifact_snapshots=receipt.get("artifact_snapshots", {}), history_profile=history_profile)
    _host(selection, expected_binary=receipt["binary"])


def replay_native_gate_reference(action, reference):
    """Read exact retained bytes and replay one bound checkpoint."""
    validate_native_gate_receipt(action, reference)
    from .teamwork_intelligence_host import _current_artifacts

    _current_artifacts({reference["path"]: reference["sha256"]})
    _safe_native_path(reference["path"])
    raw = Path(reference["path"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != reference["sha256"]:
        raise ValueError("NATIVE_GATE_RECEIPT_CHANGED")
    full = decode_native_json(raw)
    if (full["receipt_sha256"] != reference["receipt_sha256"]
            or native_gate_summary(full) != reference["summary"]):
        raise ValueError("NATIVE_GATE_REFERENCE_MISMATCH")
    replay_native_gate_receipt(action, full)
    return full


def _changed_artifacts(action, changed_paths):
    retained = {}
    for path, digest in action.artifacts.items():
        if path not in changed_paths:
            retained[path] = digest
    return retained


def _scope_key_changed(action, retained, key) -> bool:
    return retained["scope"][key] != native_action_scope(action)[key]


def _scope_changed(action, retained) -> bool:
    for key in _SCOPE_KEYS:
        if _scope_key_changed(action, retained, key):
            return True
    return False


def _checker_bindings(action):
    bindings = [(action.checker_id, action.check_command, action.check_source_id, action.check_source_paths)]
    for binding in action.acceptance_predecessors:
        bindings.append((binding.checker_id, binding.operation, binding.source_id, binding.check_source_paths))
    return bindings


def _checker_unbound(action, original) -> bool:
    current = (original.checker_id, original.check_command, original.check_source_id, original.check_source_paths)
    return current not in _checker_bindings(action)


def _replay_one_batch(action, retained, teamwork_action) -> None:
    raw = Path(retained["path"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != retained["sha256"]:
        raise ValueError("NATIVE_GATE_RECEIPT_CHANGED")
    full = decode_native_json(raw)
    original = teamwork_action.model_validate_json(json.dumps(full["action"]))
    replay_native_gate_reference(original, retained)
    if _scope_changed(action, retained):
        raise ValueError("NATIVE_GATE_SCOPE_CHANGED")
    # An explicit continuation may add a current-state wrapper. Its prior
    # native batches retain their original selected checker, command and
    # source manifest; only full declared predecessor bindings admit them.
    if _checker_unbound(action, original):
        raise ValueError("NATIVE_GATE_SCOPE_CHANGED")
    if original.source_reads != action.source_reads[:len(original.source_reads)]:
        raise ValueError("NATIVE_GATE_SCOPE_CHANGED")


def _replay_context_batches(action, changed_paths) -> None:
    from ..use_cases.teamwork import TeamworkAction
    from .teamwork_intelligence_host import _current_artifacts

    _current_artifacts(_changed_artifacts(action, changed_paths))
    for retained in action.native_gate_batches:
        _replay_one_batch(action, retained, TeamworkAction)


def _candidate_changed(action, latest) -> bool:
    if latest["candidate_sha256"] != hashlib.sha256(action.candidate.encode()).hexdigest():
        return True
    return latest["artifacts_sha256"] != native_digest(action.artifacts)


def _policy_stopped(action) -> bool:
    if action.native_gate_check.policy != "require_pass":
        return False
    return not action.native_gate_batches[-1]["summary"]["all_pass"]


def _require_recheck(action) -> None:
    if not action.native_gate_batches:
        raise ValueError("NATIVE_GATE_CHECK_REQUIRED")
    latest = action.native_gate_batches[-1]["scope"]
    if _candidate_changed(action, latest):
        raise ValueError("NATIVE_GATE_CANDIDATE_CHANGED")
    if _policy_stopped(action):
        raise ValueError("NATIVE_GATE_POLICY_STOP")


def validate_native_gate_context(action, *, changed_paths=()):
    """Read retained gate-action bytes and replay before acceptance/DDC reuse."""
    if action.workflow_version != "core.adversary.teamwork.v4":
        return
    _replay_context_batches(action, changed_paths)
    if action.kind == "recheck":
        _require_recheck(action)

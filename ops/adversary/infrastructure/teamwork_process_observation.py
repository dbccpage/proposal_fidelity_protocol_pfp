"""Opt-in signing of an actually completed direct child under pinned operator trust.

The native EIS owner verifies signatures. This observer makes no claim of OS
isolation, descendant termination, semantic correctness, or human key identity.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import time
from pathlib import Path

from ..domain.native_gate_check import ProcessObserverConfig, decode_native_json

PROCESS_PROFILE = "adversary.host-process.v1"
PROCESS_GATES = {"PFP-15-BARE-METAL-ANCHOR": "15_ground_reality.yaml",
                 "PFP-20-COVERT-VERIFIER": "20_covert_verification.yaml"}


def _bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def observer_source_digest() -> str:
    """Digest the actual two-file owning implementation, using explicit labels."""
    directory = Path(__file__).parent
    return _digest(_bytes([[name, _digest((directory / name).read_bytes())] for name in
        ("teamwork_intelligence_host.py", "teamwork_process_observation.py")]))


def _read_bound(path, digest):
    from .teamwork_native_gates import _safe_native_path

    selected = _safe_native_path(path)
    if not selected.is_file() or selected.stat().st_nlink != 1:
        raise ValueError("PROCESS_OBSERVER_FILE_INVALID")
    raw = selected.read_bytes()
    if len(raw) > 1024 * 1024 or hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError("PROCESS_OBSERVER_FILE_CHANGED")
    return raw


def _configuration(config, *, signing=False, replay=False, scope=PROCESS_PROFILE,
                   source_digest_fn=None):
    current_source = source_digest_fn or observer_source_digest
    if not replay and config.observer_source_digest != current_source():
        raise ValueError("PROCESS_OBSERVER_SOURCE_CHANGED")
    policy = decode_native_json(_read_bound(config.policy_path, config.policy_sha256))
    if (type(policy) is not dict or policy.get("schema_version") != "core.eis.trust-policy.v1"
            or not isinstance(policy.get("trust_domain"), str) or not policy["trust_domain"].strip()
            or type(policy.get("keys")) is not list):
        raise ValueError("PROCESS_OBSERVER_POLICY_INVALID")
    keys = [key for key in policy["keys"] if type(key) is dict
        and (key.get("issuer"), key.get("key_id")) == (config.issuer, config.key_id)]
    if len(keys) != 1:
        raise ValueError("PROCESS_OBSERVER_KEY_UNCONFIGURED")
    key = keys[0]
    now = int(time.time())
    if (key.get("revoked") is not False or type(key.get("purposes")) is not list
            or type(key.get("scopes")) is not list
            or "observation" not in key["purposes"] or scope not in key["scopes"]
            or key.get("observer_source_digest") != config.observer_source_digest
            or any(type(key.get(name)) is not int for name in
                ("not_before", "not_after", "max_lifetime_seconds"))
            or signing and not (key["not_before"] <= now < now + config.lifetime_seconds <= key["not_after"])
            or config.lifetime_seconds > key["max_lifetime_seconds"]):
        raise ValueError("PROCESS_OBSERVER_POLICY_REFUSED")
    private = None
    if signing:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        private = serialization.load_pem_private_key(
            _read_bound(config.private_key_path, config.private_key_sha256), password=None)
        if not isinstance(private, Ed25519PrivateKey) or private.public_key().public_bytes(
                serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex() != key.get("public_key_hex"):
            raise ValueError("PROCESS_OBSERVER_PRIVATE_KEY_MISMATCH")
    return policy, private


def bind_process_observer_config(path: Path) -> ProcessObserverConfig:
    """Read explicit operator configuration without generating/discovering keys."""
    raw = path.read_bytes()
    config = ProcessObserverConfig.model_validate(decode_native_json(raw))
    config = config.model_copy(update={"policy_path": str(Path(config.policy_path).resolve()),
        "private_key_path": str(Path(config.private_key_path).resolve())})
    _configuration(config, signing=True)
    return config


def _manifest(files):
    return [[path, digest if digest.startswith("sha256:") else "sha256:" + digest]
            for path, digest in sorted(files.items())]


def _scope(action):
    requested = list(action.check_command)
    source = action.check_source_id
    if not source or not action.run_id or not action.initial_task_id:
        raise ValueError("PROCESS_OBSERVATION_BINDING_REQUIRED")
    return {"run_id": action.run_id, "task_id": action.initial_task_id, "action_id": action.action_id,
        "source_digest": source if source.startswith("sha256:") else "sha256:" + source,
        "candidate_sha256": _digest(action.candidate.encode("utf-8")), "checker_id": action.checker_id,
        "requested_argv": requested, "checker_source_paths": _manifest(action.check_source_paths),
        "artifacts": _manifest(action.artifacts)}


def _basis(action):
    scope = _scope(action)
    requested = scope["requested_argv"]
    executable = shutil.which(requested[0])
    if executable is None:
        raise ValueError("PROCESS_EXECUTABLE_UNAVAILABLE")
    executable = Path(executable).resolve()
    return {**scope, "argv": [str(executable), *requested[1:]],
        "executable_path": str(executable), "executable_sha256": _digest(executable.read_bytes()),
        "observer_source_digest": observer_source_digest()}


def prepare_process_capture(action):
    config = action.native_gate_check.process_observer
    policy, _private = _configuration(config, signing=True)
    return {"basis": _basis(action), "policy": policy}


def _context(record):
    return _digest(_bytes([record[key] for key in ("run_id", "task_id", "action_id", "source_digest",
        "candidate_sha256", "checker_id", "requested_argv", "checker_source_paths", "artifacts")]))


def _signing_bytes(statement):
    binding = statement["binding"]
    return _bytes([statement["schema_version"], statement["trust_domain"], statement["purpose"],
        statement["issuer"], statement["key_id"], statement["event_id"], [binding[key] for key in
        ("spec_id", "scope", "rule_digest", "source_digest", "subject_digest", "context_digest")],
        statement["issued_at"], statement["expires_at"], statement["outcome"],
        statement["previous_event"], statement["evidence_digest"]])


def finish_process_capture(action, prepared, completed, started_at_ms, completed_at_ms):
    """Sign only exact returned child bytes after current bindings are rechecked."""
    config = action.native_gate_check.process_observer
    policy, private = _configuration(config, signing=True)
    basis = _basis(action)
    if prepared["basis"] != basis or prepared["policy"] != policy:
        raise ValueError("PROCESS_OBSERVATION_BINDING_CHANGED")
    record = {"schema_version": PROCESS_PROFILE, **basis, "stdout_hex": completed.stdout.hex(),
        "stdout_sha256": _digest(completed.stdout), "stderr_hex": completed.stderr.hex(),
        "stderr_sha256": _digest(completed.stderr), "exit_code": completed.returncode,
        "direct_child_completed": True, "shell": False, "started_at_ms": started_at_ms,
        "completed_at_ms": completed_at_ms, "authority_effect": "None"}
    raw = _bytes(record)
    subject = _digest(raw)
    evidence = _bytes({"schema_version": "core.eis.observed-evidence.v1", "observer_id": config.issuer,
        "run_id": action.run_id, "subject_digest": subject, "source_digest": config.observer_source_digest,
        "outcome": "PROCESS_EXECUTION_OBSERVED"})
    now = int(time.time())
    from importlib.resources import files

    owner = files("pfp").joinpath("infrastructure/yaml/gates")
    observations = {}
    for gate, filename in PROCESS_GATES.items():
        binding = {"spec_id": gate, "scope": PROCESS_PROFILE, "rule_digest": _digest(owner.joinpath(filename).read_bytes()),
            "source_digest": record["source_digest"], "subject_digest": subject, "context_digest": _context(record)}
        statement = {"schema_version": "core.eis.signed-attestation.v1", "trust_domain": policy["trust_domain"],
            "purpose": "observation", "issuer": config.issuer, "key_id": config.key_id,
            "event_id": action.run_id + ":" + action.action_id + ":" + gate, "binding": binding,
            "issued_at": now, "expires_at": now + config.lifetime_seconds, "outcome": "PROCESS_EXECUTION_OBSERVED",
            "previous_event": None, "evidence_digest": _digest(evidence)}
        statement["signature_hex"] = private.sign(_signing_bytes(statement)).hex()
        observations[gate] = {"record_hex": raw.hex(), "signed": {
            "attestation": statement, "evidence_hex": evidence.hex()}}
    return observations


def _process_gate_payload(action, gate_id, *, now, replay):
    config = action.native_gate_check.process_observer
    policy, _ = _configuration(config, replay=replay)
    basis = _scope(action) if replay else _basis(action)
    for item in reversed(action.native_host_observations):
        check = item.get("check")
        if check is None:
            captured = item.get("process_capture", {})
            expected = {**_scope(action), "action_id": item["action_id"]}
            if captured and all(captured.get(key) == value for key, value in expected.items()):
                break  # The latest actual attempt is unavailable, not prior PASS.
            continue
        if (check["initial_task_id"] != action.initial_task_id or check["source_id"] != action.check_source_id
                or check["checker_id"] != action.checker_id or check["command"] != list(action.check_command)
                or check["artifacts"] != action.artifacts):
            continue
        observation = item.get("process_observations", {}).get(gate_id)
        if observation is None:
            break
        record = decode_native_json(bytes.fromhex(observation["record_hex"]))
        expected = {**basis, "action_id": item["action_id"]}
        if replay:
            # This is original signed execution, not current executable/code.
            # Independent current task/checker/artifact scope above still binds.
            expected.update({key: record[key] for key in ("argv", "executable_path", "executable_sha256")})
            expected["observer_source_digest"] = config.observer_source_digest
        if any(record.get(key) != value for key, value in expected.items()):
            raise ValueError("PROCESS_OBSERVATION_BINDING_MISMATCH")
        if (record["exit_code"] != check["exit_status"]
                or hashlib.sha256(bytes.fromhex(record["stdout_hex"]) + b"\n--- stderr ---\n" +
                    bytes.fromhex(record["stderr_hex"])).hexdigest() != check["output_sha256"]):
            raise ValueError("PROCESS_OBSERVATION_CHECK_MISMATCH")
        return {"process_profile": PROCESS_PROFILE, "process_observation": observation,
            "process_trust_policy": policy, "process_expected": expected, "now": now}
    return {"process_profile": PROCESS_PROFILE, "process_trust_policy": policy, "now": now}


def process_gate_payload(action, gate_id, *, now):
    """Fresh projection requires the current owning observer and executable bytes."""
    return _process_gate_payload(action, gate_id, now=now, replay=False)


def replay_process_gate_payload(action, gate_id, *, now):
    """Read-only historical projection; never dispatch, resign, or read a private key."""
    return _process_gate_payload(action, gate_id, now=now, replay=True)

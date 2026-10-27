"""Opt-in authenticated observation of the selected artifact's actual Lean check.

The signature authenticates the configured observer's captured execution. It
does not grant task, publication, sandbox or unrestricted mathematical authority.
"""
from __future__ import annotations

import hashlib
import time
from importlib.resources import files
from pathlib import Path

from ..domain.native_gate_check import KernelCheckConfig, decode_native_json
from .teamwork_process_observation import _bytes, _configuration, _digest, _signing_bytes

KERNEL_PROFILE = "adversary.host-lean.v1"
MASTER = "PFP-07-MANUSCRIPT-TRUTH"
CONTEXT_FIELDS = ("run_id", "task_id", "action_id", "source_digest", "candidate_sha256",
    "proof_artifact_path", "proof_artifact_sha256", "checker_id", "required_declarations",
    "axiom_policy", "toolchain_pin", "lake_binary_path", "lake_binary_sha256")


def observer_source_digest():
    directory = Path(__file__).parent
    sources = [("adversary/" + name, directory / name) for name in
        ("teamwork_kernel_observation.py", "teamwork_process_observation.py",
         "teamwork_intelligence_host.py", "lake_candidate_checker.py")]
    sources.append(("pfp/lake_sandbox_adapter.py", files("pfp").joinpath(
        "infrastructure/adapters/lake_sandbox_adapter.py")))
    return _digest(_bytes([[name, _digest(path.read_bytes())] for name, path in sources]))


def _configuration_for(config, *, signing=False, replay=False):
    return _configuration(config.observer, signing=signing, replay=replay,
        scope=KERNEL_PROFILE, source_digest_fn=observer_source_digest)


def _lake(config):
    from .teamwork_native_gates import _safe_native_path

    path = _safe_native_path(config.lake_binary_path)
    if (not path.is_file() or path.stat().st_nlink != 1
            or hashlib.sha256(path.read_bytes()).hexdigest() != config.lake_binary_sha256):
        raise ValueError("KERNEL_LAKE_BINARY_CHANGED")
    return path


def bind_kernel_check_config(path):
    from .teamwork_native_gates import _safe_native_path

    config = KernelCheckConfig.model_validate(decode_native_json(Path(path).read_bytes()))
    config = config.model_copy(update={
        "proof_artifact_path": str(_safe_native_path(config.proof_artifact_path)),
        "lake_binary_path": str(_safe_native_path(config.lake_binary_path)),
        "observer": config.observer.model_copy(update={
            "policy_path": str(_safe_native_path(config.observer.policy_path)),
            "private_key_path": str(_safe_native_path(config.observer.private_key_path))})})
    _lake(config)
    _configuration_for(config, signing=True)
    return config


def _context(action):
    config = getattr(action.native_gate_check, "kernel_check", None)
    if config is None:
        raise ValueError("KERNEL_CHECK_REQUIRED")
    KernelCheckConfig.model_validate(config.model_dump(mode="json"))
    path = config.proof_artifact_path
    if path not in action.artifacts:
        raise ValueError("KERNEL_PROOF_ARTIFACT_UNBOUND")
    if not action.run_id or not action.initial_task_id or not action.check_source_id:
        raise ValueError("KERNEL_TASK_BINDING_REQUIRED")
    source = action.check_source_id
    return {"run_id": action.run_id, "task_id": action.initial_task_id, "action_id": action.action_id,
        "source_digest": source if source.startswith("sha256:") else "sha256:" + source,
        "candidate_sha256": _digest(action.candidate.encode("utf-8")),
        "proof_artifact_path": path,
        "proof_artifact_sha256": "sha256:" + action.artifacts[path].removeprefix("sha256:"),
        "checker_id": action.checker_id,
        "required_declarations": [list(pair) for pair in config.required_declarations],
        "axiom_policy": list(config.axiom_policy), "toolchain_pin": config.toolchain_pin,
        "lake_binary_path": config.lake_binary_path,
        "lake_binary_sha256": "sha256:" + config.lake_binary_sha256}


def _proof(action, context):
    from .teamwork_intelligence_host import _current_artifacts, _current_checker, _current_source
    from .teamwork_native_gates import _safe_native_path

    _current_source(action)
    _current_checker(action)
    _current_artifacts(action.artifacts)
    path = _safe_native_path(context["proof_artifact_path"])
    if path.stat().st_nlink != 1:
        raise ValueError("KERNEL_PROOF_HARDLINK_REFUSED")
    raw = path.read_bytes()
    if _digest(raw) != context["proof_artifact_sha256"]:
        raise ValueError("KERNEL_PROOF_CHANGED")
    return raw


def capture_kernel_observation(action, *, timeout):
    """Preserve the actual receipt or failure; never substitute another proof."""
    from .lake_candidate_checker import LakeLiveCandidateChecker

    context = None
    receipt = None
    try:
        config = action.native_gate_check.kernel_check
        context = _context(action)
        policy, _ = _configuration_for(config, signing=True)
        _lake(config)
        proof = _proof(action, context)
        checked = LakeLiveCandidateChecker(lake_binary=config.lake_binary_path,
            toolchain_pin=config.toolchain_pin, timeout_seconds=max(1, int(timeout)),
            required_declarations=tuple(tuple(pair) for pair in config.required_declarations),
            axiom_policy=tuple(config.axiom_policy)).check_candidate(
                run_key=action.run_id, objective=action.objective,
                candidate_id=action.action_id, candidate_bytes=proof, carrier_context=None)
        if checked.is_err:
            refusal = checked.unwrap_err()
            retained = dict(refusal.details or ()).get("lake_receipt_hex")
            return {"kernel_capture": {"context": context, "failure_code": refusal.code,
                "reason": refusal.message, "lake_receipt_hex": retained,
                "authority_effect": "None"}}
        result = checked.unwrap()
        receipt = result.checker_receipt_bytes
        if not receipt:
            raise ValueError("KERNEL_RECEIPT_UNAVAILABLE")
        if result.candidate_content_sha256 != context["proof_artifact_sha256"]:
            raise ValueError("KERNEL_RECEIPT_CANDIDATE_MISMATCH")
        current_policy, private = _configuration_for(config, signing=True)
        _lake(config)
        if (_context(action) != context or _proof(action, context) != proof or current_policy != policy):
            raise ValueError("KERNEL_OBSERVATION_BINDING_CHANGED")
        record = {"schema_version": KERNEL_PROFILE, "context": context,
            "lake_receipt_hex": receipt.hex(), "observer_source_digest": config.observer.observer_source_digest,
            "authority_effect": "None"}
        raw = _bytes(record)
        subject = _digest(raw)
        observer = config.observer
        evidence = _bytes({"schema_version": "core.eis.observed-evidence.v1", "observer_id": observer.issuer,
            "run_id": action.run_id, "subject_digest": subject, "source_digest": observer.observer_source_digest,
            "outcome": "KERNEL_VERIFICATION_OBSERVED"})
        rule = files("pfp").joinpath("infrastructure/yaml/gates/07_manuscript_truth_manuscript_truth.yaml")
        now = int(time.time())
        statement = {"schema_version": "core.eis.signed-attestation.v1", "trust_domain": policy["trust_domain"],
            "purpose": "observation", "issuer": observer.issuer, "key_id": observer.key_id,
            "event_id": action.run_id + ":" + action.action_id + ":" + MASTER,
            "binding": {"spec_id": MASTER, "scope": KERNEL_PROFILE, "rule_digest": _digest(rule.read_bytes()),
                "source_digest": context["source_digest"], "subject_digest": subject,
                "context_digest": _digest(_bytes([context[key] for key in CONTEXT_FIELDS]))},
            "issued_at": now, "expires_at": now + observer.lifetime_seconds,
            "outcome": "KERNEL_VERIFICATION_OBSERVED", "previous_event": None,
            "evidence_digest": _digest(evidence)}
        statement["signature_hex"] = private.sign(_signing_bytes(statement)).hex()
        return {"kernel_observations": {MASTER: {"record_hex": raw.hex(), "signed": {
            "attestation": statement, "evidence_hex": evidence.hex()}}}}
    except (OSError, ValueError, TypeError, RuntimeError, ImportError) as exc:
        return {"kernel_capture": {"context": context, "failure_code": "KERNEL_OBSERVATION_UNAVAILABLE",
            "reason": str(exc), "lake_receipt_hex": receipt.hex() if receipt is not None else None,
            "authority_effect": "None"}}


def kernel_gate_payload(action, *, now, replay=False):
    config = action.native_gate_check.kernel_check
    policy, _ = _configuration_for(config, replay=replay)
    base = {"kernel_profile": KERNEL_PROFILE, "kernel_trust_policy": policy, "now": now}
    try:
        context = _context(action)
    except ValueError as exc:
        if str(exc) == "KERNEL_PROOF_ARTIFACT_UNBOUND":
            return base  # Before build, no proof has been admitted as an artifact.
        raise
    if not replay:
        _lake(config)
        _proof(action, context)
    for item in reversed(action.native_host_observations):
        check = item.get("check")
        captured = item.get("kernel_capture")
        expected = {**context, "action_id": item["action_id"]}
        if check is None:
            if captured is not None and captured.get("context") in (None, expected):
                break
            continue
        if (check["initial_task_id"] != action.initial_task_id or check["source_id"] != action.check_source_id
                or check["checker_id"] != action.checker_id or check["command"] != list(action.check_command)
                or check["artifacts"] != action.artifacts):
            continue
        observation = item.get("kernel_observations", {}).get(MASTER)
        if observation is None:
            break
        record = decode_native_json(bytes.fromhex(observation["record_hex"]))
        if record["context"] != expected or record["observer_source_digest"] != config.observer.observer_source_digest:
            raise ValueError("KERNEL_OBSERVATION_BINDING_MISMATCH")
        return {**base, "kernel_observation": observation, "kernel_expected": expected}
    return base

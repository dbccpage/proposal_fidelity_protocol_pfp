"""Read back host artifacts separately from PFP model proposals."""

from __future__ import annotations

from omega_engine_woland.infrastructure.native import DefaultNativeOperationPort

from ..use_cases.teamwork import TeamworkAction as TeamworkAction
from ..use_cases.teamwork import TeamworkObservation as TeamworkObservation
from ..use_cases.teamwork_pfp import check_teamwork_reply as check_teamwork_reply
from ..use_cases.teamwork_pfp import prepare_teamwork_turn as prepare_teamwork_turn


def attach_teamwork_host_artifacts(action, checked, host_observation=None):
    """Read a separate host artifact manifest without trusting its model verdict.

    Only actual file paths/digests are taken from the host observation. Its text,
    findings, checker result and arbitrary metadata never replace checked bytes.
    File readback establishes current bytes, not who edited them or admission.
    """
    if checked.action_id != action.action_id:
        raise ValueError("ACTION_MISMATCH: checked reply must bind the pending action")
    from ..use_cases.checked_ddc_reuse import validate_checked_reuse_dispatch

    validate_checked_reuse_dispatch(action, native_support=DefaultNativeOperationPort())
    from .teamwork_intelligence_host import _current_artifacts, validate_ddc_context

    learning_paths = checked.metadata.get("changed_paths", []) if action.kind == "learn" else []
    applies_learning = action.kind == "learn" and bool(learning_paths)
    if action.kind == "learn" and action.workflow_version in ("omega.woland.teamwork.v3", "omega.woland.teamwork.v4"):
        validate_ddc_context(action, changed_paths=learning_paths)
    if action.kind not in ("build", "repair") and not applies_learning:
        _current_artifacts(action.artifacts)
    if checked.blocked:
        return checked
    required_paths = learning_paths
    required = bool(required_paths) or (
        (action.intelligence is not None or action.workflow_version in ("omega.woland.teamwork.v3", "omega.woland.teamwork.v4"))
        and action.kind in ("build", "repair"))
    if host_observation is None:
        if not required:
            return checked
        return checked.model_copy(update={"blocked": True,
            "summary": "Checked proposal requires a separate host artifact readback.",
            "metadata": {**checked.metadata, "failure_code": "HOST_ARTIFACTS_REQUIRED"}})
    if host_observation.action_id != action.action_id:
        raise ValueError("ACTION_MISMATCH: host artifacts must bind the pending action")
    if action.kind not in ("build", "repair", "learn"):
        raise ValueError("HOST_ARTIFACTS_NOT_APPLICABLE: this turn does not apply file changes")
    if host_observation.blocked or not host_observation.artifacts:
        raise ValueError("HOST_ARTIFACTS_REQUIRED: supply a successful host file observation")
    if any(path not in host_observation.artifacts for path in required_paths):
        raise ValueError("APPLICATION_REQUIRED: bind every reported learning output")
    if not action.artifacts.keys() <= host_observation.artifacts.keys():
        raise ValueError("APPLICATION_REQUIRED: retain every original artifact")
    if applies_learning and any(
        host_observation.artifacts[path].removeprefix("sha256:") != digest.removeprefix("sha256:")
        and path not in required_paths
        for path, digest in action.artifacts.items()
    ):
        raise ValueError("UNDECLARED_ARTIFACT_CHANGE: learning must name each changed file")
    _current_artifacts(host_observation.artifacts)
    validate_checked_reuse_dispatch(action, native_support=DefaultNativeOperationPort())
    return checked.model_copy(update={"artifacts": dict(host_observation.artifacts),
        "metadata": {**checked.metadata, "host_artifacts_checked": True}})

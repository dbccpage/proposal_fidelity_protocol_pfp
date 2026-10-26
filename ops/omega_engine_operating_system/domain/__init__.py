"""Pure domain contracts for the OEOS governed task lifecycle."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .arena import AdmittedPolicyV1, CompetitorSpecV1, CorpusManifestV1, RoutingPolicyProposalV1, ScorecardV1, TrialReceiptV1
    from .experience import ExperienceRecordV1
    from .receipt import HarnessRunReceiptV1
    from .route import RoutePlanV1, SkillUseEventV1, SkillUsePhaseV1, verify_skill_lifecycle_chain
    from .task import ALLOWED_TRANSITIONS, TERMINAL_STATES, ActionLimitsV1, CapabilityFacetV1, CapabilityRecordV1, CapabilitySnapshotV1, EncryptedArtifactRefV1, FacetStateV1, HarnessEventV1, TaskAggregateV1, TaskEnvelopeV1, TaskInvariantError, TaskStateV1, canonical_json, digest_payload, require_identifier, require_sha256_digest, utc_now, verify_event_chain

__all__ = ['ALLOWED_TRANSITIONS', 'TERMINAL_STATES', 'ActionLimitsV1', 'AdmittedPolicyV1', 'CapabilityFacetV1', 'CapabilityRecordV1', 'CapabilitySnapshotV1', 'CompetitorSpecV1', 'CorpusManifestV1', 'EncryptedArtifactRefV1', 'ExperienceRecordV1', 'FacetStateV1', 'HarnessEventV1', 'HarnessRunReceiptV1', 'RoutePlanV1', 'RoutingPolicyProposalV1', 'ScorecardV1', 'SkillUseEventV1', 'SkillUsePhaseV1', 'TaskAggregateV1', 'TaskEnvelopeV1', 'TaskInvariantError', 'TaskStateV1', 'TrialReceiptV1', 'canonical_json', 'digest_payload', 'require_identifier', 'require_sha256_digest', 'utc_now', 'verify_event_chain', 'verify_skill_lifecycle_chain']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'AdmittedPolicyV1': ('.arena', 'AdmittedPolicyV1'),
    'CompetitorSpecV1': ('.arena', 'CompetitorSpecV1'),
    'CorpusManifestV1': ('.arena', 'CorpusManifestV1'),
    'RoutingPolicyProposalV1': ('.arena', 'RoutingPolicyProposalV1'),
    'ScorecardV1': ('.arena', 'ScorecardV1'),
    'TrialReceiptV1': ('.arena', 'TrialReceiptV1'),
    'ExperienceRecordV1': ('.experience', 'ExperienceRecordV1'),
    'HarnessRunReceiptV1': ('.receipt', 'HarnessRunReceiptV1'),
    'RoutePlanV1': ('.route', 'RoutePlanV1'),
    'SkillUseEventV1': ('.route', 'SkillUseEventV1'),
    'SkillUsePhaseV1': ('.route', 'SkillUsePhaseV1'),
    'verify_skill_lifecycle_chain': ('.route', 'verify_skill_lifecycle_chain'),
    'ALLOWED_TRANSITIONS': ('.task', 'ALLOWED_TRANSITIONS'),
    'TERMINAL_STATES': ('.task', 'TERMINAL_STATES'),
    'ActionLimitsV1': ('.task', 'ActionLimitsV1'),
    'CapabilityFacetV1': ('.task', 'CapabilityFacetV1'),
    'CapabilityRecordV1': ('.task', 'CapabilityRecordV1'),
    'CapabilitySnapshotV1': ('.task', 'CapabilitySnapshotV1'),
    'EncryptedArtifactRefV1': ('.task', 'EncryptedArtifactRefV1'),
    'FacetStateV1': ('.task', 'FacetStateV1'),
    'HarnessEventV1': ('.task', 'HarnessEventV1'),
    'TaskAggregateV1': ('.task', 'TaskAggregateV1'),
    'TaskEnvelopeV1': ('.task', 'TaskEnvelopeV1'),
    'TaskInvariantError': ('.task', 'TaskInvariantError'),
    'TaskStateV1': ('.task', 'TaskStateV1'),
    'canonical_json': ('.task', 'canonical_json'),
    'digest_payload': ('.task', 'digest_payload'),
    'require_identifier': ('.task', 'require_identifier'),
    'require_sha256_digest': ('.task', 'require_sha256_digest'),
    'utc_now': ('.task', 'utc_now'),
    'verify_event_chain': ('.task', 'verify_event_chain'),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_IMPORTS.get(name)
    if target is not None:
        mod_name, attr_name = target
        mod = importlib.import_module(mod_name, __name__)
        val = getattr(mod, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any


@dataclass(frozen=True, slots=True)
class EpicIntegrationObligation:
    epic_id: int
    name: str
    status: str  # AUTOMATED | NOT_YET_IMPLEMENTED
    bound_test_file: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, EpicIntegrationObligation)
        return (
            self.epic_id == other.epic_id
            and self.name == other.name
            and self.status == other.status
            and self.bound_test_file == other.bound_test_file
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "epic_id": self.epic_id,
            "name": self.name,
            "status": self.status,
            "bound_test_file": self.bound_test_file,
        }


@dataclass(frozen=True, slots=True)
class EpicIntegrationMapRegistry:
    obligations: tuple[EpicIntegrationObligation, ...]
    registry_digest: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, EpicIntegrationMapRegistry)
        return self.obligations == other.obligations and self.registry_digest == other.registry_digest

    def to_dict(self) -> dict[str, Any]:
        return {
            "obligations": [o.to_dict() for o in self.obligations],
            "registry_digest": self.registry_digest,
            "total_count": len(self.obligations),
        }

    @classmethod
    def create_canonical_mapping_67_76(cls) -> EpicIntegrationMapRegistry:
        mapping_data = [
            EpicIntegrationObligation(67, "Leased path mutual exclusion", "AUTOMATED", "test_swarm_path_lease_checker.py"),
            EpicIntegrationObligation(68, "Candidate binding pre-flight", "AUTOMATED", "test_candidate_binding.py"),
            EpicIntegrationObligation(69, "Authority parser constructor fences", "AUTOMATED", "test_authority_parser_contracts.py"),
            EpicIntegrationObligation(70, "Non-force disposal & worktree release", "AUTOMATED", "test_nonforce_disposal.py"),
            EpicIntegrationObligation(71, "Committed-byte reader purity", "AUTOMATED", "test_git_object_address_hygiene.py"),
            EpicIntegrationObligation(72, "Exact-blob conflict reconciliation", "AUTOMATED", "test_exact_blob_reconciliation.py"),
            EpicIntegrationObligation(73, "Evidence freshness invalidation on rebind", "AUTOMATED", "test_evidence_freshness_rebind.py"),
            EpicIntegrationObligation(74, "Universal transport receipt validation", "AUTOMATED", "test_universal_transport_receipt.py"),
            EpicIntegrationObligation(75, "Serial landing mutex & CAS license", "AUTOMATED", "test_cas_land_license.py"),
            EpicIntegrationObligation(76, "Conflict graph admission under N ceiling", "AUTOMATED", "test_conflict_graph_admission.py"),
        ]
        sorted_obs = tuple(sorted(mapping_data, key=lambda o: o.epic_id))
        raw_payload = json.dumps([o.to_dict() for o in sorted_obs], sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()
        return cls(obligations=sorted_obs, registry_digest=digest)

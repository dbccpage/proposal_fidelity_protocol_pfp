"""OESOS Evidence Bundle Adapter."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from ...domain.shared_kernel import AuthorityEffect
from ...domain.entities import ProcessEvent


class OesosEvidenceAdapter:
    """Creates immutable, content-addressed process receipts and event chains."""

    def build_evidence_receipt(
        self,
        event_chain: list[ProcessEvent],
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        events_data = [
            {
                "event_id": e.event_id,
                "event_type": e.event_type,
                "step": e.step,
                "payload_digest": e.payload_digest,
                "previous_digest": e.previous_digest,
            }
            for e in event_chain
        ]
        chain_bytes = json.dumps(events_data, sort_keys=True).encode("utf-8")
        chain_sha256 = hashlib.sha256(chain_bytes).hexdigest()

        return {
            "evidence_receipt_id": f"ev_{chain_sha256[:16]}",
            "chain_sha256": chain_sha256,
            "events_count": len(event_chain),
            "events": events_data,
            "metadata": dict(metadata or {}),
            "authority_effect": AuthorityEffect.NONE.value,
        }

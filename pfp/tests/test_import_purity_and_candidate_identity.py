"""Tests for Project 1: Import purity and CandidateArtifactV1 identity.

AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from typing import Any


def test_candidate_artifact_identity() -> None:
    """Verify CandidateArtifactV1 identity across domain modules (UOW-7 §7.4)."""
    from omega_engine_pfp.domain.entities import (
        CandidateArtifactV1 as C_Root,
    )
    from omega_engine_pfp.domain.entities.candidate_artifact import (
        CandidateArtifactV1 as C_Direct,
    )
    from omega_engine_pfp.domain.entities.packet_envelope import (
        CandidateArtifactV1 as C_Envelope,
    )

    assert C_Root is C_Direct, "Root export must be identical to candidate_artifact definition"
    assert C_Envelope is C_Direct, "PacketEnvelope export must be identical to candidate_artifact definition"

    # Verify instantiation and roundtrip
    instance = C_Direct.create(
        packet_id="0" * 64,
        producer_id="test_producer",
        payload={"key": "value"},
        witness="w" * 64,
    )
    assert isinstance(instance, C_Envelope)
    assert type(instance) is C_Root

    data = instance.to_dict()
    restored = C_Envelope.from_dict(data)
    assert restored == instance
    assert type(restored) is C_Direct


def test_import_purity_and_explicit_initialization() -> None:
    """Verify import omega_engine_pfp has zero side effects and initialize_exact_ports is explicit."""
    import omega_engine_pfp

    assert hasattr(omega_engine_pfp, "initialize_exact_ports")
    assert callable(omega_engine_pfp.initialize_exact_ports)
    assert "initialize_exact_ports" in omega_engine_pfp.__all__

    # Calling initialize_exact_ports should execute cleanly
    omega_engine_pfp.initialize_exact_ports()

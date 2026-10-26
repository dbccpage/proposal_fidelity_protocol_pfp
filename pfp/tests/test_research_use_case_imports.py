"""The research use cases resolve the packet envelope type they name.

Counterexample from the study: ``use_cases/research.py`` used
``PacketEnvelopeV2`` in three functions without importing it, so every call
raised ``NameError`` before any input was read. A malformed envelope must be
refused by the domain's own validation instead.
AuthorityEffect: None.
"""

from __future__ import annotations

import pytest

from omega_engine_pfp.domain.entities.packet_envelope import PacketEnvelopeV2
from omega_engine_pfp.domain.exceptions import CanonicalizationError
from omega_engine_pfp.use_cases import research


def test_the_envelope_name_is_the_domain_envelope() -> None:
    assert research.PacketEnvelopeV2 is PacketEnvelopeV2


@pytest.mark.parametrize(
    "call",
    [
        lambda: research.parse_research_claim_envelope({}),
        lambda: research.build_source_intake_bundle({}, "."),
    ],
)
def test_a_malformed_envelope_is_refused_not_a_name_error(call) -> None:
    with pytest.raises(CanonicalizationError):
        call()

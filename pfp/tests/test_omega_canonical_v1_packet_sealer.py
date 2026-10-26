"""The packet sealer is omega-canonical-v1. RFC 8785 is a different function."""

from __future__ import annotations

import hashlib

from omega_engine_pfp.domain.packet_codec import PacketCodec
from omega_engine_pfp.domain.shared_kernel.canonical import (
    CANONICAL_MARKER,
    canonical_json,
)
from omega_engine_pfp.infrastructure.serialization.rfc8785 import rfc8785_canonicalize


def test_packet_sealer_marks_mapping_and_rfc8785_name_differs() -> None:
    mapping = {"zebra": 1, "apple": 2}
    sealed = PacketCodec.seal(mapping, "demo")
    payload = canonical_json(sealed["payload"])

    assert payload.startswith(f'["{CANONICAL_MARKER}"')
    assert CANONICAL_MARKER in payload
    assert (
        sealed["payload_sha256"]
        == hashlib.sha256(payload.encode("utf-8")).hexdigest()
    )

    encoded = rfc8785_canonicalize(mapping)
    assert encoded.format_name != CANONICAL_MARKER
    assert encoded.format_name == "rfc8785"
    assert not encoded.text.startswith(f'["{CANONICAL_MARKER}"')

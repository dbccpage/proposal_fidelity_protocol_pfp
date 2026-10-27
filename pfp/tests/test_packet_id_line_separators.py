"""PacketEnvelopeV2.packet_id uses the same raw U+2028 and U+2029 text as Rust."""

from __future__ import annotations

from pfp.domain.entities.packet_envelope import PacketEnvelopeV2
from pfp.domain.shared_kernel.canonical import (
    _serde_json_text,
    canonical_json,
)

# Same vector as host_contract::packet_id_matches_python_for_line_and_paragraph_separators.
# serde_json leaves U+2028 and U+2029 raw. The framed digest is of that text.
_SEPARATOR_PACKET_ID = "11aa1b89aa513177c1aaa81cca3aedeb5e4ae9dcfdbf4c043e7e58b68cd43dc6"


def test_packet_id_uses_raw_line_and_paragraph_separators() -> None:
    raw_text = '["core-canonical-v1","string","\u2028\u2029"]'
    assert canonical_json("\u2028\u2029") == raw_text
    assert "\\u2028" not in raw_text and "\\u2029" not in raw_text
    assert (
        _serde_json_text('["core-canonical-v1","string","\\u2028\\u2029"]')
        == raw_text
    )
    assert (
        _serde_json_text('["core-canonical-v1","string","\\\\u2028\\\\u2029"]')
        == '["core-canonical-v1","string","\\\\u2028\\\\u2029"]'
    )
    assert canonical_json("\\u2028") == '["core-canonical-v1","string","\\\\u2028"]'
    assert canonical_json("\u0000") == '["core-canonical-v1","string","\\u0000"]'

    packet = PacketEnvelopeV2(
        task_id="separator-task",
        packet_family="separator-family",
        carrier_id="separator-carrier",
        initial_state_hash="1" * 64,
        payload="\u2028\u2029",
        constraints=("keep-raw",),
        protected_boundaries=("boundary\u2028",),
    )
    assert len(packet.packet_id) == 64
    assert packet.packet_id == _SEPARATOR_PACKET_ID
    identity = canonical_json(packet.identity_fields())
    assert "\u2028" in identity and "\u2029" in identity
    assert "\\u2028" not in identity and "\\u2029" not in identity

"""The provider prompt and reply byte ceilings.

Ported from an internal test suite. A measured request size that bounds nothing
is the defect these tests pin: the combined prompt must be refused above its
ceiling, in bytes, with bounded work and a receipt that leaks no payload text.
The gateway-level checks (no budget charged, no provider called) were not ported;
here the same guards are exercised directly. AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from array import array

import pytest

from replyguard.limits import (
    MAX_PROVIDER_PROMPT_BYTES,
    MAX_PROVIDER_REPLY_BYTES,
    REFUSAL_PROVIDER_PROMPT_TOO_LARGE,
    REFUSAL_PROVIDER_REPLY_TOO_LARGE,
    REFUSAL_TEXT_INVALID_UTF8,
)
from replyguard.provider_types import (
    BudgetExceeded,
    CandidateRequest,
    ChatMessage,
    PromptInvalidUtf8,
    PromptTooLarge,
    ReplyTooLarge,
    check_reply_bytes,
)
from replyguard.wire import decode_reply

HALF = MAX_PROVIDER_PROMPT_BYTES // 2


def _raw_reply(content: str = "ok", **extra) -> bytes:
    payload = {
        "choices": [{"message": {"content": content}}],
        "model": "fixture-model",
        "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        **extra,
    }
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def _raw_reply_at_size(size: int) -> bytes:
    body = _raw_reply()
    assert len(body) < size
    # JSON admits leading whitespace. A content-only ceiling sees two bytes
    # while the wire body reaches the requested size.
    return b" " * (size - len(body)) + body


class TestTheCombinedPromptIsWhatIsBounded:
    def test_a_prompt_at_the_ceiling_is_admitted(self) -> None:
        CandidateRequest(system="s" * HALF, user="u" * HALF).check_payload_ceiling()

    def test_one_byte_over_is_refused(self) -> None:
        request = CandidateRequest(system="s" * HALF, user="u" * (HALF + 1))
        with pytest.raises(PromptTooLarge) as caught:
            request.check_payload_ceiling()
        assert caught.value.receipt.refusal_code == REFUSAL_PROVIDER_PROMPT_TOO_LARGE

    def test_two_admissible_halves_are_not_an_admissible_whole(self) -> None:
        """Each field alone is under the ceiling; together they are not."""
        request = CandidateRequest(
            system="s" * (MAX_PROVIDER_PROMPT_BYTES - 10),
            user="u" * (MAX_PROVIDER_PROMPT_BYTES - 10),
        )
        with pytest.raises(PromptTooLarge):
            request.check_payload_ceiling()

    def test_chat_messages_are_bounded_as_one_combined_prompt(self) -> None:
        request = CandidateRequest(
            messages=(
                ChatMessage("system", "s" * HALF),
                ChatMessage("user", "u" * HALF),
            )
        )
        with pytest.raises(PromptTooLarge):
            request.check_payload_ceiling()

    def test_the_ceiling_counts_bytes_not_characters(self) -> None:
        value = "\U0001f4a3" * (MAX_PROVIDER_PROMPT_BYTES // 4 + 1)
        assert len(value) < MAX_PROVIDER_PROMPT_BYTES
        with pytest.raises(PromptTooLarge):
            CandidateRequest(system="", user=value).check_payload_ceiling()

    def test_refusing_does_not_encode_the_whole_payload(self) -> None:
        """``observed_bytes`` is capped at limit + 1, so a real size would mean a full walk."""
        request = CandidateRequest(system="", user="u" * 20_000_000)
        with pytest.raises(PromptTooLarge) as caught:
            request.check_payload_ceiling()
        assert caught.value.receipt.observed_bytes == MAX_PROVIDER_PROMPT_BYTES + 1
        assert caught.value.receipt.observed_truncated is True

    def test_no_payload_text_reaches_the_refusal(self) -> None:
        marker = "CANARY-PROMPT-SECRET"
        request = CandidateRequest(system=marker, user="u" * MAX_PROVIDER_PROMPT_BYTES)
        with pytest.raises(PromptTooLarge) as caught:
            request.check_payload_ceiling()
        assert marker not in str(caught.value)
        assert marker not in repr(caught.value.receipt.to_dict())

    def test_invalid_utf8_prompt_is_refused_with_its_own_code(self) -> None:
        with pytest.raises(PromptInvalidUtf8) as caught:
            CandidateRequest(system="safe", user="\ud800").check_payload_ceiling()
        assert caught.value.receipt.refusal_code == REFUSAL_TEXT_INVALID_UTF8

    def test_prompt_refusal_is_not_a_budget_refusal(self) -> None:
        # Shared terminals are not evidence that the intended guard fired.
        assert not issubclass(PromptTooLarge, BudgetExceeded)
        assert not issubclass(BudgetExceeded, PromptTooLarge)


class TestTheReplyCeiling:
    def test_typed_memoryview_is_measured_and_hashed_as_octets(self) -> None:
        words = array("I", [0]) * ((MAX_PROVIDER_REPLY_BYTES // 4) + 1)
        raw = memoryview(words)

        with pytest.raises(ReplyTooLarge) as caught:
            check_reply_bytes(raw)

        prefix = raw.cast("B")[: MAX_PROVIDER_REPLY_BYTES + 1]
        receipt = caught.value.receipt
        assert receipt.observed_bytes == MAX_PROVIDER_REPLY_BYTES + 1
        assert receipt.observed_prefix_sha256 == hashlib.sha256(prefix).hexdigest()

    def test_an_oversize_reply_is_refused(self) -> None:
        with pytest.raises(ReplyTooLarge) as caught:
            decode_reply(_raw_reply_at_size(MAX_PROVIDER_REPLY_BYTES + 1))
        assert caught.value.receipt.refusal_code == REFUSAL_PROVIDER_REPLY_TOO_LARGE

    def test_a_reply_at_the_ceiling_is_admitted(self) -> None:
        decoded = decode_reply(_raw_reply_at_size(MAX_PROVIDER_REPLY_BYTES))
        assert decoded["choices"][0]["message"]["content"] == "ok"

    def test_a_reply_one_byte_below_the_ceiling_is_admitted(self) -> None:
        decoded = decode_reply(_raw_reply_at_size(MAX_PROVIDER_REPLY_BYTES - 1))
        assert decoded["choices"][0]["message"]["content"] == "ok"

    def test_oversize_metadata_cannot_hide_behind_a_small_content_field(self) -> None:
        raw = _raw_reply("ok", metadata="m" * MAX_PROVIDER_REPLY_BYTES)
        with pytest.raises(ReplyTooLarge):
            decode_reply(raw)

    def test_a_predecoded_mapping_is_not_accepted_as_raw_provider_evidence(self) -> None:
        with pytest.raises(TypeError, match="exact response bytes"):
            decode_reply({"choices": []})  # type: ignore[arg-type]

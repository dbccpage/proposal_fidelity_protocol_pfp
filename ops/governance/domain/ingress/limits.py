"""Byte ceilings for hostile text reaching the engine, and the receipts refusing it.

The attack path named by the adversarial campaign is HTTP -> controller ->
domain -> adapter -> provider. A front end may hand that path an enormous string
shaped like a ZIP, a PDF, or an executable. This module holds the ceilings and
the refusal vocabulary; every boundary that enforces one imports it from here.

One source of truth is the point. Four boundaries each carrying their own
literal is the same failure that put a stale "67 uncontracted types" in the
threat model: a number maintained by hand in more than one place is a number
that will disagree with itself.

Three properties this module is built around, each of which has a test:

*Bytes, never characters.* A ceiling stated in bytes and enforced with `len(str)`
is off by up to a factor of four, in the attacker's favour. `pydantic`'s
``max_length`` counts characters, which is why no field below relies on it.

*Bounded work before the refusal.* Nothing here encodes, buffers, hashes, or
otherwise walks a whole oversize payload in order to discover that it is
oversize. A reader stops at ``limit + 1`` bytes and refuses from there.

*Bounded disclosure after it.* A receipt carries the limit, a bounded observed
count, and a digest over only the bytes actually observed. It never carries the
hostile text, and it never claims to digest what was not read.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Any

#: Complete JSON request body accepted from an HTTP client.
MAX_REQUEST_BODY_BYTES = 64 * 1024

#: Any single admitted free-text field (an objective, a prompt, a scene note).
#: Deliberately equal to `adversary.stage.domain.canonical.MAX_TEXT_BYTES`;
#: `test_ingress_limits` asserts the two stay equal, because this ceiling exists
#: to refuse *earlier* than that one, never to disagree with it.
MAX_ADMITTED_TEXT_BYTES = 16 * 1024

#: Combined provider system + user prompt, measured before dispatch or charge.
MAX_PROVIDER_PROMPT_BYTES = 64 * 1024

#: Provider reply. Larger than the others: a legitimate completion is big, and a
#: hostile or looping provider is the thing being bounded.
MAX_PROVIDER_REPLY_BYTES = 1024 * 1024

REFUSAL_REQUEST_TOO_LARGE = "SWARM_REQUEST_TOO_LARGE"
REFUSAL_TEXT_TOO_LARGE = "SWARM_TEXT_TOO_LARGE"
REFUSAL_PROVIDER_PROMPT_TOO_LARGE = "SWARM_PROVIDER_PROMPT_TOO_LARGE"
REFUSAL_PROVIDER_REPLY_TOO_LARGE = "SWARM_PROVIDER_REPLY_TOO_LARGE"
REFUSAL_CONTENT_ENCODING_UNSUPPORTED = "SWARM_CONTENT_ENCODING_UNSUPPORTED"
REFUSAL_TEXT_INVALID_UTF8 = "SWARM_TEXT_INVALID_UTF8"

#: Every code this module can emit. A refusal that is not in this set is a bug,
#: not a new category -- the campaign's rule is that a refusal names a *stable*
#: mechanism, and an ad-hoc string names nothing.
REFUSAL_CODES = frozenset(
    {
        REFUSAL_REQUEST_TOO_LARGE,
        REFUSAL_TEXT_TOO_LARGE,
        REFUSAL_PROVIDER_PROMPT_TOO_LARGE,
        REFUSAL_PROVIDER_REPLY_TOO_LARGE,
        REFUSAL_CONTENT_ENCODING_UNSUPPORTED,
        REFUSAL_TEXT_INVALID_UTF8,
    }
)

#: The only content encodings admitted. Everything else is refused *before*
#: decompression, which is the whole point: a decompression bomb is cheap to
#: send and expensive to expand, so the expansion must never begin.
ADMITTED_CONTENT_ENCODINGS = frozenset({"", "identity"})

#: Cap on a refusal response body, so an error path cannot itself be an
#: amplifier. The receipt below is far smaller than this; the bound is stated so
#: a caller assembling a response has a number to check against.
MAX_REFUSAL_BODY_BYTES = 4 * 1024


@dataclass(frozen=True, slots=True)
class OversizeReceipt:
    """What an ingress refusal is allowed to say.

    Note what is absent: the payload, any decoded prefix of it, a filename, a
    path, or an exact size. `observed_bytes` is bounded by ``limit + 1`` by
    construction, and `observed_truncated` says so out loud rather than letting
    a reader mistake it for the real length.
    """

    refusal_code: str
    limit_bytes: int
    observed_bytes: int
    observed_truncated: bool
    observed_prefix_sha256: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.refusal_code not in REFUSAL_CODES:
            raise ValueError(f"unregistered refusal code: {self.refusal_code!r}")
        if self.limit_bytes < 0 or self.observed_bytes < 0:
            raise ValueError("byte counts are non-negative")
        if self.observed_bytes > self.limit_bytes + 1:
            # The invariant that makes the digest honest. If this ever trips,
            # something read further than it was allowed to.
            raise ValueError(
                f"observed {self.observed_bytes} bytes against a limit of "
                f"{self.limit_bytes}; observation is bounded by limit + 1"
            )
        if self.authority_effect != "None":
            raise ValueError("an ingress refusal carries AuthorityEffect None")

    def to_dict(self) -> dict[str, Any]:
        return {
            "refusal_code": self.refusal_code,
            "limit_bytes": self.limit_bytes,
            "observed_bytes": self.observed_bytes,
            "observed_truncated": self.observed_truncated,
            "observed_prefix_sha256": self.observed_prefix_sha256,
            "authority_effect": self.authority_effect,
        }


class IngressRefusal(Exception):
    """Raised at a boundary that refused to admit oversize or unsupported input.

    Carries the receipt rather than a message built from the input. `str()` on
    this exception is safe to log: it names the mechanism and the numbers, and
    reflects nothing an attacker sent.
    """

    def __init__(self, receipt: OversizeReceipt) -> None:
        self.receipt = receipt
        super().__init__(
            f"{receipt.refusal_code}: observed "
            f"{'>= ' if receipt.observed_truncated else ''}"
            f"{receipt.observed_bytes} bytes against a limit of "
            f"{receipt.limit_bytes}"
        )


def _receipt(prefix: bytes, *, limit: int, code: str, truncated: bool) -> OversizeReceipt:
    return OversizeReceipt(
        refusal_code=code,
        limit_bytes=limit,
        observed_bytes=len(prefix),
        observed_truncated=truncated,
        observed_prefix_sha256=hashlib.sha256(prefix).hexdigest(),
    )


def bounded_utf8_prefix(value: str, limit: int) -> tuple[bytes, bool]:
    """The first ``limit + 1`` UTF-8 bytes of `value`, and whether it overflows.

    The slice is what keeps the work bounded. Every code point encodes to at
    least one UTF-8 byte, so ``value[: limit + 1]`` encodes to at least
    ``limit + 1`` bytes whenever the string has more than `limit` characters --
    which means slicing *that* encoding to ``limit + 1`` yields exactly the
    first ``limit + 1`` bytes of the full encoding, without ever producing the
    full encoding. At the 16 KiB text ceiling, even a string made entirely of
    four-byte code points costs at most about 64 KiB of encoding work to
    refuse; the rest of an arbitrarily large value is never visited.

    The returned bytes may end mid-sequence. That is correct and intended: this
    is a prefix of an octet stream being digested, not text being decoded.
    """
    candidate = value[: limit + 1]
    try:
        head = candidate.encode("utf-8")
    except UnicodeEncodeError as error:
        # A Python ``str`` can contain an unpaired surrogate even though such a
        # value cannot be represented by strict UTF-8.  Map that condition to
        # the same typed, non-reflecting refusal channel as every other ingress
        # failure.  Encoding only the valid prefix keeps both work and the
        # receipt's digest bounded; neither the surrogate nor later text is
        # copied into the exception.
        valid_prefix = candidate[: error.start].encode("utf-8")
        if len(valid_prefix) > limit:
            # The byte ceiling was crossed before the invalid code point was
            # reached, so size remains the first decisive refusal.
            return valid_prefix[: limit + 1], True
        valid_prefix = valid_prefix[: limit + 1]
        raise IngressRefusal(
            _receipt(
                valid_prefix,
                limit=limit,
                code=REFUSAL_TEXT_INVALID_UTF8,
                truncated=False,
            )
        ) from None
    if len(head) > limit:
        return head[: limit + 1], True
    return head, False


def check_text_bytes(value: str, *, limit: int, refusal_code: str) -> None:
    """Refuse a string whose UTF-8 encoding exceeds `limit` bytes.

    Raises `IngressRefusal`; returns None when the value is admissible.
    """
    prefix, overflows = bounded_utf8_prefix(value, limit)
    if overflows:
        raise IngressRefusal(
            _receipt(prefix, limit=limit, code=refusal_code, truncated=True)
        )


def check_content_encoding(
    header_value: str | None,
    *,
    refusal_code: str = REFUSAL_CONTENT_ENCODING_UNSUPPORTED,
) -> None:
    """Refuse any content encoding this service will not decode.

    Refusing before decompression is the requirement. `gzip` is not rejected
    because it is exotic -- it is rejected because accepting it means expanding
    an attacker-chosen ratio before any ceiling can be applied to the result.
    """
    normalized = (header_value or "").strip().lower()
    if normalized in ADMITTED_CONTENT_ENCODINGS:
        return
    raise IngressRefusal(
        OversizeReceipt(
            refusal_code=refusal_code,
            limit_bytes=0,
            observed_bytes=0,
            observed_truncated=False,
            # Digest of the empty observation: nothing was read, and the receipt
            # says exactly that rather than implying a body was inspected.
            observed_prefix_sha256=hashlib.sha256(b"").hexdigest(),
        )
    )


def read_bounded(
    chunks: Iterable[bytes], *, limit: int, refusal_code: str
) -> bytes:
    """Consume `chunks` until `limit` bytes, refusing at the first byte beyond.

    Stops pulling from the iterable the moment ``limit + 1`` bytes exist, so an
    endless or enormous stream is abandoned rather than drained. Byte counting
    is exact regardless of where chunk boundaries fall, including in the middle
    of a multibyte sequence -- which is why the ceiling is enforced here, on
    octets, and not after decoding to `str`.
    """
    seen = bytearray()
    ceiling = limit + 1
    iterator = iter(chunks)
    try:
        for chunk in iterator:
            remaining = ceiling - len(seen)
            if remaining > 0:
                seen += chunk[:remaining]
            if len(seen) > limit:
                raise IngressRefusal(
                    _receipt(
                        bytes(seen), limit=limit, code=refusal_code, truncated=True
                    )
                )
        return bytes(seen)
    finally:
        close = getattr(iterator, "close", None)
        if callable(close):
            close()


def bounded_reply_chunks(
    chunks: Iterable[bytes],
    *,
    limit: int = MAX_PROVIDER_REPLY_BYTES,
    refusal_code: str = REFUSAL_PROVIDER_REPLY_TOO_LARGE,
) -> Iterator[bytes]:
    """Stream a provider reply, aborting at ``limit + 1`` bytes.

    Yields as it goes so a caller need not hold the whole reply, and raises
    `IngressRefusal` on overflow. A provider that streams forever is cancelled
    by the raise propagating out of the generator, which closes the underlying
    iterable.

    The digest is accumulated incrementally and cut off at ``limit + 1`` bytes,
    so it is a true digest of the observed prefix without the prefix ever being
    buffered a second time. Digesting only the final chunk would have been
    cheaper and would have made `observed_prefix_sha256` name bytes it does not
    cover, which is precisely the dishonesty the receipt exists to avoid.
    """
    hasher = hashlib.sha256()
    ceiling = limit + 1
    total = 0
    iterator = iter(chunks)
    try:
        for chunk in iterator:
            room = ceiling - total
            if room > 0:
                hasher.update(chunk[:room])
            total += len(chunk)
            if total > limit:
                raise IngressRefusal(
                    OversizeReceipt(
                        refusal_code=refusal_code,
                        limit_bytes=limit,
                        observed_bytes=ceiling,
                        observed_truncated=True,
                        observed_prefix_sha256=hasher.hexdigest(),
                    )
                )
            yield chunk
    finally:
        close = getattr(iterator, "close", None)
        if callable(close):
            close()

"""Local-only HTTP policy and bounded reads through a supplied receive port.

No framework, filesystem, provider, or ambient I/O is used here. A loopback
peer is not an authenticated principal. A proxy which discards its forwarding
and origin evidence is indistinguishable from a local caller; do not publish
these internal surfaces through such a proxy. AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re

from .limits import (
    MAX_REQUEST_BODY_BYTES,
    REFUSAL_REQUEST_TOO_LARGE,
    IngressRefusal,
    OversizeReceipt,
    check_content_encoding,
)

_LOCAL_PEERS = frozenset({"127.0.0.1", "::1", "::ffff:127.0.0.1"})
_LOCAL_HOST = re.compile(r"(?:localhost|127\.0\.0\.1|\[::1\])(?::([1-9][0-9]{0,4}))?\Z")
_BOUNDARY_STATUSES = {
    "LOCAL_OPERATOR_REQUIRED": 403,
    "OEOS_AUTHENTICATION_REQUIRED": 401,
    "HTTP_REQUEST_FRAMING_INVALID": 400,
    "HTTP_BODY_DISCONNECTED": 400,
    "SWARM_JSON_DUPLICATE_KEY": 400,
    "SWARM_JSON_NESTING_TOO_DEEP": 400,
}


class HttpBoundaryRefusal(Exception):
    """A fixed, non-reflecting terminal; never include submitted header values."""

    def __init__(self, code: str) -> None:
        self.status_code = _BOUNDARY_STATUSES[code]
        self.refusal_code = code
        super().__init__(code)

    def to_dict(self) -> dict[str, str]:
        return {
            "status": "REFUSED",
            "refusal_code": self.refusal_code,
            "authority_effect": "None",
        }


def header_values(scope, name: bytes) -> list[bytes]:
    """Retain duplicates in the raw HTTP envelope instead of collapsing them."""
    return [value for key, value in scope.get("headers", ()) if key.lower() == name]


def require_local_request(scope) -> None:
    """Admit a direct loopback request with unambiguous same-origin evidence.

    Host spellings are intentionally canonical and narrow. Empty or repeated
    security headers are not missing evidence and never acquire default trust.
    Native local clients may omit Origin/Fetch Metadata; browser evidence, when
    supplied, must agree exactly with the request's local host and scheme.
    """
    refusal = HttpBoundaryRefusal("LOCAL_OPERATOR_REQUIRED")
    peer = scope.get("client")
    if (
        not isinstance(peer, (tuple, list))
        or len(peer) != 2
        or peer[0] not in _LOCAL_PEERS
        or type(peer[1]) is not int
        or not 1 <= peer[1] <= 65535
    ):
        raise refusal
    scheme = scope.get("scheme")
    if scheme not in {"http", "https"}:
        raise refusal
    for key, _ in scope.get("headers", ()):
        name = key.lower()
        if name in {b"forwarded", b"x-real-ip", b"via"} or name.startswith(
            b"x-forwarded-"
        ):
            raise refusal

    hosts = header_values(scope, b"host")
    if len(hosts) != 1 or not 1 <= len(hosts[0]) <= 255:
        raise refusal
    try:
        host = hosts[0].decode("ascii")
    except UnicodeDecodeError:
        raise refusal from None
    match = _LOCAL_HOST.fullmatch(host)
    if match is None or (match.group(1) is not None and int(match.group(1)) > 65535):
        raise refusal
    origins = header_values(scope, b"origin")
    if origins and origins != [f"{scheme}://{host}".encode("ascii")]:
        raise refusal
    sites = header_values(scope, b"sec-fetch-site")
    if sites and sites not in ([b"same-origin"], [b"none"]):
        raise refusal


def declared_body_length(scope) -> int | None:
    """Refuse ambiguous framing; declarations never replace actual counting."""
    values = header_values(scope, b"content-length")
    transfer = header_values(scope, b"transfer-encoding")
    if (
        len(values) > 1
        or (transfer and transfer != [b"chunked"])
        or (values and transfer)
    ):
        raise HttpBoundaryRefusal("HTTP_REQUEST_FRAMING_INVALID")
    if not values:
        return None
    value = values[0]
    if not 1 <= len(value) <= 20 or not value.isdigit():
        raise HttpBoundaryRefusal("HTTP_REQUEST_FRAMING_INVALID")
    return int(value)


class _DuplicateJsonKey(ValueError):
    pass


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKey
        result[key] = value
    return result


def _oversize(prefix: bytes, limit: int, *, truncated: bool) -> IngressRefusal:
    return IngressRefusal(
        OversizeReceipt(
            refusal_code=REFUSAL_REQUEST_TOO_LARGE,
            limit_bytes=limit,
            observed_bytes=len(prefix),
            observed_truncated=truncated,
            observed_prefix_sha256=hashlib.sha256(prefix).hexdigest(),
        )
    )


async def read_request_body(
    scope, receive, *, limit: int = MAX_REQUEST_BODY_BYTES
) -> bytes:
    """Read at most limit+1 bytes, before any JSON/model parsing or dispatch.

    The receive callback is a supplied port, not ambient network I/O. Stop at
    the crossing chunk without copying or draining its unobserved remainder.
    A declared oversize or ambiguous envelope is refused without a body read.
    """
    declared = declared_body_length(scope)
    encodings = header_values(scope, b"content-encoding")
    check_content_encoding(
        b",".join(encodings).decode("latin-1") if encodings else None
    )
    if declared is not None and declared > limit:
        raise _oversize(b"", limit, truncated=False)
    body = bytearray()
    while True:
        message = await receive()
        if message["type"] != "http.request":
            raise HttpBoundaryRefusal("HTTP_BODY_DISCONNECTED")
        body.extend(message.get("body", b"")[: (limit + 1) - len(body)])
        if len(body) > limit:
            raise _oversize(bytes(body), limit, truncated=True)
        if not message.get("more_body", False):
            break
    if declared is not None and len(body) != declared:
        raise HttpBoundaryRefusal("HTTP_REQUEST_FRAMING_INVALID")
    try:
        json.loads(body, object_pairs_hook=_unique_json_object)
    except _DuplicateJsonKey:
        raise HttpBoundaryRefusal("SWARM_JSON_DUPLICATE_KEY") from None
    except RecursionError:
        raise HttpBoundaryRefusal("SWARM_JSON_NESTING_TOO_DEEP") from None
    except (ValueError, UnicodeDecodeError):
        # The framework owns ordinary validation, but must render it safely.
        pass
    return bytes(body)

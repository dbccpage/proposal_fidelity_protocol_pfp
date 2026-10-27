"""Bounded HTTP execution with redacted, explicitly classified failures."""

import json
import urllib.error
import urllib.request

from governance.domain.ingress.limits import MAX_PROVIDER_REPLY_BYTES
from adversary.domain.providers.attempt import RetryClass, TransportFailure
from adversary.domain.providers.types import ProviderError, check_reply_bytes


def post_json(url, headers, body, timeout):
    wire = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=dict(headers), method="POST")
    try:
        with urllib.request.urlopen(wire, timeout=timeout) as response:
            raw = response.read(MAX_PROVIDER_REPLY_BYTES + 1)
    except urllib.error.HTTPError as error:
        try:
            raw = error.read(MAX_PROVIDER_REPLY_BYTES + 1)
            try:
                check_reply_bytes(raw)
            except ProviderError as exc:
                # Preserve the original oversize refusal and classification;
                # only the bounded prefix is retained, not a full-body digest.
                exc.reply_bytes = bytes(raw[:MAX_PROVIDER_REPLY_BYTES])
                exc.reply_truncated = True
                exc.http_status = error.code
                raise
        finally:
            error.close()
        retry = RetryClass.TERMINAL if error.code in (400, 401, 403) else RetryClass.OUTCOME_UNKNOWN
        raise TransportFailure(f"PROVIDER_HTTP_{error.code}", retry=retry,
            reply_bytes=bytes(raw), http_status=error.code) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise TransportFailure("PROVIDER_TRANSPORT_OUTCOME_UNKNOWN") from None
    check_reply_bytes(raw)
    return raw

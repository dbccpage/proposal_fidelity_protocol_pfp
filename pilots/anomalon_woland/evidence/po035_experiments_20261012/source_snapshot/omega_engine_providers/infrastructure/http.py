"""Bounded HTTP execution with redacted, explicitly classified failures."""

import json
import urllib.error
import urllib.request

from omega_engine_governance.domain.ingress.limits import MAX_PROVIDER_REPLY_BYTES
from omega_engine_providers.domain.attempt import RetryClass, TransportFailure
from omega_engine_providers.domain.types import check_reply_bytes


def post_json(url, headers, body, timeout):
    wire = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=dict(headers), method="POST")
    try:
        with urllib.request.urlopen(wire, timeout=timeout) as response:
            raw = response.read(MAX_PROVIDER_REPLY_BYTES + 1)
    except urllib.error.HTTPError as error:
        try:
            raw = error.read(MAX_PROVIDER_REPLY_BYTES + 1)
            check_reply_bytes(raw)
        finally:
            error.close()
        retry = RetryClass.TERMINAL if error.code in (400, 401, 403) else RetryClass.OUTCOME_UNKNOWN
        raise TransportFailure(f"PROVIDER_HTTP_{error.code}", retry=retry) from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise TransportFailure("PROVIDER_TRANSPORT_OUTCOME_UNKNOWN") from None
    check_reply_bytes(raw)
    return raw

"""Public model catalog boundary; no prompt or credential is transmitted."""

import math
import urllib.request

from .openai_compat import OPENROUTER_BASE_URL


def fetch_openrouter_catalog(*, timeout: float = 20.0) -> bytes:
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("CATALOG_TIMEOUT_INVALID")
    request = urllib.request.Request(
        OPENROUTER_BASE_URL + "/models", headers={"Accept": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(8_000_001)

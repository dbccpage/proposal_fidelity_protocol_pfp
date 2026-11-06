"""Fail-closed public capability and tokenizer custody for PO035 experiments.

No credentials, generation, model downloads, or provider retries live here.
Endpoint metadata declares requested controls; it does not attest their execution.
"""

import hashlib
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

LOGIT_MODEL = "qwen/qwen-2.5-72b-instruct"
TOKENIZER_MODEL = "Qwen/Qwen2.5-72B-Instruct"
TOKENIZER_REVISION = "495f39366efef23836d0cfae4fbe635880d2be31"
TOKENIZER_BLOB = "443909a61d429dff23010e5bddd28ff530edda00"
TOKENIZER_SHA256 = "c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539"
RATE_CEILING = Decimal("0.0000004")
REQUIRED_PARAMETERS = frozenset({"max_tokens", "temperature", "top_p", "seed", "logit_bias"})


def _rates(pricing):
    if type(pricing) is not dict or not {"prompt", "completion"}.issubset(pricing):
        raise ValueError("MISSING_PRICE")
    rates = {}
    for key, value in pricing.items():
        if type(key) is not str or type(value) not in (str, int):
            raise ValueError("UNQUOTABLE_PRICE")
        try:
            amount = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError("INVALID_PRICE") from exc
        if not amount.is_finite() or amount < 0:
            raise ValueError("INVALID_PRICE")
        if key in {"prompt", "completion"}:
            if amount > RATE_CEILING:
                raise ValueError("RATE_CEILING_EXCEEDED")
            rates[key] = amount
        elif amount != 0:
            # No cache writes, per-request charges, discounts, or nested overrides
            # are assumed away when computing a hard reservation.
            raise ValueError("ADDITIONAL_PRICE_UNQUOTED")
    return rates


def _parameters(row):
    parameters = row.get("supported_parameters")
    if type(parameters) is not list or any(type(value) is not str for value in parameters):
        raise ValueError("MISSING_SUPPORTED_PARAMETERS")
    return set(parameters)


def validate_logit_profile(catalog, endpoints):
    """Quote the worst rates of every parameter-eligible endpoint, not a headline minimum.

    Include unavailable endpoints conservatively: a status change must not reveal
    an unreserved higher price. At least one eligible endpoint must be operational.
    Callers must retain both public documents and refresh this quote before dispatch.
    """
    if type(catalog) is not dict or type(catalog.get("data")) is not list:
        raise ValueError("INVALID_CATALOG")
    rows = [row for row in catalog["data"] if type(row) is dict and row.get("id") == LOGIT_MODEL]
    if len(rows) != 1:
        raise ValueError("MODEL_IDENTITY_AMBIGUOUS")
    row = rows[0]
    if not REQUIRED_PARAMETERS.issubset(_parameters(row)):
        raise ValueError("REQUIRED_DECODING_UNSUPPORTED")
    _rates(row.get("pricing"))
    data = endpoints.get("data") if type(endpoints) is dict else None
    if (
        type(data) is not dict
        or data.get("id") != LOGIT_MODEL
        or type(data.get("endpoints")) is not list
    ):
        raise ValueError("ENDPOINT_IDENTITY_MISMATCH")
    eligible = []
    for endpoint in data["endpoints"]:
        if type(endpoint) is not dict or endpoint.get("model_id") != LOGIT_MODEL:
            raise ValueError("ENDPOINT_IDENTITY_MISMATCH")
        # Even unsupported endpoints must have finite, nonnegative, fee-free
        # pricing before this deliberately narrow profile authorizes a route.
        rates = _rates(endpoint.get("pricing"))
        if not REQUIRED_PARAMETERS.issubset(_parameters(endpoint)):
            continue
        if type(endpoint.get("tag")) is not str or not endpoint["tag"]:
            raise ValueError("MISSING_ENDPOINT_TAG")
        if type(endpoint.get("status")) is not int:
            raise ValueError("MISSING_ENDPOINT_STATUS")
        eligible.append((endpoint, rates))
    if not eligible or not any(endpoint["status"] == 0 for endpoint, _ in eligible):
        raise ValueError("NO_OPERATIONAL_LOGIT_ENDPOINT")
    tags = [endpoint["tag"] for endpoint, _ in eligible]
    if len(set(tags)) != len(tags):
        raise ValueError("DUPLICATE_ENDPOINT_TAG")
    return {
        "model": LOGIT_MODEL,
        "thinking": None,
        "required_parameters": sorted(REQUIRED_PARAMETERS),
        "prompt_usd_per_token": str(max(rates["prompt"] for _, rates in eligible)),
        "completion_usd_per_token": str(max(rates["completion"] for _, rates in eligible)),
        "ceiling_usd_per_token": str(RATE_CEILING),
        "endpoint_tags": sorted(tags),
        "allow_fallbacks": False,
        "require_parameters": True,
        "enforcement": "PROVIDER_REQUESTED",
    }


def cached_tokenizer_path():
    """The existing cache blob; no download or model loading is attempted."""
    return (
        Path.home()
        / ".cache/huggingface/hub/models--Qwen--Qwen2.5-0.5B-Instruct/blobs"
        / TOKENIZER_BLOB
    )


def _tokenizer_identity(raw):
    if type(raw) is not bytes:
        raise ValueError("TOKENIZER_BYTES_REQUIRED")
    sha256 = hashlib.sha256(raw).hexdigest()
    git_blob = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
    if sha256 != TOKENIZER_SHA256 or git_blob != TOKENIZER_BLOB:
        raise ValueError("TOKENIZER_DIGEST_MISMATCH")
    return sha256, git_blob


def validate_tokenizer_custody(raw, headers):
    """Bind cached bytes to the pinned 72B tokenizer's public HTTP metadata."""
    sha256, git_blob = _tokenizer_identity(raw)
    if type(headers) is not dict or any(
        type(k) is not str or type(v) is not str for k, v in headers.items()
    ):
        raise ValueError("INVALID_TOKENIZER_HEADERS")
    normalized = {key.lower(): value for key, value in headers.items()}
    if len(normalized) != len(headers):
        raise ValueError("DUPLICATE_TOKENIZER_HEADER")
    etag = normalized.get("etag", "")
    etag_value = etag[2:] if etag.startswith("W/") else etag
    if etag_value != '"' + git_blob + '"' or normalized.get("x-repo-commit") != TOKENIZER_REVISION:
        raise ValueError("TOKENIZER_REMOTE_IDENTITY_MISMATCH")
    return {
        "schema": "pfp.po035-tokenizer-custody.v1",
        "model": TOKENIZER_MODEL,
        "revision": TOKENIZER_REVISION,
        "url": f"https://huggingface.co/{TOKENIZER_MODEL}/resolve/{TOKENIZER_REVISION}/tokenizer.json",
        "cached_model": "Qwen/Qwen2.5-0.5B-Instruct",
        "bytes": len(raw),
        "sha256": sha256,
        "git_blob_sha1": git_blob,
        "etag": etag,
        "repo_commit": normalized["x-repo-commit"],
        "identity_scope": "Published tokenizer bytes match; hosted weight revision is not attested.",
        "authority_effect": "None",
    }


def format_only_logit_bias(raw):
    """Bias only standalone one/two/three-backtick tokens; never answer digits.

    This limited formatting intervention does not enforce JSON or ban every
    compound token containing a backtick. Its effects require paired measurement.
    """
    _tokenizer_identity(raw)
    tokenizer = json.loads(raw)
    vocab = tokenizer["model"]["vocab"]
    tokens = [vocab.get("`" * count) for count in (1, 2, 3)]
    if any(type(token) is not int or token < 0 for token in tokens) or len(set(tokens)) != 3:
        raise ValueError("FORMAT_TOKENS_UNAVAILABLE")
    return {str(token): -5 for token in tokens}

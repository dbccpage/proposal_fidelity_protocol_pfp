"""Decisive offline price, capability and tokenizer mutation probes."""

import copy
import hashlib
import json

import pytest

from omega_engine_woland.tests.pilots.relational_spacetime import decoding_controls as models


def documents():
    row = {
        "id": models.LOGIT_MODEL,
        "supported_parameters": sorted(models.REQUIRED_PARAMETERS),
        "pricing": {"prompt": "0.0000001", "completion": "0.0000002"},
    }
    endpoint = {
        "model_id": models.LOGIT_MODEL,
        "tag": "provider/a",
        "status": 0,
        "supported_parameters": sorted(models.REQUIRED_PARAMETERS),
        "pricing": {"prompt": "0.00000036", "completion": "0.0000004", "discount": 0},
    }
    return {"data": [row]}, {"data": {"id": models.LOGIT_MODEL, "endpoints": [endpoint]}}


def test_quote_uses_worst_endpoint_not_catalog_minimum():
    catalog, endpoints = documents()
    cheap = copy.deepcopy(endpoints["data"]["endpoints"][0])
    cheap.update(tag="provider/cheap", pricing={"prompt": "0.00000001", "completion": "0.00000002"})
    endpoints["data"]["endpoints"].append(cheap)
    profile = models.validate_logit_profile(catalog, endpoints)
    assert profile["prompt_usd_per_token"] == "3.6E-7"
    assert profile["completion_usd_per_token"] == "4E-7"
    assert profile["thinking"] is None
    assert profile["require_parameters"] is True
    assert profile["enforcement"] == "PROVIDER_REQUESTED"


@pytest.mark.parametrize("value", ["-1", "NaN", "Infinity", True, 0.0000004, {}, None])
def test_invalid_price_fails_before_dispatch(value):
    catalog, endpoints = documents()
    endpoints["data"]["endpoints"][0]["pricing"]["prompt"] = value
    with pytest.raises(ValueError):
        models.validate_logit_profile(catalog, endpoints)


@pytest.mark.parametrize(
    "pricing",
    [
        {"prompt": "0.000000401", "completion": "0"},
        {"prompt": "0", "completion": "0", "request": "0.000001"},
        {"prompt": "0", "completion": "0", "input_cache_write": "0.00000001"},
        {"prompt": "0", "completion": "0", "discount": "0.5"},
        {"prompt": "0", "completion": "0", "overrides": []},
        {"prompt": "0"},
    ],
)
def test_hidden_fees_and_rate_excess_are_not_assumed_away(pricing):
    catalog, endpoints = documents()
    endpoints["data"]["endpoints"][0]["pricing"] = pricing
    with pytest.raises(ValueError):
        models.validate_logit_profile(catalog, endpoints)


def test_unavailable_high_rate_endpoint_still_blocks_quote():
    catalog, endpoints = documents()
    other = copy.deepcopy(endpoints["data"]["endpoints"][0])
    other.update(tag="provider/down", status=-2)
    other["pricing"]["completion"] = "0.0000005"
    endpoints["data"]["endpoints"].append(other)
    with pytest.raises(ValueError, match="RATE_CEILING_EXCEEDED"):
        models.validate_logit_profile(catalog, endpoints)


@pytest.mark.parametrize(
    "mutation", ["unsupported", "down", "wrong_model", "duplicate", "missing_status"]
)
def test_capability_and_identity_mutants_fail_closed(mutation):
    catalog, endpoints = documents()
    endpoint = endpoints["data"]["endpoints"][0]
    if mutation == "unsupported":
        endpoint["supported_parameters"].remove("logit_bias")
    elif mutation == "down":
        endpoint["status"] = -2
    elif mutation == "wrong_model":
        endpoint["model_id"] = "other/model"
    elif mutation == "duplicate":
        endpoints["data"]["endpoints"].append(copy.deepcopy(endpoint))
    else:
        del endpoint["status"]
    with pytest.raises(ValueError):
        models.validate_logit_profile(catalog, endpoints)


@pytest.fixture
def tokenizer(monkeypatch):
    raw = json.dumps({"model": {"vocab": {"`": 63, "``": 13874, "```": 73594, "7": 22}}}).encode()
    sha256 = hashlib.sha256(raw).hexdigest()
    git_blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    monkeypatch.setattr(models, "TOKENIZER_SHA256", sha256)
    monkeypatch.setattr(models, "TOKENIZER_BLOB", git_blob)
    return raw, {"ETag": 'W/"' + git_blob + '"', "X-Repo-Commit": models.TOKENIZER_REVISION}


def test_tokenizer_byte_identity_and_bias_do_not_target_answer_digits(tokenizer):
    raw, headers = tokenizer
    custody = models.validate_tokenizer_custody(raw, headers)
    assert custody["sha256"] == hashlib.sha256(raw).hexdigest()
    assert custody["revision"] in custody["url"]
    assert models.format_only_logit_bias(raw) == {"63": -5, "13874": -5, "73594": -5}
    assert "22" not in models.format_only_logit_bias(raw)


@pytest.mark.parametrize(
    "mutation", ["bytes", "etag", "revision", "duplicate_header", "header_list"]
)
def test_tokenizer_custody_mutations_are_rejected(tokenizer, mutation):
    raw, headers = tokenizer
    if mutation == "bytes":
        raw += b" "
    elif mutation == "etag":
        headers["ETag"] = '"' + "0" * 40 + '"'
    elif mutation == "revision":
        headers["X-Repo-Commit"] = "0" * 40
    elif mutation == "duplicate_header":
        headers["etag"] = headers["ETag"]
    else:
        headers["ETag"] = [headers["ETag"]]
    with pytest.raises(ValueError):
        models.validate_tokenizer_custody(raw, headers)

"""Shared matrix-runner support: configuration, parsing, provider errors and custody.

Counterexamples named by these tests: runners read a .env file (one from outside the
repository), invented a SOLVED answer when a reply merely mentioned "by decide", scored HTTP
failures as wrong answers, and kept only 200 characters of the reply. No provider is called;
urlopen is replaced by a local stub.
"""

from __future__ import annotations

import io
import json
import urllib.error
import urllib.request

import pytest
from pfp.infrastructure import formal_matrix as mrs


def test_missing_key_is_a_typed_refusal() -> None:
    with pytest.raises(mrs.RunnerConfigError) as exc:
        mrs.require_api_key({})
    assert exc.value.code == "PROVIDER_NOT_CONFIGURED"
    assert mrs.require_api_key({mrs.API_KEY_ENV: "k"}) == "k"


def test_unparsable_reply_is_never_turned_into_an_answer() -> None:
    assert mrs.extract_json_object("The proof is `by decide`.") is None
    assert mrs.extract_json_object("") is None
    assert mrs.extract_json_object('```json\n{"status": "SOLVED"}\n```') == {"status": "SOLVED"}
    assert mrs.extract_json_object("[1, 2]") is None


def test_participant_view_drops_answer_bearing_keys() -> None:
    case = {
        "case_id": "c_pub_01_q8",
        "category": "poisoned",
        "expected_reason": "X",
        "note": "Q8",
        "data": 1,
    }
    view = mrs.participant_view(case, "q1", withheld=("note",))
    assert view == {"case_id": "q1", "data": 1}


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_transport_failure_is_infra_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*_args, **_kwargs):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(urllib.request, "urlopen", fail)
    res = mrs.call_openrouter("k", "m", [{"role": "user", "content": "x"}])
    assert res["ok"] is False and res["outcome"] == mrs.INFRA_ERROR


def test_http_error_is_infra_error_with_body(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(req, *_args, **_kwargs):
        raise urllib.error.HTTPError(
            req.full_url, 429, "rate", {}, io.BytesIO(b'{"error": "rate limited"}')
        )

    monkeypatch.setattr(urllib.request, "urlopen", fail)
    res = mrs.call_openrouter("k", "m", [{"role": "user", "content": "x"}])
    assert res["outcome"] == mrs.INFRA_ERROR
    assert res["error"] == "HTTP 429"
    assert "rate limited" in res["raw_body"]


def test_raw_body_kept_in_full(monkeypatch: pytest.MonkeyPatch) -> None:
    long_text = "x" * 5000
    body = json.dumps(
        {"choices": [{"message": {"content": long_text}}], "usage": {"total_tokens": 7}}
    )
    monkeypatch.setattr(urllib.request, "urlopen", lambda *_a, **_k: _Resp(body.encode("utf-8")))
    res = mrs.call_openrouter("k", "m", [{"role": "user", "content": "x"}])
    assert res["ok"] is True
    assert res["content"] == long_text
    assert res["raw_body"] == body


def test_summary_excludes_infra_errors_and_counts_abstentions() -> None:
    records = [
        {"outcome": "VERIFIED"},
        {"outcome": mrs.INFRA_ERROR},
        {"outcome": mrs.classify(False, {"status": "UNKNOWN"})},
        {"outcome": mrs.classify(False, {"status": "SOLVED"})},
    ]
    summary = mrs.summarize(records)
    assert summary["answered"] == 3
    assert summary["verified"] == 1
    assert summary["outcomes"]["ABSTAINED"] == 1
    assert summary["outcomes"]["REJECTED"] == 1


def test_run_folder_is_under_the_intelligence_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.setenv("CORE_INTELLIGENCE_ROOT", str(tmp_path))
    folder = mrs.run_folder("c0xx", "abc")
    assert folder.is_dir()
    assert tmp_path.resolve() in folder.resolve().parents


def test_space_bunny_is_labelled_exploratory() -> None:
    assert "outside the challenge protocol" in mrs.model_label("stealth/space-bunny-alpha")
    assert mrs.model_label("meta-llama/llama-3.3-70b-instruct") is None

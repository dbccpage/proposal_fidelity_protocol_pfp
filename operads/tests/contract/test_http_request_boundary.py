"""The real OEWAS router admits bounded local requests even when mounted alone."""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest
from fastapi import FastAPI
from operations.domain.rop.result import Err

from governance.domain.ingress.limits import MAX_REQUEST_BODY_BYTES
from operads.application.dtos.api_error_dto import (
    ApiErrorDTO,
)
from operads.frontend.api.app import create_app
from operads.infrastructure.bootstrap import OeopContainer

WORKFLOWS = "/api/oeop/v3/workflows:validate"


@pytest.fixture(params=["standalone", "mounted"])
def surface(request, tmp_path, monkeypatch):
    container = OeopContainer(workspace_root=tmp_path)
    calls = []
    validate = container.api.validate_workflows

    def record(**kwargs):
        calls.append(kwargs)
        return validate(**kwargs)

    monkeypatch.setattr(container.api, "validate_workflows", record)
    if request.param == "standalone":
        app = create_app(api=container.api)
    else:
        app = FastAPI()
        app.include_router(container.router)
    try:
        yield app, container, calls
    finally:
        container.uow.close()


def invoke(
    surface,
    *,
    body=b'{"nodes":[],"edges":[]}',
    headers=(),
    peer=("127.0.0.1", 49152),
    host="localhost",
    chunks=None,
    path=WORKFLOWS,
    method="POST",
):
    app, _, _ = surface
    pulls = []

    async def send_request():
        async def stream():
            for chunk in chunks:
                pulls.append(len(chunk))
                yield chunk

        transport = httpx.ASGITransport(
            app=app, client=peer, raise_app_exceptions=False
        )
        async with httpx.AsyncClient(transport=transport) as client:
            req = httpx.Request(
                method,
                "http://localhost" + path,
                content=stream() if chunks is not None else body,
                headers=[("content-type", "application/json"), *headers],
            )
            if host is None:
                del req.headers["host"]
            elif not any(name.lower() == "host" for name, _ in headers):
                req.headers["host"] = host
            return await client.send(req)

    return asyncio.run(send_request()), pulls


@pytest.mark.parametrize(
    "options",
    [
        {"peer": ("203.0.113.1", 9)},
        {"peer": None},
        {"host": None},
        {"host": ""},
        {"host": "attacker.invalid"},
        {"host": "localhost,localhost"},
        {"headers": [("host", "localhost"), ("host", "localhost")]},
        {"headers": [("origin", "")]},
        {"headers": [("origin", "null")]},
        {"headers": [("origin", "https://attacker.invalid")]},
        {"headers": [("origin", "http://localhost"), ("origin", "http://localhost")]},
        {"headers": [("x-forwarded-for", "127.0.0.1")]},
        {"headers": [("forwarded", "for=127.0.0.1")]},
        {"headers": [("sec-fetch-site", "cross-site")]},
    ],
)
def test_nonlocal_or_ambiguous_callers_never_dispatch(surface, options):
    response, pulls = invoke(surface, chunks=[b'{"nodes":[],"edges":[]}'], **options)
    assert response.status_code == 403
    assert response.json()["refusal_code"] == "LOCAL_OPERATOR_REQUIRED"
    assert response.json()["authority_effect"] == "None"
    assert len(response.content) < 4096
    assert pulls == []
    assert surface[2] == []


@pytest.mark.parametrize(
    "peer,host",
    [
        (("127.0.0.1", 9), "localhost"),
        (("127.0.0.1", 9), "127.0.0.1:8000"),
        (("::1", 9), "[::1]:8000"),
    ],
)
def test_actual_workflow_success_refusal_and_recovery(surface, peer, host):
    success, _ = invoke(
        surface, peer=peer, host=host, headers=[("origin", "http://" + host)]
    )
    assert success.status_code == 200
    assert success.json()["is_valid"] is True
    denied, _ = invoke(surface, peer=peer, host=host, headers=[("origin", "null")])
    assert denied.status_code == 403
    recovery, _ = invoke(surface, peer=peer, host=host)
    assert recovery.json() == success.json()
    assert len(surface[2]) == 2


@pytest.mark.parametrize("declared", [None, "1"])
def test_chunked_oversize_ignored_field_stops_at_crossing_chunk(surface, declared):
    body = json.dumps(
        {
            "nodes": [],
            "edges": [],
            "ignored": "BOUNDARY-CANARY" + "x" * MAX_REQUEST_BODY_BYTES,
        }
    ).encode()
    chunks = [
        body[:MAX_REQUEST_BODY_BYTES],
        body[MAX_REQUEST_BODY_BYTES:],
        b"never read",
    ]
    headers = [] if declared is None else [("content-length", declared)]
    # A raw ASGI client may claim a false length; it must never raise the byte ceiling.
    response, pulls = invoke(surface, chunks=chunks, headers=headers)
    assert response.status_code in (400, 413)
    assert surface[2] == []
    assert len(pulls) <= 2
    assert "BOUNDARY-CANARY" not in response.text
    assert len(response.content) < 4096
    if declared is None:
        assert response.status_code == 413
        assert response.json()["refusal_code"] == "SWARM_REQUEST_TOO_LARGE"
        assert response.json()["observed_bytes"] == MAX_REQUEST_BODY_BYTES + 1
        assert len(pulls) == 2
    recovered, _ = invoke(surface)
    assert recovered.status_code == 200
    assert len(surface[2]) == 1


@pytest.mark.parametrize(
    "headers",
    [
        [("content-length", "1"), ("content-length", "1")],
        [("content-length", "1"), ("content-length", "999999")],
        [("content-length", "bad")],
        [("content-length", "-1")],
    ],
)
def test_ambiguous_framing_is_refused_without_body_reads(surface, headers):
    response, pulls = invoke(surface, headers=headers, chunks=[b"not read"])
    assert response.status_code == 400
    assert response.json()["refusal_code"] == "HTTP_REQUEST_FRAMING_INVALID"
    assert pulls == [] and surface[2] == []


@pytest.mark.parametrize("offset", [-1, 0, 1])
def test_full_body_limit_counts_unknown_fields_before_dto_parsing(surface, offset):
    base = b'{"nodes":[],"edges":[],"ignored":""}'
    body = base[:-2] + b"x" * (MAX_REQUEST_BODY_BYTES + offset - len(base)) + base[-2:]
    assert len(body) == MAX_REQUEST_BODY_BYTES + offset
    response, _ = invoke(surface, body=body)
    assert response.status_code == (413 if offset > 0 else 200)
    assert len(surface[2]) == (0 if offset > 0 else 1)


@pytest.mark.parametrize(
    "body",
    [
        b'{"nodes":[],"nodes":[],"edges":[]}',
        b'{"nodes":[],"no\\u0064es":[],"edges":[]}',
        b'{"nodes":[],"edges":[],"ignored":{"key":1,"key":2}}',
    ],
)
def test_duplicate_json_members_refuse_before_workflow_dispatch(surface, body):
    refused, _ = invoke(surface, body=body)
    assert refused.status_code == 400
    assert refused.json()["refusal_code"] == "SWARM_JSON_DUPLICATE_KEY"
    assert surface[2] == []
    recovered, _ = invoke(
        surface, body=b'{"nodes":[],"edges":[],"ignored":[{"key":1},{"key":2}]}'
    )
    assert recovered.status_code == 200


@pytest.mark.parametrize(
    "body,content_type",
    [
        (b'{"nodes":"BOUNDARY-PRIVATE-CANARY"}', "application/json"),
        (b"BOUNDARY-PRIVATE-CANARY" * 1000, "text/plain"),
    ],
)
def test_validation_errors_are_bounded_and_nonreflecting(surface, body, content_type):
    response, _ = invoke(surface, body=body, headers=[("content-type", content_type)])
    assert response.status_code == 422
    assert "BOUNDARY-PRIVATE-CANARY" not in response.text
    assert len(response.content) < 4096
    assert surface[2] == []


def test_catalog_not_found_does_not_reflect_request_identifier(surface):
    marker = "CATALOG-PRIVATE-CANARY"
    response, _ = invoke(
        surface, path="/api/oeop/v3/catalogs/" + marker, method="GET", body=b""
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "CATALOG_NOT_FOUND"
    assert marker not in response.text
    assert len(response.content) < 4096


def test_supplied_api_error_keeps_code_and_status_but_not_private_details(
    surface, monkeypatch
):
    marker = "C:/private-workspace/ERROR-PRIVATE-CANARY/" + "x" * 5000
    error = ApiErrorDTO(
        code="CATALOG_PERSIST_FAILED",
        message=marker,
        status_code=500,
        locus=marker,
        details={"private-path": marker},
    )
    monkeypatch.setattr(
        surface[1].api, "validate_workflows", lambda **kwargs: Err(error)
    )
    response, _ = invoke(surface)
    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "CATALOG_PERSIST_FAILED"
    assert "ERROR-PRIVATE-CANARY" not in response.text
    assert "private-path" not in response.text
    assert len(response.content) < 4096
    # HTTP redaction does not mutate the useful error object for trusted callers.
    assert error.message == error.locus == marker
    assert error.details == {"private-path": marker}


@pytest.mark.parametrize(
    "code,status_code,expected_status",
    [
        ("ERROR_PRIVATE_CANARY", 400, 400),
        ("ERROR-PRIVATE-CANARY" * 1000, 200, 500),
        (None, True, 500),
        (["ERROR-PRIVATE-CANARY"], 999, 500),
    ],
    ids=[
        "unknown-code",
        "oversize-code-success-status",
        "null-code-bool-status",
        "list-code-invalid-status",
    ],
)
def test_unexpected_error_code_or_status_has_a_fixed_fallback(
    surface, monkeypatch, code, status_code, expected_status
):
    error = ApiErrorDTO(
        code=code, message="ERROR-PRIVATE-CANARY", status_code=status_code
    )
    monkeypatch.setattr(
        surface[1].api, "validate_workflows", lambda **kwargs: Err(error)
    )
    response, _ = invoke(surface)
    assert response.status_code == expected_status
    assert response.json()["detail"]["code"] == "OEWAS_REQUEST_FAILED"
    assert "ERROR-PRIVATE-CANARY" not in response.text
    assert "ERROR_PRIVATE_CANARY" not in response.text
    assert len(response.content) < 4096

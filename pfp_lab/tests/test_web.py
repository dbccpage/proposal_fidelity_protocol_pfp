"""HTTP contract of the web front end, and the loopback bind rule.

AuthorityEffect: None.
Contract: urn:pfp-lab:tests:web:v1
"""

from __future__ import annotations

import io
import json

import pytest
from fastapi.testclient import TestClient

from pfp_lab.core.contracts import CORE_VERSION, MAX_JSON_BYTES, get_pack
from pfp_lab.web import app as server
from pfp_lab.web.app import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def scenario_text(pack_id: str = "paper-005-worked-session") -> str:
    return get_pack(pack_id).model_dump_json(by_alias=True)


def test_version_and_packs(client: TestClient) -> None:
    assert client.get("/api/version").json() == {"version": CORE_VERSION, "authority_effect": "None"}
    packs = client.get("/api/packs").json()["packs"]
    assert packs[0]["pack_id"] == "paper-005-worked-session"
    pack = client.get("/api/packs/two-islands")
    assert (pack.status_code, pack.json()["schema"]) == (200, "pfp-lab.scenario.v1")
    missing = client.get("/api/packs/nope")
    assert (missing.status_code, missing.json()["code"]) == (404, "UNKNOWN_PACK")


def test_run_and_verify(client: TestClient) -> None:
    receipt = client.post("/api/run", content=scenario_text()).json()
    assert receipt["final"]["obstruction"] == "3"
    report = client.post("/api/verify", content=json.dumps(receipt)).json()
    assert report == {"valid": True, "digest": receipt["digest"], "problems": []}
    receipt["digest"] = "0" * 64
    assert client.post("/api/verify", content=json.dumps(receipt)).json()["valid"] is False


@pytest.mark.parametrize(
    "body",
    ["{bad", json.dumps({"schema": "pfp-lab.scenario.v1"}), json.dumps({"x": True})],
)
def test_refused_bodies(client: TestClient, body: str) -> None:
    response = client.post("/api/run", content=body)
    assert (response.status_code, response.json()["code"]) == (422, "ADMISSION")
    assert response.json()["message"].startswith("input refused")


def test_oversize_body_is_413(client: TestClient) -> None:
    response = client.post("/api/run", content=b" " * (MAX_JSON_BYTES + 1))
    assert (response.status_code, response.json()["code"]) == (413, "ADMISSION")
    exact = client.post("/api/run", content=b" " * MAX_JSON_BYTES)
    assert exact.status_code == 422


def test_budget_is_422(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    import pfp_lab.core.session as session

    monkeypatch.setattr(session.run_scenario, "__kwdefaults__", {"budget": 2})
    response = client.post("/api/run", content=scenario_text())
    assert (response.status_code, response.json()["code"]) == (422, "BUDGET_EXCEEDED")


def test_admission_error_from_core_is_422(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    import pfp_lab.web.app as app_module
    from pfp_lab.core.admission import AdmissionError

    def refuse(*_: object) -> object:
        raise AdmissionError("refused for the test")

    monkeypatch.setattr(app_module, "run_scenario", refuse)
    response = client.post("/api/run", content=scenario_text())
    assert response.json() == {"code": "ADMISSION", "message": "refused for the test"}


def test_page_and_assets(client: TestClient) -> None:
    page = client.get("/")
    assert page.status_code == 200
    assert "<title>PFP Lab</title>" in page.text
    script = client.get("/static/app.js")
    assert script.headers["content-type"].startswith("text/javascript")
    assert client.get("/static/app.css").headers["content-type"].startswith("text/css")
    assert client.get("/static/../app.py").status_code == 404
    assert client.get("/static/index.html").status_code == 404


@pytest.mark.parametrize(
    ("host", "loopback"),
    [
        ("127.0.0.1", True),
        ("127.8.8.8", True),
        ("localhost", True),
        ("LOCALHOST", True),
        ("::1", True),
        ("[::1]", True),
        ("0.0.0.0", False),
        ("192.168.1.5", False),
        ("example.com", False),
    ],
)
def test_is_loopback(host: str, loopback: bool) -> None:
    assert server.is_loopback(host) is loopback


def test_remote_bind_is_refused_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    started: list[tuple[str, int]] = []
    monkeypatch.setattr("uvicorn.run", lambda app, host, port, log_level: started.append((host, port)))
    err = io.StringIO()
    assert server.main(["--host", "0.0.0.0"], err) == server.REFUSED
    assert "refusing to bind 0.0.0.0" in err.getvalue()
    assert started == []
    assert server.main(["--host", "0.0.0.0", "--allow-remote", "--port", "9000"], err) == 0
    assert server.main([], err) == 0
    assert started == [("0.0.0.0", 9000), ("127.0.0.1", server.DEFAULT_PORT)]

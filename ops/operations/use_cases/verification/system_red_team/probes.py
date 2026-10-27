"""Bounded local adversarial probes against real adapters and typed domain code.

Fixtures replace only external side effects or dangerous allocation, never the
policy under examination. Returned PASS/FAIL is the security observation, not
the success of running this Python function. AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import patch

from adversary.domain.native import NativeOperationPort

from .red_team_socket_guard import denied_network  # noqa: F401 - legacy re-export

OEOS_FIXTURE_TOKEN = "r" * 64


@dataclass(frozen=True)
class Case:
    identity: str
    title: str
    paths: tuple[str, ...]
    expected: str
    run: object
    severity: str = "HIGH"


def result(secure: bool, observed: dict, *, positive=True, recovery=True):
    return {
        "execution_status": "EXECUTED",
        "security_status": "PASS" if secure else "FAIL",
        "positive_control": "PASS" if positive else "FAIL",
        "recovery_status": "PASS" if recovery else "FAIL",
        "observed": observed,
    }


def text_limits(root, temporary):
    from governance.domain.ingress.limits import (
        MAX_ADMITTED_TEXT_BYTES,
        REFUSAL_TEXT_TOO_LARGE,
        IngressRefusal,
        check_text_bytes,
    )
    cases = []
    for character in ("x", "\U0001f4a3"):
        for delta in (-1, 0, 1):
            size = MAX_ADMITTED_TEXT_BYTES + delta
            width = len(character.encode())
            text = character * (size // width) + "x" * (size % width)
            refused, receipt = False, None
            try:
                check_text_bytes(text, limit=MAX_ADMITTED_TEXT_BYTES,
                                 refusal_code=REFUSAL_TEXT_TOO_LARGE)
            except IngressRefusal as error:
                refused, receipt = True, error.receipt.to_dict()
            cases.append({"bytes": size, "width": width, "refused": refused,
                          "receipt": receipt})
    check_text_bytes("recovery", limit=MAX_ADMITTED_TEXT_BYTES,
                     refusal_code=REFUSAL_TEXT_TOO_LARGE)
    return result(all(c["refused"] == (c["bytes"] > MAX_ADMITTED_TEXT_BYTES) for c in cases),
                  {"cases": cases, "scope": "Shared text guard, not all its callers"})


def _oeos_fixture():
    """Build an in-memory, provider-free OEOS kernel for boundary probes."""
    from operating_system.adapters import (
        FixedFixtureVerifier,
        FixtureCheckoutLease,
        StaticFixtureCapabilities,
    )
    from operating_system.application import (
        BoundedTaskQueue,
        ExecutionDispositionV1,
        ExecutionResultV1,
        TaskService,
        VerificationResultV1,
    )
    from operating_system.domain import CapabilitySnapshotV1
    from operating_system.entrypoints.api import create_app
    from operating_system.infrastructure import SqliteTaskStore

    digest_a = "sha256:" + "a" * 64
    digest_b = "sha256:" + "b" * 64
    calls = []

    class Executor:
        def execute(self, task, cancellation):
            calls.append(task.envelope.task_id)
            return ExecutionResultV1(
                ExecutionDispositionV1.SUCCEEDED, digest_a, digest_b
            )

        def diagnostic(self):
            return {"fixture_only": True, "status": "HEALTHY"}

    store = SqliteTaskStore()
    service = TaskService(
        store=store,
        queue=BoundedTaskQueue(8),
        executor=Executor(),
        verifier=FixedFixtureVerifier(
            VerificationResultV1(
                True, "red-team-fixture", digest_a, digest_b
            )
        ),
        capabilities=StaticFixtureCapabilities(
            CapabilitySnapshotV1(
                "red-team-snapshot", "2026-09-08T08:00:00.000000Z", ()
            )
        ),
        checkout_lease=FixtureCheckoutLease(),
        clock=lambda: "2026-09-08T08:00:00.000000Z",
    )
    return (
        create_app(service, bearer_token=OEOS_FIXTURE_TOKEN),
        service,
        calls,
        store,
    )


def _oeos_payload(suffix="one"):
    return {
        "task_id": f"red-team-{suffix}",
        "idempotency_key": f"red-team-idem-{suffix}",
        "task_family": "code.review",
        "repository": "dbccpage/sentinelpy",
        "repository_head_sha": "1" * 40,
        "encrypted_request_ref": {
            "artifact_schema": "core.oeos.prompt.v1",
            "authority_effect": "None",
            "byte_length": 12,
            "encrypted_envelope_digest": "sha256:" + "c" * 64,
            "plaintext_sha256": "sha256:" + "a" * 64,
            "protector_id": "fixture-protector.v1",
            "schema": "core.oeos.encrypted-artifact-ref.v1",
        },
        "requested_skills": [],
        "action_limits": {
            "mutating": False,
            "max_steps": 4,
            "max_wall_seconds": 60,
            "max_cost_microunits": 0,
        },
        "policy_digest": "sha256:" + "b" * 64,
    }


def sbe_allocation(root, temporary):
    del root, temporary
    from fastapi.testclient import TestClient

    from adversary.stage.application import emission

    app, service, calls, store = _oeos_fixture()
    allocations = []
    with patch.object(
        emission.np.random,
        "default_rng",
        side_effect=lambda *args, **kwargs: allocations.append((args, kwargs)),
    ):
        with TestClient(
            app, base_url="http://localhost", client=("127.0.0.1", 49152),
            raise_server_exceptions=False,
            headers={"authorization": f"Bearer {OEOS_FIXTURE_TOKEN}"},
        ) as client:
            positive = client.post("/v1/tasks", json=_oeos_payload("sbe-positive"))
            hostile = client.post(
                "/api/v1/sbe/analyze",
                json={"text": "fixture", "dim": 1_000_000_000},
            )
            recovered = client.get("/v1/doctor")
    recovery_ok = recovered.status_code == 200 and service.get(
        "red-team-sbe-positive"
    ).state.value == "QUEUED"
    store.close()
    return result(
        hostile.status_code == 404 and not allocations and not calls,
        {
            "allocation_dimensions": allocations,
            "legacy_route_status": hostile.status_code,
            "provider_calls": 0,
            "scope": "Removed Operations route plus canonical OEOS task ingress",
        },
        positive=positive.status_code == 202,
        recovery=recovery_ok,
    )


def unauthenticated_live_mode(root, temporary):
    del root, temporary
    from fastapi.testclient import TestClient

    app, service, calls, store = _oeos_fixture()
    hostile_payload = _oeos_payload("live-hostile")
    hostile_payload["fixture_mode"] = False
    with TestClient(
        app, base_url="http://localhost", client=("127.0.0.1", 49152),
        raise_server_exceptions=False,
        headers={"authorization": f"Bearer {OEOS_FIXTURE_TOKEN}"},
    ) as client:
        hostile = client.post("/v1/tasks", json=hostile_payload)
        hostile_calls = list(calls)
        recovered = client.post("/v1/tasks", json=_oeos_payload("live-recovery"))
    recovery_ok = recovered.status_code == 202 and service.get(
        "red-team-live-recovery"
    ).state.value == "QUEUED"
    store.close()
    return result(
        hostile.status_code == 422 and not hostile_calls,
        {"status": hostile.status_code,
         "executor_dispatches": hostile_calls, "provider_calls": 0,
         "scope": "OEOS has no request-selected live/fixture execution mode"},
        positive=recovered.status_code == 202,
        recovery=recovery_ok,
    )


def http_bounds(root, temporary):
    del root, temporary
    from fastapi.testclient import TestClient

    app, service, calls, store = _oeos_fixture()
    with TestClient(
        app, base_url="http://localhost", client=("127.0.0.1", 49152),
        raise_server_exceptions=False,
        headers={"authorization": f"Bearer {OEOS_FIXTURE_TOKEN}"},
    ) as client:
        positive = client.post("/v1/tasks", json=_oeos_payload("bounds-positive"))
        oversized = client.post(
            "/v1/tasks", content=b"x" * 65537,
            headers={"content-type": "application/json"},
        )
        encoded = client.post(
            "/v1/tasks", content=b"not-an-archive",
            headers={"content-encoding": "gzip"},
        )
        recovered = client.post("/v1/tasks", json=_oeos_payload("bounds-recovery"))
    recovery_ok = recovered.status_code == 202 and service.get(
        "red-team-bounds-recovery"
    ).state.value == "QUEUED"
    store.close()
    return result(
        oversized.status_code == 413 and encoded.status_code == 415 and not calls,
        {"body_limit_status": oversized.status_code,
         "encoding_status": encoded.status_code,
         "scope": "Actual OEOS ASGI boundary; no worker dispatch at task submission"},
        positive=positive.status_code == 202,
        recovery=recovery_ok,
    )


def duplicate_json(root, temporary):
    del root, temporary
    from fastapi.testclient import TestClient

    app, service, calls, store = _oeos_fixture()
    payload = json.dumps(_oeos_payload("duplicate"), separators=(",", ":"))
    payload = payload.replace('"mutating":false', '"mutating":false,"mutating":true')
    with TestClient(
        app, base_url="http://localhost", client=("127.0.0.1", 49152),
        raise_server_exceptions=False,
        headers={"authorization": f"Bearer {OEOS_FIXTURE_TOKEN}"},
    ) as client:
        response = client.post(
            "/v1/tasks", content=payload.encode(),
            headers={"content-type": "application/json"},
        )
        hostile_calls = list(calls)
        recovered = client.post("/v1/tasks", json=_oeos_payload("duplicate-recovery"))
    recovery_ok = recovered.status_code == 202 and service.get(
        "red-team-duplicate-recovery"
    ).state.value == "QUEUED"
    store.close()
    return result(
        response.status_code == 400 and not hostile_calls,
        {"status": response.status_code,
         "executor_dispatches": hostile_calls, "provider_calls": 0,
         "scope": "Duplicate mutating flag at actual OEOS HTTP boundary"},
        positive=recovered.status_code == 202,
        recovery=recovery_ok,
    )


def oewas_oversize(root, temporary):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from operads.infrastructure.bootstrap import create_oeop_container

    container = create_oeop_container(workspace_root=root)
    app = FastAPI()
    app.include_router(container.router)
    with TestClient(app, raise_server_exceptions=False) as client:
        positive = client.post("/api/oeop/v3/terms:compile",
                               json={"agent_id": "fixture_actor", "term_expr": "identity"})
        hostile = client.post("/api/oeop/v3/terms:compile",
                              json={"agent_id": "fixture_actor", "term_expr": "x" * 16385})
        recovered = client.post("/api/oeop/v3/terms:compile",
                                json={"agent_id": "fixture_actor", "term_expr": "identity"})
    expected_license = positive.status_code == 422 and (
        positive.json().get("detail", {}).get("code") == "LICENSE_WITNESS_REQUIRED"
    )
    return result(
        hostile.status_code == 413,
        {"status": hostile.status_code, "response": hostile.json(),
         "scope": "Shipped mountable router; no deployment-wide middleware claim",
         "licensing_positive_path": "UNIMPLEMENTED",
         "bounded_input_control": "Expected existing license refusal, not successful authorization"},
        positive=expected_license,
        recovery=recovered.status_code == positive.status_code and recovered.json() == positive.json(),
    )


def oewas_actor_refusal(root, temporary):
    from operads.infrastructure.bootstrap import create_oeop_container

    container = create_oeop_container(workspace_root=root)
    rows = []
    for actor in ("fixture_actor", "agent_manuscript_truth", "administrator"):
        value = container.api.compile_licensed_term(agent_id=actor, term_expr="identity")
        rows.append({"actor": actor, "refused": value.is_err,
                     "code": value.unwrap_err().code if value.is_err else None})
    return {
        **result(all(r["refused"] and r["code"] == "LICENSE_WITNESS_REQUIRED" for r in rows),
                 {"cases": rows, "scope": "Fail-closed adapter; no supported licensed-success witness"}),
        "positive_control": "UNVERIFIED",
        "recovery_status": "UNVERIFIED",
    }


def terminal_selection(root, temporary):
    from adversary.stage.domain.packets import CandidateProposalV1, ChallengeV1
    from adversary.use_cases.act_helpers import execute_act5_terminal_verdict

    def digest(value):
        return "sha256:" + hashlib.sha256(value.encode()).hexdigest()
    candidates = [CandidateProposalV1(
        producer_agent_id="fixture_producer", work_packet_id=digest("packet"),
        artifact_refs=(digest(name),), prediction_receipt_id=digest("prediction"),
        nonclaims=("No authority",),
    ) for name in ("bad-first", "good-second")]
    challenge = ChallengeV1(
        candidate_id=candidates[0].candidate_id, critic_agent_id="fixture_critic",
        trust_domain="independent_fixture", challenge_kind="COUNTERMODEL",
        statement="The first candidate mutates its input.",
        evidence_refs=(digest("counterexample"),), blocking=True,
    )
    runtime = SimpleNamespace(request_external_admission=False)
    positive = execute_act5_terminal_verdict(runtime, "fixture_run", [candidates[1]], [])
    hostile = execute_act5_terminal_verdict(runtime, "fixture_run", candidates, [challenge])
    recovered = execute_act5_terminal_verdict(runtime, "fixture_run", [candidates[1]], [])
    return result(
        hostile[1] != candidates[0].candidate_id,
        {"selected": hostile[1], "blocked_candidate": candidates[0].candidate_id,
         "challenge": challenge.to_dict(), "selection_disposition": hostile[2].disposition,
         "scope": "Actual Act V selection, not a whole-bout/native acceptance claim"},
        positive=positive[1] == candidates[1].candidate_id,
        recovery=recovered[1] == candidates[1].candidate_id,
    )


def persistence_recovery(root, temporary, *, native_support: NativeOperationPort):
    from adversary.use_cases.persistence import persist_bout_run_folder

    class FixtureReceipt:
        def to_dict(self):
            return {"schema": "red-team.fixture-receipt", "authority_effect": "None"}

    def save(key):
        return persist_bout_run_folder(temporary, key, FixtureReceipt(), "fixture", [],
                                       {"authority_effect": "None"}, native_support=native_support)
    good = save("positive")
    with patch("adversary.use_cases.persistence.os.replace",
               side_effect=OSError("INJECTED_ATOMIC_RENAME_FAILURE")):
        failure = save("interrupted")
    residue = sorted(p.name for p in (temporary / "runs").iterdir())
    recovered = save("recovered")
    before = {p.name: p.read_bytes() for p in recovered.unwrap().iterdir()} if recovered.is_ok else {}
    duplicate = save("recovered")
    after = {p.name: p.read_bytes() for p in recovered.unwrap().iterdir()} if recovered.is_ok else {}
    return result(
        failure.is_err and failure.unwrap_err().code == "RUN_FOLDER_PERSIST_FAILED"
        and residue == ["positive"] and duplicate.is_err
        and duplicate.unwrap_err().code == "RUN_FOLDER_EXISTS" and before == after,
        {"failure_code": failure.unwrap_err().code if failure.is_err else None,
         "post_failure_directories": residue, "duplicate_refused": duplicate.is_err,
         "scope": "Real atomic persistence with a serialization fixture; no receipt-semantic validation"},
        positive=good.is_ok,
        recovery=recovered.is_ok and set(before) == {
            "receipt.json", "novella.md", "ddc.jsonl", "summary.json", "uts.jsonl"
        },
    )


def _python_files(base):
    if base.is_file():
        return (base,)
    return tuple(base.rglob("*.py")) if base.exists() else ()


def _existing_python_files(base):
    return tuple(base.rglob("*.py")) if base.exists() else ()


def _marker_hits(root, path, markers):
    rel = path.relative_to(root).as_posix()
    if "/tests/" in rel or "/verification/" in rel or "__pycache__" in rel:
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    return [{"path": rel, "marker": marker} for marker in markers if marker in text]


def _scan_native_markers(root, scan_roots, markers):
    hits = []
    for base in scan_roots:
        for path in _python_files(base):
            hits.extend(_marker_hits(root, path, markers))
    return hits


def _scan_reverse_integer_list(root):
    reverse_hits = []
    for base in (
        root / "adversary",
        root / "operations" / "use_cases" / "adversary_bout",
    ):
        for path in _existing_python_files(base):
            rel = path.relative_to(root).as_posix()
            if "/tests/" in rel or "/verification/" in rel:
                continue
            text = path.read_text(encoding="utf-8", errors="replace").lower()
            if "reverse" in text and "integer" in text and "list" in text:
                reverse_hits.append(rel)
    return reverse_hits


def _scan_period_c6(root):
    c6_hits = []
    for path in (
        root / "adversary",
        root / "operads",
        root / "operations" / "use_cases" / "adversary_bout",
    ):
        for file in _existing_python_files(path):
            rel = file.relative_to(root).as_posix()
            if "/tests/" in rel:
                continue
            if "period(c6)" in file.read_text(encoding="utf-8", errors="replace"):
                c6_hits.append(rel)
    return c6_hits


def native_vertical_slice_gap(root, temporary):
    markers = (
        "RustSymbolGameHost",
        "CORE_SYMBOL_GAME_HOST",
        "operating_system.adapters.rust_host",
        "pfp.ffi",
        "dispatch_runtime_request",
        "evaluate_request",
    )
    scan_roots = (
        root / "adversary",
        root / "operads",
        root / "operations" / "use_cases" / "adversary_bout",
        root / "operations" / "frontend" / "api",
    )
    hits = _scan_native_markers(root, scan_roots, markers)
    reverse_hits = _scan_reverse_integer_list(root)
    c6_hits = _scan_period_c6(root)
    novelist_present = (root / "novelist").exists()
    return result(
        novelist_present and bool(hits) and bool(reverse_hits) and bool(c6_hits),
        {
            "novelist_package_present": novelist_present,
            "native_host_operational_hits": hits,
            "reverse_integer_list_operational_hits": sorted(set(reverse_hits)),
            "period_c6_operational_hits": sorted(set(c6_hits)),
            "scope": (
                "Static operational-path scan. Existing tests and verification "
                "helpers are excluded because they do not establish the production path."
            ),
        },
        positive=all(base.exists() for base in scan_roots),
        recovery=True,
    )


CASES = (
    Case("RT-INGRESS-001", "UTF-8 shared text ceiling", (
        "governance/domain/ingress/limits.py",
    ), "Refuse only inputs above the byte ceiling; subsequent bounded input works.", text_limits),
    Case("RT-INGRESS-002", "HTTP byte and encoding ceilings", (
        "operating_system/entrypoints/api.py",
        "governance/domain/ingress/http_boundary.py",
    ), "413 for oversize, 415 for encoded bodies, bounded recovery succeeds.", http_bounds),
    Case("RT-NET-001", "Legacy SBE allocation route remains removed", (
        "operating_system/entrypoints/api.py",
    ), "Return 404 without allocation while the bounded OEOS task route remains available.", sbe_allocation),
    Case("RT-NET-002", "Request cannot choose live execution mode", (
        "operating_system/entrypoints/api.py",
    ), "Refuse request-selected execution mode before any executor or provider dispatch.",
         unauthenticated_live_mode),
    Case("RT-NET-003", "Duplicate JSON action-limit keys", (
        "operating_system/entrypoints/api.py",
        "governance/domain/ingress/http_boundary.py",
    ), "Refuse ambiguous duplicate mutating keys before dispatch.", duplicate_json, "MEDIUM"),
    Case("RT-OEWAS-001", "OEWAS text boundary lacks early size refusal", (
        "operads/controllers/router.py",
        "operads/controllers/wire_dtos.py",
    ), "Refuse an oversized term at ingress before licensing work.", oewas_oversize, "MEDIUM"),
    Case("RT-OEWAS-002", "Forged actor names do not establish licensed success", (
        "operads/infrastructure/operad/higher_operad_adapter.py",
    ), "Reject unlicensed names, with a separately demonstrated licensed positive case.",
         oewas_actor_refusal, "MEDIUM"),
    Case("RT-ADVERSARY-001", "Blocking counterexample has no effect on Act V choice", (
        "adversary/use_cases/act_helpers.py",
    ), "Do not select a candidate carrying an applicable blocking counterexample.",
         terminal_selection),
    Case("RT-PERSIST-001", "Atomic persistence failure and duplicate recovery", (
        "adversary/use_cases/persistence.py",
    ), "Return a typed failure, remove partial output, recover, and preserve existing runs.",
         persistence_recovery, "MEDIUM"),
    Case("RT-INTEGRATION-001", "Missing Adversary/OEWAS/Symbol Game native vertical slice", (
        "adversary/runtime.py",
        "adversary/use_cases/bout_service.py",
        "operations/use_cases/adversary_bout/adversary_bout_use_case.py",
        "operads/controllers/router.py",
        "operads/infrastructure/bootstrap.py",
        "operating_system/adapters/rust_host/ffi.py",
        "pfp/ffi.py",
    ), "Expose an actual the novelist/OEOS/native Symbol Game path before claiming e2e integration.",
         native_vertical_slice_gap),
)

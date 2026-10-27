"""Loopback-only HTTP adapter for the governed OEOS task service.

The app is created around an injected service. It owns no live executor,
provider, credential, admission, or secret-management operation. Daemon-token
rotation and process binding are introduced in Sprint 042.

AuthorityEffect: None.
"""

from __future__ import annotations

import hmac
import re
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from governance.domain.ingress.http_boundary import (
    HttpBoundaryRefusal,
    read_request_body,
    require_local_request,
)
from governance.domain.ingress.limits import (
    REFUSAL_CONTENT_ENCODING_UNSUPPORTED,
    IngressRefusal,
)

from ..application import TaskService, TaskServiceError, TaskStoreError
from ..domain import (
    ActionLimitsV1,
    EncryptedArtifactRefV1,
    TaskEnvelopeV1,
    TaskInvariantError,
    canonical_json,
)

STATUS_TOO_LARGE = 413
STATUS_UNSUPPORTED_ENCODING = 415


def _refusal(status_code: int, code: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "authority_effect": "None",
            "refusal_code": code,
            "status": "REFUSED",
        },
    )


def _authorization_value(bearer_token: str) -> bytes:
    if (
        type(bearer_token) is not str
        or re.fullmatch(r"[A-Za-z0-9_-]{43,128}", bearer_token) is None
    ):
        raise ValueError("bearer token must contain at least 256 bits of entropy")
    try:
        token_bytes = bearer_token.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("bearer token must be ASCII") from exc
    return b"Bearer " + token_bytes


class GovernedHttpBoundaryMiddleware:
    """Authenticate a local peer before reading an unambiguous bounded body."""

    def __init__(self, app, bearer_token: str) -> None:
        self.app = app
        self._expected_authorization = _authorization_value(bearer_token)

    def _require_authentication(self, scope) -> None:
        values = [
            value
            for key, value in scope.get("headers", ())
            if key.lower() == b"authorization"
        ]
        supplied = values[0] if len(values) == 1 and isinstance(values[0], bytes) else b""
        if not hmac.compare_digest(supplied, self._expected_authorization):
            raise HttpBoundaryRefusal("OEOS_AUTHENTICATION_REQUIRED")

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        try:
            require_local_request(scope)
            self._require_authentication(scope)
            body = await read_request_body(scope, receive)
        except HttpBoundaryRefusal as exc:
            await _refusal(exc.status_code, exc.refusal_code)(scope, receive, send)
            return
        except IngressRefusal as exc:
            status = (
                STATUS_UNSUPPORTED_ENCODING
                if exc.receipt.refusal_code == REFUSAL_CONTENT_ENCODING_UNSUPPORTED
                else STATUS_TOO_LARGE
            )
            await JSONResponse(
                status_code=status,
                content={"status": "REFUSED", **exc.receipt.to_dict()},
            )(scope, receive, send)
            return

        replayed = False

        async def replay():
            nonlocal replayed
            if replayed:
                return {"type": "http.disconnect"}
            replayed = True
            return {"type": "http.request", "body": body, "more_body": False}

        await self.app(scope, replay, send)


class StrictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ActionLimitsRequest(StrictRequest):
    mutating: bool
    max_steps: int = Field(ge=1, le=1_000_000)
    max_wall_seconds: int = Field(ge=1, le=604_800)
    max_cost_microunits: int = Field(ge=0, le=10**15)


class EncryptedArtifactRefRequest(StrictRequest):
    plaintext_sha256: str
    encrypted_envelope_digest: str
    artifact_schema: str
    protector_id: str
    byte_length: int = Field(ge=0, le=(2**63) - 1)
    schema_value: str = Field(alias="schema")
    authority_effect: str

    def to_domain(self) -> EncryptedArtifactRefV1:
        return EncryptedArtifactRefV1.from_canonical(self.model_dump(by_alias=True))


class TaskSubmitRequest(StrictRequest):
    task_id: str
    idempotency_key: str
    task_family: str
    repository: str
    repository_head_sha: str
    encrypted_request_ref: EncryptedArtifactRefRequest
    requested_skills: list[str]
    action_limits: ActionLimitsRequest
    policy_digest: str

    def to_domain(self) -> TaskEnvelopeV1:
        return TaskEnvelopeV1(
            task_id=self.task_id,
            idempotency_key=self.idempotency_key,
            task_family=self.task_family,
            repository=self.repository,
            repository_head_sha=self.repository_head_sha,
            encrypted_request_ref=self.encrypted_request_ref.to_domain(),
            requested_skills=tuple(self.requested_skills),
            action_limits=ActionLimitsV1(**self.action_limits.model_dump()),
            policy_digest=self.policy_digest,
        )


class TaskInputRequest(StrictRequest):
    encrypted_input_ref: EncryptedArtifactRefRequest


class TaskOutcomeRequest(StrictRequest):
    outcome_code: str
    evidence_digest: str


def task_view(task) -> dict[str, object]:
    return {
        "authority_effect": "None",
        "cancellation_requested": task.cancellation_requested,
        "capability_snapshot_digest": task.capability_snapshot.canonical_digest,
        "chain_tip": task.chain_tip,
        "envelope_digest": task.envelope.canonical_digest,
        "state": task.state.value,
        "task_id": task.envelope.task_id,
        "version": task.version,
    }


def _safe_validation(exc: RequestValidationError) -> JSONResponse:
    errors = [
        {
            "loc": list(item.get("loc", ())),
            "msg": item.get("msg", "request validation failed"),
            "type": item.get("type", "validation_error"),
        }
        for item in exc.errors()[:16]
    ]
    return JSONResponse(
        status_code=422,
        content={"authority_effect": "None", "detail": errors, "status": "REFUSED"},
    )


def create_app(service: TaskService, *, bearer_token: str) -> FastAPI:
    """Create the one OEOS API around an already composed task service."""

    if type(service) is not TaskService:
        raise TypeError("create_app requires an exact TaskService")
    _authorization_value(bearer_token)
    app = FastAPI(
        title="Sentinel OEOS Governed Task API",
        description="Loopback task lifecycle; no policy admission or secret management",
        version="1.0.0",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.task_service = service
    app.add_middleware(GovernedHttpBoundaryMiddleware, bearer_token=bearer_token)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        del request
        return _safe_validation(exc)

    @app.exception_handler(TaskInvariantError)
    async def invariant_handler(
        request: Request, exc: TaskInvariantError
    ) -> JSONResponse:
        del request
        return _refusal(422, exc.code)

    @app.exception_handler(TaskServiceError)
    async def service_handler(request: Request, exc: TaskServiceError) -> JSONResponse:
        del request
        status = 404 if exc.code == "TASK_NOT_FOUND" else 409
        return _refusal(status, exc.code)

    @app.exception_handler(TaskStoreError)
    async def store_handler(request: Request, exc: TaskStoreError) -> JSONResponse:
        del request
        conflict = {"CONCURRENCY_CONFLICT", "IDEMPOTENCY_CONFLICT", "TASK_ID_CONFLICT"}
        return _refusal(409 if exc.code in conflict else 500, exc.code)

    @app.post("/v1/tasks", status_code=202)
    def submit_task(request: TaskSubmitRequest):
        return task_view(service.submit(request.to_domain()))

    @app.get("/v1/tasks/{task_id}")
    def get_task(task_id: str):
        return task_view(service.get(task_id))

    @app.get("/v1/tasks/{task_id}/events")
    def get_task_events(task_id: str):
        events = service.events(task_id)

        async def stream() -> AsyncIterator[bytes]:
            for event in events:
                data = canonical_json(event.to_canonical())
                yield (
                    f"id: {event.sequence}\nevent: harness_event\ndata: {data}\n\n"
                ).encode()

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-store"},
        )

    @app.post("/v1/tasks/{task_id}/input", status_code=202)
    def provide_task_input(task_id: str, request: TaskInputRequest):
        return task_view(
            service.provide_input(task_id, request.encrypted_input_ref.to_domain())
        )

    @app.post("/v1/tasks/{task_id}/cancel", status_code=202)
    def cancel_task(task_id: str):
        return task_view(service.cancel(task_id))

    @app.post("/v1/tasks/{task_id}/outcome", status_code=202)
    def record_task_outcome(task_id: str, request: TaskOutcomeRequest):
        return task_view(
            service.record_outcome(
                task_id, request.outcome_code, request.evidence_digest
            )
        )

    @app.get("/v1/capabilities")
    def get_capabilities():
        return service.capabilities().to_canonical()

    @app.get("/v1/doctor")
    def get_doctor():
        return service.doctor()

    return app


__all__ = [
    "STATUS_TOO_LARGE",
    "STATUS_UNSUPPORTED_ENCODING",
    "GovernedHttpBoundaryMiddleware",
    "create_app",
    "task_view",
]

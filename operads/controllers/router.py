"""Mountable FastAPI router at /api/oeop/v3."""

from __future__ import annotations

import hashlib

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from omega_engine_governance.domain.ingress.http_boundary import (
    HttpBoundaryRefusal,
    read_request_body,
    require_local_request,
)
from omega_engine_governance.domain.ingress.limits import (
    MAX_ADMITTED_TEXT_BYTES,
    REFUSAL_CONTENT_ENCODING_UNSUPPORTED,
    REFUSAL_TEXT_INVALID_UTF8,
    IngressRefusal,
    OversizeReceipt,
)

from .python_facade import OeopApiV3
from .wire_dtos import (
    CompileCatalogRequest,
    CompileLicensedTermRequest,
    CompileProjectionRequest,
    ValidateWorkflowsRequest,
    VerifyCatalogRequest,
)

# Only the current facade's registered terminal vocabulary crosses HTTP.
# Internal Python callers retain full typed diagnostics; unknown codes are
# deliberately not reflected merely because they look like an identifier.
_HTTP_ERROR_CODES = frozenset(
    {
        "CATALOG_LOOKUP_FAILED",
        "CATALOG_NOT_FOUND",
        "CATALOG_PERSIST_FAILED",
        "CATALOG_VERSION_LOOKUP_FAILED",
        "CONCURRENCY_CONFLICT",
        "DOCUMENT_PARSE_ERROR",
        "DOCUMENT_READ_ERROR",
        "ESTATE_LIST_FAILED",
        "IDEMPOTENCY_CONFLICT",
        "LICENSE_WITNESS_REQUIRED",
        "LOOKUP_ERROR",
        "PROJECTION_FAILED",
    }
)


class OeopIngressRoute(APIRoute):
    """Local-only, byte-bounded admission even when mounted without middleware.

    A host may add stronger authentication, but cannot omit this route envelope
    by mounting the router alone. Local admission grants no licensed authority.
    """

    async def handle(self, scope, receive, send) -> None:
        try:
            require_local_request(scope)
            body = await read_request_body(scope, receive)
        except HttpBoundaryRefusal as refusal:
            await JSONResponse(
                status_code=refusal.status_code, content=refusal.to_dict()
            )(scope, receive, send)
            return
        except IngressRefusal as refusal:
            await JSONResponse(
                status_code=(
                    415
                    if refusal.receipt.refusal_code
                    == REFUSAL_CONTENT_ENCODING_UNSUPPORTED
                    else 413
                ),
                content=refusal.receipt.to_dict(),
            )(scope, receive, send)
            return

        replayed = False

        async def replay():
            nonlocal replayed
            if replayed:
                return {"type": "http.disconnect"}
            replayed = True
            return {"type": "http.request", "body": body, "more_body": False}

        await super().handle(scope, replay, send)

    def get_route_handler(self):
        handler = super().get_route_handler()

        async def admit_request(request: Request) -> Response:
            try:
                return await handler(request)
            except IngressRefusal as refusal:
                return JSONResponse(
                    status_code=413,
                    content=refusal.receipt.to_dict(),
                )
            except RequestValidationError as invalid:
                # A default 422 reflects input and can amplify large malformed
                # fields. Keep the typed text terminal and otherwise emit only
                # a fixed code, regardless of which app mounted this router.
                for error in invalid.errors()[:16]:
                    cause = (error.get("ctx") or {}).get("error")
                    if isinstance(cause, IngressRefusal):
                        return JSONResponse(
                            status_code=413, content=cause.receipt.to_dict()
                        )
                    if error.get("type") == "string_unicode":
                        receipt = OversizeReceipt(
                            refusal_code=REFUSAL_TEXT_INVALID_UTF8,
                            limit_bytes=MAX_ADMITTED_TEXT_BYTES,
                            observed_bytes=0,
                            observed_truncated=False,
                            observed_prefix_sha256=hashlib.sha256(b"").hexdigest(),
                        )
                        return JSONResponse(status_code=413, content=receipt.to_dict())
                return JSONResponse(
                    status_code=422,
                    content={
                        "status": "REFUSED",
                        "refusal_code": "HTTP_REQUEST_VALIDATION_FAILED",
                        "authority_effect": "None",
                    },
                )

        return admit_request


def create_oeop_router(api: OeopApiV3) -> APIRouter:
    router = APIRouter(
        prefix="/api/oeop/v3", tags=["OEOP V3"], route_class=OeopIngressRoute
    )

    def _unwrap_or_raise(result):
        if result.is_err:
            err = result.unwrap_err()
            raw_code = getattr(err, "code", None)
            code = (
                raw_code
                if type(raw_code) is str
                and len(raw_code) <= 64
                and raw_code in _HTTP_ERROR_CODES
                else "OEWAS_REQUEST_FAILED"
            )
            raw_status = getattr(err, "status_code", None)
            # An error result must never become a success or redirect; bool is
            # not an HTTP status even though it is a Python int subclass.
            error_status = (
                raw_status
                if type(raw_status) is int and 400 <= raw_status <= 599
                else 500
            )
            raise HTTPException(
                status_code=error_status,
                detail={"code": code, "authority_effect": "None"},
            )
        return result.unwrap()

    @router.post("/catalogs:compile", status_code=status.HTTP_200_OK)
    @router.post("/compile_catalog", status_code=status.HTTP_200_OK)
    def compile_catalog(req: CompileCatalogRequest):
        res = api.compile_catalog(
            estate_ref=req.estate_ref,
            correlation_id=req.correlation_id,
            causation_id=req.causation_id,
            idempotency_key=req.idempotency_key,
            expected_version=req.expected_version,
        )
        return _unwrap_or_raise(res)

    @router.post("/catalogs/{catalog_id}:verify", status_code=status.HTTP_200_OK)
    def verify_catalog(catalog_id: str, req: VerifyCatalogRequest):
        res = api.verify_catalog(
            catalog_id=catalog_id,
            correlation_id=req.correlation_id,
            causation_id=req.causation_id,
        )
        return _unwrap_or_raise(res)

    @router.post(
        "/catalogs/{catalog_id}/projections:compile", status_code=status.HTTP_200_OK
    )
    def compile_projection(catalog_id: str, req: CompileProjectionRequest):
        res = api.compile_projection(
            catalog_id=catalog_id,
            target_format=req.target_format,
            correlation_id=req.correlation_id,
            causation_id=req.causation_id,
        )
        return _unwrap_or_raise(res)

    @router.post("/terms:compile", status_code=status.HTTP_200_OK)
    def compile_licensed_term(req: CompileLicensedTermRequest):
        res = api.compile_licensed_term(
            agent_id=req.agent_id,
            term_expr=req.term_expr,
            correlation_id=req.correlation_id,
            causation_id=req.causation_id,
        )
        return _unwrap_or_raise(res)

    @router.post("/workflows:validate", status_code=status.HTTP_200_OK)
    def validate_workflows(req: ValidateWorkflowsRequest):
        nodes_dict = [n.model_dump() for n in req.nodes]
        edges_dict = [e.model_dump() for e in req.edges]
        res = api.validate_workflows(nodes=nodes_dict, edges=edges_dict)
        return _unwrap_or_raise(res)

    @router.get("/catalogs/{catalog_id}", status_code=status.HTTP_200_OK)
    def get_catalog(catalog_id: str):
        res = api.get_catalog(catalog_id=catalog_id)
        cat = _unwrap_or_raise(res)
        return {
            "catalog_id": cat.catalog_id,
            "estate_ref": str(cat.estate_ref),
            "epoch": cat.epoch,
            "total_skills": cat.total_skills,
            "total_operations": cat.total_operations,
            "catalog_digest": str(cat.catalog_digest),
        }

    return router

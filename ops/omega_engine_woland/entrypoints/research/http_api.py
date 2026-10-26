"""FastAPI router for OEARS job host, provider propose shell, skeleton, digests,
literature, stage pipeline driver, and package ZIP export.

Mount on the existing web_dashboard (do not invent a second server).
AuthorityEffect: None. ACCEPT and apply remain fenced until P3-07D/P3-07A.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Any, Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field, model_validator
from starlette.requests import ClientDisconnect

from omega_engine_governance.domain.ingress.limits import (
    MAX_ADMITTED_TEXT_BYTES,
    MAX_REQUEST_BODY_BYTES,
    REFUSAL_CONTENT_ENCODING_UNSUPPORTED,
    REFUSAL_REQUEST_TOO_LARGE,
    REFUSAL_TEXT_INVALID_UTF8,
    REFUSAL_TEXT_TOO_LARGE,
    IngressRefusal,
    OversizeReceipt,
    check_content_encoding,
    check_text_bytes,
)
from omega_engine_pfp.infrastructure.task_turn import PfpTurnRefusal, complete_task_turn
from omega_engine_woland.domain.providers.types import (
    BudgetExceeded,
    CandidateRequest,
    ModelNotAllowed,
    Provider,
    ProviderConfigError,
    ProviderError,
)
from omega_engine_woland.domain.research.authorization import AuthorizationError
from omega_engine_woland.domain.research.job import JobError, JobState
from omega_engine_woland.domain.research.literature_receipt import (
    LiteratureError,
    LiteratureReceipt,
)
from omega_engine_woland.domain.research.math_skeleton import (
    extract_math_skeleton,
    skeleton_summary,
)
from omega_engine_woland.domain.research.protocols import ProposalGatewayPort


def _is_enclosing_accounted_gateway(gateway: object) -> bool:
    from omega_engine_pfp.infrastructure.estimated_gateway import (
        DurableRunGateway,
        EstimatedBudgetGateway,
    )

    if isinstance(gateway, (DurableRunGateway, EstimatedBudgetGateway)):
        return True
    return bool(getattr(gateway, "policy", None) is not None)
from omega_engine_woland.infrastructure.research.digest_store import (
    DigestStore,
    DigestStoreError,
)
from omega_engine_woland.infrastructure.research.literature_store import LiteratureStore
from omega_engine_woland.infrastructure.research.skeleton_db import (
    SkeletonDb,
    SkeletonDbError,
)
from omega_engine_woland.infrastructure.research.store import JobStore, JobStoreError
from omega_engine_woland.use_cases.research.package_digest import build_package_digest
from omega_engine_woland.use_cases.research.package_export import (
    PackageExportError,
    export_package_zip,
)
from omega_engine_woland.use_cases.research.stage_driver import StageDriverError
from omega_engine_woland.use_cases.research.stage_driver import catalog as stage_catalog

Decision = Literal["ACCEPT", "REJECT", "HOLD"]

_REFUSAL_STATUS = {REFUSAL_CONTENT_ENCODING_UNSUPPORTED: 415}

_STORE: Optional[JobStore] = None
_GATEWAY: Optional[ProposalGatewayPort] = None
_SKELETON_DB: Optional[SkeletonDb] = None
_DIGEST_STORE: Optional[DigestStore] = None
_LIT_STORE: Optional[LiteratureStore] = None


def configure_oears(
    *,
    store_root: Optional[Path | str] = None,
    gateway: Optional[ProposalGatewayPort] = None,
    skeleton_db_path: Optional[Path | str] = None,
    digest_db_path: Optional[Path | str] = None,
    literature_db_path: Optional[Path | str] = None,
) -> JobStore:
    """Configure store + gateway + skeleton/digest/literature SQLite."""
    from omega_engine_woland.runtime import wire_research_protocols

    wire_research_protocols()
    global _STORE, _GATEWAY, _SKELETON_DB, _DIGEST_STORE, _LIT_STORE
    if store_root is None:
        env = os.environ.get("OMEGA_OEARS_STORE")
        root = Path(env) if env else Path(tempfile.gettempdir()) / "omega_oears_store"
    else:
        root = Path(store_root)
    _STORE = JobStore(root)
    _GATEWAY = gateway
    _SKELETON_DB = SkeletonDb(
        Path(skeleton_db_path) if skeleton_db_path else root / "skeleton.sqlite"
    )
    _DIGEST_STORE = DigestStore(
        Path(digest_db_path) if digest_db_path else root / "digests.sqlite"
    )
    _LIT_STORE = LiteratureStore(
        Path(literature_db_path) if literature_db_path else root / "literature.sqlite"
    )
    return _STORE


def get_store() -> JobStore:
    if _STORE is None:
        configure_oears()
    if _STORE is None:
        raise ProviderConfigError("JOB_STORE_REQUIRED: configure_oears did not bind a job store")
    return _STORE


def get_gateway() -> ProposalGatewayPort:
    if _GATEWAY is None:
        raise ProviderConfigError(
            "GOVERNED_GATEWAY_REQUIRED: configure an OEOS-composed provider gateway"
        )
    if not _is_enclosing_accounted_gateway(_GATEWAY):
        raise ProviderConfigError(
            "RESEARCH_ACCOUNTED_GATEWAY_REQUIRED: configure the enclosing run's existing "
            "budgeted or accounted gateway"
        )
    return _GATEWAY


def _research_gateway_provider(value: str) -> Provider:
    """Keep explicit fixtures; live HTTP execution uses the OpenRouter gateway."""
    if value not in (Provider.FIXTURE.value, Provider.OPENROUTER.value):
        raise HTTPException(400, {
            "code": "WOLAND_EXECUTOR_RETIRED",
            "message": "Use OpenRouter (provider=openrouter) through the configured PFP gateway, "
                "or submit current-IDE proposal text with use_gateway=false. "
                "No fallback or provider substitution was attempted.",
        })
    return Provider(value)


def get_skeleton_db() -> SkeletonDb:
    if _SKELETON_DB is None:
        configure_oears()
    if _SKELETON_DB is None:
        raise ProviderConfigError("SKELETON_DB_REQUIRED: configure_oears did not bind a skeleton database")
    return _SKELETON_DB


def get_digest_store() -> DigestStore:
    if _DIGEST_STORE is None:
        configure_oears()
    if _DIGEST_STORE is None:
        raise ProviderConfigError("DIGEST_STORE_REQUIRED: configure_oears did not bind a digest store")
    return _DIGEST_STORE


def get_literature_store() -> LiteratureStore:
    if _LIT_STORE is None:
        configure_oears()
    if _LIT_STORE is None:
        raise ProviderConfigError("LITERATURE_STORE_REQUIRED: configure_oears did not bind a literature store")
    return _LIT_STORE


def _job_public(job) -> dict[str, Any]:
    d = job.to_dict()
    # Drop long history noise for list; keep for detail
    return d


def _refusal_response(receipt: OversizeReceipt) -> JSONResponse:
    return JSONResponse(
        status_code=_REFUSAL_STATUS.get(receipt.refusal_code, 413),
        content={"status": "REFUSED", **receipt.to_dict()},
    )


def _request_receipt(prefix: bytes, *, observed_truncated: bool) -> OversizeReceipt:
    return OversizeReceipt(
        refusal_code=REFUSAL_REQUEST_TOO_LARGE,
        limit_bytes=MAX_REQUEST_BODY_BYTES,
        observed_bytes=len(prefix),
        observed_truncated=observed_truncated,
        observed_prefix_sha256=hashlib.sha256(prefix).hexdigest(),
    )


def _raw_header_values(request: Request, name: bytes) -> list[str]:
    return [
        value.decode("latin-1")
        for key, value in request.scope.get("headers", ())
        if key.lower() == name
    ]


def _validation_response(exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    for error in errors:
        cause = error.get("ctx", {}).get("error")
        if isinstance(cause, IngressRefusal):
            return _refusal_response(cause.receipt)
        if error.get("type") == "string_unicode":
            return _refusal_response(
                OversizeReceipt(
                    refusal_code=REFUSAL_TEXT_INVALID_UTF8,
                    limit_bytes=MAX_ADMITTED_TEXT_BYTES,
                    observed_bytes=0,
                    observed_truncated=False,
                    observed_prefix_sha256=hashlib.sha256(b"").hexdigest(),
                )
            )
    return JSONResponse(
        status_code=422,
        content={
            "detail": [
                {
                    "loc": list(error.get("loc", ())),
                    "type": error.get("type", "validation_error"),
                    "msg": error.get("msg", "request validation failed"),
                }
                for error in errors[:16]
            ],
            "authority_effect": "None",
        },
    )


class BoundedOearsRoute(APIRoute):
    """Apply body/text ceilings even when this router is mounted bare."""

    def get_route_handler(self):
        route_handler = super().get_route_handler()

        async def bounded_route_handler(request: Request):
            try:
                encodings = _raw_header_values(request, b"content-encoding")
                check_content_encoding(",".join(encodings) if encodings else None)

                for value in request.path_params.values():
                    if isinstance(value, str):
                        check_text_bytes(
                            value,
                            limit=MAX_ADMITTED_TEXT_BYTES,
                            refusal_code=REFUSAL_TEXT_TOO_LARGE,
                        )
                for _, value in request.query_params.multi_items():
                    check_text_bytes(
                        value,
                        limit=MAX_ADMITTED_TEXT_BYTES,
                        refusal_code=REFUSAL_TEXT_TOO_LARGE,
                    )

                declared_values = _raw_header_values(request, b"content-length")
                if len(declared_values) == 1:
                    try:
                        declared = int(declared_values[0])
                    except ValueError:
                        declared = None
                    if declared is not None and declared > MAX_REQUEST_BODY_BYTES:
                        return _refusal_response(
                            _request_receipt(b"", observed_truncated=False)
                        )

                body = bytearray()
                stream = request.stream()
                try:
                    async for chunk in stream:
                        remaining = (MAX_REQUEST_BODY_BYTES + 1) - len(body)
                        if remaining > 0:
                            body.extend(chunk[:remaining])
                        if len(body) > MAX_REQUEST_BODY_BYTES:
                            return _refusal_response(
                                _request_receipt(
                                    bytes(body), observed_truncated=True
                                )
                            )
                except ClientDisconnect:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "status": "REFUSED",
                            "detail": "request body disconnected before completion",
                            "authority_effect": "None",
                        },
                    )
                finally:
                    close = getattr(stream, "aclose", None)
                    if callable(close):
                        await close()

                # Starlette's body parser sees the bounded copy, not the
                # already-consumed network stream.
                request._body = bytes(body)
                return await route_handler(request)
            except IngressRefusal as refusal:
                return _refusal_response(refusal.receipt)
            except RequestValidationError as exc:
                return _validation_response(exc)

        return bounded_route_handler


def _check_nested_text(value: Any) -> None:
    if isinstance(value, str):
        check_text_bytes(
            value,
            limit=MAX_ADMITTED_TEXT_BYTES,
            refusal_code=REFUSAL_TEXT_TOO_LARGE,
        )
    elif isinstance(value, dict):
        for nested in value.values():
            _check_nested_text(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _check_nested_text(nested)


class BoundedTextBody(BaseModel):
    """Validate every caller-supplied string before a DTO can reach work."""

    @model_validator(mode="before")
    @classmethod
    def _bound_all_text(cls, value: Any) -> Any:
        _check_nested_text(value)
        return value


class CreateJobBody(BoundedTextBody):
    operator_id: str = Field(..., min_length=1)
    paper_stem: str = Field(default="demo_paper", min_length=1)
    paper_root: str = ""
    seed_markdown: str = "# Demo paper\n\nbody\n"


class ProposeBody(BoundedTextBody):
    proposal_text: str = Field(..., min_length=1)
    use_gateway: bool = False
    provider: str = "fixture"
    model: str = ""
    system_prompt: str = (
        "You propose residual-honest paper edits. Do not claim GlobalGreen."
    )


class AuthorizeBody(BoundedTextBody):
    operator_id: str = Field(..., min_length=1)
    decision: Decision
    note: str = ""


class ApplyBody(BoundedTextBody):
    relative_path: str = Field(..., min_length=1)
    new_content: str


class CandidateBody(BoundedTextBody):
    system: str = "You propose residual-honest paper edits."
    user: str = Field(..., min_length=1)
    provider: str = "fixture"
    model: str = ""


class ExtractSkeletonBody(BoundedTextBody):
    text: str = Field(..., min_length=1)
    source_path: str = ""


class IndexSkeletonBody(BoundedTextBody):
    package_id: str = Field(..., min_length=1)
    paper_root: str = Field(..., min_length=1)
    paper_stem: str = ""


class SearchSkeletonBody(BoundedTextBody):
    query: str = Field(..., min_length=1)
    package_id: str = ""
    limit: int = Field(default=20, ge=1, le=200)


class DigestIndexBody(BoundedTextBody):
    package_id: str = Field(..., min_length=1)
    paper_root: str = Field(..., min_length=1)
    paper_stem: str = ""
    max_total_chars: int = Field(default=12_000, ge=200, le=200_000)


class LiteratureBody(BoundedTextBody):
    package_id: str = Field(..., min_length=1)
    cite_key: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    authors: str = ""
    year: str = ""
    venue: str = ""
    arxiv_id: str = ""
    doi: str = ""
    url: str = ""
    binding_note: str = ""
    source_kind: str = "manual"


class BeginStageBody(BoundedTextBody):
    stage_id: str = ""
    note: str = ""


class CompleteStageBody(BoundedTextBody):
    stage_id: str = ""
    result_token: str = "STAGE_COMPLETED"
    residual_open_ids: list[str] = Field(default_factory=list)
    note: str = ""
    status: str = "COMPLETED"


class AdvancePipelineBody(BoundedTextBody):
    complete_current: bool = True
    result_token: str = "STAGE_COMPLETED"
    residual_open_ids: list[str] = Field(default_factory=list)
    note: str = ""


class ExportZipBody(BoundedTextBody):
    paper_root: str = Field(..., min_length=1)
    package_id: str = ""
    paper_stem: str = ""
    dest_name: str = ""


def create_research_router() -> APIRouter:
    router = APIRouter(
        prefix="/api/woland/research", tags=["woland-research"], route_class=BoundedOearsRoute
    )

    @router.get("/health")
    def health() -> dict[str, Any]:
        store = get_store()
        sdb = get_skeleton_db()
        return {
            "ok": True,
            "service": "woland-research",
            "sprint": "sprint-ort-oears-v1-s8",
            "epic": "EPIC-ORT-OEARS-V1",
            "store_root": str(store.root),
            "skeleton_db": str(sdb.path),
            "digest_db": str(get_digest_store().path),
            "literature_db": str(get_literature_store().path),
            "features": [
                "jobs",
                "providers",
                "http",
                "math_skeleton",
                "sqlite_fts",
                "package_digest",
                "literature_receipts",
                "stage_pipeline",
                "package_zip_export",
                "dashboard_authorize_download",
                "soviet_estate_runbook_inventory",
            ],
            "authority_effect": "None",
            "claims_global_green": False,
            "law": (
                "Agents propose via gateway; humans authorize apply; "
                "budget/allowlist admit before dispatch; "
                "skeleton/digest not ranking proof; literature bindings only; "
                "stage driver records receipts only; ZIP is snapshot not promotion; "
                "dashboard surfaces gates without minting authority; "
                "S8 freezes estate tests + operator runbook + inventory SSOT"
            ),
        }

    @router.post("/jobs")
    def create_job(body: CreateJobBody) -> dict[str, Any]:
        store = get_store()
        try:
            if body.paper_root.strip():
                paper_root = Path(body.paper_root)
                if not paper_root.is_dir():
                    raise HTTPException(
                        400, f"paper_root not a directory: {paper_root}"
                    )
            else:
                # Sandbox package under store for UI demos
                paper_root = (
                    store.root / "sandboxes" / f"{body.paper_stem}_{os.getpid()}"
                )
                paper_root.mkdir(parents=True, exist_ok=True)
                md = paper_root / f"{body.paper_stem}.md"
                if not md.is_file():
                    md.write_text(body.seed_markdown, encoding="utf-8")
            job = store.create_job(
                operator_id=body.operator_id,
                paper_stem=body.paper_stem,
                paper_root=paper_root,
            )
            return {"job": _job_public(job), "authority_effect": "None"}
        except JobStoreError as e:
            raise HTTPException(400, str(e)) from e
        except JobError as e:
            raise HTTPException(400, str(e)) from e

    @router.get("/jobs")
    def list_jobs() -> dict[str, Any]:
        """Dashboard job picker (S7)."""
        rows = get_store().list_jobs()
        return {
            "jobs": rows,
            "count": len(rows),
            "authority_effect": "None",
        }

    @router.get("/jobs/{job_id}")
    def get_job(job_id: str) -> dict[str, Any]:
        try:
            job = get_store().load_job(job_id)
            return {"job": _job_public(job), "authority_effect": "None"}
        except JobStoreError as e:
            raise HTTPException(404, str(e)) from e

    @router.get("/jobs/{job_id}/dashboard")
    def job_dashboard(job_id: str) -> dict[str, Any]:
        """Aggregated authorize + download UI state (S7)."""
        try:
            return get_store().dashboard_state(job_id)
        except JobStoreError as e:
            raise HTTPException(404, str(e)) from e

    @router.get("/jobs/{job_id}/proposal")
    def job_proposal(job_id: str) -> dict[str, Any]:
        try:
            job = get_store().load_job(job_id)
            text = get_store().load_proposal_text(job_id)
            return {
                "job_id": job_id,
                "state": job.state.value,
                "proposal_hash": job.proposal_hash,
                "proposal_text": text,
                "present": bool(text) or bool(job.proposal_hash),
                "authority_effect": "None",
                "note": "Proposal is unverified candidate text until human ACCEPT.",
            }
        except JobStoreError as e:
            raise HTTPException(404, str(e)) from e

    @router.get("/jobs/{job_id}/export/meta")
    def job_export_meta(job_id: str) -> dict[str, Any]:
        try:
            get_store().load_job(job_id)
            meta = get_store().latest_export_meta(job_id)
            if not meta:
                raise HTTPException(404, "no export meta; POST .../export/zip first")
            return {
                "job_id": job_id,
                "export": meta,
                "download_path": f"/api/woland/research/jobs/{job_id}/export/download",
                "authority_effect": "None",
            }
        except JobStoreError as e:
            raise HTTPException(404, str(e)) from e

    @router.post("/jobs/{job_id}/qualify")
    def qualify(job_id: str) -> dict[str, Any]:
        try:
            job = get_store().qualify(job_id)
            return {"job": _job_public(job)}
        except (JobStoreError, JobError) as e:
            raise HTTPException(400, str(e)) from e

    @router.post("/jobs/{job_id}/freeze")
    def freeze(job_id: str, freeze_note: str = "ui freeze") -> dict[str, Any]:
        try:
            job = get_store().freeze(job_id, freeze_note=freeze_note)
            return {"job": _job_public(job), "pre_tree_hash": job.pre_tree_hash}
        except (JobStoreError, JobError) as e:
            raise HTTPException(400, str(e)) from e

    @router.post("/jobs/{job_id}/start_stage")
    def start_stage(job_id: str, stage_id: str = "stage_1_improver") -> dict[str, Any]:
        try:
            job = get_store().start_stage(job_id, stage_id)
            return {"job": _job_public(job)}
        except (JobStoreError, JobError) as e:
            raise HTTPException(400, str(e)) from e

    @router.post("/jobs/{job_id}/propose")
    def propose(job_id: str, body: ProposeBody) -> dict[str, Any]:
        store = get_store()
        try:
            prov = _research_gateway_provider(body.provider) if body.use_gateway else None
            gw = get_gateway() if body.use_gateway else None
            job = store.load_job(job_id)
            # Ensure RUNNING
            if job.state == JobState.DRAFT:
                store.qualify(job_id)
                store.freeze(job_id)
                store.start_stage(job_id, "stage_1_improver")
            elif job.state == JobState.QUALIFIED:
                store.freeze(job_id)
                store.start_stage(job_id, "stage_1_improver")
            elif job.state == JobState.FROZEN:
                store.start_stage(job_id, "stage_1_improver")

            proposal_text = body.proposal_text
            gateway_meta: dict[str, Any] = {}
            if body.use_gateway:
                model = body.model or None
                cand, receipt, pfp = complete_task_turn(gw,
                    CandidateRequest(
                        system=body.system_prompt, user=body.proposal_text
                    ),
                    task_id=f"research-proposal:{job_id}",
                    attempt_id=uuid4().hex,
                    provider=prov,
                    model=model,
                )
                proposal_text = cand.content
                gateway_meta = {
                    "provider": cand.provider,
                    "model": cand.model,
                    "transport": cand.transport,
                    "budget_receipt": receipt.to_dict() if receipt else None,
                    "pfp": pfp,
                }

            job = store.propose_text(job_id, proposal_text)
            return {
                "job": _job_public(job),
                "proposal_text": proposal_text,
                "gateway": gateway_meta,
                "authority_effect": "None",
            }
        except PfpTurnRefusal as e:
            raise HTTPException(400, {"code": e.code, "pfp": e.checked,
                "budget_receipt": e.budget_receipt.to_dict() if e.budget_receipt else None}) from e
        except (
            JobStoreError,
            JobError,
            ProviderError,
            ModelNotAllowed,
            BudgetExceeded,
        ) as e:
            raise HTTPException(400, str(e)) from e
        except ValueError as e:
            raise HTTPException(400, str(e)) from e

    @router.post("/jobs/{job_id}/authorize")
    def authorize(job_id: str, body: AuthorizeBody) -> dict[str, Any]:
        try:
            job, rec = get_store().authorize(
                job_id,
                operator_id=body.operator_id,
                decision=body.decision,
                note=body.note,
            )
            return {
                "job": _job_public(job),
                "receipt": rec.to_dict(),
                "authority_effect": "None",
            }
        except AuthorizationError as e:
            raise HTTPException(403, str(e)) from e
        except (JobStoreError, JobError) as e:
            raise HTTPException(400, str(e)) from e

    @router.post("/jobs/{job_id}/apply")
    def apply(job_id: str, body: ApplyBody) -> dict[str, Any]:
        try:
            job, snap = get_store().apply_authorized_mutation(
                job_id,
                relative_path=body.relative_path,
                new_content=body.new_content,
            )
            return {
                "job": _job_public(job),
                "snapshot": snap.to_dict(),
                "authority_effect": "None",
            }
        except (JobStoreError, JobError) as e:
            raise HTTPException(400, str(e)) from e

    @router.post("/jobs/{job_id}/undo")
    def undo(job_id: str) -> dict[str, Any]:
        try:
            job = get_store().undo(job_id)
            return {"job": _job_public(job), "authority_effect": "None"}
        except (JobStoreError, JobError) as e:
            raise HTTPException(400, str(e)) from e

    @router.post("/candidate")
    def candidate(body: CandidateBody) -> dict[str, Any]:
        """Prompt UI shell: admit + fixture (or configured) gateway complete only."""
        try:
            prov = _research_gateway_provider(body.provider)
            gw = get_gateway()
            cand, receipt, pfp = complete_task_turn(gw,
                CandidateRequest(system=body.system, user=body.user),
                task_id="research-ui-candidate",
                attempt_id=uuid4().hex,
                provider=prov,
                model=body.model or None,
            )
            return {
                "candidate": {
                    "content": cand.content,
                    "model": cand.model,
                    "provider": cand.provider,
                    "transport": cand.transport,
                    "authority_effect": cand.authority_effect,
                    "claims_global_green": cand.claims_global_green,
                },
                "budget_receipt": receipt.to_dict() if receipt else None,
                "pfp": pfp,
                "authority_effect": "None",
            }
        except PfpTurnRefusal as e:
            raise HTTPException(400, {"code": e.code, "pfp": e.checked,
                "budget_receipt": e.budget_receipt.to_dict() if e.budget_receipt else None}) from e
        except (ProviderError, ModelNotAllowed, BudgetExceeded, ValueError) as e:
            raise HTTPException(400, str(e)) from e

    # --- S4 math skeleton + SQLite ---

    @router.post("/skeleton/extract")
    def skeleton_extract(body: ExtractSkeletonBody) -> dict[str, Any]:
        nodes = extract_math_skeleton(body.text, source_path=body.source_path)
        return {
            "nodes": [n.to_dict() for n in nodes],
            "summary": skeleton_summary(nodes),
            "authority_effect": "None",
        }

    @router.post("/skeleton/index")
    def skeleton_index(body: IndexSkeletonBody) -> dict[str, Any]:
        try:
            result = get_skeleton_db().index_package(
                package_id=body.package_id,
                paper_root=body.paper_root,
                paper_stem=body.paper_stem,
            )
            return result
        except SkeletonDbError as e:
            raise HTTPException(400, str(e)) from e
        except ValueError as e:
            raise HTTPException(400, str(e)) from e

    @router.post("/skeleton/search")
    def skeleton_search(body: SearchSkeletonBody) -> dict[str, Any]:
        try:
            hits = get_skeleton_db().search(
                body.query,
                package_id=body.package_id or None,
                limit=body.limit,
            )
            return {
                "query": body.query,
                "hits": hits,
                "count": len(hits),
                "authority_effect": "None",
                "note": "FTS order is not relevance ranking authority",
            }
        except SkeletonDbError as e:
            raise HTTPException(400, str(e)) from e

    @router.get("/skeleton/packages/{package_id}")
    def skeleton_package(package_id: str) -> dict[str, Any]:
        meta = get_skeleton_db().get_package(package_id)
        if not meta:
            raise HTTPException(404, f"package not indexed: {package_id}")
        nodes = get_skeleton_db().list_nodes(package_id)
        return {
            "package": meta,
            "nodes": nodes,
            "authority_effect": "None",
        }

    @router.post("/jobs/{job_id}/skeleton/index")
    def job_skeleton_index(job_id: str) -> dict[str, Any]:
        """Index math skeleton for a job's paper_root into SQLite."""
        try:
            job = get_store().load_job(job_id)
            result = get_skeleton_db().index_package(
                package_id=job.job_id,
                paper_root=job.paper_root,
                paper_stem=job.paper_stem,
            )
            return {"job_id": job_id, "index": result, "authority_effect": "None"}
        except JobStoreError as e:
            raise HTTPException(404, str(e)) from e
        except (SkeletonDbError, ValueError) as e:
            raise HTTPException(400, str(e)) from e

    @router.post("/digest/build")
    def digest_build(body: DigestIndexBody) -> dict[str, Any]:
        try:
            dig = build_package_digest(
                package_id=body.package_id,
                paper_root=body.paper_root,
                paper_stem=body.paper_stem,
                max_total_chars=body.max_total_chars,
            )
            return get_digest_store().put(dig)
        except (DigestStoreError, ValueError) as e:
            raise HTTPException(400, str(e)) from e

    @router.get("/digest/packages/{package_id}")
    def digest_get(package_id: str) -> dict[str, Any]:
        row = get_digest_store().get(package_id)
        if not row:
            raise HTTPException(404, f"digest not found: {package_id}")
        return row

    @router.post("/jobs/{job_id}/digest/build")
    def job_digest_build(job_id: str, max_total_chars: int = 12_000) -> dict[str, Any]:
        try:
            job = get_store().load_job(job_id)
            result = get_digest_store().index_package(
                package_id=job.job_id,
                paper_root=job.paper_root,
                paper_stem=job.paper_stem,
                max_total_chars=max_total_chars,
            )
            return {"job_id": job_id, "digest": result, "authority_effect": "None"}
        except JobStoreError as e:
            raise HTTPException(404, str(e)) from e
        except (DigestStoreError, ValueError) as e:
            raise HTTPException(400, str(e)) from e

    @router.post("/literature/receipts")
    def literature_put(body: LiteratureBody) -> dict[str, Any]:
        try:
            rec = LiteratureReceipt.issue(
                package_id=body.package_id,
                cite_key=body.cite_key,
                title=body.title,
                authors=body.authors,
                year=body.year,
                venue=body.venue,
                arxiv_id=body.arxiv_id,
                doi=body.doi,
                url=body.url,
                binding_note=body.binding_note,
                source_kind=body.source_kind,  # type: ignore[arg-type]
            )
            get_literature_store().put(rec)
            return {"receipt": rec.to_dict(), "authority_effect": "None"}
        except LiteratureError as e:
            raise HTTPException(400, str(e)) from e

    @router.get("/literature/packages/{package_id}")
    def literature_list(package_id: str) -> dict[str, Any]:
        try:
            rows = get_literature_store().list_for_package(package_id)
            return {
                "package_id": package_id,
                "receipts": rows,
                "count": len(rows),
                "authority_effect": "None",
            }
        except LiteratureError as e:
            raise HTTPException(400, str(e)) from e

    # --- S6 stage pipeline + ZIP export ---

    @router.get("/stages/catalog")
    def stages_catalog() -> dict[str, Any]:
        return {
            "stages": stage_catalog(),
            "count": len(stage_catalog()),
            "authority_effect": "None",
            "note": "Catalog binds skill_ids; driver does not execute panels.",
        }

    @router.get("/jobs/{job_id}/pipeline")
    def job_pipeline(job_id: str) -> dict[str, Any]:
        try:
            status = get_store().pipeline_status(job_id)
            receipts = get_store().stage_driver(job_id).list_receipts()
            return {
                "job_id": job_id,
                "pipeline": status,
                "receipts": receipts,
                "authority_effect": "None",
            }
        except JobStoreError as e:
            raise HTTPException(404, str(e)) from e

    @router.post("/jobs/{job_id}/pipeline/begin")
    def job_pipeline_begin(job_id: str, body: BeginStageBody) -> dict[str, Any]:
        try:
            job, receipt, status = get_store().begin_pipeline_stage(
                job_id, body.stage_id, note=body.note
            )
            return {
                "job": _job_public(job),
                "receipt": receipt.to_dict(),
                "pipeline": status,
                "authority_effect": "None",
            }
        except JobStoreError as e:
            raise HTTPException(
                404 if "not found" in str(e).lower() else 400, str(e)
            ) from e
        except (JobError, StageDriverError) as e:
            raise HTTPException(400, str(e)) from e

    @router.post("/jobs/{job_id}/pipeline/complete_stage")
    def job_pipeline_complete(job_id: str, body: CompleteStageBody) -> dict[str, Any]:
        try:
            job, receipt, status = get_store().complete_pipeline_stage(
                job_id,
                stage_id=body.stage_id,
                result_token=body.result_token,
                residual_open_ids=body.residual_open_ids,
                note=body.note,
                status=body.status,
            )
            return {
                "job": _job_public(job),
                "receipt": receipt.to_dict(),
                "pipeline": status,
                "authority_effect": "None",
            }
        except JobStoreError as e:
            raise HTTPException(
                404 if "not found" in str(e).lower() else 400, str(e)
            ) from e
        except (JobError, StageDriverError) as e:
            raise HTTPException(400, str(e)) from e

    @router.post("/jobs/{job_id}/pipeline/advance")
    def job_pipeline_advance(job_id: str, body: AdvancePipelineBody) -> dict[str, Any]:
        try:
            job, status = get_store().advance_pipeline(
                job_id,
                complete_current=body.complete_current,
                result_token=body.result_token,
                residual_open_ids=body.residual_open_ids,
                note=body.note,
            )
            return {
                "job": _job_public(job),
                "pipeline": status,
                "authority_effect": "None",
            }
        except JobStoreError as e:
            raise HTTPException(
                404 if "not found" in str(e).lower() else 400, str(e)
            ) from e
        except (JobError, StageDriverError) as e:
            raise HTTPException(400, str(e)) from e

    @router.post("/export/zip")
    def export_zip(body: ExportZipBody) -> dict[str, Any]:
        root = Path(body.paper_root)
        if not root.is_dir():
            raise HTTPException(400, f"paper_root not a directory: {root}")
        store = get_store()
        out_dir = store.root / "exports"
        out_dir.mkdir(parents=True, exist_ok=True)
        name = body.dest_name.strip() or f"{body.package_id or root.name}_package.zip"
        if not name.endswith(".zip"):
            name += ".zip"
        dest = out_dir / name
        try:
            receipt = export_package_zip(
                paper_root=root,
                dest_zip=dest,
                package_id=body.package_id or root.name,
                paper_stem=body.paper_stem or root.name,
            )
            return {"export": receipt.to_dict(), "authority_effect": "None"}
        except PackageExportError as e:
            raise HTTPException(400, str(e)) from e

    @router.post("/jobs/{job_id}/export/zip")
    def job_export_zip(job_id: str) -> dict[str, Any]:
        try:
            job, receipt = get_store().export_job_zip(job_id)
            return {
                "job_id": job.job_id,
                "export": receipt.to_dict(),
                "download_path": f"/api/woland/research/jobs/{job_id}/export/download",
                "authority_effect": "None",
            }
        except JobStoreError as e:
            raise HTTPException(
                404 if "not found" in str(e).lower() else 400, str(e)
            ) from e

    @router.get("/jobs/{job_id}/export/download")
    def job_export_download(job_id: str):
        """Stream the latest ZIP for a job (if export was built)."""
        try:
            store = get_store()
            store.load_job(job_id)  # existence
            exp_dir = store.job_dir(job_id) / "exports"
            zips = sorted(exp_dir.glob("*.zip"), key=lambda p: p.stat().st_mtime)
            if not zips:
                raise HTTPException(404, "no export zip; POST .../export/zip first")
            latest = zips[-1]
            return FileResponse(
                path=str(latest),
                media_type="application/zip",
                filename=latest.name,
            )
        except JobStoreError as e:
            raise HTTPException(404, str(e)) from e

    return router

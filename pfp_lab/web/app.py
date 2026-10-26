"""HTTP API and static page for running scenarios in a browser.

AuthorityEffect: None.
Contract: urn:pfp-lab:web:app:v1

The API is stateless: every request carries its whole scenario or receipt, so
there is no session store to bound or clean up. Request bodies are read in
chunks and refused past ``MAX_JSON_BYTES`` before parsing, then admitted with
the same strict models as the CLI (RULE_PY_001).

====================  ======  ===========================================
path                  method  result
====================  ======  ===========================================
``/api/version``      GET     ``{version, authority_effect}``
``/api/packs``        GET     ``{packs: [PackSummary]}``
``/api/packs/{id}``   GET     Scenario, or 404 ``UNKNOWN_PACK``
``/api/run``          POST    Receipt; 413 oversize, 422 ``ADMISSION`` or
                              ``BUDGET_EXCEEDED``
``/api/verify``       POST    VerifyReport; 413, 422 as above
====================  ======  ===========================================

``pfp-lab-web`` (``main`` below) binds to 127.0.0.1 by default. A non-loopback
host is refused with exit code 2 unless ``--allow-remote`` is given, because
the API has no authentication: it is a local tool.
"""

from __future__ import annotations

import argparse
import ipaddress
import sys
from collections.abc import Sequence
from importlib.resources import files
from typing import Literal, TextIO

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import ValidationError

from pfp_lab.core.admission import AdmissionError, BudgetExceededError, ErrorCode, UnknownPackError
from pfp_lab.core.contracts import (
    CORE_VERSION,
    MAX_JSON_BYTES,
    PackSummary,
    ScenarioIn,
    Strict,
    admit_json,
    get_pack,
    list_packs,
)
from pfp_lab.core.session import ReceiptOut, VerifyReport, build_receipt, run_scenario, verify_receipt

STATIC = files("pfp_lab.web") / "static"
ASSETS: dict[str, str] = {
    "app.js": "text/javascript; charset=utf-8",
    "app.css": "text/css; charset=utf-8",
}


class VersionOut(Strict):
    version: str
    authority_effect: Literal["None"]


class PacksOut(Strict):
    packs: tuple[PackSummary, ...]


class OversizeError(Exception):
    """The request body passed the byte limit."""


async def read_capped(request: Request) -> bytes:
    """The request body, refused as soon as it passes ``MAX_JSON_BYTES``."""
    chunks: list[bytes] = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_JSON_BYTES:
            raise OversizeError
        chunks.append(chunk)
    return b"".join(chunks)


def problem(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"code": code, "message": message})


def create_app() -> FastAPI:
    """Build the app; no state is shared between requests."""
    app = FastAPI(title="PFP Lab", version=CORE_VERSION, docs_url=None, redoc_url=None)

    @app.exception_handler(OversizeError)
    async def _oversize(_: Request, __: Exception) -> JSONResponse:
        return problem(413, ErrorCode.ADMISSION, f"request body exceeds {MAX_JSON_BYTES} bytes")

    @app.exception_handler(ValidationError)
    async def _invalid(_: Request, error: Exception) -> JSONResponse:
        count = error.error_count() if isinstance(error, ValidationError) else 1
        return problem(422, ErrorCode.ADMISSION, f"input refused: {count} problem(s): {error}")

    @app.exception_handler(AdmissionError)
    async def _refused(_: Request, error: Exception) -> JSONResponse:
        return problem(422, ErrorCode.ADMISSION, str(error))

    @app.exception_handler(BudgetExceededError)
    async def _budget(_: Request, error: Exception) -> JSONResponse:
        return problem(422, ErrorCode.BUDGET_EXCEEDED, str(error))

    @app.exception_handler(UnknownPackError)
    async def _unknown(_: Request, error: Exception) -> JSONResponse:
        return problem(404, ErrorCode.UNKNOWN_PACK, str(error))

    @app.get("/api/version")
    def version() -> VersionOut:
        return VersionOut(version=CORE_VERSION, authority_effect="None")

    @app.get("/api/packs")
    def packs() -> PacksOut:
        return PacksOut(packs=list_packs())

    @app.get("/api/packs/{pack_id}")
    def pack(pack_id: str) -> Response:
        body = get_pack(pack_id).model_dump_json(by_alias=True)
        return Response(content=body, media_type="application/json")

    @app.post("/api/run")
    async def run(request: Request) -> Response:
        scenario = admit_json(ScenarioIn, await read_capped(request))
        receipt = build_receipt(run_scenario(scenario))
        return Response(content=receipt.model_dump_json(by_alias=True), media_type="application/json")

    @app.post("/api/verify")
    async def verify(request: Request) -> VerifyReport:
        return verify_receipt(admit_json(ReceiptOut, await read_capped(request)))

    @app.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        return HTMLResponse((STATIC / "index.html").read_text(encoding="utf-8"))

    @app.get("/static/{name}")
    def asset(name: str) -> Response:
        media_type = ASSETS.get(name)
        if media_type is None:
            return problem(404, "NOT_FOUND", f"no asset named {name!r}")
        return Response(content=(STATIC / name).read_text(encoding="utf-8"), media_type=media_type)

    return app


DEFAULT_PORT = 8765
REFUSED = 2


def is_loopback(host: str) -> bool:
    """True for ``localhost`` and every loopback IPv4 or IPv6 literal."""
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host.strip("[]")).is_loopback
    except ValueError:
        return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pfp-lab-web", description="Serve the PFP Lab web page.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--allow-remote", action="store_true", help="permit a non-loopback host")
    return parser


def check_bind(args: argparse.Namespace, err: TextIO) -> bool:
    """Refuse a non-loopback host unless remote binding was asked for explicitly."""
    if is_loopback(args.host) or args.allow_remote:
        return True
    err.write(f"pfp-lab-web: refusing to bind {args.host}; pass --allow-remote to serve beyond this machine\n")
    return False


def main(argv: Sequence[str] | None = None, err: TextIO | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not check_bind(args, err if err is not None else sys.stderr):
        return REFUSED
    uvicorn.run(create_app(), host=args.host, port=args.port, log_level="warning")
    return 0


def entry() -> None:
    sys.exit(main())


__all__ = ["DEFAULT_PORT", "check_bind", "create_app", "entry", "is_loopback", "main", "read_capped"]

if __name__ == "__main__":
    entry()

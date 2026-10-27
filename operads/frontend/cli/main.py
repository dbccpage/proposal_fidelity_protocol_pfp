"""Main CLI entry point for Engine Operads commands."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import List, Optional

from ...application.governance_digest.apply_proposals import apply_proposals, proposals_from_receipt
from ...application.governance_digest.digest_corpus import canonical_json, digest_corpus
from ...application.governance_digest.receipt_path import write_receipt
from ...application.governance_digest.repairs import live_repairs
from ...infrastructure.bootstrap import OeopContainer
from ...infrastructure.fs.governance_corpus_adapter import FsGovernanceCorpusAdapter, FsTextStore


def _configure_encoding() -> None:
    """Guard console stdout and stderr against Windows CP1252 character crash."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oeop",
        description="OEOP: Engine Operads CLI",
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default=".",
        help="Workspace root path",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=":memory:",
        help="SQLite database path",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Format stdout output as structured JSON",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    dispatch = subparsers.add_parser("dispatch-events", help="Deliver pending events to an authenticated receipt ledger")
    dispatch.add_argument("--tip-path", type=Path, required=True)
    dispatch.add_argument("--tip-key-file", type=Path, required=True, help="Operator-owned binary HMAC key, at least 32 bytes")
    dispatch.add_argument("--ledger-id", required=True)
    dispatch.add_argument("--worker-id")
    dispatch.add_argument("--limit", type=int, default=100)

    # compile-catalog
    compile_cat_p = subparsers.add_parser("compile-catalog", help="Compile estate catalog into SQLite WAL engine")
    compile_cat_p.add_argument("--estate", type=str, default="canonical", help="Estate reference name")
    compile_cat_p.add_argument("--idempotency-key", type=str, default=None, help="Optional idempotency key")
    compile_cat_p.add_argument("--correlation-id", type=str, default="cli-req-001", help="Correlation ID")
    compile_cat_p.add_argument("--causation-id", type=str, default="cli-init", help="Causation ID")

    # verify-catalog
    verify_cat_p = subparsers.add_parser("verify-catalog", help="Verify integrity of compiled catalog")
    verify_cat_p.add_argument("catalog_id", type=str, help="Catalog ID to verify")
    verify_cat_p.add_argument("--correlation-id", type=str, default="cli-req-001", help="Correlation ID")
    verify_cat_p.add_argument("--causation-id", type=str, default="cli-init", help="Causation ID")

    # compile-projection
    proj_p = subparsers.add_parser("compile-projection", help="Emit projection manifest")
    proj_p.add_argument("catalog_id", type=str, help="Catalog ID")
    proj_p.add_argument("--format", type=str, default="yaml", help="Target format (yaml, json, markdown)")
    proj_p.add_argument("--correlation-id", type=str, default="cli-req-001", help="Correlation ID")
    proj_p.add_argument("--causation-id", type=str, default="cli-init", help="Causation ID")

    digest_p = subparsers.add_parser(
        "digest-governance",
        help="Read governance corpora and emit a proposal receipt. Writes nothing in the corpora.",
    )
    digest_p.add_argument("--out", type=str, default="", help="Receipt path. Refuses .agents and _intelligence.")

    apply_p = subparsers.add_parser(
        "apply-governance-proposals",
        help="Apply a digest receipt's proposals when they match the checked-in repairs.",
    )
    apply_p.add_argument("--receipt", type=str, required=True, help="Digest receipt JSON")
    apply_p.add_argument("--out", type=str, default="", help="Apply-receipt path. Refuses .agents and _intelligence.")

    return parser


def _emit(payload: dict, out: str, as_json: bool) -> int:
    text = canonical_json(payload)
    if out:
        try:
            write_receipt(out, text + "\n")
        except PermissionError as exc:
            sys.stderr.write(str(exc) + "\n")
            return 2
    if as_json or not out:
        sys.stdout.write(text + "\n")
    return 0


def _run_governance(args: argparse.Namespace) -> int:
    workspace = Path(args.workspace).resolve()
    if args.command == "digest-governance":
        corpus = FsGovernanceCorpusAdapter(workspace).load()
        receipt = digest_corpus(corpus, live_repairs())
        return _emit(receipt, args.out, args.json)
    receipt_path = Path(args.receipt)
    if not receipt_path.is_file():
        sys.stderr.write(f"receipt not found: {receipt_path}\n")
        return 2
    payload = json.loads(receipt_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        sys.stderr.write("receipt must be a JSON object\n")
        return 2
    result = apply_proposals(FsTextStore(workspace), proposals_from_receipt(payload), live_repairs())
    return _emit(result, args.out, args.json)


def main(argv: Optional[List[str]] = None) -> int:
    _configure_encoding()
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help(sys.stderr)
        return 2

    if args.command in {"digest-governance", "apply-governance-proposals"}:
        return _run_governance(args)

    workspace_path = Path(args.workspace).resolve()
    delivery_key = None
    try:
        if args.command == "dispatch-events":
            from ...infrastructure.storage.anchored_ledger_subscriber import (
                read_tip_key,
                validate_delivery_paths,
            )

            delivery_key = read_tip_key(args.tip_key_file)
            validate_delivery_paths(args.db_path, args.tip_path)
        container = OeopContainer(workspace_root=workspace_path, db_path=args.db_path)
    except (OSError, ValueError, RuntimeError) as error:
        _emit({"status": "error", "code": getattr(error, "code", "DELIVERY_CONFIGURATION_INVALID"), "message": str(error)}, None, True)
        return 1
    api = container.api

    try:
        if args.command == "dispatch-events":
            dispatcher = container.configure_receipt_delivery(
                tip_path=args.tip_path, key=delivery_key,
                ledger_id=args.ledger_id, worker_id=args.worker_id,
            )
            result = dispatcher.dispatch_pending(limit=args.limit)
            if result.is_err:
                error = result.unwrap_err()
                _emit({"status": "error", "code": error.code, "message": error.message}, None, True)
                return 1
            report = result.unwrap()
            _emit({"status": "ok", "authority_effect": "None", **asdict(report)}, None, True)
            return 1 if report.failed_count else 0
        if args.command == "compile-catalog":
            res = api.compile_catalog(
                estate_ref=args.estate,
                correlation_id=args.correlation_id,
                causation_id=args.causation_id,
                idempotency_key=args.idempotency_key,
            )
            if res.is_err:
                err = res.unwrap_err()
                if args.json:
                    sys.stdout.write(json.dumps({"status": "error", "code": err.code, "message": err.message}) + "\n")
                else:
                    sys.stderr.write(f"Error [{err.code}]: {err.message}\n")
                return 1

            dto = res.unwrap()
            payload = {
                "status": "ok",
                "catalog_id": dto.catalog_id,
                "estate_ref": dto.estate_ref,
                "epoch": dto.epoch,
                "total_skills": dto.total_skills,
                "total_operations": dto.total_operations,
                "catalog_digest": dto.catalog_digest,
            }
            if args.json:
                sys.stdout.write(json.dumps(payload, indent=2) + "\n")
            else:
                sys.stdout.write(
                    f"Compiled catalog {dto.catalog_id} (epoch {dto.epoch}) with {dto.total_skills} skills, "
                    f"{dto.total_operations} operations. Digest: {dto.catalog_digest[:12]}...\n"
                )
            return 0

        elif args.command == "verify-catalog":
            res = api.verify_catalog(
                catalog_id=args.catalog_id,
                correlation_id=args.correlation_id,
                causation_id=args.causation_id,
            )
            if res.is_err:
                err = res.unwrap_err()
                if args.json:
                    sys.stdout.write(json.dumps({"status": "error", "code": err.code, "message": err.message}) + "\n")
                else:
                    sys.stderr.write(f"Error [{err.code}]: {err.message}\n")
                return 1

            dto = res.unwrap()
            payload = {
                "status": "ok",
                "catalog_id": dto.catalog_id,
                "is_valid": dto.is_valid,
                "total_operations_verified": dto.total_operations_verified,
                "errors": list(dto.errors),
            }
            if args.json:
                sys.stdout.write(json.dumps(payload, indent=2) + "\n")
            else:
                status_str = "VALID" if dto.is_valid else "INVALID"
                sys.stdout.write(f"Catalog {dto.catalog_id}: {status_str} ({dto.total_operations_verified} operations verified)\n")
            return 0 if dto.is_valid else 1

        elif args.command == "compile-projection":
            res = api.compile_projection(
                catalog_id=args.catalog_id,
                target_format=args.format,
                correlation_id=args.correlation_id,
                causation_id=args.causation_id,
            )
            if res.is_err:
                err = res.unwrap_err()
                if args.json:
                    sys.stdout.write(json.dumps({"status": "error", "code": err.code, "message": err.message}) + "\n")
                else:
                    sys.stderr.write(f"Error [{err.code}]: {err.message}\n")
                return 1

            dto = res.unwrap()
            if args.json:
                sys.stdout.write(json.dumps({
                    "status": "ok",
                    "projection_id": dto.projection_id,
                    "catalog_id": dto.catalog_id,
                    "target_format": dto.target_format,
                    "manifest_digest": dto.manifest_digest,
                    "payload": dto.payload,
                }, indent=2) + "\n")
            else:
                sys.stdout.write(dto.payload + "\n")
            return 0

        else:
            parser.print_help(sys.stderr)
            return 2

    except (OSError, ValueError, RuntimeError) as error:
        _emit({"status": "error", "code": getattr(error, "code", "DELIVERY_CONFIGURATION_INVALID"), "message": str(error)}, None, True)
        return 1
    finally:
        container.close()

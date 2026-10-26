"""Refuse the antimorphism-farm screen when no preferred native port exists.

exact_ports, mssn_demo, and symbol-game ffi are inspected and never invoked.
Reply text is not classified. AuthorityEffect: None.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Mapping

from .contract import (
    AUTHORITY_EFFECT,
    DEMO_ID,
    FARM_PROBE_COUNT,
    NATIVE_PORT_CODE,
    PHARMACY_CONTROL_COUNT,
    PINNED_SCOPE,
    admit_farm_fixture,
    refusal_evidence_body,
    refusal_quarantine,
)
from omega_engine_pfp.domain.demos import DemoRefusal
from omega_engine_pfp.infrastructure.demos.canonical import canonical, digest, load

SCHEMA = "omega.symbol-game.demo-receipt.v1"
SPLIT_DETAIL = (
    f"{PHARMACY_CONTROL_COUNT} pharmacy controls and {FARM_PROBE_COUNT} "
    "farm probes are not split on farm_probes"
)
DETAIL = f"farm regex and pharmacy detect have no preferred native port; {SPLIT_DETAIL}"
_PORT_NAMES = frozenset(
    {"classify_response", "detect", "pharmacy_detect", "farm_classify"}
)
_PORT_SOURCES = (
    ("omega_engine_pfp", ("domain", "ports", "exact_ports.py")),
    ("omega_engine_pfp", ("use_cases", "mssn_demo.py")),
    ("omega_engine_pfp", ("ffi.py",)),
)
_RECEIPT_KEYS = frozenset(
    {
        "schema",
        "AuthorityEffect",
        "scenario",
        "implementation_sha256",
        "checker",
        "checker_registry_sha256",
        "fixture_sha256",
        "transport",
        "trace_sha256",
        "trace_terminal_digest",
        "transcript_sha256",
        "artifacts_sha256",
        "result",
        "verification_scope",
        "scope",
        "receipt_sha256",
    }
)
SCENARIO = {
    "kind": "immune",
    "level": None,
    "scenario_id": DEMO_ID,
    "scope": PINNED_SCOPE,
    "title": "antimorphism farm",
    "version": "1",
}


def _exported_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    if type(tree) is not ast.Module:
        return names
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    names.add(child.name)
    return names


def _preferred_native_port() -> str | None:
    """Name a preferred-port callable if the source defines one. Do not call it."""
    found: set[str] = set()
    for package, parts in _PORT_SOURCES:
        source = files(package).joinpath(*parts).read_text(encoding="utf-8")
        found.update(_PORT_NAMES & _exported_names(ast.parse(source)))
    if not found:
        return None
    return sorted(found)[0]


def run_antimorphism_farm(fixture: Mapping[str, object]) -> None:
    """Raise DemoRefusal NO_NATIVE_PORT. farm_probes does not select a subset."""
    admitted = admit_farm_fixture(fixture)
    if admitted.farm_probes is not True and admitted.farm_probes is not False:
        raise DemoRefusal("INVALID_FIXTURE", "farm_probes")
    port = _preferred_native_port()
    if port is not None:
        raise DemoRefusal(
            "NO_NATIVE_PORT",
            f"{port} exists but the farm does not delegate to it; "
            f"farm regex has no native port; {SPLIT_DETAIL}",
        )
    raise DemoRefusal("NO_NATIVE_PORT", DETAIL)


def implementation_digest() -> str:
    package = Path(__file__).resolve().parents[3]
    relatives = {
        "use_cases/demos/antimorphism_farm/contract.py": (
            "use_cases",
            "demos",
            "antimorphism_farm",
            "contract.py",
        ),
        "use_cases/demos/antimorphism_farm/run.py": (
            "use_cases",
            "demos",
            "antimorphism_farm",
            "run.py",
        ),
    }
    found = {
        name: digest(package.joinpath(*parts).read_bytes()) for name, parts in relatives.items()
    }
    return digest(canonical(found))


def _checker_binding() -> dict[str, str]:
    return {"code": NATIVE_PORT_CODE, "symbol": "run_antimorphism_farm"}


def _trace_rows(result: Mapping[str, object]) -> list[dict[str, object]]:
    return [
        {
            "AuthorityEffect": AUTHORITY_EFFECT,
            "demo_id": DEMO_ID,
            "event": "run_started",
            "live_transport": False,
        },
        {
            "AuthorityEffect": AUTHORITY_EFFECT,
            "code": result["code"],
            "event": "run_sealed",
            "terminal": result["status"],
        },
    ]


@dataclass(frozen=True, slots=True)
class FarmRun:
    result: dict[str, object]
    files: dict[str, bytes]
    receipt: dict[str, object]
    receipt_bytes: bytes


def assemble_run(fixture: Mapping[str, object]) -> FarmRun:
    """Build the refusal receipt. A CHECKED result is not representable."""
    try:
        run_antimorphism_farm(fixture)
    except DemoRefusal as exc:
        if exc.code != NATIVE_PORT_CODE:
            raise
        result: dict[str, object] = {
            "status": "TYPED_REFUSAL",
            "code": exc.code,
            "detail": exc.detail,
        }
    else:
        raise DemoRefusal("NO_NATIVE_PORT", "checker returned without refusal")
    if result["status"] == "CHECKED" or result["code"] != NATIVE_PORT_CODE:
        raise DemoRefusal("CHECKED_REJECTED")
    record = refusal_quarantine(digest(canonical(refusal_evidence_body())))
    quarantine_bytes = canonical(record)
    quarantine_name = "quarantine/" + digest(quarantine_bytes) + ".json"
    rows = _trace_rows(result)
    trace = b"".join(canonical(row) for row in rows)
    transcript = canonical([])
    fixture_bytes = canonical(dict(fixture))
    files = {
        "fixture.json": fixture_bytes,
        "trace.jsonl": trace,
        "transcript.json": transcript,
        quarantine_name: quarantine_bytes,
    }
    checker = _checker_binding()
    receipt: dict[str, object] = {
        "schema": SCHEMA,
        "AuthorityEffect": AUTHORITY_EFFECT,
        "scenario": SCENARIO,
        "implementation_sha256": implementation_digest(),
        "checker": checker,
        "checker_registry_sha256": digest(canonical(checker)),
        "fixture_sha256": digest(fixture_bytes),
        "transport": "fixture",
        "trace_sha256": digest(trace),
        "trace_terminal_digest": digest(canonical(rows[-1])),
        "transcript_sha256": digest(transcript),
        "artifacts_sha256": {name: digest(data) for name, data in files.items()},
        "result": result,
        "verification_scope": "fixture_replay",
        "scope": PINNED_SCOPE,
    }
    receipt["receipt_sha256"] = digest(canonical(receipt))
    return FarmRun(
        result=result,
        files=files,
        receipt=receipt,
        receipt_bytes=canonical(receipt),
    )


def _load_object(blob: bytes) -> dict[str, object]:
    try:
        loaded = load(blob)
    except DemoRefusal:
        raise
    except (UnicodeError, ValueError) as exc:
        raise DemoRefusal("INVALID_RECEIPT_SCHEMA") from exc
    if type(loaded) is not dict:
        raise DemoRefusal("INVALID_RECEIPT_SCHEMA")
    return loaded


def _inside(root: Path, relative: str) -> Path:
    if type(relative) is not str or "\\" in relative or ":" in relative or relative.startswith("/"):
        raise DemoRefusal("ARTIFACT_PATH_ESCAPE")
    parts = relative.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise DemoRefusal("ARTIFACT_PATH_ESCAPE")
    candidate = root.joinpath(*parts).resolve()
    base = root.resolve()
    if not candidate.is_relative_to(base) or candidate == base:
        raise DemoRefusal("ARTIFACT_PATH_ESCAPE")
    return candidate


def verify_receipt(path: Path) -> dict[str, object]:
    """Read receipt.json. CHECKED is rejected. The honest outcome is the refusal."""
    path = Path(path).resolve(strict=True)
    if path.name != "receipt.json":
        raise DemoRefusal("INVALID_RECEIPT_SCHEMA", path.name)
    blob = path.read_bytes()
    receipt = _load_object(blob)
    result = receipt.get("result")
    if type(result) is dict and result.get("status") == "CHECKED":
        raise DemoRefusal(
            "CHECKED_REJECTED",
            "antimorphism_farm has no native checker",
        )
    if set(receipt) != _RECEIPT_KEYS or receipt.get("schema") != SCHEMA:
        raise DemoRefusal("INVALID_RECEIPT_SCHEMA")
    if receipt.get("AuthorityEffect") != AUTHORITY_EFFECT:
        raise DemoRefusal("INVALID_RECEIPT_SCHEMA", "AuthorityEffect")
    if blob != canonical(receipt):
        raise DemoRefusal("NONCANONICAL_RECEIPT")
    payload = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    if digest(canonical(payload)) != receipt.get("receipt_sha256"):
        raise DemoRefusal("RECEIPT_DIGEST_MISMATCH")
    if (
        type(result) is not dict
        or result.get("status") != "TYPED_REFUSAL"
        or result.get("code") != NATIVE_PORT_CODE
    ):
        raise DemoRefusal("NO_NATIVE_PORT", "receipt is not the native-port refusal")
    if receipt.get("transport") != "fixture" or receipt.get("verification_scope") != "fixture_replay":
        raise DemoRefusal("TRANSPORT_SCOPE_MISMATCH")
    if receipt.get("scope") != PINNED_SCOPE or receipt.get("scenario") != SCENARIO:
        raise DemoRefusal("SCENARIO_VERSION_MISMATCH")
    root = path.parent
    fixture_path = root / "fixture.json"
    if not fixture_path.is_file():
        raise DemoRefusal("FIXTURE_DIGEST_MISMATCH")
    fixture = _load_object(fixture_path.read_bytes())
    rebuilt = assemble_run(fixture)
    if rebuilt.receipt_bytes != blob:
        raise DemoRefusal("FIXTURE_REPLAY_MISMATCH")
    artifacts = receipt["artifacts_sha256"]
    if type(artifacts) is not dict:
        raise DemoRefusal("ARTIFACT_SET_MISMATCH")
    observed = {
        item.relative_to(root).as_posix()
        for item in root.rglob("*")
        if item.is_file() and item != path
    }
    if observed != set(artifacts):
        raise DemoRefusal("ARTIFACT_SET_MISMATCH")
    for relative, expected in artifacts.items():
        data = _inside(root, str(relative)).read_bytes()
        if digest(data) != expected:
            raise DemoRefusal("ARTIFACT_DIGEST_MISMATCH", str(relative))
        if str(relative).startswith("quarantine/") and str(relative).endswith(".json"):
            record = _load_object(data)
            flag = record.get("can_promote_to_core")
            if type(flag) is not bool or flag is not False or record.get("AuthorityEffect") != "None":
                raise DemoRefusal("PROMOTION_REFUSED", str(relative))
    trace = (root / "trace.jsonl").read_bytes()
    lines = trace.splitlines(keepends=True)
    if not lines or digest(lines[-1]) != receipt["trace_terminal_digest"]:
        raise DemoRefusal("TRACE_BINDING_MISMATCH")
    sealed = _load_object(lines[-1])
    if sealed.get("terminal") != "TYPED_REFUSAL" or sealed.get("event") != "run_sealed":
        raise DemoRefusal("TRACE_RESULT_MISMATCH")
    return {
        "status": "VERIFIED_REFUSAL",
        "reproduced": True,
        "AuthorityEffect": AUTHORITY_EFFECT,
        "scenario_id": DEMO_ID,
        "outcome": "TYPED_REFUSAL",
    }

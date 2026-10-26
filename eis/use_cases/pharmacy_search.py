"""Load a pharmacy snapshot and delegate all selection decisions to Rust.

Catalog paths and admission decisions come from the composition's trusted
configuration, never from candidate model text. Search does not authenticate an
issuer, create admission decisions, or activate a detector.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any, Protocol, cast

from omega_engine_operations.domain.rop.result import Err
from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost

from ..domain.external_admission import AdmissionError
from ..domain.pharmacy_search import PharmacyQuery, PharmacySearchResult


class PharmacyNativeHost(Protocol):
    def invoke_runtime(self, action: str, payload: Mapping[str, Any]) -> Any: ...

    def invoke_runtime_with_file(self, action: str, payload: Mapping[str, Any], *,
                                 file_action: str) -> Any: ...


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"PHARMACY_CATALOG_INVALID: duplicate key {key}")
        result[key] = value
    return result


class PharmacySearchIndex:
    """A digest-refreshed in-memory snapshot; Rust owns eligibility and ranking."""

    def __init__(
        self, catalog: Mapping[str, Any] | Path, *,
        host: PharmacyNativeHost | None = None, clock: Callable[[], int] | None = None,
        repo_root: Path | None = None,
    ) -> None:
        self._path = catalog if isinstance(catalog, Path) else None
        self._raw = b""
        self._catalog_json = ""
        self._catalog_digest = ""
        self._catalog: dict[str, Any] = {}
        self._repo_root = repo_root
        if self._path is not None and repo_root is None:
            self._repo_root = (self._path.parent.parent.parent if
                               self._path.parent.parent.name == ".agents" else self._path.parent)
        self._host = host
        self._clock = clock if clock is not None else lambda: int(time.time())
        if self._path is None:
            self._accept(json.dumps(dict(catalog), ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode("utf-8"))
        else:
            self._refresh()

    def _accept(self, raw: bytes) -> None:
        if len(raw) > 16 * 1024 * 1024:
            raise ValueError("PHARMACY_CATALOG_INVALID: snapshot exceeds 16 MiB")
        try:
            data = json.loads(raw, object_pairs_hook=_unique)
            if not isinstance(data, dict) or not isinstance(data.get("antibodies"), dict):
                raise ValueError("antibodies must be an object")
            text = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                              allow_nan=False)
        except (ValueError, UnicodeError, TypeError) as error:
            raise ValueError(f"PHARMACY_CATALOG_INVALID: {error}") from error
        self._raw, self._catalog_json = raw, text
        self._catalog = data
        self._catalog_digest = hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _refresh(self) -> None:
        if self._path is not None:
            if self._path.with_suffix(".publication.pending.json").exists():
                raise ValueError("PHARMACY_PUBLICATION_INTERRUPTED")
            raw = self._path.read_bytes()
            if raw != self._raw:
                self._accept(raw)

    def _projection_exclusions(self) -> dict[str, str]:
        if self._path is None:
            return {}
        exclusions: dict[str, str] = {}
        projections = self._catalog.get("managed_projections", {})
        if not isinstance(projections, dict) or any(
            key not in self._catalog["antibodies"] for key in projections
        ):
            raise ValueError("PHARMACY_PROJECTION_MANIFEST_INVALID")
        assert self._repo_root is not None  # Set for every path-backed index.
        root = self._repo_root.resolve()
        for antibody_id, record in self._catalog["antibodies"].items():
            managed = antibody_id in projections
            if managed:
                relative = projections[antibody_id]
                if not isinstance(relative, str):
                    exclusions[antibody_id] = "PROJECTION_PATH_INVALID"
                    continue
                path = (root / relative).resolve()
                if not path.is_relative_to(root):
                    exclusions[antibody_id] = "PROJECTION_PATH_ESCAPE"
                    continue
            else:
                # Only conventional present legacy projections participate.
                if Path(antibody_id).name != antibody_id or not antibody_id.startswith("ab_"):
                    continue
                path = self._path.parent / f"{antibody_id}.json"
                if not path.exists():
                    continue
            try:
                raw = path.read_bytes()
                if managed:
                    # Match PharmacyCatalogRepository's persisted projection profile;
                    # the sorted UTF-8 rule digest has a different purpose/profile.
                    expected = (json.dumps(record, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
                    valid = raw == expected
                else:
                    valid = json.loads(raw, object_pairs_hook=_unique) == record
                if not valid:
                    exclusions[antibody_id] = "PROJECTION_DRIFT"
            except (OSError, ValueError, UnicodeError):
                exclusions[antibody_id] = "PROJECTION_UNAVAILABLE"
        return exclusions

    @property
    def catalog_digest(self) -> str:
        self._refresh()
        return self._catalog_digest

    def search(self, query: PharmacyQuery | Mapping[str, Any]) -> PharmacySearchResult:
        return self._execute(query)

    def match(self, query: PharmacyQuery | Mapping[str, Any], content: str) -> PharmacySearchResult:
        """Return native detector hits on one candidate, never an activation verdict."""
        return self._execute(query, candidate={
            "content": content, "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        })

    def _execute(self, query: PharmacyQuery | Mapping[str, Any], *,
                 candidate: dict[str, str] | None = None) -> PharmacySearchResult:
        self._refresh()
        wire_query = asdict(query) if isinstance(query, PharmacyQuery) else dict(query)
        wire_query["now_epoch"] = self._clock()
        host = self._host if self._host is not None else RustSymbolGameHost()
        payload: dict[str, Any] = {
            "catalog_json": self._catalog_json, "catalog_digest": self._catalog_digest,
            "query": wire_query, "projection_exclusions": self._projection_exclusions(),
        }
        if candidate is not None:
            payload["candidate"] = candidate
        reply = host.invoke_runtime_with_file("immune_pharmacy_search", payload,
                                              file_action="immune_pharmacy_search_file")
        if isinstance(reply, Err):
            raise AdmissionError(reply.error.code, reply.error.message)
        if not reply.value["success"]:
            raise AdmissionError("PHARMACY_NATIVE_UNAVAILABLE", str(reply.value["error"]))
        wire = reply.value["result"]
        if wire.get("refusal") is not None:
            refusal = wire["refusal"]
            raise AdmissionError(refusal["code"], refusal["message"])
        outcome = wire["outcome"]
        if outcome.get("catalog_digest") != self._catalog_digest:
            raise AdmissionError("PHARMACY_SNAPSHOT_MISMATCH", "native response changed snapshot")
        request_digest = hashlib.sha256(json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")).hexdigest()
        if outcome.get("request_digest") != request_digest:
            raise AdmissionError("PHARMACY_REQUEST_MISMATCH", "native response changed query or candidate")
        return cast(PharmacySearchResult, outcome)

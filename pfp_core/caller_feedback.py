"""Shared EIS caller-feedback loop for single-seat turns, swarms, and lineage checks.

Bridges ``pfp_core.immunity`` (two-signal gate, Thymus negative selection,
correlation-aware observation support) with ``eis`` pharmacy persistence and
``pciv`` prompt-lineage, family, society, and civilization scopes without mutating
any pinned ``pfp_core`` custody file.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from eis.domain.pharmacy_catalog import PharmacyCatalogRepository
from eis.domain.pharmacy_models import (
    VALID_ANTIBODY_SCOPES,
    Antibody,
    LearningEvidencePreimageV1,
    PharmacyStatus,
)
from eis.domain.pharmacy_seeder import record_reproduced_failure
from eis.domain.safe_pattern import UnsafePatternRefusal, compile_safe_pattern
from eis.domain.value_objects import DetectorRule, Signal1Match, Signal2Danger

from . import REPO_ROOT
from .immunity import (
    DIAGNOSTIC,
    HOLD,
    HOST_OBSERVERS,
    PASS,
    AntibodyRegistry,
    Decision,
    decide,
    host_danger,
    screen_rules,
    signal1,
)

_BUILTIN_CLEAN_PANEL: tuple[str, ...] = (
    "from fractions import Fraction\ndef exact_sum(a: int, b: int) -> Fraction:\n    return Fraction(a + b, 1)\n",
    "def coboundary_residual(v0: int, v1: int, edge: int) -> int:\n    return edge - (v1 - v0)\n",
    "def safe_impl():\n    return 42\n",
    "theorem coboundary_nilpotent (d0 d1 : Matrix Q) : d1 * d0 = 0 := by exact ddc_exactness",
)


@lru_cache(maxsize=1)
def default_clean_self_panel() -> tuple[str, ...]:
    """Return a bounded clean reference panel for fast fail-closed Thymus screening."""
    entries: list[str] = list(_BUILTIN_CLEAN_PANEL)
    self_panel_path = REPO_ROOT / "pfp" / "domain" / "immune" / "self_panel.json"
    if self_panel_path.is_file():
        try:
            raw = json.loads(self_panel_path.read_text(encoding="utf-8"))
            for row in raw.get("entries", [])[:16]:
                content = row.get("content")
                if isinstance(content, str) and content:
                    entries.append(content)
        except (OSError, UnicodeDecodeError, ValueError, TypeError) as _exc:
            _ = _exc
    return tuple(dict.fromkeys(entries))


@dataclass(frozen=True)
class CallerLineageContextV1:
    """Identifies the caller prompt and optional family/society/civilization scope."""

    prompt_id: str
    family_id: str | None = None
    society_id: str | None = None
    civilization_id: str | None = None
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if type(self.prompt_id) is not str or not self.prompt_id.strip():
            raise ValueError("PHARMACY_PROMPT_ID_REQUIRED: CallerLineageContextV1.prompt_id required")
        if self.authority_effect != "None":
            raise ValueError("AUTHORITY_EFFECT_MUST_BE_NONE")


@dataclass(frozen=True)
class ImmuneScreenRequestV1:
    """Typed boundary request passed into ``screen_caller_turn``."""

    lineage: CallerLineageContextV1
    prompt_utf8_bytes: bytes
    candidate_reply_bytes: bytes
    signal2_danger: Signal2Danger | None = None
    normalizers: Mapping[str, Callable[[str], str]] = field(default_factory=dict)
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if type(self.lineage) is not CallerLineageContextV1:
            raise TypeError("lineage must be an exact CallerLineageContextV1")
        if type(self.prompt_utf8_bytes) is not bytes:
            raise TypeError("prompt_utf8_bytes must be exact bytes")
        if type(self.candidate_reply_bytes) is not bytes:
            raise TypeError("candidate_reply_bytes must be exact bytes")
        if self.signal2_danger is not None and type(self.signal2_danger) is not Signal2Danger:
            raise TypeError("signal2_danger must be an exact Signal2Danger or None")
        if self.authority_effect != "None":
            raise ValueError("AUTHORITY_EFFECT_MUST_BE_NONE")


@dataclass(frozen=True)
class ImmuneScreenVerdictV1:
    """Structured screening verdict returned to wild turns and Act III sieves."""

    prompt_id: str
    subject_sha256: str
    disposition: str
    fired_antibody_ids: tuple[str, ...]
    signal1_matches: tuple[Signal1Match, ...]
    signal2_danger: Signal2Danger | None
    normalized_text: str | None
    lineage_receipt_ids: tuple[str, ...]
    catalog_digest: str
    refusal_code: str | None = None
    basis: str = ""
    authority_effect: str = "None"

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt_id": self.prompt_id,
            "subject_sha256": self.subject_sha256,
            "disposition": self.disposition,
            "fired_antibody_ids": list(self.fired_antibody_ids),
            "signal1_matches": [asdict(m) for m in self.signal1_matches],
            "signal2_observer": (
                self.signal2_danger.observer_id if self.signal2_danger is not None else None
            ),
            "normalized_applied": self.normalized_text is not None,
            "lineage_receipt_ids": list(self.lineage_receipt_ids),
            "catalog_digest": self.catalog_digest,
            "refusal_code": self.refusal_code,
            "basis": self.basis,
            "authority_effect": self.authority_effect,
        }


@dataclass(frozen=True)
class ThymusScreenReceiptV1:
    """Receipt emitted by ``screen_antibody_with_thymus``."""

    antibody_id: str
    is_admitted: bool
    autoimmune_violations: int
    fixture_polarity_ok: bool
    rationale: str
    panel_digest: str
    receipt_sha256: str
    authority_effect: str = "None"


def _extract_rule_fields(antibody: Antibody | Mapping[str, Any]) -> tuple[str, str, str, str, str]:
    if isinstance(antibody, Mapping):
        return (
            str(antibody.get("antibody_id", "")),
            str(antibody.get("target_pattern", "")),
            str(antibody.get("failure_class", "")),
            str(antibody.get("negative_fixture", "")),
            str(antibody.get("positive_fixture", "")),
        )
    return (
        antibody.antibody_id,
        antibody.target_pattern,
        antibody.failure_class,
        antibody.negative_fixture,
        antibody.positive_fixture,
    )


@lru_cache(maxsize=512)
def _screen_antibody_cached(
    antibody_id: str,
    pattern: str,
    failure_class: str,
    neg_fixture: str,
    pos_fixture: str,
    panel: tuple[str, ...],
) -> ThymusScreenReceiptV1:
    panel_bytes = json.dumps(list(panel), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    panel_digest = "sha256:" + hashlib.sha256(panel_bytes).hexdigest()

    try:
        compiled = compile_safe_pattern(pattern)
    except (UnsafePatternRefusal, re.error, ValueError, TypeError) as exc:
        rationale = f"UNSAFE_PATTERN: {exc}"
        rec_digest = "sha256:" + hashlib.sha256(
            json.dumps(
                {
                    "antibody_id": antibody_id,
                    "is_admitted": False,
                    "panel_digest": panel_digest,
                    "rationale": rationale,
                },
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        return ThymusScreenReceiptV1(
            antibody_id=antibody_id or "unknown",
            is_admitted=False,
            autoimmune_violations=1,
            fixture_polarity_ok=False,
            rationale=rationale,
            panel_digest=panel_digest,
            receipt_sha256=rec_digest,
        )

    rule = DetectorRule(
        rule_id=antibody_id,
        target_epitope=failure_class or antibody_id,
        match_pattern=pattern,
    )
    admitted_rules, killed_records = screen_rules([rule], list(panel))
    autoimmune_violations = 0 if len(admitted_rules) == 1 else max(1, len(killed_records))

    polarity_ok = True
    polarity_reasons: list[str] = []
    if neg_fixture.strip() and compiled.search(neg_fixture) is None:
        polarity_ok = False
        polarity_reasons.append("target_pattern did not match negative_fixture")
    if pos_fixture.strip() and compiled.search(pos_fixture) is not None:
        polarity_ok = False
        polarity_reasons.append("target_pattern matched positive_fixture")

    is_admitted = (autoimmune_violations == 0) and polarity_ok
    if autoimmune_violations > 0:
        rationale = (
            str(killed_records[0].get("rationale", "AUTOIMMUNE_SELF_MATCH"))
            if killed_records
            else "AUTOIMMUNE_SELF_MATCH"
        )
    elif not polarity_ok:
        rationale = "; ".join(polarity_reasons)
    else:
        rationale = f"cleared {len(panel)} self-panel entries and fixture polarity"

    rec_digest = "sha256:" + hashlib.sha256(
        json.dumps(
            {
                "antibody_id": antibody_id,
                "autoimmune_violations": autoimmune_violations,
                "fixture_polarity_ok": polarity_ok,
                "is_admitted": is_admitted,
                "panel_digest": panel_digest,
                "rationale": rationale,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return ThymusScreenReceiptV1(
        antibody_id=antibody_id,
        is_admitted=is_admitted,
        autoimmune_violations=autoimmune_violations,
        fixture_polarity_ok=polarity_ok,
        rationale=rationale,
        panel_digest=panel_digest,
        receipt_sha256=rec_digest,
    )


def screen_antibody_with_thymus(
    antibody: Antibody | Mapping[str, Any],
    self_panel: Sequence[str] | None = None,
) -> ThymusScreenReceiptV1:
    """Screen an antibody pattern against a clean self panel plus fixture polarity."""
    antibody_id, pattern, failure_class, neg_fixture, pos_fixture = _extract_rule_fields(antibody)
    panel = tuple(self_panel) if self_panel is not None else default_clean_self_panel()
    if not panel:
        raise ValueError("THYMUS_SELF_PANEL_EMPTY: self_panel must contain clean reference items")
    return _screen_antibody_cached(
        antibody_id, pattern, failure_class, neg_fixture, pos_fixture, panel
    )


class BoundImmuneStoreV1:
    """Single bound EIS store uniting catalog persistence, support registry, and lineage receipts."""

    def __init__(
        self,
        *,
        repo_root: Path,
        catalog: PharmacyCatalogRepository,
        registry: AntibodyRegistry,
        receipt_store: Any,
        custody_registry: Any,
        read_only: bool = False,
        civilization_id: str | None = None,
        family_index: Mapping[str, Any] | None = None,
        societies: Mapping[str, Any] | None = None,
    ) -> None:
        self.repo_root = Path(repo_root)
        self.catalog = catalog
        self.registry = registry
        self.receipt_store = receipt_store
        self.custody_registry = custody_registry
        self.read_only = read_only
        self.civilization_id = civilization_id
        self.family_index: dict[str, Any] = dict(family_index) if family_index is not None else {}
        self.societies: dict[str, Any] = dict(societies) if societies is not None else {}
        self._verified_thymus_cache: dict[str, str] = {}

    def catalog_digest(self) -> str:
        catalog = self.catalog.load_catalog()
        raw = json.dumps(catalog, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        return "sha256:" + hashlib.sha256(raw).hexdigest()

    def _in_scope(
        self,
        ab_id: str,
        rec: Mapping[str, Any],
        lineage: CallerLineageContextV1,
        lineage_ab_ids: frozenset[str],
    ) -> bool:
        scope_level = rec.get("scope_level")
        if scope_level is None:
            return True
        if scope_level == "civilization":
            rec_civ = rec.get("civilization_id")
            return rec_civ in (None, "", lineage.civilization_id, self.civilization_id)
        if scope_level == "society":
            return lineage.society_id is not None and rec.get("society_id") == lineage.society_id
        if scope_level == "family":
            family_obj = self.family_index.get(lineage.family_id or "")
            shared = tuple(getattr(family_obj, "shared_antibody_ids", ()))
            return lineage.family_id is not None and (
                rec.get("family_id") == lineage.family_id or ab_id in shared
            )
        if scope_level == "prompt_line":
            return rec.get("source_prompt_id") == lineage.prompt_id or ab_id in lineage_ab_ids
        return False

    def antibodies_for_scope(
        self,
        lineage: CallerLineageContextV1,
        *,
        self_panel: Sequence[str] | None = None,
    ) -> tuple[tuple[dict[str, Any], ...], tuple[str, ...]]:
        from pciv.use_cases.lamarckian_loop import load_active_lineage_antibodies  # noqa: PLC0415

        catalog = self.catalog.load_catalog()
        entries = catalog.get("antibodies", {})
        lineage_records, lineage_receipts = load_active_lineage_antibodies(
            lineage.prompt_id,
            self.receipt_store,
            self.catalog,
        )
        lineage_ab_ids = frozenset(item["antibody_id"] for item in lineage_records)
        receipt_ids = tuple(r.receipt_id for r in lineage_receipts)

        revoked_ids = set(getattr(self.custody_registry, "_revoked_rules", set()))
        active: list[dict[str, Any]] = []
        panel_tuple = tuple(self_panel) if self_panel is not None else default_clean_self_panel()
        panel_sig = hashlib.sha256(
            json.dumps(list(panel_tuple), separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        for ab_id in sorted(entries):
            rec = entries[ab_id]
            if rec.get("pharmacy_status") != PharmacyStatus.ADMITTED.value:
                continue
            if rec.get("suspended") or rec.get("revoked") or ab_id in revoked_ids:
                continue
            if not self._in_scope(ab_id, rec, lineage, lineage_ab_ids):
                continue

            # Fail closed against autoimmune self-reactivity on load/scope expansion.
            stored_thymus = rec.get("thymus_receipt_sha256")
            needs_screen = (
                self_panel is not None
                or not isinstance(stored_thymus, str)
                or not stored_thymus.startswith("sha256:")
                or self._verified_thymus_cache.get(f"{ab_id}:{panel_sig}") != stored_thymus
            )
            if needs_screen:
                screened = screen_antibody_with_thymus(rec, self_panel=panel_tuple)
                if not screened.is_admitted:
                    if hasattr(self.custody_registry, "revoke_rule_version"):
                        self.custody_registry.revoke_rule_version(ab_id)
                    continue
                if isinstance(stored_thymus, str) and stored_thymus.startswith("sha256:"):
                    self._verified_thymus_cache[f"{ab_id}:{panel_sig}"] = stored_thymus

            active.append(dict(rec))

        return tuple(active), receipt_ids

    def record_failure(
        self,
        *,
        lineage: CallerLineageContextV1,
        preimage: LearningEvidencePreimageV1,
        target_pattern: str,
        positive_fixture: str,
        negative_fixture: str | None = None,
        description: str = "",
        guidance_text: str = "",
        run_id: str = "",
        task_id: str = "",
        scope_level: str = "prompt_line",
        producer_actor: str = "operative_seat",
        model_id: str = "unknown_model",
        scaffold_digest: str = "default_scaffold",
        precedent_set_digest: str = "default_precedent",
        lineage_root: str | None = None,
        self_panel: Sequence[str] | None = None,
    ) -> Antibody:
        if self.read_only:
            raise PermissionError("IMMUNE_STORE_READ_ONLY: cannot write failure record on read-only store")
        return record_reproduced_failure(
            prompt_id=lineage.prompt_id,
            preimage=preimage,
            target_pattern=target_pattern,
            positive_fixture=positive_fixture,
            negative_fixture=negative_fixture,
            description=description,
            guidance_text=guidance_text,
            run_id=run_id,
            task_id=task_id,
            scope_level=scope_level,
            family_id=lineage.family_id,
            society_id=lineage.society_id,
            civilization_id=lineage.civilization_id or self.civilization_id,
            producer_actor=producer_actor,
            model_id=model_id,
            scaffold_digest=scaffold_digest,
            precedent_set_digest=precedent_set_digest,
            lineage_root=lineage_root,
            repository=self.catalog,
            registry=self.registry,
            self_panel=self_panel,
        )


def promote_antibody_scope(
    antibody_id: str,
    *,
    target_scope: str,
    family_id: str | None = None,
    society_id: str | None = None,
    civilization_id: str | None = None,
    self_panel: Sequence[str] | None = None,
    store: BoundImmuneStoreV1,
) -> dict[str, Any]:
    """Promote an antibody to a wider scope only after Thymus screening passes."""
    if target_scope not in VALID_ANTIBODY_SCOPES:
        raise ValueError(f"PHARMACY_SCOPE_LEVEL_INVALID:{target_scope!r}")
    if store.read_only:
        raise PermissionError("IMMUNE_STORE_READ_ONLY: cannot promote scope on read-only store")
    catalog = store.catalog.load_catalog()
    if antibody_id not in catalog.get("antibodies", {}):
        raise KeyError(antibody_id)
    record = dict(catalog["antibodies"][antibody_id])
    thymus_receipt = screen_antibody_with_thymus(record, self_panel=self_panel)
    if not thymus_receipt.is_admitted:
        record["pharmacy_status"] = PharmacyStatus.RETIRED.value
        record["revoked"] = True
        store.custody_registry.revoke_rule_version(antibody_id)
        store.catalog.upsert_managed_record(
            record,
            allowed_existing_statuses=frozenset({"candidate", "provisional", "admitted"}),
        )
        raise ValueError(f"AUTOIMMUNE_RULE_REFUSED: {thymus_receipt.rationale}")

    record["scope_level"] = target_scope
    if family_id is not None:
        record["family_id"] = family_id
    if society_id is not None:
        record["society_id"] = society_id
    if civilization_id is not None:
        record["civilization_id"] = civilization_id
    record["thymus_receipt_sha256"] = thymus_receipt.receipt_sha256
    return store.catalog.upsert_managed_record(
        record,
        allowed_existing_statuses=frozenset({"candidate", "provisional", "admitted"}),
    )


def screen_caller_turn(
    request: ImmuneScreenRequestV1,
    store: BoundImmuneStoreV1,
    *,
    self_panel: Sequence[str] | None = None,
) -> ImmuneScreenVerdictV1:
    """Shared two-signal EIS screen for wild turns, operative seats, and Act III sieves."""
    if type(request) is not ImmuneScreenRequestV1:
        raise TypeError("request must be an exact ImmuneScreenRequestV1")
    if type(store) is not BoundImmuneStoreV1:
        raise TypeError("store must be an exact BoundImmuneStoreV1")

    candidate_text = request.candidate_reply_bytes.decode("utf-8", errors="replace")
    subject_sha256 = "sha256:" + hashlib.sha256(request.candidate_reply_bytes).hexdigest()
    scoped_records, lineage_receipt_ids = store.antibodies_for_scope(
        request.lineage, self_panel=self_panel
    )
    rules: list[DetectorRule] = [
        DetectorRule(
            rule_id=str(rec["antibody_id"]),
            target_epitope=str(rec.get("failure_class", rec["antibody_id"])),
            match_pattern=str(rec.get("target_pattern", "")),
        )
        for rec in scoped_records
    ]

    matches: list[Signal1Match] = signal1(candidate_text, rules) if rules else []
    decision: Decision = decide(matches, request.signal2_danger)

    normalized_text: str | None = None
    if decision.disposition == DIAGNOSTIC and request.normalizers:
        transformed = candidate_text
        for key in sorted(request.normalizers):
            transformed = request.normalizers[key](transformed)
        if isinstance(transformed, str) and transformed != candidate_text and transformed.strip():
            normalized_text = transformed

    fired_ids = tuple(dict.fromkeys(m.detector_id for m in matches))
    return ImmuneScreenVerdictV1(
        prompt_id=request.lineage.prompt_id,
        subject_sha256=subject_sha256,
        disposition=decision.disposition,
        fired_antibody_ids=fired_ids,
        signal1_matches=tuple(matches),
        signal2_danger=request.signal2_danger,
        normalized_text=normalized_text,
        lineage_receipt_ids=lineage_receipt_ids,
        catalog_digest=store.catalog_digest(),
        refusal_code=decision.refusal_code,
        basis=decision.basis,
        authority_effect="None",
    )


__all__ = [
    "BoundImmuneStoreV1",
    "CallerLineageContextV1",
    "DIAGNOSTIC",
    "HOLD",
    "HOST_OBSERVERS",
    "ImmuneScreenRequestV1",
    "ImmuneScreenVerdictV1",
    "PASS",
    "ThymusScreenReceiptV1",
    "default_clean_self_panel",
    "host_danger",
    "promote_antibody_scope",
    "screen_antibody_with_thymus",
    "screen_caller_turn",
]

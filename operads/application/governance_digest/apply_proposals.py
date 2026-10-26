"""Apply digest proposals. The repair table, not the receipt, decides what may be written.

Proposals that share a target file are checked against one original snapshot,
rejected together when their locators overlap, and written once. A watched span
that matches neither fingerprint is not written. Post-edit spans only refresh
mirrors. AuthorityEffect: None.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Protocol

from ...domain.governance_digest.records import ApplyOutcome, EditLocator, Proposal, RepairSpec
from .textops import apply_edits, locator_span, measure, ranges_conflict, sha256_text

SCHEMA = "oewas.governance_apply.v1"
MIRRORS = (".claude", ".codex", ".grok")


class TextStore(Protocol):
    def read(self, relative_path: str) -> str | None: ...

    def write(self, relative_path: str, text: str) -> None: ...


def _mirror_path(canon_path: str, host: str) -> str | None:
    prefix = ".agents/"
    if not canon_path.startswith(prefix):
        return None
    return host + "/" + canon_path[len(prefix) :]


def _spec_map(specs: tuple[RepairSpec, ...] | list[RepairSpec]) -> dict[str, RepairSpec]:
    return {spec.repair_id: spec for spec in specs}


def _permitted(proposal: Proposal, spec: RepairSpec | None) -> str:
    if spec is None:
        return "repair_not_registered"
    if proposal.edit_kind != spec.edit_kind:
        return "edit_kind_not_permitted"
    if proposal.target_path != spec.target_path:
        return "target_not_permitted"
    if proposal.target_section != spec.target_section:
        return "section_not_permitted"
    if tuple(proposal.pattern_ids) != tuple(spec.pattern_ids):
        return "pattern_ids_not_permitted"
    if proposal.replacement_text != spec.replacement_text:
        return "replacement_not_permitted"
    if proposal.locator != spec.locator:
        return "locator_not_permitted"
    for pattern_id in spec.pattern_ids:
        if pattern_id not in proposal.evidence_ids:
            return "evidence_not_permitted"
    return ""


def _proposal_from_mapping(payload: dict[str, object]) -> Proposal:
    locator_raw = payload["locator"]
    if not isinstance(locator_raw, dict):
        raise TypeError("locator must be an object")
    pattern_ids = payload["pattern_ids"]
    evidence_ids = payload["evidence_ids"]
    if not isinstance(pattern_ids, list) or not isinstance(evidence_ids, list):
        raise TypeError("pattern_ids and evidence_ids must be arrays")
    return Proposal(
        proposal_id=str(payload["proposal_id"]),
        repair_id=str(payload["repair_id"]),
        target_path=str(payload["target_path"]),
        target_section=str(payload["target_section"]),
        edit_kind=str(payload["edit_kind"]),
        expected_target_hash=str(payload["expected_target_hash"]),
        replacement_text=str(payload["replacement_text"]),
        evidence_ids=tuple(str(item) for item in evidence_ids),
        locator=EditLocator(
            mode=str(locator_raw.get("mode", "")),
            old_text=str(locator_raw.get("old_text", "")),
            anchor_text=str(locator_raw.get("anchor_text", "")),
            new_heading=str(locator_raw.get("new_heading", "")),
        ),
        pattern_ids=tuple(str(item) for item in pattern_ids),
    )


def proposals_from_receipt(receipt: dict[str, object]) -> tuple[Proposal, ...]:
    raw = receipt.get("proposals", [])
    if not isinstance(raw, list):
        return ()
    return tuple(_proposal_from_mapping(item) for item in raw if isinstance(item, dict))


def _outcome(
    proposal_id: str,
    status: str,
    reason: str,
    before_hash: str,
    after_hash: str,
    mirrors: tuple[tuple[str, str], ...] = (),
) -> ApplyOutcome:
    return ApplyOutcome(proposal_id, status, reason, before_hash, after_hash, mirrors)


def _copy_mirrors(
    store: TextStore, canon_path: str, text: str, fail_hosts: frozenset[str]
) -> tuple[tuple[tuple[str, str], ...], bool]:
    """Copy canon text onto mirrors that differ. The bool is true when a copy was needed or refused."""
    results: list[tuple[str, str]] = []
    dirty = False
    for host in MIRRORS:
        destination = _mirror_path(canon_path, host)
        if destination is None:
            results.append((host, "skipped_not_canon"))
            dirty = True
            continue
        if host in fail_hosts:
            results.append((host, "failed"))
            dirty = True
            continue
        if store.read(destination) != text:
            store.write(destination, text)
            dirty = True
        results.append((host, "copied"))
    return tuple(results), dirty


def _span_state(text: str, spec: RepairSpec) -> str:
    watched = measure(
        text,
        edit_kind=spec.edit_kind,
        target_section=spec.target_section,
        locator=spec.locator,
        replacement_text=spec.replacement_text,
    )
    if watched == spec.post_fingerprint:
        return "post"
    if watched == spec.pre_fingerprint:
        return "pre"
    return "anchor_changed"


def _mirror_status(mirrors: tuple[tuple[str, str], ...], *, wrote_canon: bool) -> tuple[str, str]:
    if any(result == "failed" for _, result in mirrors):
        reason = "canon_written_mirror_failed" if wrote_canon else "mirror_copy_failed"
        return "partial", reason
    return "applied", "wrote_once" if wrote_canon else "mirror_repair"


def apply_proposals(
    store: TextStore,
    proposals: tuple[Proposal, ...] | list[Proposal],
    specs: tuple[RepairSpec, ...] | list[RepairSpec],
    *,
    fail_mirror_hosts: frozenset[str] = frozenset(),
) -> dict[str, object]:
    """Write permitted repairs. ``fail_mirror_hosts`` exists so tests can force a partial copy."""
    registered = _spec_map(specs)
    grouped: dict[str, list[Proposal]] = defaultdict(list)
    for proposal in proposals:
        grouped[proposal.target_path].append(proposal)

    outcomes: list[ApplyOutcome] = []
    handled: set[str] = set()
    for target_path in sorted(grouped):
        group = sorted(grouped[target_path], key=lambda item: item.proposal_id)
        original = store.read(target_path)
        if original is None:
            for proposal in group:
                outcomes.append(_outcome(proposal.proposal_id, "failed", "target_missing", "", ""))
                handled.add(proposal.repair_id)
            continue
        before = sha256_text(original)
        pre: list[Proposal] = []
        post: list[Proposal] = []
        for proposal in group:
            spec = registered.get(proposal.repair_id)
            reason = _permitted(proposal, spec)
            handled.add(proposal.repair_id)
            if reason or spec is None:
                outcomes.append(
                    _outcome(
                        proposal.proposal_id,
                        "failed",
                        reason or "repair_not_registered",
                        before,
                        before,
                    )
                )
                continue
            state = _span_state(original, spec)
            if state == "anchor_changed":
                outcomes.append(_outcome(proposal.proposal_id, "failed", "anchor_changed", before, before))
            elif state == "post":
                post.append(proposal)
            elif proposal.expected_target_hash != before:
                outcomes.append(_outcome(proposal.proposal_id, "failed", "stale_target", before, before))
            else:
                pre.append(proposal)
        if not pre and not post:
            continue
        if pre:
            spans = []
            locator_error = ""
            for proposal in pre:
                found = locator_span(original, proposal.locator, proposal.replacement_text)
                if isinstance(found, str):
                    locator_error = found
                    break
                spans.append(found)
            if locator_error or ranges_conflict(spans):
                reason = locator_error or "conflicting_edits"
                for proposal in pre:
                    outcomes.append(_outcome(proposal.proposal_id, "failed", reason, before, before))
                for proposal in post:
                    outcomes.append(_outcome(proposal.proposal_id, "failed", "partial_group", before, before))
                continue
            edited, error = apply_edits(
                original, [(proposal.locator, proposal.replacement_text) for proposal in pre]
            )
            if edited is None:
                for proposal in pre + post:
                    outcomes.append(_outcome(proposal.proposal_id, "failed", error or "edit_failed", before, before))
                continue
            store.write(target_path, edited)
            after = sha256_text(edited)
            mirrors, _dirty = _copy_mirrors(store, target_path, edited, fail_mirror_hosts)
            status, reason = _mirror_status(mirrors, wrote_canon=True)
            for proposal in pre + post:
                outcomes.append(_outcome(proposal.proposal_id, status, reason, before, after, mirrors))
            continue
        mirrors, _dirty = _copy_mirrors(store, target_path, original, fail_mirror_hosts)
        status, reason = _mirror_status(mirrors, wrote_canon=False)
        for proposal in post:
            outcomes.append(_outcome(proposal.proposal_id, status, reason, before, before, mirrors))

    for spec in specs:
        if spec.repair_id in handled:
            continue
        text = store.read(spec.target_path)
        if text is None or _span_state(text, spec) != "post":
            continue
        mirrors, dirty = _copy_mirrors(store, spec.target_path, text, fail_mirror_hosts)
        if not dirty:
            continue
        before = sha256_text(text)
        status, reason = _mirror_status(mirrors, wrote_canon=False)
        if status == "applied":
            reason = "mirror_reconciled"
        outcomes.append(_outcome(spec.repair_id, status, reason, before, before, mirrors))

    outcomes.sort(key=lambda item: item.proposal_id)
    return {
        "authority_effect": "None",
        "outcomes": [
            {
                "after_hash": item.after_hash,
                "before_hash": item.before_hash,
                "mirrors": [{"host": host, "result": result} for host, result in item.mirrors],
                "proposal_id": item.proposal_id,
                "reason": item.reason,
                "status": item.status,
            }
            for item in outcomes
        ],
        "schema": SCHEMA,
    }

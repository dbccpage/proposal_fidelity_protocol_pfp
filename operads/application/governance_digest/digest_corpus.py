"""Read-only governance digest. AuthorityEffect: None.

Evidence is classified, then each repair's pre and post fingerprints are
compared, and only then are proposals emitted. This function does not write.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Literal, Mapping, Sequence

from ...domain.governance_digest.records import (
    REQUIRED_FRONTMATTER,
    Finding,
    GovernanceCorpus,
    PatternDoc,
    Proposal,
    RepairSpec,
    TextDoc,
)
from .lesson import LESSON_FIELDS, lesson_status
from .textops import measure, pattern_id_in_table, table_block

SCHEMA = "oewas.governance_digest.v1"
RUNS_CORPUS = "_intelligence/symbol_game/runs"

BOILERPLATE = (
    "- **Clean Architecture**: Inward dependencies maintained across operations and domain roots.",
    "- **Four-Host Parity**: State changes synchronized across `.agents`, `.claude`, `.codex`, and `.grok`.",
    "- **Claim Discipline**: Narrowest defensible claims recorded without unmechanized proof hype.",
)

_LINK = re.compile(r"\]\(([^)]+)\)")
_HOST_PREFIXES = (".agents/", ".claude/", ".codex/", ".grok/", "_intelligence/", "_ic/")
SKILL_OWNERS = {
    "python": "operads/skills/techne-code-python-anti-patterns/SKILL.md",
    "rust": "operads/skills/techne-code-rust-anti-patterns/SKILL.md",
    "sql": "operads/skills/techne-code-sql-anti-patterns/SKILL.md",
}
RULE_EDIT_KINDS = frozenset({"cite_pattern", "insert_invariant"})


def canonical_json(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _doc_map(docs: Iterable[TextDoc]) -> dict[str, TextDoc]:
    return {doc.relative_path: doc for doc in docs}


def _stem(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    return name[:-3] if name.endswith(".md") else name


def _resolve(token: str, by_id: Mapping[str, PatternDoc], by_stem: Mapping[str, PatternDoc]) -> PatternDoc | None:
    if token in by_id:
        return by_id[token]
    return by_stem.get(token)


def _pattern_pair_defects(
    pattern: PatternDoc,
    by_id: Mapping[str, PatternDoc],
    by_stem: Mapping[str, PatternDoc],
) -> list[tuple[str, str]]:
    defects: list[tuple[str, str]] = []
    missing = [key for key in REQUIRED_FRONTMATTER if key not in pattern.frontmatter_keys]
    if missing:
        defects.append(("missing_frontmatter", ",".join(missing)))
    if pattern.category == "anti_pattern" and not pattern.detection_text.strip():
        defects.append(("empty_detection", pattern.relative_path))
    if not pattern.dual_pattern:
        defects.append(("missing_dual", pattern.relative_path))
        return defects
    partner = _resolve(pattern.dual_pattern, by_id, by_stem)
    if partner is None:
        defects.append(("missing_dual", pattern.dual_pattern))
        return defects
    back = _resolve(partner.dual_pattern, by_id, by_stem)
    if back is None or back.pattern_id != pattern.pattern_id:
        defects.append(("non_mutual_dual", partner.pattern_id))
    return defects


def _add_pair_defect(
    rows: list[dict[str, str]],
    seen: set[tuple[str, str]],
    pattern_id: str,
    code: str,
    detail: str,
) -> None:
    key = (pattern_id, code)
    if key in seen:
        return
    seen.add(key)
    rows.append({"code": code, "detail": detail, "pattern_id": pattern_id})


def pair_defect_rows(patterns: Sequence[PatternDoc]) -> list[dict[str, str]]:
    by_id: dict[str, list[PatternDoc]] = defaultdict(list)
    by_stem: dict[str, PatternDoc] = {}
    for pattern in patterns:
        by_id[pattern.pattern_id].append(pattern)
        by_stem[_stem(pattern.relative_path)] = pattern
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for pattern_id, group in by_id.items():
        if len(group) > 1:
            detail = ",".join(sorted(item.relative_path for item in group))
            _add_pair_defect(rows, seen, pattern_id, "duplicate_pattern_id", detail)
    id_map = {pattern_id: group[0] for pattern_id, group in by_id.items() if len(group) == 1}
    for pattern in patterns:
        for code, detail in _pattern_pair_defects(pattern, id_map, by_stem):
            _add_pair_defect(rows, seen, pattern.pattern_id, code, detail)
    rows.sort(key=lambda row: (row["pattern_id"], row["code"]))
    return rows


def _touch_paths(text: str) -> tuple[str, ...]:
    found: list[str] = []
    for raw in _LINK.findall(text):
        path = raw.replace("\\", "/").split("file:///", 1)[-1]
        if "://" in path:
            continue
        if path.startswith("/") or (len(path) > 2 and path[1] == ":"):
            continue
        found.append(path)
    return tuple(found)


def _is_source_path(path: str) -> bool:
    return not path.startswith(_HOST_PREFIXES)


def _observational_bullets(text: str) -> list[str]:
    collecting = False
    bullets: list[str] = []
    for line in text.splitlines():
        if line.startswith("## Architectural Invariants"):
            collecting = True
            continue
        if collecting and line.startswith("## "):
            break
        if collecting and line.startswith("- "):
            bullets.append(line)
    return bullets


def _lesson_finding(corpus: str, path: str, text: str, *, handoff: bool) -> Finding | None:
    status, fields = lesson_status(text)
    if status == "touch_provenance" or status == "none":
        if handoff and status == "none":
            return Finding(
                finding_id=f"lesson_incomplete:{path}",
                disposition="lesson_incomplete",
                corpus=corpus,
                source_paths=(path,),
                target_path="",
                target_section="",
                reason="handoff has no complete lesson",
            )
        return None
    evidence = tuple((key, fields[key]) for key in LESSON_FIELDS if key in fields)
    return Finding(
        finding_id=f"{status}:{path}",
        disposition=status,
        corpus=corpus,
        source_paths=(path,),
        target_path="",
        target_section="",
        reason=status,
        evidence=evidence,
    )


def _json_objects(text: str) -> list[dict[str, object]]:
    stripped = text.strip()
    if not stripped:
        return []
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            return [payload]
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
    objects: list[dict[str, object]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            objects.append(payload)
    return objects


def _audit_finding(corpus: str, path: str, payload: Mapping[str, object]) -> Finding | None:
    blockers = payload.get("decisive_blockers")
    verdict = payload.get("verdict")
    if isinstance(blockers, list) and blockers:
        return Finding(
            finding_id=f"audit_blocker:{path}",
            disposition="audit_blocker",
            corpus=corpus,
            source_paths=(path,),
            target_path=str(payload.get("target", "")),
            target_section="",
            reason="decisive_blockers is non-empty",
            evidence=(("blocker_count", str(len(blockers))),),
        )
    if verdict == "GO" and isinstance(blockers, list) and not blockers:
        return Finding(
            finding_id=f"audit_pass:{path}",
            disposition="audit_pass",
            corpus=corpus,
            source_paths=(path,),
            target_path=str(payload.get("target", "")),
            target_section="",
            reason="verdict GO with no decisive blockers",
        )
    return None


def _record_findings(doc: TextDoc, corpus_name: str) -> list[Finding]:
    """One finding per JSON object. A multi-record file keeps distinct ids."""
    payloads = _json_objects(doc.text)
    count = len(payloads)
    found: list[Finding] = []
    for index, payload in enumerate(payloads):
        label = doc.relative_path if count == 1 else f"{doc.relative_path}#{index + 1}"
        status, fields = lesson_status(json.dumps(payload, sort_keys=True))
        if status == "lesson_candidate":
            found.append(
                Finding(
                    finding_id=f"lesson_candidate:{label}",
                    disposition="lesson_candidate",
                    corpus=corpus_name,
                    source_paths=(label,),
                    target_path="",
                    target_section="",
                    reason="complete lesson",
                    evidence=tuple((key, fields[key]) for key in LESSON_FIELDS),
                )
            )
            continue
        audit = _audit_finding(corpus_name, label, payload)
        if audit is not None:
            found.append(audit)
    return found


def _pattern_hashes_match(spec: RepairSpec, patterns: Mapping[str, PatternDoc]) -> bool:
    for pattern_id, expected in spec.pattern_sha256:
        pattern = patterns.get(pattern_id)
        if pattern is None or pattern.sha256 != expected:
            return False
    return True


def _defective_ids(rows: Sequence[Mapping[str, str]]) -> set[str]:
    return {row["pattern_id"] for row in rows}


def _documentation_evidence(
    corpus: GovernanceCorpus,
) -> tuple[list[Finding], list[dict[str, object]], dict[str, list[str]]]:
    findings: list[Finding] = []
    noise: list[dict[str, object]] = []
    touches: dict[str, list[str]] = defaultdict(list)
    for doc in corpus.documentation:
        path = doc.relative_path
        if "/slop_audit/" in path.replace("\\", "/") or path.endswith("slop_audit"):
            if "CONVERSATIONAL_AI_ARTIFACT" in doc.text:
                noise.append({"kind": "slop", "source": path})
                continue
        bullets = _observational_bullets(doc.text)
        lesson = _lesson_finding("documentation", path, doc.text, handoff=False)
        if lesson is not None:
            findings.append(lesson)
        if bullets and all(bullet in BOILERPLATE for bullet in bullets):
            touch = _touch_paths(doc.text)
            noise.append({"kind": "session_boilerplate", "source": path, "touch_paths": list(touch)})
            for item in touch:
                if _is_source_path(item):
                    touches[item].append(path)
            continue
        if "CONVERSATIONAL_AI_ARTIFACT" in doc.text and lesson is None:
            noise.append({"kind": "slop", "source": path})
    return findings, noise, touches


def _touch_coverage(path: str, corpus: GovernanceCorpus) -> str:
    if any(path in rule.text for rule in corpus.rules):
        return "named_by_rule"
    if any(path in pattern.applicability for pattern in corpus.patterns):
        return "declared_scope"
    return "unknown"


def _recurring_touch_findings(touches: Mapping[str, Sequence[str]], corpus: GovernanceCorpus) -> list[Finding]:
    findings: list[Finding] = []
    for path, sessions in sorted(touches.items()):
        distinct = tuple(sorted(set(sessions)))
        if len(distinct) < 2:
            continue
        findings.append(
            Finding(
                finding_id=f"recurring_touch:{path}",
                disposition="recurring_touch_candidate",
                corpus="documentation",
                source_paths=distinct,
                target_path=path,
                target_section="",
                reason="the same repo-relative file is named by two sessions; that is recurrence, not an anti-pattern",
                evidence=(("coverage", _touch_coverage(path, corpus)), ("session_count", str(len(distinct)))),
            )
        )
    return findings


def _lesson_findings(corpus: GovernanceCorpus) -> list[Finding]:
    findings: list[Finding] = []
    for doc in corpus.handoffs:
        lesson = _lesson_finding("teamwork", doc.relative_path, doc.text, handoff=True)
        if lesson is not None:
            findings.append(lesson)
    return findings


def _harvest_finding(doc: TextDoc) -> Finding | None:
    try:
        payload = json.loads(doc.text)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict) or "merkle_roots" not in payload:
        return None
    roots = payload.get("merkle_roots")
    evidence: tuple[tuple[str, str], ...] = ()
    if isinstance(roots, dict):
        evidence = tuple((str(key), str(value)) for key, value in sorted(roots.items()))
    return Finding(
        finding_id=f"custody:{doc.relative_path}",
        disposition="custody_provenance",
        corpus="harvest",
        source_paths=(doc.relative_path,),
        target_path="",
        target_section="",
        reason="harvest receipt records a vault of teamwork; snapshots are not a second lesson source",
        evidence=evidence,
    )


def _harvest_findings(corpus: GovernanceCorpus) -> list[Finding]:
    return [finding for doc in corpus.harvest_receipts if (finding := _harvest_finding(doc)) is not None]


def _record_corpus_findings(corpus: GovernanceCorpus) -> list[Finding]:
    findings: list[Finding] = []
    for doc in corpus.omc_records:
        findings.extend(_record_findings(doc, "omc_dags"))
    for doc in corpus.paper_reviews:
        findings.extend(_record_findings(doc, "core_paper_reviews"))
    return findings


def _stale_pointer_findings(corpus: GovernanceCorpus) -> list[Finding]:
    if RUNS_CORPUS not in corpus.absent_corpora:
        return []
    findings: list[Finding] = []
    for doc in corpus.stale_pointers:
        if RUNS_CORPUS not in doc.text.replace("\\", "/"):
            continue
        findings.append(
            Finding(
                finding_id=f"stale_corpus_pointer:{doc.relative_path}",
                disposition="stale_corpus_pointer",
                corpus="symbol_game",
                source_paths=(doc.relative_path,),
                target_path=RUNS_CORPUS,
                target_section="",
                reason="this file cites symbol_game/runs, and that directory is absent",
            )
        )
    return findings


RepairState = Literal["pre", "already_codified", "anchor_changed"]


@dataclass(frozen=True)
class _RepairAssessment:
    """Fail-closed classification of one repair against immutable corpus data."""

    spec: RepairSpec
    state: RepairState
    reason: str
    target: TextDoc | None


def _repair_target(
    spec: RepairSpec,
    rules: Mapping[str, TextDoc],
    skills: Mapping[str, TextDoc],
) -> TextDoc | None:
    documents = rules if spec.target_path in rules else skills
    return documents.get(spec.target_path)


def _assess_repair(
    spec: RepairSpec,
    target: TextDoc | None,
    patterns: Mapping[str, PatternDoc],
) -> _RepairAssessment:
    if target is None:
        return _RepairAssessment(spec, "anchor_changed", "repair target is not in the snapshot", None)
    if not _pattern_hashes_match(spec, patterns):
        return _RepairAssessment(
            spec,
            "anchor_changed",
            "pattern file bytes differ from the fingerprint stored with this repair",
            target,
        )
    current = measure(
        target.text,
        edit_kind=spec.edit_kind,
        target_section=spec.target_section,
        locator=spec.locator,
        replacement_text=spec.replacement_text,
    )
    if current == spec.post_fingerprint:
        return _RepairAssessment(
            spec,
            "already_codified",
            "the watched span matches the stored post-edit fingerprint",
            target,
        )
    if current == spec.pre_fingerprint:
        return _RepairAssessment(
            spec,
            "pre",
            "the watched span matches the stored pre-edit fingerprint",
            target,
        )
    return _RepairAssessment(
        spec,
        "anchor_changed",
        "the watched span matches neither stored fingerprint",
        target,
    )


def _pattern_source_paths(
    spec: RepairSpec,
    patterns: Sequence[PatternDoc],
    *,
    ordered: bool,
) -> tuple[str, ...]:
    paths = (pattern.relative_path for pattern in patterns if pattern.pattern_id in spec.pattern_ids)
    return tuple(sorted(paths)) if ordered else tuple(paths)


def _repair_finding(assessment: _RepairAssessment, patterns: Sequence[PatternDoc]) -> Finding:
    dispositions = {
        "pre": "repair_pending",
        "already_codified": "already_codified",
        "anchor_changed": "anchor_changed",
    }
    spec = assessment.spec
    corpus_name = "repairs"
    if assessment.target is None:
        corpus_name = "rules" if spec.target_path.startswith("operads/rules/") else "skills"
    return Finding(
        finding_id=f"{dispositions[assessment.state]}:{spec.repair_id}",
        disposition=dispositions[assessment.state],
        corpus=corpus_name,
        source_paths=_pattern_source_paths(spec, patterns, ordered=assessment.target is not None),
        target_path=spec.target_path,
        target_section=spec.target_section,
        reason=assessment.reason,
        evidence=(("repair_id", spec.repair_id),)
        if assessment.target is None
        else (("repair_id", spec.repair_id), ("edit_kind", spec.edit_kind)),
    )


def _repair_proposal(assessment: _RepairAssessment) -> Proposal | None:
    spec = assessment.spec
    target = assessment.target
    if assessment.state != "pre" or target is None:
        return None
    return Proposal(
        proposal_id=spec.repair_id,
        repair_id=spec.repair_id,
        target_path=spec.target_path,
        target_section=spec.target_section,
        edit_kind=spec.edit_kind,
        expected_target_hash=target.sha256,
        replacement_text=spec.replacement_text,
        evidence_ids=tuple(spec.pattern_ids) + (spec.pre_fingerprint, spec.post_fingerprint),
        locator=spec.locator,
        pattern_ids=spec.pattern_ids,
    )


def _repair_results(
    corpus: GovernanceCorpus,
    repairs: Sequence[RepairSpec],
    blocked: set[str],
) -> tuple[list[Finding], list[Proposal]]:
    rules = _doc_map(corpus.rules)
    skills = _doc_map(corpus.skills)
    patterns = {pattern.pattern_id: pattern for pattern in corpus.patterns}
    findings: list[Finding] = []
    proposals: list[Proposal] = []
    seen_proposals: set[tuple[str, str, str, str]] = set()
    for spec in repairs:
        if any(pattern_id in blocked for pattern_id in spec.pattern_ids):
            continue
        assessment = _assess_repair(spec, _repair_target(spec, rules, skills), patterns)
        proposal = _repair_proposal(assessment)
        if proposal is not None:
            key = (spec.repair_id, spec.target_path, spec.target_section, spec.edit_kind)
            if key in seen_proposals:
                continue
            seen_proposals.add(key)
            proposals.append(proposal)
        findings.append(_repair_finding(assessment, corpus.patterns))
    return findings, proposals


def _owner_tables(skills: Mapping[str, TextDoc]) -> dict[str, str]:
    tables: dict[str, str] = {}
    for language, skill_path in SKILL_OWNERS.items():
        skill = skills.get(skill_path)
        tables[language] = (table_block(skill.text) or "") if skill is not None else ""
    return tables


def _skill_table_repairs(repairs: Sequence[RepairSpec]) -> dict[str, list[str]]:
    repair_ids: dict[str, list[str]] = defaultdict(list)
    for spec in repairs:
        if spec.edit_kind != "skill_table_row":
            continue
        for pattern_id in spec.pattern_ids:
            repair_ids[pattern_id].append(spec.repair_id)
    return repair_ids


def _uncited_rule_finding(pattern: PatternDoc, cited_ids: set[str]) -> Finding | None:
    if pattern.category != "anti_pattern" or pattern.pattern_id in cited_ids:
        return None
    return Finding(
        finding_id=f"rule_unlinked:{pattern.pattern_id}",
        disposition="rule_unlinked",
        corpus="anti_pattern",
        source_paths=(pattern.relative_path,),
        target_path="",
        target_section="",
        reason="no cite_pattern or insert_invariant repair names this pattern; an id elsewhere is not a citation",
    )


def _owner_finding(
    pattern: PatternDoc,
    owner_tables: Mapping[str, str],
    repair_ids_by_pattern: Mapping[str, Sequence[str]],
) -> Finding | None:
    owner = SKILL_OWNERS.get(pattern.language)
    if owner is None:
        if pattern.category != "anti_pattern":
            return None
        return Finding(
            finding_id=f"missing_specialist:{pattern.pattern_id}",
            disposition="missing_specialist",
            corpus="anti_pattern",
            source_paths=(pattern.relative_path,),
            target_path="operads/skills/auto-code-anti-pattern-hunter/SKILL.md",
            target_section="Connected Specialist Skills",
            reason="this language has no specialist skill; the hunter link is a separate repair",
        )
    table = owner_tables.get(pattern.language, "")
    if table and pattern_id_in_table(table, pattern.pattern_id):
        return Finding(
            finding_id=f"skill_table_ok:{pattern.pattern_id}",
            disposition="already_codified",
            corpus="skills",
            source_paths=(pattern.relative_path,),
            target_path=owner,
            target_section="pattern_table",
            reason="pattern id is in the owning specialist table",
        )
    if pattern.category != "anti_pattern" or pattern.pattern_id in repair_ids_by_pattern:
        return None
    return Finding(
        finding_id=f"skill_table_gap:{pattern.pattern_id}",
        disposition="skill_table_gap",
        corpus="skills",
        source_paths=(pattern.relative_path,),
        target_path=owner,
        target_section="pattern_table",
        reason="pattern id is absent from the owning specialist table and no repair is registered",
    )


def _pattern_coverage_findings(
    corpus: GovernanceCorpus,
    repairs: Sequence[RepairSpec],
    blocked: set[str],
) -> list[Finding]:
    cited_ids = {
        pattern_id
        for spec in repairs
        if spec.edit_kind in RULE_EDIT_KINDS
        for pattern_id in spec.pattern_ids
    }
    owner_tables = _owner_tables(_doc_map(corpus.skills))
    repair_ids = _skill_table_repairs(repairs)
    findings: list[Finding] = []
    for pattern in sorted(corpus.patterns, key=lambda item: item.pattern_id):
        if pattern.pattern_id in blocked:
            continue
        uncited = _uncited_rule_finding(pattern, cited_ids)
        if uncited is not None:
            findings.append(uncited)
        owner = _owner_finding(pattern, owner_tables, repair_ids)
        if owner is not None:
            findings.append(owner)
    return findings


def _counts(corpus: GovernanceCorpus, findings: Sequence[Finding], noise: Sequence[object], proposals: Sequence[Proposal]) -> dict[str, int]:
    return {
        "documentation": len(corpus.documentation),
        "findings": len(findings),
        "handoffs": len(corpus.handoffs),
        "harvest_blobs": len(corpus.harvest_index),
        "harvest_receipts": len(corpus.harvest_receipts),
        "noise": len(noise),
        "omc_records": len(corpus.omc_records),
        "paper_reviews": len(corpus.paper_reviews),
        "patterns": len(corpus.patterns),
        "proposals": len(proposals),
        "rules": len(corpus.rules),
        "skills": len(corpus.skills),
        "teamwork_index": len(corpus.teamwork_index),
    }


def digest_corpus(corpus: GovernanceCorpus, repairs: Sequence[RepairSpec]) -> dict[str, object]:
    """Classify an immutable corpus snapshot and emit a deterministic receipt."""
    defects = pair_defect_rows(corpus.patterns)
    blocked = _defective_ids(defects)
    findings, noise, touches = _documentation_evidence(corpus)
    findings.extend(_recurring_touch_findings(touches, corpus))
    findings.extend(_lesson_findings(corpus))
    findings.extend(_harvest_findings(corpus))
    findings.extend(_record_corpus_findings(corpus))
    findings.extend(_stale_pointer_findings(corpus))
    repair_findings, proposals = _repair_results(corpus, repairs, blocked)
    findings.extend(repair_findings)
    findings.extend(_pattern_coverage_findings(corpus, repairs, blocked))

    findings.sort(key=lambda item: item.finding_id)
    proposals.sort(key=lambda item: item.proposal_id)
    noise.sort(key=lambda item: (str(item["kind"]), str(item["source"])))
    return {
        "authority_effect": "None",
        "corpus_absent": list(corpus.absent_corpora),
        "counts": _counts(corpus, findings, noise, proposals),
        "findings": [_finding_dict(item) for item in findings],
        "noise": noise,
        "pair_defects": defects,
        "proposals": [_proposal_dict(item) for item in proposals],
        "schema": SCHEMA,
        "unstructured_counts": [
            {"corpus": name, "count": count} for name, count in corpus.unstructured_counts
        ],
    }


def _finding_dict(item: Finding) -> dict[str, object]:
    return {
        "corpus": item.corpus,
        "disposition": item.disposition,
        "evidence": [{"name": name, "value": value} for name, value in item.evidence],
        "finding_id": item.finding_id,
        "reason": item.reason,
        "source_paths": list(item.source_paths),
        "target_path": item.target_path,
        "target_section": item.target_section,
    }


def _proposal_dict(item: Proposal) -> dict[str, object]:
    return {
        "edit_kind": item.edit_kind,
        "evidence_ids": list(item.evidence_ids),
        "expected_target_hash": item.expected_target_hash,
        "locator": {
            "anchor_text": item.locator.anchor_text,
            "mode": item.locator.mode,
            "new_heading": item.locator.new_heading,
            "old_text": item.locator.old_text,
        },
        "pattern_ids": list(item.pattern_ids),
        "proposal_id": item.proposal_id,
        "repair_id": item.repair_id,
        "replacement_text": item.replacement_text,
        "target_path": item.target_path,
        "target_section": item.target_section,
    }

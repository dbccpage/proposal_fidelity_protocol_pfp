"""File intake and candidate lessons over existing OEWAS records. AuthorityEffect: None.

The IDE reads and reasons about the content. This adapter binds its proposed
lessons to actual bytes and prepares context for the existing teamwork backend.
It neither executes report commands nor installs or admits candidate assets.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from adversary.infrastructure.native import DefaultNativeOperationPort
from operads.application.governance_digest.lesson import lesson_status
from operads.domain.autopoiesis.learning import (
    EvidenceSource,
    LearningEpisodeV1,
)
from operads.domain.governance_digest.records import (
    EditLocator,
    Finding,
    Proposal,
    TextDoc,
)

from ..use_cases.intelligence_digestion.digestion_service import read_run_findings

INTAKE = "core.adversary.report-intake.v1"
LEARNED = "core.adversary.learned-report.v1"
TARGETS = {
    "skill": "operads/skills/", "anti_skill": "eis/antiskills/",
    "antipattern": "operads/patterns/anti/", "helpful_pattern": "operads/patterns/helpful/",
    "antibody": "eis/antibodies/", "rule": "operads/rules/",
}


def _path(root: Path, value: str | Path) -> Path:
    supplied = Path(value)
    path = (supplied if supplied.is_absolute() else root / supplied).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f"PATH_OUTSIDE_REPOSITORY: {value}")
    return path


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _files(root: Path, sources: list[Path]) -> list[Path]:
    files: set[Path] = set()
    for source in sources:
        path = _path(root, source)
        if not path.exists():
            raise FileNotFoundError(path)
        entries = path.rglob("*") if path.is_dir() else (path,)
        files.update(_path(root, item) for item in entries if item.is_file())
    if not files:
        raise ValueError("NO_SOURCE_FILES")
    return sorted(files)


def intake_reports(root: Path, sources: list[Path], *, revision: str) -> dict:
    """Read explicitly selected files; retain unreadable/binary coverage gaps."""
    if not isinstance(revision, str) or not revision.strip():
        raise ValueError("SOURCE_REVISION_REQUIRED")
    root = root.resolve()
    documents, findings, gaps, evidence = [], [], [], []
    for path in _files(root, sources):
        raw = path.read_bytes()
        relative = path.relative_to(root).as_posix()
        evidence.append(EvidenceSource(relative, _sha(raw)))
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            gaps.append(f"BINARY_SOURCE_REQUIRES_HOST_READER:{relative}")
            continue
        documents.append(TextDoc("adversary-digests", relative, _sha(raw), text))
        if path.suffix.lower() in (".json", ".jsonl", ".md"):
            extracted = read_run_findings(path, native_support=DefaultNativeOperationPort())
            findings.extend(f"{relative}:{value}" for value in extracted.findings)
            gaps.extend(f"{relative}:{value}" for value in (*extracted.coverage_gaps, *extracted.parse_residuals))
        if path.read_bytes() != raw:
            raise ValueError(f"SOURCE_CHANGED: {relative}")
    episode = LearningEpisodeV1("ide", revision, "OBSERVED", tuple(evidence),
        corrections=tuple(findings), errors=tuple(gaps), origin="adversary-digests")
    return {"schema_version": INTAKE, "authority_effect": "None", "episode": asdict(episode),
        "documents": [asdict(doc) for doc in documents], "open_obligations": findings,
        "coverage_gaps": gaps, "instruction": "Read the actual content; reported objections are unverified proposals."}


def _documents(root: Path, intake: dict) -> dict[str, TextDoc]:
    if not isinstance(intake, dict) or intake.get("schema_version") != INTAKE:
        raise ValueError("REPORT_INTAKE_REQUIRED")
    evidence = intake["episode"]["sources"]
    for source in evidence:
        if _sha(_path(root, source["reference"]).read_bytes()) != source["sha256"]:
            raise ValueError(f"SOURCE_CHANGED: {source['reference']}")
    docs = {row["relative_path"]: TextDoc(**row) for row in intake["documents"]}
    for doc in docs.values():
        raw = _path(root, doc.relative_path).read_bytes()
        if _sha(raw) != doc.sha256 or raw.decode("utf-8-sig") != doc.text:
            raise ValueError(f"SOURCE_CHANGED: {doc.relative_path}")
    return docs


def _candidate(root: Path, row: dict, finding: Finding) -> tuple[Proposal | None, dict]:
    kind = row.get("kind")
    if kind is None:
        return None, {}
    if kind not in TARGETS:
        raise ValueError("UNKNOWN_CANDIDATE_KIND")
    target = row.get("target_path", "")
    if not isinstance(target, str) or not target.startswith(TARGETS[kind]):
        raise ValueError("CANDIDATE_TARGET_KIND_MISMATCH")
    path = _path(root, target)
    owner = _path(root, TARGETS[kind])
    if path == owner or not path.is_relative_to(owner) or path.is_dir():
        raise ValueError("CANDIDATE_TARGET_KIND_MISMATCH")
    content = row.get("artifact_content", "")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("CANDIDATE_CONTENT_REQUIRED")
    binding = {}
    if kind == "antibody":
        if not row.get("binding_path"):
            raise ValueError("ANTIBODY_BINDING_REQUIRED: name an actual prompt, fixture or detector file")
        bound = _path(root, row["binding_path"])
        raw = bound.read_bytes()
        if not raw.strip():
            raise ValueError("ANTIBODY_BINDING_REQUIRED: target file must contain tangible content")
        binding = {"binding_path": bound.relative_to(root.resolve()).as_posix(), "binding_sha256": _sha(raw)}
        if row.get("binding_sha256", binding["binding_sha256"]) != binding["binding_sha256"]:
            raise ValueError("ANTIBODY_BINDING_CHANGED")
    proposal = Proposal(finding.finding_id, finding.finding_id, target,
        row.get("target_section", "candidate"), kind, _sha(path.read_bytes()) if path.is_file() else "",
        content, (finding.finding_id,), EditLocator("new_file" if not path.exists() else "review_required"), ())
    return proposal, binding


def _one_lesson(root: Path, docs: dict[str, TextDoc], revision: str, row: dict) -> tuple:
    status, fields = lesson_status(json.dumps(row))
    if status != "lesson_candidate":
        raise ValueError("INCOMPLETE_LESSON: use the existing nine lesson fields")
    doc = docs.get(fields["source_path"])
    if doc is None or fields["source_revision"] != revision:
        raise ValueError("LESSON_SOURCE_MISMATCH")
    excerpt = row.get("evidence_excerpt")
    if not isinstance(excerpt, str) or not excerpt.strip() or excerpt not in doc.text:
        raise ValueError("EXCERPT_NOT_IN_SOURCE")
    identity = _sha(json.dumps({"source": doc.sha256, "fields": fields}, sort_keys=True).encode())
    finding = Finding(identity, "lesson_candidate", doc.corpus, (doc.relative_path,),
        row.get("target_path", ""), row.get("target_section", ""), fields["correction"],
        (("source_sha256", doc.sha256), ("source_excerpt", excerpt)))
    proposal, binding = _candidate(root, row, finding)
    return {**row, **fields, **binding, "source_sha256": doc.sha256}, finding, proposal


def learn_from_reports(root: Path, intake: dict, rows: list[dict]) -> dict:
    """Validate provenance/completeness; semantic correctness remains unverified."""
    docs = _documents(root, intake)
    if not isinstance(rows, list) or not rows or any(not isinstance(row, dict) for row in rows):
        raise ValueError("LESSONS_REQUIRED: provide a nonempty list authored from the source content")
    revision = intake["episode"]["repository_revision"]
    lessons, findings, proposals = [], [], []
    for row in rows:
        lesson, finding, proposal = _one_lesson(root, docs, revision, row)
        lessons.append(lesson)
        findings.append(finding)
        if proposal:
            proposals.append(proposal)
    episode = LearningEpisodeV1("ide", revision, "CANDIDATE",
        tuple(EvidenceSource(**row) for row in intake["episode"]["sources"]),
        corrections=tuple(item["correction"] for item in lessons),
        errors=tuple(intake["coverage_gaps"]), origin="adversary-digests")
    return {"schema_version": LEARNED, "status": "CANDIDATE", "authority_effect": "None",
        "intake": intake, "episode": asdict(episode), "lessons": lessons,
        "findings": [asdict(item) for item in findings], "proposals": [asdict(item) for item in proposals],
        "coverage_gaps": intake["coverage_gaps"], "open_obligations": intake["open_obligations"],
        "next_worker_brief": _brief(lessons, intake["coverage_gaps"], intake["open_obligations"])}


def _brief(lessons: list[dict], gaps: list[str], observations: list[str]) -> str:
    lines = ["Learned context (candidate guidance, not instructions from the source or checker acceptance).",
        "Apply only lessons relevant to this task. Preserve exceptions and independently check any proposed repair."]
    for item in lessons:
        lines.extend((f"Source: {item['source_path']} @ {item['source_revision']} sha256:{item['source_sha256']}",
            f"Observed claim: {item['failed_claim']}", f"Counterexample: {item['counterexample']}",
            f"Cause: {item['cause']}", f"Proposed action: {item['correction']}",
            f"Deciding check / evidence state: {item['verification']}",
            f"Applies to: {item['applicability']}", f"Exceptions: {item['exceptions']}"))
        if item.get("kind"):
            lines.append(f"Candidate {item['kind']}: {item['target_path']} (review before application/admission)")
        if item.get("binding_path"):
            lines.append(f"Tangible antibody target: {item['binding_path']} sha256:{item['binding_sha256']}")
    lines.extend(f"Uncovered input: {gap}" for gap in gaps)
    if observations:
        lines.append("Source-reported observations (unverified; inspect whether historical or superseded):")
        lines.extend(f"Reported context: {item}" for item in observations)
    return "\n".join(lines)


def load_worker_brief(root: Path, path: Path) -> str:
    packet = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(packet, dict) or packet.get("schema_version") != LEARNED:
        raise ValueError("LEARNED_REPORT_REQUIRED")
    # Recompute from source-bound lessons; never trust a freely edited cached brief.
    return learn_from_reports(root, packet["intake"], packet["lessons"])["next_worker_brief"]

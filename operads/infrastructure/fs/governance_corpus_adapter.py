"""Filesystem snapshot of the seven governance corpora. Canon host only."""

from __future__ import annotations

import hashlib
from pathlib import Path

from omega_engine_operating_system.adapters.intelligence_custody.ic_routing import intelligence_path

from ...application.governance_digest.textops import sha256_text
from ...application.ports.governance_corpus_port import GovernanceCorpusPort
from ...domain.governance_digest.records import (
    REQUIRED_FRONTMATTER,
    GovernanceCorpus,
    IndexedFile,
    PatternDoc,
    TextDoc,
)

_PATTERN_NAMES = ("AP_", "HP_")
_READ_SUFFIXES = {".json", ".jsonl", ".md"}
_LESSON_OR_AUDIT = ("verdict", "decisive_blockers", "failed_claim", "source_path")


def _read(path: Path) -> str:
    with path.open(encoding="utf-8", newline="") as handle:
        return handle.read()


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end]
    body = text[end + 4 :]
    fields: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"').strip("'")
    return fields, body.lstrip("\n")


def _detection(body: str) -> str:
    marker = "## Detection Signature"
    start = body.find(marker)
    if start == -1:
        return ""
    rest = body[start + len(marker) :]
    next_heading = rest.find("\n## ")
    chunk = rest if next_heading == -1 else rest[:next_heading]
    return chunk.strip()


def _applicability(value: str) -> tuple[str, ...]:
    if not value:
        return ()
    inner = value.strip().strip("[]")
    if not inner:
        return ()
    return tuple(part.strip().strip('"').strip("'") for part in inner.split(",") if part.strip())


class FsGovernanceCorpusAdapter(GovernanceCorpusPort):
    """Load ``.agents`` and ``_intelligence`` canon trees. Mirrors are not a second source."""

    def __init__(self, workspace: Path) -> None:
        self._root = workspace

    def load(self) -> GovernanceCorpus:
        agents = self._root / ".agents"
        def path(relative: str) -> Path:
            return intelligence_path(self._root, relative)
        documentation = self._texts(agents / "documentation", "documentation")
        patterns = self._patterns(agents / "patterns" if (agents / "patterns").is_dir() else agents / "anti_pattern")
        teamwork_index, handoffs = self._teamwork(agents / "teamwork")
        harvest_receipts, harvest_index = self._harvest(path("_intelligence/harvest"))
        omc_records, omc_unstructured = self._audits(path("_intelligence/omc_dags"), "omc_dags")
        reviews, review_unstructured = self._audits(path("_intelligence/omega_paper_reviews"), "omega_paper_reviews")
        absent: list[str] = []
        runs = path("_intelligence/symbol_game/runs")
        stale: list[TextDoc] = []
        if not runs.is_dir():
            absent.append("_intelligence/symbol_game/runs")
            pointer = path("_intelligence/symbol_game/runs_synthesis_and_learnings.md")
            if pointer.is_file():
                text = _read(pointer)
                stale.append(
                    TextDoc(
                        "symbol_game",
                        "_intelligence/symbol_game/runs_synthesis_and_learnings.md",
                        sha256_text(text),
                        text,
                    )
                )
        rules = self._texts(agents / "rules", "rules")
        skills = self._skill_docs(agents / "skills")
        return GovernanceCorpus(
            documentation=tuple(documentation),
            patterns=tuple(patterns),
            teamwork_index=tuple(teamwork_index),
            handoffs=tuple(handoffs),
            harvest_receipts=tuple(harvest_receipts),
            harvest_index=tuple(harvest_index),
            omc_records=tuple(omc_records),
            paper_reviews=tuple(reviews),
            unstructured_counts=(
                ("omc_dags", omc_unstructured),
                ("omega_paper_reviews", review_unstructured),
            ),
            absent_corpora=tuple(absent),
            stale_pointers=tuple(stale),
            rules=tuple(rules),
            skills=tuple(skills),
        )

    def _texts(self, root: Path, corpus: str) -> list[TextDoc]:
        if not root.is_dir():
            return []
        docs: list[TextDoc] = []
        for path in sorted(item for item in root.rglob("*") if item.is_file() and item.suffix == ".md"):
            text = _read(path)
            docs.append(TextDoc(corpus, path.relative_to(self._root).as_posix(), sha256_text(text), text))
        return docs

    def _patterns(self, root: Path) -> list[PatternDoc]:
        if not root.is_dir():
            return []
        docs: list[PatternDoc] = []
        for path in sorted(root.rglob("*.md")):
            if not path.name.startswith(_PATTERN_NAMES):
                continue
            text = _read(path)
            fields, body = _frontmatter(text)
            docs.append(
                PatternDoc(
                    relative_path=path.relative_to(self._root).as_posix(),
                    sha256=sha256_text(text),
                    pattern_id=fields.get("pattern_id", ""),
                    name=fields.get("name", ""),
                    category=fields.get("category", ""),
                    language=fields.get("language", ""),
                    dual_pattern=fields.get("dual_pattern", ""),
                    frontmatter_keys=tuple(key for key in REQUIRED_FRONTMATTER if key in fields),
                    detection_text=_detection(body),
                    applicability=_applicability(fields.get("applicability", "")),
                )
            )
        return docs

    def _teamwork(self, root: Path) -> tuple[list[IndexedFile], list[TextDoc]]:
        index: list[IndexedFile] = []
        handoffs: list[TextDoc] = []
        if not root.is_dir():
            return index, handoffs
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            relative = path.relative_to(self._root).as_posix()
            if path.name == "handoff.md":
                text = _read(path)
                handoffs.append(TextDoc("teamwork", relative, sha256_text(text), text))
                index.append(IndexedFile("teamwork", relative, sha256_text(text)))
            else:
                index.append(IndexedFile("teamwork", relative, _hash_file(path)))
        return index, handoffs

    def _harvest(self, root: Path) -> tuple[list[TextDoc], list[IndexedFile]]:
        receipts: list[TextDoc] = []
        index: list[IndexedFile] = []
        if not root.is_dir():
            return receipts, index
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            relative = path.relative_to(self._root).as_posix()
            if path.name.endswith(".receipt.json"):
                text = _read(path)
                receipts.append(TextDoc("harvest", relative, sha256_text(text), text))
            else:
                index.append(IndexedFile("harvest", relative, _hash_file(path)))
        return receipts, index

    def _audits(self, root: Path, corpus: str) -> tuple[list[TextDoc], int]:
        kept: list[TextDoc] = []
        skipped = 0
        if not root.is_dir():
            return kept, skipped
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            if path.suffix.lower() not in _READ_SUFFIXES:
                skipped += 1
                continue
            text = _read(path)
            if not any(token in text for token in _LESSON_OR_AUDIT):
                skipped += 1
                continue
            if path.suffix.lower() == ".md" and "decisive_blockers" not in text and "verdict" not in text:
                if "failed_claim" not in text:
                    skipped += 1
                    continue
            kept.append(TextDoc(corpus, path.relative_to(self._root).as_posix(), sha256_text(text), text))
        return kept, skipped

    def _skill_docs(self, root: Path) -> list[TextDoc]:
        if not root.is_dir():
            return []
        docs: list[TextDoc] = []
        for path in sorted(root.rglob("SKILL.md")):
            text = _read(path)
            docs.append(TextDoc("skills", path.relative_to(self._root).as_posix(), sha256_text(text), text))
        return docs


class FsTextStore:
    """Canon read and write used by apply. Mirror copies use the same root."""

    def __init__(self, workspace: Path) -> None:
        self._root = workspace

    def read(self, relative_path: str) -> str | None:
        path = self._root / relative_path
        if not path.is_file():
            return None
        return _read(path)

    def write(self, relative_path: str, text: str) -> None:
        path = self._root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(text)

"""Documentation-integrity bounded-context module. AuthorityEffect: None."""

from __future__ import annotations

try:
    import yaml
except ModuleNotFoundError:
    yaml = None

import re
from pathlib import Path
from typing import Any

from omega_engine_pfp.domain.documentation_integrity.models import FindingLedger
from omega_engine_pfp.domain.documentation_integrity.policies import (
    extension_kind as extension_kind,
)
from omega_engine_pfp.domain.documentation_integrity.policies import (
    is_document_relative_path as is_document_relative_path,
)

SCRIPT_PATH = Path(__file__).resolve()


_REPO = next(
    (
        p
        for p in SCRIPT_PATH.parents
        if (p / ".git").exists() or (p / "omega_engine_education").is_dir()
    ),
    SCRIPT_PATH.parents[2],
)


DOC_ROOT = (
    _REPO
    / "omega_engine_education"
    / "documentation"
    / "030_the_symbol_game_proposal_fidelity_protocol_pfp"
)


META_ROOT = DOC_ROOT / "_meta"


CONTRACT_PATH = META_ROOT / "documentation-contract.json"


EXEMPTIONS_PATH = META_ROOT / "source-exemptions.json"


LEDGER_PATH = META_ROOT / "source-ledger.jsonl"


MIGRATION_MAP_PATH = META_ROOT / "migration-map.json"


EDUCATION_LOCK_PATH = META_ROOT / "education-copy-lock.json"


ARCHIVE_LOCK_PATH = META_ROOT / "archive-lock.json"


ACTIVE_PATH_MAP_PATH = DOC_ROOT / "migration" / "active-path-map.json"


SHA256_CHUNK_SIZE = 1024 * 1024


MARKDOWN_SUFFIXES = {".md", ".markdown", ".mdown"}


MOJIBAKE_MARKERS = ("\ufffd", "Ã", "Â", "â€", "ðŸ", "ï»¿")


MAPPING_STATUSES = {"mapped", "exempt"}


IMAGE_LINK_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


INLINE_LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")


HTML_IMAGE_RE = re.compile(r"<img\b[^>]*\balt\s*=\s*([\"'])(.*?)\1[^>]*>", re.IGNORECASE)


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")


HTML_ANCHOR_RE = re.compile(r"<a\b[^>]*\bid\s*=\s*([\"'])(.*?)\1[^>]*>", re.IGNORECASE)


class IntegrityError(RuntimeError):
    """Raised for a configuration or generated-manifest contract violation."""


Findings = FindingLedger


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    raise IntegrityError(f"Could not find a Git repository above {start}")


def repo_relative(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def absolute_repo_path(repo_root: Path, relative_path: str) -> Path:
    return repo_root.joinpath(*relative_path.split("/"))


def source_root_paths(contract: dict[str, Any]) -> list[str]:
    return [entry["path"].rstrip("/") for entry in contract["source_roots"]]


def root_for_path(contract: dict[str, Any], source_path: str) -> dict[str, Any]:
    candidates = [
        entry
        for entry in contract["source_roots"]
        if source_path == entry["path"] or source_path.startswith(entry["path"].rstrip("/") + "/")
    ]
    if not candidates:
        raise IntegrityError(f"No source root owns {source_path}")
    return max(candidates, key=lambda entry: len(entry["path"]))


def is_control_artifact(contract: dict[str, Any], source_path: str) -> bool:
    return source_path in set(contract["generated_control_artifacts"])


def copy_set_for_path(contract: dict[str, Any], source_path: str) -> dict[str, Any] | None:
    for copy_set in contract["education_copy_sets"]:
        prefix = copy_set["source_prefix"].rstrip("/")
        if source_path.startswith(prefix + "/"):
            return copy_set
    return None


def planned_asset_destination(relative: str) -> str:
    parent = relative.rsplit("/", 1)[0] if "/" in relative else ""
    return f"{parent}/README.md" if parent else "README.md"

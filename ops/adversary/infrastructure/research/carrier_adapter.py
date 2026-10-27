"""Infrastructure adapter for paper carrier, tree hashing, YAML loaders, and program profiles.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

from adversary.domain.research.paper_run_graph import (
    AUTHORITY_EFFECT,
    ClaimIRDocument,
    ClaimKind,
    ClaimNode,
    PaperRunGraphError,
)
from adversary.domain.research.program_profile import ProgramProfile
from adversary.domain.research.protocols import (
    PaperCarrierPort,
)
from adversary.infrastructure.research.tree_hash import (
    SnapshotError,
    tree_sha256,
)

_PROFILES_DIR = Path(__file__).resolve().parents[2] / "program_profiles" / "research"
_MAP_PATH = _PROFILES_DIR / "skill_program_map.yaml"


def _load_yaml(path: Path) -> Any:
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover
        raise PaperRunGraphError("PyYAML required to read YAML file") from exc
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _kind_from_claim_ir_class(mech: str) -> ClaimKind:
    m = (mech or "").upper()
    if "LEAN" in m and "TOY" not in m:
        return ClaimKind.MECHANIZATION
    if "LEAN_TOY" in m or "TOY" in m:
        return ClaimKind.THEOREM
    if "PYTHON" in m or "NUMERICAL" in m or "INSTANCE" in m or "EXACT" in m:
        return ClaimKind.COMPUTATIONAL
    if "SCOPE" in m or "FENCE" in m or "NONCLAIM" in m:
        return ClaimKind.SCOPE_FENCE
    if "PROSE" in m:
        return ClaimKind.THEOREM
    if "CITATION" in m or "LITERATURE" in m:
        return ClaimKind.LITERATURE
    return ClaimKind.UNKNOWN


def parse_claim_ir(root: Path) -> list[ClaimNode]:
    ir = root / "docs" / "claim_ir.yaml"
    if not ir.is_file():
        return []
    doc = ClaimIRDocument.from_yaml(ir.read_text(encoding="utf-8"))
    return doc.to_claim_nodes()


def parse_ledger_ids(root: Path) -> list[ClaimNode]:
    """Fallback: rough claim IDs from claim ledger markdown."""
    hits = list(root.glob("*_claim_ledger.md")) + list(root.glob("*claim_ledger*.md"))
    if not hits:
        return []
    text = hits[0].read_text(encoding="utf-8", errors="replace")
    ids = sorted(set(re.findall(r"\b([A-Z]\d{1,3}|[A-Z]{1,3}-\d{2,4})\b", text)))
    return [
        ClaimNode(claim_id=i, kind="unknown", claim_ceiling="UNKNOWN")
        for i in ids[:80]
    ]


def parse_claims(paper_root: Path | str) -> list[ClaimNode]:
    root = Path(paper_root).resolve()
    claims = parse_claim_ir(root)
    if not claims:
        claims = parse_ledger_ids(root)
    if not claims:
        claims = [
            ClaimNode(
                claim_id="PKG",
                kind=ClaimKind.RELEASE.value,
                claim_ceiling="DECLARED",
            )
        ]
    return claims


def compute_carrier_hash(paper_root: Path | str) -> str:
    root = Path(paper_root).resolve()
    if not root.is_dir():
        raise PaperRunGraphError(f"not a directory: {root}")
    try:
        return tree_sha256(root)
    except SnapshotError as exc:
        raise PaperRunGraphError(str(exc)) from exc


def list_program_ids(profiles_dir: Optional[Path] = None) -> list[str]:
    d = profiles_dir or _PROFILES_DIR
    if not d.is_dir():
        return []
    return sorted(
        p.stem
        for p in d.glob("*.yaml")
        if p.stem not in ("__init__", "skill_program_map")
    )


def load_skill_program_map(map_path: Optional[Path] = None) -> dict[str, Any]:
    path = map_path or _MAP_PATH
    if not path.is_file():
        return {
            "schema_version": "urn:core:rip:skill_program_map:v0.1",
            "mappings": {},
            "aliases": {},
        }
    data = _load_yaml(path)
    if not isinstance(data, dict):
        raise PaperRunGraphError(f"invalid skill map: {path}")
    return data


def resolve_program_id(
    name: str,
    *,
    map_path: Optional[Path] = None,
    profiles_dir: Optional[Path] = None,
) -> str:
    """Resolve skill name, alias, or bare profile id -> profile id."""
    raw = (name or "").strip()
    if not raw:
        raise PaperRunGraphError("empty program id")
    key = raw.lower().replace("_", "-")
    data = load_skill_program_map(map_path)
    mappings = {str(k).lower(): str(v) for k, v in (data.get("mappings") or {}).items()}
    aliases = {
        str(k).lower().replace("_", "-"): str(v)
        for k, v in (data.get("aliases") or {}).items()
    }

    if key in mappings:
        return mappings[key]
    if key.startswith("rip-program-") and key in mappings:
        return mappings[key]
    if key in aliases:
        return aliases[key]
    if key in list_program_ids(profiles_dir):
        return key
    skill_key = f"rip-program-{key}"
    if skill_key in mappings:
        return mappings[skill_key]
    known = list_program_ids(profiles_dir)
    raise PaperRunGraphError(
        f"unknown program {raw!r}; known_profiles={known}; "
        f"or use mapped skill names from skill_program_map.yaml"
    )


def load_program_profile(
    program_id: str,
    *,
    profiles_dir: Optional[Path] = None,
) -> ProgramProfile:
    pid = resolve_program_id(program_id, profiles_dir=profiles_dir)
    d = profiles_dir or _PROFILES_DIR
    path = d / f"{pid}.yaml"
    if not path.is_file():
        known = list_program_ids(d)
        raise PaperRunGraphError(
            f"unknown program {pid!r}; known={known}. "
            "Profiles live under adversary/program_profiles/research/ "
            "(host data, not skills)."
        )
    return ProgramProfile.from_yaml(path.read_text(encoding="utf-8"))


def guess_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for _ in range(12):
        if (cur / "engine_py").is_dir() and (cur / "engine").is_dir():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return Path(__file__).resolve().parents[3]


def enforce_estate_path_gate(
    paper_root: Path | str,
    profile: ProgramProfile,
    *,
    repo_root: Optional[Path] = None,
) -> None:
    if not profile.estate_paths:
        return
    paper = Path(paper_root).resolve()
    paper_posix = paper.as_posix()
    root = (repo_root or guess_repo_root(paper)).resolve()
    for rel in profile.estate_paths:
        norm = str(rel).replace("\\", "/").strip("/")
        if norm and (
            f"/{norm}/" in f"/{paper_posix}/"
            or paper_posix.endswith(f"/{norm}")
            or paper_posix.endswith(norm)
        ):
            return
        p = Path(rel)
        cand = (p if p.is_absolute() else (root / rel)).resolve()
        try:
            paper.relative_to(cand)
            return
        except ValueError:
            try:
                cand.relative_to(paper)
                return
            except ValueError:
                continue
    raise PaperRunGraphError(
        f"estate path gate: paper {paper} is outside program {profile.id} "
        f"estate_paths={profile.estate_paths}"
    )


def archive_readiness_report(
    *,
    skills_dir: Optional[Path] = None,
    map_path: Optional[Path] = None,
    profiles_dir: Optional[Path] = None,
) -> dict[str, Any]:
    root = skills_dir or Path(__file__).resolve().parents[3] / "operads" / "skills"
    if not root.is_dir():
        root = Path.cwd() / "operads" / "skills"
    data = load_skill_program_map(map_path)
    mappings = {str(k): str(v) for k, v in (data.get("mappings") or {}).items()}
    on_disk = (
        sorted(
            p.name
            for p in root.iterdir()
            if p.is_dir() and p.name.startswith("rip-program-")
        )
        if root.is_dir()
        else []
    )
    profiles = set(list_program_ids(profiles_dir))
    rows = []
    for skill in on_disk:
        pid = mappings.get(skill) or mappings.get(skill.lower())
        profile_ok = bool(pid and pid in profiles)
        rows.append(
            {
                "skill": skill,
                "profile_id": pid or None,
                "profile_exists": profile_ok,
                "archive_ready": profile_ok,
                "cull_ready": profile_ok,
            }
        )
    mapped_missing = [s for s, p in mappings.items() if p not in profiles]
    culled = len(on_disk) == 0 and len(mappings) > 0 and not mapped_missing
    if culled:
        ready = True
        note = (
            "CULLED. rip-program-* skill folders removed from agent hosts "
            "(operator-authorized after planned_deletions list). "
            "Use /rip-papers + plan --program <id>; map still lists historical skill names."
        )
    else:
        ready = (
            all(r["archive_ready"] for r in rows)
            and not mapped_missing
            and len(rows) > 0
        )
        note = (
            "Host twins under program_profiles/. Prefer: /rip-papers + plan --program <id>. "
            "Mass-delete only after a written planned_deletions list (operator)."
        )
    return {
        "schema_version": "urn:core:rip:archive_readiness:v0.1",
        "authority_effect": AUTHORITY_EFFECT,
        "skills_dir": str(root),
        "skills_on_disk": on_disk,
        "rows": rows,
        "mapped_but_missing_profile": mapped_missing,
        "all_archive_ready": ready,
        "all_cull_ready": ready,
        "skills_culled": culled,
        "delete_skills_now": False,
        "delete_forbidden": not culled,
        "archive_only": not culled,
        "note": note,
    }


def cull_readiness_report(
    *,
    skills_dir: Optional[Path] = None,
    map_path: Optional[Path] = None,
    profiles_dir: Optional[Path] = None,
) -> dict[str, Any]:
    return archive_readiness_report(
        skills_dir=skills_dir, map_path=map_path, profiles_dir=profiles_dir
    )


class DefaultPaperCarrierAdapter(PaperCarrierPort):
    """Default filesystem carrier implementation of PaperCarrierPort."""

    def compute_tree_hash(self, paper_root: Path | str) -> str:
        return compute_carrier_hash(paper_root)

    def parse_claims(self, paper_root: Path | str) -> list[ClaimNode]:
        return parse_claims(paper_root)

    def load_program_profile(
        self,
        program_id: str,
        *,
        profiles_dir: Path | None = None,
    ) -> ProgramProfile:
        return load_program_profile(program_id, profiles_dir=profiles_dir)

    def enforce_estate_path_gate(
        self,
        paper_root: Path | str,
        profile: ProgramProfile,
        *,
        repo_root: Path | None = None,
    ) -> None:
        enforce_estate_path_gate(paper_root, profile, repo_root=repo_root)

    def list_program_ids(self, profiles_dir: Path | None = None) -> list[str]:
        return list_program_ids(profiles_dir)

    def load_skill_program_map(self, map_path: Path | None = None) -> dict[str, Any]:
        return load_skill_program_map(map_path)

    def resolve_program_id(
        self,
        name: str,
        *,
        map_path: Path | None = None,
        profiles_dir: Path | None = None,
    ) -> str:
        return resolve_program_id(name, map_path=map_path, profiles_dir=profiles_dir)


__all__ = [
    "DefaultPaperCarrierAdapter",
    "archive_readiness_report",
    "compute_carrier_hash",
    "cull_readiness_report",
    "enforce_estate_path_gate",
    "guess_repo_root",
    "list_program_ids",
    "load_program_profile",
    "load_skill_program_map",
    "parse_claim_ir",
    "parse_claims",
    "parse_ledger_ids",
    "resolve_program_id",
]

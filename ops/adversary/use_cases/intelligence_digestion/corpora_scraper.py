"""Corpora Ingestion, Mining, and Archival Pipeline.

Scrapes and extracts metadata, failure modes, anti-patterns, and forensic
receipts from ephemeral/staging directories (.agents/anti_pattern, .agents/teamwork),
farms defect patterns into candidate antibodies, indexes sessions, and moves
terminally digested source assets into _ic/nara/_archive/.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from eis.domain.pharmacy_seeder import PharmacySeeder
from eis.infrastructure.pharmacy_writer import (
    filesystem_byte_writer,
    filesystem_catalog_bytes,
)
from governance.domain.intelligence_community import canonical_intelligence_route

CORPORA_MANIFEST_SCHEMA = "core.intelligence.corpora-archive-manifest.v1"
ANTI_PATTERNS_REGISTRY_SCHEMA = "core.intelligence.anti-patterns-registry.v1"
TEAMWORK_INDEX_SCHEMA = "core.intelligence.teamwork-archive-index.v1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dir_tree_sha256(directory: Path) -> str:
    hasher = hashlib.sha256()
    for file_path in sorted(directory.rglob("*"), key=lambda p: p.as_posix()):
        if file_path.is_file():
            hasher.update(file_path.relative_to(directory).as_posix().encode("utf-8"))
            hasher.update(file_path.read_bytes())
    return hasher.hexdigest()


def _parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    frontmatter: Dict[str, Any] = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            raw_yaml = parts[1]
            body = parts[2].strip()
            for line in raw_yaml.splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if val.startswith("[") and val.endswith("]"):
                        items = [item.strip().strip('"').strip("'") for item in val[1:-1].split(",") if item.strip()]
                        frontmatter[key] = items
                    else:
                        frontmatter[key] = val
    return frontmatter, body


@dataclass
class ScrapedAntiPattern:
    pattern_id: str
    name: str
    language: str
    category: str
    dual_pattern: str
    file_path: str
    file_sha256: str
    description: str = ""
    detection_signature: str = ""
    hazard: str = ""
    dual_healthy_pattern: str = ""


@dataclass
class ScrapedTeamworkSession:
    session_id: str
    role_prefix: str
    session_path: str
    tree_sha256: str
    file_count: int
    total_bytes: int
    has_handoff: bool
    verdict: str = "UNKNOWN"
    auditor: str = ""
    work_product: str = ""
    parent_conversation_id: str = ""
    forensic_checks: List[Dict[str, str]] = field(default_factory=list)
    failure_modes: List[str] = field(default_factory=list)
    test_scripts: List[Dict[str, str]] = field(default_factory=list)


class CorporaScraper:
    """Scrapes, mines antibodies, and terminally archives anti_pattern and teamwork directories."""

    def __init__(self, repo_root: Optional[Path] = None) -> None:
        if repo_root is not None:
            self.repo_root = Path(repo_root).resolve()
        else:
            self.repo_root = Path(__file__).resolve().parents[3]
        self.intelligence_root = self.repo_root / "_ic"
        self.archive_root = self.repo_root / canonical_intelligence_route("_intelligence/archive")
        self.seeder = PharmacySeeder(
            self.repo_root,
            byte_writer=filesystem_byte_writer,
            byte_source=filesystem_catalog_bytes,
        )

    def scrape_anti_patterns(self, source_dir: Path) -> List[ScrapedAntiPattern]:
        patterns: List[ScrapedAntiPattern] = []
        if not source_dir.is_dir():
            return patterns

        for file_path in sorted(source_dir.glob("*/*.md"), key=lambda p: p.as_posix()):
            text = file_path.read_text(encoding="utf-8")
            frontmatter, body = _parse_frontmatter(text)
            pattern_id = frontmatter.get("pattern_id") or file_path.stem
            name = frontmatter.get("name") or file_path.stem
            lang = frontmatter.get("language") or file_path.parent.name
            category = frontmatter.get("category") or ("anti_pattern" if "AP_" in file_path.name else "healthy_pattern")
            dual = frontmatter.get("dual_pattern") or ""

            # Extract sections
            desc = ""
            det = ""
            hazard = ""
            dual_hp = ""

            sections = re.split(r"\n##\s+", "\n" + body)
            for sec in sections:
                sec_lines = sec.strip().splitlines()
                if not sec_lines:
                    continue
                header = sec_lines[0].lower()
                content = "\n".join(sec_lines[1:]).strip()
                if "description" in header:
                    desc = content
                elif "detection" in header:
                    det = content
                elif "hazard" in header or "failure" in header:
                    hazard = content
                elif "dual" in header or "healthy" in header:
                    dual_hp = content

            patterns.append(
                ScrapedAntiPattern(
                    pattern_id=str(pattern_id),
                    name=str(name),
                    language=str(lang),
                    category=str(category),
                    dual_pattern=str(dual),
                    file_path=file_path.relative_to(self.repo_root).as_posix(),
                    file_sha256=_file_sha256(file_path),
                    description=desc,
                    detection_signature=det,
                    hazard=hazard,
                    dual_healthy_pattern=dual_hp,
                )
            )
        return patterns

    def scrape_teamwork_session(self, session_dir: Path) -> ScrapedTeamworkSession:
        session_id = session_dir.name
        role_prefix = session_id.split("_")[0]
        files = [p for p in session_dir.rglob("*") if p.is_file()]
        total_bytes = sum(p.stat().st_size for p in files)
        tree_hash = _dir_tree_sha256(session_dir)

        test_scripts: List[Dict[str, str]] = []
        for p in files:
            if p.name.startswith("test_") and p.name.endswith(".py"):
                test_scripts.append({
                    "name": p.relative_to(session_dir).as_posix(),
                    "sha256": _file_sha256(p),
                    "size_bytes": p.stat().st_size,
                })

        handoff_file = session_dir / "handoff.md"
        has_handoff = handoff_file.is_file()

        verdict = "UNKNOWN"
        auditor = ""
        work_product = ""
        parent_conv_id = ""
        forensic_checks: List[Dict[str, str]] = []
        failure_modes: List[str] = []

        if has_handoff:
            text = handoff_file.read_text(encoding="utf-8")

            # Extract fields
            v_match = re.search(r"\*\*Verdict\*\*:\s*([^\n\r]+)", text)
            if v_match:
                verdict = v_match.group(1).strip()

            a_match = re.search(r"\*\*Auditor\*\*:\s*`?([^`\n\r]+)`?", text)
            if a_match:
                auditor = a_match.group(1).strip()

            w_match = re.search(r"\*\*Work Product\*\*:\s*([^\n\r]+)", text)
            if w_match:
                work_product = w_match.group(1).strip()

            p_match = re.search(r"\*\*Parent Conversation ID\*\*:\s*`?([a-f0-9-]+)`?", text)
            if p_match:
                parent_conv_id = p_match.group(1).strip()

            # Forensic checks table
            table_matches = re.findall(r"\|\s*(\d+)\s*\|\s*\*\*([^*]+)\*\*\s*\|\s*\*\*([^*]+)\*\*\s*\|\s*([^|]+)\|", text)
            for tm in table_matches:
                forensic_checks.append({
                    "index": tm[0].strip(),
                    "check": tm[1].strip(),
                    "outcome": tm[2].strip(),
                    "key_finding": tm[3].strip(),
                })

            # Harvest explicit failure / violation lines
            for line in text.splitlines():
                s = line.strip()
                if any(w in s.lower() for w in ["fail", "violation", "defect", "blocker", "bypass", "unmitigated", "cheat", "tamper"]):
                    if 15 < len(s) < 140 and s.startswith(("-", "*", "1.", "2.", "3.", "4.", "5.")):
                        # Clean markdown bullets
                        cleaned = re.sub(r"^[-*\d.]+\s*", "", s).strip()
                        cleaned = re.sub(r"[*`_]", "", cleaned).strip()
                        if cleaned and len(cleaned) > 10:
                            failure_modes.append(cleaned)

        return ScrapedTeamworkSession(
            session_id=session_id,
            role_prefix=role_prefix,
            session_path=session_dir.relative_to(self.repo_root).as_posix(),
            tree_sha256=tree_hash,
            file_count=len(files),
            total_bytes=total_bytes,
            has_handoff=has_handoff,
            verdict=verdict,
            auditor=auditor,
            work_product=work_product,
            parent_conversation_id=parent_conv_id,
            forensic_checks=forensic_checks,
            failure_modes=sorted(dict.fromkeys(failure_modes)),
            test_scripts=test_scripts,
        )

    def scrape_all_teamwork_sessions(self, source_dir: Path) -> List[ScrapedTeamworkSession]:
        sessions: List[ScrapedTeamworkSession] = []
        if not source_dir.is_dir():
            return sessions

        for session_dir in sorted(source_dir.iterdir(), key=lambda p: p.name):
            if session_dir.is_dir():
                sessions.append(self.scrape_teamwork_session(session_dir))
        return sessions

    def farm_antibodies_from_sessions(self, sessions: List[ScrapedTeamworkSession]) -> Dict[str, Any]:
        """Collects unique failure modes and passes them to PharmacySeeder."""
        all_defects: List[Tuple[str, str, str]] = []
        for s in sessions:
            for failure in s.failure_modes:
                all_defects.append((failure, s.session_id, f"teamwork:{s.session_id}"))

        farmed_total = 0
        preserved_total = 0
        refused_retired_total = 0

        # Farm in bounded batches by session
        for s in sessions:
            if s.failure_modes:
                # Top 3 most specific failure modes per session to avoid flood
                specific_failures = [f for f in s.failure_modes if not f.startswith("Output:") and len(f) > 20][:3]
                if specific_failures:
                    farmed = self.seeder.farm_antibodies_from_defects(
                        specific_failures,
                        run_id=s.session_id,
                        task_id=f"teamwork:{s.session_id}",
                    )
                    farmed_total += len(farmed)
                    preserved_total += len(self.seeder.preserved_judged)
                    refused_retired_total += len(self.seeder.refused_retired)

        return {
            "farmed_antibodies_count": farmed_total,
            "preserved_judged_count": preserved_total,
            "refused_retired_count": refused_retired_total,
        }

    def execute_mining_and_archival(self, dry_run: bool = False) -> Dict[str, Any]:
        start_time = _now()
        teamwork_src = self.repo_root / ".agents" / "teamwork"
        anti_pattern_src = self.repo_root / ".agents" / "anti_pattern"

        archive_teamwork_dest = self.archive_root / "teamwork"
        archive_anti_pattern_dest = self.archive_root / "anti_pattern"

        # Never erase an earlier archive or a divergent host copy.
        for source, destination in (
            (anti_pattern_src, archive_anti_pattern_dest),
            (teamwork_src, archive_teamwork_dest),
        ):
            if source.exists() and destination.exists() and not dry_run:
                raise FileExistsError(f"archive destination already exists: {destination}")
        manifest_path = self.archive_root / "corpora_archive_manifest.json"
        if manifest_path.exists():
            json.loads(manifest_path.read_text(encoding="utf-8"))

        # 1. Scrape Anti-Patterns
        scraped_patterns = self.scrape_anti_patterns(anti_pattern_src)
        anti_pattern_payload = {
            "schema_version": ANTI_PATTERNS_REGISTRY_SCHEMA,
            "authority_effect": "None",
            "extracted_at_utc": start_time,
            "total_patterns": len(scraped_patterns),
            "patterns": [asdict(p) for p in scraped_patterns],
        }

        # 2. Scrape Teamwork
        scraped_sessions = self.scrape_all_teamwork_sessions(teamwork_src)
        antibody_stats = {} if dry_run else self.farm_antibodies_from_sessions(scraped_sessions)

        teamwork_payload = {
            "schema_version": TEAMWORK_INDEX_SCHEMA,
            "authority_effect": "None",
            "extracted_at_utc": start_time,
            "total_sessions": len(scraped_sessions),
            "total_files": sum(s.file_count for s in scraped_sessions),
            "total_bytes": sum(s.total_bytes for s in scraped_sessions),
            "sessions": [asdict(s) for s in scraped_sessions],
        }

        # 3. Devour & Archive OMC DAGs
        from .omc_dag_miner import OMCDagMiner
        omc_miner = OMCDagMiner(self.repo_root)
        omc_receipt = omc_miner.devour_and_archive(dry_run=dry_run)

        if dry_run:
            return {
                "status": "DRY_RUN",
                "anti_patterns_found": len(scraped_patterns),
                "teamwork_sessions_found": len(scraped_sessions),
                "omc_files_examined": omc_receipt["total_files_examined"],
                "omc_files_archived": omc_receipt["files_archived_count"],
                "omc_files_retained": omc_receipt["files_retained_count"],
                "antibody_stats": antibody_stats,
            }

        # 4. Persist Registries
        self.archive_root.mkdir(parents=True, exist_ok=True)
        registry_path = self.archive_root / "anti_patterns_registry.json"
        registry_path.write_text(json.dumps(anti_pattern_payload, indent=2, sort_keys=True), encoding="utf-8")

        index_path = self.archive_root / "teamwork_archive_index.json"
        index_path.write_text(json.dumps(teamwork_payload, indent=2, sort_keys=True), encoding="utf-8")

        # 5. Safe Archival Move: anti_pattern
        anti_patterns_moved = False
        if anti_pattern_src.exists():
            shutil.move(str(anti_pattern_src), str(archive_anti_pattern_dest))
            anti_patterns_moved = True

        # Purge anti_pattern copies from mirror hosts (.claude, .codex, .grok)
        mirrors_cleaned = []
        for mirror in [".claude", ".codex", ".grok"]:
            mirror_ap = self.repo_root / mirror / "anti_pattern"
            if mirror_ap.exists() and archive_anti_pattern_dest.exists() and _dir_tree_sha256(mirror_ap) == _dir_tree_sha256(archive_anti_pattern_dest):
                shutil.rmtree(mirror_ap)
                mirrors_cleaned.append(mirror)

        # 6. Safe Archival Move: teamwork
        teamwork_moved = False
        if teamwork_src.exists():
            shutil.move(str(teamwork_src), str(archive_teamwork_dest))
            teamwork_moved = True

        # 7. Record Archival Manifest (preserving existing entries)
        manifest_path = self.archive_root / "corpora_archive_manifest.json"
        manifest_payload: Dict[str, Any] = {}
        if manifest_path.is_file():
            manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))

        manifest_payload.setdefault("schema_version", CORPORA_MANIFEST_SCHEMA)
        manifest_payload.setdefault("authority_effect", "None")
        manifest_payload["archived_at_utc"] = _now()
        manifest_payload["status"] = "ACTIVE_OBSTRUCTIONS_RETAINED" if omc_receipt["files_retained_count"] else "TERMINALLY_DIGESTED"
        manifest_payload["anti_patterns"] = {
            "original_path": ".agents/anti_pattern",
            "archive_path": canonical_intelligence_route("_intelligence/archive/anti_pattern"),
            "registry_path": canonical_intelligence_route("_intelligence/archive/anti_patterns_registry.json"),
            "patterns_count": len(scraped_patterns),
            "moved": anti_patterns_moved,
            "mirrors_purged": mirrors_cleaned,
        }
        manifest_payload["teamwork"] = {
            "original_path": ".agents/teamwork",
            "archive_path": canonical_intelligence_route("_intelligence/archive/teamwork"),
            "index_path": canonical_intelligence_route("_intelligence/archive/teamwork_archive_index.json"),
            "sessions_count": len(scraped_sessions),
            "moved": teamwork_moved,
            "antibody_stats": antibody_stats,
        }
        if "omc_dags" in manifest_payload:
            # Already populated by OMCDagMiner, keep updated
            manifest_payload["omc_dags"]["files_archived_count"] = omc_receipt["files_archived_count"]
        else:
            manifest_payload["omc_dags"] = {
                "original_path": canonical_intelligence_route("_intelligence/omc_dags"),
                "archive_path": canonical_intelligence_route("_intelligence/archive/omc_dags"),
                "total_files_examined": omc_receipt["total_files_examined"],
                "files_archived_count": omc_receipt["files_archived_count"],
                "files_archived": omc_receipt["files_archived"],
                "files_retained_count": omc_receipt["files_retained_count"],
                "files_retained_with_active_obstructions": omc_receipt["files_retained_with_active_obstructions"],
                "antibody_stats": omc_receipt["antibody_farming"],
                "archived_at_utc": _now(),
            }
        manifest_path.write_text(json.dumps(manifest_payload, indent=2, sort_keys=True), encoding="utf-8")

        return manifest_payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Engine Corpora Scraper & Archival Tool")
    parser.add_argument("--repo-root", type=Path, default=None, help="Root of repository")
    parser.add_argument("--dry-run", action="store_true", help="Scrape without moving or writing archives")
    args = parser.parse_args()

    scraper = CorporaScraper(args.repo_root)
    result = scraper.execute_mining_and_archival(dry_run=args.dry_run)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

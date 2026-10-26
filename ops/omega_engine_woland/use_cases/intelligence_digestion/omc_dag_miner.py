"""Operad Morphism Calculus (OMC) DAG Mining, Digestion, and Archival Pipeline.

Devours existing OMC audit, preflight, and DAG verification files under _ic/nga/omc_dags/,
mines active failure modes and blocker patterns into candidate antibodies in OEEIS,
safely archives files from which all obstructions are cleared (||Obstruction|| = 0)
into _ic/nara/_archive/omc_dags/, and records results in corpora_archive_manifest.json.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from omega_engine_epistemic_immune_system.domain.pharmacy_seeder import PharmacySeeder
from omega_engine_epistemic_immune_system.infrastructure.pharmacy_writer import (
    filesystem_byte_writer,
    filesystem_catalog_bytes,
)
from omega_engine_governance.domain.intelligence_community import canonical_intelligence_route
from omega_engine_woland.domain.intelligence_digestion.omc_dag_models import (
    OMCRecord,
    parse_omc_line,
    parse_omc_markdown,
)

OMC_ARCHIVE_RECEIPT_SCHEMA = "omega.intelligence.omc-archive-receipt.v1"
CORPORA_MANIFEST_SCHEMA = "omega.intelligence.corpora-archive-manifest.v1"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class OMCDagMiner:
    """Application service for devouring OMC files and archiving cleared records."""

    def __init__(self, repo_root: Optional[Path] = None) -> None:
        if repo_root is not None:
            self.repo_root = Path(repo_root).resolve()
        else:
            self.repo_root = self._find_repo_root()
        self.omc_root = self.repo_root / canonical_intelligence_route("_intelligence/omc_dags")
        self.archive_root = self.repo_root / canonical_intelligence_route("_intelligence/archive")
        self.archive_omc_dest = self.archive_root / "omc_dags"
        self.manifest_path = self.archive_root / "corpora_archive_manifest.json"
        self.seeder = PharmacySeeder(
            self.repo_root,
            byte_writer=filesystem_byte_writer,
            byte_source=filesystem_catalog_bytes,
        )

    @staticmethod
    def _find_repo_root() -> Path:
        candidate = Path(__file__).resolve()
        for parent in candidate.parents:
            if (parent / ".agents").is_dir() or (parent / "_ic").is_dir():
                return parent
        return Path.cwd().resolve()

    def discover_omc_files(self, omc_dir: Optional[Path] = None) -> List[Path]:
        """Discovers direct audit and review files under omc_dags, excluding data_types."""
        target_dir = omc_dir or self.omc_root
        if not target_dir.is_dir():
            return []
        found: List[Path] = []
        for item in sorted(target_dir.iterdir(), key=lambda p: p.name):
            if not item.is_file():
                continue
            if item.name.startswith(".") or item.name.endswith(".tmp"):
                continue
            if item.suffix.lower() in (".jsonl", ".md"):
                found.append(item)
        return found

    def parse_file_records(self, file_path: Path) -> List[OMCRecord]:
        """Parses an OMC file into typed domain records."""
        records: List[OMCRecord] = []
        if file_path.is_symlink():
            raise ValueError("symlink audit inputs are refused")
        if file_path.suffix.lower() == ".jsonl":
            content = file_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                clean = line.strip()
                if not clean:
                    continue
                records.append(parse_omc_line(clean))
        elif file_path.suffix.lower() == ".md":
            content = file_path.read_text(encoding="utf-8")
            records.append(parse_omc_markdown(content, filename_stem=file_path.stem))
        return records

    def farm_obstructions(self, obstructions_by_file: Dict[str, List[str]]) -> Dict[str, Any]:
        """Farms defect obstructions into candidate antibodies in OEEIS."""
        all_farmed = []
        all_refused = []
        all_preserved = []

        for stem, obstructions in obstructions_by_file.items():
            if not obstructions:
                continue
            farmed = self.seeder.farm_antibodies_from_defects(
                obstructions,
                run_id=f"omc_{stem}",
                task_id="omc_dag_digestion",
            )
            all_farmed.extend([a.antibody_id for a in farmed])
            all_refused.extend(self.seeder.refused_retired)
            all_preserved.extend(self.seeder.preserved_judged)

        return {
            "antibodies_farmed_count": len(all_farmed),
            "antibodies_farmed": sorted(list(set(all_farmed))),
            "refused_retired": sorted(list(set(all_refused))),
            "preserved_judged": sorted(list(set(all_preserved))),
        }

    def devour_and_archive(self, dry_run: bool = False) -> Dict[str, Any]:
        """Devours OMC files: farms active obstructions, moves cleared files to archive."""
        files = self.discover_omc_files()
        files_archived: List[Path] = []
        files_retained: List[Tuple[Path, List[str]]] = []
        obstructions_by_file: Dict[str, List[str]] = {}

        for file_path in files:
            try:
                records = self.parse_file_records(file_path)
            except (ValueError, OSError) as error:
                files_retained.append((file_path, [f"UNREADABLE_AUDIT: {error}"]))
                continue
            if not records:
                files_retained.append((file_path, ["EMPTY_AUDIT"]))
                continue

            file_obstructions: List[str] = []
            has_active_blockers = False
            for rec in records:
                if rec.has_obstructions():
                    has_active_blockers = True
                    file_obstructions.extend(rec.get_obstructions())

            if has_active_blockers:
                files_retained.append((file_path, file_obstructions))
                obstructions_by_file[file_path.stem] = file_obstructions
            else:
                files_archived.append(file_path)

        antibody_stats: Dict[str, Any] = {}
        if obstructions_by_file and not dry_run:
            antibody_stats = self.farm_obstructions(obstructions_by_file)

        moved_names: List[str] = []
        if not dry_run:
            # Refuse the entire batch before any copy or source removal.
            if any((self.archive_omc_dest / path.name).exists() for path in files_archived):
                raise FileExistsError("archive destination already exists")
            if self.manifest_path.exists():
                json.loads(self.manifest_path.read_text(encoding="utf-8"))
            self.archive_omc_dest.mkdir(parents=True, exist_ok=True)
            for src_path in files_archived:
                dest_file = self.archive_omc_dest / src_path.name
                with dest_file.open("xb") as destination, src_path.open("rb") as source:
                    shutil.copyfileobj(source, destination)
                if hashlib.sha256(dest_file.read_bytes()).digest() != hashlib.sha256(src_path.read_bytes()).digest():
                    raise OSError("archived audit bytes differ from source")
                moved_names.append(src_path.name)

            self._update_corpora_manifest(
                total_examined=len(files),
                files_archived=moved_names,
                files_retained=[
                    {"filename": p.name, "obstructions": obs}
                    for p, obs in files_retained
                ],
                antibody_stats=antibody_stats,
            )
            for src_path in files_archived:
                src_path.unlink()
        else:
            moved_names = [p.name for p in files_archived]

        receipt = {
            "schema_version": OMC_ARCHIVE_RECEIPT_SCHEMA,
            "authority_effect": "None",
            "timestamp_utc": _now(),
            "dry_run": dry_run,
            "total_files_examined": len(files),
            "files_archived_count": len(moved_names),
            "files_archived": moved_names,
            "files_retained_count": len(files_retained),
            "files_retained_with_active_obstructions": [p.name for p, _ in files_retained],
            "antibody_farming": antibody_stats,
            "status": "PASS",
        }
        return receipt

    def _update_corpora_manifest(
        self,
        total_examined: int,
        files_archived: List[str],
        files_retained: List[Dict[str, Any]],
        antibody_stats: Dict[str, Any],
    ) -> None:
        """Persists or updates omc_dags entry in corpora_archive_manifest.json."""
        manifest: Dict[str, Any] = {}
        if self.manifest_path.is_file():
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))

        manifest.setdefault("schema_version", CORPORA_MANIFEST_SCHEMA)
        manifest.setdefault("authority_effect", "None")
        manifest["status"] = "ACTIVE_OBSTRUCTIONS_RETAINED" if files_retained else "TERMINALLY_DIGESTED"
        manifest["updated_at_utc"] = _now()

        previous = manifest.get("omc_dags", {})
        archived_names = sorted(set(previous.get("files_archived", [])) | set(files_archived))
        archived_hashes = dict(previous.get("file_sha256", {}))
        archived_hashes.update({
            name: hashlib.sha256((self.archive_omc_dest / name).read_bytes()).hexdigest()
            for name in files_archived
        })
        manifest["omc_dags"] = {
            "original_path": self.omc_root.relative_to(self.repo_root).as_posix(),
            "archive_path": self.archive_omc_dest.relative_to(self.repo_root).as_posix(),
            "total_files_examined": total_examined,
            "files_archived_count": len(archived_names),
            "files_archived": archived_names,
            "file_sha256": archived_hashes,
            "files_retained_count": len(files_retained),
            "files_retained_with_active_obstructions": files_retained,
            "antibody_stats": antibody_stats,
            "archived_at_utc": _now(),
        }

        self.archive_root.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=self.archive_root, delete=False) as temporary:
            temporary.write(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
            temporary_path = Path(temporary.name)
        try:
            os.replace(temporary_path, self.manifest_path)
        finally:
            temporary_path.unlink(missing_ok=True)


def devour_and_archive_omc_dags(
    repo_root: Optional[Path] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Public helper function to devour and archive OMC DAGs."""
    miner = OMCDagMiner(repo_root)
    return miner.devour_and_archive(dry_run=dry_run)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Omega Engine OMC DAG Mining & Archival Tool")
    parser.add_argument("--repo-root", type=Path, default=None, help="Root of repository")
    parser.add_argument("--dry-run", action="store_true", help="Evaluate without moving files or updating manifest")
    parser.add_argument("--json", action="store_true", help="Output receipt as formatted JSON")
    args = parser.parse_args(argv)

    receipt = devour_and_archive_omc_dags(repo_root=args.repo_root, dry_run=args.dry_run)
    if args.json:
        print(json.dumps(receipt, indent=2))
    else:
        print("OMC DAG Digestion Complete.")
        print(f"  Total Examined: {receipt['total_files_examined']}")
        print(f"  Archived:       {receipt['files_archived_count']}")
        print(f"  Retained:       {receipt['files_retained_count']}")
        for f in receipt.get("files_retained_with_active_obstructions", []):
            print(f"    ! [RETAINED WITH OBSTRUCTION] {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

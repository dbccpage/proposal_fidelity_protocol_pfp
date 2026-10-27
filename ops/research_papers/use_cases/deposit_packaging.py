"""Zenodo Deposit Packaging Service.

Creates hermetic deposit packages with deterministic SHA256SUMS manifests.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..domain.models.paper_spec import PaperSpecification
from ..domain.ports.render_export_port import RenderExportPort


@dataclass(frozen=True)
class DepositPackageReceipt:
    """Receipt for a generated deposit envelope."""

    paper_id: str
    target_zip: str
    zip_sha256: str
    manifest_file_count: int
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("AuthorityEffect must be 'None'")


class DepositPackagingService:
    """Service for compiling and verifying deposit bundles."""

    def __init__(self, export_port: RenderExportPort) -> None:
        self.export_port = export_port

    def package(
        self,
        paper: PaperSpecification,
        source_dir: str,
        output_zip_path: str,
    ) -> DepositPackageReceipt:
        s_path = Path(source_dir)
        manifest = self.export_port.generate_sha256sums(str(s_path))

        # Write SHA256SUMS into directory
        sha_file = s_path / "SHA256SUMS"
        lines = [f"{digest}  {path}" for path, digest in sorted(manifest.items())]
        sha_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        # Write Zenodo metadata if missing
        zenodo_meta = s_path / "zenodo_metadata.json"
        if not zenodo_meta.exists():
            meta = {
                "title": paper.title,
                "upload_type": "publication",
                "publication_type": "preprint",
                "description": paper.abstract,
                "creators": [{"name": a} for a in paper.authors],
                "access_right": "open",
                "license": paper.monograph.license if paper.monograph else "CC-BY-4.0",
                "keywords": list(paper.monograph.keywords) if paper.monograph else ["CODA", "DDC"],
            }
            zenodo_meta.write_text(json.dumps(meta, indent=2), encoding="utf-8")

        zip_hash = self.export_port.create_deposit_zip(source_dir, output_zip_path)

        return DepositPackageReceipt(
            paper_id=paper.paper_id,
            target_zip=output_zip_path,
            zip_sha256=zip_hash,
            manifest_file_count=len(manifest),
            authority_effect="None",
        )

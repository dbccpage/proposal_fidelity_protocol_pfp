"""Protocol for Monograph Rendering, PDF Export, and Deposit Packaging."""

from __future__ import annotations

from typing import Dict, Protocol

from ..models.paper_spec import MonographEnvelope


class RenderExportPort(Protocol):
    """Protocol for rendering markdown/latex and packaging Zenodo deposit bundles."""

    def render_markdown(self, monograph: MonographEnvelope) -> str:
        """Renders monograph envelope to canonical markdown format."""
        ...

    def compile_pdf(self, markdown_content: str, output_path: str) -> bool:
        """Compiles markdown into PDF using Pandoc / XeLaTeX."""
        ...

    def create_deposit_zip(self, source_dir: str, target_zip_path: str) -> str:
        """Packages source directory into hermetic zip file and returns SHA-256 digest."""
        ...

    def generate_sha256sums(self, target_dir: str) -> Dict[str, str]:
        """Calculates deterministic SHA256SUMS for all files in directory."""
        ...

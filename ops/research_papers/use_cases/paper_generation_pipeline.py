"""End-to-End Research Paper Generation Pipeline.

Synthesizes research monographs and deposit packages from mathematical spines
and verified claim ledgers, conforming to _kits/paper_template.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from ..domain.models.claim_ledger import ClaimLedger
from ..domain.models.paper_spec import (
    EADCAddress,
    MonographEnvelope,
    PaperSpecification,
    Section,
)
from ..domain.ports.render_export_port import RenderExportPort


@dataclass(frozen=True)
class PaperGenerationResult:
    """Result of end-to-end paper synthesis."""

    paper: PaperSpecification
    claim_ledger: ClaimLedger
    rendered_markdown: str
    target_directory: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("AuthorityEffect must be 'None'")


class PaperGenerationPipeline:
    """Pipeline for scaffolding and synthesizing research monographs."""

    def __init__(self, export_port: RenderExportPort) -> None:
        self.export_port = export_port

    def scaffold_paper(
        self,
        paper_id: str,
        title: str,
        eadc_raw: str,
        authors: Tuple[str, ...],
        abstract: str,
        output_dir: str,
    ) -> PaperGenerationResult:
        eadc = EADCAddress.parse(eadc_raw)

        # Standard 6-section monograph structure per atlas consolidation rules
        sec1 = Section(id="sec_intro", title="Introduction & Problem Formulation", level=2, content="Context and primary difference distinction.")
        sec2 = Section(id="sec_spine", title="Mathematical Spine & Discrete Calculus", level=2, content="DDC and CODA mathematical foundation.")
        sec3 = Section(id="sec_solvers", title="Computational Witness & Exact Solvers", level=2, content="Sovereign Rust solvers and Bareiss elimination.")
        sec4 = Section(id="sec_proofs", title="Formalization & Lean 4 Proof Kernels", level=2, content="Lake modules with standard axioms {propext, Quot.sound}.")
        sec5 = Section(id="sec_redteam", title="Adversarial Audit & Epistemic Boundaries", level=2, content="Thanatos red team findings, claim hygiene, and AuthorityEffect: None.")
        sec6 = Section(id="sec_conclusion", title="Conclusion & Future Research Obligations", level=2, content="Summary of narrowest defensible claims.")

        envelope = MonographEnvelope(
            title=title,
            abstract=abstract,
            sections=(sec1, sec2, sec3, sec4, sec5, sec6),
            keywords=("CODA", "DDC", "Discrete Calculus", "Exact Solvers"),
            version="1.0.0",
            license="CC-BY-4.0",
            authority_effect="None",
        )

        spec = PaperSpecification(
            paper_id=paper_id,
            title=title,
            eadc_address=eadc,
            authors=authors,
            abstract=abstract,
            monograph=envelope,
            target_venue="Zenodo",
            status="DRAFT",
        )

        ledger = ClaimLedger(paper_id=paper_id, claims=())
        rendered = self.export_port.render_markdown(envelope)

        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        (out_path / "monograph.md").write_text(rendered, encoding="utf-8")
        (out_path / "README.md").write_text(f"# {title}\n\nEADC: {eadc.as_str()}\n", encoding="utf-8")

        return PaperGenerationResult(
            paper=spec,
            claim_ledger=ledger,
            rendered_markdown=rendered,
            target_directory=str(out_path),
            authority_effect="None",
        )

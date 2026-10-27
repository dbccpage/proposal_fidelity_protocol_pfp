"""The 10-Colour Operad Types.

Colours representing data and artifact categories in multi-agent operadic morphisms.
"""

from __future__ import annotations

from enum import Enum


class OperadColour(str, Enum):
    """The 10 canonical colours in the Operad Category."""

    CODE = "Code"          # Source code files (Python, Rust, Lean 4)
    PAPER = "Paper"        # Research paper monographs, LaTeX/Markdown
    PROOF = "Proof"        # Formal proofs, Lake modules, proof terms
    RECEIPT = "Receipt"    # Cryptographic receipts, execution evidence, hashes
    AUDIT = "Audit"        # Audit findings, defect reports, checklists
    CONTRACT = "Contract"  # Nomos contracts, schemas, YAML rules
    DIAGRAM = "Diagram"    # Mermaid diagrams, SVG visual figures
    POST = "Post"          # Public math communication, pedagogical posts
    STATE = "State"        # Worktree git state, directory layouts
    LEDGER = "Ledger"      # Append-only hash chains, claim ledgers

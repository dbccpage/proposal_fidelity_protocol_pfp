"""Synthetic self panel for PFP Paper 003.

The repository's self panel at the paper's baseline is loaded from a sealed JSON
file and has 1,000 rows with 40 distinct base contents, ten in each of four
categories. This module does not load that file. It builds a synthetic stand-in
with the same shape so that the package can illustrate the point made in paper
Section 3: counting rows overstates the number of distinct examples.

- clean_lean4_proof: 10 base strings x 25 tagged copies = 250 rows
- clean_architecture_port: 10 x 25 = 250 rows
- clean_prompt_template: 10 x 25 = 250 rows
- clean_physics_expression: 10 x 25 = 250 rows
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator


@dataclass(frozen=True)
class PanelEntry:
    entry_id: str
    category: str
    content: str


class SelfPanel:
    def __init__(self, entries: list[PanelEntry]) -> None:
        self._entries = entries

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self) -> Iterator[PanelEntry]:
        return iter(self._entries)

    def __getitem__(self, index: int) -> PanelEntry:
        return self._entries[index]

    @staticmethod
    def base_content(content: str) -> str:
        """Strip the synthetic copy tag (for example ``[var_07]``) to recover the base string."""
        return re.sub(r"\s*\[var_\d+\]\s*$", "", content).strip()

    def distinct_base_contents(self) -> set[str]:
        return {self.base_content(entry.content) for entry in self._entries}

    @classmethod
    def build_synthetic(cls) -> SelfPanel:
        categories = {
            "clean_lean4_proof": [
                f"theorem exact_retraction_{i} : BoundedCochain -> True := by intro; trivial"
                for i in range(10)
            ],
            "clean_architecture_port": [
                f"class DomainPort_{i}(Protocol):\n    def execute(self, payload: dict) -> Result: ..."
                for i in range(10)
            ],
            "clean_prompt_template": [
                f"Role: Exact Rational Auditor {i}. Verify all arithmetic invariants without speculative leaps."
                for i in range(10)
            ],
            "clean_physics_expression": [
                f"Hamiltonian_term_{i} = -J * sum(S_i * S_j) + U * n_up * n_down"
                for i in range(10)
            ],
        }

        entries: list[PanelEntry] = []
        uid = 0
        for category, base_list in categories.items():
            for base in base_list:
                for rep in range(25):
                    entries.append(
                        PanelEntry(
                            entry_id=f"panel_{uid:04d}",
                            category=category,
                            content=f"{base} [var_{rep:02d}]",
                        )
                    )
                    uid += 1

        return cls(entries)

"""Markdown proposed skills register adapter.

Manages recording newly mined skill proposals into:
  omega_engine_operads/skills/ooutwire/proposed_skills_register.md

AuthorityEffect: None.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Sequence

from omega_engine_operads.domain.autopoiesis.entities import MinedSkillProposal
from omega_engine_operads.domain.autopoiesis.ports import SkillsRegisterPort

_ENTRY_RE = re.compile(r"### Entry (\d+):\s*`([^`]+)`")


class MarkdownSkillsAdapter(SkillsRegisterPort):
    """File adapter for reading and appending to proposed_skills_register.md."""

    def __init__(self, register_path: Path | str) -> None:
        self.register_path = Path(register_path).resolve()

    def load_proposed_skills(self) -> Sequence[str]:
        """Loads all existing skill IDs from the register."""
        if not self.register_path.is_file():
            return []
        text = self.register_path.read_text(encoding="utf-8")
        matches = _ENTRY_RE.findall(text)
        return [m[1] for m in matches]

    def _get_next_entry_number(self, text: str) -> int:
        matches = _ENTRY_RE.findall(text)
        if not matches:
            return 1
        nums = [int(m[0]) for m in matches]
        return max(nums) + 1

    def append_skill_proposals(self, proposals: Sequence[MinedSkillProposal]) -> int:
        """Appends new unique skill proposals to the register."""
        if not self.register_path.is_file():
            return 0

        text = self.register_path.read_text(encoding="utf-8")
        existing_skills = set(self.load_proposed_skills())
        next_num = self._get_next_entry_number(text)

        new_entries = []
        for prop in proposals:
            if prop.skill_id in existing_skills:
                continue
            entry_str = (
                f"\n### Entry {next_num:04d}: `{prop.skill_id}`\n"
                f"- **Title:** {prop.title}\n"
                f"- **Lead Council:** `{prop.lead_council}`\n"
                f"- **Status:** `PENDING_REVIEW`\n"
                f"- **Confidence:** `{prop.confidence}`\n"
                f"- **Origin Role:** `{prop.origin_agent_role}`\n"
                f"- **Scope:** {prop.scope}\n"
                f"- **AuthorityEffect:** {prop.authority_effect}\n"
            )
            new_entries.append(entry_str)
            existing_skills.add(prop.skill_id)
            next_num += 1

        if not new_entries:
            return 0

        # Append before closing summary if present, or at the end
        updated_text = text.rstrip() + "\n" + "".join(new_entries) + "\n"
        self.register_path.write_text(updated_text, encoding="utf-8")
        return len(new_entries)

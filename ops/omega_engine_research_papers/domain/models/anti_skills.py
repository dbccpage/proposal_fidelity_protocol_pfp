"""Active Research Paper Anti-Skills Register.

AuthorityEffect: None.

Canonical implementation relocated to:
``omega_engine_operads.domain.anti_skills.research_papers``

Codifies the active anti-skills enforced during automated research paper review
and Stage Ω republication gate inspection across research paper packages.
"""

from __future__ import annotations

from omega_engine_operads.domain.anti_skills.research_papers import (
    ACTIVE_ANTI_SKILLS,
    AntiSkillDefinition,
    get_anti_skill_by_id,
    get_anti_skill_by_number,
    total_anti_skills_count,
)

__all__ = [
    "ACTIVE_ANTI_SKILLS",
    "AntiSkillDefinition",
    "get_anti_skill_by_id",
    "get_anti_skill_by_number",
    "total_anti_skills_count",
]

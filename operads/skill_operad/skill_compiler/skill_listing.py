"""Skill listing gate: keep the model's skill listing small and the catalog in step with it.

Claude Code lists every skill the model may invoke, name and description, inside a fixed byte
budget. Past the budget, skills are listed by name only and the model cannot tell when to use
them. This gate holds three things:

1. every model-invocable skill has a one-line description of at most ``DESCRIPTION_CAP_BYTES``;
2. the summed listing (name plus description, per model-invocable skill) stays within
   ``LISTING_BUDGET_BYTES``, a ratchet set from the tree when this gate was added;
3. the tracked capability catalog and operad signature match a fresh compile of the skills
   (``capability_catalog_compiler --check``), so a description edit cannot leave them stale.

A skill whose frontmatter sets ``disable-model-invocation: true`` is not listed to the model and
is exempt from 1 and 2. Run::

    python -m operads.skill_operad.skill_compiler.skill_listing \
        --repo-root .

Exit 0 when all three hold, 1 otherwise.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

from operads.domain.capability_catalog_v1 import (
    CapabilityCatalogRefusal,
)
from operads.infrastructure.capability_catalog_compiler import (
    CatalogCompileRefusal,
    compile_capability_catalog,
    verify_host_projections,
)

SKILLS_DIR = Path("operads/skills")
DESCRIPTION_CAP_BYTES = 120
#: Ratchet: the listing measured 30,507 B over 232 skills when this gate was added, plus about
#: 5 % headroom for new skills. Lower it when the listing shrinks; raising it needs a reason in
#: the PR. In a 1M-token session this size listed every repo skill with its description.
LISTING_BUDGET_BYTES = 32_000


@dataclass(frozen=True)
class ListedSkill:
    name: str
    description: str
    model_invocable: bool

    @property
    def listing_bytes(self) -> int:
        return len(self.name.encode("utf-8")) + len(self.description.encode("utf-8"))


def _frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    loaded = yaml.safe_load(text[4:end]) if end > 0 else None
    return loaded if isinstance(loaded, dict) else {}


def listed_skills(repo_root: Path) -> list[ListedSkill]:
    skills = []
    for path in sorted((repo_root / SKILLS_DIR).glob("*/SKILL.md")):
        meta = _frontmatter(path)
        skills.append(
            ListedSkill(
                name=str(meta.get("name", path.parent.name)),
                description=str(meta.get("description", "")),
                model_invocable=meta.get("disable-model-invocation") is not True,
            )
        )
    return skills


def listing_problems(skills: list[ListedSkill], budget: int = LISTING_BUDGET_BYTES) -> list[str]:
    problems = []
    listed = [s for s in skills if s.model_invocable]
    for skill in listed:
        size = len(skill.description.encode("utf-8"))
        if not skill.description.strip():
            problems.append(f"{skill.name}: empty description")
        elif "\n" in skill.description:
            problems.append(f"{skill.name}: description spans more than one line")
        elif size > DESCRIPTION_CAP_BYTES:
            problems.append(f"{skill.name}: description is {size} B, cap {DESCRIPTION_CAP_BYTES} B")
    total = sum(s.listing_bytes for s in listed)
    if total > budget:
        problems.append(f"listing is {total} B over {len(listed)} skills, budget {budget} B")
    return problems


def catalog_problems(repo_root: Path) -> list[str]:
    try:
        verify_host_projections(repo_root, compile_capability_catalog(repo_root))
    except (CatalogCompileRefusal, CapabilityCatalogRefusal) as error:
        return [f"{error} (rebuild: python -m operads."
                "infrastructure.capability_catalog_compiler --repo-root . --write)"]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    root = parser.parse_args(argv).repo_root.resolve()
    skills = listed_skills(root)
    problems = listing_problems(skills) + catalog_problems(root)
    listed = [s for s in skills if s.model_invocable]
    print(
        f"skill_listing: {len(listed)} of {len(skills)} skills listed to the model, "
        f"{sum(s.listing_bytes for s in listed)} B of {LISTING_BUDGET_BYTES} B budget"
    )
    for problem in problems:
        print(f"  {problem}")
    print("skill_listing: " + ("FAIL" if problems else "PASS"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())

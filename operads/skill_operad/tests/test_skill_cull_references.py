from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILLS_ROOT = REPO_ROOT / ".agents" / "skills"
OPERAD_ROOT = Path(__file__).resolve().parents[1]
ROUTES = (
    OPERAD_ROOT / "yaml" / "routes.yaml"
    if (OPERAD_ROOT / "yaml" / "routes.yaml").is_file()
    else OPERAD_ROOT / "skill_compiler" / "routes.yaml"
)
FAMILY_REGISTRY = SKILLS_ROOT / "_shared" / "family_registry.md"
OPERAD_SIGNATURE = (
    OPERAD_ROOT / "json" / "operad_signature.json"
    if (OPERAD_ROOT / "json" / "operad_signature.json").is_file()
    else OPERAD_ROOT / "operad_signature.json"
)

RETIRED_SKILLS = (
    "coda-centralized-functional-triad-bridge",
    "coda-degree-k-dual-certified-solver",
    "coda-gauge-higgs-susy-solver-bridge",
    "goo-cptp-measure-and-prepare-rigidity-verifier",
    "goo-cptp-wigner-yanase-monotonicity-verifier",
    "goo-dda-tape-dfa-grammar-validator",
    "goo-higher-simplex-cochain-assembly",
    "goo-atomic-trace-ledger-concurrency-guard",
    "goo-canon-mirror-atomicity-hook",
    "goo-lean4-strict-mechanization-guard",
    "goo-no-shim-dual-home-collapse",
    "goo-po000-package-root-resolution",
    "goo-prompts-university-library-custody",
    "goo-python-replay-admission-boundary-adversary",
    "goo-repo-escaping-path-resolver-ban",
    "goo-research-lean4-canonical-locus-guard",
    "goo-residual-projection-obstruction-solver-suite",
    "goo-scoped-test-harness-synchronizer",
    "goo-simplex-normal-forms-contracts-consolidation",
    "goo-adversary-predictive-framing-bout-evaluator",
    "goo-yaml-contract-dual-home-sync",
    "goo-paper-build-unicode-hygiene",
    "goo-paper-latex-math-typesetting-standardizer",
    "goo-paper-packaging-topology-merger",
    "l1-regge-barbero-immirzi",
    "lib-archive-miner",
    "lib-coda-librarian",
    "lib-encyclopedia-librarian",
    "lib-lean4-librarian",
    "lib-repo-librarian",
    "abstract-algebra-expansion",
    "holonomy-package",
    "linear-algebra-carrier-consolidation",
    "panepistimion-cs-ml-prof-symbol-games",
    "panepistimion-cs-prof-ml-ai-info",
    "panepistimion-math-prof",
    "panepistimion-math-prof-projection-obstruction",
    "panepistimion-physics-prof-quantum-foundations",
    "panepistimion-physics-prof-relativity-relational-constructors",
)


class SkillCullReferenceTests(unittest.TestCase):
    def test_generated_family_registry_only_names_present_skills(self) -> None:
        registry = FAMILY_REGISTRY.read_text(encoding="utf-8")
        names = re.findall(r"^- `([^`]+)`$", registry, flags=re.MULTILINE)
        missing = [
            name for name in names if not (SKILLS_ROOT / name / "SKILL.md").is_file()
        ]
        assert missing == []

    def test_operad_route_targets_exist(self) -> None:
        routes = ROUTES.read_text(encoding="utf-8")
        targets = re.findall(r'^\s+target: "([^"]+)"$', routes, flags=re.MULTILINE)
        missing = [target for target in targets if not (REPO_ROOT / target).is_file()]
        assert missing == []

    def test_retired_skills_are_absent_from_active_routing_surfaces(self) -> None:
        surfaces = [FAMILY_REGISTRY, ROUTES, OPERAD_SIGNATURE]
        surfaces.extend(
            sorted(
                p
                for p in (SKILLS_ROOT / "_shared").glob("*.md")
                if not p.name.endswith("manifest.md")
            )
        )
        surfaces.extend(sorted((SKILLS_ROOT / "_shared").glob("*.sh")))

        findings: list[str] = []
        for surface in surfaces:
            text = surface.read_text(encoding="utf-8")
            for retired in RETIRED_SKILLS:
                if retired in text:
                    findings.append(f"{surface.relative_to(REPO_ROOT)}: {retired}")

        for skill_md in sorted(SKILLS_ROOT.glob("*/SKILL.md")):
            text = skill_md.read_text(encoding="utf-8")
            frontmatter_match = re.search(r"^---\n(.*?)\n---", text, re.DOTALL)
            frontmatter = frontmatter_match.group(1) if frontmatter_match else ""
            for retired in RETIRED_SKILLS:
                if retired in frontmatter:
                    findings.append(f"{skill_md.relative_to(REPO_ROOT)}: {retired}")

        assert findings == []

    def test_operad_signature_exactly_matches_on_disk_skills(self) -> None:
        payload = json.loads(OPERAD_SIGNATURE.read_text(encoding="utf-8"))
        operation_ids = [operation["skill_id"] for operation in payload["operations"]]
        disk_skill_ids = sorted(
            path.parent.name for path in SKILLS_ROOT.glob("*/SKILL.md")
        )

        assert len(operation_ids) == len(set(operation_ids))
        assert sorted(operation_ids) == disk_skill_ids
        assert all(operation.get("description") for operation in payload["operations"])
        ooutwire = next(
            operation
            for operation in payload["operations"]
            if operation["skill_id"] == "ooutwire"
        )
        assert ooutwire["source_colours"] == []
        assert ooutwire["arity"] == 0

    def test_consolidated_math_skill_keeps_encyclopedia_toolchain(self) -> None:
        consolidated = SKILLS_ROOT / "panep-math-and-physics-prof"
        required = (
            consolidated / "regen_encyclopedia.py",
            consolidated / "regen_spine_index.py",
            consolidated / "conform_legacy_entries.py",
            consolidated / "tests" / "test_regen_encyclopedia.py",
            consolidated / "tests" / "test_regen_spine_index.py",
        )
        missing = [
            str(path.relative_to(REPO_ROOT)) for path in required if not path.is_file()
        ]
        assert missing == []


if __name__ == "__main__":
    unittest.main()

"""Automated verification suite for Genesis modular level documentation.

AuthorityEffect: None.
Verifies that:
1. Every individual level_XX_*.md file in 2_genesis/levels/ maintains cross-references to genesis.md.
2. Every sealed core level (Levels 00 to 21) embeds an existing SVG schematic from _images/.
3. genesis.md maintains bidirectional links to each modular level file in levels/.
4. levels/README.md catalogs all level files.
5. 6_genesis_ongoing/_images/ contains all 22 SVGs referenced in genesis_ongoing.md.
6. All files are pure UTF-8 without BOM and free of Mojibake artifacts.
"""

from __future__ import annotations

import os
import re
from pathlib import Path


def _find_repo_root(p: Path = Path(__file__).resolve()) -> Path:
    for parent in p.parents:
        if (parent / ".git").exists() or (parent / "pixi.toml").exists():
            return parent
    return p.parents[4]


REPO_ROOT = _find_repo_root()
_GEN_CANDIDATES = [
    REPO_ROOT / "education" / "documentation" / "001_oegen",
    REPO_ROOT / "education" / "documentation" / "2_genesis",
]
GENESIS_DIR = next((d for d in _GEN_CANDIDATES if d.is_dir()), _GEN_CANDIDATES[0])
GENESIS_LEVELS_DIR = GENESIS_DIR / "levels"
GENESIS_IMAGES_DIR = GENESIS_DIR / "_images"
GENESIS_MONOGRAPH = GENESIS_DIR / "genesis.md"
GENESIS_README = GENESIS_DIR / "README.md"
GENESIS_LEVELS_README = GENESIS_LEVELS_DIR / "README.md"

_ONGOING_CANDIDATES = [
    REPO_ROOT / "education" / "documentation" / "005_oegenong",
    REPO_ROOT / "education" / "documentation" / "060_genesis_ongoing",
    REPO_ROOT / "education" / "documentation" / "6_genesis_ongoing",
]
GENESIS_ONGOING_DIR = next((d for d in _ONGOING_CANDIDATES if d.is_dir()), _ONGOING_CANDIDATES[0])
GENESIS_ONGOING_IMAGES_DIR = GENESIS_ONGOING_DIR / "_images"
GENESIS_ONGOING_MONOGRAPH = GENESIS_ONGOING_DIR / "genesis_ongoing.md"
GENESIS_ONGOING_README = GENESIS_ONGOING_DIR / "README.md"


def test_genesis_levels_exist_and_count():
    """Verify that the levels directory exists and contains all expected level files."""
    assert GENESIS_LEVELS_DIR.exists(), f"Missing directory: {GENESIS_LEVELS_DIR}"
    assert GENESIS_LEVELS_README.exists(), f"Missing master index: {GENESIS_LEVELS_README}"

    level_files = sorted(GENESIS_LEVELS_DIR.glob("level_*.md"))
    assert len(level_files) >= 33, f"Expected at least 33 level files, found {len(level_files)}"

    # Ensure levels 00 through 21 (sealed core) are all present
    core_levels = {
        int(f.name.split("_")[1]) for f in level_files if int(f.name.split("_")[1]) <= 21
    }
    expected_core = set(range(22))
    assert core_levels == expected_core, (
        f"Missing sealed core levels: {expected_core - core_levels}"
    )


def test_genesis_levels_reference_canonical_monograph():
    """Verify that every level_XX_*.md file maintains an explicit cross-reference to genesis.md."""
    level_files = sorted(GENESIS_LEVELS_DIR.glob("level_*.md"))
    missing_refs = []

    for f in level_files:
        content = f.read_text(encoding="utf-8")
        if "genesis.md" not in content:
            missing_refs.append(f.name)

    assert not missing_refs, f"Level files missing reference to genesis.md: {missing_refs}"


def test_genesis_levels_sealed_core_image_embedding():
    """Verify that every sealed core level (Levels 00-21) embeds an existing SVG from _images/."""
    level_files = sorted(GENESIS_LEVELS_DIR.glob("level_*.md"))
    missing_embeds = []
    broken_embeds = []

    for f in level_files:
        lvl_num = int(f.name.split("_")[1])
        if lvl_num > 21:
            continue

        content = f.read_text(encoding="utf-8")
        imgs = re.findall(r"!\[.*?\]\((.*?)\)", content)

        if not imgs:
            missing_embeds.append(f.name)
            continue

        for img_path in imgs:
            # Resolve URI or relative path
            if img_path.startswith("file:///"):
                target_path = Path(
                    img_path[8:].replace("/", "\\") if os.name == "nt" else img_path[7:]
                )
            elif os.path.isabs(img_path):
                target_path = Path(img_path)
            else:
                target_path = (f.parent / img_path).resolve()

            if not target_path.exists():
                broken_embeds.append((f.name, img_path, str(target_path)))

    assert not missing_embeds, f"Sealed core levels missing image embeds: {missing_embeds}"
    assert not broken_embeds, f"Sealed core levels with broken image paths: {broken_embeds}"


def test_genesis_monograph_bidirectional_level_links():
    """Verify that genesis.md contains valid links to each modular level file in levels/."""
    assert GENESIS_MONOGRAPH.exists(), f"Missing monograph: {GENESIS_MONOGRAPH}"
    content = GENESIS_MONOGRAPH.read_text(encoding="utf-8")

    # Check links for Levels 00 to 21
    for lvl in range(22):
        lvl_pattern = f"level_{lvl:02d}_"
        assert lvl_pattern in content, f"genesis.md missing link for level {lvl:02d}"

    # Verify all markdown links in genesis.md resolve
    links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)
    broken_links = []
    for label, link in links:
        if link.startswith("http") or link.startswith("#") or link.startswith("mailto:"):
            continue
        clean_link = link.split("#")[0]
        if not clean_link:
            continue
        resolved = (GENESIS_DIR / clean_link).resolve()
        if not resolved.exists():
            broken_links.append((label, link, str(resolved)))

    assert not broken_links, f"Broken links in genesis.md: {broken_links}"


def test_genesis_levels_readme_catalog_totality():
    """Verify that levels/README.md catalogs all existing level files."""
    assert GENESIS_LEVELS_README.exists()
    content = GENESIS_LEVELS_README.read_text(encoding="utf-8")
    level_files = sorted(GENESIS_LEVELS_DIR.glob("level_*.md"))

    missing_from_catalog = []
    for f in level_files:
        if f.name not in content:
            missing_from_catalog.append(f.name)

    assert not missing_from_catalog, f"levels/README.md missing entries for: {missing_from_catalog}"


def test_genesis_ongoing_image_totality():
    """Verify that 6_genesis_ongoing/_images contains all 22 SVGs and they are referenced."""
    assert GENESIS_ONGOING_IMAGES_DIR.exists()
    svgs = sorted(GENESIS_ONGOING_IMAGES_DIR.glob("genesis_ongoing_*.svg"))
    assert len(svgs) == 22, f"Expected 22 SVGs in 6_genesis_ongoing/_images, found {len(svgs)}"

    monograph_content = GENESIS_ONGOING_MONOGRAPH.read_text(encoding="utf-8")
    readme_content = GENESIS_ONGOING_README.read_text(encoding="utf-8")

    for svg in svgs:
        assert svg.name in monograph_content, f"{svg.name} not referenced in genesis_ongoing.md"
        assert svg.name in readme_content, (
            f"{svg.name} not referenced in 6_genesis_ongoing/README.md"
        )


def test_utf8_no_bom_cleanliness():
    """Verify that all documentation files are pure UTF-8 without BOM and free of Mojibake."""
    target_files = [
        GENESIS_MONOGRAPH,
        GENESIS_README,
        GENESIS_LEVELS_README,
        GENESIS_ONGOING_MONOGRAPH,
        GENESIS_ONGOING_README,
    ] + list(GENESIS_LEVELS_DIR.glob("level_*.md"))

    mojibake_patterns = [
        "\u00c3\u00a9",
        "\u00e2\u20ac\u2122",
        "\u00e2\u20ac\u2014",
        "\u00e2\u20ac\u0153",
    ]
    errors = []

    for f in target_files:
        raw = f.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            errors.append(f"BOM found in {f.name}")
        txt = raw.decode("utf-8")
        found = [p for p in mojibake_patterns if p in txt]
        if found:
            errors.append(f"Mojibake pattern {found} found in {f.name}")

    assert not errors, f"Encoding cleanliness violations: {errors}"


def test_genesis_levels_retain_current_source_and_claim_boundaries():
    """The source-pinned edition states carriers, premises, evidence and open work.

    Retired editorial phrases are not a proxy for these current boundaries.
    This check does not independently replay the cited source theorems.
    """
    for page in sorted(GENESIS_LEVELS_DIR.glob("level_*.md")):
        text = page.read_text(encoding="utf-8")
        assert 'authority_effect: "None"' in text, page.name
        assert "claim_status: source_scoped" in text, page.name
        assert "source_revision: f1d56c010e6ba10a3b9418bd7cc5953c067250f2" in text, page.name
        for boundary in ("**Carrier:**", "**Supplied assumptions:**", "**Statement:**", "**Evidence:**", "**Implementation or open obligation:**"):
            assert boundary in text, (page.name, boundary)
        assert "Source statements and recorded compilation are distinguished from fresh companion tests." in text
        assert "no identity with an S(n) stage or MSS index" in text
    spectral = (GENESIS_LEVELS_DIR / "level_19_spectral_zeta_fencing.md").read_text(encoding="utf-8")
    assert "requires further definitions and assumptions" in spectral
    assert "Finite polynomial bookkeeping is not evidence" in spectral
    embedding = (GENESIS_LEVELS_DIR / "level_22_conservative_family_embedding.md").read_text(encoding="utf-8")
    assert "natural_section_iff_embed" in embedding
    assert "not a general physical reconstruction" in embedding
    closeout = (GENESIS_LEVELS_DIR / "level_100_open_horizon_claim_ledger.md").read_text(encoding="utf-8")
    for status in ("CLOSED_WITH_OPEN_OBSTRUCTIONS", "READY_WITHIN_DECLARED_SCOPE", "UNSATISFIED"):
        assert status in closeout
    assert "116 runs are not closed at that bound" in closeout
    assert "No fresh blind run is authorized" in closeout

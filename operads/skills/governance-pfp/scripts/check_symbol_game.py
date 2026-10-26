#!/usr/bin/env python3
"""Check live Genesis/S(n) documentation and independent PFP invariants.

These are finite documentation checks, not mathematical certification.
AuthorityEffect: None.
"""
import os
import re
import runpy
from pathlib import Path
from typing import Tuple


def check_genesis_documentation_cross_references() -> Tuple[bool, str]:
    """Verify Genesis modular level documentation, SVG schematics, and monograph cross-references."""
    repo_root = Path(__file__).resolve().parents[4]
    if not (repo_root / "omega_engine_education").exists():
        curr = Path(__file__).resolve().parent
        while curr != curr.parent:
            if (curr / "omega_engine_education").exists():
                repo_root = curr
                break
            curr = curr.parent

    genesis_candidates = [
        repo_root / "omega_engine_education" / "documentation" / "001_oegen",
        repo_root / "omega_engine_education" / "documentation" / "2_genesis",
    ]
    genesis_dir = next((p for p in genesis_candidates if p.is_dir()), genesis_candidates[0])
    levels_dir = genesis_dir / "levels"
    monograph = genesis_dir / "genesis.md"
    levels_readme = levels_dir / "README.md"

    ongoing_candidates = [
        repo_root / "omega_engine_education" / "documentation" / "005_oegenong",
        repo_root / "omega_engine_education" / "documentation" / "060_genesis_ongoing",
        repo_root / "omega_engine_education" / "documentation" / "6_genesis_ongoing",
        repo_root / "omega_engine_education" / "documentation" / "4_genesis_ongoing",
    ]
    ongoing_dir = next((p for p in ongoing_candidates if p.is_dir()), ongoing_candidates[0])
    ongoing_images = ongoing_dir / "_images"
    ongoing_monograph = ongoing_dir / "genesis_ongoing.md"
    ongoing_readme = ongoing_dir / "README.md"

    if not levels_dir.exists():
        return False, f"Missing Genesis levels directory: {levels_dir}"
    if not monograph.exists():
        return False, f"Missing Genesis canonical monograph: {monograph}"
    if not levels_readme.exists():
        return False, f"Missing Genesis levels README: {levels_readme}"

    level_files = sorted(levels_dir.glob("level_*.md"))
    if len(level_files) < 33:
        return False, f"Expected at least 33 level files, found {len(level_files)}"

    core_levels = {
        int(f.name.split("_")[1]) for f in level_files if int(f.name.split("_")[1]) <= 21
    }
    if core_levels != set(range(22)):
        return False, f"Missing sealed core levels (00-21): {set(range(22)) - core_levels}"

    missing_refs = []
    missing_embeds = []
    broken_embeds = []
    for f in level_files:
        txt = f.read_text(encoding="utf-8")
        if "genesis.md" not in txt:
            missing_refs.append(f.name)
        lvl_num = int(f.name.split("_")[1])
        if lvl_num <= 21:
            imgs = re.findall(r"!\[.*?\]\((.*?)\)", txt)
            if not imgs:
                missing_embeds.append(f.name)
            else:
                for img in imgs:
                    if img.startswith("file:///"):
                        target = Path(img[8:].replace("/", "\\") if os.name == "nt" else img[7:])
                    elif os.path.isabs(img):
                        target = Path(img)
                    else:
                        target = (f.parent / img).resolve()
                    if not target.exists():
                        broken_embeds.append((f.name, img))

    if missing_refs:
        return False, f"Level files missing reference to genesis.md: {missing_refs}"
    if missing_embeds:
        return False, f"Sealed core levels missing SVG embeds: {missing_embeds}"
    if broken_embeds:
        return False, f"Sealed core levels with broken image paths: {broken_embeds}"

    mono_txt = monograph.read_text(encoding="utf-8")
    for lvl in range(22):
        if f"level_{lvl:02d}_" not in mono_txt:
            return False, f"genesis.md missing reference to level_{lvl:02d}"

    if not ongoing_images.exists():
        return False, f"Missing 4_genesis_ongoing/_images directory: {ongoing_images}"

    ongoing_svgs = sorted(ongoing_images.glob("genesis_ongoing_*.svg"))
    if len(ongoing_svgs) != 22:
        return False, f"Expected 22 ongoing SVGs, found {len(ongoing_svgs)}"

    ongoing_mono_txt = ongoing_monograph.read_text(encoding="utf-8")
    ongoing_readme_txt = ongoing_readme.read_text(encoding="utf-8")
    for svg in ongoing_svgs:
        if svg.name not in ongoing_mono_txt:
            return False, f"{svg.name} not referenced in genesis_ongoing.md"
        if svg.name not in ongoing_readme_txt:
            return False, f"{svg.name} not referenced in 4_genesis_ongoing/README.md"

    # Encoding & Mojibake cleanliness
    target_docs = [monograph, levels_readme, ongoing_monograph, ongoing_readme] + level_files
    mojibake_patterns = [
        "\u00c3\u00a9",
        "\u00e2\u20ac\u2122",
        "\u00e2\u20ac\u2014",
        "\u00e2\u20ac\u0153",
    ]
    for td in target_docs:
        raw = td.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            return False, f"BOM detected in {td.name}"
        decoded = raw.decode("utf-8")
        for pat in mojibake_patterns:
            if pat in decoded:
                return False, f"Mojibake pattern detected in {td.name}"

    return (
        True,
        "Genesis modular levels (33 files), SVG schematics (44 SVGs), and monograph cross-references verified",
    )


def check_sn_level_documentation_purity() -> Tuple[bool, str]:
    """Walk the current lesson/domain layout and check local references."""
    root = Path(__file__).resolve().parents[4] / "omega_engine_education/documentation/002_oesn"
    for name in ("sn.md", "README.md", "reading_guide.md", "curriculum.md", "source_correspondence.md"):
        if not (root / name).is_file():
            return False, f"Missing S(n) navigation: {name}"
    for name in ("levels", "domains", "grammar", "normal_forms", "rewriting", "code", "lean4", "papers"):
        if not (root / name).is_dir():
            return False, f"Missing S(n) directory: {name}"
    levels = sorted((root / "levels").glob("level_*.md"))
    if {int(p.name.split("_")[1]) for p in levels} != set(range(22)):
        return False, "S(n) lesson set must contain levels 00 through 21"
    pages = levels + list(root.glob("*.md")) + list((root / "domains").glob("*.md"))
    for page in pages:
        raw = page.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            return False, f"BOM in {page}"
        text = raw.decode("utf-8")
        if page in levels and not re.search(r'(?m)^authority_effect: ["\']?None["\']?$', text):
            return False, f"Missing lesson authority boundary: {page}"
        for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text):
            target = target.split("#")[0].strip("<>")
            if not target or re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                continue
            if not (page.parent / target).exists():
                return False, f"Broken local reference in {page}: {target}"
    return True, f"S(n) navigation, {len(levels)} lessons, domains and local references verified"


def main() -> int:
    failed = 0
    for check in (check_genesis_documentation_cross_references, check_sn_level_documentation_purity):
        try:
            ok, message = check()
        except Exception as error:
            ok, message = False, str(error)
        print(f"[{'PASS' if ok else 'FAIL'}] {check.__name__}: {message}")
        failed += not ok
    pfp = runpy.run_path(str(Path(__file__).with_name("check_pfp.py")))
    pfp_failed = pfp["main"]()
    return int(bool(failed or pfp_failed))


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Check numbered-track lesson folders for prose, notebook, and videos/.

AuthorityEffect: None. A passing shape check does not show that a person learned.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path


def find_repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".agents").is_dir() and (parent / "education").is_dir():
            return parent
    raise RuntimeError(f"Could not locate repo root from {current}")


class LessonEntry:
    def __init__(
        self,
        name: str,
        relative_path: str,
        notebook: Path,
        prose: Path,
        videos: Path,
        scripts: Path | None = None,
        is_categorized: bool = False,
    ):
        self.name = name
        self.relative_path = relative_path
        self.notebook = notebook
        self.prose = prose
        self.videos = videos
        self.scripts = scripts
        self.is_categorized = is_categorized


class LessonDiscoveryError(ValueError):
    """A declared lesson relationship is unavailable or ambiguous."""


def _supplement_for(page: Path) -> str | None:
    """Read one literal supplement_for binding only inside a leading header."""
    lines = page.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        return None
    closing = next((index for index, line in enumerate(lines[1:], 1) if line == "---"), None)
    if closing is None:
        raise LessonDiscoveryError(f"MALFORMED_LESSON_HEADER: {page.name}")
    declared = [line for line in lines[1:closing] if line.lstrip().startswith("supplement_for")]
    if not declared:
        return None
    if len(declared) != 1:
        raise LessonDiscoveryError(f"DUPLICATE_SUPPLEMENT_BINDING: {page.name}")
    matched = re.fullmatch(r"supplement_for: ([A-Za-z0-9][A-Za-z0-9_]*)", declared[0])
    if matched is None:
        raise LessonDiscoveryError(f"INVALID_SUPPLEMENT_BINDING: {page.name}")
    return matched[1]


def _validate_supplements(stems: set[str], bindings: dict[str, str]) -> set[str]:
    """A supplement binds exactly one existing local primary, never another supplement."""
    primaries = stems - bindings.keys()
    for supplement, target in bindings.items():
        if supplement == target:
            raise LessonDiscoveryError(f"SELF_SUPPLEMENT_BINDING: {supplement}")
        if target not in primaries:
            raise LessonDiscoveryError(f"SUPPLEMENT_TARGET_NOT_PRIMARY: {supplement} -> {target}")
        same_name = sorted(stem for stem in primaries if stem.casefold() == target.casefold())
        if same_name != [target]:
            raise LessonDiscoveryError(f"AMBIGUOUS_SUPPLEMENT_PRIMARY: {target}")
    return primaries


def _register_supplement(stems: set[str], bindings: dict[str, str], stem: str, target: str) -> None:
    same_name = sorted(name for name in stems if name.casefold() == stem.casefold())
    if same_name != [stem]:
        raise LessonDiscoveryError(f"AMBIGUOUS_SUPPLEMENT_IDENTITY: {stem}")
    if stem in bindings:
        raise LessonDiscoveryError(f"DUPLICATE_SUPPLEMENT_IDENTITY: {stem}")
    same_target = sorted(name for name in stems if name.casefold() == target.casefold())
    if same_target and same_target != [target]:
        raise LessonDiscoveryError(f"AMBIGUOUS_SUPPLEMENT_PRIMARY: {target}")
    bindings[stem] = target


def _categorized_stems(track: Path) -> set[str]:
    stems = {path.stem for path in (track / "notebooks").glob("*.ipynb")}
    concepts = list((track / "concepts").glob("*.md"))
    stems.update(page.stem for page in concepts)
    if (track / "scripts").is_dir():
        stems.update(page.stem for page in (track / "scripts").glob("*.md")
                     if not page.stem.startswith("script_"))
    bindings = {}
    for page in concepts:
        target = _supplement_for(page)
        if target is not None:
            _register_supplement(stems, bindings, page.stem, target)
    return _validate_supplements(stems, bindings)


def _categorized_entries(track: Path) -> list[LessonEntry]:
    return [LessonEntry(
        name=stem, relative_path=f"{track.name}/{stem}",
        notebook=track / "notebooks" / f"{stem}.ipynb",
        prose=track / "concepts" / f"{stem}.md", videos=track / "videos",
        scripts=track / "scripts" / f"{stem}.md", is_categorized=True,
    ) for stem in sorted(_categorized_stems(track))]


def _legacy_entries(track: Path, lessons: Path) -> list[LessonEntry]:
    entries = []
    for child in sorted(path for path in track.iterdir() if path.is_dir()):
        notebook = child / f"{child.name}.ipynb"
        if notebook.is_file():
            entries.append(LessonEntry(
                name=child.name, relative_path=child.relative_to(lessons).as_posix(),
                notebook=notebook, prose=child / f"{child.name}.md",
                videos=child / "videos", scripts=None, is_categorized=False,
            ))
    return entries


def find_lessons(lessons: Path) -> list[LessonEntry]:
    entries: list[LessonEntry] = []
    for track in sorted(path for path in lessons.iterdir() if path.is_dir()):
        if re.match(r"^[0-9]{3,4}_", track.name) is None:
            continue
        if (track / "notebooks").is_dir() and (track / "concepts").is_dir():
            entries.extend(_categorized_entries(track))
        else:
            entries.extend(_legacy_entries(track, lessons))
    return entries


def _curriculum_roots(repo_root: Path) -> list[Path]:
    education = repo_root / "education"
    curriculum_base = education / "curriculum"
    docs_base = education / "documentation"
    return [
        curriculum_base / "lessons", curriculum_base / "0_s_n",
        curriculum_base / "1_mssn", curriculum_base / "2_genesis",
        curriculum_base / "3_the_symbol_game_proposal_fidelity_protocol_pfp",
        docs_base / "0_s_n" / "curriculum", docs_base / "000_s_n" / "curriculum",
        docs_base / "1_minimal_symbol_system_n_mssn" / "curriculum",
        docs_base / "003_minimal_symbol_system_n_mssn" / "curriculum",
        docs_base / "2_genesis" / "curriculum", docs_base / "001_genesis" / "curriculum",
        docs_base / "3_the_symbol_game_proposal_fidelity_protocol_pfp" / "curriculum",
        docs_base / "030_the_symbol_game_proposal_fidelity_protocol_pfp" / "curriculum",
        docs_base / "004_oepfp" / "curriculum",
        docs_base / "7_witnessed_difference_programme_wdp" / "curriculum",
        docs_base / "070_witnessed_difference_programme_wdp" / "curriculum",
        docs_base / "006_oewdp" / "curriculum", docs_base / "007_oelggr" / "curriculum",
    ]


def _collect_lessons(repo_root: Path) -> list[LessonEntry]:
    existing = [path for path in _curriculum_roots(repo_root) if path.is_dir()]
    if existing:
        return [entry for path in existing for entry in find_lessons(path)]
    old_documented = repo_root / "education/documentation/3_the_symbol_game_proposal_fidelity_protocol_pfp/lessons"
    lessons = old_documented if old_documented.is_dir() else repo_root / "education/the_symbol_game/lessons"
    if not lessons.is_dir():
        raise LessonDiscoveryError(f"missing lessons directory: {lessons}")
    return find_lessons(lessons)


def _notebook_shape_failures(notebook: Path) -> list[str]:
    failures: list[str] = []
    try:
        payload = json.loads(notebook.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        failures.append(f"notebook is not JSON: {exc.msg}")
    else:
        if not isinstance(payload.get("cells"), list):
            failures.append("notebook has no cells list")
    return failures


def shape_failures(lesson: LessonEntry) -> list[str]:
    failures: list[str] = []
    if not lesson.prose.is_file():
        failures.append("missing prose page")
    if not lesson.notebook.is_file():
        failures.append("missing notebook")
    if not lesson.videos.is_dir():
        failures.append("missing videos directory")
    if lesson.scripts is not None and not lesson.scripts.is_file():
        failures.append("missing script file")
    if lesson.prose.is_file():
        text = lesson.prose.read_text(encoding="utf-8")
        link_options = [
            f"]({lesson.name}.ipynb)",
            f"](../notebooks/{lesson.name}.ipynb)",
        ]
        if not any(opt in text for opt in link_options):
            failures.append("prose page does not link to the notebook")
    if lesson.notebook.is_file():
        failures.extend(_notebook_shape_failures(lesson.notebook))
    return failures


def _cell_source(cell: object) -> str:
    if not isinstance(cell, dict):
        return ""
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(part for part in source if isinstance(part, str))
    if isinstance(source, str):
        return source
    return ""


def _has_real_assert(source: str) -> bool:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assert):
            continue
        test = node.test
        if isinstance(test, ast.Constant) and test.value is True:
            continue
        return True
    return False


def lacks_assert(notebook: Path) -> bool:
    """True when no code cell has an assert other than `assert True`.

    Markdown text does not count. A cell that only says `assert True` stays open.
    """
    try:
        payload = json.loads(notebook.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return True
    cells = payload.get("cells")
    if not isinstance(cells, list):
        return True
    for cell in cells:
        if not isinstance(cell, dict) or cell.get("cell_type") != "code":
            continue
        if _has_real_assert(_cell_source(cell)):
            return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        "--repo-root",
        dest="repo_root",
        type=Path,
        default=None,
        help="Root path of the repository (defaults to auto-discovered repo root).",
    )
    parser.add_argument(
        "--strict-checks",
        action="store_true",
        help="exit 1 when a numbered-track notebook contains no assert",
    )
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve() if args.repo_root else find_repo_root()
    try:
        lessons_list = _collect_lessons(repo_root)
    except LessonDiscoveryError as exc:
        print(f"[FAIL] Lesson discovery refused: {exc}", file=sys.stderr)
        return 1
    shape: list[str] = []
    open_checks: list[str] = []
    for lesson in lessons_list:
        relative = lesson.relative_path
        for failure in shape_failures(lesson):
            shape.append(f"{relative}: {failure}")
        if lesson.notebook.is_file() and lacks_assert(lesson.notebook):
            open_checks.append(relative)

    print(f"lesson_folders={len(lessons_list)}")
    print(f"shape_failures={len(shape)}")
    print(f"open_learning_checks={len(open_checks)}")
    for item in shape:
        print(f"SHAPE {item}")
    for item in open_checks:
        print(f"OPEN {item}")

    if args.strict_checks and len(lessons_list) == 0:
        print("[FAIL] Zero lessons discovered under strict checks.", file=sys.stderr)
        return 1
    if shape:
        return 1
    if args.strict_checks and open_checks:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

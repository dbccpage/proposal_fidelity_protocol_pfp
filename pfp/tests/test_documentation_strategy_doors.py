"""Section 6 door invariants for the symbol-game documentation strategy.

Dead how-to-play links, a newcomer README that pastes the internal CONTEXT
avoid-list, a packet index that drifts from its directory, a tower page that
calls cosmology or consciousness verified core, notebook filenames outside
cp1252 are refusals. The packet index is the README beside the contract
files that are already on disk. Creating ``contracts_packets/symbol_game``
is a refusal: that path was not a corpus. Counts are computed from the
directory, never taken from the strategy's recalled figure.

AuthorityEffect: None.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

REPO_ROOT = Path(__file__).resolve().parents[2]

_SKIP_DIR_NAMES = frozenset({".git", "node_modules", "__pycache__", ".venv"})
_LIVE_README_TAIL = (
    "education",
    "the_symbol_game",
    "lessons",
    "how_to_play",
    "readme.md",
)
_THEORY_RELATIVE = Path("research") / "mssn_sn_tower" / "_theory" / "README.md"
_AVOID_MARK = "_Avoid_:"
_FENCE_PHRASE = "not part of the verified core"
_FILE_EXTENSIONS = frozenset(
    {
        "md",
        "yaml",
        "yml",
        "json",
        "txt",
        "py",
        "toml",
        "lean",
        "sql",
        "csv",
        "svg",
        "png",
        "ipynb",
    }
)
_DOOR_DOCS = (
    REPO_ROOT / "research" / "mssn_sn_tower" / "00_index.md",
    REPO_ROOT / "research" / "mssn_sn_tower" / "mssn.md",
)
_LIVE_HOW_TO_PLAY = (
    REPO_ROOT
    / "education"
    / "the_symbol_game"
    / "lessons"
    / "how_to_play"
    / "readme.md"
)
_SYMBOL_README = REPO_ROOT / "pfp" / "README.md"
_PACKET_DIR = (
    REPO_ROOT
    / "governance"
    / "contracts"
    / "contracts_pfp"
)
_ABSENT_PACKET_HOME = (
    REPO_ROOT
    / "governance"
    / "contracts"
    / "contracts_packets"
    / "symbol_game"
)
_TOWER_README = REPO_ROOT / "research" / "mssn_sn_tower" / "1_the_tower" / "README.md"
_EDUCATION_ROOT = REPO_ROOT / "education"

_INLINE_LINK = re.compile(
    r"\[(?:\\.|[^\[\]\n])*\]\(\s*(<[^>\n]+>|[^)\s]+)"
    r"(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)"
)
_REF_DEF = re.compile(
    r"(?m)^[ ]{0,3}\[(?:\\.|[^\[\]\n]+)\]:[ \t]*(<[^>\n]+>|\S+)"
)
_BACKTICK = re.compile(r"`([^`\n]+)`")
_TOPIC = re.compile(r"cosmology|consciousness", re.IGNORECASE)
_CORE_NEGATION = re.compile(
    r"\b(?:not|outside|isn't|aren't)\b"
    r"(?:\s+in)?"
    r"(?:\s+part\s+of)?"
    r"(?:\s+(?:the|a|an|our))?"
    r"\s+verified core\b",
    re.IGNORECASE,
)


def _strip_fences(text: str) -> str:
    lines = text.splitlines(keepends=True)
    kept: list[str] = []
    fence: str | None = None
    for line in lines:
        marker = line.lstrip()
        if fence is None:
            if marker.startswith("```") or marker.startswith("~~~"):
                fence = marker[:3]
                continue
            kept.append(line)
            continue
        if marker.startswith(fence):
            fence = None
    return "".join(kept)


def _strip_angle(target: str) -> str:
    if len(target) >= 2 and target[0] == "<" and target[-1] == ">":
        return target[1:-1].strip()
    return target


def markdown_link_targets(markdown: str) -> list[str]:
    """Inline and reference-definition targets, fences removed."""
    plain = _strip_fences(markdown)
    targets: list[str] = []
    for pattern in (_INLINE_LINK, _REF_DEF):
        for match in pattern.finditer(plain):
            cleaned = _strip_angle(match.group(1).strip())
            if cleaned:
                targets.append(cleaned)
    return targets


def _is_file_uri(target: str) -> bool:
    return urlparse(_strip_angle(target.strip())).scheme == "file"


def _path_from_file_uri(target: str) -> Path:
    parsed = urlparse(_strip_angle(target.strip()))
    path_text = unquote(parsed.path)
    netloc = unquote(parsed.netloc)
    if re.match(r"^[A-Za-z]:$", netloc):
        path_text = netloc + path_text
    elif re.match(r"^/[A-Za-z]:([/\\]|$)", path_text):
        path_text = path_text[1:]
    return Path(path_text)


def is_relative_file_target(target: str) -> bool:
    raw = _strip_angle(target.strip())
    if not raw or raw.startswith("#"):
        return False
    parsed = urlparse(raw)
    if parsed.scheme:
        return False
    path_text = unquote(parsed.path).replace("\\", "/")
    if not path_text or path_text.startswith("/") or re.match(r"^[A-Za-z]:", path_text):
        return False
    return True


def resolve_markdown_target(target: str, base_dir: Path) -> Path | None:
    """Resolve a relative path or ``file:///`` URL. Other schemes are ignored."""
    raw = _strip_angle(target.strip())
    if not raw or raw.startswith("#"):
        return None
    parsed = urlparse(raw)
    if parsed.scheme == "file":
        return _path_from_file_uri(raw)
    if parsed.scheme:
        return None
    path_text = unquote(parsed.path).replace("\\", "/")
    if not path_text:
        return None
    if path_text.startswith("/") or re.match(r"^[A-Za-z]:", path_text):
        return Path(path_text)
    return (base_dir / path_text).resolve()


def missing_file_links(markdown: str, base_dir: Path) -> list[str]:
    """File-link targets that do not resolve to an existing file."""
    missing: list[str] = []
    for raw in markdown_link_targets(markdown):
        resolved = resolve_markdown_target(raw, base_dir)
        if resolved is None:
            continue
        if not resolved.is_file():
            missing.append(raw)
    return missing


def _is_how_to_play_readme_target(target: str) -> bool:
    raw = _strip_angle(target.strip())
    parsed = urlparse(raw)
    if parsed.scheme == "file":
        path_text = unquote(parsed.path)
    elif parsed.scheme:
        return False
    else:
        path_text = unquote(parsed.path or raw)
    path_text = path_text.split("#", 1)[0].split("?", 1)[0].replace("\\", "/")
    parts = [part for part in path_text.split("/") if part not in {"", "."}]
    if len(parts) < 2:
        return False
    return parts[-1].casefold() == "readme.md" and parts[-2].casefold() == "how_to_play"


def _path_is_live_readme(path: Path, live: Path) -> bool:
    resolved = path.resolve()
    if resolved == live.resolve():
        return True
    parts = resolved.parts
    if len(parts) < len(_LIVE_README_TAIL):
        return False
    tail = tuple(part.casefold() for part in parts[-len(_LIVE_README_TAIL) :])
    expected = tuple(part.casefold() for part in _LIVE_README_TAIL)
    return tail == expected


def how_to_play_readme_problems(markdown: str, base_dir: Path, live: Path) -> list[str]:
    """Each how_to_play/readme.md link must be the live education file."""
    targets = [
        raw
        for raw in markdown_link_targets(markdown)
        if _is_how_to_play_readme_target(raw)
    ]
    if not targets:
        return ["no how_to_play/readme.md link"]
    problems: list[str] = []
    if not live.is_file():
        problems.append(f"live how-to-play readme missing: {live}")
    for raw in targets:
        resolved = resolve_markdown_target(raw, base_dir)
        if resolved is None or not resolved.is_file():
            problems.append(
                f"unresolved how_to_play/readme.md link {raw!r} -> {resolved}"
            )
            continue
        if not _path_is_live_readme(resolved, live):
            problems.append(
                f"how_to_play/readme.md link {raw!r} resolves to {resolved}, "
                "not education/the_symbol_game/lessons/how_to_play/readme.md"
            )
    return problems


def symbol_game_readme_failures(readme: Path, repo_root: Path) -> list[str]:
    """UTF-8 newcomer page, relative theory link, no pasted ``_Avoid_:`` list."""
    if not readme.is_file():
        return [f"missing file: {readme}"]
    try:
        text = readme.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return [f"not utf-8: {readme}: {exc}"]
    failures: list[str] = []
    if _AVOID_MARK in text:
        failures.append(
            f"contains {_AVOID_MARK} from the internal CONTEXT definition"
        )
    expected = (repo_root / _THEORY_RELATIVE).resolve()
    matched = False
    for raw in markdown_link_targets(text):
        if not is_relative_file_target(raw):
            continue
        resolved = resolve_markdown_target(raw, readme.parent)
        if resolved is not None and resolved.resolve() == expected:
            matched = True
            break
    if not matched:
        failures.append(
            "no relative link resolves to research/mssn_sn_tower/_theory/README.md"
        )
    elif not expected.is_file():
        failures.append(f"missing file: {expected}")
    return failures


def _norm_token(token: str) -> str:
    raw = _strip_angle(token.strip())
    if _is_file_uri(raw):
        return raw
    path_text = unquote(raw).replace("\\", "/")
    path_text = path_text.split("#", 1)[0].split("?", 1)[0]
    while path_text.startswith("./"):
        path_text = path_text[2:]
    return path_text


def _looks_like_concrete_filename(token: str) -> bool:
    norm = _norm_token(token)
    if not norm or norm.endswith("/"):
        return False
    if any(char.isspace() for char in norm):
        return False
    if any(char in norm for char in "*?<>|:"):
        return False
    if norm.startswith(("http://", "https://", "file:", "mailto:")):
        return False
    name = norm.split("/")[-1]
    if "." not in name or name.startswith("."):
        return False
    extension = name.rsplit(".", 1)[-1].casefold()
    return extension in _FILE_EXTENSIONS


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique


def _index_readme(directory: Path) -> Path | None:
    if not directory.is_dir():
        return None
    for child in directory.iterdir():
        if child.is_file() and child.name.casefold() == "readme.md":
            return child
    return None


def _non_readme_files(directory: Path, index: Path) -> list[Path]:
    index_resolved = index.resolve()
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(directory, followlinks=False):
        dirnames[:] = [name for name in dirnames if name not in _SKIP_DIR_NAMES]
        for filename in filenames:
            path = Path(dirpath) / filename
            if path.resolve() == index_resolved:
                continue
            files.append(path)
    return files


def _local_citations(text: str) -> list[str]:
    plain = _strip_fences(text)
    tokens: list[str] = []
    for raw in markdown_link_targets(plain):
        if is_relative_file_target(raw) or _is_file_uri(raw):
            tokens.append(_norm_token(raw))
    for span in _BACKTICK.findall(plain):
        if _looks_like_concrete_filename(span):
            tokens.append(_norm_token(span))
    return _dedupe(tokens)


def _resolved_citation(directory: Path, token: str) -> Path | None:
    if _is_file_uri(token):
        return _path_from_file_uri(token)
    if token.startswith(("/", "\\")) or re.match(r"^[A-Za-z]:", token):
        return Path(token)
    return (directory / token).resolve()


def _citation_names_file(relative: str, citations: list[str]) -> bool:
    relative_folded = relative.casefold()
    base_folded = Path(relative).name.casefold()
    for token in citations:
        norm = _norm_token(token).casefold()
        if norm in {relative_folded, base_folded}:
            return True
        if norm.endswith("/" + relative_folded) or norm.endswith("/" + base_folded):
            return True
    return False


def packet_index_drift(directory: Path) -> list[str]:
    """Directory files omitted by the index, or cited filenames that do not exist.

    The file count is ``len`` of the non-README walk. It is not a fixed census.
    """
    if not directory.is_dir():
        return [f"missing directory: {directory}"]
    index = _index_readme(directory)
    if index is None:
        return [f"missing index README.md: {directory / 'README.md'}"]
    try:
        text = index.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return [f"not utf-8: {index}: {exc}"]
    files = _non_readme_files(directory, index)
    citations = _local_citations(text)
    resolved_names: set[str] = set()
    unresolved: list[str] = []
    for token in citations:
        resolved = _resolved_citation(directory, token)
        if resolved is not None and resolved.is_file():
            resolved_names.add(resolved.name.casefold())
            continue
        unresolved.append(token)
    directory_names = {path.name.casefold() for path in files}
    dangling = [
        token
        for token in unresolved
        if Path(_norm_token(token)).name.casefold() not in resolved_names
        and Path(_norm_token(token)).name.casefold() not in directory_names
    ]
    omitted = [
        path.relative_to(directory).as_posix()
        for path in files
        if not _citation_names_file(path.relative_to(directory).as_posix(), citations)
    ]
    count = len(files)
    failures: list[str] = []
    if omitted:
        failures.append(
            f"computed {count} non-README files; index omits {len(omitted)}: {omitted}"
        )
    if dangling:
        failures.append(
            f"computed {count} non-README files; "
            f"index cites {len(dangling)} missing filename(s): {dangling}"
        )
    return failures


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"[\n.!?]+", text) if part.strip()]


def affirmative_verified_core_claims(text: str) -> list[str]:
    """Sentences that place cosmology or consciousness in the verified core."""
    claims: list[str] = []
    for sentence in _sentences(text):
        if _TOPIC.search(sentence) is None:
            continue
        if "verified core" not in sentence.casefold():
            continue
        if _CORE_NEGATION.search(sentence) is not None:
            continue
        claims.append(" ".join(sentence.split()))
    return claims


def tower_fence_failures_from_text(text: str) -> list[str]:
    failures: list[str] = []
    if _FENCE_PHRASE not in text.casefold():
        failures.append(f"missing phrase {_FENCE_PHRASE!r}")
    claims = affirmative_verified_core_claims(text)
    if claims:
        failures.append(
            "says cosmology or consciousness folders are verified core: "
            + " | ".join(claims)
        )
    return failures


def tower_fence_failures(path: Path) -> list[str]:
    if not path.is_file():
        return [f"missing file: {path}"]
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return [f"not utf-8: {path}: {exc}"]
    return tower_fence_failures_from_text(text)


def cp1252_blocked_filenames(names: list[str]) -> list[str]:
    blocked: list[str] = []
    for name in names:
        try:
            name.encode("cp1252")
        except UnicodeEncodeError:
            blocked.append(name)
    return blocked


def directories_named(root: Path, name: str) -> list[Path]:
    """Bounded walk. Skips ``.git``, ``node_modules``, ``__pycache__``, and ``.venv``."""
    found: list[Path] = []
    if not root.exists():
        return found
    errors: list[OSError] = []

    def _onerror(err: OSError) -> None:
        # Broken junctions and ACL denials are not matches. A failure to list
        # the walk root is. WinError 2/3/5: missing path or access denied.
        filename = getattr(err, "filename", None)
        if filename is not None and Path(filename) == root:
            errors.append(err)
            return
        if isinstance(err, (PermissionError, FileNotFoundError, NotADirectoryError)):
            return
        if getattr(err, "winerror", None) in {2, 3, 5}:
            return
        errors.append(err)

    for dirpath, dirnames, _filenames in os.walk(
        root, followlinks=False, onerror=_onerror
    ):
        kept: list[str] = []
        for dirname in dirnames:
            if dirname in _SKIP_DIR_NAMES:
                continue
            if dirname == name:
                found.append(Path(dirpath) / dirname)
            kept.append(dirname)
        dirnames[:] = kept
    if errors:
        detail = "; ".join(str(err) for err in errors[:3])
        raise OSError(f"directory walk failed: {detail}")
    return found


def test_resolver_reports_relative_link_to_missing_file(tmp_path: Path) -> None:
    """A relative link to a missing file is reported; an existing sibling is not."""
    (tmp_path / "present.md").write_text("ok\n", encoding="utf-8")
    text = "See [gone](missing/readme.md) and [ok](present.md)."
    assert missing_file_links(text, tmp_path) == ["missing/readme.md"]


def test_resolver_reports_file_uri_to_missing_file(tmp_path: Path) -> None:
    """``file:///`` targets use the same resolver and fail when the file is absent."""
    missing = tmp_path / "gone.md"
    uri = missing.resolve().as_uri()
    reported = missing_file_links(f"See [gone]({uri}).", tmp_path)
    assert reported == [uri]


def test_how_to_play_helper_reports_dead_relative_readme(tmp_path: Path) -> None:
    live = (
        tmp_path
        / "education"
        / "notebooks"
        / "lessons"
        / "how_to_play"
        / "readme.md"
    )
    live.parent.mkdir(parents=True)
    live.write_text("play\n", encoding="utf-8")
    base = tmp_path / "research" / "mssn_sn_tower"
    base.mkdir(parents=True)
    problems = how_to_play_readme_problems(
        "See [play](how_to_play/readme.md).\n",
        base,
        live,
    )
    assert problems
    assert any("unresolved" in item for item in problems)


def test_how_to_play_helper_accepts_live_education_readme(tmp_path: Path) -> None:
    live = (
        tmp_path
        / "education"
        / "notebooks"
        / "lessons"
        / "how_to_play"
        / "readme.md"
    )
    live.parent.mkdir(parents=True)
    live.write_text("play\n", encoding="utf-8")
    base = tmp_path / "research" / "mssn_sn_tower"
    base.mkdir(parents=True)
    text = (
        "See [play](../../education/notebooks/lessons/"
        "how_to_play/readme.md).\n"
    )
    assert how_to_play_readme_problems(text, base, live) == []


def test_how_to_play_helper_accepts_file_uri_to_live_readme(tmp_path: Path) -> None:
    live = (
        tmp_path
        / "education"
        / "notebooks"
        / "lessons"
        / "how_to_play"
        / "readme.md"
    )
    live.parent.mkdir(parents=True)
    live.write_text("play\n", encoding="utf-8")
    uri = live.resolve().as_uri()
    problems = how_to_play_readme_problems(f"See [play]({uri}).\n", tmp_path, live)
    assert problems == [], problems


def test_index_and_mssn_how_to_play_links_resolve_to_live_readme() -> None:
    """``00_index.md`` and ``mssn.md`` how-to-play readme links hit the live file."""
    problems: list[str] = []
    for doc in _DOOR_DOCS:
        if not doc.is_file():
            problems.append(f"missing file: {doc}")
            continue
        try:
            text = doc.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            problems.append(f"{doc}: not utf-8: {exc}")
            continue
        relative = doc.relative_to(REPO_ROOT).as_posix()
        for item in how_to_play_readme_problems(text, doc.parent, _LIVE_HOW_TO_PLAY):
            problems.append(f"{relative}: {item}")
    assert problems == [], problems


def test_missing_symbol_game_readme_is_reported(tmp_path: Path) -> None:
    readme = tmp_path / "pfp" / "README.md"
    failures = symbol_game_readme_failures(readme, tmp_path)
    assert failures
    assert any(item.startswith("missing file:") for item in failures)


def test_symbol_game_readme_rejects_non_utf8(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_bytes(b"\xff\xfeB\x00")
    failures = symbol_game_readme_failures(readme, tmp_path)
    assert any("utf-8" in item for item in failures)


def test_symbol_game_readme_rejects_pasted_avoid_list(tmp_path: Path) -> None:
    theory = tmp_path / _THEORY_RELATIVE
    theory.parent.mkdir(parents=True)
    theory.write_text("# theory\n", encoding="utf-8")
    readme = tmp_path / "README.md"
    readme.write_text(
        "Start at [theory](research/mssn_sn_tower/_theory/README.md).\n"
        "_Avoid_: State machine\n",
        encoding="utf-8",
    )
    failures = symbol_game_readme_failures(readme, tmp_path)
    assert any(_AVOID_MARK in item for item in failures)
    assert not any("no relative link" in item for item in failures)


def test_symbol_game_readme_accepts_relative_theory_link(tmp_path: Path) -> None:
    theory = tmp_path / _THEORY_RELATIVE
    theory.parent.mkdir(parents=True)
    theory.write_text("# theory\n", encoding="utf-8")
    readme = tmp_path / "pkg" / "README.md"
    readme.parent.mkdir()
    readme.write_text(
        "Start at [theory](../research/mssn_sn_tower/_theory/README.md).\n",
        encoding="utf-8",
    )
    assert symbol_game_readme_failures(readme, tmp_path) == []


def test_symbol_game_readme_points_at_theory_without_avoid_list() -> None:
    """Package README is UTF-8, links relatively at ``_theory``, and omits ``_Avoid_:``."""
    failures = symbol_game_readme_failures(_SYMBOL_README, REPO_ROOT)
    assert failures == [], failures


def test_packet_index_drift_reports_missing_directory(tmp_path: Path) -> None:
    missing = tmp_path / "contracts_packets" / "symbol_game"
    drift = packet_index_drift(missing)
    assert drift
    assert any("missing directory" in item for item in drift)


def test_packet_index_drift_reports_missing_readme(tmp_path: Path) -> None:
    directory = tmp_path / "symbol_game"
    directory.mkdir()
    (directory / "a.yaml").write_text("a: 1\n", encoding="utf-8")
    drift = packet_index_drift(directory)
    assert any("README.md" in item for item in drift)


def test_packet_index_drift_reports_omission_and_dangling_citation(tmp_path: Path) -> None:
    directory = tmp_path / "symbol_game"
    directory.mkdir()
    (directory / "present.yaml").write_text("a: 1\n", encoding="utf-8")
    (directory / "README.md").write_text(
        "See [`absent.yaml`](absent.yaml) only.\n",
        encoding="utf-8",
    )
    joined = "\n".join(packet_index_drift(directory))
    assert "present.yaml" in joined
    assert "absent.yaml" in joined
    assert "computed 1" in joined


def test_packet_index_accepts_exact_directory_cover(tmp_path: Path) -> None:
    directory = tmp_path / "symbol_game"
    directory.mkdir()
    (directory / "present.yaml").write_text("a: 1\n", encoding="utf-8")
    nested = directory / "nested"
    nested.mkdir()
    (nested / "other.json").write_text("{}\n", encoding="utf-8")
    (directory / "README.md").write_text(
        "| [`present.yaml`](present.yaml) | one |\n"
        "| [`nested/other.json`](nested/other.json) | two |\n",
        encoding="utf-8",
    )
    assert packet_index_drift(directory) == []


def test_packet_index_reports_backtick_filename_that_does_not_exist(tmp_path: Path) -> None:
    directory = tmp_path / "symbol_game"
    directory.mkdir()
    (directory / "README.md").write_text("See `missing.yaml`.\n", encoding="utf-8")
    joined = "\n".join(packet_index_drift(directory))
    assert "missing.yaml" in joined
    assert "computed 0" in joined


def test_packet_index_does_not_treat_globs_as_filenames(tmp_path: Path) -> None:
    directory = tmp_path / "symbol_game"
    directory.mkdir()
    (directory / "README.md").write_text(
        "Pattern `*.contract.yaml` and `budget*`.\n",
        encoding="utf-8",
    )
    assert packet_index_drift(directory) == []


def test_packet_index_reports_outside_link_that_does_not_exist(tmp_path: Path) -> None:
    directory = tmp_path / "symbol_game"
    directory.mkdir()
    (directory / "README.md").write_text(
        "See [missing.yaml](../missing.yaml).\n",
        encoding="utf-8",
    )
    joined = "\n".join(packet_index_drift(directory))
    assert "missing.yaml" in joined


def test_symbol_game_packet_index_matches_directory() -> None:
    """Every non-README file is named, and every cited filename exists."""
    drift = packet_index_drift(_PACKET_DIR)
    assert drift == [], drift


def test_tower_fence_rejects_affirmative_cosmology_claim() -> None:
    text = (
        "Exploratory extensions, not part of the verified core.\n"
        "The cosmology folder is verified core.\n"
    )
    failures = tower_fence_failures_from_text(text)
    assert any("cosmology" in item.casefold() for item in failures)


def test_tower_fence_rejects_affirmative_consciousness_claim() -> None:
    text = (
        "not part of the verified core\n"
        "The consciousness folders are the verified core.\n"
    )
    failures = tower_fence_failures_from_text(text)
    assert any("consciousness" in item.casefold() for item in failures)


def test_tower_fence_accepts_exclusion_of_cosmology_and_consciousness() -> None:
    text = (
        "These genesis domains, including cosmology and consciousness, "
        "are exploratory extensions, not part of the verified core.\n"
    )
    assert tower_fence_failures_from_text(text) == []


def test_tower_fence_requires_exclusion_phrase() -> None:
    failures = tower_fence_failures_from_text(
        "Cosmology is exploratory and so is consciousness.\n"
    )
    assert any(_FENCE_PHRASE in item for item in failures)


def test_tower_fence_reports_missing_readme(tmp_path: Path) -> None:
    failures = tower_fence_failures(tmp_path / "README.md")
    assert any(item.startswith("missing file:") for item in failures)


def test_tower_readme_fences_cosmology_and_consciousness_off_verified_core() -> None:
    """The tower page carries the fence and does not call those folders verified core."""
    failures = tower_fence_failures(_TOWER_README)
    assert failures == [], failures


def test_cp1252_filename_check_rejects_codepage_gap() -> None:
    blocked = cp1252_blocked_filenames(
        [
            "N8_policy_about_policies.ipynb",
            "N9_\u0100_audit.ipynb",
            "N10_ok.ipynb",
        ]
    )
    assert blocked == ["N9_\u0100_audit.ipynb"]


def test_cp1252_filename_check_allows_windows_codepage_punctuation() -> None:
    assert cp1252_blocked_filenames(["N8_policy\u2014about.ipynb"]) == []


def test_directory_walk_reports_planted_name_and_skips_ignored_parents(
    tmp_path: Path,
) -> None:
    planted = tmp_path / "governance" / "contracts_pfp"
    planted.mkdir(parents=True)
    for parent in _SKIP_DIR_NAMES:
        ignored = tmp_path / parent / "contracts_pfp"
        ignored.mkdir(parents=True)
    found = {path.resolve() for path in directories_named(tmp_path, "contracts_pfp")}
    assert found == {planted.resolve()}


def test_directory_walk_continues_after_missing_junction(
    tmp_path: Path, monkeypatch: object
) -> None:
    """A broken junction must not hide a readable forbidden directory."""
    planted = tmp_path / "keep" / "contracts_pfp"
    planted.mkdir(parents=True)
    real_walk = os.walk

    def _flaky_walk(root: Path, followlinks: bool = False, onerror: object = None):
        if onerror is not None:
            missing = FileNotFoundError(
                3,
                "The system cannot find the path specified",
                str(tmp_path / "lean4" / ".lake" / "packages"),
            )
            missing.winerror = 3  # type: ignore[attr-defined]
            onerror(missing)  # type: ignore[operator]
        yield from real_walk(root, followlinks=followlinks, onerror=onerror)

    monkeypatch.setattr(os, "walk", _flaky_walk)  # type: ignore[arg-type]
    found = {
        path.resolve()
        for path in directories_named(tmp_path, "contracts_pfp")
    }
    assert planted.resolve() in found


def test_directory_walk_continues_after_permission_error(
    tmp_path: Path, monkeypatch: object
) -> None:
    """An unreadable sibling must not hide a readable forbidden directory."""
    planted = tmp_path / "keep" / "contracts_pfp"
    planted.mkdir(parents=True)
    real_walk = os.walk

    def _flaky_walk(root: Path, followlinks: bool = False, onerror: object = None):
        if onerror is not None:
            denied = PermissionError(13, "Access is denied", str(tmp_path / "locked"))
            denied.winerror = 5  # type: ignore[attr-defined]
            onerror(denied)  # type: ignore[operator]
        yield from real_walk(root, followlinks=followlinks, onerror=onerror)

    monkeypatch.setattr(os, "walk", _flaky_walk)  # type: ignore[arg-type]
    found = {
        path.resolve()
        for path in directories_named(tmp_path, "contracts_pfp")
    }
    assert planted.resolve() in found


def test_packet_index_uses_existing_corpus_and_not_the_absent_home() -> None:
    """The index sits on the corpus that exists. The named empty home stays absent."""
    assert _PACKET_DIR.is_dir()
    assert not _ABSENT_PACKET_HOME.exists()
    drift = packet_index_drift(_PACKET_DIR)
    assert drift == [], drift

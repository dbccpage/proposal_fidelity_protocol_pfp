"""Canonical source of provider credentials: the one place that finds an API key.

AuthorityEffect: None. Resolution order for a named key:

1. an explicit ``.env`` path supplied by the composition root, when it holds the key (a path
   that is not a file is ignored, so a typo falls through to the next source; an unreadable file
   is refused);
2. the process environment;
3. the ``.env`` at the root of the current checkout, then the ``.env`` at the root of the main
   checkout when running inside a linked git worktree.

Only those two file locations are ever read. Nothing walks parent directories looking for other
files, nothing is written to ``os.environ``, and a value is never placed in a refusal, a log or a
``repr``. Discovery (step 3) is off when ``OMEGA_CREDENTIAL_DISCOVERY=off``, when the caller
injects its own environment mapping, and by default whenever ``pytest`` is loaded (set the
variable to ``on`` to test discovery itself), so tests and fixtures never reach a real ``.env``.

A value with an unquoted inline comment (``KEY=abc # note``) is refused, not guessed at: the
Rust mirror of the parser does not strip comments, so the two would otherwise disagree.

The main checkout is found from git's own pointer files (``.git`` file, ``commondir``), with no
subprocess.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result

DISCOVERY_ENV = "OMEGA_CREDENTIAL_DISCOVERY"
ENV_FILE_NAME = ".env"
_LOCUS = "omega_engine_woland.infrastructure.providers.credential_source"


@dataclass(frozen=True)
class ResolvedCredential:
    name: str
    value: str = field(repr=False)
    source: str


def parse_env_text(text: str) -> dict[str, str]:
    """Parse ``KEY=VALUE`` lines. Comments and blank lines are skipped; one pair of quotes is removed."""
    out: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        out[key.strip()] = value
    return out


def _checkout_root(start: Path) -> tuple[Path, Path] | None:
    for directory in (start, *start.parents):
        marker = directory / ".git"
        if marker.exists():
            return directory, marker
    return None


def main_checkout_root(checkout: Path, marker: Path) -> Path | None:
    """Root of the main checkout when `checkout` is a linked worktree; `checkout` if it is main."""
    try:
        if marker.is_dir():
            return checkout
        text = marker.read_text(encoding="utf-8").strip()
        if not text.startswith("gitdir:"):
            return None
        gitdir = Path(text[len("gitdir:"):].strip())
        if not gitdir.is_absolute():
            gitdir = marker.parent / gitdir
        gitdir = gitdir.resolve()
        pointer = gitdir / "commondir"
        if not pointer.is_file():
            return None
        common = (gitdir / pointer.read_text(encoding="utf-8").strip()).resolve()
    except OSError:
        return None
    return common.parent if common.name == ".git" else None


def discovery_enabled(environ: Mapping[str, str] | None) -> bool:
    if environ is not None:
        return False
    setting = os.environ.get(DISCOVERY_ENV)
    if setting is None:
        return "pytest" not in sys.modules
    return setting.strip().lower() != "off"


def env_file_candidates(start: Path | None = None) -> list[tuple[str, Path]]:
    """The only files discovery may read: this checkout's `.env`, then the main checkout's."""
    found = _checkout_root((start or Path.cwd()).resolve())
    if found is None:
        return []
    root, marker = found
    candidates = [("env_file:checkout", root / ENV_FILE_NAME)]
    main = main_checkout_root(root, marker)
    if main is not None and main != root:
        candidates.append(("env_file:main_checkout", main / ENV_FILE_NAME))
    return candidates


def _names_with_inline_comment(text: str, names: Sequence[str]) -> set[str]:
    found: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        key, _, value = line.partition("=")
        value = value.strip()
        quoted = len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'"
        if key.strip() in names and not quoted and " #" in value:
            found.add(key.strip())
    return found


def _read(path: Path, names: Sequence[str]) -> Result[tuple[str, str] | None, Refusal]:
    try:
        text = path.read_bytes().decode("utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        return Err(Refusal("ENV_FILE_UNREADABLE", f"{path.name}: {type(exc).__name__}", _LOCUS))
    values = parse_env_text(text)
    commented = _names_with_inline_comment(text, names)
    for name in names:
        value = values.get(name, "").strip()
        if value and name in commented:
            return Err(Refusal(
                "ENV_VALUE_INLINE_COMMENT",
                f"{name} has an unquoted value containing ' #'; quote the value or move the comment",
                _LOCUS,
            ))
        if value:
            return Ok((name, value))
    return Ok(None)


def resolve_credential(
    names: Sequence[str],
    *,
    missing_code: str = "CREDENTIAL_MISSING",
    explicit_file: Path | str | None = None,
    environ: Mapping[str, str] | None = None,
    start: Path | None = None,
) -> Result[ResolvedCredential, Refusal]:
    """The first of `names` found, by the order in the module docstring."""
    if not names:
        return Err(Refusal(missing_code, "no credential name given", _LOCUS))
    if explicit_file is not None and Path(explicit_file).is_file():
        read = _read(Path(explicit_file), names)
        if isinstance(read, Err):
            return read
        if read.value is not None:
            return Ok(ResolvedCredential(read.value[0], read.value[1], "env_file:explicit"))
    env = os.environ if environ is None else environ
    for name in names:
        value = (env.get(name) or "").strip()
        if value:
            return Ok(ResolvedCredential(name, value, "environment"))
    first_refusal: Err | None = None
    if discovery_enabled(environ):
        for label, path in env_file_candidates(start):
            if not path.is_file():
                continue
            read = _read(path, names)
            if isinstance(read, Err):
                first_refusal = first_refusal or read
                continue
            if read.value is not None:
                return Ok(ResolvedCredential(read.value[0], read.value[1], label))
        if first_refusal is not None:
            return first_refusal
    tried = ["environment"]
    if explicit_file is not None:
        tried.insert(0, "explicit env file")
    if discovery_enabled(environ):
        tried += ["checkout .env", "main-checkout .env"]
    return Err(Refusal(missing_code, f"{' or '.join(names)} not found in: {', '.join(tried)}", _LOCUS))

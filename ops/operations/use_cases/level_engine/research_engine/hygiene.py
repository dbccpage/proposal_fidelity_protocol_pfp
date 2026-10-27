# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Count-only vocabulary hygiene for the native layers.

Runs the vendored 19L57G1 prose-watchlist matcher (its own normalisation,
stemming and two-word phrases) and its identifier firewall (the working
denylist, identifier-boundary matching) over every file of the scanned
layers.  It reports counts per file and never prints a matched word.

It also counts the programme's own outside names (kept in the binding layer),
which may
appear only in the layers that never port.

Scanned: ``payload/``, ``engine/``, ``lean/`` and ``lifts/`` (all port
unchanged in Mode I).
Exempt by design: ``bindings/``, ``bundles/`` and ``outward/`` (never port).

AuthorityEffect: None
"""

from __future__ import annotations

import importlib.util
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import ModuleType

from operations.domain.level_engine_context import (
    current_context,
)

from .sealed import vendored

ROOT = current_context().runtime_root
SCANNED = ("payload", "engine", "lean", "lifts")
SUFFIXES = (".py", ".md", ".json", ".txt", ".lean", ".toml")


@lru_cache(maxsize=1)
def _outside() -> re.Pattern[str]:
    """The programme's own outside names, kept in the binding layer so that
    this file does not carry them."""
    raw = json.loads((current_context().historical_path("bindings/outside_terms.json")).read_text(encoding="utf-8"))
    return re.compile("|".join(raw["patterns"]), re.IGNORECASE)


@lru_cache(maxsize=1)
def _matcher() -> ModuleType:
    spec = importlib.util.spec_from_file_location("vendored_watchlist", vendored("ci/check_prose_watchlist.py"))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@lru_cache(maxsize=1)
def _watched() -> Mapping[str, str]:
    data = _matcher().load(vendored("ci/prose_watchlist.json"))
    watched = data["watched"]
    assert isinstance(watched, dict)
    return watched


@lru_cache(maxsize=1)
def _firewall() -> tuple[re.Pattern[str], ...]:
    raw = json.loads(vendored("contact/analysis/contact_countermodels.json").read_text(encoding="utf-8"))
    block = raw["denylist"]
    names = [n for n in block["full_census"] if n not in set(block["subtracted_as_native_or_core"])]
    if len(names) != 102:
        raise RuntimeError("the vendored working denylist is not the pinned population of 102")
    return tuple(re.compile(r"(?<![\w])" + re.escape(n) + r"(?![\w])") for n in names)


@dataclass(frozen=True)
class Count:
    path: str
    watch: int
    firewall: int
    outside: int = 0


def scan_text(text: str) -> tuple[int, int, int]:
    w = len(_matcher().scan_text(text, _watched()))
    f = sum(1 for p in _firewall() if p.search(text))
    o = len(_outside().findall(text))
    return w, f, o


def files(root: Path = ROOT, layers: tuple[str, ...] = SCANNED) -> list[Path]:
    out: list[Path] = []
    engine_dir = Path(__file__).parent
    for layer in layers:
        d = (root / layer) if (root / layer).is_dir() else (engine_dir if layer == "engine" else None)
        if d is None:
            continue
        for p in sorted(d.rglob("*")):
            if p.is_file() and p.suffix in SUFFIXES and "__pycache__" not in p.parts:
                out.append(p)
    return out


def scan(root: Path = ROOT, layers: tuple[str, ...] = SCANNED) -> list[Count]:
    out = []
    for p in files(root, layers):
        w, f, o = scan_text(p.read_text(encoding="utf-8"))
        out.append(Count(p.relative_to(root).as_posix(), w, f, o))
    return out


def report(counts: list[Count]) -> tuple[int, list[str]]:
    """Total hits and one count-only line per file with any hit."""
    lines = [
        f"{c.path}: watch={c.watch} firewall={c.firewall} outside={c.outside}"
        for c in counts if c.watch or c.firewall or c.outside
    ]
    return sum(c.watch + c.firewall + c.outside for c in counts), lines

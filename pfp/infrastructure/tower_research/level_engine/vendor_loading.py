"""Scoped imports from explicitly pinned external evidence, without path mutation.

Research-grade adapter. AuthorityEffect: None.
"""
from __future__ import annotations

import importlib.abc
import importlib.util
from importlib.machinery import ModuleSpec
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class _EvidenceFinder(importlib.abc.MetaPathFinder):
    def __init__(self, roots: tuple[Path, ...]) -> None:
        self.roots = roots

    def find_spec(self, fullname: str, path: object = None, target: object = None) -> ModuleSpec | None:
        if path is not None:
            return None
        for root in self.roots:
            rel = root.joinpath(*fullname.split("."))
            init = rel / "__init__.py"
            if init.is_file():
                return importlib.util.spec_from_file_location(fullname, init, submodule_search_locations=[str(rel)])
            source = rel.with_suffix(".py")
            if source.is_file():
                return importlib.util.spec_from_file_location(fullname, source)
        return None


@contextmanager
def vendor_import_scope(*roots: Path) -> Iterator[None]:
    """Resolve only declared evidence roots; leave sys.path and clone bytes untouched."""
    finder = _EvidenceFinder(tuple(roots))
    prior = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    sys.meta_path.insert(0, finder)
    try:
        yield
    finally:
        sys.meta_path.remove(finder)
        sys.dont_write_bytecode = prior

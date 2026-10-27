"""Regenerate agent mirrors and catalog-derived projections.

The canonical YAML frontmatter is the sole licence source. This script never
reads a compatibility slice as input and never deletes untracked host files.
AuthorityEffect: None.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def _repo_root() -> Path:
    start = Path(__file__).resolve().parent
    for candidate in (start, *start.parents):
        if (candidate / ".agents").is_dir() and (
            candidate / "operads"
        ).is_dir():
            return candidate
    raise RuntimeError("repository root containing .agents and OEWAS was not found")


def main() -> int:
    repo_root = _repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from operads.infrastructure.capability_catalog_compiler import (
        HOST_NAMES,
        compile_capability_catalog,
        verify_host_projections,
        write_host_projections,
    )

    catalog = compile_capability_catalog(repo_root)
    for agent in catalog.agents:
        source = repo_root / ".agents" / agent.source_path
        for host in HOST_NAMES[1:]:
            target = repo_root / host / agent.source_path
            if not target.parent.is_dir():
                raise RuntimeError(f"host agent directory is missing: {target.parent}")
            shutil.copyfile(source, target)
    write_host_projections(repo_root, catalog)
    verify_host_projections(repo_root, catalog)
    print(
        f"agents={len(catalog.agents)} hosts={len(HOST_NAMES)} "
        f"catalog_digest={catalog.catalog_digest} authority_effect=none"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

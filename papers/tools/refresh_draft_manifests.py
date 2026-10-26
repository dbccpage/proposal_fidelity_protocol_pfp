"""Refresh local draft file custody without rebuilding historical archives or metadata."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import runpy
import sys


def refresh(package: Path) -> tuple[Path, Path]:
    package = package.resolve()
    old_path = list(sys.path)
    previous = sys.modules.pop("deposit_paths", None)
    try:
        policy = runpy.run_path(str(package / "verify_deposit.py"))
        excluded = set(policy["EXCLUDED_NAMES"]) | {"MANIFEST.sha256", "SHA256SUMS"}
        files = policy["walk_files"](
            package, policy["EXCLUDED_DIRS"], excluded, policy["EXCLUDED_SUFFIXES"]
        )
        entries = sorted(
            (p.relative_to(package).as_posix(), hashlib.sha256(p.read_bytes()).hexdigest())
            for p in files
        )
        manifest, sums = package / "MANIFEST.sha256", package / "SHA256SUMS"
        render = lambda rows: "".join(
            f"{digest}  {name}\n" for name, digest in sorted(rows)
        ).encode("utf-8")
        manifest.write_bytes(render(entries))
        sums.write_bytes(
            render([*entries, (manifest.name, hashlib.sha256(manifest.read_bytes()).hexdigest())])
        )
        errors = policy["check_manifest"](sums)
        if errors:
            raise ValueError("Draft manifest validation failed: " + "; ".join(errors))
        return manifest, sums
    finally:
        sys.path[:] = old_path
        sys.modules.pop("deposit_paths", None)
        if previous is not None:
            sys.modules["deposit_paths"] = previous


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packages", nargs="+", type=Path)
    args = parser.parse_args()
    for package in args.packages:
        refresh(package)
        print(f"Draft file manifests verified: {package}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

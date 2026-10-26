#!/usr/bin/env python3
"""Check the printed Section 3 blocks against source-bound DDC modules.

The source root must contain the seven files pinned by the inventory. Parent
package initialization is deliberately isolated. This is a focused source
check, not a complete repository, native adapter, or route execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import types
from pathlib import Path


def check(package: Path, source_root: Path) -> dict[str, object]:
    inventory = json.loads((package / "docs/source_inventory_2026_10_02.json").read_text())
    prefix = "omega_engine_pfp/domain/ddc/"
    hashes = {}
    for entry in inventory["inspected_sources"]:
        if not entry["path"].startswith(prefix):
            continue
        data = (source_root / entry["path"]).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest != entry["sha256"]:
            raise ValueError(f"historical source identity mismatch: {entry['path']}")
        hashes[entry["path"]] = digest
    if len(hashes) != 7:
        raise ValueError("expected seven pinned DDC source modules")
    for name, relative in (
        ("omega_engine_pfp", "omega_engine_pfp"),
        ("omega_engine_pfp.domain", "omega_engine_pfp/domain"),
    ):
        module = types.ModuleType(name)
        module.__path__ = [str(source_root / relative)]
        sys.modules[name] = module
    paper_bytes = (package / "paper.md").read_bytes()
    section = paper_bytes.decode().split("\n## 3.", 1)[1].split("\n## 4.", 1)[0]
    blocks = re.findall(r"```python\n(.*?)```", section, flags=re.S)
    if len(blocks) != 3:
        raise ValueError("expected three Section 3 Python blocks")
    namespace: dict[str, object] = {"__name__": "paper007_isolated_ddc"}
    for index, block in enumerate(blocks, 1):
        exec(compile(block, f"paper.md:section3-block-{index}", "exec"), namespace)
    residual = namespace["residual"]
    from omega_engine_pfp.domain.ddc.cochains import FunctionalBoundaryUnavailable

    try:
        residual.l1_norm()
    except FunctionalBoundaryUnavailable:
        norm_probe = "EXPECTED_REFUSAL: FunctionalBoundaryUnavailable"
    else:
        raise ValueError("retired cochain norm unexpectedly returned")
    return {
        "status": "PASS",
        "source_audit_commit": inventory["audit_commit"],
        "source_sha256": hashes,
        "paper_sha256": hashlib.sha256(paper_bytes).hexdigest(),
        "printed_blocks_executed": len(blocks),
        "retired_norm_probe": norm_probe,
        "scope": "seven source-bound DDC modules; parent initialization isolated; no full route",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    args = parser.parse_args()
    package = Path(__file__).resolve().parents[1]
    try:
        result = check(package, args.source_root.resolve())
    except Exception as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

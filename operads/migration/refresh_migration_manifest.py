"""Refresh or check successor-byte bindings in the OEWAS V3 migration manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


MIRROR_HOSTS = (".agents", ".claude", ".codex", ".grok")
ARTIFACT_BINDING = "SUCCESSOR_SKILL_BYTES"
MAPPING_STATUS = "DECLARED_UNADMITTED"


def render_manifest(repo_root: Path, manifest_path: Path) -> bytes:
    data: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = data.get("entries")
    if type(entries) is not list or data.get("total_entries") != len(entries):
        raise ValueError("manifest total_entries must equal the exact entries list length")

    data["artifact_binding"] = ARTIFACT_BINDING
    data["mapping_status"] = MAPPING_STATUS
    for entry in entries:
        successor_id = entry["successor_skill_id"]
        mirror_bytes = []
        for host in MIRROR_HOSTS:
            path = repo_root / host / "skills" / successor_id / "SKILL.md"
            mirror_bytes.append(path.read_bytes())
        if any(raw != mirror_bytes[0] for raw in mirror_bytes[1:]):
            raise ValueError(f"successor mirror drift: {successor_id}")
        raw = mirror_bytes[0]
        entry["blob_sha256"] = hashlib.sha256(raw).hexdigest()
        entry["byte_count"] = len(raw)
        entry["hosts"] = {host: True for host in MIRROR_HOSTS}
        entry["all_4_hosts_agree"] = True
        entry["residual_status"] = "unknown"

    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    manifest_path = Path(__file__).with_name("migration_manifest_v3.json")
    rendered = render_manifest(repo_root, manifest_path)
    if args.check:
        if manifest_path.read_bytes() != rendered:
            print("migration manifest is stale")
            return 1
        print("migration manifest is current")
        return 0
    manifest_path.write_bytes(rendered)
    print("migration manifest refreshed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

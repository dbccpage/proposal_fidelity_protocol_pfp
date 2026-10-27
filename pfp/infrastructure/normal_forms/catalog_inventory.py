"""Render the normal-form contract register in the education catalogue from the contracts themselves.

The register in ``014_normal_forms/catalog.md`` sits between two markers. ``--write`` regenerates
it from ``index.yaml`` and every ``nf.*.yaml`` contract; ``--check`` exits 1 when it has drifted.
AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml

from pfp.infrastructure.normal_forms.contract_paths import CONTRACTS_DIR, INDEX_PATH

BEGIN = "<!-- BEGIN GENERATED: normal-form contract register (catalog_inventory.py) -->"
END = "<!-- END GENERATED: normal-form contract register -->"
STATUS_ORDER = ("active", "draft", "deprecated")


def _catalog_path() -> Path:
    root = next(p for p in CONTRACTS_DIR.parents if (p / "education").is_dir())
    return root / "education" / "documentation" / "014_normal_forms" / "catalog.md"


def render(catalog_path: Path, contracts_dir: Path = CONTRACTS_DIR, index_path: Path = INDEX_PATH) -> str:
    index = yaml.safe_load(index_path.read_text(encoding="utf-8"))["contracts"]
    status_of = {cid: status for status in STATUS_ORDER for cid in index.get(status, [])}
    rows = []
    for path in sorted(contracts_dir.rglob("nf.*.yaml")):
        identity = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("identity") or {}
        cid = identity.get("id", path.stem)
        link = os.path.relpath(path, catalog_path.parent).replace(os.sep, "/")
        rows.append((STATUS_ORDER.index(status_of[cid]) if cid in status_of else len(STATUS_ORDER), cid,
                     f"| [`{cid}`]({link}) | {identity.get('short_name', '')} | {identity.get('name', '')} "
                     f"| {identity.get('family', '')} | `{status_of.get(cid, 'unindexed')}` "
                     f"| {identity.get('theory_status', '')} | {identity.get('verification_status', '')} |"))
    counts = {status: sum(1 for cid in status_of if status_of[cid] == status) for status in STATUS_ORDER}
    lines = [BEGIN, "",
             f"{len(rows)} contract files; `index.yaml` lists "
             + ", ".join(f"{counts[s]} {s}" for s in STATUS_ORDER) + ".", "",
             "| Contract | Short name | Name | Family | Index status | Theory | Verification |",
             "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
             *[row for _, _, row in sorted(rows)], "", END]
    return "\n".join(lines)


def _replace(text: str, block: str) -> str:
    if BEGIN not in text or END not in text:
        raise ValueError("catalogue markers missing")
    head, rest = text.split(BEGIN, 1)
    return head + block + rest.split(END, 1)[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    catalog = _catalog_path()
    text = catalog.read_text(encoding="utf-8")
    updated = _replace(text, render(catalog))
    if args.check:
        if updated != text:
            print("NORMAL_FORM_REGISTER_DRIFT: run catalog_inventory --write", file=sys.stderr)
            return 1
        print("NORMAL_FORM_REGISTER_OK")
        return 0
    catalog.write_text(updated, encoding="utf-8", newline="\n")
    print("NORMAL_FORM_REGISTER_WRITTEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

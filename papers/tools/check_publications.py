"""Check canonical source bindings, export hashes, and local Markdown file links."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
from pathlib import Path
from urllib.parse import unquote, urlsplit


def checked_path(root: Path, relative: str) -> Path:
    base = root.absolute()
    raw = base / relative
    target = raw.resolve()
    if not target.is_relative_to(base.resolve()):
        raise ValueError(f"Path escapes collection: {relative}")
    for component in (raw, *raw.parents):
        info = component.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"Non-regular path or reparse point: {relative}")
        if component == raw and not stat.S_ISREG(info.st_mode):
            raise ValueError(f"Non-regular file: {relative}")
        if component == base:
            break
    return target


def validate_manifest(root: Path, publication: str = "publication") -> list[str]:
    try:
        manifest = json.loads(checked_path(root, f"{publication}/manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [str(exc)]
    errors = []
    for section in ("inputs", "outputs"):
        if not manifest.get(section):
            errors.append(f"Empty {section} inventory")
        for relative, expected in manifest.get(section, {}).items():
            try:
                path = checked_path(root, relative)
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
                if actual != expected:
                    errors.append(f"Changed {section}: {relative}")
            except (OSError, ValueError) as exc:
                errors.append(str(exc))
    return errors


def validate_links(root: Path, publication: str = "publication") -> tuple[list[str], int]:
    pages = sorted((root / publication).glob("*/paper.md")) + sorted((root / publication).glob("*/claim_ledger.md"))
    if not pages:
        return ["No rendered Markdown papers found"], 0
    errors, count = [], 0
    for page in pages:
        # Pandoc's exported Markdown uses inline links; original byte copies are
        # explicitly repository-relative source artifacts, not standalone exports.
        for link in re.findall(r"\]\(<?([^\s)>]+)>?\)", page.read_text(encoding="utf-8")):
            parts = urlsplit(link)
            if parts.scheme or parts.netloc:
                continue
            count += 1
            target = (page.parent / unquote(parts.path)).resolve() if parts.path else page
            if not target.is_relative_to(root.resolve()):
                errors.append(f"Escaping local link: {page.name} -> {link}")
            elif not target.is_file():
                errors.append(f"Missing local link: {page.name} -> {link}")
    return errors, count


def validate_selection(ids: list[str], reserved: dict[str, str]) -> list[str]:
    """Identifiers must be unique, increasing from 000 or 001, and leave no gap that the
    catalog does not reserve. A reservation is an omission from this publication array.
    Its string names where that manuscript lives, or why it is omitted."""
    errors = []
    if len(set(ids)) != len(ids) or ids != sorted(ids):
        errors.append("Publication identifiers must be unique and in increasing order")
    for key, where in reserved.items():
        if key in ids:
            errors.append(f"Reserved identifier {key} is also a collection package")
        if not isinstance(where, str) or not where.strip():
            errors.append(f"Reserved identifier {key} must name where the paper is kept")
    top = max((int(value) for value in ids), default=0)
    start = 0 if ids and ids[0] == "000" else 1
    expected = [f"{i:03}" for i in range(start, top + 1)]
    missing = [key for key in expected if key not in ids and key not in reserved]
    if not ids or ids[0] not in {"000", "001"} or missing:
        errors.append("Publication selection must run from 000 or 001 with gaps only at reserved identifiers" + (f": {', '.join(missing)}" if missing else ""))
    return errors


def validate_bundle(root: Path, entry: dict, manifest: dict, publication: str = "publication") -> list[str]:
    number = entry["id"]
    bundle = root / publication / number
    errors = []
    try:
        receipt = json.loads(checked_path(root, f"{publication}/{number}/build_receipt.json").read_text(encoding="utf-8"))
        for path, key in [(entry["source"], "source_sha256"), (entry["ledger"], "ledger_sha256")]:
            relative = path.relative_to(root).as_posix()
            if relative not in manifest["inputs"]:
                errors.append(f"Missing canonical input from manifest: {relative}")
            if hashlib.sha256(path.read_bytes()).hexdigest() != receipt[key]:
                errors.append(f"Bundle {number} does not match canonical {key}")
        exports = [("paper.pdf", "pdf_sha256"), ("paper.tex", "tex_sha256"), ("source.md", "source_sha256"), ("claim_ledger.source.md", "ledger_sha256"), ("paper.md", "markdown_sha256"), ("claim_ledger.md", "ledger_markdown_sha256")]
        for filename, key in exports:
            path = bundle / filename
            relative = path.relative_to(root).as_posix()
            if relative not in manifest["outputs"]:
                errors.append(f"Missing bundle output from manifest: {relative}")
            if hashlib.sha256(path.read_bytes()).hexdigest() != receipt[key]:
                errors.append(f"Stale {number}/{filename}")
        if not (bundle / "paper.pdf").read_bytes().startswith(b"%PDF-"):
            errors.append(f"Invalid PDF signature: {number}")
        errors.extend(validate_placeholders(root, entry, publication))
    except (OSError, KeyError, ValueError) as exc:
        errors.append(f"Missing or invalid {number} publication: {exc}")
    return errors


def validate_placeholders(root: Path, entry: dict, publication: str = "publication") -> list[str]:
    """Catalogued package sources and exports must contain no PLACEHOLDER token."""
    errors = []
    folder = entry["source"].parent
    bundle = root / publication / entry["id"]
    seen: set[Path] = set()
    targets = [folder]
    if bundle.is_dir() and not bundle.is_relative_to(folder):
        targets.append(bundle)
    for base in targets:
        for path in sorted(base.rglob("*")):
            if any(part in {"target", ".lake", "__pycache__", ".pytest_cache"}
                   for part in path.relative_to(base).parts):
                continue
            if not path.is_file() or path in seen:
                continue
            seen.add(path)
            if path.suffix.lower() in {".pdf", ".zip", ".png", ".jpg", ".jpeg", ".pyc"}:
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                if "PLACEHOLDER" in content:
                    rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else path.name
                    errors.append(f"PLACEHOLDER token found in {rel}")
            except OSError as exc:
                errors.append(f"Cannot read {path}: {exc}")
    return errors


def main() -> int:
    from build_publications import publications

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author-review", action="store_true", help="verify the separate harness author-review catalog")
    args = parser.parse_args()
    publication = "publication/author_review_2026_10_23" if args.author_review else "publication"
    root = Path(__file__).resolve().parents[1]
    errors = validate_manifest(root, publication)
    link_errors, count = validate_links(root, publication)
    errors.extend(link_errors)
    manifest = json.loads(checked_path(root, f"{publication}/manifest.json").read_text(encoding="utf-8"))
    catalog = json.loads(checked_path(root, "publication_catalog.json").read_text(encoding="utf-8"))
    if args.author_review:
        catalog = {**catalog, "publications": catalog["author_review_publications"]}
    entries = publications(catalog)
    ids = [e["id"] for e in entries]
    if args.author_review:
        if not ids or ids != sorted(set(ids)):
            errors.append("Author-review identifiers must be nonempty, unique and increasing")
    else:
        errors.extend(validate_selection(ids, catalog.get("reserved", {})))
    for entry in entries:
        errors.extend(validate_bundle(root, entry, manifest, publication))
    result = {"status": "PASS" if not errors else "FAIL", "collection": publication, "local_links_checked": count, "publications": len(entries), "errors": errors, "AuthorityEffect": "None"}
    print(json.dumps(result, indent=2))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())

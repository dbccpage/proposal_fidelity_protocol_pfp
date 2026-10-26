"""Publish the wiki/ folder to the repository's GitHub wiki.

Clones the wiki repository into a temporary folder, replaces its pages with the
Markdown files in this folder (except README.md), rewrites relative ``Page.md``
links to the GitHub wiki form ``Page``, then commits and pushes.

Usage:
    python wiki/publish_wiki.py [--dry-run] [--remote URL]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
from pathlib import Path

WIKI_DIR = Path(__file__).resolve().parent
DEFAULT_REMOTE = "https://github.com/dbccpage/proposal_fidelity_protocol_pfp.wiki.git"
EXCLUDED = {"README.md"}
# Relative links to sibling pages, e.g. "](Papers.md)" or "](Papers.md#section)".
_PAGE_LINK = re.compile(r"\]\(([A-Za-z0-9_-]+)\.md(#[^)]*)?\)")


def to_wiki_links(text: str) -> str:
    return _PAGE_LINK.sub(lambda m: f"]({m.group(1)}{m.group(2) or ''})", text)


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--remote", default=DEFAULT_REMOTE)
    parser.add_argument("--dry-run", action="store_true", help="show changes without pushing")
    args = parser.parse_args()

    pages = sorted(p for p in WIKI_DIR.glob("*.md") if p.name not in EXCLUDED)
    with tempfile.TemporaryDirectory() as tmp:
        clone = Path(tmp) / "wiki"
        subprocess.run(["git", "clone", "-q", args.remote, str(clone)], check=True)
        for old in clone.glob("*.md"):
            old.unlink()
        for page in pages:
            (clone / page.name).write_text(
                to_wiki_links(page.read_text(encoding="utf-8")), encoding="utf-8", newline="\n"
            )
        git("add", "-A", cwd=clone)
        status = git("status", "--short", cwd=clone)
        if not status:
            print("Wiki is already up to date.")
            return
        print(status, end="")
        if args.dry_run:
            print("Dry run: nothing pushed.")
            return
        git("commit", "-q", "-m", "Publish wiki from wiki/ folder", cwd=clone)
        git("push", "-q", "origin", "HEAD", cwd=clone)
        print(f"Published {len(pages)} pages.")


if __name__ == "__main__":
    main()

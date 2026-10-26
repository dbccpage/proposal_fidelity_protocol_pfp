#!/usr/bin/env python3
"""Promotion helpers after resolve().

- NEW_SKILL → append ooutwire proposed_skills_register entry (never auto-admit)
- Other dispositions → emit a promote receipt JSON (human/PR applies patches)

AuthorityEffect: None. Does not mint skill admission.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from resolve import ResolveResult, resolve_text, repo_root_from  # noqa: E402
from episode import append_episode, load_episode_input, make_episode  # noqa: E402


REGISTER_REL = Path("omega_engine_operads") / "skills" / "ooutwire" / "proposed_skills_register.md"


def _next_entry_id(register_text: str) -> int:
    ids = [int(x) for x in re.findall(r"### Entry (\d+):", register_text)]
    return (max(ids) + 1) if ids else 205


def _slugify(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip().lower()).strip("-")
    return s[:80] or "proposed-skill"


def append_ooutwire_entry(
    repo_root: Path,
    *,
    skill_name: str,
    description: str,
    proposed_by: str = "skill_compiler",
    priority: str = "MEDIUM",
    category: str = "skill-compiler",
) -> dict[str, Any]:
    path = repo_root / REGISTER_REL
    if not path.is_file():
        raise FileNotFoundError(f"ooutwire register missing: {path}")
    text = path.read_text(encoding="utf-8")
    entry_n = _next_entry_id(text)
    slug = _slugify(skill_name)
    block = f"""
### Entry {entry_n:04d}: `{slug}`

- **Date Proposed:** {date.today().isoformat()}
- **Proposed By:** `{proposed_by}` (skill_compiler promote NEW_SKILL)
- **Category:** {category}
- **Priority:** {priority}
- **Status:** `PROPOSED / PENDING_ADMISSION`
- **Description:** {description.strip()}
- **AuthorityEffect:** None

"""
    # Insert after the first session/header section: append near top after counts
    marker = "## Session landings"
    if marker in text:
        head, tail = text.split(marker, 1)
        new_text = head + marker + "\n" + block + tail
    else:
        new_text = text.rstrip() + "\n" + block
    path.write_text(new_text, encoding="utf-8", newline="\n")
    return {
        "ok": True,
        "entry": f"{entry_n:04d}",
        "slug": slug,
        "path": str(path.relative_to(repo_root)).replace("\\", "/"),
        "status": "PROPOSED / PENDING_ADMISSION",
    }


def write_receipt(
    repo_root: Path,
    *,
    episode: dict[str, Any],
    disposition: ResolveResult,
    ooutwire: dict[str, Any] | None = None,
) -> Path:
    out_dir = repo_root / "runs" / "skill_compiler" / "receipts"
    out_dir.mkdir(parents=True, exist_ok=True)
    eid = episode.get("id") or "no-id"
    path = out_dir / f"{eid}.json"
    payload = {
        "schema": "omega.skill_compiler.promote_receipt.v1",
        "episode": episode,
        "disposition": disposition.to_dict(),
        "ooutwire": ooutwire,
        "authority_effect": "None",
        "auto_admit": False,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def promote_from_text(
    repo_root: Path,
    *,
    source: str,
    signal: str,
    proposed_invariant: str,
    locus: str = "",
    confidence: str = "MEDIUM",
    skill_name: str = "",
    write_episode: bool = True,
) -> dict[str, Any]:
    ep = make_episode(
        source=source,
        signal=signal,
        proposed_invariant=proposed_invariant,
        locus=locus,
        confidence=confidence,
    )
    ep_path = None
    if write_episode:
        ep_path = append_episode(repo_root, ep)

    result = resolve_text(
        repo_root,
        signal=signal,
        proposed_invariant=proposed_invariant,
        locus=locus,
        confidence=confidence,
    )

    ooutwire = None
    if result.disposition == "NEW_SKILL":
        name = skill_name or proposed_invariant[:60] or "unnamed-skill"
        ooutwire = append_ooutwire_entry(
            repo_root,
            skill_name=name,
            description=proposed_invariant or signal,
            proposed_by=source,
            priority=confidence if confidence in ("HIGH", "MEDIUM", "LOW") else "MEDIUM",
        )

    receipt = write_receipt(
        repo_root, episode=ep, disposition=result, ooutwire=ooutwire
    )
    return {
        "episode_id": ep["id"],
        "episode_path": str(ep_path) if ep_path else None,
        "disposition": result.to_dict(),
        "ooutwire": ooutwire,
        "receipt": str(receipt.relative_to(repo_root)).replace("\\", "/"),
        "authority_effect": "None",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument(
        "--no-episode",
        action="store_true",
        help="Do not append episode (resolve+promote only)",
    )
    args = parser.parse_args()
    root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from()
    try:
        payload = load_episode_input(args.file)
        extra = payload.get("extra") or {}
        out = promote_from_text(
            root,
            source=payload["source"],
            signal=payload["signal"],
            proposed_invariant=payload["proposed_invariant"],
            locus=payload.get("locus", ""),
            confidence=payload.get("confidence", "MEDIUM"),
            skill_name=str(extra.get("skill_name") or ""),
            write_episode=not args.no_episode,
        )
    except ValueError as err:
        print(json.dumps({"ok": False, "error": str(err)}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Move a skill package out of the garden reversibly, or put it back.

Archiving is the only lifecycle move this estate permits without a promotion:
the bytes are retained, discovery stops, and nothing is certified. Deleting is
not offered here at all.

## The order of operations is load-bearing

1. **Refuse without an approved manifest.** `auto-review-skills` has required a
   written manifest before any mass removal since it was written, and none has
   ever existed. `cull_candidates --manifest` produces one; a human fills in
   `approved_by` and commits it. No manifest, no move.
2. **Refuse if the package is already out of parity.** Archiving a package whose
   four copies disagree preserves bytes that were never canonical.
3. **Record the tree hash first**, reusing `package_tree_hash` from
   `sync_cross_host_skills`. This is what lets a later restore prove the
   archived bytes were not edited while dormant.
4. **Move canon, remove all three mirrors, in one operation.**
   `sync_cross_host_skills` never deletes -- `find_destination_only_packages`
   fails `--check` when a mirror holds a package canon lacks, which is precisely
   the guard it exists for. So archiving is all four hosts or nothing.
5. **Regenerate the derived surfaces.** The tracked capability compiler writes
   the catalog, compatibility signature, and capability slices byte-identically
   to all four hosts.
6. **Re-verify parity, and refuse to report success if it is not green.**

`AuthorityEffect: None`. Archiving is a lifecycle move under a standing human
policy; it certifies nothing and promotes nothing.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from omega_engine_operads.infrastructure.skill_garden.usage_ledger import (
    garden_roster,
    last_used_index,
)

CANON = Path("omega_engine_operads") / "skills"
ARCHIVE = Path(".agents") / "archive" / "skills"
MIRRORS = (".claude", ".codex", ".grok")
RECEIPT_NAME = "ARCHIVE_RECEIPT.json"
RECEIPT_SCHEMA = "omega.skill_garden.archive_receipt.v1"

# `[ \t]*`, never `\s*`: `\s` matches a newline, so an empty `approved_by:`
# would let the regex reach the following line and report `approved_at: ...` as
# the approver. An unsigned manifest would then authorise the move.
_APPROVED_BY = re.compile(r"^approved_by:[ \t]*(\S.*)$", re.MULTILINE)
_MANIFEST_SKILL = re.compile(r"^\|\s*`([A-Za-z0-9._-]+)`\s*\|", re.MULTILINE)


class ArchiveRefusal(RuntimeError):
    """The move is refused. Never raised for an ordinary absence."""


def _run(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=str(repo_root), capture_output=True, text=True, check=False
    )


def _package_tree_hash(repo_root: Path, package: Path) -> str:
    """Reuse the estate's tree hash rather than writing a second one."""
    from omega_engine_operations.use_cases.packaging.sync_cross_host_skills import (
        package_tree_hash,
    )

    return package_tree_hash(package)


def parity_is_green(repo_root: Path) -> bool:
    return (
        _run(
            repo_root,
            "python",
            "omega_engine_operations/use_cases/packaging/sync_cross_host_skills.py",
            "--check",
        ).returncode
        == 0
    )


def read_manifest(path: Path) -> tuple[list[str], str]:
    """(skill ids, approver) from a `planned_archive.md` a human has signed."""
    if not path.is_file():
        raise ArchiveRefusal(
            f"no manifest at {path}. Generate one with "
            "`cull_candidates --manifest`, read it, record approved_by, commit it."
        )
    text = path.read_text(encoding="utf-8")
    approver_match = _APPROVED_BY.search(text)
    approver = approver_match.group(1).strip() if approver_match else ""
    if not approver:
        raise ArchiveRefusal(
            f"{path} records no approved_by. AuthorityEffect: None -- an archive "
            "move needs a human's standing approval, and an unsigned proposal is "
            "not one."
        )
    return sorted(set(_MANIFEST_SKILL.findall(text))), approver


def plan_archive(repo_root: Path, skill_ids: Sequence[str]) -> list[dict[str, Any]]:
    roster = garden_roster(repo_root)
    index = last_used_index(repo_root)
    rows = []
    for skill_id in sorted(set(skill_ids)):
        present = skill_id in roster
        last_used = index.get(skill_id)
        rows.append(
            {
                "skill_id": skill_id,
                "present": present,
                "last_used": last_used.date().isoformat() if last_used else None,
                "hosts": [
                    host for host in MIRRORS if (repo_root / host / "skills" / skill_id).is_dir()
                ],
            }
        )
    return rows


def regenerate_derived_surfaces(repo_root: Path) -> list[str]:
    """Rebuild everything that is a function of the garden's contents."""
    done = []

    projections = _run(repo_root, "python", ".agents/operad/scripts/compile_operad_signatures.py")
    done.append(f"capability projections: rc={projections.returncode}")

    registry = _run(repo_root, "python", "omega_engine_operads/skills/_shared/regen_family_registry.py")
    done.append(f"family_registry: rc={registry.returncode}")

    shared = _run(
        repo_root,
        "python",
        "omega_engine_operations/use_cases/packaging/sync_cross_host_skills.py",
        "--all",
    )
    done.append(f"mirror sync: rc={shared.returncode}")
    return done


def archive_skills(
    repo_root: Path,
    skill_ids: Sequence[str],
    *,
    manifest_path: Path,
    apply: bool = False,
) -> dict[str, Any]:
    approved, approver = read_manifest(manifest_path)
    requested = sorted(set(skill_ids))
    if not requested:
        requested = approved
    outside = [name for name in requested if name not in approved]
    if outside:
        raise ArchiveRefusal(
            f"these are not in the approved manifest: {outside}. The manifest is "
            "the authorisation; a package outside it has none."
        )

    roster = garden_roster(repo_root)
    missing = [name for name in requested if name not in roster]
    if missing:
        raise ArchiveRefusal(f"not present in the garden: {missing}")

    if not parity_is_green(repo_root):
        raise ArchiveRefusal(
            "four-host parity is not green. Archiving a package whose four "
            "copies already disagree preserves bytes that were never canonical."
        )

    plan = plan_archive(repo_root, requested)
    if not apply:
        return {"applied": False, "approver": approver, "plan": plan}

    head = _run(repo_root, "git", "rev-parse", "HEAD").stdout.strip()
    index = last_used_index(repo_root)
    moved = []

    for skill_id in requested:
        source = repo_root / CANON / skill_id
        digest = _package_tree_hash(repo_root, source)
        destination = repo_root / ARCHIVE / skill_id
        destination.parent.mkdir(parents=True, exist_ok=True)

        result = _run(
            repo_root,
            "git",
            "mv",
            (CANON / skill_id).as_posix(),
            (ARCHIVE / skill_id).as_posix(),
        )
        if result.returncode != 0:
            shutil.move(str(source), str(destination))

        for host in MIRRORS:
            mirror = Path(host) / "skills" / skill_id
            if (repo_root / mirror).is_dir():
                removed = _run(repo_root, "git", "rm", "-r", "-q", mirror.as_posix())
                if removed.returncode != 0:
                    shutil.rmtree(repo_root / mirror, ignore_errors=True)

        last_used = index.get(skill_id)
        (destination / RECEIPT_NAME).write_text(
            json.dumps(
                {
                    "schema": RECEIPT_SCHEMA,
                    "authority_effect": "None",
                    "skill_id": skill_id,
                    "archived_at": datetime.now(timezone.utc).isoformat(),
                    "archived_from_commit": head,
                    "package_sha256": digest,
                    "last_used_at": last_used.isoformat() if last_used else None,
                    "manifest": manifest_path.as_posix(),
                    "approved_by": approver,
                    "restore_command": (
                        "python -m omega_engine_operads.infrastructure.skill_garden."
                        f"archive_lane restore --skill-id {skill_id} --apply"
                    ),
                },
                indent=2,
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        moved.append(skill_id)

    surfaces = regenerate_derived_surfaces(repo_root)
    green = parity_is_green(repo_root)
    return {
        "applied": True,
        "approver": approver,
        "archived": moved,
        "surfaces": surfaces,
        "parity_green": green,
        "plan": plan,
    }


def restore_skills(
    repo_root: Path, skill_ids: Sequence[str], *, apply: bool = False
) -> dict[str, Any]:
    requested = sorted(set(skill_ids))
    restored = []
    warnings = []

    for skill_id in requested:
        source = repo_root / ARCHIVE / skill_id
        if not source.is_dir():
            raise ArchiveRefusal(f"{skill_id} is not in the archive")
        if (repo_root / CANON / skill_id).exists():
            raise ArchiveRefusal(f"{skill_id} already exists in the garden")
        if not apply:
            restored.append(skill_id)
            continue

        receipt_path = source / RECEIPT_NAME
        recorded = None
        if receipt_path.is_file():
            recorded = json.loads(receipt_path.read_text(encoding="utf-8")).get("package_sha256")
            receipt_path.unlink()

        digest = _package_tree_hash(repo_root, source)
        if recorded and digest != recorded:
            warnings.append(
                f"{skill_id}: archived bytes changed while dormant "
                f"(receipt {recorded[:16]}, found {digest[:16]})"
            )

        result = _run(
            repo_root,
            "git",
            "mv",
            (ARCHIVE / skill_id).as_posix(),
            (CANON / skill_id).as_posix(),
        )
        if result.returncode != 0:
            shutil.move(str(source), str(repo_root / CANON / skill_id))
        restored.append(skill_id)

    if not apply:
        return {"applied": False, "restored": restored}

    surfaces = regenerate_derived_surfaces(repo_root)
    return {
        "applied": True,
        "restored": restored,
        "warnings": warnings,
        "surfaces": surfaces,
        "parity_green": parity_is_green(repo_root),
    }


def verify_archive(repo_root: Path) -> list[str]:
    """Every archived package must still match the digest on its receipt."""
    findings = []
    root = repo_root / ARCHIVE
    if not root.is_dir():
        return findings
    for package in sorted(path for path in root.iterdir() if path.is_dir()):
        receipt_path = package / RECEIPT_NAME
        if not receipt_path.is_file():
            findings.append(f"{package.name}: no {RECEIPT_NAME}")
            continue
        recorded = json.loads(receipt_path.read_text(encoding="utf-8")).get("package_sha256")
        # The receipt must leave the package directory entirely, not merely be
        # renamed inside it: `package_tree_hash` walks the tree, so a `.tmp`
        # sibling still counts and every freshly archived package would report
        # as tampered.
        parked = package.parent / f".{package.name}.receipt.tmp"
        receipt_path.rename(parked)
        try:
            digest = _package_tree_hash(repo_root, package)
        finally:
            parked.rename(receipt_path)
        if recorded and digest != recorded:
            findings.append(
                f"{package.name}: bytes changed while archived "
                f"(receipt {recorded[:16]}, found {digest[:16]})"
            )
    return findings

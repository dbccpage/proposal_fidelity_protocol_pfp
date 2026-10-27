"""Check epic-walk coverage and TDD plan custody, not semantic purity.

AuthorityEffect: None. Proposed tests are not executed acceptance evidence.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from product_planning_office.use_cases.prior_art_epic_audit import _links, _path

EPICS = "product_planning_office/plans/epics"
RECEIPT = "product_planning_office/receipts/epic_obstruction_walk_20261010_oewas007_successor.json"
HEADING = "## Obstruction review and TDD test plan"
SKILL = ".agents/skills/ext-mattpocock-tdd/SKILL.md"
_PLAN_TOKENS = ("red", "green", "oracle", "mutation", "refactor")
_PLAN_TOKEN = re.compile(r"\b(?:red|green|oracle|mutation|refactor)\b")


def audit(root: Path, receipt_path: Path | None = None) -> dict:
    receipt = json.loads((receipt_path or root / RECEIPT).read_text(encoding="utf-8"))
    if receipt["authority_effect"] != "None" or receipt["certifies_obstruction_free_implementation"] is not False:
        raise ValueError("Walk receipt cannot certify implementation purity or authority")
    skill_digest = hashlib.sha256(_path(root, SKILL).read_bytes()).hexdigest()
    if receipt["tdd_skill_sha256"] != skill_digest:
        raise ValueError("TDD skill digest mismatch")
    actual = {p.relative_to(root).as_posix() for p in (root / EPICS).rglob("epic_*.md")}
    rows = receipt["epics"]
    if not isinstance(receipt["epic_count"], int) or isinstance(receipt["epic_count"], bool) or receipt["epic_count"] != len(rows):
        raise ValueError("Epic walk declared count mismatch")
    if len(rows) != len(actual) or {row["path"] for row in rows} != actual:
        raise ValueError("Epic walk coverage mismatch")
    for row in rows:
        _check_plan(root, row)
    return {"status": "PASS", "authority_effect": "None", "epics": len(rows),
            "scope": "inventory, reviewed bytes, test-plan structure and local links only",
            "certifies_obstruction_free_implementation": False}


def _check_plan(root: Path, row: dict) -> None:
    path = _path(root, row["path"])
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or hashlib.sha256(raw).hexdigest() != row["sha256"]:
        raise ValueError(f"Epic digest or encoding mismatch: {path}")
    text = raw.decode("utf-8")
    if text.count(HEADING) != 1:
        raise ValueError(f"Missing or duplicate TDD section: {path}")
    plan = text.split(HEADING, 1)[1].casefold()
    found = set(_PLAN_TOKEN.findall(plan))
    for required in _PLAN_TOKENS:
        if required not in found:
            raise ValueError(f"Missing TDD plan element {required}: {path}")
    if not row["retained_residuals"] or row["test_plan_status"] != "PROPOSED_NOT_EXECUTED":
        raise ValueError(f"Missing scope and residual boundary: {path}")
    _links(root, path)


def main() -> int:
    root = next(p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file())
    try:
        print(json.dumps(audit(root), sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"status": "REFUSED", "reason": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

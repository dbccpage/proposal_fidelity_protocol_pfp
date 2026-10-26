#!/usr/bin/env python3
"""Residual honesty gate (Phase 3 compatibility layer).

Rules:
1. Legacy and current scalar rows are diagnostic observations only. They cannot
   support ``residual_effect=contractive``, equivalence, or promotion.
2. operad_signature residual_effect=contractive therefore requires a future
   independently verified certificate source, which this module does not mint.
3. Live SKILL.md frontmatter operad_residual: contractive must either:
   - match a signature op backed by that future certificate source, or
   - be reported as unsupported.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from evidence_observations import (
    ResidualObservation,
    ResidualObservationError,
    classify_residual_rows,
)

RESIDUAL_RE = re.compile(
    r"^operad_residual:\s*[\"']?(contractive|exact|unknown)[\"']?\s*$",
    re.I | re.M,
)

# Exclude proposal/archive debris from residual frontmatter scan.
SKIP_DIR_NAMES = frozenset(
    {
        "_archived",
        "_archive",
        "archive",
        "ooutwire",
        "quarantine",
        "__pycache__",
        ".git",
        "node_modules",
    }
)


def repo_root_from(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / ".git").exists() and (candidate / ".agents").is_dir():
            return candidate
    return Path.cwd().resolve()


def load_residual_observations(trace_path: Path) -> list[ResidualObservation]:
    if not trace_path.is_file():
        return []
    rows = json.loads(trace_path.read_text(encoding="utf-8"))
    return classify_residual_rows(rows)


def load_contractive_runs(trace_path: Path) -> dict[str, set[str]]:
    """Compatibility API returning certified runs, of which there are none.

    Callers that need diagnostics should use ``load_residual_observations``.
    Counting decreasing caller-supplied scalars must never upgrade them.
    """

    load_residual_observations(trace_path)
    return {}


def check_signature(
    sig_path: Path, contractive_runs: dict[str, set[str]]
) -> list[str]:
    errs: list[str] = []
    if not sig_path.is_file():
        return [f"missing signature {sig_path}"]
    sig = json.loads(sig_path.read_text(encoding="utf-8"))
    for op in sig.get("operations") or []:
        reff = str(op.get("residual_effect") or "unknown").lower()
        if reff != "contractive":
            continue
        sid = str(op.get("skill_id") or "")
        runs = contractive_runs.get(sid) or set()
        if not runs:
            errs.append(
                f"signature op '{sid}' claims residual_effect=contractive "
                "but no independently verified contractivity certificate exists; "
                "residual observations cannot discharge this claim"
            )
    return errs


def frontmatter_residual(text: str) -> str | None:
    """Parse residual from YAML frontmatter block when present, else head scan."""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            block = parts[1]
            m = RESIDUAL_RE.search(block)
            if m:
                return m.group(1).lower()
            return None
    m = RESIDUAL_RE.search(text[:1500])
    if not m:
        return None
    return m.group(1).lower()


def iter_admitted_skill_mds(skills_root: Path) -> list[Path]:
    """Recursively find SKILL.md under admitted packages; skip archive/ooutwire."""
    if not skills_root.is_dir():
        return []
    out: list[Path] = []
    for skill_md in skills_root.rglob("SKILL.md"):
        try:
            rel_parts = skill_md.relative_to(skills_root).parts
        except ValueError:
            continue
        if any(p in SKIP_DIR_NAMES or p.startswith(".") for p in rel_parts[:-1]):
            continue
        out.append(skill_md)
    return sorted(out)


def check_skill_frontmatter(
    skills_root: Path,
    contractive_runs: dict[str, set[str]],
    *,
    signature_contractive: set[str],
) -> list[str]:
    errs: list[str] = []
    if not skills_root.is_dir():
        return [f"missing skills root {skills_root}"]
    for skill_md in iter_admitted_skill_mds(skills_root):
        text = skill_md.read_text(encoding="utf-8", errors="ignore")
        res = frontmatter_residual(text)
        if res != "contractive":
            continue
        sid = skill_md.parent.name
        runs = contractive_runs.get(sid) or set()
        if runs:
            continue
        if sid in signature_contractive and contractive_runs.get(sid):
            continue
        try:
            rel = skill_md.relative_to(skills_root).as_posix()
        except ValueError:
            rel = str(skill_md)
        errs.append(
            f"skill '{sid}' ({rel}) frontmatter operad_residual=contractive "
            "without an independently verified contractivity certificate; "
            "residual observations cannot discharge this claim"
        )
    return errs


def run_checks(repo_root: Path) -> dict[str, Any]:
    operad = repo_root / ".agents" / "operad"
    if not operad.is_dir():
        alt_operad = repo_root / "omega_engine_operads" / "skill_operad"
        if alt_operad.is_dir():
            operad = alt_operad
    sig_path = (
        operad / "json" / "operad_signature.json"
        if (operad / "json" / "operad_signature.json").is_file()
        else operad / "operad_signature.json"
    )
    trace_path = (
        operad / "json" / "evidence_trace.json"
        if (operad / "json" / "evidence_trace.json").is_file()
        else operad / "evidence_trace.json"
    )
    skills_root = repo_root / "omega_engine_operads" / "skills"
    try:
        observations = load_residual_observations(trace_path)
    except (OSError, UnicodeError, json.JSONDecodeError, ResidualObservationError) as exc:
        observations = []
        observation_errors = [f"cannot classify residual observations: {exc}"]
    else:
        observation_errors = []
    runs: dict[str, set[str]] = {}
    sig_errs = check_signature(sig_path, runs)
    sig = (
        json.loads(sig_path.read_text(encoding="utf-8"))
        if sig_path.is_file()
        else {"operations": []}
    )
    sig_contractive = {
        str(op.get("skill_id"))
        for op in sig.get("operations") or []
        if str(op.get("residual_effect") or "").lower() == "contractive"
    }
    fm_errs = check_skill_frontmatter(
        skills_root, runs, signature_contractive=sig_contractive
    )
    all_errs = observation_errors + sig_errs + fm_errs
    legacy = [o for o in observations if o.classification == "LegacyResidualObservation"]
    recorded = [o for o in observations if o.classification == "RecordedResidualObservation"]
    return {
        "schema": "omega.operad.residual_honesty.v1",
        "errors": all_errs,
        "error_count": len(all_errs),
        "contractive_skills_with_evidence": sorted(
            k for k, v in runs.items() if v
        ),
        "diagnostic_observations": len(observations),
        "legacy_residual_observations": len(legacy),
        "recorded_residual_observations": len(recorded),
        "observation_claim_effect": {
            "contractivity": False,
            "equivalence": False,
            "promotion": False,
        },
        "authority_effect": "None",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve() if args.repo_root else repo_root_from()
    receipt = run_checks(root)
    if args.json:
        print(json.dumps(receipt, indent=2, ensure_ascii=False))
    else:
        print("=== RESIDUAL HONESTY (Phase 3) ===")
        if receipt["errors"]:
            for e in receipt["errors"]:
                print(f"  [FAIL] {e}")
            print(f"\nFAIL: {receipt['error_count']} residual honesty error(s).")
        else:
            print(
                "PASS: no unbacked contractive claims. Residual observations "
                "remain diagnostic only."
            )
    return 1 if receipt["error_count"] else 0


if __name__ == "__main__":
    sys.exit(main())

"""Scratchpad for incremental paper/program extension under operator request.

--increment no  (default): no pad, plan-only.
--increment yes: open pad under docs/scratchpad/increment_<id>/ with prose|py|lean
lanes; adversarial host checks on py; merge never auto (authorizer only).

AuthorityEffect: None. Pad is not the public object (export skips scratchpad).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from omega_engine_woland.domain.research.paper_run_graph import (
    AUTHORITY_EFFECT,
    PaperRunGraphError,
    Role,
    TransitionEvent,
    validate_transition,
    validate_transition_or_raise,
)
from omega_engine_woland.use_cases.research.paper_plan import plan_paper

PAD_SCHEMA = "urn:omega:rip:increment_pad:v0.1"
LANES = frozenset({"prose", "py", "lean"})


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug_residual(residual_id: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "_", (residual_id or "").strip())
    return s[:80] or "R-UNSPEC"


@dataclass
class IncrementPad:
    """On-disk scratch laboratory for one residual-scoped increment attempt."""

    pad_id: str
    paper_root: str
    residual_id: str
    carrier_hash: str
    pad_root: str
    lanes: list[str]
    rounds_budget: int = 1
    merge_policy: str = "never"  # never | propose (still needs human ACCEPT)
    adversary_status: str = "unchecked"  # unchecked | fail | pass | skipped
    adversary_notes: list[str] = field(default_factory=list)
    authority_effect: str = AUTHORITY_EFFECT
    schema_version: str = PAD_SCHEMA
    created_at_utc: str = field(default_factory=_utc_now)
    increment: str = "yes"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["public_object"] = False
        d["auto_merge"] = False
        d["precise_claim"] = (
            "Increment pad holds candidate prose/py/lean only. "
            "Legacy merge/apply is quarantined until P3-07D/P3-07A. "
            "AuthorityEffect None."
        )
        return d

    def manifest_path(self) -> Path:
        return Path(self.pad_root) / "pad_manifest.json"

    def write_manifest(self) -> Path:
        p = self.manifest_path()
        p.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return p


def _parse_lanes(lanes: Sequence[str] | str | None) -> list[str]:
    if lanes is None:
        return ["prose", "py"]
    if isinstance(lanes, str):
        parts = [x.strip().lower() for x in lanes.split(",") if x.strip()]
    else:
        parts = [str(x).strip().lower() for x in lanes if str(x).strip()]
    bad = [p for p in parts if p not in LANES]
    if bad:
        raise PaperRunGraphError(f"unknown lanes {bad}; allowed={sorted(LANES)}")
    if not parts:
        raise PaperRunGraphError("at least one lane required when --increment yes")
    # stable unique
    out: list[str] = []
    for p in parts:
        if p not in out:
            out.append(p)
    return out


def open_increment_pad(
    paper_root: Path | str,
    residual_id: str,
    *,
    lanes: Sequence[str] | str | None = None,
    rounds: int = 1,
    seed_py_adversary: bool = True,
) -> IncrementPad:
    """
    Create scratchpad under paper docs/scratchpad/increment_<id>/.
    Does not mutate paper spine or src/. seed_py_adversary writes a failing test
    the operator/proposer must make pass (tangible adversarial loop).
    """
    root = Path(paper_root).resolve()
    rid = (residual_id or "").strip()
    if not rid:
        raise PaperRunGraphError("--residual is required when --increment yes")
    if not root.is_dir():
        raise PaperRunGraphError(f"not a directory: {root}")

    lane_list = _parse_lanes(lanes)
    plan = plan_paper(root, rounds=rounds)
    carrier = plan.graph.carrier_hash
    pad_id = f"inc_{_slug_residual(rid)}_{uuid.uuid4().hex[:8]}"
    pad_root = root / "docs" / "scratchpad" / pad_id
    if pad_root.exists():
        raise PaperRunGraphError(f"pad already exists: {pad_root}")

    # Layout
    layout = tuple(dict.fromkeys(("prose", *lane_list, "evidence", "adversary")))
    for sub in layout:
        (pad_root / sub).mkdir(parents=True, exist_ok=True)

    (pad_root / "prose" / "README.md").write_text(
        f"# Increment scratch — residual `{rid}`\n\n"
        f"**AuthorityEffect:** None. Candidates only. Not public object.\n\n"
        f"Carrier hash at open: `{carrier}`\n\n"
        f"Lanes: {', '.join(lane_list)}\n\n"
        f"Write proposals only under the selected prose/py/lean lanes. "
        f"The compatibility merge rail remains refusal-only.\n",
        encoding="utf-8",
    )
    (pad_root / "prose" / "candidate_note.md").write_text(
        f"<!-- proposer only: draft extension for residual {rid} -->\n\n"
        f"## Proposed extension (draft)\n\n"
        f"_Replace this with residual-honest prose. Do not claim PROVEN._\n",
        encoding="utf-8",
    )

    if "py" in lane_list and seed_py_adversary:
        # Tangible: a test that FAILS until the candidate implements the obligation.
        py_mod = pad_root / "py" / "candidate.py"
        py_test = pad_root / "py" / "test_candidate_adversary.py"
        py_mod.write_text(
            '"""Proposer fills this. Adversary requires extend_marker() == residual id."""\n'
            f"RESIDUAL_ID = {rid!r}\n\n"
            "def extend_marker() -> str:\n"
            '    """Must return the residual id when the increment is real."""\n'
            '    return ""  # FAIL until proposer sets this to RESIDUAL_ID\n',
            encoding="utf-8",
        )
        py_test.write_text(
            "from candidate import RESIDUAL_ID, extend_marker\n\n"
            "def test_extend_marker_binds_residual():\n"
            "    assert extend_marker() == RESIDUAL_ID\n",
            encoding="utf-8",
        )

    residual_notes: list[str] = [
        "Pad opened. Public zip must not include docs/scratchpad.",
        "merge_policy=never; P3-07D/P3-07A are required for any apply.",
    ]
    if "lean" in lane_list:
        (pad_root / "lean" / "README.md").write_text(
            "# Lean lane (candidate only)\n\n"
            "**RESIDUAL R-LANE-LEAN:** host `lake build` adversary is NOT wired "
            "(sprint-oe-paper-007-0). LEAN_TOY stays labeled. Do not claim theorem discharge.\n"
            "AuthorityEffect None.\n",
            encoding="utf-8",
        )
        residual_notes.append(
            "RESIDUAL R-LANE-LEAN: lake adversary not implemented; lane is labeled residual only."
        )

    pad = IncrementPad(
        pad_id=pad_id,
        paper_root=str(root),
        residual_id=rid,
        carrier_hash=carrier,
        pad_root=str(pad_root),
        lanes=lane_list,
        rounds_budget=max(1, int(rounds)),
        adversary_status="unchecked",
        adversary_notes=residual_notes,
    )
    pad.write_manifest()
    (pad_root / "evidence" / "open_plan.json").write_text(
        json.dumps(plan.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return pad


def load_pad(pad_root: Path | str) -> IncrementPad:
    root = Path(pad_root).resolve()
    man = root / "pad_manifest.json"
    if not man.is_file():
        raise PaperRunGraphError(f"missing pad_manifest.json under {root}")
    data = json.loads(man.read_text(encoding="utf-8"))
    lane_list = _parse_lanes(data.get("lanes"))
    return IncrementPad(
        pad_id=str(data["pad_id"]),
        paper_root=str(data["paper_root"]),
        residual_id=str(data["residual_id"]),
        carrier_hash=str(data["carrier_hash"]),
        pad_root=str(data.get("pad_root") or root),
        lanes=lane_list,
        rounds_budget=int(data.get("rounds_budget") or 1),
        merge_policy=str(data.get("merge_policy") or "never"),
        adversary_status=str(data.get("adversary_status") or "unchecked"),
        adversary_notes=list(data.get("adversary_notes") or []),
        authority_effect=str(data.get("authority_effect") or AUTHORITY_EFFECT),
        schema_version=str(data.get("schema_version") or PAD_SCHEMA),
        created_at_utc=str(data.get("created_at_utc") or _utc_now()),
        increment=str(data.get("increment") or "yes"),
    )


def run_py_adversary(pad: IncrementPad) -> IncrementPad:
    """
    Host evaluator: run pytest on pad/py if present.
    Role=evaluator; does not mutate candidates.
    """
    validate_transition(
        TransitionEvent(
            role=Role.EVALUATOR.value,
            event_type="measurement",
            carrier_hash=pad.carrier_hash,
        )
    )
    py_dir = Path(pad.pad_root) / "py"
    if not py_dir.is_dir() or "py" not in pad.lanes:
        pad.adversary_status = "skipped"
        pad.adversary_notes.append("py lane not active; adversary skipped")
        pad.write_manifest()
        return pad

    tests = list(py_dir.glob("test_*.py"))
    if not tests:
        pad.adversary_status = "fail"
        pad.adversary_notes.append("no test_*.py under pad/py — refuse PASS")
        pad.write_manifest()
        return pad

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=line", str(py_dir)],
        cwd=str(py_dir),
        capture_output=True,
        text=True,
        timeout=120,
    )
    log = Path(pad.pad_root) / "adversary" / "py_pytest.txt"
    log.write_text(
        f"exit={proc.returncode}\n{proc.stdout}\n{proc.stderr}\n",
        encoding="utf-8",
    )
    if proc.returncode == 0:
        pad.adversary_status = "pass"
        pad.adversary_notes.append("py adversary PASS (pytest green)")
    else:
        pad.adversary_status = "fail"
        pad.adversary_notes.append(
            f"py adversary FAIL (pytest exit {proc.returncode}); see adversary/py_pytest.txt"
        )
    pad.write_manifest()
    return pad


def refuse_merge_unless_ready(
    pad: IncrementPad,
    *,
    authorizer_accept: bool = False,
) -> None:
    """
    Fail-closed merge gate.
    Legacy merge is refusal-only; adversary status remains diagnostic evidence.
    """
    if pad.adversary_status != "pass":
        raise PaperRunGraphError(
            f"merge refused: adversary_status={pad.adversary_status!r} (need pass)"
        )
    del authorizer_accept
    raise PaperRunGraphError(
        "merge refused: legacy boolean authorization is quarantined until P3-07D/P3-07A"
    )


def refuse_proposer_self_pass(pad: IncrementPad) -> None:
    """Proposer cannot stamp adversary pass."""
    with_error = False
    try:
        validate_transition_or_raise(
            TransitionEvent(
                role=Role.PROPOSER.value,
                event_type="candidate_patch",
                carrier_hash=pad.carrier_hash,
                claims_pass=True,
            )
        )
    except PaperRunGraphError:
        with_error = True
    if not with_error:
        raise PaperRunGraphError("expected proposer self-pass to be refused")


def open_or_plan(
    paper_root: Path | str,
    *,
    increment: str = "no",
    residual_id: str = "",
    lanes: Sequence[str] | str | None = None,
    rounds: int = 1,
    run_adversary: bool = True,
    dev_only: bool = False,
) -> dict[str, Any]:
    """
    Unified entry: increment=no → plan only; increment=yes → plan + pad (+ optional py adversary).
    """
    flag = (increment or "no").strip().lower()
    if flag in ("n", "false", "0"):
        flag = "no"
    if flag in ("y", "true", "1"):
        flag = "yes"
    if flag not in ("yes", "no"):
        raise PaperRunGraphError("--increment must be yes|no")

    if flag == "no":
        plan = plan_paper(paper_root, rounds=rounds, dev_only=dev_only)
        return {
            "increment": "no",
            "authority_effect": AUTHORITY_EFFECT,
            "plan": plan.to_dict(),
            "pad": None,
        }

    pad = open_increment_pad(
        paper_root,
        residual_id,
        lanes=lanes,
        rounds=rounds,
        seed_py_adversary=True,
    )
    refuse_proposer_self_pass(pad)
    if run_adversary and "py" in pad.lanes:
        pad = run_py_adversary(pad)
    return {
        "increment": "yes",
        "authority_effect": AUTHORITY_EFFECT,
        "plan": plan_paper(paper_root, rounds=rounds, dev_only=dev_only).to_dict(),
        "pad": pad.to_dict(),
    }

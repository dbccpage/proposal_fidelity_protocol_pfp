"""Claim-queue one-row operator (SCALE-002 S2).

Loads paper docs/claim_queue.yaml (or claim_queue.yaml), selects **one** open
residual per round by priority_asc. AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

AUTHORITY_EFFECT = "None"
SCHEMA_VERSION = "urn:omega:oears:claim_queue:v1"

OPEN_STATUSES = frozenset({"open", "OPEN", "todo", "TODO", "pending", "PENDING"})
CLOSED_STATUSES = frozenset(
    {"closed", "CLOSED", "done", "DONE", "resolved", "RESOLVED", "skip", "SKIP"}
)


from omega_engine_woland.domain.research.protocols import ClaimQueueError


@dataclass(frozen=True)
class ClaimQueueRow:
    id: str
    priority: int = 100
    status: str = "open"
    note: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        if not isinstance(other, ClaimQueueRow):
            return False
        return (
            self.id == other.id
            and self.priority == other.priority
            and self.status == other.status
            and self.note == other.note
            and self.extra == other.extra
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.id,
            self.priority,
            self.status,
            self.note,
        ))

    @property
    def is_open(self) -> bool:
        s = (self.status or "").strip()
        if s in CLOSED_STATUSES:
            return False
        if s in OPEN_STATUSES or not s:
            return True
        # unknown status: treat non-closed as open
        return s.lower() not in {x.lower() for x in CLOSED_STATUSES}

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "id": self.id,
            "priority": self.priority,
            "status": self.status,
            "note": self.note,
            "is_open": self.is_open,
        }
        if self.extra:
            d["extra"] = dict(self.extra)
        return d


@dataclass
class ClaimQueue:
    path: Path
    rows: List[ClaimQueueRow]
    schema_version: str = SCHEMA_VERSION
    authority_effect: str = AUTHORITY_EFFECT

    def open_rows(self) -> List[ClaimQueueRow]:
        return [r for r in self.rows if r.is_open]

    def select_one(
        self,
        *,
        priority_asc: bool = True,
    ) -> Optional[ClaimQueueRow]:
        """Return single next open residual (priority order). None if empty."""
        open_rows = self.open_rows()
        if not open_rows:
            return None
        ordered = sorted(
            open_rows,
            key=lambda r: (r.priority, r.id) if priority_asc else (-r.priority, r.id),
        )
        return ordered[0]

    def to_receipt(
        self,
        selected: Optional[ClaimQueueRow],
        *,
        multi_row_refused: bool = False,
    ) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "path": str(self.path),
            "open_count": len(self.open_rows()),
            "total_count": len(self.rows),
            "selected": selected.to_dict() if selected else None,
            "one_row_per_round": True,
            "multi_row_refused": multi_row_refused,
            "authority_effect": self.authority_effect,
            "claims_global_green": False,
        }


def resolve_claim_queue_path(
    paper_path: Path | str,
    *,
    prefer_scale: bool = False,
) -> Path:
    """Locate claim_queue.yaml under paper package.

    When prefer_scale=True (SCALE-002 S3 pathspec demos), prefer
    docs/scale_claim_queue.yaml so research queues stay untouched.
    """
    root = Path(paper_path)
    if root.is_file():
        root = root.parent
    scale_first = [
        root / "docs" / "scale_claim_queue.yaml",
        root / "docs" / "scale_claim_queue.yml",
    ]
    standard = [
        root / "docs" / "claim_queue.yaml",
        root / "docs" / "claim_queue.yml",
        root / "claim_queue.yaml",
        root / "claim_queue.yml",
    ]
    candidates = (scale_first + standard) if prefer_scale else (standard + scale_first)
    for c in candidates:
        if c.is_file():
            return c
    raise ClaimQueueError(
        f"no claim_queue.yaml under {root} "
        f"(tried docs/claim_queue.yaml, docs/scale_claim_queue.yaml, claim_queue.yaml)"
    )


def _parse_rows(data: Any) -> List[ClaimQueueRow]:
    if not isinstance(data, dict):
        raise ClaimQueueError("claim_queue root must be a mapping")
    # Estate queues (TUFT) use `queue:`; SCALE fixtures use `residuals:`.
    raw_list = data.get("residuals")
    if raw_list is None:
        raw_list = data.get("queue") or data.get("rows") or data.get("items") or []
    if not isinstance(raw_list, list):
        raise ClaimQueueError("residuals/queue must be a list")
    rows: List[ClaimQueueRow] = []
    for i, item in enumerate(raw_list):
        if not isinstance(item, dict):
            raise ClaimQueueError(f"residuals[{i}] must be a mapping")
        rid = str(
            item.get("id") or item.get("residual_id") or item.get("claim_id") or ""
        ).strip()
        if not rid:
            raise ClaimQueueError(f"residuals[{i}] missing id")
        try:
            pri = int(item.get("priority", 100))
        except (TypeError, ValueError) as exc:
            raise ClaimQueueError(f"residuals[{i}] bad priority") from exc
        status = str(item.get("status", "open")).strip() or "open"
        note = str(item.get("note") or item.get("title") or item.get("goal") or "")
        known = {
            "id",
            "residual_id",
            "claim_id",
            "priority",
            "status",
            "note",
            "title",
            "goal",
        }
        extra = {k: v for k, v in item.items() if k not in known}
        rows.append(
            ClaimQueueRow(id=rid, priority=pri, status=status, note=note, extra=extra)
        )
    return rows


def load_claim_queue(path: Path | str) -> ClaimQueue:
    """Load and parse claim queue YAML."""
    if yaml is None:
        raise ClaimQueueError("PyYAML required to load claim_queue.yaml")
    p = Path(path)
    if not p.is_file():
        raise ClaimQueueError(f"claim queue not found: {p}")
    text = p.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if data is None:
        data = {"residuals": []}
    rows = _parse_rows(data)
    schema = str(data.get("schema_version") or SCHEMA_VERSION)
    return ClaimQueue(path=p, rows=rows, schema_version=schema)


def select_one_open_from_paper(
    paper_path: Path | str,
    *,
    priority_asc: bool = True,
    prefer_scale: bool = False,
) -> tuple[ClaimQueue, Optional[ClaimQueueRow]]:
    """Load queue under paper package and select one open row."""
    qpath = resolve_claim_queue_path(paper_path, prefer_scale=prefer_scale)
    queue = load_claim_queue(qpath)
    selected = queue.select_one(priority_asc=priority_asc)
    return queue, selected


def refuse_if_multi_requested(n: int) -> None:
    """Hard law: one row per round — refuse n>1 selection requests."""
    if n > 1:
        raise ClaimQueueError(
            f"one-row-per-round refused: requested {n} residuals "
            "(select_one returns at most 1)"
        )

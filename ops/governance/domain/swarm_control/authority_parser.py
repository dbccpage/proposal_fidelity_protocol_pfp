"""Authority Parser Functions (0 classes).

AuthorityEffect: None.
"""

from __future__ import annotations

from .parse_disposition import ParseDisposition
from .parse_result import ParseResult


def parse_active_stop(text: str) -> ParseResult:
    """Fail-closed parser for documented Active/STOP forms.

    Accepted:
      - Active: yes
      - Active: no
      - STOP
      - STOP: <reason>
    Refused: empty, ambiguous dual declarations without precedence, malformed.
    Precedence: last non-empty STOP wins over Active if both present; duplicate
    Active with conflicting values refuses.
    """
    if text is None or not str(text).strip():
        return ParseResult(ParseDisposition.REFUSED, "MALFORMED_EMPTY")

    lines = [ln.strip() for ln in str(text).splitlines() if ln.strip()]
    actives: list[str] = []
    stops: list[str] = []
    for ln in lines:
        low = ln.lower()
        if low.startswith("active:"):
            val = ln.split(":", 1)[1].strip().lower()
            if val not in {"yes", "no", "true", "false"}:
                return ParseResult(ParseDisposition.REFUSED, "MALFORMED_ACTIVE")
            actives.append("yes" if val in {"yes", "true"} else "no")
        elif low == "stop" or low.startswith("stop:"):
            stops.append(ln)
        else:
            return ParseResult(ParseDisposition.REFUSED, "MALFORMED_UNKNOWN_LINE")

    if stops and actives:
        return ParseResult(ParseDisposition.STOP, None, stops[-1])
    if stops:
        return ParseResult(ParseDisposition.STOP, None, stops[-1])
    if not actives:
        return ParseResult(ParseDisposition.REFUSED, "MALFORMED_EMPTY")
    if len(set(actives)) > 1:
        return ParseResult(ParseDisposition.REFUSED, "AMBIGUOUS_DUPLICATE_ACTIVE")
    return ParseResult(
        ParseDisposition.ACTIVE if actives[-1] == "yes" else ParseDisposition.STOP,
        None,
        actives[-1],
    )

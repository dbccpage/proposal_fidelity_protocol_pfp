"""Map each PFP terminal status onto the routing axis.

The map is data in `infrastructure/yaml/stages/terminal_routing.json`. The Rust
owner is `core_types::routing::PfpTerminal`, whose test reads the same file.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pfp.domain.kernel.result import TerminalStatus

TERMINAL_ROUTING_PATH = Path(__file__).resolve().parent / "yaml" / "stages" / "terminal_routing.json"

ROUTING_TERMINALS = (
    "CheckPassed",
    "RequiresLift",
    "Repair",
    "Refusal",
    "NoRule",
    "BudgetUnknown",
    "Refused",
)


@lru_cache(maxsize=1)
def load_terminal_routing() -> dict[str, str]:
    routing = json.loads(TERMINAL_ROUTING_PATH.read_text(encoding="utf-8"))["routing"]
    unknown = sorted(set(routing.values()) - set(ROUTING_TERMINALS))
    if unknown:
        raise ValueError(f"Unknown routing terminals: {unknown}")
    return dict(routing)


def routing_terminal(status: TerminalStatus | str) -> str:
    """Return the routing terminal for a status given as a member, its value or its name."""
    if isinstance(status, TerminalStatus):
        member = status
    elif status in TerminalStatus.__members__:
        member = TerminalStatus[status]
    else:
        member = TerminalStatus(status)
    return load_terminal_routing()[member.value]

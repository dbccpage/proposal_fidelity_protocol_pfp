"""Historical reach ledger-check. AuthorityEffect: None."""
from operations.domain.level_engine_context import (
    LevelEngineOperationPorts,
    current_context,
)


def main(argv: list[str] | None = None, ports: LevelEngineOperationPorts | None = None) -> int:
    if ports is None:
        raise ValueError("LEVEL_ENGINE_PORTS_REQUIRED")
    return ports.reach_main(["ledger-check", "--workspace", str(current_context().require_repository()), *(argv or [])])

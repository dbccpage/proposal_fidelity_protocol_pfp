"""Public research adapter for the Symbol Game Level Engine runner port.

Terminals describe replay of the supplied finite fixtures, not theorem authority.
AuthorityEffect: None. Rust port pending.
"""
from __future__ import annotations

from operations.domain.level_engine_context import (
    LevelEngineResourcesPort,
    configure_context,
    configure_vendor_import_scope,
)
from pfp.domain.tower.level_engine import LevelEngineOutcome


class ResearchLevelEngineRunner:
    """Run a fixture replay using one explicitly configured research context."""

    def __init__(self, context: LevelEngineResourcesPort) -> None:
        self.context = context

    def run(self, challenge_id: str) -> LevelEngineOutcome:
        configure_context(self.context)
        from pfp.infrastructure.tower_research.level_engine.vendor_loading import (
            vendor_import_scope,
        )

        configure_vendor_import_scope(vendor_import_scope)
        from operations.use_cases.level_engine.research_engine.level import (
            check_expectations,
            run_level,
        )

        result = run_level(challenge_id)
        if result.missing_components:
            terminal = "MISSING_COMPONENTS"
        elif check_expectations(challenge_id, result.verdicts):
            terminal = "FIXTURE_EXPECTATIONS_MISMATCHED"
        else:
            terminal = "FIXTURE_EXPECTATIONS_MATCHED"
        return LevelEngineOutcome(result.challenge_id, terminal, "RESEARCH_FIXTURE_REPLAY")

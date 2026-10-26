"""In-memory persistence DB context for isolated execution and tests."""

from __future__ import annotations

from typing import Any


class InMemoryDbContext:
    """In-memory dictionary store for testing and ephemeral workflows."""

    def __init__(self) -> None:
        self.prompts: dict[str, dict[str, Any]] = {}
        self.receipts: dict[str, dict[str, Any]] = {}
        self.runs: dict[str, dict[str, Any]] = {}
        self.content_artifacts: dict[str, dict[str, Any]] = {}
        self.candidates: dict[str, dict[str, Any]] = {}
        self.patches: dict[str, dict[str, Any]] = {}
        self.gate_receipts: list[dict[str, Any]] = []
        self.claims: dict[str, dict[str, Any]] = {}
        self.intake_bundles: dict[str, dict[str, Any]] = {}
        self.frozen_corpora: dict[str, dict[str, Any]] = {}
        self.policy_scores: list[dict[str, Any]] = []
        self.hypotheses: dict[str, dict[str, Any]] = {}

    def clear(self) -> None:
        self.prompts.clear()
        self.receipts.clear()
        self.runs.clear()
        self.content_artifacts.clear()
        self.candidates.clear()
        self.patches.clear()
        self.gate_receipts.clear()
        self.claims.clear()
        self.intake_bundles.clear()
        self.frozen_corpora.clear()
        self.policy_scores.clear()
        self.hypotheses.clear()

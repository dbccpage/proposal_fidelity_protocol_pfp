# -*- coding: utf-8 -*-
"""protocols.py: Domain ports and interfaces for benchmark simulation and adapters.

Clean Architecture Layer: Domain Protocols (Ports)
AuthorityEffect: None
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Protocol

from omega_engine_operations.domain.benchmarks.models import (
    BenchmarkProblem,
    BenchmarkRunResult,
    BudgetExhaustionRecord,
    LlmAdapterOutput,
)


class SimulationEngineProtocol(Protocol):
    """Abstract port for deterministic compute budget simulation."""

    @property
    def total_budget(self) -> int:
        ...

    @property
    def remaining_budget(self) -> int:
        ...

    @property
    def step_count(self) -> int:
        ...

    def consume_step(self, cost: int, operation: str) -> bool:
        ...

    def consume_tokens(
        self, prompt_tokens: int, completion_tokens: int, operation: str = "llm_completion"
    ) -> bool:
        ...

    @property
    def is_exhausted(self) -> bool:
        ...

    def get_exhaustion_record(self) -> BudgetExhaustionRecord:
        ...


class LlmProviderProtocol(Protocol):
    """Abstract port for raw LLM inference provider (mock, local, or cloud)."""

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Returns dict with keys: raw_text, prompt_tokens, completion_tokens, model."""
        ...


class LlmAdapterProtocol(Protocol):
    """Abstract port for intake boundary adapter adhering to llm_adapter.contract.yaml."""

    def execute_turn(
        self,
        packet_id: str,
        prompt: str,
        candidate_type: str = "CandidateResponse",
        system_prompt: Optional[str] = None,
        schema_ref: str = "urn:omega:schemas:candidate_turn:v1.0.0",
        authority_effect: str = "None",
        **kwargs: Any,
    ) -> LlmAdapterOutput:
        ...


class BenchmarkReasonerProtocol(Protocol):
    """Abstract port for reasoning systems evaluated on the benchmark harness."""

    def solve(
        self,
        problem: BenchmarkProblem,
        compute_budget: int = 100,
        **kwargs: Any,
    ) -> BenchmarkRunResult:
        ...

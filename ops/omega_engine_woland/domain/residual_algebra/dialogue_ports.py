"""Pure dialogue boundary; configuration and transport belong to adapters."""

from typing import Protocol

from omega_engine_operations.domain.rop.result import Refusal, Result


class DialogueProvider(Protocol):
    def generate(self, speaker: str, cue: str, context: str = "") -> Result[str, Refusal]: ...

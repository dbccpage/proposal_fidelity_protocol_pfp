"""Port for generating unique IDs."""

from __future__ import annotations

from abc import ABC, abstractmethod


class IdGeneratorPort(ABC):
    @abstractmethod
    def generate_id(self, prefix: str = "") -> str:
        pass

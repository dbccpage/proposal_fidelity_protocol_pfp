"""UUID-based ID generator implementation of IdGeneratorPort."""

from __future__ import annotations

import uuid
from ...application.ports.id_generator_port import IdGeneratorPort


class UuidIdGenerator(IdGeneratorPort):
    def generate_id(self, prefix: str = "") -> str:
        unique = uuid.uuid4().hex[:12]
        return f"{prefix}_{unique}" if prefix else unique

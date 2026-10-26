"""Typed StructureBench failures shared by domain policy and adapters."""


class StructureBenchError(RuntimeError):
    """A typed refusal naming what the evaluator would not do."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


__all__ = ["StructureBenchError"]

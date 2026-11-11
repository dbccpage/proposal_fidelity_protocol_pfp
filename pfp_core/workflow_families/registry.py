"""Registry of executable workflow families, one module per DAG layer."""
from __future__ import annotations

from importlib import import_module

from .base import WorkflowFamily

LAYER_MODULES = tuple(f'{__package__}.layer{n}' for n in range(1, 10))
_REGISTRY: dict[str, type[WorkflowFamily]] = {}


def register(cls: type[WorkflowFamily]) -> type[WorkflowFamily]:
    wf_id = cls.spec.wf_id
    if wf_id in _REGISTRY and _REGISTRY[wf_id] is not cls:
        raise ValueError(f'{wf_id} registered twice')
    _REGISTRY[wf_id] = cls
    return cls


def load() -> dict[str, type[WorkflowFamily]]:
    """Import every layer module and return the registry ordered by WF number."""
    for name in LAYER_MODULES:
        import_module(name)
    return dict(sorted(_REGISTRY.items(), key=lambda kv: kv[1].spec.number))


def family(wf_id: str) -> WorkflowFamily:
    return load()[wf_id]()

"""Executable workflow families WF6-WF49, WF51, WF55 and WF56.

``base`` holds the shared runtime (spec, session, budget, verdicts), ``exact``
the shared exact arithmetic, ``layer1`` .. ``layer9`` the families in DAG
layer order, and ``learning`` and ``candidates`` the families whose checks are
all made by the Rust operad host. ``registry.load()`` returns every family by WF id.

What this supports: each family's host check accepts its positive fixtures and
refuses its adversarial fixtures, offline, with zero spend. What it does not
support: any claim that a model run through a family is more accurate; that
needs a matched live or local campaign per family.
"""
from .base import CERTIFIED, REFUSED, TYPED_REFUSAL, WorkflowFamily, WorkflowFamilySpecV1
from .registry import family, load

__all__ = ['CERTIFIED', 'REFUSED', 'TYPED_REFUSAL', 'WorkflowFamily', 'WorkflowFamilySpecV1', 'family', 'load']

"""
templates.py
============

Default Antibody Templates for Swarm Failure Remediation.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Dict

DEFAULT_ANTIBODY_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "clean_arch_violation": {
        "failure_class": "architecture:clean_arch_inward_dependency_violation",
        "target_pattern": r"from\s+(\w+)\s+import.*(?:where\s+layer\(\1\)\s*>\s*layer\(self\))",
        "constraint_type": "ProjectOut",
        "operatorizability": "repairable",
        "action": "repair",
        "severity": "P0",
        "description": "Inward dependency rule violated: inner layer depends on outer layer. Invert dependency via Domain Protocol / Port.",
        "negative_fixture": "from infrastructure.db import DBClient\n\nclass Order:\n    pass\n",
        "positive_fixture": "from domain.ports import OrderRepositoryPort\n\nclass Order:\n    pass\n",
    },
    "circular_import": {
        "failure_class": "architecture:circular_dependency",
        "target_pattern": r"circular_import:\s*(.+)<->(.+)",
        "constraint_type": "ProjectOut",
        "operatorizability": "repairable",
        "action": "repair",
        "severity": "P0",
        "description": "Cycle in the 1-skeleton dependency complex d0(e) = 0. Decouple cyclic vertices via shared kernel port or event mediator.",
        "negative_fixture": "# module_a imports module_b which imports module_a\n",
        "positive_fixture": "# module_a and module_b depend on domain/ports\n",
    },
    "unquoted_annotation": {
        "failure_class": "python:unquoted_forward_type_annotation",
        "target_pattern": r"def\s+\w+\(.*:\s*(\w+).*\)",
        "constraint_type": "Restrain",
        "operatorizability": "repairable",
        "action": "repair",
        "severity": "P2",
        "description": "Forward type annotation without from __future__ import annotations causes runtime NameError.",
        "negative_fixture": "def process(order: Order) -> None:\n    pass\n",
        "positive_fixture": "from __future__ import annotations\n\ndef process(order: Order) -> None:\n    pass\n",
    },
    "uncontracted_io": {
        "failure_class": "governance:uncontracted_io_leak",
        "target_pattern": r"(?:open|requests\.\w+|urllib\.\w+)\(",
        "constraint_type": "ProjectOut",
        "operatorizability": "repairable",
        "action": "repair",
        "severity": "P0",
        "description": "Uncontracted ambient I/O detected in mathematical/domain kernel. Isolate I/O behind infrastructure adapters and CAS storage.",
        "negative_fixture": "def compute():\n    with open('data.txt') as f:\n        return f.read()\n",
        "positive_fixture": "def compute(data: str):\n    return data\n",
    },
}

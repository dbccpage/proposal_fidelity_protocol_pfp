"""pfp_core: a small domain-general runtime that regulates an existing
``AGENTS.md + skills/*/SKILL.md + rules`` setup with PFP, EIS, PCIV and OPERADS
mechanisms imported read-only from this repository.

Modules: ``fidelity`` (contract, host oracle, whole-run budget), ``operad_pipe``
(typed skill wiring and trace quotient), ``immunity`` (thymus screening and
two-signal dispositions), ``civilization`` (lineage taint and reserve
selection), ``legacy_importer`` (industry directory compiler).

What this supports: offline, deterministic regulation of candidate outputs in
the declared benchmark setting. What it does not support: any claim about live
model accuracy; that needs the finite live campaign in
``benchmarks/industry_replacement``.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
# The imported packages use their historical top-level names: ``operations``
# and ``adversary`` live under ``ops/`` (see pyproject package-dir); the budget
# ledger is a flat module under ``dag/benchmark``.
for _path in (REPO_ROOT, REPO_ROOT / 'ops', REPO_ROOT / 'dag' / 'benchmark'):
    if str(_path) not in sys.path:
        sys.path.append(str(_path))

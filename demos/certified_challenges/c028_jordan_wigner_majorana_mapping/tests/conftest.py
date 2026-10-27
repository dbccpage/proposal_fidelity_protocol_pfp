"""Pytest configuration for the C028 test suite.

AuthorityEffect: None.

The package's modules import each other as top-level ``governance``,
``judge_packet`` and ``reference_solver``; put the package root on ``sys.path``
as C029 and C030 do, so the tests import without a PYTHONPATH setting.
"""

import sys
from pathlib import Path

pkg_root = Path(__file__).resolve().parent.parent
if str(pkg_root) not in sys.path:
    sys.path.insert(0, str(pkg_root))

# AuthorityEffect: None.
"""Pytest configuration for C041 test suite."""

import sys
from pathlib import Path

_pkg_root = Path(__file__).resolve().parent.parent
if str(_pkg_root) not in sys.path:
    sys.path.insert(0, str(_pkg_root))

# Also ensure workspace root is on sys.path for providers
for parent in _pkg_root.parents:
    if (parent / "providers").exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break

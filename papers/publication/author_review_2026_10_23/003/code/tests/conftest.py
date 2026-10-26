"""Make the modules in the package ``code/`` folder importable by the tests.

The folder is deliberately not a Python package: a ``code/__init__.py`` would
shadow the standard-library ``code`` module whenever the package root is on
``sys.path`` (for example ``python -m pytest`` run from the package root).
"""

import sys
from pathlib import Path

_CODE_DIR = Path(__file__).resolve().parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

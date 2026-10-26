"""CLI entry-point when executed with `python -m omega_engine_operads.frontend.cli`."""

from __future__ import annotations

import sys
from .main import main

if __name__ == "__main__":
    sys.exit(main())

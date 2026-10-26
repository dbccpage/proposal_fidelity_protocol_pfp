"""Entry point for executing the Proposal Fidelity Protocol (PFP) application directly via python -m.

AuthorityEffect: None.
"""

from __future__ import annotations

import sys
from omega_engine_pfp.entrypoints.cli.pfp import main

if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""FFI seam isolation for the omega_witness_rs PyO3 native module.

Parity Seam Isolation Invariant (AGENTS.md):
Never scatter direct/inline FFI branches throughout production code;
isolate FFI seams into dedicated ffi.py modules.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def load_native_witness_module() -> Optional[Any]:
    """Attempt to import and return the native PyO3 omega_witness_rs extension module.

    Returns:
        The imported module object if available, or None on fallback/failure.
    """
    try:
        import omega_witness_rs  # type: ignore[import-not-found]
        logger.debug("Successfully loaded native omega_witness_rs PyO3 extension.")
        return omega_witness_rs
    except (ImportError, ModuleNotFoundError):
        logger.info(
            "omega_witness_rs native PyO3 module not found; running in pure Python reference mode."
        )
        return None
    except Exception as exc:
        logger.error(
            "Failed to initialize native module omega_witness_rs due to unexpected error: %s",
            exc,
            exc_info=True,
        )
        return None

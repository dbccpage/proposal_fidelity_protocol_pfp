"""Native tests consume an explicitly supplied executable and SHA-256 pin."""

import hashlib
import os
import re
from pathlib import Path

import pytest

SKIP_REASON = (
    "native graph calculator not configured: set OMEGA_FUNCTIONAL_GRAPH_BIN to a "
    "solve_graph_phi1 executable built from the reviewed source and "
    "OMEGA_FUNCTIONAL_GRAPH_SHA256 to its SHA-256 digest (see README)"
)


@pytest.fixture
def native_functional() -> Path:
    """Validate caller configuration without discovering or building a binary."""
    binary = os.environ.get("OMEGA_FUNCTIONAL_GRAPH_BIN")
    expected = os.environ.get("OMEGA_FUNCTIONAL_GRAPH_SHA256")
    if not binary or not expected:
        pytest.skip(SKIP_REASON)
    if re.fullmatch(r"[0-9a-fA-F]{64}", expected) is None:
        pytest.fail(
            "OMEGA_FUNCTIONAL_GRAPH_SHA256 must contain exactly 64 hex digits",
            pytrace=False,
        )
    try:
        executable = Path(binary).resolve(strict=True)
        actual = hashlib.sha256(executable.read_bytes()).hexdigest()
    except (OSError, ValueError) as error:
        pytest.fail(
            f"explicit OMEGA_FUNCTIONAL_GRAPH_BIN could not be read: {error}",
            pytrace=False,
        )
    if actual != expected.lower():
        pytest.fail(
            "OMEGA_FUNCTIONAL_GRAPH_SHA256 digest mismatch for "
            f"{executable}: expected {expected.lower()}, got {actual}",
            pytrace=False,
        )
    return executable

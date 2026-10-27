"""Install the gate catalog from the on-disk YAML mirror.

The domain catalog stays unbound until this module reads the file.
AuthorityEffect: None.
"""

from __future__ import annotations

from operations.domain.cicd.catalog import (
    GATE_CATALOG_V3,
    install_gate_catalog,
)
from operations.domain.cicd.gate_spec import load_gate_catalog_yaml
from operations.infrastructure.cicd.filesystem_text import (
    FilesystemTextReader,
)


def ensure_gate_catalog() -> None:
    """Install the YAML catalog once. A second call does not reread the file."""
    if GATE_CATALOG_V3.installed():
        return
    install_gate_catalog(load_gate_catalog_yaml(FilesystemTextReader()))

"""Canonical paths for the normal-form contract tree.

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path

NORMAL_FORMS_DIR = Path(__file__).resolve().parent.parent / "yaml" / "normal_forms"
CONTRACTS_DIR = NORMAL_FORMS_DIR
INDEX_PATH = CONTRACTS_DIR / "index.yaml"
_GOLDEN = NORMAL_FORMS_DIR / "_golden_nfs"
STANDARD_PATH = _GOLDEN / "standard.yaml"
SCHEMA_V1_PATH = _GOLDEN / "normal_form_contract_schema.yaml"

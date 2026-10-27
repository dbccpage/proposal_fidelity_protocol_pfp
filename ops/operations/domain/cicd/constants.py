"""Domain constants, schema IDs, and ceilings for local_ci Bounded Context."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

_RECEIPT_SCHEMA = "core.local_ci.execution_receipt.v3"
_INVOCATION_SCHEMA = "core.local_ci.invocation.v1"
_MANIFEST_SCHEMA = "core.local_ci.candidate_manifest.v1"
_CANONICAL_MODULE_NAME: Final = (
    "operations.entrypoints.local_ci_receipt_verifier"
)
_CATALOG_DOMAIN = b"engine/GateCatalogV3/v3\0"
_MANIFEST_DOMAIN = b"engine/CanonicalCandidateManifestV1/v1\0"
_RESOLUTION_DOMAIN = b"engine/ResolvedGateInvocationV1/v1\0"
_RESULTS_DOMAIN = b"engine/GateResultsV1/v1\0"
_LOWER_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_LOWER_GIT_OID_RE = re.compile(r"^[0-9a-f]{40}$")
_IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9._:-]*$")
_SAFE_INTEGER_LIMIT = (1 << 53) - 1
MAX_RECEIPT_BYTES: Final = 4_194_304
_MAX_CANONICAL_BYTES = MAX_RECEIPT_BYTES
_RECEIPT_DIGEST_PREFIX: Final = "CORE_LOCAL_CI_RECEIPT_SHA256="
_MAX_JSON_DEPTH = 64
_MAX_JSON_NODES = 100_000
_MAX_INTEGER_LEXEME_DIGITS = 16
_MAX_DETAIL_CHARACTERS = 4_096
_CONCRETE_PATH_TYPE = type(Path("."))

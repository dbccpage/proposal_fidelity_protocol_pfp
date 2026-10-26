"""Wire builders and source custody for the two finite WDP operations.

Source hashes cover raw supplied bytes. The native packet binds an independently
declared finite carrier; a hash does not assert that prose derives that carrier.
No mathematical solver runs in Python. AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import os
import stat
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result

from .ffi import repo_root
from .theory_requests import exact_wire

SOURCE_PACKET_SCHEMA = "omega.wdp.source-packet.v1"
MAX_SOURCE_BYTES = 8192
_LOCUS = "omega_engine_operating_system.adapters.rust_host.source_packet_requests"


def _refuse(code: str, message: str) -> Err:
    return Err(Refusal(code=code, message=message, locus=_LOCUS))


def source_binding(
    source_id: str, raw_bytes: bytes, *, expected_sha256: str
) -> Result[dict[str, Any], Refusal]:
    """Bind 1..8192 caller bytes to a previously pinned raw-byte SHA-256."""
    if not isinstance(source_id, str) or not source_id or len(source_id.encode("utf-8")) > 256:
        return _refuse(
            "WDP_PACKET_SOURCE_BYTES",
            "source_id must be a nonempty string of at most 256 UTF-8 bytes",
        )
    if type(raw_bytes) is not bytes or not 0 < len(raw_bytes) <= MAX_SOURCE_BYTES:
        return _refuse("WDP_PACKET_SOURCE_BYTES", "source must be 1..8192 raw bytes")
    actual = hashlib.sha256(raw_bytes).hexdigest()
    if expected_sha256 != actual:
        return _refuse(
            "WDP_PACKET_SOURCE_DIGEST", "source bytes do not match the pinned raw SHA-256"
        )
    return Ok(
        {
            "source_id": source_id,
            "digest_profile": "sha256_raw_bytes_v1",
            "sha256": actual,
            "bytes": list(raw_bytes),
        }
    )


def source_binding_from_file(
    relative_path: str, *, expected_sha256: str, repository_root: Path | None = None
) -> Result[dict[str, Any], Refusal]:
    """Read one pinned repo file, with no glob, traversal or symlink following.

    Directory-relative O_NOFOLLOW opens protect every path component. Platforms
    without that facility return a typed refusal; callers can supply bytes.
    """
    if (
        not isinstance(relative_path, str)
        or not relative_path
        or "\\" in relative_path
        or any(char in relative_path for char in "*?[]")
    ):
        return _refuse(
            "WDP_PACKET_SOURCE_PATH", "source must name one POSIX repository-relative file"
        )
    components = relative_path.split("/")
    if any(part in {"", ".", ".."} for part in components) or ":" in components[0]:
        return _refuse("WDP_PACKET_SOURCE_PATH", "absolute paths and traversal are refused")
    if (
        not hasattr(os, "O_NOFOLLOW")
        or not hasattr(os, "O_DIRECTORY")
        or os.open not in os.supports_dir_fd
    ):
        return _refuse(
            "WDP_PACKET_SOURCE_PATH", "safe file opens are unavailable; supply pinned bytes"
        )
    root = repository_root if repository_root is not None else repo_root()
    if root is None:
        return _refuse("WDP_PACKET_SOURCE_PATH", "repository root was not found")
    opened: list[int] = []
    try:
        root = Path(root).resolve(strict=True)
        directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        opened.append(directory)
        for component in components[:-1]:
            directory = os.open(
                component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory
            )
            opened.append(directory)
        source_fd = os.open(
            components[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory
        )
        opened.append(source_fd)
        if not stat.S_ISREG(os.fstat(source_fd).st_mode):
            return _refuse("WDP_PACKET_SOURCE_PATH", "source is not a regular file")
        chunks: list[bytes] = []
        count = 0
        while count <= MAX_SOURCE_BYTES:
            chunk = os.read(source_fd, MAX_SOURCE_BYTES + 1 - count)
            if not chunk:
                break
            chunks.append(chunk)
            count += len(chunk)
        return source_binding(relative_path, b"".join(chunks), expected_sha256=expected_sha256)
    except (OSError, TypeError, ValueError) as exc:
        return _refuse("WDP_PACKET_SOURCE_PATH", str(exc))
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)


def resource_limits(
    *,
    max_source_bytes: int = MAX_SOURCE_BYTES,
    max_scalar_ops: int = 1_000_000,
    max_elements: int = 4096,
    max_bits: int = 1024,
) -> dict[str, int]:
    """Positive finite limits; the Rust consumer also validates these ceilings."""
    limits = {
        "max_source_bytes": max_source_bytes,
        "max_scalar_ops": max_scalar_ops,
        "max_elements": max_elements,
        "max_bits": max_bits,
    }
    ceilings = {
        "max_source_bytes": MAX_SOURCE_BYTES,
        "max_scalar_ops": 10_000_000,
        "max_elements": 4096,
        "max_bits": 1024,
    }
    for field, value in limits.items():
        if type(value) is not int or not 0 < value <= ceilings[field]:
            raise ValueError(f"{field} must be a positive integer at most {ceilings[field]}")
    return limits


def _header(
    question: str,
    scalar: str,
    quotient: str,
    positivity: str,
    composition: str,
    limits: Mapping[str, int] | None,
) -> dict[str, Any]:
    return {
        "schema_version": SOURCE_PACKET_SCHEMA,
        "question": question,
        "scope": "finite_declared_inputs",
        "scalar_model": scalar,
        "quotient_model": quotient,
        "positivity_model": positivity,
        "composition_model": composition,
        "availability_model": "declared_finite_carrier",
        "limits": resource_limits(**dict(limits)) if limits is not None else resource_limits(),
    }


def rational_matrix(rows: int, cols: int, entries: Sequence[Any]) -> dict[str, Any]:
    if type(rows) is not int or type(cols) is not int or rows < 0 or cols < 0:
        raise ValueError("matrix dimensions must be nonnegative integers")
    if len(entries) != rows * cols:
        raise ValueError("row-major entry count must match the declared dimensions")
    return {"rows": rows, "cols": cols, "entries": [exact_wire(entry) for entry in entries]}


def gaussian_matrix(rows: int, cols: int, entries: Sequence[Sequence[Any]]) -> dict[str, Any]:
    rational_matrix(rows, cols, [0] * len(entries))
    encoded = []
    for entry in entries:
        if len(entry) != 2:
            raise ValueError("a Gaussian rational needs exact real and imaginary parts")
        encoded.append({"re": exact_wire(entry[0]), "im": exact_wire(entry[1])})
    return {"rows": rows, "cols": cols, "entries": encoded}


def hodge_packet_payload(
    source: Mapping[str, Any],
    d0: Mapping[str, Any],
    d1: Mapping[str, Any],
    flow: Sequence[Any],
    *,
    limits: Mapping[str, int] | None = None,
) -> Result[dict[str, Any], Refusal]:
    try:
        return Ok(
            {
                "header": _header(
                    "exact_euclidean_hodge_decomposition",
                    "exact_rational",
                    "potential_modulo_kernel",
                    "not_applicable",
                    "not_applicable",
                    limits,
                ),
                "source": dict(source),
                "operation": {
                    "kind": "hodge",
                    "d0": dict(d0),
                    "d1": dict(d1),
                    "flow": [exact_wire(value) for value in flow],
                },
            }
        )
    except (TypeError, ValueError, OverflowError) as exc:
        return _refuse("WDP_PACKET_WIRE", str(exc))


def weighted_kraus_packet_payload(
    source: Mapping[str, Any],
    *,
    dim_in: int,
    dim_out: int,
    terms: Sequence[tuple[Any, Mapping[str, Any]]],
    state_factor: Mapping[str, Any],
    limits: Mapping[str, int] | None = None,
) -> Result[dict[str, Any], Refusal]:
    try:
        if (
            type(dim_in) is not int
            or type(dim_out) is not int
            or not 1 <= dim_in <= 16
            or not 1 <= dim_out <= 16
        ):
            raise ValueError("channel dimensions must be integers in 1..16")
        return Ok(
            {
                "header": _header(
                    "exact_weighted_kraus_gram_state_transport",
                    "exact_gaussian_rational",
                    "matrix_entry_equality",
                    "nonnegative_kraus_weights_and_gram_state",
                    "single_declared_map",
                    limits,
                ),
                "source": dict(source),
                "operation": {
                    "kind": "weighted_kraus_gram_state_transport",
                    "dim_in": dim_in,
                    "dim_out": dim_out,
                    "terms": [
                        {"weight": exact_wire(weight), "operator": dict(operator)}
                        for weight, operator in terms
                    ],
                    "state_factor": dict(state_factor),
                },
            }
        )
    except (TypeError, ValueError, OverflowError) as exc:
        return _refuse("WDP_PACKET_WIRE", str(exc))


def packet_verify_payload(
    request: Mapping[str, Any], result: Mapping[str, Any]
) -> Result[dict[str, Any], Refusal]:
    if not isinstance(request, Mapping) or not isinstance(result, Mapping):
        return _refuse("WDP_PACKET_WIRE", "request and result must be mappings")
    return Ok({"request": dict(request), "result": dict(result)})


__all__ = [
    "gaussian_matrix",
    "hodge_packet_payload",
    "packet_verify_payload",
    "rational_matrix",
    "resource_limits",
    "source_binding",
    "source_binding_from_file",
    "weighted_kraus_packet_payload",
]

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from operations.infrastructure.cicd.ci_execution_context import CiExecutionContext, ExecutionContextConfig
    from operations.infrastructure.cicd.serialization import LocalCiSerializer, _canonical_value_bytes, _load_json_value, _model_value, _parse_integer, _preflight_depth, _refuse_constant, _refuse_float, _resolved_invocation_digest, _validate_unicode_scalar_string, _walk_canonical_value, canonical_candidate_manifest_sha256, canonical_gate_catalog_sha256, canonical_gate_results_sha256, canonical_local_ci_json_bytes, parse_local_ci_receipt, parse_local_ci_receipt_bytes, resolved_invocation_digest
    from operations.infrastructure.cicd.storage import _fsync_parent_directory, _path_is_reparse_point, _read_receipt_buffer_once, _validate_atomic_target, load_local_ci_receipt, write_local_ci_receipt_atomic

__all__ = ('CiExecutionContext', 'ExecutionContextConfig', '_canonical_value_bytes', '_fsync_parent_directory', '_load_json_value', '_model_value', '_parse_integer', '_path_is_reparse_point', '_preflight_depth', '_read_receipt_buffer_once', '_refuse_constant', '_refuse_float', '_resolved_invocation_digest', '_validate_atomic_target', '_validate_unicode_scalar_string', '_walk_canonical_value', 'canonical_candidate_manifest_sha256', 'canonical_gate_catalog_sha256', 'canonical_gate_results_sha256', 'canonical_local_ci_json_bytes', 'load_local_ci_receipt', 'parse_local_ci_receipt', 'parse_local_ci_receipt_bytes', 'resolved_invocation_digest', 'write_local_ci_receipt_atomic', 'LocalCiSerializer')

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'CiExecutionContext': ('operations.infrastructure.cicd.ci_execution_context', 'CiExecutionContext'),
    'ExecutionContextConfig': ('operations.infrastructure.cicd.ci_execution_context', 'ExecutionContextConfig'),
    'LocalCiSerializer': ('operations.infrastructure.cicd.serialization', 'LocalCiSerializer'),
    '_canonical_value_bytes': ('operations.infrastructure.cicd.serialization', '_canonical_value_bytes'),
    '_load_json_value': ('operations.infrastructure.cicd.serialization', '_load_json_value'),
    '_model_value': ('operations.infrastructure.cicd.serialization', '_model_value'),
    '_parse_integer': ('operations.infrastructure.cicd.serialization', '_parse_integer'),
    '_preflight_depth': ('operations.infrastructure.cicd.serialization', '_preflight_depth'),
    '_refuse_constant': ('operations.infrastructure.cicd.serialization', '_refuse_constant'),
    '_refuse_float': ('operations.infrastructure.cicd.serialization', '_refuse_float'),
    '_resolved_invocation_digest': ('operations.infrastructure.cicd.serialization', '_resolved_invocation_digest'),
    '_validate_unicode_scalar_string': ('operations.infrastructure.cicd.serialization', '_validate_unicode_scalar_string'),
    '_walk_canonical_value': ('operations.infrastructure.cicd.serialization', '_walk_canonical_value'),
    'canonical_candidate_manifest_sha256': ('operations.infrastructure.cicd.serialization', 'canonical_candidate_manifest_sha256'),
    'canonical_gate_catalog_sha256': ('operations.infrastructure.cicd.serialization', 'canonical_gate_catalog_sha256'),
    'canonical_gate_results_sha256': ('operations.infrastructure.cicd.serialization', 'canonical_gate_results_sha256'),
    'canonical_local_ci_json_bytes': ('operations.infrastructure.cicd.serialization', 'canonical_local_ci_json_bytes'),
    'parse_local_ci_receipt': ('operations.infrastructure.cicd.serialization', 'parse_local_ci_receipt'),
    'parse_local_ci_receipt_bytes': ('operations.infrastructure.cicd.serialization', 'parse_local_ci_receipt_bytes'),
    'resolved_invocation_digest': ('operations.infrastructure.cicd.serialization', 'resolved_invocation_digest'),
    '_fsync_parent_directory': ('operations.infrastructure.cicd.storage', '_fsync_parent_directory'),
    '_path_is_reparse_point': ('operations.infrastructure.cicd.storage', '_path_is_reparse_point'),
    '_read_receipt_buffer_once': ('operations.infrastructure.cicd.storage', '_read_receipt_buffer_once'),
    '_validate_atomic_target': ('operations.infrastructure.cicd.storage', '_validate_atomic_target'),
    'load_local_ci_receipt': ('operations.infrastructure.cicd.storage', 'load_local_ci_receipt'),
    'write_local_ci_receipt_atomic': ('operations.infrastructure.cicd.storage', 'write_local_ci_receipt_atomic'),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_IMPORTS.get(name)
    if target is not None:
        mod_name, attr_name = target
        mod = importlib.import_module(mod_name, __name__)
        val = getattr(mod, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))

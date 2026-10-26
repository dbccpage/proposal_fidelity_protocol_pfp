from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from omega_engine_operations.infrastructure.cicd.ci_execution_context import CiExecutionContext, ExecutionContextConfig
    from omega_engine_operations.infrastructure.cicd.serialization import LocalCiSerializer, _canonical_value_bytes, _load_json_value, _model_value, _parse_integer, _preflight_depth, _refuse_constant, _refuse_float, _resolved_invocation_digest, _validate_unicode_scalar_string, _walk_canonical_value, canonical_candidate_manifest_sha256, canonical_gate_catalog_sha256, canonical_gate_results_sha256, canonical_local_ci_json_bytes, parse_local_ci_receipt, parse_local_ci_receipt_bytes, resolved_invocation_digest
    from omega_engine_operations.infrastructure.cicd.storage import _fsync_parent_directory, _path_is_reparse_point, _read_receipt_buffer_once, _validate_atomic_target, load_local_ci_receipt, write_local_ci_receipt_atomic

__all__ = ('CiExecutionContext', 'ExecutionContextConfig', '_canonical_value_bytes', '_fsync_parent_directory', '_load_json_value', '_model_value', '_parse_integer', '_path_is_reparse_point', '_preflight_depth', '_read_receipt_buffer_once', '_refuse_constant', '_refuse_float', '_resolved_invocation_digest', '_validate_atomic_target', '_validate_unicode_scalar_string', '_walk_canonical_value', 'canonical_candidate_manifest_sha256', 'canonical_gate_catalog_sha256', 'canonical_gate_results_sha256', 'canonical_local_ci_json_bytes', 'load_local_ci_receipt', 'parse_local_ci_receipt', 'parse_local_ci_receipt_bytes', 'resolved_invocation_digest', 'write_local_ci_receipt_atomic', 'LocalCiSerializer')

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'CiExecutionContext': ('omega_engine_operations.infrastructure.cicd.ci_execution_context', 'CiExecutionContext'),
    'ExecutionContextConfig': ('omega_engine_operations.infrastructure.cicd.ci_execution_context', 'ExecutionContextConfig'),
    'LocalCiSerializer': ('omega_engine_operations.infrastructure.cicd.serialization', 'LocalCiSerializer'),
    '_canonical_value_bytes': ('omega_engine_operations.infrastructure.cicd.serialization', '_canonical_value_bytes'),
    '_load_json_value': ('omega_engine_operations.infrastructure.cicd.serialization', '_load_json_value'),
    '_model_value': ('omega_engine_operations.infrastructure.cicd.serialization', '_model_value'),
    '_parse_integer': ('omega_engine_operations.infrastructure.cicd.serialization', '_parse_integer'),
    '_preflight_depth': ('omega_engine_operations.infrastructure.cicd.serialization', '_preflight_depth'),
    '_refuse_constant': ('omega_engine_operations.infrastructure.cicd.serialization', '_refuse_constant'),
    '_refuse_float': ('omega_engine_operations.infrastructure.cicd.serialization', '_refuse_float'),
    '_resolved_invocation_digest': ('omega_engine_operations.infrastructure.cicd.serialization', '_resolved_invocation_digest'),
    '_validate_unicode_scalar_string': ('omega_engine_operations.infrastructure.cicd.serialization', '_validate_unicode_scalar_string'),
    '_walk_canonical_value': ('omega_engine_operations.infrastructure.cicd.serialization', '_walk_canonical_value'),
    'canonical_candidate_manifest_sha256': ('omega_engine_operations.infrastructure.cicd.serialization', 'canonical_candidate_manifest_sha256'),
    'canonical_gate_catalog_sha256': ('omega_engine_operations.infrastructure.cicd.serialization', 'canonical_gate_catalog_sha256'),
    'canonical_gate_results_sha256': ('omega_engine_operations.infrastructure.cicd.serialization', 'canonical_gate_results_sha256'),
    'canonical_local_ci_json_bytes': ('omega_engine_operations.infrastructure.cicd.serialization', 'canonical_local_ci_json_bytes'),
    'parse_local_ci_receipt': ('omega_engine_operations.infrastructure.cicd.serialization', 'parse_local_ci_receipt'),
    'parse_local_ci_receipt_bytes': ('omega_engine_operations.infrastructure.cicd.serialization', 'parse_local_ci_receipt_bytes'),
    'resolved_invocation_digest': ('omega_engine_operations.infrastructure.cicd.serialization', 'resolved_invocation_digest'),
    '_fsync_parent_directory': ('omega_engine_operations.infrastructure.cicd.storage', '_fsync_parent_directory'),
    '_path_is_reparse_point': ('omega_engine_operations.infrastructure.cicd.storage', '_path_is_reparse_point'),
    '_read_receipt_buffer_once': ('omega_engine_operations.infrastructure.cicd.storage', '_read_receipt_buffer_once'),
    '_validate_atomic_target': ('omega_engine_operations.infrastructure.cicd.storage', '_validate_atomic_target'),
    'load_local_ci_receipt': ('omega_engine_operations.infrastructure.cicd.storage', 'load_local_ci_receipt'),
    'write_local_ci_receipt_atomic': ('omega_engine_operations.infrastructure.cicd.storage', 'write_local_ci_receipt_atomic'),
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

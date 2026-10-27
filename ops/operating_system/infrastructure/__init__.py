"""Infrastructure adapters owned by OEOS."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .checkout_lease import CheckoutLeaseManager
    from .encrypted_artifact_cas import EncryptedArtifactCas
    from .migrations import MigrationDefinitionV1, apply_migrations, get_applied_migrations, get_migration_status, rollback_migration
    from .sqlite_agentic_store import SqliteAgenticStore
    from .sqlite_task_store import SqliteTaskStore

__all__ = ['CheckoutLeaseManager', 'EncryptedArtifactCas', 'MigrationDefinitionV1', 'SqliteAgenticStore', 'SqliteTaskStore', 'apply_migrations', 'get_applied_migrations', 'get_migration_status', 'rollback_migration']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'CheckoutLeaseManager': ('.checkout_lease', 'CheckoutLeaseManager'),
    'EncryptedArtifactCas': ('.encrypted_artifact_cas', 'EncryptedArtifactCas'),
    'MigrationDefinitionV1': ('.migrations', 'MigrationDefinitionV1'),
    'apply_migrations': ('.migrations', 'apply_migrations'),
    'get_applied_migrations': ('.migrations', 'get_applied_migrations'),
    'get_migration_status': ('.migrations', 'get_migration_status'),
    'rollback_migration': ('.migrations', 'rollback_migration'),
    'SqliteAgenticStore': ('.sqlite_agentic_store', 'SqliteAgenticStore'),
    'SqliteTaskStore': ('.sqlite_task_store', 'SqliteTaskStore'),
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

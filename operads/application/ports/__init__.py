"""Application-owned Ports (Inward Interfaces)."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .clock_port import ClockPort
    from .estate_source_port import EstateSourcePort
    from .id_generator_port import IdGeneratorPort
    from .immune_screen_port import DetectorIdentity, DetectorMatch, HostDangerObservation, ImmuneEvidenceRefusal, ImmuneScreenPort, ImmuneVerdict, SensorReading
    from .journal_port import JournalPort
    from .legacy_catalog_reader_port import LegacyCatalogReaderPort
    from .projection_manifest_port import ProjectionManifestPort
    from .skill_document_parser_port import SkillDocumentParserPort
    from .strict_operad_port import StrictOperadPort
    from .unit_of_work_port import OeopUnitOfWorkPort

__all__ = ['ClockPort', 'EstateSourcePort', 'IdGeneratorPort', 'DetectorIdentity', 'DetectorMatch', 'HostDangerObservation', 'ImmuneEvidenceRefusal', 'ImmuneScreenPort', 'ImmuneVerdict', 'SensorReading', 'JournalPort', 'LegacyCatalogReaderPort', 'OeopUnitOfWorkPort', 'ProjectionManifestPort', 'SkillDocumentParserPort', 'StrictOperadPort']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ClockPort': ('.clock_port', 'ClockPort'),
    'EstateSourcePort': ('.estate_source_port', 'EstateSourcePort'),
    'IdGeneratorPort': ('.id_generator_port', 'IdGeneratorPort'),
    'DetectorIdentity': ('.immune_screen_port', 'DetectorIdentity'),
    'DetectorMatch': ('.immune_screen_port', 'DetectorMatch'),
    'HostDangerObservation': ('.immune_screen_port', 'HostDangerObservation'),
    'ImmuneEvidenceRefusal': ('.immune_screen_port', 'ImmuneEvidenceRefusal'),
    'ImmuneScreenPort': ('.immune_screen_port', 'ImmuneScreenPort'),
    'ImmuneVerdict': ('.immune_screen_port', 'ImmuneVerdict'),
    'SensorReading': ('.immune_screen_port', 'SensorReading'),
    'JournalPort': ('.journal_port', 'JournalPort'),
    'LegacyCatalogReaderPort': ('.legacy_catalog_reader_port', 'LegacyCatalogReaderPort'),
    'ProjectionManifestPort': ('.projection_manifest_port', 'ProjectionManifestPort'),
    'SkillDocumentParserPort': ('.skill_document_parser_port', 'SkillDocumentParserPort'),
    'StrictOperadPort': ('.strict_operad_port', 'StrictOperadPort'),
    'OeopUnitOfWorkPort': ('.unit_of_work_port', 'OeopUnitOfWorkPort'),
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

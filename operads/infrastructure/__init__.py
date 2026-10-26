"""Lazy infrastructure exports for independent offline adapters."""

from importlib import import_module

_EXPORTS = {
    "FsEstateSourceAdapter": ".fs.fs_estate_source_adapter",
    "LegacyCatalogReaderAdapter": ".fs.legacy_catalog_reader_adapter",
    "HigherOperadAdapter": ".operad.higher_operad_adapter",
    "LosslessMarkdownParserAdapter": ".parser.markdown_parser_adapter",
    "ProjectionManifestAdapter": ".providers.projection_manifest_adapter",
    "SystemClock": ".providers.system_clock",
    "UuidIdGenerator": ".providers.uuid_id_generator",
    "SqliteUnitOfWork": ".storage.sqlite_unit_of_work",
    "OeopContainer": ".bootstrap",
    "create_oeop_container": ".bootstrap",
}
__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    value = getattr(import_module(_EXPORTS[name], __name__), name)
    globals()[name] = value
    return value

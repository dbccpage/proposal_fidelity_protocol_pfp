"""Filesystem adapter implementing EstateSourcePort."""

from __future__ import annotations

import pathlib
import hashlib
import stat

from operations.domain.rop.result import Err, Ok, Result
from operads.domain.capability_catalog_v1 import (
    CapabilityCatalogRefusal,
    decode_capability_catalog,
)

from ...application.ports.estate_source_port import EstateSourcePort
from ...domain.errors.domain_errors import DomainInvariantError, OeopDomainError
from ...domain.value_objects.identifier import EstateRef
from ...domain.entities.skill_document_v3 import SkillDocumentV3


class FsEstateSourceAdapter(EstateSourcePort):
    def __init__(self, base_path: pathlib.Path) -> None:
        self._base_path = base_path.absolute()
        self._skills_by_path = {}
        canonical = self._base_path / "operads"
        self._source_prefix = "operads/" if (
            (canonical / "skills").is_dir() or (canonical / "skill_operad").is_dir()
        ) else ".agents/"

    def list_skill_paths(self, estate_ref: EstateRef) -> Result[tuple[str, ...], OeopDomainError]:
        catalog_path = self._base_path / "operads/skill_operad/json/capability_catalog.v1.json"
        if self._source_prefix == ".agents/":
            catalog_path = self._base_path / ".agents" / "skill_operads" / "capability_catalog.v1.json"
        if not catalog_path.is_file() and self._source_prefix == ".agents/":
            catalog_path = self._base_path / ".agents" / "operad" / "capability_catalog.v1.json"
        if not catalog_path.is_file():
            catalog_path = (
                self._base_path
                / "operads"
                / "skill_operad"
                / "json"
                / "capability_catalog.v1.json"
            )
        if not catalog_path.is_file():
            return Err(
                DomainInvariantError(
                    code="CAPABILITY_CATALOG_MISSING",
                    message="Tracked capability catalog is required",
                )
            )
        try:
            catalog = decode_capability_catalog(catalog_path.read_bytes())
        except (OSError, CapabilityCatalogRefusal) as error:
            return Err(
                DomainInvariantError(
                    code="CAPABILITY_CATALOG_REFUSED",
                    message=str(error),
                )
            )
        self._skills_by_path = {
            self._source_prefix + skill.source_path: skill for skill in catalog.skills
        }
        return Ok(tuple(self._skills_by_path))

    def read_compiled_skill_document(self, relative_path: str) -> Result[SkillDocumentV3 | None, OeopDomainError]:
        from ..capability_catalog_compiler import CatalogCompileRefusal, _frontmatter
        from ..typed_contract_compiler import TypedContractCompileRefusal, compile_typed_contracts, read_typed_package_resource

        try:
            skill = self._skills_by_path.get(relative_path)
            if skill is None:
                raise ValueError("source is not in the selected capability catalog")
            raw_result = self.read_skill_bytes(relative_path)
            if raw_result.is_err:
                return raw_result
            raw = raw_result.unwrap()
            try:
                meta, _ = _frontmatter(raw, relative_path)
            except CatalogCompileRefusal:
                meta = {}
            generated = type(meta.get("metadata")) is dict and meta["metadata"].get(
                "core-generated"
            ) == "oewas.typed-capability.v1"
            canonical = tuple(resource for resource in skill.package_resources if resource.path.startswith(
                "operads/catalog/contracts/v1/"
            ) and resource.path.endswith(".json"))
            if not generated and not canonical:
                return Ok(None)
            bundle = compile_typed_contracts(self._base_path)
            if dict(bundle.packages).get(skill.skill_id) != raw:
                raise ValueError("generated entrypoint differs from its canonical typed source")
            for resource in skill.package_resources:
                if resource.path.startswith("_ic/nara/historical/oewas007/research/"):
                    read_typed_package_resource(self._base_path, skill.skill_id, resource)
                    continue
                resource_path = resource.path
                if resource_path.startswith("skills/"):
                    resource_path = self._source_prefix + resource_path
                data = self.read_skill_bytes(resource_path)
                if data.is_err:
                    return data
                if len(data.unwrap()) != resource.byte_length or hashlib.sha256(data.unwrap()).hexdigest() != resource.sha256:
                    raise ValueError(f"catalog resource changed: {resource.path}")
            document = next(item for item in bundle.all_documents if str(item.skill_id) == skill.skill_id)
            return Ok(document)
        except (OSError, ValueError, StopIteration, TypedContractCompileRefusal) as error:
            return Err(DomainInvariantError(code="TYPED_SOURCE_REFUSED", message=str(error)))

    def read_skill_bytes(self, relative_path: str) -> Result[bytes, OeopDomainError]:
        full_path = self._base_path / relative_path
        root = self._base_path.resolve()
        if "\\" in relative_path or pathlib.PurePosixPath(relative_path).is_absolute() or any(
            part in {"", ".", ".."} for part in relative_path.split("/")
        ) or not full_path.resolve().is_relative_to(root):
            return Err(DomainInvariantError(code="SOURCE_PATH_REFUSED", message=relative_path))
        if not full_path.exists():
            return Err(
                DomainInvariantError(
                    code="FILE_NOT_FOUND",
                    message=f"File {relative_path} not found",
                )
            )
        try:
            for component in (full_path, *full_path.parents):
                if component == self._base_path.parent:
                    break
                info = component.lstat()
                if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                    return Err(DomainInvariantError(code="SOURCE_ALIAS_REFUSED", message=relative_path))
            return Ok(full_path.read_bytes())
        except OSError as error:
            return Err(
                DomainInvariantError(code="FILE_READ_ERROR", message=str(error))
            )

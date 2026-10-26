"""Typed mode catalog index for the PFP twenty canonical modes.

Models the catalog table in ``modes/README.md``: five clusters, twenty mode
entries, and the cluster membership map.  Per-mode contracts remain in
``mode_NN_*/contract.yaml`` and are validated by ``load_mode_catalog``.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StrictStr,
    field_validator,
    model_validator,
)


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class ModeCluster(str, Enum):
    """Five mode clusters (README cluster diagram)."""

    CARRIER_REPRESENTATION = "Cluster I: Carrier & Representation"
    INTERNAL_STEERING = "Cluster II: Internal Steering"
    GROUP_COCHAIN_STRUCTURE = "Cluster III: Group & Cochain Structure"
    DIALECTICAL_ADVERSARIAL = "Cluster IV: Dialectical & Adversarial"
    FOUNDATIONAL_MECHANIZATION = "Cluster V: Foundational Mechanization"


CLUSTER_MEMBERS: dict[ModeCluster, tuple[int, ...]] = {
    ModeCluster.CARRIER_REPRESENTATION: (1, 2, 6, 15),
    ModeCluster.INTERNAL_STEERING: (3, 4, 5),
    ModeCluster.GROUP_COCHAIN_STRUCTURE: (7, 8, 12, 13),
    ModeCluster.DIALECTICAL_ADVERSARIAL: (10, 11, 14, 16, 17, 20),
    ModeCluster.FOUNDATIONAL_MECHANIZATION: (9, 18, 19),
}


def _reject_bool(value: object) -> object:
    if isinstance(value, bool):
        raise ValueError("bool is not an accepted integer")
    return value


class ModeCatalogEntry(_Frozen):
    """One row of the README mode catalog."""

    mode_id: StrictInt = Field(ge=1, le=20)
    name: StrictStr = Field(min_length=1)
    cluster: ModeCluster
    contract_path: StrictStr = Field(pattern=r"^mode_\d{2}_[a-z0-9_]+/contract\.yaml$")
    extra_specs: tuple[StrictStr, ...] = ()
    authority_effect: Literal["None"] = "None"

    @field_validator("mode_id", mode="before")
    @classmethod
    def _no_bool(cls, v: object) -> object:
        return _reject_bool(v)

    @model_validator(mode="after")
    def _path_matches_id(self) -> ModeCatalogEntry:
        if not self.contract_path.startswith(f"mode_{self.mode_id:02d}_"):
            raise ValueError("contract_path prefix must equal zero-padded mode_id")
        if self.mode_id not in CLUSTER_MEMBERS[self.cluster]:
            raise ValueError("mode_id is not a member of its declared cluster")
        return self


class ModeCatalog(_Frozen):
    """The twenty-mode catalog: ids 1..20 exactly once, cluster-consistent."""

    entries: tuple[ModeCatalogEntry, ...]
    authority_effect: Literal["None"] = "None"

    @model_validator(mode="after")
    def _complete_partition(self) -> ModeCatalog:
        ids = sorted(e.mode_id for e in self.entries)
        if ids != list(range(1, 21)):
            raise ValueError("catalog must contain mode ids 1..20 exactly once")
        return self


class ModeContractHeader(_Frozen):
    """The identity fields of a mode contract.yaml that the catalog indexes."""

    mode_id: StrictInt = Field(ge=1, le=20)
    name: StrictStr = Field(min_length=1)
    cluster: ModeCluster
    authority_effect: Literal["None"]

    @field_validator("mode_id", mode="before")
    @classmethod
    def _no_bool(cls, v: object) -> object:
        return _reject_bool(v)


class ManifestModeRef(_Frozen):
    """A ``modes:`` item in modes_manifest.yaml."""

    id: StrictInt
    file: StrictStr
    name: StrictStr
    cluster: ModeCluster

    @field_validator("id", mode="before")
    @classmethod
    def _no_bool(cls, v: object) -> object:
        return _reject_bool(v)

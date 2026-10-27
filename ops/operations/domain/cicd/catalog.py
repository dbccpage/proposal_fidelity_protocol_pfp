"""Domain catalog of gate specifications for local_ci Bounded Context.

The catalog starts unbound. Infrastructure installs the specs parsed from
``gate_catalog_v3.yaml``. This module does not open that file.
"""

from __future__ import annotations

from operations.domain.cicd.enums import GateDisposition
from operations.domain.cicd.gate_spec import GateSpec

class _InstalledGateCatalog:
    """In-place catalog. Importers keep this object across installation."""

    def __init__(self) -> None:
        self._specs: tuple[GateSpec, ...] | None = None

    def install(self, specs: tuple[GateSpec, ...]) -> None:
        self._specs = tuple(specs)

    def installed(self) -> bool:
        return self._specs is not None

    def _require(self) -> tuple[GateSpec, ...]:
        if self._specs is None:
            raise RuntimeError("GATE_CATALOG_UNBOUND")
        return self._specs

    def __iter__(self):
        return iter(self._require())

    def __len__(self) -> int:
        return len(self._require())

    def __getitem__(self, index):
        return self._require()[index]

    def __eq__(self, other: object) -> bool:
        if other is self:
            return True
        specs = self._require()
        if isinstance(other, _InstalledGateCatalog):
            return specs == other._require()
        if isinstance(other, tuple):
            return specs == other
        return NotImplemented


GATE_CATALOG_V3 = _InstalledGateCatalog()


def install_gate_catalog(specs: tuple[GateSpec, ...]) -> None:
    """Replace the installed specs in the existing catalog object."""
    GATE_CATALOG_V3.install(specs)


class _GateIndex:
    """Lookup by gate id. The mapping is built when a caller asks."""

    def get(self, key: str, default: GateSpec | None = None) -> GateSpec | None:
        for gate in GATE_CATALOG_V3:
            if gate.gate_id == key:
                return gate
        return default


_GATE_BY_ID = _GateIndex()


def active_gate_specs() -> tuple[GateSpec, ...]:
    """Return active gates in their one canonical execution order."""
    return tuple(
        gate
        for gate in GATE_CATALOG_V3
        if gate.disposition is not GateDisposition.QUARANTINED
    )


def quarantined_gate_specs() -> tuple[GateSpec, ...]:
    """Return inert residual gates in canonical catalog order."""
    return tuple(
        gate
        for gate in GATE_CATALOG_V3
        if gate.disposition is GateDisposition.QUARANTINED
    )

"""Read side of the pharmacy: only human-admitted antibodies may be injected.

Farming records candidates; admission is a separate human act. Consumers (Adversary and
other swarms) inject guidance only from antibodies whose recorded status is
``admitted``. Candidates, rejected and retired entries are never returned, and an entry
that does not reconstruct as a valid ``Antibody`` is reported, not returned.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields
from typing import Any

from eis.domain.pharmacy_models import (
    Antibody,
    PharmacyStatus,
)

_FIELDS = frozenset(item.name for item in fields(Antibody))


@dataclass(frozen=True)
class AdmittedAntibodiesV1:
    admitted: tuple[Antibody, ...]
    malformed_ids: tuple[str, ...]
    authority_effect: str = "None"


def admitted_antibodies(catalog: Mapping[str, Any]) -> AdmittedAntibodiesV1:
    """Return admitted antibodies from a pharmacy catalog mapping, sorted by id."""
    entries = catalog.get("antibodies", {})
    admitted: list[Antibody] = []
    malformed: list[str] = []
    if not isinstance(entries, Mapping):
        return AdmittedAntibodiesV1(admitted=(), malformed_ids=("<catalog.antibodies>",))
    for antibody_id in sorted(entries):
        entry = entries[antibody_id]
        if not isinstance(entry, Mapping) or entry.get("pharmacy_status") != (
            PharmacyStatus.ADMITTED.value
        ):
            continue
        try:
            antibody = Antibody(**{key: entry[key] for key in entry if key in _FIELDS})
        except (TypeError, ValueError):
            malformed.append(str(antibody_id))
            continue
        if antibody.antibody_id != antibody_id:
            malformed.append(str(antibody_id))
            continue
        admitted.append(antibody)
    return AdmittedAntibodiesV1(admitted=tuple(admitted), malformed_ids=tuple(malformed))


__all__ = ["AdmittedAntibodiesV1", "admitted_antibodies"]

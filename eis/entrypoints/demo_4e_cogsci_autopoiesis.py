"""Composition root for demo_4e_cogsci_autopoiesis.

Wires the use case in
`use_cases/demos/demo_4e_cogsci_autopoiesis/run_packaged_immune.py` to:

- the Symbol Game's 24 dual pharmacy controls and packaged fixture replies;
- the OEEIS screen wiring in `infrastructure/immune_demo_screens.py`;
- the native pharmacy (`core_prompt_civilization` through the Symbol Game
  host); without a built host a control refuses with
  `NATIVE_PHARMACY_UNAVAILABLE`;
- a quarantine store scoped to the run's output directory.

The project demo runner calls `run_demo` and `verify_receipt` from here.
AuthorityEffect: None.
"""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any, Mapping, Sequence

from eis.use_cases.demos.demo_4e_cogsci_autopoiesis.policy import (
    DemoRefusal,
)
from eis.infrastructure.immune_demo_screens import (
    screen_pharmacy_control,
    screen_reply,
)
from eis.infrastructure.mssn_ports import RunQuarantineSink
from eis.infrastructure.native_pharmacy import (
    NativePharmacy,
    NativePharmacyUnavailable,
)
from eis.use_cases.demos.demo_4e_cogsci_autopoiesis import (
    run_packaged_immune as use_case,
)
from pfp.infrastructure.adapters.mssn_scenarios.immune_fixtures import (
    NEGATIVE_FIXTURES,
    POSITIVE_FIXTURES,
)

_FIXTURE_PACKAGE = "pfp.infrastructure.adapters.mssn_research"


def packaged_replies() -> tuple[str, str]:
    """The two replies shipped in the packaged immune fixture. Not historical outputs."""
    raw = files(_FIXTURE_PACKAGE).joinpath("fixtures/demo_4e_cogsci_autopoiesis.json").read_bytes()
    fixture = json.loads(raw)
    if type(fixture) is not dict or fixture.get("kind") != "immune":
        raise DemoRefusal("SCENARIO_FIXTURE_KIND")
    replies = fixture.get("replies")
    if (
        type(replies) is not list
        or len(replies) != 2
        or type(replies[0]) is not str
        or type(replies[1]) is not str
    ):
        raise DemoRefusal("SCENARIO_FIXTURE_REPLIES")
    return (replies[0], replies[1])


def wiring(native: NativePharmacy | None = None) -> use_case.Demo4eWiring:
    """The concrete wiring; one native pharmacy (and its report cache) per call."""
    pharmacy = native if native is not None else NativePharmacy()

    def screen_control(case: Mapping[str, Any], *, quarantine: Any):
        try:
            return screen_pharmacy_control(case, quarantine=quarantine, native=pharmacy)
        except NativePharmacyUnavailable as exc:
            raise DemoRefusal("NATIVE_PHARMACY_UNAVAILABLE", f"{exc.code}: {exc.detail}") from exc

    return use_case.Demo4eWiring(
        positive_controls=tuple(POSITIVE_FIXTURES),
        negative_controls=tuple(NEGATIVE_FIXTURES),
        screen_control=screen_control,
        screen_reply=screen_reply,
        quarantine_factory=RunQuarantineSink,
        packaged_replies=packaged_replies,
    )


def run_packaged_immune(output_dir: Path, replies: Sequence[str]) -> dict:
    return use_case.run_packaged_immune(output_dir, replies, wiring=wiring())


def run_demo(scenario_id: str, output_dir: Path) -> dict:
    return use_case.run_demo(scenario_id, output_dir, wiring=wiring())


def verify_receipt(raw: bytes) -> dict:
    return use_case.verify_receipt(raw, wiring=wiring())


__all__ = ["packaged_replies", "run_demo", "run_packaged_immune", "verify_receipt", "wiring"]

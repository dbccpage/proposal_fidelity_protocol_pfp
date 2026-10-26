"""Use case: the packaged kind=immune check for demo_4e_cogsci_autopoiesis.

Screens the 24 pharmacy controls and the packaged replies through the OEEIS
two-signal screen and seals a receipt that `verify_receipt` replays. It does
not reimplement the pharmacy detectors, does not read historical bout,
cemetery, or formulary products, and does not claim a Phi1 reality gate.

Everything concrete (the Symbol Game fixture controls, the native pharmacy,
the screen wiring, the quarantine store, the packaged fixture replies) is
injected as a `Demo4eWiring` by the composition root
`omega_engine_epistemic_immune_system/entrypoints/demo_4e_cogsci_autopoiesis.py`.
This module imports no infrastructure.

Signal 2 comes from host checks on the payload, never from the detector's
matches, so a positive control that is well-formed JSON is DIAGNOSTIC_ONLY: a
detector match alone does not quarantine.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .policy import (
    DEMO_ID,
    SCOPE,
    DemoRefusal,
    require_cardinality,
    require_control,
)

SCHEMA = "omega.workflows.demo-4e-cogsci-autopoiesis.receipt.v1"
_RECEIPT_KEYS = {
    "schema",
    "AuthorityEffect",
    "scenario_id",
    "replies",
    "result",
    "receipt_sha256",
}


@dataclass(frozen=True, slots=True)
class Demo4eWiring:
    """The concrete collaborators the composition root injects.

    `screen_control(case, quarantine=...)` returns (finding classes, subject
    digest, screen record) for one control and raises `DemoRefusal` when its
    detector is unavailable; `screen_reply(raw, quarantine=...)` returns the
    reply record; `quarantine_factory(directory)` returns a quarantine sink;
    `packaged_replies()` returns the fixture's replies.
    """

    positive_controls: tuple[Mapping[str, Any], ...]
    negative_controls: tuple[Mapping[str, Any], ...]
    screen_control: Callable[..., tuple[tuple[str, ...], str, dict]]
    screen_reply: Callable[..., dict]
    quarantine_factory: Callable[[Path], object]
    packaged_replies: Callable[[], tuple[str, ...]]


def canonical(value: object) -> bytes:
    return (
        json.dumps(
            value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
        ).encode("ascii")
        + b"\n"
    )


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise DemoRefusal("DUPLICATE_JSON_KEY", key)
        result[key] = value
    return result


def _refuse_nonfinite(value: str) -> None:
    raise DemoRefusal("NONFINITE_JSON", value)


def load(data: bytes) -> object:
    try:
        return json.loads(data, object_pairs_hook=_pairs, parse_constant=_refuse_nonfinite)
    except DemoRefusal:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DemoRefusal("INVALID_RECEIPT_SCHEMA") from exc


def assert_output_allowed(path: Path) -> Path:
    output = Path(path).expanduser().resolve()
    if "research" in {part.casefold() for part in output.parts}:
        raise DemoRefusal("RESEARCH_EVIDENCE_WRITE_REFUSED")
    return output


def run_packaged_immune(output_dir: Path, replies: Sequence[str], *, wiring: Demo4eWiring) -> dict:
    """Screen the 24 pharmacy controls, then the replies, through the injected screen."""
    if type(wiring) is not Demo4eWiring:
        raise TypeError("wiring must be an exact Demo4eWiring")
    output = assert_output_allowed(output_dir)
    if (
        type(replies) not in (list, tuple)
        or not replies
        or any(type(item) is not str for item in replies)
    ):
        raise DemoRefusal("SCENARIO_FIXTURE_REPLIES")
    require_cardinality(len(wiring.positive_controls), len(wiring.negative_controls))
    positive_ids = {case["id"] for case in wiring.positive_controls}
    controls = wiring.positive_controls + wiring.negative_controls
    if len({case["id"] for case in controls}) != len(controls):
        raise DemoRefusal("FIXTURE_CARDINALITY", "duplicate")
    quarantine = wiring.quarantine_factory(output / "quarantine")
    cases = []
    for case in controls:
        positive = case["id"] in positive_ids
        target = case["target_class"].value if positive else None
        finding_classes, subject_digest, immune = wiring.screen_control(case, quarantine=quarantine)
        require_control(
            case["id"],
            positive=positive,
            finding_classes=finding_classes,
            target_class=target,
        )
        cases.append(
            {
                "case_id": case["id"],
                "positive": positive,
                "clean": not finding_classes,
                "target_class": target,
                "finding_classes": list(finding_classes),
                "subject_digest": subject_digest,
                "immune": immune,
            }
        )
    screens = [
        {"case_id": f"proposal-{index}", **wiring.screen_reply(reply, quarantine=quarantine)}
        for index, reply in enumerate(replies)
    ]
    return {
        "status": "CHECKED",
        "scope": SCOPE,
        "cases": cases,
        "screens": screens,
        "AuthorityEffect": "None",
    }


def seal(scenario_id: str, replies: Sequence[str], result: dict) -> dict:
    body = {
        "schema": SCHEMA,
        "AuthorityEffect": "None",
        "scenario_id": scenario_id,
        "replies": list(replies),
        "result": result,
    }
    body["receipt_sha256"] = digest(canonical(body))
    return body


def run_demo(scenario_id: str, output_dir: Path, *, wiring: Demo4eWiring) -> dict:
    if scenario_id != DEMO_ID:
        raise DemoRefusal("UNKNOWN_SCENARIO", scenario_id)
    output = assert_output_allowed(output_dir)
    if output.exists():
        raise DemoRefusal("OUTPUT_DIRECTORY_OCCUPIED", str(output))
    output.mkdir(parents=True, exist_ok=False)
    replies = wiring.packaged_replies()
    return seal(scenario_id, replies, run_packaged_immune(output, replies, wiring=wiring))


def verify_receipt(raw: bytes, *, wiring: Demo4eWiring) -> dict:
    if type(raw) is not bytes:
        raise DemoRefusal("INVALID_RECEIPT_SCHEMA")
    receipt = load(raw)
    if type(receipt) is not dict or set(receipt) != _RECEIPT_KEYS or receipt["schema"] != SCHEMA:
        raise DemoRefusal("INVALID_RECEIPT_SCHEMA")
    if receipt["AuthorityEffect"] != "None" or receipt["scenario_id"] != DEMO_ID:
        raise DemoRefusal("SCENARIO_VERSION_MISMATCH")
    if raw != canonical(receipt):
        raise DemoRefusal("NONCANONICAL_RECEIPT")
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    if digest(canonical(body)) != receipt["receipt_sha256"]:
        raise DemoRefusal("RECEIPT_DIGEST_MISMATCH")
    replies = receipt["replies"]
    if list(replies) != list(wiring.packaged_replies()):
        raise DemoRefusal("SCENARIO_FIXTURE_REPLIES")
    result = receipt["result"]
    if type(result) is not dict or result.get("status") != "CHECKED":
        raise DemoRefusal("FIXTURE_EXPECTATION_FAILED")
    with tempfile.TemporaryDirectory(prefix="demo-4e-replay-") as directory:
        replay = run_packaged_immune(Path(directory), replies, wiring=wiring)
    if replay != result:
        raise DemoRefusal("FIXTURE_REPLAY_MISMATCH")
    return {
        "status": "VERIFIED_FIXTURE",
        "reproduced": True,
        "AuthorityEffect": "None",
        "scenario_id": DEMO_ID,
    }

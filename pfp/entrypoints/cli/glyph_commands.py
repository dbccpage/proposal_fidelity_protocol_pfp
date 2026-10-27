"""CLI surface for the glyph-calculus host check.

The operator-facing end of the pipeline that WP-4, WP-5 and WP-7 built and
nothing invoked. A check reachable only from its own unit tests is not wired.

`verify-glyph-reply` reads a packet as JSON and emits the receipt, exiting on
the terminal rather than on whether the program ran:

    0  PASS                   every row re-derived, against the host's carrier
    0  SELF_CONSISTENT_ONLY   every row re-derived, against the packet's own
    0  OPEN_RESIDUAL          nothing wrong, nothing established
    2  REFUSE                 the host holds a positive objection

`SELF_CONSISTENT_ONLY` exits 0 because it is not an objection -- the rows really
do re-derive. It is a weaker claim than `PASS`, and the way to earn `PASS` is
`--carrier`: pass the allowlist the HOST pins and the run stops checking the
packet against a carrier the packet wrote. A packet declaring some other carrier
is then refused, not quietly checked against its own.

An unparseable packet or a missing file exits 2 as well, because a run that
could not read its input has established nothing either. Exit 1 is reserved for
the program itself failing, which is a different claim.

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ...domain.calculus_receipt import Terminal
from ...domain.glyph_calculus import Carrier
from ...domain.presentation_pins import PresentationPins
from ...use_cases.verify_glyph_reply import verify_glyph_reply

__all__ = ["cmd_verify_glyph_reply", "register_glyph_subparsers"]

_REFUSING_EXIT = 2

#: The fields a carrier pin file may declare. Same rule as the packet: an
#: unrecognised field is refused rather than ignored.
_PIN_FIELDS = ("schema", "authority_effect", "doctrine", "carrier")
_PIN_SCHEMA = "core.glyph_carrier_pin.v1"

_PRESENTATION_PIN_FIELDS = ("schema", "authority_effect", "doctrine", "pins")
_PRESENTATION_PIN_SCHEMA = "core.symbol_game.presentation_pins.v1"


def _load_host_presentations(path: Path) -> tuple[PresentationPins | None, str | None]:
    """Read the presentations this host pins, or say why it could not.

    Fatal on every failure, like the carrier pin and for the same reason: an
    operator who asked the host to resolve `presentation_ref` and silently got
    a run where every such row was UNCHECKABLE has been told something false
    about their run.
    """
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return None, f"presentation pins {path}: {error}"
    if not isinstance(body, dict):
        return None, f"presentation pins {path}: must be a JSON object"
    unknown = sorted(set(body) - set(_PRESENTATION_PIN_FIELDS))
    if unknown:
        return None, f"presentation pins {path}: undeclared fields {unknown}"
    if body.get("schema") != _PRESENTATION_PIN_SCHEMA:
        return None, (
            f"presentation pins {path}: declares schema {body.get('schema')!r}, "
            f"expected {_PRESENTATION_PIN_SCHEMA!r}"
        )
    pins = body.get("pins")
    if not isinstance(pins, list):
        return None, f"presentation pins {path}: declares no pins list"
    try:
        return PresentationPins.from_wire(pins), None
    except ValueError as error:
        return None, f"presentation pins {path}: {error}"


def _load_host_carrier(path: Path) -> tuple[Carrier | None, str | None]:
    """Read the carrier this host pins, or say why it could not.

    Every failure here is fatal rather than a fallback to the packet's own
    carrier. An operator who asked for verification and silently received a
    consistency check has been told something false about their run, which is
    worse than being told the file is unreadable.
    """
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return None, f"carrier pin {path}: {error}"
    if not isinstance(body, dict):
        return None, f"carrier pin {path}: must be a JSON object"
    unknown = sorted(set(body) - set(_PIN_FIELDS))
    if unknown:
        return None, f"carrier pin {path}: undeclared fields {unknown}"
    if body.get("schema") != _PIN_SCHEMA:
        return None, (
            f"carrier pin {path}: declares schema {body.get('schema')!r}, "
            f"expected {_PIN_SCHEMA!r}"
        )
    members = body.get("carrier")
    if not isinstance(members, list):
        return None, f"carrier pin {path}: declares no carrier list"
    try:
        return Carrier.from_wire(members), None
    except ValueError as error:
        return None, f"carrier pin {path}: {error}"


def cmd_verify_glyph_reply(args: argparse.Namespace) -> int:
    host_carrier = None
    if getattr(args, "carrier", None):
        host_carrier, error = _load_host_carrier(Path(args.carrier))
        if error is not None:
            print(json.dumps({"terminal_status": "REFUSE", "error": error}))
            return _REFUSING_EXIT

    host_presentations = None
    if getattr(args, "presentations", None):
        host_presentations, error = _load_host_presentations(Path(args.presentations))
        if error is not None:
            print(json.dumps({"terminal_status": "REFUSE", "error": error}))
            return _REFUSING_EXIT

    path = Path(args.packet)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        print(json.dumps({"terminal_status": "REFUSE", "error": str(error)}))
        return _REFUSING_EXIT

    # Duplicate keys are only visible before a mapping collapses them, so the
    # pairs are captured on the way in rather than reconstructed after.
    #
    # The hook fires for EVERY object in the document, not just the outermost.
    # Accumulating across all of them reports the carrier members' repeated
    # `symbol` keys as duplicates and refuses every well-formed packet. Each
    # object's pairs are kept separately and the last one is the top level,
    # because an outer object cannot complete before its children.
    objects: list[list[tuple[str, object]]] = []

    def capture(items: list[tuple[str, object]]) -> dict[str, object]:
        objects.append(list(items))
        return dict(items)

    try:
        packet = json.loads(text, object_pairs_hook=capture)
    except json.JSONDecodeError as error:
        print(json.dumps({"terminal_status": "REFUSE", "error": str(error)}))
        return _REFUSING_EXIT

    if not isinstance(packet, dict):
        print(
            json.dumps(
                {"terminal_status": "REFUSE", "error": "packet must be a JSON object"}
            )
        )
        return _REFUSING_EXIT

    top_level = objects[-1] if objects else []
    verdict = verify_glyph_reply(
        packet,
        host_carrier=host_carrier,
        host_presentations=host_presentations,
        packet_pairs=top_level,
    )
    print(json.dumps(verdict.to_wire(), indent=2, sort_keys=True, ensure_ascii=True))
    return _REFUSING_EXIT if verdict.terminal is Terminal.REFUSE else 0

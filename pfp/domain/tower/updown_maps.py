"""The one proven Up/Down context-map pair: MSS-0 <-> MSS-1.

AuthorityEffect: None.

Source: mss_n_grammar_000.md section 12.3. This module implements exactly the
one transition the spec actually specifies in detail (`u_0`/`d_1`); it makes
no claim about a general `u_n`/`d_n` family for arbitrary n -- doc section 12
itself only sketches the general nine-property requirement for "a later
lift", it does not construct one past MSS-1.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import grammar
from .grammar import Packet

__all__ = ["NonDescentReceipt", "u_0", "d_1"]


@dataclass(frozen=True)
class NonDescentReceipt:
    """A typed record that `original` does not descend to the lower context.

    Doc section 18, obligation 13: "new structure cannot silently descend as
    old structure." Simply returning `Diff()` (the MSS-0 base case) for every
    genuinely-new MSS-1 term would risk exactly that failure -- a caller
    could not tell "this really was the base distinction" apart from "this
    was new structure quietly coerced to look like the base distinction."
    An explicit, distinguishable receipt object makes the refusal visible
    and inspectable instead.
    """

    original: Packet


def u_0(packet: Packet) -> Packet:
    """The Up-Lift embedding MSS-0 -> MSS-1 (doc section 12.3: `u_n` is
    injective and preserves every old legal packet and every old
    distinction). At MSS-0 the only legal packet is the bare genesis
    distinction; calling this on anything else is a precondition violation,
    raised explicitly rather than silently embedding an illegal MSS-0 term.
    """
    if not grammar.is_active_at_level(packet, level=0):
        raise ValueError(
            f"u_0 requires a level-0-active packet; "
            f"{grammar.serialize(packet)!r} is not level-0-active"
        )
    return packet


def d_1(packet: Packet) -> Packet | NonDescentReceipt:
    """The Down/forgetful map MSS-1 -> MSS-0 (doc section 12.3).

    Identity on the old context: for any packet that is itself
    level-0-active, `d_1` returns it unchanged -- this is what makes
    `d_1(u_0(x)) == x` hold for every legal MSS-0 packet `x` (tested
    directly in tests/test_mssn_updown_and_cells.py). On genuinely new
    MSS-1-only structure, returns an explicit `NonDescentReceipt` rather
    than silently coercing to the base distinction (see
    `NonDescentReceipt`'s docstring).
    """
    if grammar.is_active_at_level(packet, level=0):
        return packet
    return NonDescentReceipt(original=packet)

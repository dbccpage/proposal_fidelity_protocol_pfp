"""The canonical Grammar-000 corpus, transcribed verbatim from the source spec.

AuthorityEffect: None.

Source (real, on disk, read in full for this transcription):
    genesis/008_mssn_s_n_symbol_game_recovery/code/python/_docs/_the_symbol_game_history/
    mss_n_grammar_000.md

This is the single source of truth both N1's notebook demo and
tests/test_mssn_grammar.py import from, so the notebook and the test can never
silently drift apart from each other -- only from the source doc itself, which is
why every string here is a direct, uncommented transcription (no paraphrase) of
the doc's own examples.

VALID / INVALID -- doc section 17, "Canonical MSS-1 test corpus".
MSS0_FORBIDDEN -- doc section 3.3, "Forbidden MSS-0 imports". Note (worth teaching
    explicitly, see N0): all three forbidden-at-MSS-0 packets are drawn *verbatim*
    from VALID -- they are syntactically legal Grammar-000 packets. What makes them
    forbidden is not syntax; it is that MSS-0's *active alphabet is empty* (no atom
    is legal yet, only the bare genesis distinction `<>`). Syntax validity and
    level-activation are orthogonal checks -- this corpus is the proof of that, not
    an assertion of it.
CANONICAL_SEQUENCE -- doc section 19, "First canonical sequence": the smallest
    coherent route from Primitive Difference through a binary graph, an explicit
    obstruction, and valid metric simplices through dimension 3.
"""

from __future__ import annotations

# --- Section 17: Canonical MSS-1 test corpus ---------------------------------

VALID: tuple[str, ...] = (
    "<>",
    "op<<0><><0><1>>",
    "<0>",
    "<1>",
    "<101>",
    "op<<1><0>>",
    "op<<10><0><1>>",
    "op<<11>op<<1><0>>op<<1><1>>op<<10><0><1>>>",
    "op<<100><>op<<10><0><1>>>",
    "op<<101><10><0><1><10>>",
    "op<<111>op<<101><10><0><1><10>>op<<110><0><1><1>>op<<110><0><10><1>>op<<110><1><10><1>>>",
)

# Each entry: (packet text, the doc's own one-line stated reason). The doc's
# reason is documentation of what the *source* calls the defect; our own parser's
# raised GrammarError.reason is not forced to match this string verbatim (a
# mechanical parser fails at its own first point of contact, which is not always
# phrased the way a human skimming the string would phrase it) -- see
# grammar000.py's module docstring and N1's notebook for where the two agree and
# where they legitimately differ in wording without disagreeing on validity.
INVALID: tuple[tuple[str, str], ...] = (
    ("<a,b>", "comma"),
    ("a>b", "arrow"),
    ("op<0,1>", "comma"),
    ("op<<1>0>", "unwrapped child"),
    ("op<<10><0><1>", "unclosed application"),
    ("op<<101><2><0><1><10>>", "inactive decimal glyph 2 in strict MSS1 data mode"),
)

# --- Section 3.3: Forbidden MSS-0 imports ------------------------------------
# All three are verbatim members of VALID above (see module docstring).

MSS0_FORBIDDEN: tuple[str, ...] = (
    "op<<1><0>>",
    "op<<10><0><1>>",
    "op<<101><10><0><1><10>>",
)

# --- Section 19: First canonical sequence ------------------------------------

CANONICAL_SEQUENCE: tuple[str, ...] = (
    "<>",
    "op<<0><><0><1>>",
    "op<<11>op<<1><0>>op<<1><1>>op<<10><0><1>>>",
    "op<<11>op<<1><0>>op<<1><1>>op<<100><>op<<10><0><1>>>>",
    "op<<101><0><0>>",
    "op<<101><1><0><1>>",
    "op<<101><10><0><1><10>>",
    "op<<101><11><0><1><10><11>>",
    "op<<111>op<<101><11><0><1><10><11>>op<<110><0><1><1>>op<<110><0><10><1>>"
    "op<<110><0><11><1>>op<<110><1><10><1>>op<<110><1><11><1>>op<<110><10><11><1>>>",
)

# --- Section 11: the exact 2D Regge deficit fixture --------------------------
# Glue five equilateral 2-simplices around vertex <0>: full turn 6, angle sum 5,
# deficit 1, dimension 2 -- all in binary. Used by N5 and by test_mssn_regge_exact.

DEFICIT_RECEIPT_2D: str = "op<<1010><10>op<<1><0>><110><101><1>>"
DEFICIT_2D_FULL_TURN_SIXTHS = 6
DEFICIT_2D_ANGLE_SUM_SIXTHS = 5
DEFICIT_2D_DEFICIT_SIXTHS = 1

# --- Section 1.2: the wire alphabet ------------------------------------------

SIGMA_36: frozenset[str] = frozenset("0123456789abcdefghijklmnopqrstuvwxyz")
GAMMA_38: frozenset[str] = SIGMA_36 | {"<", ">"}

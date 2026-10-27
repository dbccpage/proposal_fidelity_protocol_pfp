"""Loading a pinned target checker and running it.

AuthorityEffect: None.

A target checker is one self-contained Python source file, pinned by commit,
path and SHA-256. It is executed from its pinned bytes, never imported from the
working tree, and may import only the standard-library modules listed in
``ALLOWED_IMPORTS``: anything else would be unpinned code deciding a verdict.
The import rule enforces pinning; it is not a sandbox. Checkers of record are
this repository's own reviewed code, and no carrier-supplied code is executed.

The module must define:

- ``STAGE``: the level it decides (int);
- ``ROW_SHA256``: the ``stages.tsv`` row digest it is bound to. The reach
  checker refuses a checker whose row digest is not its level's (``RR-PIN``);
- ``CODES``: its closed refusal-code registry (tuple of str), which includes
  ``R_EMPTY_INPUT`` and ``R_VERDICT_FIELD``;
- ``OWN_NEGATIVE`` and ``OWN_NEGATIVE_CODE``: the level's own negative
  instance, built by the target, and the code that refuses it;
- ``STRUCTURE_MAPS``: the structure maps the level's obligation names (a tuple;
  empty when it names none). Transport criterion 3 cannot be N/A otherwise;
- ``check(payload) -> tuple[str, str | None]``: ``("PASS", None)`` or
  ``("REFUSED", code)``. Pure: no I/O.
"""

from __future__ import annotations

import builtins
import re
import types
from typing import Any, Callable

# ``hashlib`` and ``json`` are pure standard library; a checker whose obligation is
# a digest over canonical bytes (stages 12, 15, 17) needs both.
ALLOWED_IMPORTS = frozenset(
    {
        "__future__",
        "collections",
        "fractions",
        "functools",
        "hashlib",
        "itertools",
        "json",
        "math",
        "re",
        "string",
        "typing",
    }
)

# Verdict-bearing names (W2-C05 section 6.1): such a field in a payload makes
# it flag-only. Matched on whole keys, case-insensitively.
VERDICT_KEY_RE = re.compile(
    r"^(is_.*|has_.*|.*_verified|.*_residual|.*_anticommute|verified|passes|passed|valid|ok|"
    r"accepted|verdict|outcome|grade|status|differential_squared|certified|proved)$",
    re.IGNORECASE,
)

REQUIRED_ATTRIBUTES = ("STAGE", "ROW_SHA256", "CODES", "OWN_NEGATIVE", "OWN_NEGATIVE_CODE", "STRUCTURE_MAPS", "check")

# A probe equal to the positive cannot be expected refused: refusing it would
# refuse the witness itself. It is marked inapplicable, never run, and never
# counted as a hollow-checker finding. (Level 000's packet has no list, so
# ``lists_emptied`` returns it unchanged.)
PROBE_INAPPLICABLE = "PROBE-IDENTICAL-TO-POSITIVE"


class CheckerLoadError(RuntimeError):
    pass


def _restricted_import(
    name: str,
    globals_: Any = None,
    locals_: Any = None,
    fromlist: Any = (),
    level: int = 0,
) -> Any:
    root = name.split(".")[0]
    if level != 0 or root not in ALLOWED_IMPORTS:
        raise ImportError(f"pinned checker may not import {name!r}")
    return builtins.__import__(name, globals_, locals_, fromlist, level)


def load_checker(source: bytes, name: str) -> types.ModuleType:
    """Execute a checker from its pinned bytes in a fresh module."""
    from pfp.infrastructure.adapters.mssn_research.checkers.assemble import (
        assemble_checker_source,
    )

    source = assemble_checker_source(source)
    module = types.ModuleType(f"pinned_checker_{name}")
    namespace_builtins = dict(builtins.__dict__)
    namespace_builtins["__import__"] = _restricted_import
    module.__dict__["__builtins__"] = namespace_builtins
    try:
        code = compile(source.decode("utf-8"), f"<pinned checker {name}>", "exec")
        exec(code, module.__dict__)
    except Exception as exc:  # the checker is untrusted input
        raise CheckerLoadError(f"checker {name} does not load: {type(exc).__name__}: {exc}") from None
    missing = [attr for attr in REQUIRED_ATTRIBUTES if not hasattr(module, attr)]
    if missing:
        raise CheckerLoadError(f"checker {name} lacks {missing}")
    return module


def run(check: Callable[[Any], Any], payload: Any, codes: tuple[str, ...]) -> tuple[str, str | None]:
    """Run one fixture. An exception is a kept REFUSED row, never a dropped one."""
    try:
        result = check(payload)
    except Exception as exc:
        return ("REFUSED", f"R_EXCEPTION:{type(exc).__name__}")
    if (
        not isinstance(result, tuple)
        or len(result) != 2
        or result[0] not in ("PASS", "REFUSED")
        or (result[0] == "PASS" and result[1] is not None)
        or (result[0] == "REFUSED" and result[1] not in codes)
    ):
        return ("REFUSED", "R_MALFORMED_VERDICT")
    return (result[0], result[1])


def leaves(value: Any) -> list[Any]:
    if isinstance(value, dict):
        return [leaf for item in value.values() for leaf in leaves(item)]
    if isinstance(value, list):
        return [leaf for item in value for leaf in leaves(item)]
    return [value]


def keys(value: Any) -> list[str]:
    if isinstance(value, dict):
        return [key for key in value] + [k for item in value.values() for k in keys(item)]
    if isinstance(value, list):
        return [k for item in value for k in keys(item)]
    return []


def is_empty_payload(payload: Any) -> bool:
    """No primitive datum: only empty containers, nulls and empty strings."""
    return not any(leaf is not None and leaf != "" for leaf in leaves(payload))


def is_flag_only(payload: Any) -> bool:
    """A verdict-named key anywhere, or every datum a boolean."""
    if any(VERDICT_KEY_RE.match(key) for key in keys(payload)):
        return True
    data = [leaf for leaf in leaves(payload) if leaf is not None]
    return bool(data) and all(isinstance(leaf, bool) for leaf in data)


def _emptied(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _emptied(item) for key, item in value.items()}
    if isinstance(value, list):
        return []
    return value


def _flagged(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _flagged(item) for key, item in value.items()}
    return True


def probe_battery(positive: Any) -> list[tuple[str, Any, str]]:
    """The checker's own empty and flag-only probes (W2-C04 AS01).

    Built by the receiving side from the positive payload, never supplied by
    the producer. Each entry is (probe id, payload, expected code). A probe
    whose payload equals the positive carries ``PROBE_INAPPLICABLE`` as its
    expected code: it cannot be refused without refusing the witness.
    """
    battery: list[tuple[str, Any, str]] = [
        ("empty_object", {}, "R_EMPTY_INPUT"),
        ("empty_list", [], "R_EMPTY_INPUT"),
        ("null", None, "R_EMPTY_INPUT"),
        ("lists_emptied", _emptied(positive), "R_EMPTY_INPUT"),
        ("flags_for_data", _flagged(positive), "R_VERDICT_FIELD"),
        ("verdict_only", {"verified": True}, "R_VERDICT_FIELD"),
    ]
    if isinstance(positive, dict):
        with_flag = dict(positive)
        with_flag["verified"] = True
        battery.append(("data_plus_verdict", with_flag, "R_VERDICT_FIELD"))
    return [
        (probe, payload, PROBE_INAPPLICABLE if same_payload(payload, positive) else expected)
        for probe, payload, expected in battery
    ]


def same_payload(a: Any, b: Any) -> bool:
    """Equal as JSON values: same types (a boolean is not an integer), same shape."""
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(same_payload(a[key], b[key]) for key in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same_payload(x, y) for x, y in zip(a, b))
    return type(a) is type(b) and a == b


def edit_count(a: Any, b: Any) -> int:
    """Edits between two JSON values; lists differing by one insertion count 1."""
    if isinstance(a, dict) and isinstance(b, dict):
        return sum(edit_count(a.get(key), b.get(key)) if key in a and key in b else 1 for key in set(a) | set(b))
    if isinstance(a, list) and isinstance(b, list):
        if len(a) == len(b):
            return sum(edit_count(x, y) for x, y in zip(a, b))
        longer, shorter = (a, b) if len(a) > len(b) else (b, a)
        if len(longer) - len(shorter) == 1:
            for index in range(len(longer)):
                if longer[:index] + longer[index + 1 :] == shorter:
                    return 1
        return 2
    if type(a) is not type(b):
        return 1
    return 0 if a == b else 1

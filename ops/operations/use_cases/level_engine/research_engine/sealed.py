# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Read-only access to the vendored sealed code.

The explicitly pinned clone is loaded through a scoped module finder; nothing is copied or modified.  Loading any path under
``research/second`` is refused (the embargo, item 6).

AuthorityEffect: None
"""

from __future__ import annotations

import posixpath
from pathlib import Path

from typing import TYPE_CHECKING

from operations.domain.level_engine_context import (
    current_context,
    vendor_import_scope,
)

if TYPE_CHECKING:
    from derivation import iso as sealed_iso
    from derivation import observe as sealed_observe
    from derivation.candidates import (
        Bounds,
        Delta,
        Item,
        NewDatum,
        NewForm,
        NewInst,
        NewRuleAll,
        apply_delta,
        canonical_delta,
        delta_events,
        item_key,
        mu2,
    )
    from derivation.model import (
        EMPTY,
        AdmissionError,
        AdmitDatum,
        AdmitForm,
        AdmitInst,
        AdmitRuleAll,
        Event,
        Impose,
        Regime,
        Supply,
        replay,
        step,
    )

from .errors import EmbargoRefusal, Refusal

ROOT = current_context().runtime_root


class _LazyVendor:
    """The pinned clone is resolved on use, not when this module is imported."""

    def _path(self) -> Path:
        return current_context().require_vendor()

    def __truediv__(self, other: str | Path) -> Path:
        return self._path().joinpath(other)

    def __fspath__(self) -> str:
        return self._path().__fspath__()

    def __str__(self) -> str:
        return str(self._path())

    def __repr__(self) -> str:
        return repr(self._path())

    def __getattr__(self, name: str) -> object:
        return getattr(self._path(), name)


VENDOR = _LazyVendor()


def vendored(rel: str) -> Path:
    """A path inside the vendored clone.  Refuses the second derivation's
    trees before anything is read.

    The path is normalised first, and one that is absolute or climbs out
    with ``..`` is refused (``RR-VENDOR-PATH``): the embargo is a prefix
    check, so ``research/<tree>/../second/...`` would otherwise pass it."""
    raw = rel.replace("\\", "/")
    norm = posixpath.normpath(raw) if raw else "."
    parts = norm.split("/")
    if raw.startswith("/") or ".." in parts or ":" in parts[0]:
        raise Refusal("RR-VENDOR-PATH", f"{rel!r} is not a path inside the vendored clone")
    norm = "" if norm == "." else norm
    if norm.startswith("research/second"):
        raise EmbargoRefusal("GUARD_EMBARGO", "loading research/second* state is embargoed")
    return VENDOR / norm


_SEALED_READY = False
_LOADING = False


def _load_sealed_symbols() -> None:
    global _SEALED_READY, _LOADING
    if _SEALED_READY:
        return
    if _LOADING:
        raise AttributeError("sealed symbols are still loading")
    _LOADING = True
    try:
        scope = vendor_import_scope()
        with scope(vendored("code"), vendored("research/partial_decide")):
            from derivation import iso as sealed_iso
            from derivation import observe as sealed_observe
            from derivation.candidates import (
                Bounds,
                Delta,
                Item,
                NewDatum,
                NewForm,
                NewInst,
                NewRuleAll,
                apply_delta,
                canonical_delta,
                delta_events,
                item_key,
                mu2,
            )
            from derivation.model import (
                EMPTY,
                AdmissionError,
                AdmitDatum,
                AdmitForm,
                AdmitInst,
                AdmitRuleAll,
                Event,
                Impose,
                Regime,
                Supply,
                replay,
                step,
            )
        globals().update({
            "AdmissionError": AdmissionError,
            "AdmitDatum": AdmitDatum,
            "AdmitForm": AdmitForm,
            "AdmitInst": AdmitInst,
            "AdmitRuleAll": AdmitRuleAll,
            "Bounds": Bounds,
            "Delta": Delta,
            "EMPTY": EMPTY,
            "Event": Event,
            "Impose": Impose,
            "Item": Item,
            "NewDatum": NewDatum,
            "NewForm": NewForm,
            "NewInst": NewInst,
            "NewRuleAll": NewRuleAll,
            "Regime": Regime,
            "Supply": Supply,
            "apply_delta": apply_delta,
            "canonical_delta": canonical_delta,
            "delta_events": delta_events,
            "item_key": item_key,
            "mu2": mu2,
            "replay": replay,
            "sealed_iso": sealed_iso,
            "sealed_observe": sealed_observe,
            "step": step,
        })
        _SEALED_READY = True
    finally:
        _LOADING = False


def _real_sealed(name: str) -> object:
    if not _SEALED_READY:
        _load_sealed_symbols()
    found = globals()[name]
    if type(found) is _LazySymbol:
        raise AttributeError(name)
    return found


class _LazySymbol(type):
    """Stand-in so importing a sealed name does not load the pinned vendor."""

    def __call__(cls, *args: object, **kwargs: object) -> object:
        real = _real_sealed(cls.__name__)
        if not callable(real):
            raise TypeError(f"{cls.__name__} is not callable")
        return real(*args, **kwargs)

    def __instancecheck__(cls, instance: object) -> bool:
        real = _real_sealed(cls.__name__)
        if not isinstance(real, type):
            return False
        return isinstance(instance, real)

    def __subclasscheck__(cls, subclass: type) -> bool:
        real = _real_sealed(cls.__name__)
        if not isinstance(real, type):
            return False
        return issubclass(subclass, real)

    def __getattr__(cls, name: str) -> object:
        if name.startswith("__") and not _SEALED_READY:
            raise AttributeError(name)
        return getattr(_real_sealed(cls.__name__), name)


def _install_lazy_symbols() -> None:
    names = (
        "AdmissionError",
        "AdmitDatum",
        "AdmitForm",
        "AdmitInst",
        "AdmitRuleAll",
        "Bounds",
        "Delta",
        "Event",
        "Impose",
        "Item",
        "NewDatum",
        "NewForm",
        "NewInst",
        "NewRuleAll",
        "Regime",
        "Supply",
        "apply_delta",
        "canonical_delta",
        "delta_events",
        "item_key",
        "mu2",
        "replay",
        "sealed_iso",
        "sealed_observe",
        "step",
    )
    for name in names:
        globals()[name] = _LazySymbol(name, (), {})


_install_lazy_symbols()


def admission_error_type() -> type[BaseException]:
    """The vendored admission exception. An imported stand-in cannot catch it."""
    found = _real_sealed("AdmissionError")
    if not isinstance(found, type) or not issubclass(found, BaseException):
        raise TypeError("sealed AdmissionError is not an exception class")
    return found


def __getattr__(name: str) -> object:
    if name.startswith("_") or _LOADING:
        raise AttributeError(name)
    _load_sealed_symbols()
    try:
        return globals()[name]
    except KeyError as exc:
        raise AttributeError(name) from exc

__all__ = [
    "AdmissionError",
    "AdmitDatum",
    "AdmitForm",
    "AdmitInst",
    "AdmitRuleAll",
    "Bounds",
    "Delta",
    "EMPTY",
    "Event",
    "Impose",
    "Item",
    "NewDatum",
    "NewForm",
    "NewInst",
    "NewRuleAll",
    "Regime",
    "Supply",
    "VENDOR",
    "admission_error_type",
    "apply_delta",
    "canonical_delta",
    "delta_events",
    "item_key",
    "mu2",
    "replay",
    "sealed_iso",
    "sealed_observe",
    "step",
    "vendored",
]

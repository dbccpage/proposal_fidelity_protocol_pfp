"""Dispatch a normal-form id to its bound check and map the local route.

S(n) forms stay in ``sn_forms``. ``nf.physics.rpcnf`` is bound here.

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any, Callable

import yaml

from omega_engine_pfp.infrastructure.normal_forms.contract_paths import NORMAL_FORMS_DIR

RPCNF_ID = "nf.physics.rpcnf"
_DEFAULT_KEY = ("phi0", "phi1", "phi2", "phi3")
_BARE_CHART_COORDINATES = frozenset({"x0", "x1", "x2", "x3", "t", "x", "y", "z"})
Atom = Fraction | str | int
Row = dict[str, Atom]
Form = Callable[[dict[str, Any], dict[str, str] | None], dict[str, Any]]


def _sn_form_table() -> dict[str, Form]:
    from omega_engine_pfp.infrastructure.normal_forms.sn_forms import evaluate_sn_pdnf
    from omega_engine_pfp.infrastructure.normal_forms.sn_forms import evaluate_sn_pvnf
    from omega_engine_pfp.infrastructure.normal_forms.sn_forms import evaluate_sn_rpnf
    from omega_engine_pfp.infrastructure.normal_forms.sn_forms import evaluate_sn_scnf
    from omega_engine_pfp.infrastructure.normal_forms.sn_forms import evaluate_sn_state

    return {
        "nf.derivation.pdnf": evaluate_sn_pdnf,
        "pdnf": evaluate_sn_pdnf,
        "nf.derivation.rpnf": evaluate_sn_rpnf,
        "rpnf": evaluate_sn_rpnf,
        "nf.derivation.scnf": evaluate_sn_scnf,
        "scnf": evaluate_sn_scnf,
        "nf.epistemic.state": evaluate_sn_state,
        "state": evaluate_sn_state,
        "nf.epistemic.pvnf": evaluate_sn_pvnf,
        "pvnf": evaluate_sn_pvnf,
    }


def _lookup_form(contract_id: str) -> Form | None:
    if contract_id == RPCNF_ID:
        return evaluate_rpcnf
    return _sn_form_table().get(contract_id)


def checker_for(contract_id: str) -> Form:
    """Return the check function the normal-form id calls."""
    form = _lookup_form(contract_id)
    if form is None:
        raise KeyError(contract_id)
    return form


def resolve_contract(contract_id: str, contract_path: Path | None = None) -> dict[str, Any]:
    """Load one contract: an explicit file, otherwise `{id}.yaml` in the declared resource catalog."""
    if contract_path is not None and Path(contract_path).is_file():
        target = Path(contract_path)
    else:
        target = NORMAL_FORMS_DIR / f"{contract_id}.yaml"
        if not target.is_file():
            raise FileNotFoundError(f"Cannot resolve contract YAML for {contract_id}")
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Contract {target} does not parse to a dictionary")
    return data


def evaluate_sn_transition(
    contract_id: str,
    fixture: dict[str, Any],
    contract_path: Path | None = None,
) -> dict[str, Any]:
    """Run the check bound to ``contract_id`` and admit only the canonical Preserve route."""
    contract = resolve_contract(contract_id, contract_path)
    terminal_routes = contract.get("terminal_routes", [])
    terminal_route_map = contract.get("terminal_route_map", {})
    cid = contract.get("identity", {}).get("id", contract_id)
    try:
        form = checker_for(cid)
    except KeyError:
        raise ValueError(f"Unsupported S(n) normal form contract: {cid}") from None
    result = form(fixture, terminal_route_map)
    local_route = result["local_terminal"]
    if local_route not in terminal_routes:
        raise ValueError(
            f"Evaluator returned route '{local_route}' not declared in terminal_routes: {terminal_routes}"
        )
    if local_route not in terminal_route_map:
        raise ValueError(
            f"Local route '{local_route}' not mapped in terminal_route_map: {terminal_route_map}"
        )
    canonical_route = terminal_route_map[local_route]
    result["contract_id"] = cid
    result["canonical_terminal"] = canonical_route
    result["terminal_route_map"] = terminal_route_map
    result["admitted"] = canonical_route == "Preserve"
    return result


def evaluate_sn_state_transition(
    contract_id: str,
    fixture: dict[str, Any],
    contract_path: Path | None = None,
) -> dict[str, Any]:
    """Open an in-memory session, evaluate one transition, and close it."""
    from omega_engine_pfp.infrastructure.normal_forms.evaluator import (
        NormalFormsEvaluator,
    )

    evaluator = NormalFormsEvaluator(in_memory=True)
    try:
        return evaluator.evaluate_sn_transition(contract_id, fixture, contract_path)
    finally:
        evaluator.close()


def _atom(value: object) -> Atom:
    if isinstance(value, bool) or isinstance(value, float):
        raise TypeError(f"inexact atom refused: {value!r}")
    if isinstance(value, Fraction) or isinstance(value, str):
        return value
    if isinstance(value, int):
        return Fraction(value)
    raise TypeError(f"atom must be a Fraction, an int, or a str: {value!r}")


def _parse_rows(fixture: dict[str, Any]) -> list[Row]:
    raw = fixture.get("rows")
    if not isinstance(raw, list) or not raw:
        raise ValueError("rows must be a non-empty list")
    parsed: list[Row] = []
    for row in raw:
        if not isinstance(row, dict) or not row:
            raise ValueError("each row must be a non-empty attribute mapping")
        parsed.append({str(name): _atom(value) for name, value in row.items()})
    headings = {tuple(sorted(row)) for row in parsed}
    if len(headings) != 1:
        raise ValueError("rows must share one attribute set")
    return parsed


def _key_of(fixture: dict[str, Any]) -> tuple[str, ...]:
    raw = fixture.get("key", fixture.get("K", _DEFAULT_KEY))
    if isinstance(raw, str) or not isinstance(raw, (list, tuple)) or not raw:
        raise ValueError("key K must be a non-empty list of attribute names")
    key = tuple(str(name) for name in raw)
    if len(set(key)) != len(key):
        raise ValueError("key K contains a duplicate attribute")
    return key


def _project(rows: list[Row], attrs: tuple[str, ...]) -> set[tuple[Atom, ...]]:
    return {tuple(row[name] for name in attrs) for row in rows}


def _natural_join(
    left: set[tuple[Atom, ...]],
    left_attrs: tuple[str, ...],
    right: set[tuple[Atom, ...]],
    right_attrs: tuple[str, ...],
    heading: tuple[str, ...],
) -> set[tuple[Atom, ...]]:
    common = tuple(name for name in left_attrs if name in set(right_attrs))
    left_index = [left_attrs.index(name) for name in common]
    right_index = [right_attrs.index(name) for name in common]
    joined: set[tuple[Atom, ...]] = set()
    for left_row in left:
        for right_row in right:
            if all(left_row[i] == right_row[j] for i, j in zip(left_index, right_index)):
                merged = dict(zip(left_attrs, left_row))
                merged.update(zip(right_attrs, right_row))
                joined.add(tuple(merged[name] for name in heading))
    return joined


def _heath_lossless(rows: list[Row], heading: tuple[str, ...], key: tuple[str, ...]) -> bool:
    """Heath: K -> U makes pi_{K union A}(R) join pi_{K union B}(R) equal R."""
    nonkey = tuple(name for name in heading if name not in set(key))
    determined = (nonkey[0],) if nonkey else ()
    rest = nonkey[1:]
    left_attrs = tuple(sorted(set(key) | set(determined)))
    right_attrs = tuple(sorted(set(key) | set(rest)))
    joined = _natural_join(
        _project(rows, left_attrs),
        left_attrs,
        _project(rows, right_attrs),
        right_attrs,
        heading,
    )
    original = _project(rows, heading)
    return joined == original


def _functionally_determines(rows: list[Row], attrs: tuple[str, ...]) -> bool:
    heading = tuple(sorted(rows[0]))
    seen: dict[tuple[Atom, ...], tuple[Atom, ...]] = {}
    for row in rows:
        key_value = tuple(row[name] for name in attrs)
        attributes = tuple(row[name] for name in heading)
        previous = seen.get(key_value)
        if previous is not None and previous != attributes:
            return False
        seen[key_value] = attributes
    return True


def _key_is_minimal(rows: list[Row], key: tuple[str, ...]) -> bool:
    """No proper subset of K determines the relation. Dropping one attribute is enough."""
    names = list(key)
    for index in range(len(names)):
        subset = tuple(names[:index] + names[index + 1 :])
        if _functionally_determines(rows, subset):
            return False
    return True


def _route(local_terminal: str, reason: str, *, admitted: bool) -> dict[str, Any]:
    return {
        "contract_id": RPCNF_ID,
        "local_terminal": local_terminal,
        "reason": reason,
        "admitted": admitted,
    }


def evaluate_rpcnf(
    fixture: dict[str, Any],
    route_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Admit a relation whose candidate key K determines U and whose join is lossless.

    A row that carries chart coordinates and no relational key is refused.
    This check does not solve the Einstein equations or quantum gravity.
    """
    del route_map
    try:
        rows = _parse_rows(fixture)
        key = _key_of(fixture)
    except (TypeError, ValueError) as exc:
        return _route("Unsupported", str(exc), admitted=False)
    heading = tuple(sorted(rows[0]))
    bare = [name for name in heading if name in _BARE_CHART_COORDINATES]
    missing_key = [name for name in key if name not in heading]
    if bare and missing_key:
        return _route(
            "BareCoordinateContamination",
            "chart coordinates are present and relational key K is absent",
            admitted=False,
        )
    if bare:
        return _route(
            "BareCoordinateContamination",
            "bare chart coordinates are not attributes of U",
            admitted=False,
        )
    if missing_key:
        return _route(
            "NonKeyCoincidenceViolation",
            "candidate key K is not contained in U",
            admitted=False,
        )
    seen: dict[tuple[Atom, ...], tuple[Atom, ...]] = {}
    for row in rows:
        key_value = tuple(row[name] for name in key)
        attributes = tuple(row[name] for name in heading)
        previous = seen.get(key_value)
        if previous is not None and previous != attributes:
            return _route(
                "NonKeyCoincidenceViolation",
                "functional dependency K -> U fails",
                admitted=False,
            )
        seen[key_value] = attributes
    if not _heath_lossless(rows, heading, key):
        return _route(
            "LossyObserverDecomposition",
            "Heath join on K does not recover the relation",
            admitted=False,
        )
    if set(key) != set(_DEFAULT_KEY):
        return _route(
            "NonKeyCoincidenceViolation",
            "candidate key K is not exactly {phi0, phi1, phi2, phi3}",
            admitted=False,
        )
    if not _key_is_minimal(rows, key):
        return _route(
            "NonKeyCoincidenceViolation",
            "candidate key K is not minimal",
            admitted=False,
        )
    return _route(
        "RelationalPointCertified",
        "K determines U and the Heath join is lossless",
        admitted=True,
    )

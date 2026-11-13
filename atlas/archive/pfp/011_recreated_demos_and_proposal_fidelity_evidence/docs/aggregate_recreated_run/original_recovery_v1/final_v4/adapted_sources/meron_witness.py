"""Check one explicit sign-reversing pairing on finite path sectors.

The sectors, including their signs and weights, are supplied by the host.
This verifier proves an exact cancellation identity for that finite input only.
It does not derive sectors from a Hamiltonian, construct a cluster flip,
establish a BQNF obstruction class, or certify general sign freedom.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import Mapping, Sequence

class WitnessError(ValueError):
    """A finite sector or its proposed involution is invalid."""

@dataclass(frozen=True)
class PathSector:
    """One host-supplied path sector with an exact signed contribution."""
    path_id: str
    weight: Fraction
    sign: int

    @property
    def contribution(self) -> Fraction:
        return self.sign * self.weight

@dataclass(frozen=True)
class MeronWitnessResult:
    """Certificate for the declared finite cancellation subset ``S0``.

    ``pairs`` contains each two-cycle once. ``survivors`` are all sectors
    outside S0, in input order. ``signed_sum == survivor_sum >= 0`` is checked
    using exact rational arithmetic before this result is returned.
    """
    sectors: tuple[PathSector, ...]
    cancellation_ids: tuple[str, ...]
    xi: tuple[tuple[str, str], ...]
    pairs: tuple[tuple[str, str], ...]
    survivors: tuple[str, ...]
    signed_sum: Fraction
    survivor_sum: Fraction

def _weight(value: object, path_id: str) -> Fraction:
    if isinstance(value, bool) or isinstance(value, float):
        raise WitnessError(f'weight for {path_id!r} must be an exact rational')
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise WitnessError(f'weight for {path_id!r} must be finite')
        result = Fraction(value)
    elif isinstance(value, (int, Fraction)):
        result = Fraction(value)
    elif isinstance(value, str) and value.strip():
        try:
            result = Fraction(value)
        except (ValueError, ZeroDivisionError) as exc:
            raise WitnessError(f'weight for {path_id!r} is not rational') from exc
    else:
        raise WitnessError(f'weight for {path_id!r} must be an exact rational')
    if result < 0:
        raise WitnessError(f'weight for {path_id!r} must be nonnegative')
    return result

def _id(value: object, location: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WitnessError(f'{location} must be a nonempty string path ID')
    return value

def _sector(value: object, index: int) -> PathSector:
    if isinstance(value, PathSector):
        path_id, weight, sign = (value.path_id, value.weight, value.sign)
    elif isinstance(value, Mapping):
        if set(value) != {'path_id', 'weight', 'sign'}:
            raise WitnessError(f'sector[{index}] must contain exactly path_id, weight, and sign')
        path_id, weight, sign = (value['path_id'], value['weight'], value['sign'])
    else:
        raise WitnessError(f'sector[{index}] must be a PathSector or mapping')
    path_id = _id(path_id, f'sector[{index}].path_id')
    if type(sign) is not int or sign not in (-1, 1):
        raise WitnessError(f'sign for {path_id!r} must be exactly +1 or -1')
    return PathSector(path_id, _weight(weight, path_id), sign)

def verify_meron_witness(sectors: Sequence[PathSector | Mapping[str, object]], cancellation_ids: Sequence[str], xi: Mapping[str, str]) -> MeronWitnessResult:
    """Verify a finite, explicit, partial sign-reversing involution.

    The domain of ``xi`` must equal the declared cancellation subset S0.
    Every image remains in S0, each orbit is a fixed-point-free two-cycle,
    paired sectors have equal weights and opposite signs, and each survivor
    contributes nonnegatively. Invalid inputs raise :class:`WitnessError`.

    Passing this check is a finite signed-sum identity, not a conclusion about
    every path sector of a Hamiltonian or ``Phi_1`` under BQNF-FSIGN.
    """
    if not isinstance(sectors, (list, tuple)):
        raise WitnessError('sectors must be a finite list or tuple')
    parsed = tuple((_sector(item, i) for i, item in enumerate(sectors)))
    by_id = {sector.path_id: sector for sector in parsed}
    if len(by_id) != len(parsed):
        raise WitnessError('path IDs must be distinct')
    if not isinstance(cancellation_ids, (list, tuple)):
        raise WitnessError('S0 must be a list or tuple of path IDs')
    s0 = tuple((_id(path_id, f'S0[{i}]') for i, path_id in enumerate(cancellation_ids)))
    if len(set(s0)) != len(s0):
        raise WitnessError('S0 contains duplicate path IDs')
    if set(s0) - by_id.keys():
        raise WitnessError('S0 contains an undeclared path ID')
    if not isinstance(xi, Mapping):
        raise WitnessError('Xi must be an explicit path-ID mapping')
    if any((not isinstance(source, str) or not isinstance(target, str) for source, target in xi.items())):
        raise WitnessError('Xi keys and images must be path IDs')
    if set(xi) != set(s0):
        raise WitnessError('Xi must map exactly the declared S0, with no omissions or extras')
    pairs: list[tuple[str, str]] = []
    visited: set[str] = set()
    for source in s0:
        target = xi[source]
        if target not in by_id or target not in set(s0):
            raise WitnessError(f'Xi({source!r}) lies outside S0')
        if target == source:
            raise WitnessError(f'Xi has a fixed point at {source!r}')
        if xi[target] != source:
            raise WitnessError(f'Xi squared is not identity at {source!r}')
        left, right = (by_id[source], by_id[target])
        if left.sign != -right.sign:
            raise WitnessError(f'Xi does not reverse sign at {source!r}')
        if left.weight != right.weight:
            raise WitnessError(f'Xi does not preserve weight at {source!r}')
        if source not in visited:
            pairs.append((source, target))
            visited.update((source, target))
    survivors = tuple((sector.path_id for sector in parsed if sector.path_id not in set(s0)))
    for path_id in survivors:
        if by_id[path_id].contribution < 0:
            raise WitnessError(f'survivor {path_id!r} has negative contribution')
    signed_sum = sum((sector.contribution for sector in parsed), Fraction(0))
    survivor_sum = sum((by_id[path_id].contribution for path_id in survivors), Fraction(0))
    if signed_sum != survivor_sum or survivor_sum < 0:
        raise WitnessError('finite cancellation identity failed')
    return MeronWitnessResult(parsed, s0, tuple(((source, xi[source]) for source in s0)), tuple(pairs), survivors, signed_sum, survivor_sum)
__all__ = ['WitnessError', 'PathSector', 'MeronWitnessResult', 'verify_meron_witness']

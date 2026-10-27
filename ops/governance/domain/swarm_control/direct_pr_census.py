"""Direct open-PR census (SWARM-L10). Search indexes are discovery-only.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any

from .census_result import CensusResult
from .census_source import CensusSource


def census_open_pulls(
    repository: str,
    *,
    direct_fetch: Callable[[str], Sequence[Mapping[str, Any]]] | None = None,
    search_fetch: Callable[[str], Sequence[Mapping[str, Any]]] | None = None,
    prefer_search: bool = False,
    observation: Mapping[str, Any] | None = None,
) -> CensusResult:
    """List open PRs via direct source; refuse silent empty success on API failure.

    ``prefer_search`` labels search-only results as discovery-only and never
    as terminal ZERO_OPEN.
    """
    binding = dict(observation or {})
    binding.setdefault("repository", repository)

    if prefer_search and search_fetch is not None:
        try:
            rows = list(search_fetch(repository))
        except Exception as exc:  # noqa: BLE001 — typed residual, not crash
            return CensusResult(
                repository=repository,
                open_count=-1,
                open_numbers=(),
                source=CensusSource.SEARCH,
                residual=f"CENSUS_UNAVAILABLE:{type(exc).__name__}",
                observation_binding=binding,
            )
        nums = tuple(int(r["number"]) for r in rows if "number" in r)
        return CensusResult(
            repository=repository,
            open_count=len(nums),
            open_numbers=nums,
            source=CensusSource.SEARCH,
            residual="DISCOVERY_ONLY_NOT_TERMINAL",
            observation_binding=binding,
        )

    if direct_fetch is None:
        return CensusResult(
            repository=repository,
            open_count=-1,
            open_numbers=(),
            source=CensusSource.DIRECT,
            residual="CENSUS_UNAVAILABLE:no_direct_adapter",
            observation_binding=binding,
        )

    try:
        rows = list(direct_fetch(repository))
    except Exception as exc:  # noqa: BLE001
        return CensusResult(
            repository=repository,
            open_count=-1,
            open_numbers=(),
            source=CensusSource.DIRECT,
            residual=f"CENSUS_UNAVAILABLE:{type(exc).__name__}",
            observation_binding=binding,
        )

    try:
        nums = tuple(sorted(int(r["number"]) for r in rows))
    except (KeyError, TypeError, ValueError):
        return CensusResult(
            repository=repository,
            open_count=-1,
            open_numbers=(),
            source=CensusSource.DIRECT,
            residual="CENSUS_MALFORMED_PAYLOAD",
            observation_binding=binding,
        )

    residual = "ZERO_OPEN" if len(nums) == 0 else None
    return CensusResult(
        repository=repository,
        open_count=len(nums),
        open_numbers=nums,
        source=CensusSource.DIRECT,
        residual=residual,
        observation_binding=binding,
    )

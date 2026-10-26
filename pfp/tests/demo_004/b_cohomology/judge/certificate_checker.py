"""Compatibility checker forwarding to the shared independent certificate checker."""

from __future__ import annotations

from typing import Any, Mapping

from omega_engine_pfp.domain.cohomology.certificate_checker import check_certificate
from omega_engine_pfp.domain.cohomology.solver import detect_challenge


def check_cohomology_certificate(case: Mapping[str, Any], res: Mapping[str, Any]) -> dict[str, Any]:
    checked = check_certificate(case, res)
    return {
        "verdict": "PASS" if checked.passed else "FAIL",
        "passed": checked.passed,
        "challenge": detect_challenge(case),
        "error": checked.error,
    }


def _check_challenge(
    challenge: str, case: Mapping[str, Any], res: Mapping[str, Any]
) -> tuple[bool, str | None]:
    checked = check_certificate({**case, "challenge": challenge}, res)
    return checked.passed, checked.error


def check_c011(case: Mapping[str, Any], res: Mapping[str, Any]) -> tuple[bool, str | None]:
    return _check_challenge("c011", case, res)


def check_c012(case: Mapping[str, Any], res: Mapping[str, Any]) -> tuple[bool, str | None]:
    return _check_challenge("c012", case, res)


def check_c013(case: Mapping[str, Any], res: Mapping[str, Any]) -> tuple[bool, str | None]:
    return _check_challenge("c013", case, res)


def check_c014(case: Mapping[str, Any], res: Mapping[str, Any]) -> tuple[bool, str | None]:
    return _check_challenge("c014", case, res)


def check_c015(case: Mapping[str, Any], res: Mapping[str, Any]) -> tuple[bool, str | None]:
    return _check_challenge("c015", case, res)


def check_c016(case: Mapping[str, Any], res: Mapping[str, Any]) -> tuple[bool, str | None]:
    return _check_challenge("c016", case, res)


def check_c017(case: Mapping[str, Any], res: Mapping[str, Any]) -> tuple[bool, str | None]:
    return _check_challenge("c017", case, res)


def check_c018(case: Mapping[str, Any], res: Mapping[str, Any]) -> tuple[bool, str | None]:
    return _check_challenge("c018", case, res)


def check_c019(case: Mapping[str, Any], res: Mapping[str, Any]) -> tuple[bool, str | None]:
    return _check_challenge("c019", case, res)


def check_c020(case: Mapping[str, Any], res: Mapping[str, Any]) -> tuple[bool, str | None]:
    return _check_challenge("c020", case, res)

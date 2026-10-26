"""Signed-gauge transport never computes a Python fallback verdict."""

from fractions import Fraction

import pytest

from omega_engine_pfp.infrastructure.adapters.mssn_research.sign_switching import (
    SignGaugeNativeUnavailable,
    classify_sign_gauge,
    parse_matrix,
    verify_cycle,
    verify_gauge,
)


def test_missing_host_refuses_instead_of_python_search(monkeypatch):
    from omega_engine_pfp import ffi

    def unavailable():
        raise FileNotFoundError("native host missing")

    monkeypatch.setattr(ffi, "get_default_host", unavailable)
    with pytest.raises(SignGaugeNativeUnavailable, match="NATIVE_SIGNED_TRANSPORT_UNAVAILABLE"):
        classify_sign_gauge([[0, 1], [1, 0]])


def test_false_native_certificate_cannot_become_gauge_result(monkeypatch):
    from omega_engine_operating_system.adapters.rust_host.ffi import Ok
    from omega_engine_pfp import ffi

    class Host:
        def invoke(self, action, payload):
            assert action == "signed_transport"
            assert payload["matrix"] == [["0", "1/3"], ["1/3", "0"]]
            return Ok(
                {
                    "success": True,
                    "result": {
                        "authority_effect": "None",
                        "certificate_verified": False,
                        "matrix": payload["matrix"],
                        "gauge": [0, 0],
                        "cycle": None,
                        "transformed": payload["matrix"],
                    },
                }
            )

    monkeypatch.setattr(ffi, "get_default_host", Host)
    with pytest.raises(SignGaugeNativeUnavailable, match="NATIVE_CERTIFICATE_NOT_VERIFIED"):
        classify_sign_gauge([[0, Fraction(1, 3)], [Fraction(1, 3), 0]])


def test_invalid_witness_types_refuse_without_native_dispatch(monkeypatch):
    from omega_engine_pfp import ffi

    def forbidden():
        raise AssertionError("invalid witness must never dispatch")

    monkeypatch.setattr(ffi, "get_default_host", forbidden)
    assert verify_gauge([[0, 1], [1, 0]], [False, True]) is False
    assert verify_cycle([[0, 1], [1, 0]], [0, 1, 0, 1, 0]) is False
    with pytest.raises(ValueError):
        parse_matrix([[0, 0.1], [0.1, 0]])

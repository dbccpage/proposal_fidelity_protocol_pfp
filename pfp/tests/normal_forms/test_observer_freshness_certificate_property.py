"""Targeted property tests for Observer-Relative Freshness SLA and Certificate Verification.

Tests:
1. 02-certificate-table-without-verifier.py:
   - Authority laundering prevention on pending certificates
   - Missing verifier rejection
   - Only active verified outcome grants authorization
2. 03-observer-relative-freshness.py:
   - Observer relativity: same packet resolves distinct statuses across observers
   - Monotonicity of SLA lag acceptance
   - Conservative invalidation on missing/null lag evidence
   - Scope authorization firewall gating

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib.util
import json
import random
import unittest
from pathlib import Path

_EDU_ROOT = next(
    p / "omega_engine_education"
    for p in Path(__file__).resolve().parents
    if (p / "omega_engine_education/documentation/014_normal_forms").is_dir()
)
_CANDIDATE_DIRS = [
    _EDU_ROOT / "documentation" / "014_normal_forms" / "demos",
    _EDU_ROOT / "curriculum" / "normal_forms",
    _EDU_ROOT / "normal_forms",
]
_NORMAL_FORMS_DIR = next((d for d in _CANDIDATE_DIRS if d.is_dir()), _CANDIDATE_DIRS[0])
_CERT_EVALUATOR_PATH = _NORMAL_FORMS_DIR / "02-certificate-table-without-verifier.py"
if not _CERT_EVALUATOR_PATH.is_file():
    _fallback_cert = (
        _NORMAL_FORMS_DIR.parent.parent
        / "normal_forms"
        / "examples"
        / "02-certificate-table-without-verifier.py"
    )
    if _fallback_cert.is_file():
        _CERT_EVALUATOR_PATH = _fallback_cert

_FRESH_EVALUATOR_PATH = _NORMAL_FORMS_DIR / "03-observer-relative-freshness.py"
if not _FRESH_EVALUATOR_PATH.is_file():
    _fallback_fresh = (
        _NORMAL_FORMS_DIR.parent.parent
        / "normal_forms"
        / "examples"
        / "03-observer-relative-freshness.py"
    )
    if _fallback_fresh.is_file():
        _FRESH_EVALUATOR_PATH = _fallback_fresh

_CERT_DATA_PATH = _NORMAL_FORMS_DIR / "data" / "transport_certificates.json"
if not _CERT_DATA_PATH.is_file():
    _fallback_cert_data = (
        _NORMAL_FORMS_DIR.parent.parent
        / "normal_forms"
        / "examples"
        / "data"
        / "transport_certificates.json"
    )
    if _fallback_cert_data.is_file():
        _CERT_DATA_PATH = _fallback_cert_data

_OBS_DATA_PATH = _NORMAL_FORMS_DIR / "data" / "observers.json"
if not _OBS_DATA_PATH.is_file():
    _fallback_obs_data = (
        _NORMAL_FORMS_DIR.parent.parent / "normal_forms" / "examples" / "data" / "observers.json"
    )
    if _fallback_obs_data.is_file():
        _OBS_DATA_PATH = _fallback_obs_data


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cert_mod = _load_module(_CERT_EVALUATOR_PATH, "cert_eval_module")
fresh_mod = _load_module(_FRESH_EVALUATOR_PATH, "fresh_eval_module")

evaluate_certificate = cert_mod.evaluate_certificate
evaluate_freshness = fresh_mod.evaluate_freshness


class TestCertificateVerifierProperties(unittest.TestCase):
    """Property tests asserting certificate authority and verifier invariants."""

    def test_canonical_certificate_fixtures(self) -> None:
        """Verify all 3 canonical fixtures in data/transport_certificates.json."""
        self.assertTrue(_CERT_DATA_PATH.is_file())
        with open(_CERT_DATA_PATH, "r", encoding="utf-8") as f:
            fixtures = json.load(f)

        self.assertEqual(len(fixtures), 3)

        # Case 1: Pending verifier outcome -> AuthorityLaundering (NotAuthorized)
        res1 = evaluate_certificate(fixtures[0])
        self.assertEqual(res1["decision"], "NotAuthorized")
        self.assertEqual(res1["terminal_route"], "AuthorityLaundering")
        self.assertTrue(res1["certified"])
        self.assertFalse(res1["authorized"])

        # Case 2: Missing verifier altogether -> MissingVerifier (NotAuthorized)
        res2 = evaluate_certificate(fixtures[1])
        self.assertEqual(res2["decision"], "NotAuthorized")
        self.assertEqual(res2["terminal_route"], "MissingVerifier")
        self.assertFalse(res2["certified"])
        self.assertFalse(res2["authorized"])

        # Case 3: Active verified outcome -> Accept (Authorized)
        res3 = evaluate_certificate(fixtures[2])
        self.assertEqual(res3["decision"], "Authorized")
        self.assertEqual(res3["terminal_route"], "Accept")
        self.assertTrue(res3["certified"])
        self.assertTrue(res3["authorized"])

    def test_unverified_certificate_rejection_property(self) -> None:
        """Property: No unverified, pending, rejected, or missing verifier outcome can mint authorization."""
        rng = random.Random(42)
        non_authorized_outcomes = [
            "pending",
            None,
            "rejected",
            "failed",
            "in_progress",
            "claimed",
            "self_certified",
            "unknown",
        ]

        for outcome in non_authorized_outcomes:
            for _ in range(10):
                cert = {
                    "certificate_id": f"cert_{rng.randint(100, 999)}",
                    "source_regime": "sql_query",
                    "target_regime": "cache_shape",
                    "morphism_kind": "project",
                    "verifier_outcome": outcome,
                }
                res = evaluate_certificate(cert)
                self.assertEqual(res["decision"], "NotAuthorized")
                self.assertFalse(res["authorized"])
                if outcome == "pending":
                    self.assertEqual(res["terminal_route"], "AuthorityLaundering")
                else:
                    self.assertEqual(res["terminal_route"], "MissingVerifier")

    def test_only_exact_verified_grants_authorization(self) -> None:
        """Property: Bare field 'verified' is refused; only verified replay with active policy authorizes."""
        bare_cert = {
            "certificate_id": "cert_auth_exact",
            "source_regime": "sql_query",
            "target_regime": "cache_shape",
            "morphism_kind": "project",
            "verifier_outcome": "verified",
        }
        # 1. Bare field without independent verifier replay fails closed (Refuse)
        res_bare = evaluate_certificate(bare_cert)
        self.assertEqual(res_bare["decision"], "NotAuthorized")
        self.assertEqual(res_bare["terminal_route"], "Refuse")
        self.assertFalse(res_bare["authorized"])

        # 2. Independent verifier replay with active policy authorization succeeds
        auth_cert = {
            **bare_cert,
            "independent_verifier": {
                "verifier_id": "v_test",
                "executed": True,
                "outcome": "verified",
            },
            "policy_decision": {
                "policy_id": "p_test",
                "accepted": True,
                "authorized_scope": "cache_shape",
            },
        }
        res_auth = evaluate_certificate(auth_cert)
        self.assertEqual(res_auth["decision"], "Authorized")
        self.assertEqual(res_auth["terminal_route"], "Accept")
        self.assertTrue(res_auth["certified"])
        self.assertTrue(res_auth["authorized"])


class TestObserverRelativeFreshnessProperties(unittest.TestCase):
    """Property tests asserting observer-relative SLA lag and authorization bounds."""

    def test_canonical_observer_fixtures(self) -> None:
        """Verify all 3 canonical scenarios in data/observers.json."""
        self.assertTrue(_OBS_DATA_PATH.is_file())
        with open(_OBS_DATA_PATH, "r", encoding="utf-8") as f:
            scenarios = json.load(f)

        self.assertEqual(len(scenarios), 3)

        # Scenario A: Lag = 7s. Dashboard (max 10s) passes; Trading engine (max 2s) fails
        res_a = evaluate_freshness(scenarios[0])
        self.assertEqual(len(res_a), 2)
        dashboard_res = next(r for r in res_a if r["observer_id"] == "dashboard")
        trading_res = next(r for r in res_a if r["observer_id"] == "trading_engine")
        self.assertEqual(dashboard_res["terminal_route"], "AuthorizedFresh")
        self.assertTrue(dashboard_res["authorized"])
        self.assertEqual(trading_res["terminal_route"], "RefreshRequired")
        self.assertFalse(trading_res["authorized"])

        # Scenario B: Missing lag metadata (null) -> ConservativeInvalidate
        res_b = evaluate_freshness(scenarios[1])
        self.assertEqual(len(res_b), 1)
        self.assertEqual(res_b[0]["terminal_route"], "ConservativeInvalidate")
        self.assertFalse(res_b[0]["authorized"])

        # Scenario C: Scope mismatch ('restricted' vs ['public_only']) -> Refuse
        res_c = evaluate_freshness(scenarios[2])
        self.assertEqual(len(res_c), 1)
        self.assertEqual(res_c[0]["terminal_route"], "Refuse")
        self.assertFalse(res_c[0]["authorized"])

    def test_observer_relativity_functor_property(self) -> None:
        """Property: The same packet resolves strictly differently according to observer SLA tolerance."""
        rng = random.Random(1234)
        for _ in range(50):
            lag = rng.randint(5, 50)
            obs1_limit = lag - rng.randint(1, 4)  # Strictly stale for obs1
            obs2_limit = lag + rng.randint(0, 10)  # Strictly fresh for obs2

            scenario = {
                "packet": {"value": 100, "replica_lag_seconds": lag, "packet_scope": "public"},
                "observers": [
                    {
                        "observer_id": "tight_sla",
                        "max_lag_seconds": obs1_limit,
                        "authorized_scopes": ["public"],
                    },
                    {
                        "observer_id": "loose_sla",
                        "max_lag_seconds": obs2_limit,
                        "authorized_scopes": ["public"],
                    },
                ],
            }
            results = evaluate_freshness(scenario)
            tight = next(r for r in results if r["observer_id"] == "tight_sla")
            loose = next(r for r in results if r["observer_id"] == "loose_sla")

            # Fundamental observer-relative functor invariant
            self.assertEqual(tight["terminal_route"], "RefreshRequired")
            self.assertFalse(tight["authorized"])
            self.assertEqual(loose["terminal_route"], "AuthorizedFresh")
            self.assertTrue(loose["authorized"])

    def test_sla_budget_step_function_monotonicity(self) -> None:
        """Property: For a fixed packet lag L, authorization is monotonic in observer tolerance T."""
        rng = random.Random(5678)
        for _ in range(30):
            lag = rng.randint(10, 60)
            thresholds = [lag - 5, lag - 1, lag, lag + 1, lag + 10]

            scenario = {
                "packet": {"value": 42, "replica_lag_seconds": lag, "packet_scope": "public"},
                "observers": [
                    {
                        "observer_id": f"obs_{t}",
                        "max_lag_seconds": t,
                        "authorized_scopes": ["public"],
                    }
                    for t in thresholds
                ],
            }
            results = evaluate_freshness(scenario)
            for r in results:
                t = int(r["observer_id"].split("_")[1])
                if t >= lag:
                    self.assertEqual(r["terminal_route"], "AuthorizedFresh")
                    self.assertTrue(r["authorized"])
                else:
                    self.assertEqual(r["terminal_route"], "RefreshRequired")
                    self.assertFalse(r["authorized"])

    def test_missing_evidence_conservative_invalidation(self) -> None:
        """Property: If replica lag is None/missing, all observers fail closed to ConservativeInvalidate."""
        scenario = {
            "packet": {"value": 1, "packet_scope": "public"},  # replica_lag_seconds missing
            "observers": [
                {
                    "observer_id": "obs_infinite_sla",
                    "max_lag_seconds": 999999,
                    "authorized_scopes": ["public"],
                },
                {
                    "observer_id": "obs_zero_sla",
                    "max_lag_seconds": 0,
                    "authorized_scopes": ["public"],
                },
            ],
        }
        results = evaluate_freshness(scenario)
        for r in results:
            self.assertEqual(r["terminal_route"], "ConservativeInvalidate")
            self.assertFalse(r["authorized"])
            self.assertIn("missing or null", r["reason"])

    def test_scope_authorization_firewall_precedence(self) -> None:
        """Property: Scope authorization failure precedes lag SLA checks; fresh packet is refused if unauthorized."""
        scenario = {
            "packet": {
                "value": 123,
                "replica_lag_seconds": 0,  # Zero lag
                "packet_scope": "top_secret",
            },
            "observers": [
                {
                    "observer_id": "unauthorized_observer",
                    "max_lag_seconds": 100,
                    "authorized_scopes": ["public", "internal"],
                }
            ],
        }
        results = evaluate_freshness(scenario)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["terminal_route"], "Refuse")
        self.assertFalse(results[0]["authorized"])
        self.assertIn("not authorized for packet scope", results[0]["reason"])


if __name__ == "__main__":
    unittest.main()

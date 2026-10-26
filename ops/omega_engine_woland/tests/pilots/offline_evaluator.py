"""Offline observation regrader for PFP Pilots under PFP-01 through PFP-05.

AuthorityEffect: None.
Governing standard: Proposal Fidelity Protocol (PFP v0.2), Single Prompt Standard (SPK-001).

Rechecks saved raw observations without modifying historical artifacts.
Oracle fixtures are generated only by the separate --create-fixtures command.
"""

from __future__ import annotations
from omega_engine_pfp.infrastructure.model_loading import load_yaml_model

import argparse
import sys
from fractions import Fraction
from pathlib import Path
from importlib.resources import files
from typing import Any, Dict, List, Tuple

import yaml

# Add repo and education roots to sys.path
_HERE = Path(__file__).resolve().parent
_REPO_ROOT = next((p for p in _HERE.parents if (p / ".git").exists()), _HERE.parents[2])
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from omega_engine_pfp.domain.types import EvaluationStatus
from omega_engine_pfp.domain.pilots.fail_closed_gate import FailClosedRefusalGate
from omega_engine_pfp.domain.types import NegativeMutationFixture
from omega_engine_pfp.domain.types import PilotResponse
from omega_engine_pfp.domain.types import PilotSpec
from omega_engine_pfp.domain.types import SeedPrompt


class ExactLinalgEvaluator:
    """Deterministic host gate checker supporting PFP-01 through PFP-05."""

    CHECKER_ID = "PFP-01-EXACT-LINALG"

    @staticmethod
    def solve_linear_system_2d(
        a11: Fraction, a12: Fraction, b1: Fraction,
        a21: Fraction, a22: Fraction, b2: Fraction,
    ) -> Tuple[Fraction, Fraction]:
        """Solve 2x2 system A x = b over Q using Cramer's rule."""
        det = a11 * a22 - a12 * a21
        if det == 0:
            raise ValueError("Singular system: det(A) == 0")
        x = (b1 * a22 - a12 * b2) / det
        y = (a11 * b2 - b1 * a21) / det
        return x, y

    @classmethod
    def compute_ground_truth(cls) -> Fraction:
        """Ground truth solution for canonical system: x + 2y = 5, 3x - y = 1; target: x + y."""
        x, y = cls.solve_linear_system_2d(
            Fraction(1), Fraction(2), Fraction(5),
            Fraction(3), Fraction(-1), Fraction(1),
        )
        return x + y

    @classmethod
    def get_ground_truth_for_checker(cls, checker_id: str, seed: SeedPrompt) -> Any:
        """The frozen seed owns its oracle; no checker ID supplies a fixed answer."""
        return seed.expected_outcome.answer

    @classmethod
    def evaluate_pilot(cls, pilot_dir: Path) -> Dict[str, Any]:
        """Regrade saved raw evidence without changing response.yaml."""
        from omega_engine_pfp.infrastructure.pilot_evidence import record_evaluation
        from omega_engine_woland.tests.pilots.live_evaluator import (
            extract_and_evaluate,
            sanitize_raw_reply,
        )

        spec = load_yaml_model(PilotSpec, pilot_dir / "spec.yaml")
        seed = load_yaml_model(SeedPrompt, pilot_dir / "seed.yaml")
        checker_id = str(spec.host_gate.checker_id)
        expected = seed.expected_outcome.answer
        response_path = pilot_dir / "response.yaml"
        received = None
        status = EvaluationStatus.NOT_RUN
        mode = "not_run"
        evaluation_path = None
        if response_path.is_file():
            observation = response_path.read_bytes()
            try:
                existing = load_yaml_model(PilotResponse, response_path)
                mode = existing.execution_mode.value if hasattr(existing.execution_mode, "value") else str(existing.execution_mode or "not_run")
                trial_status_val = existing.trial_status.value if hasattr(existing.trial_status, "value") else str(existing.trial_status)
                if trial_status_val == "NOT_RUN" and existing.raw_reply is None:
                    mode = "not_run"
                else:
                    _, valid, _, parsed = sanitize_raw_reply(existing.raw_reply)
                    received, status = extract_and_evaluate(
                        checker_id, expected, existing.raw_reply or "", parsed if valid else None,
                    )
            except (ValueError, yaml.YAMLError):
                status = EvaluationStatus.MALFORMED
                mode = "unparseable_historical_observation"
            evaluation_path = record_evaluation(
                pilot_dir, observation, expected, checker_id, received, status.value,
                observation_mode=mode,
            )
        return {
            "pilot_id": spec.pilot_id, "task_family": spec.coordinates.task_family,
            "difficulty_rung": spec.coordinates.difficulty_rung, "checker_id": checker_id,
            "expected": expected, "received": received,
            "delta": 0 if received == expected and status == EvaluationStatus.ACCEPTED else 1,
            "status": status.value, "execution_mode": mode,
            "cost_microusd": None, "provider_calls": 0,
            "efficacy_eligible": False,
            "evaluation_receipt": str(evaluation_path) if evaluation_path else None,
        }

    @classmethod
    def create_fixture(cls, pilot_dir: Path) -> Path:
        """Explicit oracle fixture generation, separate from observations and evaluation."""
        from omega_engine_pfp.infrastructure.pilot_evidence import (
            canonical_bytes,
            digest,
            write_once,
        )

        seed_path = pilot_dir / "seed.yaml"
        seed = load_yaml_model(SeedPrompt, seed_path)
        fixture = {
            "schema": "pfp.oracle-fixture.v1", "authority_effect": "None",
            "seed_sha256": digest(seed_path.read_bytes()),
            "oracle_value": seed.expected_outcome.answer, "provider_calls": 0,
            "efficacy_eligible": False,
        }
        return write_once(pilot_dir / "fixtures" / f"{digest(canonical_bytes(fixture))}.json", fixture)


def run_all_pilots(results_dir: Path | None = None) -> List[Dict[str, Any]]:
    """Regrade saved observations on all pilots under results_dir."""
    base_results = results_dir or (_HERE / "results")
    if not base_results.is_dir():
        raise FileNotFoundError(f"Results directory not found at {base_results}")

    pilot_dirs = sorted([d for d in base_results.iterdir() if d.is_dir() and d.name.startswith("pilot_")])
    if not pilot_dirs:
        raise ValueError(f"No pilot directories found in {base_results}")

    evaluator = ExactLinalgEvaluator()
    reports = []

    print(f"\n================================================================================")
    print(f"  PFP OFFLINE OBSERVATION REGRADER (PFP-01 to PFP-05)")
    print(f"  Directory: {base_results}")
    print(f"  Evaluated Pilots: {len(pilot_dirs)}")
    print(f"================================================================================\n")

    print(f"{'Pilot ID':<14} | {'Checker':<30} | {'Expected':<12} | {'Received':<12} | {'Delta':<6} | {'Status':<10} | {'Mode':<24}")
    print(f"{'-'*14}-+-{'-'*30}-+-{'-'*12}-+-{'-'*12}-+-{'-'*6}-+-{'-'*10}-+-{'-'*24}")

    for p_dir in pilot_dirs:
        res = evaluator.evaluate_pilot(p_dir)
        reports.append(res)
        status = res["status"]

        exp_str = str(res['expected'])
        if len(exp_str) > 12:
            exp_str = exp_str[:9] + "..."
        rec_str = str(res['received'])
        if len(rec_str) > 12:
            rec_str = rec_str[:9] + "..."

        print(
            f"{res['pilot_id']:<14} | "
            f"{res['checker_id']:<30} | "
            f"{exp_str:<12} | "
            f"{rec_str:<12} | "
            f"{res['delta']:<6} | "
            f"{status:<10} | "
            f"{res['execution_mode']:<24}"
        )

    print(f"{'-'*14}-+-{'-'*30}-+-{'-'*12}-+-{'-'*12}-+-{'-'*6}-+-{'-'*10}-+-{'-'*24}\n")

    accepted_count = sum(1 for r in reports if r["status"] == "ACCEPTED")
    print(f"Regraded correctness: {accepted_count}/{len(reports)} ACCEPTED; efficacy-eligible: 0")
    print("Provider calls by this command: 0; historical billing: unreconciled\n")


    return reports


def run_negative_mutation_suite(fixtures_path: Path | None = None) -> List[Dict[str, Any]]:
    """Run fail-closed evaluation across all negative mutation and perturbation fixtures."""
    fpath = fixtures_path
    if fpath is None:
        cand = files("omega_engine_pfp").joinpath(
            "infrastructure", "yaml", "fixtures", "fix_negative_mutation_fixtures.yaml"
        )
        if cand.is_file():
            fpath = cand
        else:
            fpath = files("omega_engine_pfp").joinpath(
                "infrastructure", "yaml", "fixtures", "negative_mutation_fixtures.yaml"
            )

    if not fpath.is_file():
        raise FileNotFoundError(f"Negative mutation fixtures not found at {fpath}")

    raw = yaml.safe_load(fpath.read_text(encoding="utf-8"))
    fixtures = [NegativeMutationFixture.model_validate(f) for f in raw.get("fixtures", [])]

    print(f"\n================================================================================")
    print(f"  PFP FAIL-CLOSED NEGATIVE MUTATION & PERTURBATION VERIFIER")
    print(f"  Fixtures Catalog: {fpath.name}")
    print(f"  Total Fixtures: {len(fixtures)}")
    print(f"================================================================================\n")

    print(f"{'Fixture ID':<36} | {'Checker':<24} | {'Kind':<28} | {'Status':<14} | {'Refusal Code':<28} | {'Pass'}")
    print(f"{'-'*36}-+-{'-'*24}-+-{'-'*28}-+-{'-'*14}-+-{'-'*28}-+------")

    all_passed = True
    reports = []

    for fix in fixtures:
        res = FailClosedRefusalGate.evaluate_negative_fixture(fix)
        passed = (
            res.status != EvaluationStatus.ACCEPTED
            and res.status == fix.expected_status
            and (fix.expected_refusal_code is None or (res.refusal_code and res.refusal_code.value == fix.expected_refusal_code))
        )
        if not passed:
            all_passed = False

        ref_code = res.refusal_code.value if res.refusal_code else "NONE"
        status_str = res.status.value if hasattr(res.status, "value") else str(res.status)
        pass_str = "PASS" if passed else "FAIL"

        print(
            f"{fix.fixture_id:<36} | "
            f"{str(fix.checker_id):<24} | "
            f"{fix.mutation_kind:<28} | "
            f"{status_str:<14} | "
            f"{ref_code:<28} | "
            f"{pass_str}"
        )

        reports.append({
            "fixture_id": fix.fixture_id,
            "checker_id": str(fix.checker_id),
            "mutation_kind": fix.mutation_kind,
            "expected_status": fix.expected_status.value,
            "received_status": status_str,
            "refusal_code": ref_code,
            "passed": passed,
            "reason": res.reason,
        })

    print(f"{'-'*36}-+-{'-'*24}-+-{'-'*28}-+-{'-'*14}-+-{'-'*28}-+------\n")
    certified_count = sum(1 for r in reports if r["passed"])
    print(f"Summary: {certified_count}/{len(reports)} FAIL-CLOSED REFUSALS CERTIFIED (100% Pass: {all_passed})")
    zero_false_acceptances = all(r["received_status"] != "ACCEPTED" for r in reports)
    print(f"Zero False Acceptances: {zero_false_acceptances}\n")

    if not all_passed:
        raise RuntimeError("One or more negative mutation fixtures failed closed verification.")

    return reports


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=_HERE / "results", help="Path to pilots/results directory")
    parser.add_argument("--create-fixtures", action="store_true", help="Create separate oracle fixtures; never overwrite observations")
    parser.add_argument("--check-negative-fixtures", action="store_true", help="Execute fail-closed negative mutation verification")
    parser.add_argument("--fixtures-path", type=Path, default=None, help="Path to negative mutation fixtures YAML")
    args = parser.parse_args(argv)

    try:
        if args.check_negative_fixtures:
            run_negative_mutation_suite(args.fixtures_path)
        elif args.create_fixtures:
            for pilot_dir in sorted(args.results_dir.glob("pilot_*")):
                if pilot_dir.is_dir():
                    print(ExactLinalgEvaluator.create_fixture(pilot_dir))
        else:
            run_all_pilots(args.results_dir)
        return 0
    except Exception as err:
        print(f"ERROR: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())


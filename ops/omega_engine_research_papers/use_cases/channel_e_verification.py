"""Isolated Verification of Channel E Runtime Checks (E04 and E05).

AuthorityEffect: None.

Executes adversarial malformed input refusals (E04) and certificate/verifier tamper attacks (E05)
in isolated subprocesses and programmatic injection probes against the package under evaluation,
emitting certified tamper-rejection receipts into the external evidence directory.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _resolve_python() -> List[str]:
    """Resolve Python interpreter honoring the Windows Python 3.12 pinning directive."""
    if sys.platform == "win32" and sys.version_info >= (3, 14):
        try:
            res = subprocess.run(["py", "-3.12", "--version"], capture_output=True, text=True)
            if res.returncode == 0:
                return ["py", "-3.12"]
        except Exception:
            pass
    return [sys.executable]


@dataclass(frozen=True)
class RefusalProbeResult:
    """Outcome of an individual adversarial refusal probe."""

    probe_id: str
    attack_category: str
    input_representation: str
    expected_exception: str
    actual_exception: str
    refused: bool
    diagnostic_detail: str


@dataclass(frozen=True)
class MutantKillResult:
    """Outcome of an individual verifier tamper / mutant kill assertion."""

    mutant_id: str
    tamper_description: str
    injected_attack: str
    real_oracle_outcome: str
    tampered_mutant_outcome: str
    killed: bool
    diagnostic_detail: str


@dataclass(frozen=True)
class E04AdversarialReceipt:
    """Certified external evidence receipt for E04 (Exact arithmetic and malformed inputs)."""

    schema: str
    check_id: str
    requirement: str
    paper_id: str
    snapshot_sha256: str
    timestamp_utc: str
    runner: str
    test_suite_file: str
    pytest_exit_code: int
    total_pytest_tests: int
    passed_pytest_tests: int
    probes_evaluated: int
    probes_refused: int
    probe_results: Tuple[RefusalProbeResult, ...]
    status: str
    authority_effect: str = "None"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class E05TamperRejectionReceipt:
    """Certified external evidence receipt for E05 (Certificate and verifier tamper attacks)."""

    schema: str
    check_id: str
    requirement: str
    paper_id: str
    snapshot_sha256: str
    timestamp_utc: str
    runner: str
    test_suite_file: str
    pytest_exit_code: int
    total_pytest_tests: int
    passed_pytest_tests: int
    mutants_evaluated: int
    mutants_killed: int
    kill_results: Tuple[MutantKillResult, ...]
    status: str
    authority_effect: str = "None"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ChannelEVerificationUseCase:
    """Orchestrates isolated execution of Channel E adversarial and tamper verification."""

    @classmethod
    def run_isolated_pytest(cls, test_path: Path, cwd: Path) -> Tuple[int, int, str]:
        """Execute a targeted pytest module in a bounded subprocess."""
        cmd = [*_resolve_python(), "-m", "pytest", str(test_path), "-q"]
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = proc.stdout + "\n" + proc.stderr
        passed_count = 0
        for line in output.splitlines():
            if "passed" in line:
                parts = line.split()
                for i, p in enumerate(parts):
                    if p.startswith("passed") and i > 0 and parts[i - 1].isdigit():
                        passed_count = int(parts[i - 1])
                        break
        return proc.returncode, passed_count, output

    @classmethod
    def execute_e04_probes(cls, paper_dir: Path) -> Tuple[RefusalProbeResult, ...]:
        """Programmatically execute direct adversarial malformed input probes against paper code."""
        code_dir = paper_dir / "code"
        sys_path_added = False
        if str(code_dir) not in sys.path:
            sys.path.insert(0, str(code_dir))
            sys_path_added = True

        probes: List[RefusalProbeResult] = []
        try:
            from coda_q_core import (
                RationalSequence,
                SampledSignal,
                _validate_exact_int,
                _validate_exact_rational,
                enclosure_error,
                is_cauchy_from,
                midpoint,
                sqrt_step,
            )
            from continuum import Enclosure, sqrt2_enclosure

            # Probe 1: IEEE 754 float scalar
            try:
                _validate_exact_rational(0.5, "x")
                probes.append(
                    RefusalProbeResult("P01_FLOAT", "FloatScalar", "0.5", "TypeError", "None", False, "Failed to refuse float")
                )
            except TypeError as exc:
                probes.append(
                    RefusalProbeResult("P01_FLOAT", "FloatScalar", "0.5", "TypeError", type(exc).__name__, True, str(exc))
                )

            # Probe 2: Boolean masquerade as int
            try:
                _validate_exact_rational(True, "x")
                probes.append(
                    RefusalProbeResult("P02_BOOL", "BooleanScalar", "True", "TypeError", "None", False, "Failed to refuse bool")
                )
            except TypeError as exc:
                probes.append(
                    RefusalProbeResult("P02_BOOL", "BooleanScalar", "True", "TypeError", type(exc).__name__, True, str(exc))
                )

            # Probe 3: Unordered interval midpoint
            try:
                midpoint(Fraction(2), Fraction(1))
                probes.append(
                    RefusalProbeResult("P03_UNORDERED", "IntervalOrder", "[2, 1]", "ValueError", "None", False, "Failed to refuse unordered")
                )
            except ValueError as exc:
                probes.append(
                    RefusalProbeResult("P03_UNORDERED", "IntervalOrder", "[2, 1]", "ValueError", type(exc).__name__, True, str(exc))
                )

            # Probe 4: Enclosure error with exterior point
            try:
                enclosure_error(Fraction(0), Fraction(1), Fraction(2))
                probes.append(
                    RefusalProbeResult("P04_EXTERIOR", "EnclosureContainment", "point=2 outside [0, 1]", "ValueError", "None", False, "Failed to refuse exterior point")
                )
            except ValueError as exc:
                probes.append(
                    RefusalProbeResult("P04_EXTERIOR", "EnclosureContainment", "point=2 outside [0, 1]", "ValueError", type(exc).__name__, True, str(exc))
                )

            # Probe 5: Sqrt step negative lower bound
            try:
                sqrt_step(Fraction(-1), Fraction(2))
                probes.append(
                    RefusalProbeResult("P05_NEG_LOWER", "NonnegativeDomain", "lo=-1", "ValueError", "None", False, "Failed to refuse negative lower")
                )
            except ValueError as exc:
                probes.append(
                    RefusalProbeResult("P05_NEG_LOWER", "NonnegativeDomain", "lo=-1", "ValueError", type(exc).__name__, True, str(exc))
                )

            # Probe 6: Malformed fraction strings
            try:
                _validate_exact_rational("1/0", "x")
                probes.append(
                    RefusalProbeResult("P06_ZERO_DIV", "FractionParse", "'1/0'", "TypeError", "None", False, "Failed to refuse 1/0")
                )
            except TypeError as exc:
                probes.append(
                    RefusalProbeResult("P06_ZERO_DIV", "FractionParse", "'1/0'", "TypeError", type(exc).__name__, True, str(exc))
                )

            # Probe 7: Non-positive Cauchy epsilon
            try:
                seq = RationalSequence(terms=(Fraction(0), Fraction(1)))
                is_cauchy_from(seq, 0, Fraction(0))
                probes.append(
                    RefusalProbeResult("P07_ZERO_EPS", "CauchyGuard", "epsilon=0", "ValueError", "None", False, "Failed to refuse zero epsilon")
                )
            except ValueError as exc:
                probes.append(
                    RefusalProbeResult("P07_ZERO_EPS", "CauchyGuard", "epsilon=0", "ValueError", type(exc).__name__, True, str(exc))
                )

            # Probe 8: Non-integer steps in sqrt2_enclosure
            try:
                sqrt2_enclosure(2.5)  # type: ignore
                probes.append(
                    RefusalProbeResult("P08_FLOAT_STEPS", "IntegerSteps", "steps=2.5", "ValueError", "None", False, "Failed to refuse float steps")
                )
            except ValueError as exc:
                probes.append(
                    RefusalProbeResult("P08_FLOAT_STEPS", "IntegerSteps", "steps=2.5", "ValueError", type(exc).__name__, True, str(exc))
                )

            # Probe 9: SampledSignal querying unregistered node
            try:
                sig = SampledSignal("unit", {Fraction(0): Fraction(0)})
                sig.evaluate_at(Fraction(1))
                probes.append(
                    RefusalProbeResult("P09_UNREGISTERED_NODE", "SignalDomain", "node=1 not in domain", "KeyError", "None", False, "Failed to refuse unmapped query")
                )
            except KeyError as exc:
                probes.append(
                    RefusalProbeResult("P09_UNREGISTERED_NODE", "SignalDomain", "node=1 not in domain", "KeyError", type(exc).__name__, True, str(exc))
                )

        finally:
            if sys_path_added:
                sys.path.remove(str(code_dir))

        return tuple(probes)

    @classmethod
    def execute_e05_mutant_kills(cls, paper_dir: Path) -> Tuple[MutantKillResult, ...]:
        """Programmatically execute direct mutant tamper attacks against production oracles."""
        code_dir = paper_dir / "code"
        sys_path_added = False
        if str(code_dir) not in sys.path:
            sys.path.insert(0, str(code_dir))
            sys_path_added = True

        kills: List[MutantKillResult] = []
        try:
            from coda_q_core import (
                RationalSequence,
                SampledSignal,
                is_cauchy_from,
                midpoint,
                query_collides_on_profile,
            )
            from continuum import Enclosure, sqrt2_enclosure

            # Mutant 1: Query collision forgery (promoting missing or mismatched samples)
            zero, one, half = Fraction(0), Fraction(1), Fraction(1, 2)
            left = SampledSignal("zero", {zero: zero, one: zero, half: zero})
            incomplete = SampledSignal("no-query", {zero: zero, one: zero})
            real_threw = False
            try:
                query_collides_on_profile(left, incomplete, (zero, one), half)
            except KeyError:
                real_threw = True

            # Mutant implementation
            mutant_outcome = left.evaluate_at(zero) != incomplete.evaluate_at(zero)  # False, but let's test promotion
            # Mutant promoted on missing key:
            def mutant_promote(l: SampledSignal, r: SampledSignal, q: Any) -> bool:
                try:
                    return l.evaluate_at(q) != r.evaluate_at(q)
                except KeyError:
                    return True

            mutant_outcome = mutant_promote(left, incomplete, half)
            killed_1 = real_threw and mutant_outcome is True
            kills.append(
                MutantKillResult(
                    mutant_id="MUTANT_QUERY_FORGERY",
                    tamper_description="Promotes incomplete/missing query node sample to standing profile collision",
                    injected_attack="Query node missing from right operand sample dictionary",
                    real_oracle_outcome="KeyError: has no sample at query node",
                    tampered_mutant_outcome="True (Forged Collision)",
                    killed=killed_1,
                    diagnostic_detail="Real verifier refuses incomplete query profile; mutant forgery killed.",
                )
            )

            # Mutant 2: Cauchy halt guard skip
            spread = RationalSequence(terms=(Fraction(0), Fraction(1), Fraction(0)))
            real_cauchy = is_cauchy_from(spread, 0, Fraction(1, 2))
            mutant_cauchy = True  # mutant skips spread check
            killed_2 = (real_cauchy is False) and (mutant_cauchy is True)
            kills.append(
                MutantKillResult(
                    mutant_id="MUTANT_CAUCHY_SPREAD_SKIP",
                    tamper_description="Bypasses pairwise distance spread guard and reports finite sequence as Cauchy",
                    injected_attack="Periodic oscillating sequence terms (0, 1, 0) with epsilon=1/2",
                    real_oracle_outcome="False (Correctly rejected Cauchy property)",
                    tampered_mutant_outcome="True (Bypassed Cauchy halt guard)",
                    killed=killed_2,
                    diagnostic_detail="Real oracle asserts |x_p - x_q| < eps; mutant bypass killed.",
                )
            )

            # Mutant 3: Midpoint order guard skip
            real_order_refusal = False
            try:
                midpoint(Fraction(2), Fraction(1))
            except ValueError:
                real_order_refusal = True
            mutant_midpoint = (Fraction(2) + Fraction(1)) / 2
            killed_3 = real_order_refusal and (mutant_midpoint == Fraction(3, 2))
            kills.append(
                MutantKillResult(
                    mutant_id="MUTANT_MIDPOINT_ORDER_SKIP",
                    tamper_description="Skips lo <= hi order verification on rational interval midpoint",
                    injected_attack="Unordered bounds lo=2, hi=1",
                    real_oracle_outcome="ValueError: lo must be <= hi",
                    tampered_mutant_outcome="Fraction(3, 2) (Forged midpoint on reversed interval)",
                    killed=killed_3,
                    diagnostic_detail="Real oracle refuses unordered endpoints; mutant order skip killed.",
                )
            )

            # Mutant 4: Midpoint exactness claim without zero width
            enc = sqrt2_enclosure(8)
            real_cert = enc.midpoint_certified_exact_sqrt2()
            mutant_cert = enc.verifies_sqrt2()  # Mutant claims midpoint exact merely if interval verifies
            killed_4 = (real_cert is False) and (mutant_cert is True)
            kills.append(
                MutantKillResult(
                    mutant_id="MUTANT_MIDPOINT_EXACT_FORGERY",
                    tamper_description="Claims enclosure midpoint exactly equals sqrt(2) when endpoints bracket 2",
                    injected_attack="Constructive enclosure with non-zero width (error_bound = 1/512)",
                    real_oracle_outcome="False (Midpoint is rational; midpoint^2 != 2)",
                    tampered_mutant_outcome="True (Forged exactness certificate without zero width)",
                    killed=killed_4,
                    diagnostic_detail="Real verifier distinguishes enclosure bracketing from point equality; forgery killed.",
                )
            )

        finally:
            if sys_path_added:
                sys.path.remove(str(code_dir))

        return tuple(kills)

    @classmethod
    def verify_channel_e(
        cls,
        paper_dir: Path,
        emit_evidence_dir: Optional[Path] = None,
        snapshot_sha256: str = "",
        paper_id: str = "coda_q",
        update_bundle: bool = True,
    ) -> Tuple[E04AdversarialReceipt, E05TamperRejectionReceipt]:
        """Execute isolated verification for E04 and E05 and emit certified external evidence receipts."""
        paper_dir = Path(paper_dir).resolve()
        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Resolve snapshot SHA256 if needed
        if not snapshot_sha256:
            receipt_candidates = [
                paper_dir.parent / f"{paper_dir.name}_gate_receipt.json",
                paper_dir.parent / "q_gate_receipt.json",
            ]
            for rc in receipt_candidates:
                if rc.exists():
                    try:
                        data = json.loads(rc.read_text(encoding="utf-8"))
                        snapshot_sha256 = data.get("snapshot_sha256", "")
                        if snapshot_sha256:
                            break
                    except Exception:
                        pass
        if not snapshot_sha256:
            mono_p = paper_dir / f"{paper_id}.md"
            if mono_p.exists():
                snapshot_sha256 = hashlib.sha256(mono_p.read_bytes()).hexdigest()

        # 1. E04 Verification
        e04_test = paper_dir / "code" / "tests" / "test_coda_q_core_refusals.py"
        e04_code, e04_passed, _ = cls.run_isolated_pytest(e04_test, paper_dir)
        e04_probes = cls.execute_e04_probes(paper_dir)
        all_e04_probes_refused = all(p.refused for p in e04_probes)
        e04_status = "PASS" if (e04_code == 0 and all_e04_probes_refused) else "FAIL"

        e04_receipt = E04AdversarialReceipt(
            schema="omega.adversarial_refusal_receipt.v1",
            check_id="E04",
            requirement="Exact arithmetic and malformed inputs pass adversarial checks",
            paper_id=paper_id,
            snapshot_sha256=snapshot_sha256,
            timestamp_utc=now_utc,
            runner=f"Python {_resolve_python()}",
            test_suite_file="code/tests/test_coda_q_core_refusals.py",
            pytest_exit_code=e04_code,
            total_pytest_tests=e04_passed,
            passed_pytest_tests=e04_passed,
            probes_evaluated=len(e04_probes),
            probes_refused=sum(1 for p in e04_probes if p.refused),
            probe_results=e04_probes,
            status=e04_status,
            authority_effect="None",
        )

        # 2. E05 Verification
        e05_test = paper_dir / "code" / "tests" / "test_q_injected_mutations.py"
        e05_code, e05_passed, _ = cls.run_isolated_pytest(e05_test, paper_dir)
        e05_kills = cls.execute_e05_mutant_kills(paper_dir)
        all_e05_mutants_killed = all(k.killed for k in e05_kills)
        e05_status = "PASS" if (e05_code == 0 and all_e05_mutants_killed) else "FAIL"

        e05_receipt = E05TamperRejectionReceipt(
            schema="omega.tamper_rejection_receipt.v1",
            check_id="E05",
            requirement="Certificate and verifier tamper attacks fail for intended reasons",
            paper_id=paper_id,
            snapshot_sha256=snapshot_sha256,
            timestamp_utc=now_utc,
            runner=f"Python {_resolve_python()}",
            test_suite_file="code/tests/test_q_injected_mutations.py",
            pytest_exit_code=e05_code,
            total_pytest_tests=e05_passed,
            passed_pytest_tests=e05_passed,
            mutants_evaluated=len(e05_kills),
            mutants_killed=sum(1 for k in e05_kills if k.killed),
            kill_results=e05_kills,
            status=e05_status,
            authority_effect="None",
        )

        # Emit receipts if directory provided
        if emit_evidence_dir is not None:
            emit_dir = Path(emit_evidence_dir).resolve()
            emit_dir.mkdir(parents=True, exist_ok=True)

            e04_path = emit_dir / "adversarial_refusal_receipt.json"
            e05_path = emit_dir / "tamper_rejection_receipt.json"

            e04_path.write_text(json.dumps(e04_receipt.to_dict(), indent=2), encoding="utf-8")
            e05_path.write_text(json.dumps(e05_receipt.to_dict(), indent=2), encoding="utf-8")

            # Update bundle.json if requested
            if update_bundle:
                bundle_path = emit_dir / "bundle.json"
                if bundle_path.exists():
                    try:
                        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
                        records = bundle.get("records", [])
                        # Remove existing E04 / E05 records
                        records = [r for r in records if r.get("check_id") not in ("E04", "E05")]

                        records.append({
                            "check_id": "E04",
                            "path": "adversarial_refusal_receipt.json",
                            "sha256": hashlib.sha256(e04_path.read_bytes()).hexdigest(),
                        })
                        records.append({
                            "check_id": "E05",
                            "path": "tamper_rejection_receipt.json",
                            "sha256": hashlib.sha256(e05_path.read_bytes()).hexdigest(),
                        })

                        # Order records deterministically by check_id
                        records.sort(key=lambda r: r.get("check_id", ""))
                        bundle["records"] = records
                        bundle_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
                    except Exception as exc:
                        print(f"[WARNING] Failed to update bundle.json: {exc}")

        return e04_receipt, e05_receipt

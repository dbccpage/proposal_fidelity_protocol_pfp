"""Package demonstration 3: the four candidate phrase detectors.

Every sentence below is constructed fixture text written by the authors, not
observed model output. The demonstration shows only that the phrase lists in
``canaries.py`` behave as written on these sentences: each positive fixture is
flagged by its detector and each clean control, including a true statement about
the attractive Hubbard model, is not flagged. It measures no accuracy,
sensitivity, or false-suppression rate. See paper Section 3.1.
"""

from typing import NamedTuple

from demo_checks import require
from native_host_detector import scan_canaries

FIXTURE_TEXT = {
    "AM-FSP-8-UNRESTRICTED-SOLVER-CLAIM": (
        "Modern neural network quantum states and tensor networks have overcome this "
        "limitation, providing an unrestricted polynomial-time sign-free solution for all "
        "fermion systems without requiring P = NP."
    ),
    "AM-FSP-2-FRUSTRATED-OBSTRUCTION": (
        "For attractive U < 0, particle-hole symmetry holds on any lattice including the "
        "triangle and pentagon."
    ),
    "AM-FSP-7-UNVERIFIED-MAJORANA-LIFT": (
        "Continuous-time Majorana decomposition secures positive Monte Carlo weights."
    ),
    "AM-FSP-4-ORBIT-SUM-MISMATCH": (
        "Meron cluster algorithms eliminate sign oscillations across arbitrary non-bipartite "
        "parameter regimes, ignoring orbit-cancellation breakdowns."
    ),
}

TRUE_ATTRACTIVE_U_STATEMENT = (
    "For attractive U < 0 with equal spin populations, determinant QMC is "
    "sign-problem-free on any lattice."
)


class Case(NamedTuple):
    label: str
    text: str
    expected_canary: str | None


_CASES = [
    Case(
        label="Clean control: exact cochain calculation",
        text="We compute the discrete cochain boundary of a 1-chain on a bipartite square lattice over Q.",
        expected_canary=None,
    ),
    Case(
        label="Clean control: diagonal sign-gauge test",
        text="We test whether diagonal sign gauge S = diag(1, -1, 1) eliminates negative signs on this triangle.",
        expected_canary=None,
    ),
    Case(
        label="Clean control: true attractive-U statement",
        text=TRUE_ATTRACTIVE_U_STATEMENT,
        expected_canary=None,
    ),
    Case(
        label="AM-FSP-8 constructed sentence",
        text="Our novel tensor ansatz bypasses the sign problem in polynomial time on general frustrated topologies.",
        expected_canary="AM-FSP-8-UNRESTRICTED-SOLVER-CLAIM",
    ),
    Case(
        label="AM-FSP-8 paper fixture",
        text=FIXTURE_TEXT["AM-FSP-8-UNRESTRICTED-SOLVER-CLAIM"],
        expected_canary="AM-FSP-8-UNRESTRICTED-SOLVER-CLAIM",
    ),
    Case(
        label="AM-FSP-2 constructed sentence",
        text="We construct an exact particle-hole symmetry on triangle plaquettes with negative hopping.",
        expected_canary="AM-FSP-2-FRUSTRATED-OBSTRUCTION",
    ),
    Case(
        label="AM-FSP-2 paper fixture",
        text=FIXTURE_TEXT["AM-FSP-2-FRUSTRATED-OBSTRUCTION"],
        expected_canary="AM-FSP-2-FRUSTRATED-OBSTRUCTION",
    ),
    Case(
        label="AM-FSP-7 constructed sentence",
        text="A continuous majorana lift is applied across the whole non-orientable surface without topological defect strings.",
        expected_canary="AM-FSP-7-UNVERIFIED-MAJORANA-LIFT",
    ),
    Case(
        label="AM-FSP-7 paper fixture",
        text=FIXTURE_TEXT["AM-FSP-7-UNVERIFIED-MAJORANA-LIFT"],
        expected_canary="AM-FSP-7-UNVERIFIED-MAJORANA-LIFT",
    ),
    Case(
        label="AM-FSP-4 paper fixture",
        text=FIXTURE_TEXT["AM-FSP-4-ORBIT-SUM-MISMATCH"],
        expected_canary="AM-FSP-4-ORBIT-SUM-MISMATCH",
    ),
]


def run_demo() -> dict[str, str | int]:
    print("=" * 70)
    print("DEMO 3: FOUR CANDIDATE PHRASE DETECTORS ON CONSTRUCTED SENTENCES")
    print("=" * 70)

    detections = 0
    clean_count = 0
    backend = "python"
    for idx, case in enumerate(_CASES, 1):
        print(f"\n[Case {idx}] {case.label}")
        print(f"          Input: \"{case.text}\"")
        findings, backend = scan_canaries(case.text)

        if case.expected_canary is None:
            require(not findings, f"expected no finding, got {[f.canary_id for f in findings]}")
            clean_count += 1
            print("          -> no finding (as expected)")
        else:
            matched_ids = [f.canary_id for f in findings]
            require(
                case.expected_canary in matched_ids,
                f"expected {case.expected_canary} in {matched_ids}",
            )
            detections += 1
            for f in findings:
                print(f"          -> {f.canary_id} ({f.severity}); phrase '{f.pattern_matched}'")

    print("\n" + "=" * 70)
    print(
        f"DEMO 3 PASSED ({backend} backend): {detections} constructed positives flagged, "
        f"{clean_count} clean controls not flagged, out of {len(_CASES)} cases."
    )
    print("=" * 70)
    return {
        "status": "PASSED",
        "demo": "demo3_canaries_audit",
        "total_cases": len(_CASES),
        "detections": detections,
        "clean_controls": clean_count,
        "backend": backend,
    }


if __name__ == "__main__":
    raise SystemExit(0 if run_demo()["status"] == "PASSED" else 1)

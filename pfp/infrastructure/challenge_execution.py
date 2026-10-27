"""Isolated source judges, bounded host controls, and replay custody.

Never executes model-generated code. Each child imports one trusted retained
challenge to prevent old bare module names colliding. AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
import json
import platform
import subprocess
import sys
from collections import Counter
from copy import deepcopy
from pathlib import Path

from pfp.use_cases.pfp_proposal import CheckProposalUseCase, repair_feedback

from adversary.tests.pilots.challenge_suite.catalog import ROOT
from adversary.tests.pilots.challenge_suite.catalog import canonical
from adversary.tests.pilots.challenge_suite.catalog import digest
from adversary.tests.pilots.challenge_suite.catalog import load_case
from adversary.tests.pilots.challenge_suite.catalog import load_plan
from adversary.tests.pilots.challenge_suite.catalog import relocated
from adversary.tests.pilots.challenge_suite.catalog import selected_rows

# Separate entrypoints, not a common stored-answer comparator. C042's SAT/DRAT
# paths are complementary, so its one dispatcher is explicitly a single judge.
JUDGES = {
    11: "circulation_checker:verify_circulation_certificate potential_checker:verify_potential_certificate",
    12: "sheaf_algebraic_checker:verify_algebraic_certificate sheaf_echelon_checker:verify_echelon_certificate",
    13: "snf_algebraic_checker:verify_algebraic_certificate snf_elimination_checker:verify_elimination_certificate",
    14: "hodge_algebraic_checker:verify_algebraic_certificate hodge_elimination_checker:verify_elimination_certificate",
    15: "f2_algebraic_checker:check_algebraic_certificate independent_checker:check_independent_persistence",
    16: "algebraic_cup_checker:check_algebraic_cup_certificate independent_checker:check_independent_cup_products",
    17: "algebraic_holonomy_checker:check_algebraic_holonomy_certificate independent_checker:check_independent_holonomy",
    18: "frustration_checker:check_frustration_certificate independent_checker:check_independent_frustration",
    19: "h2_obstruction_checker:check_h2_certificate independent_checker:check_independent_h2",
    20: "exact_checker:check_certificate independent_checker:independent_check_certificate",
    21: "algebraic_checker:verify_certificate spectral_checker:verify_spectral_optimality",
    22: "exact_checker:check_certificate independent_checker:independent_check_certificate",
    23: "exact_checker:check_certificate independent_checker:independent_check_certificate",
    24: "exact_checker:check_certificate independent_checker:independent_check_certificate",
    25: "exact_checker:verify_exact independent_checker:verify_independent",
    26: "exact_checker:verify_exact independent_checker:verify_independent",
    27: "exact_checker:verify_exact independent_checker:verify_independent",
    28: "exact_checker:verify_exact independent_checker:verify_independent",
    29: "exact_checker:verify_exact",
    30: "exact_checker:verify_exact independent_checker:verify_independent",
    31: "u1_algebraic_checker:verify_chiral_u1_certificate u1_mitm_checker:verify_mitm_certificate",
    32: "sugra_matrix_checker:verify_sugra_matrix_certificate sugra_weight_checker:verify_sugra_weight_certificate",
    33: "freudenthal_checker:verify_freudenthal_certificate kostant_checker:verify_kostant_certificate",
    34: "affine_hnf_checker:verify_affine_hnf_certificate facet_point_checker:verify_facet_point_certificate",
    35: "jacobi_character_checker:verify_jacobi_character_certificate matrix_inversion_checker:verify_matrix_inversion_certificate",
    36: "hypergeometric_mirror_checker:verify_hypergeometric_mirror_certificate picard_fuchs_recurrence_checker:verify_picard_fuchs_recurrence_certificate",
    37: "combinatorial_fusion_checker:verify_combinatorial_fusion_certificate verlinde_cyclotomic_checker:verify_verlinde_cyclotomic_certificate",
    38: "combinatorial_primal_checker:verify_combinatorial_primal_certificate homology_dual_potential_checker:verify_homology_dual_potential_certificate",
    39: "homology_cohomology_checker:verify_homology_cohomology_certificate stabilizer_tableau_checker:verify_stabilizer_tableau_certificate",
    40: "coset_group_theory_checker:verify_coset_group_theory_certificate field_reduction_checker:verify_field_reduction_certificate",
    41: "exact_checker:verify_exact independent_checker:verify_independent",
    42: "dual_evaluator:evaluate_dual",
    43: "independent_checker:check_independent ramsey_vdw_checker:check",
    44: "exact_checker:check_exact independent_checker:independent_check",
    45: "exact_checker:check_exact independent_checker:check_independent",
    46: "exact_checker:check_exact independent_checker:check_independent",
    47: "exact_checker:check_solution independent_checker:independent_check",
    48: "exact_checker:check_solution independent_checker:independent_check",
    49: "exact_checker:check_solution independent_checker:independent_check",
    50: "exact_checker:check_solution independent_checker:independent_check",
    51: "exact_checker:check_solution independent_checker:check_solution",
    52: "exact_checker:check_solution independent_checker:check_solution",
    53: "exact_checker:check_solution independent_checker:check_solution",
    54: "exact_checker:check_exact independent_checker:independent_check",
    55: "exact_checker:check_exact independent_checker:independent_check",
    56: "exact_checker:check_exact independent_checker:independent_check",
    57: "exact_checker:check independent_checker:independent_check",
    58: "exact_checker:verify_candidate independent_checker:check_candidate_indep",
    59: "exact_checker:verify_candidate independent_checker:independent_check",
    60: "exact_checker:verify_candidate independent_checker:independent_check",
}


def c005_gate(case, answer):
    from pilots.llm_mechanism.c005_hosted_decode_controls.checkers import (
        verify_consistency_certificate,
        verify_cycle_repair,
    )
    from pilots.llm_mechanism.c005_hosted_decode_controls.schemas import (
        validate_json_schema,
    )

    valid, reason = validate_json_schema(
        answer, "consistency_verdict" if case["kind"] == "consistency" else "cycle_repair_solution"
    )
    if not valid:
        return False, reason
    if case["kind"] == "consistency":
        checked = verify_consistency_certificate(
            case["edges"], answer.get("verdict"), answer.get("certificate")
        )
        accepted = checked.is_valid
    else:
        if answer["status"] != "SOLVED":
            return False, "UNPARSEABLE is not a solved witness"
        checked = verify_cycle_repair(
            [e[2] for e in case["edges"]],
            case["weights"],
            answer.get("repaired", []),
            answer.get("weighted_l1"),
        )
        accepted = checked.is_valid and checked.is_optimal
    return accepted, checked.error_message or "Verified original C005 predicate"


def source_bindings(challenge):
    files = sorted(
        p
        for p in challenge.rglob("*.py")
        if "__pycache__" not in p.parts and "tests" not in p.relative_to(challenge).parts
    )
    if challenge.name.startswith("c029_"):
        from pfp.domain.quantum import c029_coset

        files.append(Path(c029_coset.__file__).resolve())
    return {p.relative_to(ROOT).as_posix(): digest(p.read_bytes()) for p in files}


def judges_for(challenge):
    n = int(challenge.name[1:4])
    if n == 1:
        from adversary.tests.pilots.challenge_suite.c001 import CHECKER_ID, check_answer
        return [(CHECKER_ID, check_answer)]
    if n == 5:
        return [("c005:task_predicate", c005_gate)]
    package = challenge.relative_to(ROOT).as_posix().replace("/", ".")
    suffix = (
        ".judge_packet.checkers"
        if (challenge / "judge_packet/checkers").is_dir()
        else ".judge_packet"
    )
    entries = []
    for entry in JUDGES[n].split():
        module, function = entry.split(":")
        entries.append(
            (entry, getattr(importlib.import_module(package + suffix + "." + module), function))
        )
    if n == 29:
        from pfp.domain.quantum.c029_coset import (
            CHECKER_ID,
            verify_independent_coset,
        )

        entries.append((CHECKER_ID, verify_independent_coset))
    return entries


def normalized_case(challenge_id: str, case: dict) -> dict:
    """Expose C024's declared participant input to its solver and both judges.

    Retained C024 case files wrap the public input exactly as its participant
    runner does. Other challenges and already unwrapped inputs keep their shape.
    The detached wrapped input cannot mutate the source case during preparation.
    """
    if challenge_id == "C024" and "input" in case:
        if type(case["input"]) is not dict:
            raise ValueError("INVALID_C024_INPUT_WRAPPER")
        return deepcopy(case["input"])
    return case


def worker(request):
    row = request["row"]
    source = ROOT / relocated(row["source"])
    challenge = (
        ROOT / relocated(row["challenge_path"])
        if "challenge_path" in row
        else next(p for p in source.parents if p.name[:4] == row["challenge"].lower())
    )
    case = load_case(row)
    try:
        case = normalized_case(row["challenge"], case)
        judges = judges_for(challenge)
        if request["kind"] == "NO_LLM":
            package = challenge.relative_to(ROOT).as_posix().replace("/", ".")
            if row["challenge"] == "C001":
                answer = importlib.import_module(package + ".solve").solve(case)
            elif row["challenge"] == "C005":
                answer = (
                    dict(verdict=case["expected_verdict"], certificate=case["expected_certificate"])
                    if case["kind"] == "consistency"
                    else dict(
                        status="SOLVED",
                        repaired=case["expected_repaired"],
                        weighted_l1=case["expected_weighted_l1"],
                    )
                )
            elif row["challenge"] == "C023":
                answer = importlib.import_module(package + ".reference_solver.synthesis").solve(case)
            elif row["challenge"] == "C060":
                answer = importlib.import_module(package + ".reference_solver.checker").check(
                    case["case"], case["cert"]
                )
            else:
                answer = importlib.import_module(package + ".reference_solver.solver").solve(case)
                if row["challenge"] in ("C015", "C016", "C017", "C018", "C019"):
                    if type(answer) is not tuple or len(answer) != 2 or type(answer[0]) is not dict:
                        raise ValueError("INVALID_WITNESS_TRACE_RESULT")
                    answer = answer[0]
            result = CheckProposalUseCase().check_answer(case, answer, judges)
            # Host baselines are not successful neural proposals.
            status = "FIXTURE_VERIFIED" if result.status == "HOST_ACCEPTED" else result.status
            return dict(
                status=status,
                failure_class=result.failure_class,
                judges=result.judges,
                answer=answer,
            )
        result = (
            CheckProposalUseCase().check_answer(case, request["answer"], judges)
            if request["kind"] == "CHECK_ANSWER"
            else CheckProposalUseCase().execute(case, request["raw_reply"], judges)
        )
        checked = dict(**result.to_dict(), feedback=repair_feedback(result))
        if any(j.get("error") == "IndependentVerificationUnavailable" for j in result.judges):
            checked.update(status="INFRASTRUCTURE_ERROR",
                failure_class="VERIFICATION_UNAVAILABLE", feedback=None)
            return checked
        if row["challenge"] == "C021" and result.failure_class != "ENVELOPE":
            from pfp.ffi import get_default_host
            from pfp.infrastructure.adapters.pfp_proposals import (
                SymbolGameProposalAdapter,
            )

            host = get_default_host()
            outcome = (host.stabilizer_check(case, request["answer"])
                if request["kind"] == "CHECK_ANSWER"
                else SymbolGameProposalAdapter(host).verify_q40(case, request["raw_reply"]))
            if outcome.is_err:
                return dict(
                    status="INFRASTRUCTURE_ERROR",
                    failure_class="NATIVE_HOST",
                    reason=str(outcome.unwrap_err()),
                )
            native = dict(outcome.unwrap())
            checked["native_outcome"] = native
            checked["native_binary_sha256"] = digest(host.binary_path.read_bytes())
            if native.get("success") is not True:
                checked.update(
                    status="INFRASTRUCTURE_ERROR", failure_class="NATIVE_HOST", feedback=None
                )
            elif ("Pass" in native.get("result", {})) != (
                result.status in ("HOST_ACCEPTED", "TYPED_REFUSAL")
            ):
                checked.update(
                    status="CHECKER_DEFECT", failure_class="NATIVE_DISAGREEMENT", feedback=None
                )
        return checked
    except Exception as exc:
        return dict(
            status="INFRASTRUCTURE_ERROR",
            failure_class="RUNTIME",
            error=type(exc).__name__,
            reason=str(exc),
        )


def isolated(request, timeout=20):
    try:
        process = subprocess.run(
            [sys.executable, "-m", "pfp.infrastructure.challenge_execution"],
            input=canonical(request),
            capture_output=True,
            cwd=ROOT,
            timeout=timeout,
        )
        if process.returncode:
            return dict(
                status="INFRASTRUCTURE_ERROR",
                failure_class="WORKER",
                reason=process.stderr.decode("utf-8", errors="replace")[-2000:],
            )
        return json.loads(process.stdout)
    except subprocess.TimeoutExpired:
        return dict(status="INFRASTRUCTURE_ERROR", failure_class="TIMEOUT", timeout_seconds=timeout)


def run_host(output, timeout=20):
    if output.exists():
        raise ValueError("RUN_ALREADY_EXISTS")
    output.mkdir(parents=True)
    plan = load_plan()
    rows = []
    for family in plan["families"]:
        for ordinal, row in enumerate(selected_rows(family)):
            result = isolated(dict(kind="NO_LLM", row=row), timeout)
            challenge = ROOT / relocated(next(
                c["path"] for c in family["challenges"] if c["challenge"] == row["challenge"]
            ))
            receipt = dict(
                schema="pfp.challenge-control.v1",
                authority_effect="None",
                execution_mode="NO_LLM",
                python=platform.python_version(),
                row=row,
                sources=source_bindings(challenge),
                result=result,
                provider_calls=0,
                cost_microusd=0,
            )
            raw = canonical(receipt)
            name = family["pilot_id"] + f"_{ordinal:03d}.json"
            (output / name).write_bytes(raw)
            rows.append(
                dict(
                    path=name,
                    sha256=digest(raw),
                    pilot_id=family["pilot_id"],
                    status=result["status"],
                    failure_class=result["failure_class"],
                )
            )
            print(
                json.dumps(
                    dict(
                        pilot=family["pilot_id"],
                        challenge=row["challenge"],
                        case=row["case_id"],
                        status=result["status"],
                    )
                ),
                flush=True,
            )
    manifest = dict(
        schema="pfp.challenge-controls.v1",
        authority_effect="None",
        rows=rows,
        totals=dict(Counter(r["status"] for r in rows)),
        provider_calls=0,
        cost_microusd=0,
    )
    (output / "manifest.json").write_bytes(canonical(manifest))
    return manifest


def replay_host(output, timeout=20):
    manifest = json.loads((output / "manifest.json").read_bytes())
    for item in manifest["rows"]:
        raw = (output / item["path"]).read_bytes()
        if digest(raw) != item["sha256"]:
            raise ValueError("RECEIPT_DIGEST_MISMATCH")
        receipt = json.loads(raw)
        if receipt["python"] != platform.python_version():
            raise ValueError("PYTHON_VERSION_DRIFT")
        for path, expected in receipt["sources"].items():
            if digest((ROOT / path).read_bytes()) != expected:
                raise ValueError("CHECKER_SOURCE_DRIFT")
        request = dict(kind="NO_LLM", row=receipt["row"])
        actual = isolated(request, timeout)
        if canonical(actual) != canonical(receipt["result"]):
            raise ValueError("REPLAY_RESULT_MISMATCH: " + item["path"])
    return manifest


if __name__ == "__main__":
    print(
        json.dumps(worker(json.loads(sys.stdin.buffer.read())), ensure_ascii=True, allow_nan=False)
    )

"""Replay trivial answers against the C045-C050 pilot checkers, as committed.

Paper 010 reports how many of ten panel cases each model passed in challenges
C045 to C050 (Table 3). This replay asks what the same pass rule gives for
answers that need no mathematics: an empty object, an abstention, a refusal
with each declared reason, and a constant verdict. It also records, for each
runner, the source line that builds the prompt and the case identifiers of the
panel.

The checkers are read from the commits that recorded the runs, extracted with
`git archive` into a temporary directory, and imported from there. The runner
scripts are parsed, never imported or executed, so no network or credential
code runs. The replay needs a git checkout that contains those commits.

Usage, from the series directory:

    py -3.12 tools/replay_formal_math_baselines.py            # print JSON
    py -3.12 tools/replay_formal_math_baselines.py --write    # update the record
    py -3.12 tools/replay_formal_math_baselines.py --check    # compare with it

With ``--checkers-at REV`` the same panels (still read from the run commits) are
replayed against the checkers of a later commit, for example a corrected
harness; ``--write`` and ``--check`` then use a record named for that commit.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import io
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

SERIES = Path(__file__).resolve().parents[1]
RECORD = SERIES / "verification" / "formal_math_baselines.json"
E = "omega_engine_projects/mssn_sn_symgam/challenges/e_formal_math"
PKG = E.replace("/", ".")
RUN_C045 = "ea2b55d841bdbe283f2f6ac77abe8a1677cbf0f8"
RUN_C046_C050 = "46bd1dec156260f073b77caa07d8a453f8efad30"
# At RUN_C045, reference_solver/knots_catalog.py annotates with `Tuple` without
# importing it, so Python 3.12 cannot import the C045 exact checker (Python 3.14
# defers annotations and can). The merge commit below changes only that import
# line in the C045 folder, so the checkers are replayed from it.
CHECK_C045 = "c568c20062697b54ddb8729e2476d4cfdb5c4982"
PARENT_INITS = ("omega_engine_projects/__init__.py", "omega_engine_projects/mssn_sn_symgam/__init__.py")

# challenge: (commit of the runner, commit of the checkers, folder, runner,
#             second checker, exact checker)
CHALLENGES = {
    "C045": (RUN_C045, CHECK_C045, "c045_knot_polynomials_from_pd", "run_c045_matrix.py",
             ("judge_packet.checkers.independent_checker", "check_independent"),
             ("judge_packet.checkers.exact_checker", "check_exact")),
    "C046": (RUN_C046_C050, RUN_C046_C050, "c046_knuth_bendix_completion", "run_c046_matrix.py",
             ("judge_packet.checkers.independent_checker", "check_independent"),
             ("judge_packet.checkers.exact_checker", "check_exact")),
    "C047": (RUN_C046_C050, RUN_C046_C050, "c047_sequence_law_discovery", "run_c047_matrix.py",
             ("judge_packet.independent_checker", "independent_check"),
             ("judge_packet.exact_checker", "check_solution")),
    "C048": (RUN_C046_C050, RUN_C046_C050, "c048_ternary_quadratic_forms", "run_c048_matrix.py",
             ("judge_packet.independent_checker", "independent_check"),
             ("judge_packet.exact_checker", "check_solution")),
    "C049": (RUN_C046_C050, RUN_C046_C050, "c049_finite_category_universal_constructions", "run_c049_matrix.py",
             ("judge_packet.independent_checker", "independent_check"),
             ("judge_packet.exact_checker", "check_solution")),
    "C050": (RUN_C046_C050, RUN_C046_C050, "c050_equational_theorem_proving", "run_c050_matrix.py",
             ("judge_packet.independent_checker", "independent_check"),
             ("judge_packet.exact_checker", "check_solution")),
}


# The author's reading of each panel identifier (Paper 010, Table 4): whether it
# names the expected verdict or answer, names only the object of the task, or
# neither. The replay checks that the three lists partition the panel.
IDENTIFIER_READING = {
    "C045": {
        "verdict_or_answer": ["c045_m02_trefoil_identify", "c045_m04_figure8_identify", "c045_m06_cinquefoil_identify",
                              "c045_m07_compare_trefoil_figure8", "c045_m08_compare_trefoil_gauge",
                              "c045_m09_refusal_corrupt_edge", "c045_m10_refusal_bad_understrand"],
        "object": ["c045_m01_unknot", "c045_m03_trefoil_polynomials", "c045_m05_figure8_polynomials"],
        "neither": [],
    },
    "C046": {
        "verdict_or_answer": ["c046_m04_check_confluent_group", "c046_m05_check_non_confluent_group",
                              "c046_m08_refusal_commutativity", "c046_m09_refusal_malformed_term",
                              "c046_m10_refusal_step_budget"],
        "object": ["c046_m01_group_complete", "c046_m02_monoid_complete", "c046_m03_semilattice_complete"],
        "neither": ["c046_m06_reduce_inv_inv", "c046_m07_reduce_nested"],
    },
    "C047": {
        "verdict_or_answer": ["c047_m07_prand_decoy", "c047_m08_order9_decoy", "c047_m09_non_integer_term",
                              "c047_m10_note_fib_diverges"],
        "object": ["c047_m01_fibonacci", "c047_m02_catalan", "c047_m03_factorial", "c047_m04_period_4",
                   "c047_m05_jacobsthal", "c047_m06_preperiod_fib"],
        "neither": [],
    },
    "C048": {
        "verdict_or_answer": ["c048_m01_solv_11_m2", "c048_m02_solv_pyth", "c048_m03_solv_35_m8", "c048_m04_solv_27_m9",
                              "c048_m05_obstr_inf_111", "c048_m06_obstr_inf_235", "c048_m07_obstr_2_11_m7",
                              "c048_m08_obstr_p_12_m7", "c048_m09_malformed", "c048_m10_poison_claim_no_solution"],
        "object": [],
        "neither": [],
    },
    "C049": {
        "verdict_or_answer": ["c049_m05_no_product_disc2", "c049_m07_adj_identity", "c049_m08_not_adj_cardinality",
                              "c049_m09_poison_non_assoc", "c049_m10_poison_bait_claim"],
        "object": ["c049_m01_product_poset_3", "c049_m02_equalizer_same", "c049_m03_pullback_cospan",
                   "c049_m04_terminal_linear", "c049_m06_coproduct_poset"],
        "neither": [],
    },
    "C050": {
        "verdict_or_answer": ["c050_m06_cm_idempotent_comm", "c050_m07_cm_unary_proj",
                              "c050_m08_cm_left_unit_implies_right", "c050_m09_poison_fake_note",
                              "c050_m10_poison_malformed"],
        "object": ["c050_m01_involution", "c050_m02_double_neg", "c050_m03_combinator_I", "c050_m04_assoc_shift",
                   "c050_m05_comm_swap"],
        "neither": [],
    },
}


def _refusal(reason: str):
    return lambda case: {"case_id": case["case_id"], "status": "REFUSED", "reason": reason, "witness": {}}


def _out_of_scope(witness):
    return lambda case: {"case_id": case["case_id"], "status": "OUT_OF_SCOPE", "witness": witness}


def _solved(**fields):
    return lambda case: {"case_id": case["case_id"], "status": "SOLVED", **fields}


COMMON = {
    "empty object": lambda case: {},
    "case_id only": lambda case: {"case_id": case["case_id"]},
    "abstain (UNKNOWN)": lambda case: {"case_id": case["case_id"], "status": "UNKNOWN"},
}
SPECIFIC = {
    "C045": {f"refuse all, {r}": _refusal(r) for r in ("EDGE_LABEL_MULTIPLICITY", "ORIENTATION_INCONSISTENT", "NON_PLANAR")},
    "C046": {f"refuse all, {r}": _refusal(r) for r in ("ORDER_FAILURE", "MALFORMED_TERM", "MAX_STEPS_EXCEEDED", "MALFORMED_INPUT")},
    "C047": {
        "out of scope, NON_INTEGER_TERM at 0": _out_of_scope({"reason": "NON_INTEGER_TERM", "index": 0}),
        "recurrence with empty polys": _solved(kind="RECURRENCE", start=0, polys=[]),
        "none within bounds, empty minor_rows": lambda case: {
            "case_id": case["case_id"], "status": "SOLVED", "kind": "NONE_WITHIN_BOUNDS",
            "order": case["r_max"], "degree": case["d_max"], "start_range": [0, 5], "minor_rows": []},
    },
    "C048": {
        "out of scope, MALFORMED_COEFFICIENT": _out_of_scope({"reason": "MALFORMED_COEFFICIENT"}),
        "constant obstruction at inf": _solved(kind="LOCAL_OBSTRUCTION", place="inf"),
        "constant obstruction at 2": _solved(kind="LOCAL_OBSTRUCTION", place="2"),
    },
    "C049": {
        "out of scope, NON_ASSOCIATIVE": _out_of_scope({"reason": "NON_ASSOCIATIVE"}),
        "constant DOES_NOT_EXIST": _solved(kind="DOES_NOT_EXIST"),
    },
    "C050": {
        "out of scope, MALFORMED": _out_of_scope("MALFORMED"),
    },
}


def repo_root() -> Path:
    out = subprocess.run(["git", "-C", str(SERIES), "rev-parse", "--show-toplevel"],
                         capture_output=True, text=True, check=True)
    return Path(out.stdout.strip())


def git_bytes(root: Path, rev: str, path: str) -> bytes:
    return subprocess.run(["git", "-C", str(root), "show", f"{rev}:{path}"], capture_output=True, check=True).stdout


def extract(root: Path, rev: str, paths: list[str], dest: Path) -> None:
    tar = subprocess.run(["git", "-C", str(root), "archive", "--format=tar", rev, *paths],
                         capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(tar)) as archive:
        archive.extractall(dest, filter="data")


def panel(source: str) -> list[dict]:
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "TEST_CASES" for t in node.targets):
            cases = ast.literal_eval(node.value)
            if not isinstance(cases, list) or not cases:
                raise ValueError("TEST_CASES is not a non-empty list")
            return cases
    raise ValueError("runner defines no TEST_CASES")


def accepts(check, case: dict, answer: dict) -> bool:
    try:
        verdict = check(case, answer)
    except Exception:  # noqa: BLE001 - a crash is recorded as not accepted
        return False
    return verdict[0] is True


def resolve(root: Path, rev: str) -> str:
    return subprocess.run(["git", "-C", str(root), "rev-parse", "--verify", f"{rev}^{{commit}}"],
                          capture_output=True, text=True, check=True).stdout.strip()


def replay(checkers_at: str | None = None) -> dict:
    root = repo_root()
    sys.dont_write_bytecode = True
    later = resolve(root, checkers_at) if checkers_at else None
    if later:
        scope = ("Trivial answers replayed against the C045-C050 checkers of a later commit, on the panels of the "
                 "commits that recorded the runs; a case passes when both checkers accept. No model is called.")
        commits = {"runs": {"C045": RUN_C045, "C046-C050": RUN_C046_C050}, "checkers": later}
    else:
        scope = ("Trivial answers replayed against the C045-C050 pilot checkers at the commits that recorded the runs; "
                 "a case passes when both checkers accept, as in the runners. No model is called.")
        commits = {"C045 run": RUN_C045, "C045 checkers": CHECK_C045, "C046-C050 run and checkers": RUN_C046_C050}
    result: dict = {"scope": scope, "commits": commits, "challenges": {}}
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp)
        extract(root, later or RUN_C046_C050, list(PARENT_INITS), dest)
        for _run, checkers, folder, _runner, _second, _exact in CHALLENGES.values():
            extract(root, later or checkers, [f"{E}/{folder}"], dest)
        sys.path.insert(0, str(dest))
        try:
            for cid, (run, checkers, folder, runner, second, exact) in CHALLENGES.items():
                checkers = later or checkers
                source = git_bytes(root, run, f"{E}/{folder}/{runner}").decode("utf-8")
                cases = panel(source)
                modules = [importlib.import_module(f"{PKG}.{folder}.{name}") for name, _fn in (second, exact)]
                for module in modules:
                    if not Path(module.__file__).resolve().is_relative_to(dest.resolve()):
                        raise RuntimeError(f"{module.__name__} was not imported from the extracted commit")
                check_second = getattr(modules[0], second[1])
                check_exact = getattr(modules[1], exact[1])
                responders = {**COMMON, **SPECIFIC[cid]}
                rows = {}
                for name, make in responders.items():
                    both = [c["case_id"] for c in cases
                            if accepts(check_exact, c, make(c)) and accepts(check_second, c, make(c))]
                    rows[name] = {
                        "second_checker_accepts": sum(accepts(check_second, c, make(c)) for c in cases),
                        "exact_checker_accepts": sum(accepts(check_exact, c, make(c)) for c in cases),
                        "both_accept": len(both),
                        "cases_passed": both,
                    }
                prompt_lines = [line.strip() for line in source.splitlines() if "Case ID:" in line]
                reading = IDENTIFIER_READING[cid]
                read_ids = [case_id for group in reading.values() for case_id in group]
                if sorted(read_ids) != sorted(c["case_id"] for c in cases):
                    raise ValueError(f"{cid}: the identifier reading does not partition the panel")
                result["challenges"][cid] = {
                    "runner_commit": run,
                    "checker_commit": checkers,
                    "runner": f"{E}/{folder}/{runner}",
                    "prompt_lines": prompt_lines,
                    "panel_case_ids": [c["case_id"] for c in cases],
                    "panel_cases_with_note": [c["case_id"] for c in cases if "note" in c],
                    "identifier_reading": {key: len(value) for key, value in reading.items()},
                    "identifier_reading_ids": reading,
                    "panel_size": len(cases),
                    "trivial_answers": rows,
                    "best_trivial_both_accept": max(r["both_accept"] for r in rows.values()),
                }
        finally:
            sys.path.remove(str(dest))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write the record in verification/")
    mode.add_argument("--check", action="store_true", help="compare with the record in verification/")
    parser.add_argument("--checkers-at", metavar="REV", help="replay against the checkers of a later commit")
    args = parser.parse_args()
    result = replay(args.checkers_at)
    record = RECORD
    if args.checkers_at:
        record = RECORD.with_name(f"formal_math_baselines_checkers_at_{result['commits']['checkers'][:12]}.json")
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.write:
        record.write_bytes(text.encode("utf-8"))
        print(f"wrote {record.relative_to(SERIES).as_posix()}")
        return 0
    if args.check:
        if record.read_bytes() != text.encode("utf-8"):
            print(f"{record.name} differs from the replay", file=sys.stderr)
            return 1
        print(f"{record.name} matches the replay")
        return 0
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

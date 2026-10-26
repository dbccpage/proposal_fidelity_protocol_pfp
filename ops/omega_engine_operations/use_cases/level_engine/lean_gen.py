"""Generate the Lean certificates for the value clauses of ``distance_form``
and of every level whose spec renders its own certificate module
(``LEAN_MODULE`` and ``lean_render``), and the axiom-report module.

    symbol-game level-engine lean generate
    symbol-game level-engine lean generate --check

Each certificate states the verdict the Python engine computed for one
fixture; the kernel re-decides it with the exact-rational library, so a
disagreement between the two fails ``lake build``.  Only fixtures whose value
clauses the engine evaluates (their relational clauses hold) get
certificates, matching the level runner.

AuthorityEffect: None
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING

from omega_engine_operations.domain.level_engine_context import (
    LevelEngineResourcesPort,
    configure_context,
    current_context,
)

if TYPE_CHECKING:
    from omega_engine_operations.use_cases.level_engine.research_engine.exact.q import Q
    from omega_engine_operations.use_cases.level_engine.research_engine.level import (
        Fixture,
        LevelResult,
        Spec,
    )
    from omega_engine_operations.use_cases.level_engine.research_engine.structure import (
        FiniteStructure,
    )


def load_spec(cid: str) -> Spec:
    from omega_engine_operations.use_cases.level_engine.research_engine.level import (
        load_spec as load,
    )
    return load(cid)


def load_fixtures(path: Path) -> tuple[Fixture, ...]:
    from omega_engine_operations.use_cases.level_engine.research_engine.level import (
        load_fixtures as load,
    )
    return load(path)


def run_level(cid: str) -> LevelResult:
    from omega_engine_operations.use_cases.level_engine.research_engine.level import (
        run_level as run,
    )
    return run(cid)


# Levels whose spec renders its own certificate module, in report order.
LEAN_LEVELS: tuple[str, ...] = (
    "answer_keeping", "associator_tables", "bound_axioms", "budgeted_releases", "class_operations", "closed_faces",
    "commuting_checks", "confirmed_runs", "cycle_words", "dual_endpoints", "face_products", "far_blind",
    "filtered_pages", "flow_certificate", "forced_differences", "hinge_deficits", "isolated_roots", "joint_payoffs",
    "joint_rank", "loop_products", "mirror_pairs", "named_frames", "ordered_log", "ordered_splits", "outward_bounds",
    "overlap_choices", "patched_views", "rated_limits", "refined_sums", "reindexed_fibres", "rim_cochains",
    "same_background", "scale_steps", "scope_fence", "side_reduction", "signed_cells", "signed_totals",
    "size_keeping", "split_weights", "square_one", "stable_profiles", "step_weights", "table_polynomial",
    "table_roots", "three_way_split", "two_party_bound", "unit_rows", "use_once_terms", "walk_transport",
    "weighted_update", "witnessed_triples",
)

LIBRARY_THEOREMS = (
    "ExactRat.Frac.eqv_trans",
    "ExactRat.Frac.add_respects",
    "ExactRat.Frac.mul_respects",
    "ExactRat.Frac.inv_respects",
    "ExactRat.Frac.pos_respects",
    "ExactRat.QN.instDecidableEq",
    "ExactRat.QN.add_comm",
    "ExactRat.QN.add_assoc",
    "ExactRat.QN.zero_add",
    "ExactRat.QN.add_zero",
    "ExactRat.QN.neg_add_cancel",
    "ExactRat.QN.mul_comm",
    "ExactRat.QN.mul_assoc",
    "ExactRat.QN.one_mul",
    "ExactRat.QN.mul_one",
    "ExactRat.QN.zero_mul",
    "ExactRat.QN.mul_add",
    "ExactRat.QN.add_mul",
    "ExactRat.QN.zero_ne_one",
    "ExactRat.QN.inv_zero",
    "ExactRat.QN.mul_inv_cancel",
    "ExactRat.QN.inv_mul_cancel",
    "ExactRat.QN.neg_add",
    "ExactRat.QN.pos_add",
    "ExactRat.QN.pos_mul",
    "ExactRat.QN.trichotomy",
    "ExactRat.QN.not_pos_and_pos_neg",
    "ExactRat.QN.lt_irrefl",
    "ExactRat.QN.lt_trans",
    "ExactRat.QN.lt_trichotomy",
    "ExactRat.QN.add_lt_add_right",
    "ExactRat.QN.mul_pos",
    "ExactRat.det_one_by_one",
    "ExactRat.det_two_by_two",
    "ExactRat.QN.eval_padd",
    "ExactRat.QN.eval_shift",
    "ExactRat.QN.eval_diff",
    "ExactRat.QN.nonneg_step",
    "ExactRat.QN.pos_step",
    "ExactRat.QN.nonneg_from",
    "ExactRat.QN.pos_from",
    "ExactRat.QN.eval_reverse",
    "ExactRat.QN.halving_bound",
)


def _q(x: Q) -> str:
    return f"QN.ofPair ({x.num}) {x.den}"


def evaluated() -> list[tuple[str, FiniteStructure, dict[str, str]]]:
    """Fixtures whose value clauses the engine evaluates, in fixture order."""
    fixtures = {f.fid: f for f in load_fixtures(current_context().resource("payload/distance_form"))}
    out = []
    for v in run_level("distance_form").verdicts:
        decoded = dict(v.decoded)
        if decoded.get("form_positive") in ("PASS", "FAIL"):
            out.append((v.fid, fixtures[v.fid].structure, decoded))
    return out


def certificates() -> list[tuple[str, str, str]]:
    """(theorem name, statement, value clause) for every evaluated fixture."""
    from omega_engine_operations.use_cases.level_engine.research_engine.exact.linalg import (
        first_nonpositive_minor,
    )

    spec = load_spec("distance_form")
    out: list[tuple[str, str, str]] = []
    for fid, fs, decoded in evaluated():
        form = getattr(spec, "form")(fs)
        assert form is not None
        name = f"table_{fid}"
        diag = "true" if decoded["diagonal_zero"] == "PASS" else "false"
        pos = "true" if decoded["form_positive"] == "PASS" else "false"
        k = first_nonpositive_minor(form)
        first = "none" if k is None else f"some {k}"
        out.append((f"{fid}_diagonal_zero", f"diagonalZero {name} = {diag}", "diagonal_zero"))
        out.append((f"{fid}_form_positive", f"formPositive {name} = {pos}", "form_positive"))
        out.append((f"{fid}_first_nonpositive", f"firstNonpositive (leadingMinors (form {name})) 1 = {first}",
                    "form_positive"))
    return out


def tables() -> list[tuple[str, list[list[Q]]]]:
    spec = load_spec("distance_form")
    out = []
    for fid, fs, _ in evaluated():
        table = getattr(spec, "table")(fs)
        assert table is not None
        pts = fs.elements("pt")
        out.append((fid, [[table[(x, y)] for y in pts] for x in pts]))
    return out


def render_certificates() -> str:
    lines = [
        "import ExactRat",
        "",
        "/-!",
        "# Value clauses of `distance_form`, decided by the kernel",
        "",
        "Generated by `tools/lean_gen.py` from the fixtures; do not edit. Each table",
        "lists the squared distance of every ordered pair of points. Each theorem",
        "states the verdict the Python engine computed, and `decide` re-checks it with",
        "the exact-rational library.",
        "",
        "AuthorityEffect: None",
        "-/",
        "",
        "namespace DistanceForm",
        "",
        "open ExactRat",
        "",
        "/-- Entry `(i, j)` of a table. -/",
        "def entry (d : Mat) (i j : Nat) : QN := (d.getD i []).getD j 0",
        "",
        "/-- The form of a table: for points `i, j` other than the first,",
        "`(d(0,i) + d(0,j) - d(i,j)) / 2`. -/",
        "def form (d : Mat) : Mat :=",
        "  (List.range (d.length - 1)).map fun i =>",
        "    (List.range (d.length - 1)).map fun j =>",
        "      (entry d 0 (i + 1) + entry d 0 (j + 1) - entry d (i + 1) (j + 1)) * QN.ofPair 1 2",
        "",
        "/-- Every point is at squared distance zero from itself. -/",
        "def diagonalZero (d : Mat) : Bool := (List.range d.length).all fun i => decide (entry d i i = 0)",
        "",
        "/-- The table is symmetric and its form has only positive leading minors. -/",
        "def formPositive (d : Mat) : Bool := isSymmetric d && minorsPositive (form d)",
        "",
    ]
    for fid, rows in tables():
        lines.append(f"def table_{fid} : Mat :=")
        body = ",\n    ".join("[" + ", ".join(_q(x) for x in row) + "]" for row in rows)
        lines.append(f"  [{body}]")
        lines.append("")
    for name, stmt, _ in certificates():
        lines.append(f"theorem {name} : {stmt} := by decide")
        lines.append("")
    lines += ["end DistanceForm", ""]
    return "\n".join(lines)


def module_name(cid: str) -> str:
    return str(getattr(load_spec(cid), "LEAN_MODULE"))


def module_path(cid: str) -> Path:
    return current_context().lean_path(f"{module_name(cid)}.lean")


def render_module(cid: str) -> str:
    spec = load_spec(cid)
    render = getattr(spec, "lean_render")
    text: str = render(load_fixtures(current_context().resource(f"payload/{cid}")), run_level(cid).verdicts)
    return text


def module_theorems(cid: str) -> list[str]:
    spec = load_spec(cid)
    return [name for name, _, _ in getattr(spec, "lean_certificates")(run_level(cid).verdicts)]


def reported() -> list[str]:
    out = list(LIBRARY_THEOREMS) + [f"DistanceForm.{name}" for name, _, _ in certificates()]
    for cid in LEAN_LEVELS:
        out += module_theorems(cid)
    return out


def render_report() -> str:
    lines = [
        "import ExactRat",
        "import DistanceForm",
        *[f"import {module_name(cid)}" for cid in LEAN_LEVELS],
        "",
        "/-! Axiom report. Generated by `tools/lean_gen.py`; do not edit. AuthorityEffect: None -/",
        "",
    ]
    lines += [f"#print axioms {n}" for n in reported()]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None, *, context: LevelEngineResourcesPort | None = None) -> int:
    if context is not None:
        configure_context(context)
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    bad = 0
    files = [(current_context().lean_path("DistanceForm.lean"), render_certificates())] + [(module_path(c), render_module(c)) for c in LEAN_LEVELS]
    for path, text in files + [(current_context().lean_path("AxiomReport.lean"), render_report())]:
        data = text.encode("ascii")
        if args.check:
            if not path.exists() or path.read_bytes() != data:
                print(f"LEAN SOURCE DRIFT: {path.name}")
                bad += 1
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    if args.check and not bad:
        print("LEAN SOURCES OK: generated certificates and report are current")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

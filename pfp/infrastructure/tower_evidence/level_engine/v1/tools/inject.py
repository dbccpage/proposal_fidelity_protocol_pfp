"""Prove the guards by injection.

Each injection is a minimal edit on disk, never committed.  It must make the
named command fail and print the exact code; then the edit is reversed and
the same command must pass.  The tree must be clean before and after.  The
result table is written to ``INJECTIONS.md`` (no timings, no timestamps).

    python tools/inject.py            # run every injection
    python tools/inject.py --only I1  # one

AuthorityEffect: None
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
BUILD = [PY, "run_bootstrap.py", "--out", "_scratch/inj"]
EXPECT_TEST = [PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_levels.py", "-k", "frozen_expectations"]
WATCHED = "curva" + "ture"  # assembled so this file does not carry the word


def _json(fn: Callable[[dict[str, object]], None]) -> Callable[[str], str]:
    def go(text: str) -> str:
        doc = json.loads(text)
        fn(doc)
        return json.dumps(doc, sort_keys=True, indent=2, ensure_ascii=True) + "\n"

    return go


def _replace(old: str, new: str) -> Callable[[str], str]:
    def go(text: str) -> str:
        if old not in text:
            raise RuntimeError(f"anchor not found: {old[:60]!r}")
        return text.replace(old, new, 1)

    return go


def _drop_fixture(fid: str) -> Callable[[dict[str, object]], None]:
    def go(doc: dict[str, object]) -> None:
        fx = doc["fixtures"]
        assert isinstance(fx, list)
        doc["fixtures"] = [f for f in fx if f["id"] != fid]

    return go


def _own_neg_equals_pos(doc: dict[str, object]) -> None:
    fx = doc["fixtures"]
    assert isinstance(fx, list)
    pos = next(f for f in fx if f["id"] == "pos")
    neg = next(f for f in fx if f["id"] == "own_neg")
    neg["structure"] = pos["structure"]
    neg["protected"] = pos["protected"]


def _empty_positive(doc: dict[str, object]) -> None:
    fx = doc["fixtures"]
    assert isinstance(fx, list)
    next(f for f in fx if f["id"] == "pos")["structure"] = {}


def _flip_pinned_tree(doc: dict[str, object]) -> None:
    vendored = doc["vendored"]
    assert isinstance(vendored, dict)
    tree = str(vendored["19L57G1"]["tree"])
    vendored["19L57G1"]["tree"] = tree[:-1] + ("0" if tree[-1] != "0" else "1")


LIFT = (PY, "tools/lift_check.py")
WORKING_TREE_RECORD = (PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_reach_records.py", "-k")
PROPOSALS = "lifts/record_reading/proposals.json"


def _step(k: int, key: str, value: object) -> Callable[[str], str]:
    """Set one field of one proposed step (a mutated lift)."""
    def fn(doc: dict[str, object]) -> None:
        steps = doc["steps"]
        assert isinstance(steps, list)
        steps[k][key] = value

    return _json(fn)


def _context_positions(doc: dict[str, object]) -> None:
    steps = doc["steps"]
    assert isinstance(steps, list)
    steps[0]["context_witness"]["positions"] = [0, 1]


def _reblock_023(doc: dict[str, object]) -> None:
    levels = doc["levels"]
    assert isinstance(levels, list)
    next(e for e in levels if e["level"] == 23)["blocked_by"] = ["witness_not_sealed"]


def _both(first: Callable[[str], str], second: Callable[[str], str]) -> Callable[[str], str]:
    """Two minimal edits to one file, applied together."""
    def go(text: str) -> str:
        return second(first(text))

    return go


NAMED_SOURCE_TEST = (PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_levels.py", "-k", "named_source")


@dataclass(frozen=True)
class Injection:
    ident: str
    guard: str
    what: str
    path: str
    edit: Callable[[str], str]
    commands: tuple[tuple[str, ...], ...]
    code: str


INJECTIONS = (
    Injection("I1", "fixed claims", "the candidate builder offers instances on claim forms (a claim-overwrite repair)",
              "engine/search.py",
              _replace("    out: list[Item] = []\n    for f, sorts in s.witness_forms:",
                       "    out: list[Item] = [NewInst(f, (0,) * s.base.forms[f]) for f in sorted(s.claim_forms)]\n"
                       "    for f, sorts in s.witness_forms:"),
              (tuple(BUILD),), "CLAIM_FROZEN"),
    Injection("I2", "embargo", "a challenge declares a four-item search bound",
              "payload/cell_orientation/spec.py", _replace("BOUND = 3\n", "BOUND = 4\n"),
              (tuple(BUILD),), "GUARD_EMBARGO"),
    Injection("I3", "exact values", "a fixture value is written as a JSON float",
              "payload/distance_form/instance.json", _replace('"1/1"', "1.0"),
              (tuple(BUILD),), "RR-FLOAT"),
    Injection("I4", "fixture expectations", "the own negative is replaced by the positive",
              "payload/edge_endpoints/instance.json", _json(_own_neg_equals_pos),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I5", "intake", "the own negative is deleted",
              "payload/edge_endpoints/instance.json", _json(_drop_fixture("own_neg")),
              (tuple(BUILD),), "MISSING_NEGATIVE"),
    Injection("I6", "intake", "the positive is an empty payload",
              "payload/cell_faces/instance.json", _json(_empty_positive),
              (tuple(BUILD),), "EMPTY_FIXTURE"),
    Injection("I7", "exhaustion", "the enumeration stops one item count early",
              "engine/search.py",
              _replace("    for size in range(0, bound.max_items + 1):", "    for size in range(0, bound.max_items):"),
              (tuple(BUILD),), "RR-EXHAUSTION"),
    Injection("I8", "custody", "one character of the pinned tree id changes",
              "PINS.json", _json(_flip_pinned_tree),
              ((PY, "tools/vendor.py", "--check"),), "RR-PIN"),
    Injection("I9", "transport", "the typed map drops the relations, so fixtures coincide",
              "outward/bundles.py",
              _replace('        "relations": structure["tuples"],', '        "relations": [],'),
              (tuple(BUILD),), "RR-TRANSPORT-COLLAPSE"),
    Injection("I10", "hygiene", "a watched word is appended to a payload restatement",
              "payload/cell_faces/RESTATEMENT.md", lambda t: t + f"\nA note on {WATCHED}.\n",
              ((PY, "gate.py", "--step", "hygiene"),), "watch=1"),
    Injection("I11", "agreement", "the compile step drops the separation requirement (a lossy restatement)",
              "payload/edge_endpoints/spec.py",
              _replace("        reqs.append(Separate(\"protect\", min(i, j), max(i, j)))",
                       "        pass"),
              (tuple(BUILD), (PY, "tools/preflight_draft.py", "_scratch/inj", "L002", "tests/checkers/arcs.py")),
              "DISAGREEMENT:near_protect"),
    Injection("I12", "clause census", "a hosted challenge declares its answer native (type D)",
              "payload/distance_form/spec.py", _replace('ANSWER_TYPE = "M"', 'ANSWER_TYPE = "D"'),
              (tuple(EXPECT_TEST),), "ANSWER_TYPE_DISAGREES"),
    Injection("I13", "descent", "decoding gives a fresh datum an old meaning",
              "engine/encoding.py",
              _replace('        raise NonDescent("NON_DESCENT_DATUM", f"datum {n} is not an element of the claim")',
                       "        pass"),
              (tuple(EXPECT_TEST),), "RR-NON-DESCENT"),
    Injection("I14", "binding", "a ladder row digest is edited",
              "bindings/L003.json", _replace('"row_sha256": "sha256:', '"row_sha256": "sha256:0'),
              ((PY, "tools/bind.py", "--check"),), "ROW_DIGEST"),
    Injection("I15", "Lean tokens", "a law's proof is replaced by a placeholder token",
              "engine/lean/ExactRat/Laws.lean",
              _replace("theorem inv_zero : (0 : QN)\u207b\u00b9 = 0 := by\n  apply sound\n  exact Frac.eqv_refl _",
                       "theorem inv_zero : (0 : QN)\u207b\u00b9 = 0 := by\n  so" + "rry"),
              ((PY, "gate.py", "--step", "lean"),), "FORBIDDEN TOKEN"),
    Injection("I16", "Lean axioms", "a reported law is proved through Classical.choice",
              "engine/lean/ExactRat/Laws.lean",
              _replace("theorem inv_zero : (0 : QN)\u207b\u00b9 = 0 := by\n  apply sound\n  exact Frac.eqv_refl _",
                       "theorem inv_zero : (0 : QN)\u207b\u00b9 = 0 :=\n"
                       "  Classical.choice \u27e8by apply sound; exact Frac.eqv_refl _\u27e9"),
              ((PY, "gate.py", "--step", "lean"),), "RR-AXIOM"),
    Injection("I17", "Lean certificates", "a generated certificate states the opposite verdict",
              "payload/distance_form/lean/DistanceForm.lean",
              _replace("theorem own_neg_form_positive : formPositive table_own_neg = false := by decide",
                       "theorem own_neg_form_positive : formPositive table_own_neg = true := by decide"),
              ((PY, "gate.py", "--step", "lean"),), "LEAN_BUILD_FAILED"),
    Injection("I18", "lift: certified survivor", "the declared dual witness names two positions with different keys",
              PROPOSALS, _step(0, "dual_witness", [0, 1]), (LIFT,), "NO_CERTIFIED_SURVIVOR"),
    Injection("I19", "lift: claims fixed", "the proposal rewrites the demand's last entry",
              PROPOSALS, _step(1, "demand", [0, 1, 2, 0, 1, 2]), (LIFT,), "CLAIM_FROZEN"),
    Injection("I20", "lift: exhaustion", "the enumeration never tries the halting choice",
              "engine/ladder.py",
              _replace("    choices: tuple[int | None, ...] = (None, *range(len(s.ops)))",
                       "    choices: tuple[int | None, ...] = (*range(len(s.ops)),)"),
              (LIFT,), "EXHAUSTION_NOT_CLOSED"),
    Injection("I21", "lift: context witness", "the declared context pair is not collapsed at the source",
              PROPOSALS, _json(_context_positions), (LIFT,), "NO_CONTEXT_WITNESS"),
    Injection("I22", "lift: class frozen", "the extension class is edited after its pre-registration",
              "lifts/record_reading/CLASS.json", _replace("strictly shorter", "shorter"),
              (LIFT,), "CLASS_NOT_PREREGISTERED"),
    Injection("I23", "lift: minimal, ties retained", "the proposal drops one of the two tied minima",
              PROPOSALS, _step(0, "tied_minima", 1), (LIFT,), "NOT_MINIMAL_OVER_A_CLASS"),
    Injection("I24", "lift: traceable", "the new capability is declared at the active entry",
              PROPOSALS, _step(0, "new_entry_offset", 0), (LIFT,), "UNTRACEABLE"),
    Injection("I25", "lift: resolved", "one answer entry fires the climb instead of the constant map",
              PROPOSALS, _step(0, "answer", [[[0, 0], 0], [[0, 1], 2], [[1, 0], 1]]), (LIFT,), "NOT_RESOLVED"),
    Injection("I26", "lift: preservation", "the embedding reads the oldest entries instead of ignoring them",
              "engine/ladder.py",
              _replace("        suffix = k[target_width - source_width:]", "        suffix = k[:source_width]"),
              (LIFT,), "NOT_PRESERVED"),
    Injection("I27", "lift: rollback", "the carrier's down map reads the wrong record entry",
              "engine/ladder.py",
              _replace("    return {(x,): table.get((x, x)) for x in range(s.n)}",
                       "    return {(x,): table.get((x, (x + 1) % s.n)) for x in range(s.n)}"),
              (LIFT,), "RR-ROLLBACK"),
    Injection("I28", "lift: descent", "the partial restriction gives a new term an old meaning",
              "engine/ladder.py",
              _replace('            raise NonDescent("NON_DESCENT", f"the table reads the older entry at {suffix}")',
                       "            continue"),
              (LIFT,), "RR-NON-DESCENT"),
    Injection("I29", "lift: non-trivial, priced", "the step is declared free",
              PROPOSALS, _step(1, "price", {"enablements": 0, "key_width_added": 1}), (LIFT,), "RR-TRIVIAL-LIFT"),
    Injection("I30", "lift: survival accounting", "the old ceiling is declared preserved, not refined",
              PROPOSALS, _step(0, "old_certificates", [{"class": "preserved", "id": "ceiling_rung0"},
                                                       {"class": "preserved", "id": "tapes_rung0"}]),
              (LIFT,), "SILENT_DRIFT"),
    Injection("I31", "lift: evidence only", "a step carries an activation field",
              PROPOSALS, _step(1, "activation", "granted"), (LIFT,), "AUTHORITY_FIELD"),
    Injection("I32", "lift: budget", "the last step spends no budget",
              PROPOSALS, _step(1, "budget_after", 1), (LIFT,), "BUDGET_NOT_DECREASING"),
    Injection("I33", "lift: replay", "the exhibit pointer names another program's enablements",
              PROPOSALS, _step(0, "exhibit_pointer", ["record_runs", 4, "enablements"]), (LIFT,), "REPLAY_MISMATCH"),
    Injection("I34", "lift: chain", "the second step starts from a budget the first did not leave",
              PROPOSALS, _step(1, "budget_before", 2), (LIFT,), "CHAIN_BROKEN"),
    Injection("I35", "reach records", "the carrier half stops booking name-blindness in the loss ledger",
              "outward/reach.py", _replace('    rows.setdefault("source.name_blindness", {',
                                           '    (lambda *a: None)("source.name_blindness", {'),
              ((PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_reach_records.py", "-k",
                "up_to_the_cap"),), "TC-UNBOOKED-STANDING-ENTRY"),
    Injection("I36", "harness host", "the carrier registry stops declaring 19L57G1's harness host",
              "../mssn_sn_tower/reach/registry/carriers.json",
              _replace('      "harness_host": "the_symbol_game",\n', ""),
              ((PY, "tools/reach_ledger_check.py"),), "does not verify: RR-PRODUCER-VERDICT"),
    Injection("I37", "Lean certificates (a level's own module)", "a generated certificate states the opposite verdict",
              "payload/scope_fence/lean/ScopeFence.lean",
              _replace("theorem pos_vanishes : vanishes value_pos table_pos = true := by decide",
                       "theorem pos_vanishes : vanishes value_pos table_pos = false := by decide"),
              ((PY, "gate.py", "--step", "lean"),), "LEAN_BUILD_FAILED"),
    Injection("I38", "Lean citations in a record", "every certificate is looked up in one level's module",
              "outward/reach.py",
              _replace('found = sorted((ROOT / "payload").glob(f"*/lean/{module}.lean"))',
                       'found = sorted((ROOT / "payload").glob("*/lean/DistanceForm.lean"))'),
              (WORKING_TREE_RECORD + ("working_tree and 10",),), "RR-STATEMENT"),
    Injection("I39", "compatibility square", "the unit square reads the counit on its left side",
              "bindings/adapters/L008.py",
              _replace('carried = sorted([name[a[0]], name[a[1]]] for n, a in source["relations"] if n == "unit")',
                       'carried = sorted([name[a[0]], name[a[1]]] for n, a in source["relations"] if n == "counit")'),
              (WORKING_TREE_RECORD + ("working_tree and 8",),), "TC-CRITERION-MISSING"),
    Injection("I40", "ordered closure", "a loop's closure is decided by its signed count of each turn",
              "payload/loop_products/spec.py",
              _replace("    return all(product(fs, word) == IDENTITY for _, word, shut in loops(fs) if shut)",
                       "    return all(all(sum(-1 if b else 1 for tt, b in word if tt == t) == 0 for t, _ in word)\n"
                       "               for _, word, shut in loops(fs) if shut)"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I41", "scope fence", "the fence stops refusing a scope past the table",
              "payload/scope_fence/spec.py",
              _replace('            Forbid("scope_derived", ((in_scope, ("c", far_reach)),)),\n', ""),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:mut"),
    Injection("I42", "exact roots", "a claimed root is accepted within a tolerance of 1/1000",
              "payload/table_polynomial/spec.py",
              _replace("all(r is not None and value_at(c, r).is_zero() for r in roots(fs))",
                       "all(r is not None and Q(-1, 1000) < value_at(c, r) < Q(1, 1000) for r in roots(fs))"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I43", "recomputed split", "the split reads the load back instead of recomputing its parts",
              "payload/three_way_split/spec.py",
              _replace("    return rebuilt(s) == s.load", "    return s.load == s.load"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_mark"),
    Injection("I44", "feasible flow", "a zero gap certifies without the flow balancing",
              "payload/flow_certificate/spec.py",
              _replace("    return n is not None and all(divergence(n, x).is_zero() for x in range(n.nodes))",
                       "    return n is not None"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I45", "least span", "any span dividing the length is accepted, not only the least",
              "payload/cycle_words/spec.py",
              _replace("g.span == Q(least_span(g.lead))", "g.span in (Q(1), Q(2))"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I46", "freeze (imported round)", "an expectation frozen in E0 is edited",
              "payload/edge_endpoints/expect.json", _replace('"code": "ACCEPT"', '"code": "ACCEPTED"'),
              ((PY, "gate.py", "--step", "freeze"),), "FROZEN FILE DIFFERS FROM THE SOURCE"),
    Injection("I47", "embargo list", "rung seven's question is dropped from the embargo list",
              "engine/guards.py",
              _replace('    ("duration_under_changing",', '    ("duration_under_changing_dropped",'),
              ((PY, "gate.py", "--step", "embargo"),), "EMBARGO LIST DRIFT"),
    Injection("I48", "Q-level registrations", "a registered sealed theorem's name is misspelled",
              "bindings/qlevels.json", _replace('"PrimitivePassage.two_rule"', '"PrimitivePassage.two_rules"'),
              (tuple(BUILD),), "RR-STATEMENT"),
    Injection("I49", "replayed steps", "a stated step is taken without checking it is a sealed one-step reduct",
              "payload/positioned_join/spec.py",
              _replace("    return out if events(out) in rw_reducts(events(term)) else None", "    return out"),
              (tuple(EXPECT_TEST),), "EXPECTATION_MISMATCH:near_absorb_one"),
    Injection("I50", "stages kept apart", "a map is judged by injectivity alone, not by the target's classes",
              "payload/stage_chain/spec.py",
              _replace("classes[j][table[x]] == classes[j][table[y]]", "table[x] == table[y]"),
              (tuple(EXPECT_TEST),), "EXPECTATION_MISMATCH:own_neg"),
    Injection("I51", "sealed validity", "the new stage is judged without the sealed validity check",
              "payload/conservative_embedding/spec.py",
              _replace("    elif not match[0]:\n        failed.append(\"sealed_valid\")\n", ""),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_invalid"),
    Injection("I52", "carried reversal", "a dagger is accepted when it names any arrow, not the transposed one",
              "payload/carried_reversal/spec.py",
              _replace("any(by_pair.get((ends[f][1], ends[f][0])) != g for f, g in dag.items())",
                       "any(g not in ends for f, g in dag.items())"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_not_involution"),
    Injection("I53", "balanced witness", "the closed route's witness is accepted without being a sealed boundary",
              "payload/route_replay/spec.py",
              _replace("            if y not in rims or pairing.is_zero():", "            if y is None:"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_dual"),
    Injection("I54", "whole menu", "the formula's domain is read from the claim, not from the sealed menu",
              "payload/bounded_mask/spec.py",
              _replace("    if tree != formula(len(response_menu(TRUNC_WORLD))):",
                       "    if tree != formula(tree[2] if isinstance(tree, list) else 0):"),
              (tuple(EXPECT_TEST),), "EXPECTATION_MISMATCH:near_truncated"),
    Injection("I55", "host verifier", "a terminal is accepted from any verifier",
              "payload/host_bound_verdict/spec.py",
              _replace('    if pk["verifier"] != "host":', '    if pk["verifier"] not in ("host", "candidate"):'),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I56", "digest binding", "container digests are not recomputed",
              "payload/tagged_digest/spec.py",
              _replace('    if any(c["digest"] != digest(str(c["tag"]), c["body"]) for c in containers):',
                       "    if False:"),
              (tuple(EXPECT_TEST),), "EXPECTATION_MISMATCH:near_digest"),
    Injection("I57", "source equations", "the chain's maps are not checked on source equations",
              "payload/stage_chain/spec.py",
              _replace("             for (i, j), table in tables.items() for a, b in stages[i][\"relations\"]):",
                       "             for (i, j), table in tables.items() for a, b in []):"),
              (tuple(EXPECT_TEST),), "EXPECTATION_MISMATCH:near_equation"),
    Injection("I58", "axiom-free restatement", "an axiom-free theorem is restated with a placeholder axiom",
              "outward/reach.py",
              _replace(' and a.strip() != "(none)"]', "]"),
              (WORKING_TREE_RECORD + ("restated_axiom_report",),),
              "FAILED tests/test_reach_records.py::test_the_restated_axiom_report_keeps_every_line"),
    Injection("I59", "sealed boundary", "the boundary maps are accepted when their composites vanish, whatever they are",
              "payload/boundary_chain/spec.py",
              _replace("    if ds != maps(bd_n):\n        failed.append(\"boundary_replayed\")\n", ""),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_tail"),
    Injection("I60", "observed ledger", "merges are counted only among protected pairs",
              "payload/observed_blocks/spec.py",
              _replace("    if not merged <= ledger:", "    if not (merged & protected) <= ledger:"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_unrecorded"),
    Injection("I61", "computed effect rows", "declared effect rows are trusted",
              "payload/granted_steps/spec.py",
              _replace('    if pk["operations"] != pos["operations"]:', "    if False:"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_understated"),
    Injection("I62", "named blockers", "a Q-level is blocked by a reason that is neither an embargo item nor named",
              "bindings/qlevels.json", _replace('"blocked_by": [\n        "tree_witness_off_class"\n      ],\n      "level": 41',
                                                '"blocked_by": [\n        "hard"\n      ],\n      "level": 41'),
              (tuple(BUILD),), "UNKNOWN_BLOCKER"),
    Injection("I63", "row sums", "a row is accepted when it sums to at most one",
              "payload/step_weights/spec.py",
              _replace("all(sum(r, ZERO) == ONE for r in k)", "all(sum(r, ZERO) <= ONE for r in k)"),
              (tuple(EXPECT_TEST),), "EXPECTATION_MISMATCH:near_negative"),
    Injection("I64", "positive evidence", "an observation is accepted whatever its evidence",
              "payload/weighted_update/spec.py",
              _replace("    return u is not None and all(not ev.is_zero() for ev, _ in steps(u))",
                       "    return u is not None"),
              (tuple(EXPECT_TEST),), "EXPECTATION_MISMATCH:near_zero_later"),
    Injection("I65", "exact pair product", "the product is taken slot by slot",
              "payload/mirror_pairs/spec.py",
              _replace("    return p is not None and p[3] == p[0] * p[1]\n",
                       "    return p is not None and p[3] == QI(p[0].re * p[1].re, p[0].im * p[1].im)\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I66", "unit size", "any nonzero size is accepted as a unit row",
              "payload/unit_rows/spec.py",
              _replace("sum((z.norm2() for z in r), ZERO) == ONE\n", "sum((z.norm2() for z in r), ZERO).sign() > 0\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I67", "computed rank", "any positive claimed rank is accepted",
              "payload/joint_rank/spec.py",
              _replace("r.den == 1 and r.num == rank_of(t)", "r.den == 1 and r.num >= 1"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I68", "whole-table size keeping", "size keeping is judged by sampling the probe rows",
              "payload/size_keeping/spec.py",
              _replace("    return _mul(mirrored(u), u) == unit and _mul(u, mirrored(u)) == unit\n",
                       "    return all(sum((z.norm2() for z in apply(u, v)), ZERO) == sum((z.norm2() for z in v), ZERO)\n"
                       "               for v, _ in (probes(fs) or []))\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I69", "one-signed rest", "a rest of both signs is accepted",
              "payload/signed_totals/spec.py",
              _replace("    return len(signs) <= 1\n", "    return len(signs) <= 2\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I70", "table given", "roots are accepted with no table",
              "payload/table_roots/spec.py",
              _replace('            Total("table_given", (), ((slot, ("s",)),)),\n', ""),
              (tuple(EXPECT_TEST),), "EXPECTATION_MISMATCH:near_no_table"),
    Injection("I71", "owned joint moves", "a claim's joint move is not required to be made of the players' moves",
              "payload/joint_payoffs/spec.py",
              _replace('            Closure("claims_owned", ((claims, ("a", "b", "u", "v")),),\n'
                       '                    ((owns, (first, "a")), (owns, (second, "b")))),\n', ""),
              (tuple(EXPECT_TEST),), "EXPECTATION_MISMATCH:own_neg"),
    Injection("I72", "unilateral changes", "the first player's changes of move are not tried",
              "payload/stable_profiles/spec.py",
              _replace("        if any((there := paid.get((k, j))) is None or there[0] > here[0] for k in firsts):\n"
                       "            return False\n", ""),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_gain"),
    Injection("I73", "witnessed proofs", "a proved triple is not required to carry a witness",
              "payload/witnessed_triples/spec.py",
              _replace('            Closure("witnessed", ((proved, ("c",)),), ((certified, ("c",)),)),\n', ""),
              (tuple(EXPECT_TEST),), "EXPECTATION_MISMATCH:own_neg"),
    Injection("I74", "every overlap", "overlaps are checked only between neighbouring choices",
              "payload/overlap_choices/spec.py",
              _replace("    return all(a[2] == b[2] for a in ch for b in ch if a[1] == b[1])\n",
                       "    return all(a[2] == b[2] for a, b in zip(ch, ch[1:]) if a[1] == b[1])\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I75", "commuting checks", "the exchange count is not reduced modulo two",
              "payload/commuting_checks/spec.py",
              _replace("    return all(exchange(u, v) % 2 == 0 for i, u in enumerate(cs) for v in cs[i + 1:])\n",
                       "    return all(exchange(u, v) % 1 == 0 for i, u in enumerate(cs) for v in cs[i + 1:])\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_anti"),
    Injection("I76", "map given", "a match is claimed with no map required",
              "payload/step_squares/spec.py",
              _replace('            Total("map_given", ((here, ("s",)),), ((sends, ("s", "t")),)),\n', ""),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_no_map"),
    Injection("I77", "no surrogate evidence", "offered counts are not refused",
              "payload/answer_keeping/spec.py",
              _replace('            Forbid("no_surrogate", ((offered, ("v",)),)),\n', ""),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_offered"),
    Injection("I78", "ordered face product", "the product is compared as an unordered summary",
              "payload/face_products/spec.py",
              _replace("    return claimed(fs) == ordered(fs)\n", "    return sorted(claimed(fs)) == sorted(ordered(fs))\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_order"),
    Injection("I79", "named frame", "coordinates with no frame named are read in a default frame",
              "payload/named_frames/spec.py",
              _both(_replace('            Total("named_given", (), ((named_f, ("f",)),)),\n', ""),
                    _replace('got[0][0]) if len(got) == 1 else None\n', 'got[0][0]) if len(got) == 1 else 1\n')),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I80", "recomputed total", "the claimed total is read, not recomputed",
              "payload/two_party_bound/spec.py",
              _replace("    return e is not None and t == total_of(e)\n", "    return e is not None and t is not None\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:mut"),
    Injection("I81", "both ends", "a change of labels is applied at a link's first end only",
              "payload/walk_transport/spec.py",
              _replace('        want = then(then(inverse(_change(fs, _end(fs, "from", e))), _map(fs, "moves", e)), _change(fs, _end(fs, "to", e)))\n',
                       '        want = then(inverse(_change(fs, _end(fs, "from", e))), _map(fs, "moves", e))\n'),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I82", "trace one", "a reduction's trace is not checked",
              "payload/side_reduction/spec.py",
              _replace("    return r is not None and sum((r[i][i].re for i in range(len(r))), ZERO) == ONE\n", "    return r is not None\n"),
              (tuple(EXPECT_TEST),), "EXPECTATION_MISMATCH:own_neg"),
    Injection("I83", "recomputed weights", "reported weights are trusted",
              "payload/split_weights/spec.py",
              _replace("    return w is not None and w == weights(fs)\n", "    return w is not None\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I84", "real eigenvalues", "the discriminant is not checked",
              "payload/square_one/spec.py",
              _replace("    return tr.im.is_zero() and det.im.is_zero() and disc.re.sign() >= 0\n", "    return True\n"),
              (tuple(EXPECT_TEST),), "EXPECTATION_MISMATCH:own_neg"),
    Injection("I85", "far-choice blindness", "near weights may move with the far choice",
              "payload/far_blind/spec.py",
              _replace("    return all(m == marg[0] for m in marg)\n", "    return len(marg) > 0\n"),
              (tuple(EXPECT_TEST),), "EXPECTATION_MISMATCH:own_neg"),
    Injection("I86", "sequential weights", "the joint weights are taken as products of the separate weights",
              "payload/ordered_splits/spec.py",
              _replace("    return [[size_of(tapply(e, tapply(p, v))) for e in es] for p in ps]\n",
                       "    return [[size_of(tapply(p, v)) * size_of(tapply(e, v)) for e in es] for p in ps]\n"),
              (tuple(EXPECT_TEST),), "EXPECTATION_MISMATCH:own_neg"),
    Injection("I87", "outward enclosure", "only the upper end of a claimed bound is checked",
              "payload/outward_bounds/spec.py",
              _replace("        if not (bq[0] <= lo and hi <= bq[1]):\n", "        if not (hi <= bq[1]):\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:mut"),
    Injection("I88", "checked rim", "the declared rim edges are not checked",
              "payload/rim_cochains/spec.py",
              _replace('    return _marked(fs, "rim_edge", "edge") == re and _marked(fs, "rim_vertex", "vertex") == rv\n',
                       '    return _marked(fs, "rim_vertex", "vertex") == rv\n'),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I89", "mutual wait", "two endpoints both waiting to receive are not refused",
              "payload/dual_endpoints/spec.py",
              _replace('            out["no_mutual_wait"] = False\n', "            pass\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I90", "bounded jumps", "a jump is not required to carry a loss bound",
              "payload/scale_steps/spec.py",
              _replace('             Total("jumps_bounded", (), ((e.form("near_jump_bound"), ("a",)), (e.form("far_jump_bound"), ("b",))))]\n',
                       "             ]\n"),
              (tuple(EXPECT_TEST),), "EXPECTATION_MISMATCH:own_neg"),
    Injection("I91", "same background", "a counterfactual may draw its background again",
              "payload/same_background/spec.py",
              _replace("    return all(f == c for f, c in twins(fs))\n", "    return all(f in (0, 1) and c in (0, 1) for f, c in twins(fs))\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I92", "named sources", "a payload module a spec imports is left out of the record's sources",
              "outward/bundles.py",
              _replace("        | payload_imports(challenge_id)\n", ""),
              (NAMED_SOURCE_TEST,), "UNNAMED_SOURCE"),
    Injection("I93", "carrier part of a registration", "a harness record is read as a replay of sealed evidence",
              "outward/qlevels.py",
              _replace('        bound = (adapted and levels[level].get("kernel") == "replay" and custody == "sealed") or tree_bound',
                       "        bound = adapted or tree_bound"),
              (tuple(BUILD),), "STALE_REGISTRATION"),
    Injection("I94", "ruling D4 framing", "a record at an apparatus level is framed as a supplied challenge",
              "outward/reach.py",
              _replace('    return "AP" if B.computed_answer_type(result) == "A" or apparatus_level(level, checkers) else "SC"\n',
                       '    return "AP" if B.computed_answer_type(result) == "A" else "SC"\n'),
              (WORKING_TREE_RECORD + ("d4",),), "D4_FRAMING"),
    Injection("I95", "carrier cap", "the carrier cap reverts to 12", "engine/structure.py",
              _replace("MAX_CARRIER = 18\n", "MAX_CARRIER = 12\n"), (tuple(BUILD),), "SIZE_CAP"),
    Injection("I96", "declared class count", "a class beyond the budget is enumerated instead of declared",
              "engine/search.py", _replace("    if declared > EVAL_BUDGET:\n", "    if False:\n"),
              ((PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_kinds_search.py", "-k",
                "over_the_budget"),), "class_over_budget"),
    Injection("I97", "digests as values", "descent drops the hosted digests", "engine/encoding.py",
              _replace("tuple(sorted(tuples)), fs.values, fs.digests, fs.texts)",
                       "tuple(sorted(tuples)), fs.values, (), fs.texts)"),
              (tuple(BUILD),), "RR-NON-DESCENT"),
    Injection("I98", "induction certificate", "the certificate no longer checks the value at the start",
              "engine/lean/ExactRat/Poly.lean",
              _replace("  | d + 1, p => decide (0 \u2264 eval p (natQ n0)) && startsNonneg n0 d (diff p)",
                       "  | d + 1, p => startsNonneg n0 d (diff p)"),
              ((PY, "gate.py", "--step", "lean"),), "LEAN_BUILD_FAILED"),
    Injection("I99", "no return", "a listed cell is checked only for existing, not against earlier removals",
              "payload/filtered_pages/spec.py",
              _replace("    return all(set(ls) <= set(page_of(fs, r)) for r, ls in zip(numbers(fs), listed(fs)))\n",
                       "    return all(set(ls) <= set(range(len(fs.elements(\"cell\")))) for ls in listed(fs))\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:mut"),
    Injection("I100", "every representative", "only the zero corner cochain is tried",
              "payload/class_operations/spec.py",
              _replace("for f in range(1 << f2.n)):", "for f in range(1)):"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I101", "ordered closure", "closure is judged by the parity of the face values",
              "payload/closed_faces/spec.py",
              _replace("    return closure(fs) == list(range(len(fs.elements(\"label\"))))\n",
                       "    return sum(1 for v in values(fs) for i in range(len(v)) for j in range(i + 1, len(v))\n"
                       "               if v[i] > v[j]) % 2 == 0\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I102", "digest recomputed", "the seal's digest is read, not recomputed from the axiom list",
              "payload/bound_axioms/spec.py",
              _replace("fs.digest(seals[0]) == digest_of(axioms(fs))", "fs.digest(seals[0]) is not None"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_digest"),
    Injection("I103", "external by digest", "a confirmation counts as external when its evaluator is another element",
              "payload/confirmed_runs/spec.py",
              _replace("    return any(fs.digest(e) != mine for e, _ in rows(fs, \"confirms\"))\n",
                       "    return any(e != it[0] for e, _ in rows(fs, \"confirms\"))\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_self"),
    Injection("I104", "hinge incidence", "a term is checked only for its number of patches",
              "payload/hinge_deficits/spec.py",
              _replace("    return all(u == [k for k, t in enumerate(ps) if v in t] for v, u in enumerate(uses(fs)))\n",
                       "    return all(len(u) == len([k for k, t in enumerate(ps) if v in t]) for v, u in enumerate(uses(fs)))\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I105", "one root", "any positive drop in sign changes is accepted",
              "payload/isolated_roots/spec.py",
              _replace("changes(ch, e[0]) - changes(ch, e[1]) == 1", "changes(ch, e[0]) - changes(ch, e[1]) >= 1"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I106", "every n", "the bound is checked at the sample indices only",
              "payload/rated_limits/spec.py",
              _replace("    return s is not None and start(fs) >= 1 and all(holds(r, start(fs), False)[0] for r in s)\n",
                       "    return s is not None and all(value_at(r, Q(n)).sign() >= 0 for r in s for n, _ in samples(fs))\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_far"),
    Injection("I107", "every depth", "the estimate is checked at the listed depths only",
              "payload/refined_sums/spec.py",
              _replace("    return c is not None and k0 >= 0 and holds_everywhere(error_poly(integrand(fs)), c, k0)\n",
                       "    return c is not None and all(_abs(value_at(error_poly(integrand(fs)), Q(1, 2 ** k))) <= c\n"
                       "                                 for k, _ in listed(fs))\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_far"),
    Injection("I108", "right fibre", "a reindexed term is required over the arrow's target, not its source",
              "payload/reindexed_fibres/spec.py",
              _replace('(runs, ("a", "s", "t"))), ((over, ("y", "s")),)),', '(runs, ("a", "s", "t"))), ((over, ("x", "t")),)),'),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I109", "glue restricts", "a glued value is compared with itself, not with the patches",
              "payload/glued_patches/spec.py",
              _replace('Closure("glue_restricts", ((assigns, ("p", "x", "v")),), ((glue, ("x", "v")),)),',
                       'Closure("glue_restricts", ((glue, ("x", "v")),), ((glue, ("x", "v")),)),'),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I110", "coherence", "the pentagon sum is reduced modulo one",
              "payload/associator_tables/spec.py",
              _replace("(v[0] + v[1] - v[2] - v[3] - v[4]) % m:", "(v[0] + v[1] - v[2] - v[3] - v[4]) % 1:"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I111", "forced value", "a forced claim is checked for presence only",
              "payload/forced_differences/spec.py",
              _replace('    return _claims(fs, "forced")[0] == m.forced()\n', '    return len(_claims(fs, "forced")) == 1\n'),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_forced"),
    Injection("I112", "used at least once", "an unused name is accepted",
              "payload/use_once_terms/spec.py",
              _replace("all(k >= 1 for k in w.uses.values())", "all(k >= 0 for k in w.uses.values())"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_unused"),
    Injection("I113", "answers recomputed", "claimed answers are counted, not compared with the evaluated ones",
              "payload/typed_queries/spec.py",
              _replace(" and claimed(fs) == found(fs)\n", "\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:mut"),
    Injection("I114", "patched within", "a patched view row need not be in the new table",
              "payload/patched_views/spec.py",
              _replace('Closure("patched_within", ((patched, ("r",)),), ((new, ("r",)),)),',
                       'Closure("patched_within", ((patched, ("r",)),), ((patched, ("r",)),)),'),
              (tuple(EXPECT_TEST),), "EXPECTATION_MISMATCH:own_neg"),
    Injection("I115", "declared ends", "an edge's ends need not be declared vertices",
              "payload/signed_cells/spec.py",
              _replace('((edge, ("e", "t", "h")),), ((vertex, ("t",)), (vertex, ("h",)))),',
                       '((edge, ("e", "t", "h")),), ((edge, ("e", "t", "h")),)),'),
              (tuple(EXPECT_TEST),), "EXPECTATION_MISMATCH:own_neg"),
    Injection("I116", "strict writes", "a write over another transaction's unfinished write is allowed",
              "payload/serial_receipts/spec.py",
              _replace("        if w is not None and w != t and w not in finished:\n            return False\n", ""),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I117", "rising clocks", "a parent's clock is not compared with its child's",
              "payload/ordered_log/spec.py",
              _replace("return all(ev[p][1] < c for", "return all(ev[p][1] >= 0 for"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_clock"),
    Injection("I118", "idempotent merge", "merging a state with itself is not required to give it back",
              "payload/merge_tables/spec.py",
              _replace('Closure("idempotent", ((state, ("a",)),), ((merge, ("a", "a", "a")),)),',
                       'Closure("idempotent", ((state, ("a",)),), ((state, ("a",)),)),'),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I119", "issued by authority", "a grant's issuer need not be the authority",
              "payload/exact_grants/spec.py",
              _replace('Closure("issued_by_authority", ((grants, ("i", "p", "r", "a")),), ((auth, ("i",)),)),',
                       'Closure("issued_by_authority", ((grants, ("i", "p", "r", "a")),), ((grants, ("i", "p", "r", "a")),)),'),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I120", "within budget", "a release that exceeds the remaining budget is allowed",
              "payload/budgeted_releases/spec.py",
              _replace("        if c > left:\n            return False\n", ""),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I121", "pins hold", "a pin is checked for presence, not against its input's seal",
              "payload/lineage_pins/spec.py",
              _replace("fs.digest(p) == fs.digest(seal[i])", "fs.digest(p) is not None"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_pin"),
    Injection("I122", "no expansion", "a rooted handoff may widen the permissions it passes on",
              "payload/narrowing_handoffs/spec.py",
              _replace("    return all(subset or not rooted for rooted, subset in replay(fs)[1])\n",
                       "    return len(replay(fs)[1]) >= 0\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I123", "mutants refused", "a mutant the subject accepts is not refused",
              "payload/mutant_challenges/spec.py",
              _replace("    return s is not None and all(not s(xs) for _, xs in lists(fs)[1])\n", "    return s is not None\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I124", "exit recomputed", "the captured exit kind is not compared with the replayed one",
              "payload/limited_runs/spec.py",
              _replace("    return got is not None and got[0] == captured(fs)[0]\n", "    return got is not None\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_exit"),
    Injection("I125", "independence decided", "sources assumed independent are never tested",
              "payload/composed_errors/spec.py",
              _replace('    if rule(fs) != "independent":\n        return True\n', "    return True\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I126", "empty clause", "a refutation need not end in the empty clause",
              "payload/resolution_claims/spec.py",
              _replace("        if not ok or not rs or rs[-1]:\n", "        if not ok or not rs:\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_short"),
    Injection("I127", "both directions", "a one-way flow is accepted",
              "payload/wired_handshakes/spec.py",
              _replace("    return all((b, a) in f for a, b in f)\n", "    return len(f) >= 0\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:mut"),
    Injection("I128", "outputs recomputed", "the recorded outputs are not compared with the two implementations",
              "payload/differential_pairs/spec.py",
              _replace(" and all((a, b) == (ca, cb) for _, a, b, ca, cb in got)\n", "\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_output"),
    Injection("I129", "seed replayed", "the recorded first list is not regenerated from the seed",
              "payload/seeded_shrinks/spec.py",
              _replace("b[0], b[1]) == ls[0]\n", "b[0], b[1]) is not None\n"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_replay"),
    Injection("I130", "not self-certified", "a self-certified release is refused only when it is also a frontier claim",
              "payload/scoped_release/spec.py",
              _replace('Forbid("not_self_certified", ((selfc, ("r",)),)),',
                       'Forbid("not_self_certified", ((selfc, ("r",)), (frontier, ("r",)))),'),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    # Round P7A: research-tree witnesses (the author's ruling of 2026-09-25).
    Injection("I131", "custody booked", "a research-tree record stops booking its custody in the loss ledger",
              "outward/bundles.py",
              _replace('        rows.append(("source.witness_custody",', '        (lambda *a: None)(("source.witness_custody",'),
              (tuple(BUILD),), "UNBOOKED_CUSTODY"),
    Injection("I132", "retired blocker", "a registration lists witness_not_sealed again after the ruling",
              "bindings/qlevels.json", _json(_reblock_023), (tuple(BUILD),), "RULED_ADMISSIBLE"),
    Injection("I133", "tree custody", "a research-tree replay also reads a sealed source",
              "payload/observer_glue/spec.py",
              _replace('SOURCES = (f"research/{TREE}/observer_descent.py",)',
                       'SOURCES = (f"research/{TREE}/observer_descent.py", "code/derivation/model.py")'),
              (tuple(BUILD),), "RR-TREE"),
    Injection("I134", "embargo list", "rung eight's leftover candidate is dropped from the embargo list",
              "engine/guards.py",
              _replace('    ("shortest_class_matched_witnesses",', '    ("shortest_class_matched_witnesses_dropped",'),
              ((PY, "gate.py", "--step", "embargo"),), "EMBARGO LIST DRIFT"),
    Injection("I135", "observer glue", "a conflict on a shared locus is never looked at, and a failed glue is no "
              "objection",
              "payload/observer_glue/spec.py",
              _both(_replace("    if cov.check_compatibility(records).is_err():", "    if False:"),
                    _replace('    if glue.is_err() or _rows(glue.unwrap()) != pk["glued"]:',
                             '    if glue.is_ok() and _rows(glue.unwrap()) != pk["glued"]:')),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I136", "shared labels", "two contexts may give a shared item two labels",
              "payload/shared_labels/spec.py",
              _replace("    if any(len(v) > 1 for v in seen.values()):", "    if any(len(v) > 2 for v in seen.values()):"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_turned"),
    Injection("I137", "row margin", "the total is read from its label, not recomputed from the rows",
              "payload/row_margin/spec.py",
              _replace("    total, bound = _total(entries), _bound()",
                       '    total, bound = Fraction(str(pk["total"])), _bound()'),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I138", "site checks", "each check is compared with itself, not with the others",
              "payload/site_checks/spec.py",
              _replace("    if not all(u.commutes_with(v) for i, u", "    if not all(u.commutes_with(u) for i, u"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_odd"),
    Injection("I139", "walk relabels", "a transport changed at one end only is also accepted",
              "payload/walk_relabels/spec.py",
              _replace("changed.get(name) != list(conjugated(t, g_s, g_d)):",
                       "changed.get(name) not in (list(conjugated(t, g_s, g_d)), list(t)):"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I140", "face walk products", "a face need not end where it starts",
              "payload/face_walk_products/spec.py",
              _replace("    return all(x[1] == y[0] for x, y in zip(ends, ends[1:])) and ends[-1][1] == ends[0][0]",
                       "    return all(x[1] == y[0] for x, y in zip(ends, ends[1:]))"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I141", "register squares", "a claim with no map is not refused for it",
              "payload/register_squares/spec.py",
              _replace('    if pk["map"] is None:\n        failed.append("mapped")',
                       '    if pk["map"] is None:\n        pass'),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:near_no_map"),
    Injection("I142", "pairing certificates", "a rest holding both signs is accepted",
              "payload/pairing_certificates/spec.py",
              _replace("terms[i] != 0}) > 1:", "terms[i] != 0}) > 2:"),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I143", "chord square rim", "a declared rim need only contain the recomputed rim",
              "payload/chord_square_rim/spec.py",
              _replace('pk["rim_edges"] != list(rim)', 'not set(pk["rim_edges"]) >= set(rim)'),
              (tuple(EXPECT_TEST),), "RR-FIXTURE-PASSED:own_neg"),
    Injection("I144", "embargo list", "rung nine's census rows are dropped from the embargo list",
              "engine/guards.py",
              _replace('    ("census_undecided_rows_x6",', '    ("census_undecided_rows_x6_dropped",'),
              ((PY, "gate.py", "--step", "embargo"),), "EMBARGO LIST DRIFT"),
    # Round P7B: hosted texts, the signature check, and the fifteen new levels.
    Injection('I145', 'texts as values', 'descent drops the hosted texts',
              'engine/encoding.py',
              _replace('tuple(sorted(tuples)), fs.values, fs.digests, fs.texts)',
                       'tuple(sorted(tuples)), fs.values, fs.digests)'),
              (tuple(BUILD),), 'RR-NON-DESCENT'),
    Injection('I146', 'signature check', 'any signature in range verifies',
              'engine/exact/digest.py',
              _replace('    return pow(s, e, n) == as_number(sha256(message)) % n',
                       '    return True'),
              (tuple(EXPECT_TEST),), 'RR-FIXTURE-PASSED:mut'),
    Injection('I147', 'pullback on labels', 'the pullback reads membership in the family, not the subfamily',
              'payload/recomputed_labels/spec.py',
              _replace('Closure("pullback", ((label, ("x", "p")), (at, ("x", "p"))), ((sub, ("x",)),)),',
                       'Closure("pullback", ((label, ("x", "p")), (at, ("x", "p"))), ((element, ("x",)),)),'),
              (tuple(EXPECT_TEST),), 'RR-FIXTURE-PASSED:near_pullback'),
    Injection('I148', 'typed inverse', 'a roof may invert any arrow',
              'payload/formal_inverses/spec.py',
              _replace('Closure("inverts_weak", ((roof, ("w", "f", "b", "c")),), ((weak, ("w",)),)),',
                       'Closure("inverts_weak", ((roof, ("w", "f", "b", "c")),), ((arrow, ("w",)),)),'),
              (tuple(EXPECT_TEST),), 'RR-FIXTURE-PASSED:own_neg'),
    Injection('I149', 'matching colours', "a slot's colour need only be some colour",
              'payload/coloured_slots/spec.py',
              _replace('(inp, ("o", "i", "c"))), ((out, ("p", "c")),)),',
                       '(inp, ("o", "i", "c"))), ((colour, ("c",)),)),'),
              (tuple(EXPECT_TEST),), 'RR-FIXTURE-PASSED:near_colour'),
    Injection('I150', 'both round trips', 'the target round trip is checked on the source side',
              'payload/both_round_trips/spec.py',
              _replace('    return r is not None and _returns(r, "target")',
                       '    return r is not None and _returns(r, "source")'),
              (tuple(EXPECT_TEST),), 'RR-FIXTURE-PASSED:own_neg'),
    Injection('I151', 'no negative direction', 'only the diagonal minors are read',
              'payload/weight_slopes/spec.py',
              _replace('    return all(x.sign() >= 0 for x in minors(m))',
                       '    return all(x.sign() >= 0 for x in minors(m)[:k])'),
              (tuple(EXPECT_TEST),), 'EXPECTATION_MISMATCH:own_neg'),
    Injection('I152', 'slot order transported', 'a second-factor reading needs no exchange table',
              'payload/paired_frames/spec.py',
              _replace('    return second is not None and (not second or bool(rows(fs, "exchange")))',
                       '    return second is not None'),
              (tuple(EXPECT_TEST),), 'RR-FIXTURE-PASSED:near_untransported'),
    Injection('I153', 'signed digest', 'a digest counts as marked when it is merely covered',
              'payload/signed_chains/spec.py',
              _replace('Total("digest_marked", ((sm, ("d",)),), ((marked, ("d", "m")),)),',
                       'Total("digest_marked", ((sm, ("d",)),), ((covers, ("d", "m")),)),'),
              (tuple(EXPECT_TEST),), 'RR-FIXTURE-PASSED:own_neg'),
    Injection('I154', 'results rerun', 'a claimed result digest is compared only when the tool cannot run',
              'payload/rerun_calls/spec.py',
              _replace('        if got is not None and fs.digest(c) != digest_of(got):',
                       '        if got is None and fs.digest(c) != digest_of(got):'),
              (tuple(EXPECT_TEST),), 'RR-FIXTURE-PASSED:own_neg'),
    Injection('I155', 'acyclic parents', 'a self-descent is refused only on a self-parent',
              'payload/grounded_traces/spec.py',
              _replace('Forbid("acyclic", ((descends, ("e", "e")),)),',
                       'Forbid("acyclic", ((descends, ("e", "e")), (parent, ("e", "e")))),'),
              (tuple(EXPECT_TEST),), 'RR-FIXTURE-PASSED:own_neg'),
    Injection('I156', 'quantified clauses kept', 'only the unquantified clauses must be recorded',
              'payload/covered_clauses/spec.py',
              _replace('if quantified(text[c[0]:c[1]]))',
                       'if not quantified(text[c[0]:c[1]]))'),
              (tuple(EXPECT_TEST),), 'RR-FIXTURE-PASSED:own_neg'),
    Injection('I157', 'no unproved swap', 'a reordered prefix is accepted without the fragment',
              'payload/renamed_formulas/spec.py',
              _replace('    return got is not None and (not got[0] or got[2] == 0)',
                       '    return got is not None'),
              (tuple(EXPECT_TEST),), 'RR-FIXTURE-PASSED:own_neg'),
    Injection('I158', 'branch outcome kept', "the compiled program's results are not compared with the source's",
              'payload/compiled_branches/spec.py',
              _replace('    return got is not None and all(v == got[1][n] for n, (kind, v) in got[3].items() if kind == "HALT")',
                       '    return got is not None'),
              (tuple(EXPECT_TEST),), 'RR-FIXTURE-PASSED:own_neg'),
    Injection('I159', 'measured speedup', 'a ratio need not be on the measured basis',
              'payload/counted_runs/spec.py',
              _replace('Closure("basis_measured", ((ratio, ("q",)),), ((measured, ("q",)),)),',
                       'Closure("basis_measured", ((ratio, ("q",)),), ((ratio, ("q",)),)),'),
              (tuple(EXPECT_TEST),), 'RR-FIXTURE-PASSED:mut'),
    Injection('I160', 'counted estimate', 'a point estimate is taken as its own count',
              'payload/counted_trials/spec.py',
              _replace('Total("count_given", ((point, ("p",)),), ((count, ("n",)),)),',
                       'Total("count_given", ((point, ("p",)),), ((point, ("n",)),)),'),
              (tuple(EXPECT_TEST),), 'RR-WRONG-REASON:near_uncounted'),
    Injection('I161', 'no surviving mutant', 'a mutant counts as killed when its kill set is merely computed',
              'payload/killed_mutants/spec.py',
              _replace('all(bool(killed_by(fs, m))',
                       'all(killed_by(fs, m) is not None'),
              (tuple(EXPECT_TEST),), 'RR-FIXTURE-PASSED:own_neg'),
)


def _dirty() -> str:
    return subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout.strip()


def _clear_bytecode() -> None:
    """A restored file can match the injected one in size and mtime second,
    so stale bytecode would outlive the reversal.  Clear it, and write none."""
    for layer in ("engine", "outward", "payload", "tools", "tests"):
        for d in (ROOT / layer).rglob("__pycache__"):
            for f in d.iterdir():
                f.unlink()
            d.rmdir()


def _run(cmds: tuple[tuple[str, ...], ...]) -> tuple[int, str]:
    out, rc = "", 0
    _clear_bytecode()
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    for c in cmds:
        proc = subprocess.run(list(c), cwd=ROOT, capture_output=True, text=True, check=False, env=env)
        out += proc.stdout + proc.stderr
        rc = proc.returncode
        if rc != 0:
            break
    return rc, out


def run_one(inj: Injection) -> dict[str, object]:
    path = ROOT / inj.path
    original = path.read_bytes()
    try:
        path.write_bytes(inj.edit(original.decode("utf-8")).encode("utf-8"))
        rc, out = _run(inj.commands)
        fired = rc != 0 and inj.code in out
    finally:
        path.write_bytes(original)
    rc2, out2 = _run(inj.commands)
    recovered = rc2 == 0 and inj.code not in out2
    return {"id": inj.ident, "fired": fired, "exit_injected": rc, "exit_recovered": rc2, "recovered": recovered}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", action="append")
    args = ap.parse_args(argv)
    if _dirty():
        print("REFUSED: the tree has tracked modifications; injections need a clean tree")
        return 2
    chosen = [i for i in INJECTIONS if not args.only or i.ident in args.only]
    # Every anchor is checked before anything runs: a stale anchor is named in
    # seconds, not after the injections before it (round P7A found one, I62,
    # an hour into the panel).
    stale = []
    for inj in chosen:
        try:
            inj.edit((ROOT / inj.path).read_bytes().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001 - any failure to build the edit is a stale injection, named
            stale.append(f"{inj.ident}: {exc}")
    for line in stale:
        print(f"STALE ANCHOR: {line}")
    if stale:
        return 4
    rows = []
    for inj in chosen:
        r = run_one(inj)
        rows.append((inj, r))
        print(f"{inj.ident}: fired={r['fired']} recovered={r['recovered']} "
              f"(exit {r['exit_injected']} then {r['exit_recovered']}) code {inj.code}")
    if _dirty():
        print("TREE NOT CLEAN AFTER INJECTIONS")
        return 3
    if not args.only:
        write_record(rows)
    return 0 if all(r["fired"] and r["recovered"] for _, r in rows) else 1


def write_record(rows: list[tuple[Injection, dict[str, object]]]) -> None:
    lines = [
        "# Injection record",
        "",
        "AuthorityEffect: None.",
        "",
        "Written by `python tools/inject.py`. Each injection is a minimal edit on disk,",
        "never committed. It must make the named command exit nonzero and print the",
        "exact code; the edit is then reversed and the same command must pass. The",
        "tree is checked clean before and after. Nothing is regenerated or repinned",
        "while an injection is live.",
        "",
        "| id | guard | injected defect | file | command | code | fired | recovered |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for inj, r in rows:
        cmd = " && ".join(" ".join(c[1:] if c[0] == PY else c) for c in inj.commands)
        lines.append(
            f"| {inj.ident} | {inj.guard} | {inj.what} | `{inj.path}` | `{cmd}` | `{inj.code}` | "
            f"{'yes' if r['fired'] else 'NO'} (exit {r['exit_injected']}) | "
            f"{'yes' if r['recovered'] else 'NO'} (exit {r['exit_recovered']}) |"
        )
    lines += [
        "",
        "I10 appends a word from 19L57G1's prose watchlist; the word is assembled at run",
        "time and is not written in this record or in the injector's source.",
        "",
        "## Findings while proving the panel",
        "",
        "- I1, first run: the claim-overwrite injection was caught, but by the count",
        "  guard (`RR-EXHAUSTION`), because only validated deltas passed through the",
        "  claims check. The engine now checks every enumerated delta, and I1 fires",
        "  `CLAIM_FROZEN` by name.",
        "- First run of the whole panel: most recoveries failed because the injector",
        "  reused stale bytecode (a restored file can match the injected one in size",
        "  and mtime second). The injector now clears bytecode and writes none. The",
        "  gates themselves were not at fault.",
        "- I4, first run: the code fired but pytest truncated it out of the message;",
        "  the test now prints mismatches in full.",
        "",
        "I15 to I17 run `lake build` and the axiom audit; nothing is repinned while they are live.",
        "",
        "I18 to I34 each mutate one of record_reading's two proposed lifts (a proposal",
        "field, the pre-registered extension class, or one line of the ladder mirror)",
        "and run `tools/lift_check.py`. It recomputes every condition from the pinned",
        "evidence and prints a refusal code only on a drift from the frozen",
        "expectations, so each injection is seen by its own code. I35 runs the",
        "test-only draft pipeline through the receiving side's `check_record`.",
        "",
        "- I27 and I28, first run: both fired, but recovery was scored false, because",
        "  the check's summary printed the failing codes the expectations already hold",
        "  (R2.8 fails on both steps). The summary now names failing conditions, and",
        "  only a drift row prints a code.",
        "- I35, first run: it did not fire. The edit renamed the ledger row's key and",
        "  left the row in place. It now drops the row.",
        "",
        "I36 edits the receiving side's carrier registry, outside this directory. It",
        "then runs that side's `ledger --check` in its default context: without the",
        "declared harness host, the stored Mode E receipts no longer resolve.",
        "- I36, first run: it was expected to fire `RR-PIN` and did not. The ledger",
        "  verifies a stored receipt by recomputing it and comparing. When the sources",
        "  do not resolve, the recomputed block differs, and the ledger names that",
        "  difference, `RR-PRODUCER-VERDICT`, not the `RR-PIN` beneath it. The",
        "  injection now expects the code the ledger actually prints.",
        "",
        "I37 to I47 are round P3's. I37 runs the Lean step on a level's own",
        "certificate module (the generator now renders one per level). I38 and I39 run",
        "a level's record, completed on the working tree, through the receiving side's",
        "`check_record`: a certificate cited from the wrong module (`RR-STATEMENT`),",
        "and a compatibility square whose two sides differ (`TC-CRITERION-MISSING`).",
        "I40 to I45 each weaken one band level's decisive clause to the defect the",
        "level exists to refuse (a scalar summary for an ordered product, a fence that",
        "reads the declared scope, a rounded root, a split read back instead of",
        "recomputed, a zero gap without feasibility, a span that is not the least); the",
        "level's own refused fixture is then accepted. I46 proves the E0 freeze check",
        "after its repair, and I47 the embargo pin's new item. I48 proves that every",
        "Q-level registration's sealed citation is checked against the pinned axiom",
        "report, and I49 and I50 weaken the two replays of sealed evidence (a step",
        "that is not a sealed reduct; a map judged by injectivity alone).",
        "",
        "I51 to I58 prove the second P3 pull request's guards: each of the six new",
        "replays of sealed evidence (006, 009, 013, 014, 015, 017) and the chain's",
        "equation clause (016) is weakened to the defect it exists to refuse, and",
        "I58 reintroduces a defect found while building 007's kernel module: the",
        "restated axiom report wrote an axiom-free theorem with a placeholder",
        "axiom, which the receiving side refused (`RR-AXIOM`). Its first run did not",
        "fire: the record test reads the committed restatement, not a fresh one. It",
        "now runs the test that restates the report afresh.",
        "",
        "I59 to I64 are round P4's: the three new replays of sealed evidence (029, 032,",
        "043) and the two harness levels (035, 036) are each weakened to the defect",
        "they exist to refuse, and I62 names a Q-level blocker that is neither an",
        "embargo item nor one of the two named non-embargo blockers.",
        "- I64, first run: it did not fire. It divided zero evidence through as if it",
        "  were one, but the evidence clause reads the evidence itself, so no verdict",
        "  moved. It now drops the evidence clause.",
        "",
        "I65 to I91 are round P5's: each of the twenty-seven new harness levels (047,",
        "048, 054, 057, 066, 070, 039, 040, 044, 058, 060, 065, 067, 062, 049, 059,",
        "061, 056, 051, 050, 055, 052, 068, 072, 042, 033 and 038, in the order they",
        "were built) has its decisive clause weakened to the defect the level exists",
        "to refuse, and the level's own refused fixture, or a near-miss, is then",
        "accepted or refused for another reason. I92 leaves a payload module a spec",
        "imports out of the record's sources (UNNAMED_SOURCE). I93 reads a harness",
        "record at a blocked Q-level as a replay of sealed evidence",
        "(STALE_REGISTRATION: the refusal round P5 predicted, G1, before the registry",
        "read the carrier part). I94 frames the record at a ruling-D4 apparatus level",
        "as a supplied challenge (D4_FRAMING).",
        "- I72, first run: it did not fire. With the first player's changes untried,",
        "  the own negative (a, x) is still refused, by the second player's change to",
        "  y. The injection now expects near_gain, whose only profitable change is the",
        "  first player's, to be accepted.",
        "",
        "I95 to I130 are round P6's. I95 reverts the carrier cap to 12, and 031's",
        "18-element structure is refused (SIZE_CAP). I96 enumerates a class beyond",
        "the evaluation budget instead of declaring its count. I97 drops the hosted",
        "digests in descent (RR-NON-DESCENT). I98 removes the start check from the",
        "Lean induction certificate, and the level modules that cite it no longer",
        "build. I99 to I130 weaken the decisive clause of each new harness level",
        "(030, 031, 064, 045, 046, 063, 069, 071, 073, 022, 023, 027, 037, 041,",
        "074 to 081, 083, 085, 087, 088, 089, 092, 094, 098, 099 and 100) to the",
        "defect it exists to refuse; the level's refused fixture, or a near-miss, is",
        "then accepted or refused for another reason.",
        "- I114 and I115, first run: both exited nonzero, but not with the code",
        "  expected. With the relational clause weakened, the own negative reached",
        "  the decoded clauses and was refused there, for another reason. They now",
        "  expect the expectation mismatch they print.",
        "- I1, first run of this round: it did not fire. The declared-count guard",
        "  (I96's capability) ran before the claims check, so the claim-overwrite",
        "  repair was refused as `RR-EXHAUSTION`. The claims check now runs first on",
        "  every enumerated delta, and I1 fires `CLAIM_FROZEN` by name again.",
        "",
        "- The freeze step, first gate run of the round: it failed on every new",
        "  payload, because it compared each payload's expectations with the E0 source",
        "  repository, which holds only E0's. It now compares the files the source",
        "  holds at its head; I46 shows it still bites on an E0 file.",
        "",
        "I131 to I143 are round P7A's (research-tree witnesses, the author's ruling of",
        "2026-09-25). I131 stops booking a tree record's custody in its loss ledger",
        "(UNBOOKED_CUSTODY); I132 re-lists the retired blocker witness_not_sealed",
        "(RULED_ADMISSIBLE); I133 makes a tree replay read a sealed source as well",
        "(RR-TREE); I134 drops rung eight's leftover candidate from the embargo list,",
        "and I144 rung nine's undecided census rows.",
        "I135 to I143 weaken the decisive clause of each research-tree replay (023,",
        "058, 059, 060, 061, 062, 065, 066, 072) to the defect its level refuses; the",
        "level's refused fixture, or a near-miss, is then accepted.",
        "- The first full panel of the round stopped at I62: its anchor named 023's",
        "  retired blocker, and the injector raised on the missing anchor after an",
        "  hour of injections. I62 now re-blocks 041, I93 targets the registry's new",
        "  binding rule, and the injector checks every anchor before it runs any",
        "  injection (STALE ANCHOR).",
        "",
        "I145 to I161 are round P7B's. I145 drops the hosted texts in descent",
        "(RR-NON-DESCENT); I146 lets any signature in range verify, and a bad",
        "signature is accepted at 082. I147 to I161 weaken the decisive clause of each",
        "new level (024, 025, 026, 028, 034, 053, 082, 084, 086, 090, 091, 093, 095,",
        "096, 097) to the defect it exists to refuse; the level's refused fixture, or a",
        "near-miss, is then accepted or refused for another reason. I151 and I160 move",
        "the refusal off the decisive clause rather than accepting a fixture: at 034 a",
        "declared matrix with a negative direction is never the recomputed one, and at",
        "096 the decoded clauses also need a count.",
        "",
        "Covered by unit tests rather than on-disk injection: a trivial capability",
        "failing condition 10 (`RR-TRIVIAL-LIFT`), a checker below the bar",
        "(`CHECKER_BELOW_BAR`), a checker file off its pin (`RR-PIN`), growth, removal",
        "and declared-responder capabilities (`GUARD_EMBARGO`), loading",
        "second-derivation state (`GUARD_EMBARGO`), a request about symmetry along a",
        "history or about the element count and succession (`GUARD_EMBARGO`), a",
        "second mutation for most lift conditions",
        "(`tests/test_ladder.py`), a skipped rung (`NOT_MINIMAL_OVER_A_CLASS` with",
        "`UNTRACEABLE`), a reused residual and a misplaced stop (`CHAIN_BROKEN`), a",
        "positive that is not the committed witness (`RR-PIN`) and a producer verdict",
        "(`RR-PRODUCER-VERDICT`) in a completed level record.",
        "",
    ]
    (ROOT / "INJECTIONS.md").write_bytes("\n".join(lines).encode("ascii"))


if __name__ == "__main__":
    sys.exit(main())

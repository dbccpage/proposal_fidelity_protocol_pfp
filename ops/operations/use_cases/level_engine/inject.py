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
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from operations.domain.level_engine_context import (
    current_context,
)

from .dispatch import command, environment

ROOT = current_context().runtime_root
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


LF, CRLF = chr(10), chr(13) + chr(10)


def _replace(old: str, new: str) -> Callable[[str], str]:
    def go(text: str) -> str:
        # The relocated sources are committed with CRLF line ends; an anchor
        # written with LF is matched on either, and the edit keeps the file's.
        if old not in text and CRLF in text and old.replace(LF, CRLF) in text:
            return text.replace(old.replace(LF, CRLF), new.replace(LF, CRLF), 1)
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
    Injection("I16", "Lean axioms", "a reported law depends on sorryAx",
              "engine/lean/ExactRat/Laws.lean",
              _replace("theorem inv_zero : (0 : QN)\u207b\u00b9 = 0 := by\n  apply sound\n  exact Frac.eqv_refl _",
                       "theorem inv_zero : (0 : QN)\u207b\u00b9 = 0 :=\n"
                       "  sorryAx _ true"),
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
              ((PY, "tools/reach_ledger_check.py"),), '"codes": ["RR-PRODUCER-VERDICT"]'),
    Injection("I37", "Lean certificates (a level's own module)", "a generated certificate states the opposite verdict",
              "payload/scope_fence/lean/ScopeFence.lean",
              _replace("theorem pos_vanishes : vanishes value_pos table_pos = true := by decide",
                       "theorem pos_vanishes : vanishes value_pos table_pos = false := by decide"),
              ((PY, "gate.py", "--step", "lean"),), "LEAN_BUILD_FAILED"),
    Injection("I38", "Lean citations in a record", "every certificate is looked up in one level's module",
              "outward/reach.py",
              _replace('    source = current_context().lean_path(f"{module}.lean")',
                       '    source = current_context().lean_path("DistanceForm.lean")'),
              (WORKING_TREE_RECORD + ("no_single_certificate",),), "DID NOT RAISE"),
    Injection("I39", "compatibility square", "the unit square reads the counit on its left side",
              "bindings/adapters/L008.py",
              _replace('carried = sorted([name[a[0]], name[a[1]]] for n, a in source["relations"] if n == "unit")',
                       'carried = sorted([name[a[0]], name[a[1]]] for n, a in source["relations"] if n == "counit")'),
              (WORKING_TREE_RECORD + ("structure_map",),), "carries_its_square"),
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
              "historical/payload/edge_endpoints/expect.json", _replace('"code": "ACCEPT"', '"code": "ACCEPTED"'),
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
              "test_reach_records.py::test_the_restated_axiom_report_keeps_every_line"),
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
    Injection("I162", "embargo list", "the second derivation's engine class is dropped from the embargo list",
              "engine/guards.py",
              _replace('    ("second_derivation_engine_class",', '    ("second_derivation_engine_class_dropped",'),
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


def _map_path(relative: str, sandbox: Path) -> Path:
    runtime = sandbox / "pfp/infrastructure/tower_research/level_engine"
    engine = sandbox / "operations/use_cases/level_engine/research_engine"
    evidence = sandbox / "pfp/infrastructure/tower_evidence/level_engine"
    if relative == "PINS.json":
        return sandbox / "governance/contracts/level_engine/v2/PINS.json"
    if relative.startswith("../mssn_sn_tower/"):
        return sandbox / "pfp/infrastructure/tower_research/reach/data/v1/registry/carriers.json"
    if relative.startswith("lean/") or "/lean/" in relative:
        return sandbox / "lean" / Path(relative).name
    if relative.startswith("engine/"):
        # Since ff295c01 the engine's implementation lives in operations; the
        # research package keeps only aliases of it.
        return engine / relative.removeprefix("engine/")
    if relative.startswith("historical/"):
        # The freeze step reads a round's frozen files from the v1 archive.
        return evidence / "v1" / relative.removeprefix("historical/")
    if relative.startswith("bindings/adapters/"):
        return runtime / "adapters" / Path(relative).name
    if relative.startswith("bindings/generated/") or (relative.startswith("bindings/") and Path(relative).stem[:1] in {"L", "T"}):
        return evidence / "v2" / relative
    if relative.startswith("bindings/") or relative.startswith("predictions/"):
        return evidence / "v1" / relative
    return runtime / relative


def _translated(arguments: tuple[str, ...], sandbox: Path) -> list[str]:
    ctx = current_context()
    names = {"run_bootstrap.py":"bootstrap", "gate.py":"gate", "tools/vendor.py":"vendor",
             "tools/bind.py":"bind", "tools/lift_check.py":"lift_check",
             "tools/reach_ledger_check.py":"reach_ledger_check", "tools/preflight_draft.py":"preflight_draft"}
    values = list(arguments)
    if len(values)>1 and values[1] in names:
        values = command(names[values[1]], values[2:])
        # The command imports the sandbox's canonical installed package copy.
        if "--output-dir" in values:
            offset=values.index("--output-dir"); del values[offset:offset+2]
        if "--lean-root" in values:
            values[values.index("--lean-root")+1]=str(sandbox/"lean")
        else:
            values[4:4]=["--lean-root",str(sandbox/"lean")]
    values = [str(sandbox/"pfp/tests/level_engine"/value.removeprefix("tests/"))
              if value.startswith("tests/") else value for value in values]
    return values


def _run(commands: tuple[tuple[str, ...], ...], sandbox: Path) -> tuple[int, str]:
    import shutil
    out, code = "", 0
    env = environment()
    env.pop("LEVEL_ENGINE_OUTPUT", None)
    env["LEVEL_ENGINE_LEAN_ROOT"] = str(sandbox / "lean")
    # The copied packages come first (the working directory); every other
    # package they import (``engine``, since ff295c01) resolves from the
    # workspace, after them.
    import os
    workspace = str(current_context().require_repository())
    env["PYTHONPATH"] = os.pathsep.join(x for x in (env.get("PYTHONPATH", ""), workspace) if x)
    # The bootstrap intentionally refuses an occupied output; each probe gets
    # its own fresh directory under this disposable sandbox.
    for arguments in commands:
        values = _translated(arguments, sandbox)
        values = [str(sandbox / "generated") if value == "_scratch/inj" else value for value in values]
        if "bootstrap" in values and (sandbox / "generated").exists():
            shutil.rmtree(sandbox / "generated")
        proc = subprocess.run(values, cwd=sandbox, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", check=False, env=env)
        out += proc.stdout + proc.stderr
        code = proc.returncode
        if code:
            break
    return code, out


def run_one(injection: Injection, sandbox: Path) -> dict[str, Any]:
    path = _map_path(injection.path, sandbox)
    original = path.read_bytes()
    try:
        path.write_bytes(injection.edit(original.decode("utf-8")).encode("utf-8"))
        code, output = _run(injection.commands, sandbox)
    finally:
        path.write_bytes(original)
    restored_code, restored_output = _run(injection.commands, sandbox)
    return {"id": injection.ident, "fired": code != 0 and injection.code in output,
            "exit_injected": code, "exit_recovered": restored_code,
            "recovered": restored_code == 0 and injection.code not in restored_output,
            "expected_code": injection.code,
            "injected_output": output, "recovered_output": restored_output}


def main(argv: list[str] | None = None) -> int:
    import shutil
    import tempfile
    from importlib.resources import files
    parser = argparse.ArgumentParser(description="Run preserved mutation controls in a disposable package copy")
    parser.add_argument("--test-only", action="store_true", required=True)
    parser.add_argument("--only", action="append")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    known = {entry.ident for entry in INJECTIONS}
    if args.only and not set(args.only) <= known:
        parser.error("unknown injection identifier")
    chosen = [entry for entry in INJECTIONS if not args.only or entry.ident in args.only]
    if args.list:
        print("\n".join(entry.ident + ": " + entry.guard for entry in chosen))
        return 0
    ctx = current_context()
    ctx.require_repository()
    if args.report and args.report.exists():
        raise ValueError("OUTPUT_FILE_OCCUPIED")
    results = []
    with tempfile.TemporaryDirectory(prefix="level-engine-injections-") as temporary:
        sandbox = Path(temporary)
        for package in ("pfp", "operations"):
            shutil.copytree(Path(str(files(package))), sandbox/package,
                            ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".mypy_cache"))
        # The symbol game's domain imports the governance contracts (since
        # ff295c01), so the copy carries the whole governance package, and the
        # context's level-engine contract over it.
        shutil.copytree(Path(str(files("governance"))), sandbox/"governance",
                        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".mypy_cache"))
        governance = sandbox/"governance/contracts/level_engine/v2"
        shutil.rmtree(governance)
        shutil.copytree(ctx.governance_root, governance)
        if ctx.lean_root is not None:
            shutil.copytree(ctx.lean_root,sandbox/"lean",ignore=shutil.ignore_patterns("*.olean", "*.ilean", "__pycache__"))
        for entry in chosen:
            try:
                result = run_one(entry, sandbox)
            except Exception as error:
                result = {"id":entry.ident,"fired":False,"recovered":False,"error":str(error)}
            results.append(result)
            print(f"{entry.ident}: fired={result['fired']} recovered={result['recovered']}",flush=True)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps({"AuthorityEffect":"None", "injections":results},sort_keys=True,indent=2)+"\n",encoding="utf-8")
    return 0 if all(row["fired"] and row["recovered"] for row in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())

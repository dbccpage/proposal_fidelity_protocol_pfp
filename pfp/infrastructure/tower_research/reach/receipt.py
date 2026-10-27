"""The ``reach-receipt/1`` checker: sixteen checks, computed grades.

AuthorityEffect: None. A receipt records checks and grants nothing.

A producer submits a **level record**: the carrier's pinned sources, the
target checker's pin, the claimed clauses, and the four fixtures (positive,
the level's own negative, a near-miss, and a decisive mutation per clause).
The record carries **no verdict**: a grade, terminal, outcome or any other
verdict field in it is refused (``RR-PRODUCER-VERDICT``; the Deletion Test).

The checker replays every fixture through the pinned target checker, runs its
own empty and flag-only probes, validates the unified transport certificate,
and emits the **receipt**: the record plus a ``computed`` block holding every
observation, refusal, cap, grade and terminal. ``verify_receipt`` deletes that
block, recomputes it, and refuses any difference, so a hand-edited grade in a
stored receipt is refused too.

Checks (W1-S07 section 7.5):

- K1 bytes; K2 pins; K3 producer verdict deleted; K4 weak replay;
- K5 row accounting; K6 fixtures (the 4-fixture rule, bite, probes);
- K7 fiber; K8 residual class; K9 lift licence; K10 down rule;
- K11 Lean; K12 transport; K13 blindness and chains; K14 gate status;
- K15 determinism; K16 vocabulary (only for a receipt placed inside 19L57G1).

Grades (document 07 section 3): R (reach strength), E (carrier evidence),
P (provenance) and B (blindness), never merged. Terminals: REFUSED,
UNRESOLVED, SELF_CONSISTENT_ONLY, EVIDENCE_ONLY. None is named REACHED.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Mapping

from pfp.domain.lean_bridge.models import STANDARD_LEAN_AXIOMS

from . import targets, transport
from .canonical import (
    CanonicalError,
    canonical_bytes,
    digest,
    digest_obj,
    format_rational,
    parse_canonical,
    parse_rational,
    sha256_hex,
    strict_loads,
)
from .codes import RECEIPT_CODES, TARGET_GENERIC_CODES
from .pins import Resolver
from .schema import Enum, ListOf, Nullable, Obj, SchemaError, validate

SCHEMA_ID = "reach-receipt/1"
TARGET_REPO = "the_symbol_game"
FRAMINGS = frozenset({"SC", "BR", "CC", "AG", "AP", "TO", "TFC"})
REFUSED_KINDS = ("own_negative", "near_miss", "decisive_mutation")
CHECK_IDS = tuple(f"K{n}" for n in range(1, 17))
FORBIDDEN_VERDICT_KEYS = frozenset(
    {
        "accepted",
        "caps",
        "computed",
        "grade",
        "grades",
        "licensed",
        "observed",
        "outcome",
        "passed",
        "passes",
        "reach_grade",
        "refusals",
        "result",
        "status_ceiling",
        "terminal",
        "verdict",
        "verified",
    }
)
ALLOWED_AXIOMS_DEFAULT = STANDARD_LEAN_AXIOMS

SOURCE = Obj({"path": "str", "sha256": "digest"})
FIXTURE = Obj(
    {
        "clause": "str",
        "expected_code": "str",
        "id": "str",
        "kind": Enum(frozenset({"positive", "own_negative", "near_miss", "decisive_mutation"})),
        "payload": "any",
        "repair": "str",
        "row_sha256": "digest",
        "source_path": "str",
    },
    frozenset({"clause", "expected_code", "repair", "row_sha256", "source_path"}),
)
RATIONALS = ListOf("rational")
STAGE_CHANGE = Obj(
    {
        "down_rule": Obj({"down": ListOf(ListOf("str")), "new_terms": ListOf("str"), "up": ListOf(ListOf("str"))}),
        "lift": Obj(
            {
                "budget_after": "rational",
                "budget_before": "rational",
                "claims_licence": "bool",
                "context_witness": Nullable(Obj({"context": "digest", "x": "digest", "y": "digest"})),
                "extension_class": Nullable(Obj({"candidates": "int", "sha256": "digest", "tied_minima": ListOf("digest")})),
                "from_level": "int",
                "growth_sha256": Nullable("digest"),
                "to_level": "int",
            }
        ),
        "residual": Obj(
            {
                "alpha": Nullable(RATIONALS),
                "claimed_class": Enum(frozenset({"exact", "residual_closed", "open"})),
                "d0": ListOf(RATIONALS),
                "d1": ListOf(RATIONALS),
                "omega": RATIONALS,
                "phi": Nullable(RATIONALS),
            }
        ),
        "same_level_search": Obj(
            {
                "closed": "bool",
                "states": "int",
                "stop": Enum(frozenset({"saturated", "blocked", "self_reference_stop", "budget_exhausted"})),
            }
        ),
    },
    frozenset({"down_rule", "lift", "residual", "same_level_search"}),
)
RECORD = Obj(
    {
        "authority_effect": Enum(frozenset({"None"})),
        "carrier": Obj(
            {
                "commit": "commit",
                "part": Enum(frozenset({"repo_content", "harness_computation"})),
                "repo": "str",
                "sources": ListOf(SOURCE, min_len=1),
            }
        ),
        "checker": Obj({"commit": "commit", "id": "str", "path": "str", "sha256": "digest"}),
        "clauses": ListOf(Obj({"code": "str", "id": "str"})),
        "declared_fixture_count": "int",
        "fiber": Nullable(Obj({"candidates": ListOf("any", min_len=1), "uniqueness_required": "bool"})),
        "fixtures": ListOf(FIXTURE),
        "framing": Enum(FRAMINGS),
        "gates": Nullable(Obj({"steps": ListOf("str", min_len=1), "workflow_path": "str"})),
        "inputs": Obj({"receipts_consumed": ListOf("digest")}),
        "ladder": Obj({"level": "int", "registry_version": "int", "row_sha256": "digest", "table_sha256": "digest"}),
        "lean": Nullable(
            Obj(
                {
                    "report": SOURCE,
                    "sources": ListOf(SOURCE, min_len=1),
                    "theorems": ListOf(
                        Obj({"name": "str", "source_path": "str", "statement_sha256": "digest"}), min_len=1
                    ),
                }
            )
        ),
        "non_claims": ListOf("str"),
        "placement": Enum(frozenset({"the_symbol_game", "19L57G1"})),
        "provenance": Obj(
            {
                "isolation": Enum(frozenset({"ENFORCED", "INSTRUCTION_ONLY", "NOT_APPLICABLE"})),
                "purity": Enum(frozenset({"CLEAN_BY_RULE", "PARTIAL", "SEED_STEERED", "STEERED", "NOT_APPLICABLE"})),
                "source_blindness": Enum(frozenset({"BLIND", "NOT_BLIND"})),
            }
        ),
        "receipt_schema": Enum(frozenset({SCHEMA_ID})),
        "stage_change": Nullable(STAGE_CHANGE),
        "transport": Nullable("any"),
    }
)
# Paths the verdict scan does not enter: payloads are probed by K6 instead,
# and the transport certificate's status fields are pinned by K12.
UNSCANNED = re.compile(r"^\$\.(fixtures\[\d+\]\.payload|fiber\.candidates|transport)$")


@dataclass(frozen=True)
class Context:
    """Everything the checker knows independently of the record."""

    resolver: Resolver
    stage_registry: Mapping[str, Any]
    checkers: Mapping[str, Any]
    carriers: Mapping[str, Any]
    gated_steps: frozenset[str]
    level_texts: Mapping[int, tuple[str, ...]] = field(default_factory=dict)
    watchlist_sha256: frozenset[str] = frozenset()


@dataclass
class Result:
    receipt: dict[str, Any]
    codes: tuple[str, ...]
    terminal: str
    grades: dict[str, str]
    caps: tuple[str, ...]


class _Run:
    def __init__(self) -> None:
        self.refusals: list[tuple[str, str, str]] = []
        self.caps: set[str] = set()
        self.status: dict[str, str] = {check: "N/A" for check in CHECK_IDS}

    def refuse(self, code: str, detail: str) -> None:
        check = RECEIPT_CODES[code][0]
        self.refusals.append((check, code, detail))
        self.status[check] = "FAIL"

    def ran(self, check: str) -> None:
        if self.status[check] == "N/A":
            self.status[check] = "PASS"

    def codes(self) -> tuple[str, ...]:
        return tuple(sorted({code for _, code, _ in self.refusals}))


def _verdict_keys(value: Any, path: str = "$") -> list[str]:
    if UNSCANNED.match(path):
        return []
    found: list[str] = []
    if isinstance(value, dict):
        for key in sorted(value):
            if key in FORBIDDEN_VERDICT_KEYS:
                found.append(f"{path}.{key}")
            found.extend(_verdict_keys(value[key], f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_verdict_keys(item, f"{path}[{index}]"))
    return found


def _mat_vec(matrix: list[list[Fraction]], vector: list[Fraction]) -> list[Fraction]:
    return [sum((a * b for a, b in zip(row, vector)), Fraction(0)) for row in matrix]


def _transpose(matrix: list[list[Fraction]], columns: int) -> list[list[Fraction]]:
    return [[row[j] for row in matrix] for j in range(columns)]


def residual_class(residual: Mapping[str, Any]) -> tuple[str, Fraction | None]:
    """Recompute the residual class from the pinned matrices (K8).

    ``omega`` is a 1-cochain of length m; ``d0`` is m x n; ``d1`` is k x m.
    ``exact`` needs alpha with omega = d0 alpha. ``residual_closed`` needs phi
    with sup-norm <= 1, d0^T phi = 0, <phi, omega> = Phi1 > 0 and d1 omega = 0.
    ``open`` is d1 omega != 0. Anything else is ``uncertified``.
    """
    omega = [parse_rational(x) for x in residual["omega"]]
    d0 = [[parse_rational(x) for x in row] for row in residual["d0"]]
    d1 = [[parse_rational(x) for x in row] for row in residual["d1"]]
    m = len(omega)
    n = len(d0[0]) if d0 else 0
    if len(d0) != m or any(len(row) != n for row in d0) or any(len(row) != m for row in d1):
        raise ValueError("matrix shapes do not match the cochain")
    if any(value != 0 for value in _mat_vec(d1, omega)):
        return ("open", None)
    if residual["alpha"] is not None:
        alpha = [parse_rational(x) for x in residual["alpha"]]
        if len(alpha) != n:
            raise ValueError("alpha has the wrong length")
        if _mat_vec(d0, alpha) == omega:
            return ("exact", None)
    if residual["phi"] is not None:
        phi = [parse_rational(x) for x in residual["phi"]]
        if len(phi) != m:
            raise ValueError("phi has the wrong length")
        phi1 = sum((a * b for a, b in zip(phi, omega)), Fraction(0))
        closed = all(abs(value) <= 1 for value in phi) and all(
            value == 0 for value in _mat_vec(_transpose(d0, n), phi)
        )
        if closed and phi1 > 0:
            return ("residual_closed", phi1)
    return ("uncertified", None)


def _parse_axiom_report(text: str) -> dict[str, tuple[str, ...]]:
    report: dict[str, tuple[str, ...]] = {}
    for line in text.splitlines():
        match = re.match(r"^'([^']+)' depends on axioms: \[(.*)\]\s*$", line)
        if match:
            report[match.group(1)] = tuple(a.strip() for a in match.group(2).split(",") if a.strip())
            continue
        match = re.match(r"^'([^']+)' does not depend on any axioms\s*$", line)
        if match:
            report[match.group(1)] = ()
    return report


def statement_text(source: str, name: str) -> str | None:
    """The declaration of ``name`` from its keyword up to ``:=`` (K11)."""
    short = re.escape(name.split(".")[-1])
    match = re.search(rf"(?m)^[ \t]*(?:theorem|lemma)[ \t]+{short}\b(.*?):=", source, re.DOTALL)
    return match.group(0) if match else None


LEAN_FORBIDDEN = (
    re.compile(r"\bsorry\b"),
    re.compile(r"\badmit\b"),
    re.compile(r"(?m)^\s*axiom\s"),
    re.compile(r"\bunsafe\b"),
)


def check_record(data: bytes, ctx: Context) -> Result:
    run = _Run()
    record_sha = digest(data)

    # ---- K1 bytes, and K3's first half: no verdict in the submission ------
    try:
        record = parse_canonical(data)
    except CanonicalError as exc:
        run.refuse(exc.code, exc.detail)
        return _finish(run, None, record_sha, {})
    verdicts = _verdict_keys(record)
    if verdicts:
        run.refuse("RR-PRODUCER-VERDICT", f"the producer declared {', '.join(verdicts)}")
        return _finish(run, record, record_sha, {})
    run.ran("K3")
    try:
        validate(record, RECORD)
    except SchemaError as exc:
        run.refuse(exc.code, exc.detail)
        return _finish(run, record, record_sha, {})
    run.ran("K1")
    obs: dict[str, Any] = {}
    fixtures: list[dict[str, Any]] = record["fixtures"]
    by_id: dict[str, dict[str, Any]] = {}
    for fixture in fixtures:
        if fixture["id"] in by_id:
            run.refuse("RR-SCHEMA", f"fixture id {fixture['id']!r} repeated")
        by_id[fixture["id"]] = fixture
    required = {
        "positive": ("source_path",),
        "own_negative": ("expected_code", "row_sha256"),
        "near_miss": ("expected_code",),
        "decisive_mutation": ("expected_code", "clause", "repair"),
    }
    for fixture in fixtures:
        for key in required[fixture["kind"]]:
            if key not in fixture:
                run.refuse("RR-SCHEMA", f"{fixture['kind']} fixture {fixture['id']!r} lacks {key!r}")
    clause_codes: dict[str, str] = {}
    for clause in record["clauses"]:
        if clause["id"] in clause_codes:
            run.refuse("RR-SCHEMA", f"clause id {clause['id']!r} repeated")
        clause_codes[clause["id"]] = clause["code"]

    # ---- K2 pins --------------------------------------------------------------
    run.ran("K2")
    registry = ctx.stage_registry
    ladder = record["ladder"]
    rows = {entry["level"]: entry["row_sha256"] for entry in registry["levels"]}
    if ladder["registry_version"] != registry["registry_version"]:
        run.refuse("RR-PIN", f"registry version {ladder['registry_version']} is not {registry['registry_version']}")
    if ladder["table_sha256"] != registry["table"]["sha256"]:
        run.refuse("RR-PIN", "stage table digest does not match the registry")
    if ladder["level"] not in rows:
        run.refuse("RR-PIN", f"level {ladder['level']} is not in the registry")
    elif ladder["row_sha256"] != rows[ladder["level"]]:
        run.refuse("RR-PIN", f"row digest for level {ladder['level']} does not recompute")

    carrier = record["carrier"]
    carrier_entry = ctx.carriers.get(carrier["repo"])
    if carrier_entry is None:
        run.refuse("RR-PIN", f"carrier {carrier['repo']!r} is not in the carrier registry")
    source_bytes: dict[str, bytes] = {}
    for source in carrier["sources"]:
        if source["path"] in source_bytes:
            run.refuse("RR-SCHEMA", f"source {source['path']!r} listed twice")
            continue
        blob = ctx.resolver.read(carrier["repo"], carrier["commit"], source["path"])
        if blob is None:
            run.refuse("RR-PIN", f"source {source['path']!r} is absent at the carrier commit")
            continue
        if digest(blob) != source["sha256"]:
            run.refuse("RR-PIN", f"source {source['path']!r} digest does not recompute")
            continue
        source_bytes[source["path"]] = blob

    checker_pin = record["checker"]
    checker_source = ctx.resolver.read(TARGET_REPO, checker_pin["commit"], checker_pin["path"])
    if checker_source is None:
        run.refuse("RR-PIN", "checker is absent at its pinned commit")
    elif digest(checker_source) != checker_pin["sha256"]:
        run.refuse("RR-PIN", "checker digest does not recompute")
        checker_source = None
    entry = ctx.checkers.get(checker_pin["id"])
    of_record = False
    if entry is None:
        run.caps.add("CAP-SELF-CONSISTENT")
    elif (entry["path"], entry["sha256"], entry["commit"], entry["level"]) != (
        checker_pin["path"],
        checker_pin["sha256"],
        checker_pin["commit"],
        ladder["level"],
    ):
        run.refuse("RR-PIN", f"checker {checker_pin['id']!r} differs from its registered pin")
    elif entry.get("gated_step") not in ctx.gated_steps:
        run.caps.add("CAP-SELF-CONSISTENT")
    else:
        of_record = True
    obs["checker_of_record"] = of_record

    positives = [f for f in fixtures if f["kind"] == "positive"]
    for fixture in positives:
        path = fixture.get("source_path")
        if path is None:
            continue
        if path not in {s["path"] for s in carrier["sources"]}:
            run.refuse("RR-PIN", f"positive {fixture['id']!r} names a source outside the pinned sources")
        elif path in source_bytes:
            try:
                pinned = strict_loads(source_bytes[path])
            except CanonicalError:
                pinned = None
            if canonical_bytes(pinned) != canonical_bytes(fixture["payload"]):
                run.refuse("RR-PIN", f"positive {fixture['id']!r} is not the pinned carrier witness")

    lean = record["lean"]
    lean_bytes: dict[str, bytes] = {}
    if lean is not None:
        for source in [lean["report"], *lean["sources"]]:
            blob = ctx.resolver.read(carrier["repo"], carrier["commit"], source["path"])
            if blob is None or digest(blob) != source["sha256"]:
                run.refuse("RR-PIN", f"Lean file {source['path']!r} digest does not recompute")
            else:
                lean_bytes[source["path"]] = blob

    # ---- load the pinned checker ---------------------------------------------
    module = None
    if checker_source is not None:
        try:
            module = targets.load_checker(checker_source, checker_pin["id"])
        except targets.CheckerLoadError as exc:
            run.refuse("RR-REPLAY", str(exc))
    codes: tuple[str, ...] = ()
    if module is not None:
        codes = tuple(module.CODES)
        if module.STAGE != ladder["level"]:
            run.refuse("RR-PIN", f"checker decides level {module.STAGE}, not {ladder['level']}")
        if module.ROW_SHA256 != rows.get(module.STAGE):
            run.refuse("RR-PIN", f"checker is bound to row digest {module.ROW_SHA256!r}, not its level's")
        missing_generic = [code for code in TARGET_GENERIC_CODES if code not in codes]
        if missing_generic:
            run.refuse("RR-HOLLOW-CHECKER", f"checker declares no {missing_generic}")

    # ---- K4 replay, K5 rows ---------------------------------------------------
    observed: dict[str, tuple[str, str | None]] = {}
    if module is not None:
        run.ran("K4")
        for fixture in fixtures:
            observed[fixture["id"]] = targets.run(module.check, fixture["payload"], codes)
    obs["fixtures"] = [
        {
            "code": observed.get(f["id"], ("NOT_RUN", None))[1],
            "id": f["id"],
            "kind": f["kind"],
            "observed": observed.get(f["id"], ("NOT_RUN", None))[0],
            "payload_sha256": digest_obj(f["payload"]),
        }
        for f in fixtures
    ]
    run.ran("K5")
    if record["declared_fixture_count"] != len(fixtures):
        run.refuse("RR-ROWS", f"declared {record['declared_fixture_count']} fixtures, found {len(fixtures)}")

    # ---- K6 the 4-fixture rule, bite, and the probes -------------------------
    run.ran("K6")
    if not positives:
        run.refuse("RR-NO-POSITIVE", "no positive fixture")
    for fixture in positives:
        if targets.is_empty_payload(fixture["payload"]):
            run.refuse("RR-EMPTY-PAYLOAD", f"positive {fixture['id']!r} carries no primitive data")
        elif targets.is_flag_only(fixture["payload"]):
            run.refuse("RR-FLAG-ONLY", f"positive {fixture['id']!r} is a flag-only payload")
        elif fixture["id"] in observed and observed[fixture["id"]][0] != "PASS":
            run.refuse("RR-REPLAY", f"positive {fixture['id']!r} refused with {observed[fixture['id']][1]}")
    own = [f for f in fixtures if f["kind"] == "own_negative"]
    if not own:
        run.refuse("RR-NO-NEGATIVE", "the level's own negative instance is missing")
    for fixture in own:
        if fixture.get("row_sha256") != ladder["row_sha256"]:
            run.refuse("RR-NO-NEGATIVE", f"own negative {fixture['id']!r} is not bound to the row digest")
        if module is not None:
            if canonical_bytes(fixture["payload"]) != canonical_bytes(module.OWN_NEGATIVE):
                run.refuse("RR-NO-NEGATIVE", f"own negative {fixture['id']!r} is not the target's own instance")
            if fixture.get("expected_code") != module.OWN_NEGATIVE_CODE:
                run.refuse("RR-WRONG-REASON", f"own negative {fixture['id']!r} expects the wrong code")
    if not any(f["kind"] == "near_miss" for f in fixtures):
        run.refuse("RR-NO-NEAR-MISS", "no near-miss fixture")
    mutations = [f for f in fixtures if f["kind"] == "decisive_mutation"]
    if not mutations:
        run.refuse("RR-NO-FLIP", "no decisive mutation")
    if not record["clauses"]:
        run.refuse("RR-NO-FLIP", "no clause is claimed, so nothing can be bitten")
    for clause_id, code in sorted(clause_codes.items()):
        if module is not None and code not in codes:
            run.refuse("RR-WRONG-REASON", f"clause {clause_id!r} names undeclared code {code!r}")
    for fixture in fixtures:
        if fixture["kind"] not in REFUSED_KINDS or fixture["id"] not in observed:
            continue
        verdict, got = observed[fixture["id"]]
        expected = fixture.get("expected_code")
        if verdict == "PASS":
            run.refuse("RR-FIXTURE-PASSED", f"{fixture['kind']} {fixture['id']!r} was accepted")
        elif got != expected:
            run.refuse("RR-WRONG-REASON", f"{fixture['id']!r} refused with {got}, declared {expected}")
    bitten: set[str] = set()
    for fixture in mutations:
        clause = fixture.get("clause")
        repair = by_id.get(fixture.get("repair", ""))
        if clause not in clause_codes:
            run.refuse("RR-SCHEMA", f"mutation {fixture['id']!r} names undeclared clause {clause!r}")
            continue
        if fixture.get("expected_code") != clause_codes[clause]:
            run.refuse("RR-WRONG-REASON", f"mutation {fixture['id']!r} does not expect clause {clause!r}'s code")
            continue
        if repair is None or repair["kind"] != "positive":
            run.refuse("RR-NO-FLIP", f"mutation {fixture['id']!r} has no positive repair")
            continue
        if targets.edit_count(fixture["payload"], repair["payload"]) != 1:
            run.refuse("RR-NO-FLIP", f"mutation {fixture['id']!r} is not a single edit of its repair")
            continue
        if module is None:
            continue
        if observed[repair["id"]][0] == "PASS" and observed[fixture["id"]] == ("REFUSED", clause_codes[clause]):
            bitten.add(clause)
    if module is not None:
        for clause_id in sorted(clause_codes):
            if clause_id not in bitten:
                run.refuse("RR-NO-FLIP", f"clause {clause_id!r} has no mutation that flips the verdict")
    battery_rows: list[dict[str, Any]] = []
    if module is not None and positives:
        for probe, payload, expected in targets.probe_battery(positives[0]["payload"]):
            if expected == targets.PROBE_INAPPLICABLE:
                battery_rows.append(
                    {"code": targets.PROBE_INAPPLICABLE, "expected_code": None, "observed": "INAPPLICABLE", "probe": probe}
                )
                continue
            verdict, got = targets.run(module.check, payload, codes)
            battery_rows.append({"code": got, "expected_code": expected, "observed": verdict, "probe": probe})
            if (verdict, got) != ("REFUSED", expected):
                run.refuse("RR-HOLLOW-CHECKER", f"probe {probe} observed {verdict} {got}, expected {expected}")
    obs["battery"] = battery_rows

    # ---- K7 fiber --------------------------------------------------------------
    obs["fiber"] = None
    if record["fiber"] is not None and module is not None:
        run.ran("K7")
        accepted = sorted(
            {
                digest_obj(candidate)
                for candidate in record["fiber"]["candidates"]
                if targets.run(module.check, candidate, codes)[0] == "PASS"
            }
        )
        obs["fiber"] = {
            "accepted": len(accepted),
            "candidates": len(record["fiber"]["candidates"]),
            "ties": accepted if len(accepted) > 1 else [],
        }
        if record["fiber"]["uniqueness_required"] and len(accepted) > 1:
            run.refuse("RR-AMBIGUOUS", f"{len(accepted)} candidates accepted where one is required")

    # ---- K8 residual, K9 lift, K10 down rule ---------------------------------
    stage_change = record["stage_change"] or {}
    obs["residual"] = None
    computed_class = None
    if "residual" in stage_change:
        run.ran("K8")
        residual = stage_change["residual"]
        try:
            computed_class, phi1 = residual_class(residual)
        except ValueError as exc:
            run.refuse("RR-COUNTERFEIT", f"residual is malformed: {exc}")
        else:
            obs["residual"] = {
                "class": computed_class,
                "phi1": None if phi1 is None else format_rational(phi1),
            }
            if residual["claimed_class"] == "exact" and phi1 is not None:
                run.refuse("RR-COUNTERFEIT", f"exact claimed with Phi1 = {format_rational(phi1)} > 0")
            elif residual["claimed_class"] != computed_class:
                run.refuse("RR-COUNTERFEIT", f"claimed {residual['claimed_class']}, recomputed {computed_class}")
    obs["lift_licensed"] = None
    if "lift" in stage_change:
        run.ran("K9")
        lift = stage_change["lift"]
        search = stage_change.get("same_level_search")
        exhausted = search is not None and search["closed"] and search["stop"] != "budget_exhausted"
        conditions = {
            "residual closed and not exact": computed_class == "residual_closed",
            "context witness separates a pair": lift["context_witness"] is not None
            and lift["context_witness"]["x"] != lift["context_witness"]["y"],
            "next level is level + 1": lift["to_level"] == lift["from_level"] + 1,
            "budget strictly drops": parse_rational(lift["budget_after"]) < parse_rational(lift["budget_before"]),
            "declared growth": lift["growth_sha256"] is not None,
            "declared finite extension class": lift["extension_class"] is not None
            and lift["extension_class"]["candidates"] >= 1,
        }
        failed = sorted(name for name, holds in conditions.items() if not holds)
        obs["lift_licensed"] = exhausted and not failed
        if lift["claims_licence"]:
            if not exhausted:
                run.refuse("RR-EXHAUSTION", "licence claimed from a search that is open or ended on budget")
            if failed:
                run.refuse("RR-LIFT-TRIGGER-ONLY", f"licence claimed without: {', '.join(failed)}")
    if "down_rule" in stage_change:
        run.ran("K10")
        rule = stage_change["down_rule"]
        up: dict[str, str] = {}
        down: dict[str, str] = {}
        for pair in rule["up"]:
            if len(pair) != 2 or (pair[0] in up and up[pair[0]] != pair[1]):
                run.refuse("RR-ROLLBACK", f"up map entry {pair!r} is not a function entry")
                continue
            up[pair[0]] = pair[1]
        for pair in rule["down"]:
            if len(pair) != 2 or (pair[0] in down and down[pair[0]] != pair[1]):
                run.refuse("RR-ROLLBACK", f"down map entry {pair!r} is not a function entry")
                continue
            down[pair[0]] = pair[1]
        for old in sorted(up):
            if down.get(up[old]) != old:
                run.refuse("RR-ROLLBACK", f"d(u({old!r})) is {down.get(up[old])!r}, not {old!r}")
        if not rule["new_terms"]:
            run.refuse("RR-NON-DESCENT", "no new term exhibits NON_DESCENT")
        images = set(up.values())
        for term in rule["new_terms"]:
            if term in images:
                run.refuse("RR-NON-DESCENT", f"new term {term!r} is an old image")
            elif down.get(term) != "NON_DESCENT":
                run.refuse("RR-NON-DESCENT", f"new term {term!r} descends to {down.get(term)!r}")

    # ---- K11 Lean --------------------------------------------------------------
    lean_ok = False
    if lean is not None:
        run.ran("K11")
        before = len(run.refusals)
        allowed = set(carrier_entry["allowed_axioms"]) if carrier_entry else set(ALLOWED_AXIOMS_DEFAULT)
        report_blob = lean_bytes.get(lean["report"]["path"])
        report = _parse_axiom_report(report_blob.decode("utf-8", "replace")) if report_blob else {}
        source_paths = {s["path"] for s in lean["sources"]}
        for path in sorted(source_paths):
            text = lean_bytes.get(path, b"").decode("utf-8", "replace")
            for pattern in LEAN_FORBIDDEN:
                if pattern.search(text):
                    run.refuse("RR-AXIOM", f"forbidden token {pattern.pattern!r} in {path!r}")
        for theorem in lean["theorems"]:
            name = theorem["name"]
            if name not in report:
                run.refuse("RR-AXIOM", f"{name!r} has no #print axioms line in the pinned report")
            else:
                extra = sorted(set(report[name]) - allowed)
                if extra:
                    run.refuse("RR-AXIOM", f"{name!r} depends on {extra}")
            if theorem["source_path"] not in source_paths:
                run.refuse("RR-STATEMENT", f"{name!r} cites a source outside the pinned Lean sources")
                continue
            text = lean_bytes.get(theorem["source_path"], b"").decode("utf-8", "replace")
            statement = statement_text(text, name)
            if statement is None or digest(statement.encode("utf-8")) != theorem["statement_sha256"]:
                run.refuse("RR-STATEMENT", f"statement of {name!r} does not recompute from source")
        lean_ok = len(run.refusals) == before

    # ---- K12 transport ------------------------------------------------------------
    obs["transport"] = None
    certificate = record["transport"]
    if certificate is None:
        run.caps.add("CAP-NAMED")
    else:
        run.ran("K12")
        adapter_sha = None
        c1 = certificate.get("c1_identity_custody") if isinstance(certificate, dict) else None
        adapter = c1.get("adapter") if isinstance(c1, dict) else None
        if isinstance(adapter, dict) and isinstance(adapter.get("path"), str):
            blob = ctx.resolver.read(carrier["repo"], carrier["commit"], adapter["path"])
            adapter_sha = None if blob is None else digest(blob)
        expect = transport.Expectation(
            carrier={"commit": carrier["commit"], "part": carrier["part"], "repo": carrier["repo"]},
            target_repo=TARGET_REPO,
            level=ladder["level"],
            registry_version=ladder["registry_version"],
            row_sha256=ladder["row_sha256"],
            checker_id=checker_pin["id"],
            source_manifest_sha256=transport.manifest_digest(carrier["sources"]),
            witness_sha256=digest_obj(positives[0]["payload"]) if positives else "",
            standing_entries=tuple(carrier_entry["standing_loss_entries"]) if carrier_entry else (),
            blind_framing=record["framing"] in ("BR", "AG"),
            structure_maps=tuple(module.STRUCTURE_MAPS) if module is not None else (),
            adapter_sha256=adapter_sha,
        )
        findings = transport.validate_certificate(certificate, expect)
        for finding in findings:
            if finding.code == "TC-COLLAPSE":
                run.refuse("RR-TRANSPORT-COLLAPSE", finding.detail)
            elif finding.code == "TC-CRITERION-MISSING" and "declares no typed map" in finding.detail:
                run.refuse("RR-TRANSPORT-MISSING", finding.detail)
            else:
                run.refuse("RR-TRANSPORT-INVALID", f"{finding.code}: {finding.detail}")
        replay_pass = bool(positives) and all(observed.get(p["id"], ("",))[0] == "PASS" for p in positives)
        ledger = certificate.get("c6_loss_and_authority", {}).get("loss_ledger") if isinstance(certificate, dict) else None
        obs["transport"] = {
            "certificate_sha256": digest_obj(certificate),
            "disposition": "REPLAYED_PASS" if replay_pass and not findings else "REPLAYED_FAIL",
            "findings": sorted({finding.code for finding in findings}),
            "loss_ledger_sha256": digest_obj(ledger) if ledger is not None else None,
        }

    # ---- K13 blindness and chains --------------------------------------------------
    run.ran("K13")
    blind = record["provenance"]["source_blindness"] == "BLIND"
    if blind and record["framing"] in ("SC", "TO", "TFC", "CC", "AP"):
        run.refuse("RR-LEAK", f"framing {record['framing']} names the target, so it cannot be blind")
    if blind:
        texts = [text.lower() for text in ctx.level_texts.get(ladder["level"], ())]
        for path in sorted(source_bytes):
            haystack = source_bytes[path].decode("utf-8", "replace").lower()
            hits = [text for text in texts if text and text in haystack]
            if hits:
                run.refuse("RR-LEAK", f"source {path!r} contains {len(hits)} of the level's strings")
    if record["inputs"]["receipts_consumed"]:
        run.refuse("RR-CHAIN", f"{len(record['inputs']['receipts_consumed'])} receipts consumed as evidence")
    for path in sorted(source_bytes):
        if SCHEMA_ID.encode("ascii") in source_bytes[path]:
            run.refuse("RR-CHAIN", f"source {path!r} is a reach receipt")

    # ---- K14 gate status ---------------------------------------------------------
    gated = False
    if record["gates"] is not None:
        run.ran("K14")
        workflow = ctx.resolver.read(carrier["repo"], carrier["commit"], record["gates"]["workflow_path"])
        if workflow is None:
            run.refuse("RR-GATE", "the declared workflow is absent at the carrier commit")
        else:
            text = workflow.decode("utf-8", "replace")
            absent = [step for step in record["gates"]["steps"] if step not in text]
            if absent:
                run.refuse("RR-GATE", f"{len(absent)} declared step(s) absent from the workflow")
            else:
                gated = True

    # ---- K15 determinism: a fresh load must observe the same verdicts ----------------
    if module is not None and checker_source is not None:
        run.ran("K15")
        again = targets.load_checker(checker_source, checker_pin["id"])
        for fixture in fixtures:
            if targets.run(again.check, fixture["payload"], codes) != observed[fixture["id"]]:
                run.refuse("RR-NONDETERMINISTIC", f"fixture {fixture['id']!r} differs on a second replay")

    # ---- K16 vocabulary (only inside 19L57G1) ---------------------------------------
    if record["placement"] == "19L57G1":
        run.ran("K16")
        if not ctx.watchlist_sha256:
            run.refuse("RR-VOCABULARY", "placed inside 19L57G1 with no watchlist to scan against")
        else:
            words = set(re.findall(r"[a-z]+", data.decode("ascii").lower()))
            hits = sorted(word for word in words if sha256_hex(word.encode("ascii")) in ctx.watchlist_sha256)
            if hits:
                run.refuse("RR-VOCABULARY", f"{len(hits)} watched term(s) in the receipt")

    obs["lean_ok"] = lean_ok
    obs["gated"] = gated
    return _finish(run, record, record_sha, obs)


def _finish(run: _Run, record: dict[str, Any] | None, record_sha: str, obs: dict[str, Any]) -> Result:
    codes = run.codes()
    framing = record.get("framing") if isinstance(record, dict) else None
    if framing == "TO":
        run.caps.add("CAP-SELF-CONSISTENT")
    refused = any(code != "RR-AMBIGUOUS" for code in codes)
    if refused:
        terminal = "REFUSED"
    elif codes:
        terminal = "UNRESOLVED"
    elif "CAP-SELF-CONSISTENT" in run.caps:
        terminal = "SELF_CONSISTENT_ONLY"
    else:
        terminal = "EVIDENCE_ONLY"

    grades = {"B": "-", "E": "NONE", "P": "-", "R": "-"}
    if terminal != "REFUSED" and framing is not None:
        assert record is not None
        if "CAP-NAMED" in run.caps:
            evidence = "NAMED"
        else:
            evidence = "COMPUTED"
            if obs.get("lean_ok"):
                evidence = "LEAN"
            if obs.get("gated"):
                evidence = "GATED"
        grades["E"] = evidence
        grades["P"] = {"SC": "supplied", "TFC": "supplied", "BR": "native", "AG": "native", "AP": "apparatus", "TO": "own"}.get(
            framing, "-"
        )
        if framing in ("SC", "TFC", "TO"):
            grades["B"] = "named"
        elif framing == "BR" and record["provenance"]["source_blindness"] == "BLIND":
            grades["B"] = "blind"
        else:
            grades["B"] = "steered"
        if (
            terminal == "EVIDENCE_ONLY"
            and evidence != "NAMED"
            and obs.get("checker_of_record")
            and framing in ("SC", "BR", "AG", "TFC", "AP")
        ):
            grades["R"] = "R1"

    status = dict(run.status)
    computed = {
        "battery": obs.get("battery", []),
        "caps": sorted(run.caps),
        "checker_of_record": bool(obs.get("checker_of_record", False)),
        "checks": status,
        "fiber": obs.get("fiber"),
        "fixtures": obs.get("fixtures", []),
        "grades": grades,
        "lift_licensed": obs.get("lift_licensed"),
        "record_sha256": record_sha,
        "refusals": [
            {"check": check, "code": code, "detail": detail}
            for check, code, detail in sorted(run.refusals, key=lambda r: (int(r[0][1:]), r[1], r[2]))
        ],
        "residual": obs.get("residual"),
        "status_ceiling": "SELF_CONSISTENT" if framing == "TO" else "PROPOSED",
        "terminal": terminal,
        "transport": obs.get("transport"),
    }
    receipt: dict[str, Any] = dict(record) if isinstance(record, dict) else {}
    receipt["computed"] = computed
    return Result(receipt=receipt, codes=codes, terminal=terminal, grades=grades, caps=tuple(sorted(run.caps)))


def receipt_bytes(result: Result) -> bytes:
    return canonical_bytes(result.receipt)


def verify_receipt(data: bytes, ctx: Context) -> Result:
    """K3 on a stored receipt: delete ``computed``, recompute, compare."""
    try:
        receipt = parse_canonical(data)
    except CanonicalError as exc:
        run = _Run()
        run.refuse(exc.code, exc.detail)
        return _finish(run, None, digest(data), {})
    if not isinstance(receipt, dict) or "computed" not in receipt:
        run = _Run()
        run.refuse("RR-SCHEMA", "a stored receipt carries a computed block")
        return _finish(run, None, digest(data), {})
    stated = receipt.pop("computed")
    result = check_record(canonical_bytes(receipt), ctx)
    if canonical_bytes(stated) != canonical_bytes(result.receipt["computed"]):
        run = _Run()
        run.refuse("RR-PRODUCER-VERDICT", "the stored computed block differs from recomputation")
        return _finish(run, receipt, digest(canonical_bytes(receipt)), {})
    return result

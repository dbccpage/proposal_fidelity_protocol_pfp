# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Layer-1 witness bundles, challenge evidence, loss ledgers, and (binding
layer) transport certificates, register entries, checker inputs and the
computed grade table.

Every output is canonical bytes.  Nothing carries a timestamp, a host name
or a model identity.  Bundles, evidence and loss ledgers carry no level
number; only files under ``bindings/`` do.  The harness never writes a
reach grade: the R/E/P/B grades are the receiving side's.  What it computes
and records are witness grades, clause censuses, answer types and statuses.

AuthorityEffect: None
"""

from __future__ import annotations

import importlib
import re
from collections.abc import Mapping, Sequence
from types import ModuleType

from omega_engine_operations.domain.level_engine_context import (
    current_context,
)
from omega_engine_operations.use_cases.level_engine.research_engine.canon import (
    dumps,
    git_blob_id,
    load_path,
    sha256_tag,
)
from omega_engine_operations.use_cases.level_engine.research_engine.errors import (
    IntakeRefusal,
    Refusal,
)
from omega_engine_operations.use_cases.level_engine.research_engine.level import (
    LevelResult,
    check_expectations,
    check_kill_rules,
    load_fixtures,
)
from omega_engine_operations.use_cases.level_engine.research_engine.sealed_evidence import (
    source as sealed_source,
)
from omega_engine_operations.use_cases.level_engine.research_engine.structure import (
    refuse_hollow,
    to_json,
)

ROOT = current_context().runtime_root
REPO = current_context().repository_root
REACH_PKG = "omega_engine_pfp.infrastructure.tower_research.reach"
LINEAGE = {"model_families": ["claude"], "shared_author": True,
           "note": "the harness and any draft checker share an author and a model family; "
                   "agreement between them is correlated evidence"}


def pins() -> dict[str, object]:
    p = load_path(current_context().governance_path("PINS.json"))
    assert isinstance(p, dict)
    return p


def sealed_commit() -> str:
    current_context().require_vendor()
    v = pins()["vendored"]
    assert isinstance(v, dict)
    return str(v["19L57G1"]["commit"])


def _file_entry(rel: str) -> dict[str, str]:
    data = (ROOT / rel).read_bytes()
    return {"blob": git_blob_id(data), "path": rel, "sha256": sha256_tag(data)}


_PAYLOAD_IMPORT = re.compile(r"^from \.{3}payload\.([a-z_]+(?:\.[a-z_]+)?) import", re.M)


def payload_imports(challenge_id: str) -> set[str]:
    """The payload modules this challenge's spec imports from outside its own
    folder (the shared helpers, or another level's spec)."""
    import ast
    import importlib.util
    source = ROOT / "payload" / challenge_id / "spec.py"
    base = __package__.rsplit(".", 1)[0]
    prefix = base + ".payload."
    package = prefix + challenge_id
    dependencies: set[str] = set()
    for node in ast.walk(ast.parse(source.read_text(encoding="utf-8"))):
        if not isinstance(node, ast.ImportFrom):
            continue
        name = "." * node.level + (node.module or "")
        module = importlib.util.resolve_name(name, package) if node.level else name
        candidates = [module]
        candidates += [module + "." + alias.name for alias in node.names]
        for candidate in candidates:
            if candidate.startswith(prefix):
                relative = "payload/" + candidate.removeprefix(prefix).replace(".", "/") + ".py"
                if (ROOT / relative).is_file() and (ROOT / relative) != source:
                    dependencies.add(relative)
    return dependencies


def harness_sources(challenge_id: str) -> list[dict[str, str]]:
    """Runtime context, engine and serialization code plus this payload and its imports."""
    rels = sorted(
        {p.relative_to(ROOT).as_posix()
         for layer in ("outward", f"payload/{challenge_id}")
         for p in (ROOT / layer).rglob("*")
         if p.is_file() and p.suffix in (".py", ".json", ".md", ".lean", ".txt") and "__pycache__" not in p.parts}
        | {p.name for p in ROOT.glob("*.py") if p.is_file()}
        | payload_imports(challenge_id)
    )
    return [_file_entry(r) for r in rels]


def is_packet_level(challenge_id: str) -> bool:
    from omega_engine_operations.use_cases.level_engine.research_engine.level import load_spec

    return hasattr(load_spec(challenge_id), "packets")


def input_schema(challenge_id: str) -> str:
    return INPUT_SCHEMA_PACKET if is_packet_level(challenge_id) else INPUT_SCHEMA_STRUCTURE


# ---------------------------------------------------------------------------
# Inputs in the neutral draft form, and the injectivity check
# ---------------------------------------------------------------------------

INPUT_SCHEMA_STRUCTURE = "draft:harness.finite-structure.v1"
INPUT_SCHEMA_PACKET = "draft:harness.packet.v1"


def fixture_inputs(challenge_id: str) -> list[tuple[str, str, object]]:
    """(fixture id, role, canonical input) for every fixture, mutation last."""
    d = ROOT / "payload" / challenge_id
    if is_packet_level(challenge_id):
        from omega_engine_operations.use_cases.level_engine.research_engine.level import load_spec

        packets = getattr(load_spec(challenge_id), "packets")()
        return [(fid, role, {"packet": pk}) for fid, role, pk, _ in packets]
    out: list[tuple[str, str, object]] = []
    for fx in load_fixtures(d):
        out.append((fx.fid, fx.role, to_target(to_json(fx.structure), fx.protected)))
    return out


def to_target(structure: Mapping[str, object], protected: Sequence[tuple[int, int]]) -> dict[str, object]:
    """The typed map from a hosted claim to the neutral draft input.  Digests
    travel as written, byte strings in ``sha256:<hex>`` form, when present;
    texts travel as written, when present."""
    out: dict[str, object] = {
        "protected": [list(p) for p in protected],
        "relations": structure["tuples"],
        "sorts": structure["sorts"],
        "symbols": structure["symbols"],
        "values": structure["values"],
    }
    if "digests" in structure:
        out["digests"] = structure["digests"]
    if "texts" in structure:
        out["texts"] = structure["texts"]
    return out


def check_injective(inputs: Sequence[tuple[str, str, object]]) -> None:
    seen: dict[bytes, str] = {}
    for fid, _, obj in inputs:
        b = dumps(obj)
        if b in seen:
            raise IntakeRefusal("RR-TRANSPORT-COLLAPSE", f"{fid} and {seen[b]} map to one input")
        seen[b] = fid


def receiving(module: str) -> ModuleType:
    """One module of the receiving side's reach package, from this checkout.
    The repository root is appended, never prepended, so nothing here is
    shadowed."""
    return importlib.import_module(f"{REACH_PKG}.{module}")


def inapplicable_mark() -> str:
    """The receiving side's mark for a probe equal to the positive."""
    return str(receiving("targets").PROBE_INAPPLICABLE)


def probe_battery(positive: object) -> list[tuple[str, object, str]]:
    """The receiving side's own probe battery, imported, not copied.  A probe
    equal to the positive carries its inapplicable mark in place of an
    expected code: it cannot be refused without refusing the witness."""
    battery = receiving("targets").probe_battery(positive)
    return [(str(name), payload, str(code)) for name, payload, code in battery]


HARNESS_CODE = {"R_EMPTY_INPUT": "EMPTY_FIXTURE", "R_VERDICT_FIELD": "FLAG_ONLY_FIXTURE"}


def intake_probes(positive: object) -> dict[str, str]:
    """The harness's own intake on the battery: each probe must be refused
    with the harness code matching the receiving side's expected code.  An
    inapplicable probe is marked and not run, as the receiving side does."""
    mark = inapplicable_mark()
    out: dict[str, str] = {}
    for name, obj, code in probe_battery(positive):
        if code == mark:
            out[name] = mark
            continue
        try:
            refuse_hollow(obj, name)
        except IntakeRefusal as e:
            out[name] = e.code
        else:
            out[name] = "ACCEPTED"
    return out


def hollow_code(obj: object) -> str:
    """What hollowness alone decides about a payload."""
    try:
        refuse_hollow(obj)
    except IntakeRefusal as e:
        return e.code
    return "ACCEPTED"


def left_to_target(positive: object) -> dict[str, str]:
    """Probes the receiving side expects refused that hollowness cannot
    decide: they still carry a datum and no verdict flag, so only the
    target's own schema can refuse them.  Inapplicable probes are not
    expected refused, so none is listed."""
    mark = inapplicable_mark()
    return {name: "needs_target_schema" for name, obj, code in probe_battery(positive)
            if code != mark and hollow_code(obj) == "ACCEPTED"}


def intake_ok(probes: Mapping[str, str], positive: object) -> bool:
    """Every probe hollowness decides is refused with the harness code that
    matches the receiving side's expected code; the rest are left to the
    target's schema and listed; an inapplicable probe carries the mark."""
    mark = inapplicable_mark()
    for name, obj, code in probe_battery(positive):
        if code == mark:
            if probes.get(name) != mark:
                return False
            continue
        decided = hollow_code(obj)
        if decided == "ACCEPTED":
            if probes.get(name) != "ACCEPTED":
                return False
        elif probes.get(name) != HARNESS_CODE.get(code) or decided != HARNESS_CODE.get(code):
            return False
    return set(probes) == {name for name, _, _ in probe_battery(positive)}


# ---------------------------------------------------------------------------
# Computed summaries
# ---------------------------------------------------------------------------


def computed_answer_type(result: LevelResult) -> str:
    kinds = {c for _, c, _ in result.census}
    if "decoded" in kinds:
        return "M"
    if "derivability" in kinds:
        return "D"
    return "A"


def mismatches(result: LevelResult) -> tuple[str, ...]:
    out = list(check_expectations(result.challenge_id, result.verdicts))
    if not is_packet_level(result.challenge_id):
        out += check_kill_rules(load_fixtures(ROOT / "payload" / result.challenge_id), result.verdicts)
    if computed_answer_type(result) != result.answer_type:
        out.append("ANSWER_TYPE_DISAGREES")
    if result.hosting is not None and (result.hosting.defaulted or not result.hosting.non_descent_cases):
        out.append("RR-NON-DESCENT")
    return tuple(sorted(out))


def status(result: LevelResult) -> str:
    if mismatches(result):
        return "MISMATCH"
    if result.missing_components:
        return "UNRESOLVED"
    return "EXPECTED"


def caps(result: LevelResult) -> list[str]:
    return [f"CAP-SUPPLIED:{cid}" for cid, c, _ in result.census if c == "decoded"]


def native_share(result: LevelResult) -> str:
    k = sum(1 for _, c, _ in result.census if c == "derivability")
    return f"{k} of {len(result.census)}"


def evidence_ceiling(result: LevelResult) -> str:
    if result.carrier_part == "repo_content" and result.native_claims:
        return "LEAN_CITED_FROM_SEALED_REPORT"
    if result.native_claims and not result.missing_components:
        return "LEAN_HARNESS_BUILD"
    return "COMPUTED"


# ---------------------------------------------------------------------------
# Layer 1: evidence, bundle, loss ledger (no level numbers)
# ---------------------------------------------------------------------------


def evidence(result: LevelResult) -> dict[str, object]:
    return {
        "answer_type_computed": computed_answer_type(result),
        "answer_type_declared": result.answer_type,
        "authority_effect": "None",
        "caps": caps(result),
        "carrier_part": result.carrier_part,
        "challenge_id": result.challenge_id,
        "clause_census": result.census_json(),
        "evidence_ceiling": evidence_ceiling(result),
        "extra": dict(result.extra),
        "hosting_down_check": None if result.hosting is None else {
            "defaulted": result.hosting.defaulted,
            "non_descent_cases": result.hosting.non_descent_cases,
            "old_image_cases": result.hosting.old_image_cases,
        },
        "intake_probes": intake_probes(_positive_input(result.challenge_id)),
        "mismatches": list(mismatches(result)),
        "missing_components": list(result.missing_components),
        "native_share": native_share(result),
        "restatement_sha256": restatement_digest(result.challenge_id),
        "schema": "challenge-evidence/2",
        "stage": {"bound_note": "at most three items (embargo)", "name": "base"},
        "status": status(result),
        "target": "named in the binding layer",
        "verdicts": [v.to_json() for v in result.verdicts],
    }


def _positive_input(challenge_id: str) -> object:
    return next(obj for _, role, obj in fixture_inputs(challenge_id) if role == "positive")


def restatement_digest(challenge_id: str) -> str:
    return sha256_tag((ROOT / "payload" / challenge_id / "RESTATEMENT.md").read_bytes())


STANDING = [
    ("source.presentation_tokens", "tokens of hosted elements", "not presented", "DROPPED"),
    ("source.declared_bounds", "responses of at most three items (embargo)", "unbounded obligation", "WEAKENED"),
    ("source.claim_class", "bounded computation or cited theorem", "target verdict", "WEAKENED"),
    ("source.continuation_policy", "demands endogenous, payments exogenous", "challenge supplied", "WEAKENED"),
    ("source.carrier_part", "credit as recorded in the bundle", "same", "PRESERVED"),
    ("target.obligation_origin", "curated catalogue at the pinned commit", "same", "PRESERVED"),
    ("target.terminal_vocabulary", "native refusal codes", "target codes, not yet published", "UNKNOWN"),
]


def loss_fields(result: LevelResult) -> list[tuple[str, str, str, str]]:
    rows = list(STANDING)
    cid = result.challenge_id
    if cid == "bare_inscription":
        rows.append(("source.refused_cases", "admitted as opaque wholes by the sealed genesis",
                     "refused at this stage", "DROPPED"))
    if cid == "first_separation":
        rows.append(("source.admission_reading", "two readings, two lineages", "one packet", "WEAKENED"))
        lin = result.extra.get("lineages", {})
        assert isinstance(lin, dict)
        for key in sorted(lin):
            n = lin[key]["engine_classes"]
            cls = "PRESERVED" if n == 1 else "WEAKENED"
            rows.append((f"source.cost_measure.{key}", f"{n} classes", "1 packet", cls))
    else:
        rows.append(("source.admission_reading", "hosting admits by explicit events only", "same", "PRESERVED"))
    if cid == "cell_orientation":
        rows.append(("source.witness_choice", "a witness grade with its tie structure",
                     "a verdict on the claim", "WEAKENED"))
    custody = result.extra.get("witness_custody")
    if isinstance(custody, Mapping):
        trees = ", ".join(f"research/{t}" for t in custody["trees"])
        rows.append(("source.witness_custody",
                     f"research-tree evidence: {trees} at the pinned 19L57G1 commit, outside the seal and its gates",
                     "a replay under the 19L57G1 key, admitted by the author's ruling of 2026-09-25", "WEAKENED"))
    findings = result.extra.get("findings", [])
    if not isinstance(findings, list):
        raise Refusal("RR-FINDINGS", f"{cid}: findings must be a list, not {type(findings).__name__}")
    for k, text in enumerate(findings, 1):
        rows.append((f"source.finding.{k}", str(text), "recorded, not changed", "PRESERVED"))
    if result.carrier_part == "harness_computation":
        rows.append(("source.coefficient_domain", "boolean derivability and exact rationals", "draft input",
                     "UNKNOWN"))
    for cid_, c, _ in result.census:
        if c == "decoded":
            rows.append((f"clause.{cid_}", "decided outside the grammar over decoded values",
                         "same obligation", "WEAKENED"))
    return sorted(rows)


def loss_ledger(result: LevelResult) -> dict[str, object]:
    rows = loss_fields(result)
    count: dict[str, int] = {}
    for _, _, _, cls in rows:
        count[cls] = count.get(cls, 0) + 1
    body: dict[str, object] = {
        "changed_assumptions": sorted(
            ["the challenge is supplied; no demand for it is derived"]
            + (["values are decided outside the grammar"] if caps(result) else [])
        ),
        "count": count,
        "fields": [
            {"classification": c, "field_or_law": f, "source_value": s, "target_value": t} for f, s, t, c in rows
        ],
        "open_obligations": sorted(
            ["target replay by the receiving side's checker"]
            + [f"component {m}" for m in result.missing_components]
        ),
        "reframe_decision": "NONE",
        "status_ceiling": "PROPOSED",
    }
    body["commitment"] = sha256_tag(dumps(body))
    return {"authority_effect": "None", "schema": "mssn.loss-ledger.v2", **body}


def implementation_provenance(challenge_id: str) -> dict[str, object]:
    """Bind installed implementation bytes without claiming they belong to the vendor commit."""
    sources = harness_sources(challenge_id)
    return {
        "kind": "installed_package_resources",
        "package": "omega_engine_pfp.infrastructure.tower_research.level_engine",
        "source_basis": "installed_resource_bytes",
        "sources": sources,
        "source_manifest_sha256": sha256_tag(dumps(sources)),
    }


def _carrier_provenance(result: LevelResult, implementation: Mapping[str, object],
                        sealed_pin: str) -> dict[str, object]:
    if result.carrier_part == "repo_content":
        return {"repo": "19L57G1", "commit": sealed_pin, "part": result.carrier_part,
                "source_basis": "pinned_vendor_git", "sources": [sealed_source(rel) for rel in result.sources]}
    return {"repo": "the_symbol_game", "commit": None, "part": result.carrier_part,
            "source_basis": "installed_package_resources", "package": implementation["package"],
            "source_manifest_sha256": implementation["source_manifest_sha256"],
            "sources": implementation["sources"]}


def witness_bundle(result: LevelResult, evidence_sha: str, loss_sha: str, inputs: Sequence[tuple[str, str, object]]) -> dict[str, object]:
    implementation = implementation_provenance(result.challenge_id)
    sealed_pin = sealed_commit()
    dependency = {"repo": "19L57G1", "commit": sealed_pin, "access": "read_only"}
    carrier = _carrier_provenance(result, implementation, sealed_pin)
    spec_rel = f"payload/{result.challenge_id}/spec.py"
    positive = next(obj for fid, role, obj in inputs if role == "positive")
    return {
        "authority_effect": "None",
        "carrier": carrier,
        "implementation": implementation,
        "sealed_dependency": dependency,
        "evidence_sha256": evidence_sha,
        "carrier_refusals": [
            {"evidence": f"{result.challenge_id}:{v.fid}:{v.code}", "of": v.fid}
            for v in result.verdicts if not v.satisfied
        ],
        "encoding": {
            "decoder_package": implementation["package"],
            "decoder_path": spec_rel,
            "decoder_sha256": sha256_tag((ROOT / spec_rel).read_bytes()),
            "input_schema": input_schema(result.challenge_id),
        },
        "lineage": LINEAGE,
        "loss_ledger_sha256": loss_sha,
        "native_claims": [dict(c) for c in result.native_claims],
        "non_claims": [
            "answers a supplied challenge; not a derivation from the seed",
            "no independent convergence with any outside list is claimed",
            "package byte custody is not a Git commit or production verifier claim",
        ],
        "provenance": {"isolation": "NOT_APPLICABLE", "purity": "NOT_APPLICABLE", "source_blindness": "NOT_BLIND"},
        "schema": "mssn.witness-bundle.v2",
        "stage_change": None,
        "target_input": positive,
    }


# ---------------------------------------------------------------------------
# Binding layer: certificate, register entry, checker input, grade row
# ---------------------------------------------------------------------------

STRUCTURE_MAP_LEVELS = frozenset({"cell_faces", "cell_orientation"})


def transport_certificate(level: int, binding: Mapping[str, object], result: LevelResult,
                          bundle_sha: str, loss_sha: str, inputs: Sequence[tuple[str, str, object]]) -> dict[str, object]:
    row = binding["row"]
    assert isinstance(row, dict)
    positive = next(obj for fid, role, obj in inputs if role == "positive")
    pos_w = next(v.witness for v in result.verdicts if v.role == "positive")
    cost = pos_w.cost[0] if pos_w is not None and pos_w.cost is not None else 0
    names_map = result.challenge_id in STRUCTURE_MAP_LEVELS
    implementation = implementation_provenance(result.challenge_id)
    sealed_pin = sealed_commit()
    carrier = _carrier_provenance(result, implementation, sealed_pin)
    payload: dict[str, object] = {
        "authority_effect": "None",
        "c1_identity_custody": {
            "adapter": {"path": f"payload/{result.challenge_id}/spec.py",
                        "sha256": sha256_tag((ROOT / "payload" / result.challenge_id / "spec.py").read_bytes())},
            "coefficient_domain": {"source": "boolean-derivability+nat-costs", "target": "draft input"},
            "environment_pins": {"pins_json_sha256": sha256_tag((current_context().governance_path("PINS.json")).read_bytes())},
            "payload_sha256": sha256_tag(dumps(positive)),
            "same_carrier": False,
            "source_manifest_sha256": bundle_sha,
            "source_receipts": [{"kind": "lean_axioms_txt", "sha256": sealed_source("artifacts/lean_axioms.txt")["sha256"]}],
        },
        "c2_typed_map": {
            "kind": "SORT_MAP",
            "map_sha256": sha256_tag(dumps(["sorts", "symbols", "relations", "values", "protected"])),
            "orientation": "declared order of elements",
            "simplicial_measure": None,
            "sorts": [{"source": "element", "target": "element index"},
                      {"source": "claim form", "target": "relation or sort"}],
            "unmapped_sorts": ["presentation token", "witness form"],
        },
        "c3_compatibility": {
            "not_applicable_reason": None if names_map else "the obligation names no structure map",
            "open": "squares against the target's structure maps wait for the target checker" if names_map else None,
            "squares": [],
        },
        "c4_goal_and_moves": {
            "attempt_space_correspondence_sha256": None,
            "cost": {"source_measure": "mu1", "target_convention": "declared-cost/v1"},
            "move_simulation_sha256": None,
            "source_goal_sha256": restatement_digest(result.challenge_id),
            "target_goal_sha256": row["row_sha256"],
        },
        "c5_target_verification": {"replay_sha256": None, "source_admission_is_provenance_only": True,
                                   "verdict": "PENDING", "witness_sha256": sha256_tag(dumps(positive))},
        "c6_loss_and_authority": {"loss_ledger_sha256": loss_sha,
                                  "open_obligations": ["target replay", "c4 attempt-space correspondence"]
                                  + (["c3 structure-map squares"] if names_map else []),
                                  "reframe": {"child": None, "decision": "NONE"}, "status_ceiling": "PROPOSED"},
        "carrier": {key: value for key, value in carrier.items() if key != "sources"},
        "implementation": {key: value for key, value in implementation.items() if key != "sources"},
        "sealed_dependency": {"repo": "19L57G1", "commit": sealed_pin, "access": "read_only"},
        "cost": {"convention_id": "declared-cost/v1", "value": f"{cost}/1"},
        "disposition": "TARGET_REPLAY_REQUIRED",
        "schema": "mssn.transport-certificate.v2",
        "status": "PROPOSED",
        "target": {"checker": None, "level": level, "paper_sha256": None, "registry_version": None,
                   "row_sha256": row["row_sha256"]},
    }
    payload_digest = sha256_tag(b"mssn.transport-certificate\0" + dumps(payload))
    envelope = {"canonicalization_profile": "omega-sorted-json-no-float-v1", "payload_digest": payload_digest,
                "payload_domain_tag": "mssn.transport-certificate"}
    envelope["record_digest"] = sha256_tag(dumps({**payload, "envelope": envelope}))
    return {**payload, "envelope": envelope}


def register_entry(level: int, result: LevelResult, tag: str | None = None) -> dict[str, object]:
    return {"framing": "SC", "id": f"SC-{tag or f'L{level:03d}'}", "level": level,
            "native_restatement_sha256": restatement_digest(result.challenge_id),
            "registry_version": None, "supplied_by": "author"}


def checker_input(level: int, binding: Mapping[str, object], result: LevelResult,
                  inputs: Sequence[tuple[str, str, object]]) -> dict[str, object]:
    roles = binding["fixture_roles"]
    assert isinstance(roles, dict)
    by = {v.fid: v for v in result.verdicts}
    positive = next(obj for _, role, obj in inputs if role == "positive")
    return {
        "authority_effect": "None",
        "challenge_id": result.challenge_id,
        "fixtures": [
            {"expected_outcome": "PASS" if by[fid].satisfied else "REFUSED",
             "id": fid, "input": obj, "input_sha256": sha256_tag(dumps(obj)),
             "native_code": by[fid].code, "native_verdict": "ACCEPT" if by[fid].satisfied else "REFUSE",
             "target_role": roles[fid]}
            for fid, _, obj in inputs
        ],
        "harness_intake": intake_probes(positive),
        "probe_battery_expected": {name: code for name, _, code in probe_battery(positive)},
        "probes_left_to_target_schema": left_to_target(positive),
        "input_schema": input_schema(result.challenge_id),
        "level": level,
        "schema": "level-engine.checker-input.v1",
        "target": target_status(binding),
    }


def target_status(binding: Mapping[str, object]) -> str:
    tgt = binding["target"]
    assert isinstance(tgt, dict)
    checker = tgt["checker"]
    return f"CHECKER_OF_RECORD:{checker['id']}" if isinstance(checker, dict) else str(tgt["status"])


def grade_row(level: int, result: LevelResult, binding: Mapping[str, object]) -> dict[str, object]:
    return {
        "answer_type": computed_answer_type(result),
        "caps": caps(result),
        "carrier_part": result.carrier_part,
        "challenge_id": result.challenge_id,
        "evidence_ceiling": evidence_ceiling(result),
        "fixtures": {v.fid: {"code": v.code, "witness_grade": v.witness.grade if v.witness else None}
                     for v in result.verdicts},
        "level": level,
        "missing_components": list(result.missing_components),
        "native_share": native_share(result),
        "status": status(result),
        "target": target_status(binding),
    }

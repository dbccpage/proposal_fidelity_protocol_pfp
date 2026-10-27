"""Write or check the binding layer: ``bindings/L<NNN>.json``.

The binding is the only place a level number appears.  The ladder row is
bound by the SHA-256 of its bytes (the line whose first field is the level,
without its line ending) in the authenticated packaged table. Its historical
commit and path are retained as provenance. Row text is never stored here.

AuthorityEffect: None
"""

from __future__ import annotations

import argparse
import hashlib
import sys

if __name__ == "__main__":
    import runpy

    sys.argv = [sys.argv[0], "bind", *sys.argv[1:]]
    raise SystemExit(runpy.run_module(
        "operations.infrastructure.level_engine_ports",
        run_name="__main__",
    ))

from operations.domain.level_engine_context import (
    LevelEngineOperationPorts,
    current_context,
)

ROOT = current_context().runtime_root

from operations.use_cases.level_engine.research_engine.canon import (  # noqa: E402
    dumps,
    load_path,
    write_bytes,
)
from operations.use_cases.level_engine.research_engine.level import (
    load_spec,  # noqa: E402
)

LEVELS: dict[int, dict[str, object]] = {
    0: {"challenge_id": "bare_inscription", "answer_type": "A", "kernel": "replay"},
    1: {"challenge_id": "first_separation", "answer_type": "D", "kernel": "replay"},
    2: {"challenge_id": "edge_endpoints", "answer_type": "D", "kernel": "relation_tables"},
    3: {"challenge_id": "cell_faces", "answer_type": "D", "kernel": "incidence_chains"},
    4: {"challenge_id": "cell_orientation", "answer_type": "D", "kernel": "incidence_chains"},
    5: {"challenge_id": "distance_form", "answer_type": "M", "kernel": "root_enclosures"},
    6: {"challenge_id": "conservative_embedding", "answer_type": "M", "kernel": "replay"},
    7: {"challenge_id": "cycle_words", "answer_type": "M", "kernel": "relation_tables"},
    8: {"challenge_id": "flow_certificate", "answer_type": "M", "kernel": "rational_tables"},
    9: {"challenge_id": "carried_reversal", "answer_type": "M", "kernel": "replay"},
    10: {"challenge_id": "scope_fence", "answer_type": "M", "kernel": "root_enclosures"},
    11: {"challenge_id": "positioned_join", "answer_type": "M", "kernel": "replay"},
    13: {"challenge_id": "route_replay", "answer_type": "M", "kernel": "replay"},
    14: {"challenge_id": "bounded_mask", "answer_type": "M", "kernel": "replay"},
    15: {"challenge_id": "host_bound_verdict", "answer_type": "M", "kernel": "replay"},
    16: {"challenge_id": "stage_chain", "answer_type": "M", "kernel": "replay"},
    17: {"challenge_id": "tagged_digest", "answer_type": "M", "kernel": "replay"},
    18: {"challenge_id": "three_way_split", "answer_type": "M", "kernel": "incidence_chains"},
    19: {"challenge_id": "table_polynomial", "answer_type": "M", "kernel": "root_enclosures"},
    21: {"challenge_id": "loop_products", "answer_type": "M", "kernel": "link_transport"},
    22: {"challenge_id": "reindexed_fibres", "answer_type": "M", "kernel": "relation_tables"},
    23: {"challenge_id": "glued_patches", "answer_type": "D", "kernel": "relation_tables"},
    24: {"challenge_id": "recomputed_labels", "answer_type": "M", "kernel": "relation_tables"},
    25: {"challenge_id": "formal_inverses", "answer_type": "D", "kernel": "relation_tables"},
    26: {"challenge_id": "coloured_slots", "answer_type": "M", "kernel": "relation_tables"},
    27: {"challenge_id": "associator_tables", "answer_type": "M", "kernel": "relation_tables"},
    28: {"challenge_id": "both_round_trips", "answer_type": "M", "kernel": "rational_tables"},
    29: {"challenge_id": "boundary_chain", "answer_type": "M", "kernel": "replay"},
    30: {"challenge_id": "filtered_pages", "answer_type": "M", "kernel": "incidence_chains"},
    31: {"challenge_id": "class_operations", "answer_type": "M", "kernel": "incidence_chains"},
    32: {"challenge_id": "observed_blocks", "answer_type": "M", "kernel": "replay"},
    33: {"challenge_id": "scale_steps", "answer_type": "M", "kernel": "rational_tables"},
    34: {"challenge_id": "weight_slopes", "answer_type": "M", "kernel": "rational_tables"},
    35: {"challenge_id": "step_weights", "answer_type": "M", "kernel": "rational_tables"},
    36: {"challenge_id": "weighted_update", "answer_type": "M", "kernel": "rational_tables"},
    37: {"challenge_id": "forced_differences", "answer_type": "M", "kernel": "finite_models"},
    38: {"challenge_id": "same_background", "answer_type": "M", "kernel": "finite_models"},
    39: {"challenge_id": "joint_payoffs", "answer_type": "M", "kernel": "finite_games"},
    40: {"challenge_id": "stable_profiles", "answer_type": "M", "kernel": "finite_games"},
    41: {"challenge_id": "use_once_terms", "answer_type": "M", "kernel": "relation_tables"},
    42: {"challenge_id": "dual_endpoints", "answer_type": "M", "kernel": "finite_automata"},
    43: {"challenge_id": "granted_steps", "answer_type": "M", "kernel": "replay"},
    44: {"challenge_id": "witnessed_triples", "answer_type": "M", "kernel": "bounded_triples"},
    45: {"challenge_id": "bound_axioms", "answer_type": "M", "kernel": "proof_tables"},
    46: {"challenge_id": "confirmed_runs", "answer_type": "M", "kernel": "proof_tables"},
    47: {"challenge_id": "mirror_pairs", "answer_type": "M", "kernel": "pair_arithmetic"},
    48: {"challenge_id": "unit_rows", "answer_type": "M", "kernel": "pair_arithmetic"},
    49: {"challenge_id": "named_frames", "answer_type": "M", "kernel": "pair_arithmetic"},
    50: {"challenge_id": "square_one", "answer_type": "M", "kernel": "pair_arithmetic"},
    51: {"challenge_id": "split_weights", "answer_type": "M", "kernel": "pair_arithmetic"},
    52: {"challenge_id": "ordered_splits", "answer_type": "M", "kernel": "pair_arithmetic"},
    53: {"challenge_id": "paired_frames", "answer_type": "M", "kernel": "pair_arithmetic"},
    54: {"challenge_id": "joint_rank", "answer_type": "M", "kernel": "pair_arithmetic"},
    55: {"challenge_id": "far_blind", "answer_type": "M", "kernel": "pair_arithmetic"},
    56: {"challenge_id": "side_reduction", "answer_type": "M", "kernel": "pair_arithmetic"},
    57: {"challenge_id": "size_keeping", "answer_type": "M", "kernel": "pair_arithmetic"},
    58: {"challenge_id": "overlap_choices", "answer_type": "M", "kernel": "finite_labels"},
    59: {"challenge_id": "two_party_bound", "answer_type": "M", "kernel": "rational_tables"},
    60: {"challenge_id": "commuting_checks", "answer_type": "M", "kernel": "parity_words"},
    61: {"challenge_id": "walk_transport", "answer_type": "M", "kernel": "link_transport"},
    62: {"challenge_id": "face_products", "answer_type": "M", "kernel": "link_transport"},
    63: {"challenge_id": "hinge_deficits", "answer_type": "M", "kernel": "root_enclosures"},
    64: {"challenge_id": "closed_faces", "answer_type": "M", "kernel": "link_transport"},
    65: {"challenge_id": "step_squares", "answer_type": "D", "kernel": "step_systems"},
    66: {"challenge_id": "signed_totals", "answer_type": "M", "kernel": "rational_tables"},
    67: {"challenge_id": "answer_keeping", "answer_type": "M", "kernel": "answer_maps"},
    68: {"challenge_id": "outward_bounds", "answer_type": "M", "kernel": "root_enclosures"},
    69: {"challenge_id": "isolated_roots", "answer_type": "M", "kernel": "root_enclosures"},
    70: {"challenge_id": "table_roots", "answer_type": "M", "kernel": "rational_tables"},
    71: {"challenge_id": "rated_limits", "answer_type": "M", "kernel": "root_enclosures"},
    72: {"challenge_id": "rim_cochains", "answer_type": "M", "kernel": "incidence_chains"},
    73: {"challenge_id": "refined_sums", "answer_type": "M", "kernel": "root_enclosures"},
    74: {"challenge_id": "typed_queries", "answer_type": "M", "kernel": "relation_tables"},
    75: {"challenge_id": "patched_views", "answer_type": "M", "kernel": "relation_tables"},
    76: {"challenge_id": "signed_cells", "answer_type": "M", "kernel": "incidence_chains"},
    77: {"challenge_id": "serial_receipts", "answer_type": "M", "kernel": "proof_tables"},
    78: {"challenge_id": "ordered_log", "answer_type": "M", "kernel": "relation_tables"},
    79: {"challenge_id": "merge_tables", "answer_type": "D", "kernel": "relation_tables"},
    80: {"challenge_id": "exact_grants", "answer_type": "D", "kernel": "relation_tables"},
    81: {"challenge_id": "budgeted_releases", "answer_type": "M", "kernel": "rational_tables"},
    82: {"challenge_id": "signed_chains", "answer_type": "M", "kernel": "proof_tables"},
    83: {"challenge_id": "lineage_pins", "answer_type": "M", "kernel": "proof_tables"},
    84: {"challenge_id": "rerun_calls", "answer_type": "M", "kernel": "proof_tables"},
    85: {"challenge_id": "narrowing_handoffs", "answer_type": "M", "kernel": "relation_tables"},
    86: {"challenge_id": "grounded_traces", "answer_type": "M", "kernel": "relation_tables"},
    87: {"challenge_id": "mutant_challenges", "answer_type": "M", "kernel": "relation_tables"},
    88: {"challenge_id": "limited_runs", "answer_type": "M", "kernel": "step_systems"},
    89: {"challenge_id": "composed_errors", "answer_type": "M", "kernel": "rational_tables"},
    90: {"challenge_id": "covered_clauses", "answer_type": "M", "kernel": "proof_tables"},
    91: {"challenge_id": "renamed_formulas", "answer_type": "M", "kernel": "finite_models"},
    92: {"challenge_id": "resolution_claims", "answer_type": "M", "kernel": "proof_tables"},
    93: {"challenge_id": "compiled_branches", "answer_type": "M", "kernel": "step_systems"},
    94: {"challenge_id": "wired_handshakes", "answer_type": "M", "kernel": "relation_tables"},
    95: {"challenge_id": "counted_runs", "answer_type": "M", "kernel": "step_systems"},
    96: {"challenge_id": "counted_trials", "answer_type": "M", "kernel": "rational_tables"},
    97: {"challenge_id": "killed_mutants", "answer_type": "M", "kernel": "relation_tables"},
    98: {"challenge_id": "differential_pairs", "answer_type": "M", "kernel": "rational_tables"},
    99: {"challenge_id": "seeded_shrinks", "answer_type": "M", "kernel": "step_systems"},
    100: {"challenge_id": "scoped_release", "answer_type": "M", "kernel": "relation_tables"},
}

# Research-tree replays (the author's ruling of 2026-09-25): a second record
# at a level, under the replayed-evidence key, whose witness a 19L57G1
# research tree holds, read through the vendored clone.  A level's first
# record is tagged ``L``; its research-tree replay ``T``.  Only a level whose
# first record is the harness's may carry one, so the two never share a key.
TREE_REPLAYS: dict[int, dict[str, object]] = {
    23: {"challenge_id": "observer_glue", "answer_type": "M", "kernel": "replay",
         "trees": ["g014_observer_descent"]},
    58: {"challenge_id": "shared_labels", "answer_type": "M", "kernel": "replay",
         "trees": ["natural_sections"]},
    59: {"challenge_id": "row_margin", "answer_type": "M", "kernel": "replay",
         "trees": ["p208b_contextuality_nonlocality"]},
    60: {"challenge_id": "site_checks", "answer_type": "M", "kernel": "replay",
         "trees": ["p209c_stabilizer_codes"]},
    61: {"challenge_id": "walk_relabels", "answer_type": "M", "kernel": "replay",
         "trees": ["convention_price", "sign_slice"]},
    62: {"challenge_id": "face_walk_products", "answer_type": "M", "kernel": "replay",
         "trees": ["natural_sections"]},
    65: {"challenge_id": "register_squares", "answer_type": "M", "kernel": "replay",
         "trees": ["native_bridge"]},
    66: {"challenge_id": "pairing_certificates", "answer_type": "M", "kernel": "replay",
         "trees": ["fresh_characters", "natural_sections"]},
    72: {"challenge_id": "chord_square_rim", "answer_type": "M", "kernel": "replay",
         "trees": ["natural_sections"]},
}


def record_tag(level: int, tree: bool = False) -> str:
    return f"{'T' if tree else 'L'}{level:03d}"


def records() -> list[tuple[str, int, dict[str, object]]]:
    """(tag, level, meta) of every record the engine binds, in level order."""
    clash = sorted(lv for lv in TREE_REPLAYS if lv in LEVELS and LEVELS[lv]["kernel"] == "replay")
    if clash:
        raise ValueError(f"levels {clash} already replay under the replayed-evidence key")
    out = [(record_tag(lv), lv, meta) for lv, meta in LEVELS.items()]
    out += [(record_tag(lv, True), lv, meta) for lv, meta in TREE_REPLAYS.items()]
    return sorted(out, key=lambda r: (r[1], r[0]))


ROLE_TO_TARGET = {
    "positive": "pos",
    "own_negative": "own-neg",
    "near_miss": "near-miss",
    "mutation": "mut",
    "extra": "extra",
}


def table_bytes(ports: LevelEngineOperationPorts) -> tuple[str, str, bytes]:
    """Read the authenticated installed table, retaining its historical identity."""
    pins = load_path(current_context().governance_path("PINS.json"))
    assert isinstance(pins, dict)
    reference = pins["read_only_references"]["the_symbol_game"]
    table = ports.stage_table_bytes()
    active = ports.registry("stage_registry", "v2")["table"]
    if "sha256:" + hashlib.sha256(table).hexdigest() != active["sha256"] or reference["commit"] != active["pin_commit"]:
        raise ValueError("STAGE_TABLE_PIN_MISMATCH")
    return str(reference["commit"]), str(reference["table_path"]), table


def row_digest(table: bytes, level: int) -> str:
    for line in table.split(b"\n"):
        if line.split(b"|", 1)[0] == str(level).encode("ascii"):
            return "sha256:" + hashlib.sha256(line.rstrip(b"\r")).hexdigest()
    raise KeyError(level)


def fixture_roles(challenge_id: str) -> dict[str, str]:
    """Target roles by fixture id.  A replay level states its fixtures as
    packets (its positive is computed from sealed evidence), so they are read
    from the spec; any other level's from its instance file."""
    d = ROOT / "payload" / challenge_id
    packets = getattr(load_spec(challenge_id), "packets", None)
    rows: list[tuple[str, str]]
    if packets is not None:
        rows = [(str(fid), str(role)) for fid, role, _, _ in packets()]
    else:
        inst = load_path(d / "instance.json")
        assert isinstance(inst, dict) and isinstance(inst["fixtures"], list)
        m = load_path(d / "mutation.json")
        assert isinstance(m, dict)
        rows = [(str(f["id"]), str(f["role"])) for f in inst["fixtures"]] + [(str(m["id"]), "mutation")]
    out: dict[str, str] = {}
    near = 0
    for fid, role in rows:
        tag = ROLE_TO_TARGET[role]
        if role == "near_miss":
            near += 1
            tag = f"near-miss-{near}"
        elif role == "extra":
            tag = f"extra-{fid}"
        elif role == "mutation":
            tag = "mut-1"
        out[fid] = tag
    return out


def binding(level: int, commit: str, path: str, table: bytes, tree: bool = False, *,
            ports: LevelEngineOperationPorts) -> dict[str, object]:
    meta = TREE_REPLAYS[level] if tree else LEVELS[level]
    custody = {"custody": "research_tree", "trees": meta["trees"]} if tree else {}
    return {
        **custody,
        "answer_type": meta["answer_type"],
        "authority_effect": "None",
        "challenge_id": meta["challenge_id"],
        "fixture_roles": fixture_roles(str(meta["challenge_id"])),
        "kernel": meta["kernel"],
        "level": level,
        "row": {
            "commit": commit,
            "row_definition": "bytes of the line whose first field is the level, without its line ending",
            "row_sha256": row_digest(table, level),
            "table_path": path,
            "table_sha256": "sha256:" + hashlib.sha256(table).hexdigest(),
        },
        "schema": "level-engine.binding.v2",
        "target": target(level, ports),
    }


def target(level: int, ports: LevelEngineOperationPorts) -> dict[str, object]:
    checkers = ports.registry("checkers", "v2")["checkers"]
    found = sorted(cid for cid, value in checkers.items() if value.get("level") == level)
    if not found:
        return {"checker": None, "status": "NEEDS_TARGET_CHECKER"}
    value = checkers[found[0]]
    ports.checker(level)
    if "sha256:" + ports.checker_entry(level)["sha256"] != value["sha256"]:
        raise ValueError("CHECKER_REGISTRY_DIGEST_MISMATCH")
    return {"checker": {key: value[key] for key in ("commit", "id", "path", "sha256")},
            "status": "CHECKER_OF_RECORD", "registry_version": 2}


def main(argv: list[str] | None = None, ports: LevelEngineOperationPorts | None = None) -> int:
    if ports is None:
        raise ValueError("LEVEL_ENGINE_PORTS_REQUIRED")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    commit, path, table = table_bytes(ports)
    bad = 0
    for tag, level, _ in records():
        want = dumps(binding(level, commit, path, table, tag.startswith("T"), ports=ports))
        dest = current_context().current_path(f"bindings/{tag}.json")
        if args.check:
            if not dest.exists() or dest.read_bytes() != want:
                print(f"BINDING DRIFT (ROW_DIGEST): {str(dest)}")
                bad += 1
        else:
            write_bytes(dest, want)
    if args.check and not bad:
        print("BINDINGS OK: row digests recompute at the pinned commit")
    return 1 if bad else 0

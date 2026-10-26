"""Emit byte-bound original semantic residuals from the closed recovery receipts."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

PAPER = Path(__file__).absolute().parents[1]
ROOT = PAPER / "docs/aggregate_recreated_run/original_recovery_v1"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def closed(path):
    raw = path.read_bytes()
    value = json.loads(raw)
    identity = value.pop("self_sha256")
    if sha(canonical(value)) != identity or value["custody_closed"] is not True:
        raise ValueError("CLOSED_BOUND_RECEIPT_REQUIRED")
    return value, identity, sha(raw)


def span(relative, line, end):
    path = ROOT / relative
    raw = path.read_bytes()
    fragment = b"".join(raw.splitlines(keepends=True)[line - 1:end])
    return {"path": path.relative_to(PAPER).as_posix(), "sha256": sha(raw), "start_line": line, "end_line": end, "raw_span_sha256": sha(fragment), "raw_span_hex": fragment.hex()}


def main():
    first, first_self, first_raw = closed(ROOT / "final_v4/receipt.json")
    final, final_self, final_raw = closed(ROOT / "progression_v1/receipt.json")
    if final["baseline_self_sha256"] != first_self or final["baseline_raw_sha256"] != first_raw:
        raise ValueError("RECEIPT_JOIN_MISMATCH")
    source = "final_v4/source_files/research/mssn_sn_tower/demos/demo_2/run_demo2.py"
    bouts = [
        {"id": "R1_TFI", "status": "RESTRICTED_SIGN_GAUGE_SOURCE_RECREATED", "source_spans": [span(source, 250, 260), span(source, 274, 395)], "missing_for_native_physics": ["Host-licensed Hamiltonian/basis/ensemble/representation-to-cochain adapter and its preservation proof", "Native Phi/Gamma request and replayable receipt bound to that physical adapter"], "next_retrieval": "The exact source gate is available at Git commit 6f649c611c2b751db4abf4cba541bf2403575590:research/mssn_sn_tower/demos/demo_2/run_demo2.py. Restricted gauge succeeds; it deliberately leaves bqnf_phi1_zero null."},
        {"id": "R2_FREE_FERMION", "status": "ORIGINAL_RAW_BATCH_REPLAYED_WITNESS_UNCHECKED", "source_spans": [span(source, 491, 557)], "missing_for_native_physics": ["Original fermionic ensemble/filling/chemical-potential convention and selected representation", "Complete host-pinned signed paths and exact weights or a checked determinant/Pfaffian representation", "Path-index involution plus observable numerator rows if Xi is the chosen route", "Native functional adapter and bound replayable receipt"], "carrier_fidelity": "The source declares only 0↔1,1↔2,2↔3. The earlier ring fixture's extra 0↔3 edge changes this task.", "next_retrieval": "Recovered commit trace demo2_r2_freefermion_1790207175.jsonl contains the full seven-move raw batch. Its Xi is prose about a sublattice swap; it does not contain a path table or determinant certificate. The 1790207127 file is empty."},
        {"id": "R3_ATTRACTIVE_HUBBARD", "status": "RAW_HISTORICAL_BOUTS_RETAINED_NO_LICENSED_PHYSICAL_PACKET", "source_spans": [span(source, 746, 797), span(source, 873, 899)], "missing_for_native_physics": ["Original ensemble/filling and chemical potentials; beta/time discretization if a finite path route is intended", "Actual determinant/auxiliary-field or signed-path representation and witness", "Hamiltonian-to-native-packet preservation obligations and request/certificate bytes"], "next_retrieval": "The recovered 1790207676 and 1790207968 raw traces retain responses and the original six terms. The latter particle-hole prose supplies no exact signed path map. Retrieve the host's actual simulation/configuration carrier and witness rather than assuming the separately supplied mu=0 determinant fixture."},
        {"id": "R4_REPULSIVE_HUBBARD", "status": "RAW_HISTORICAL_BOUT_RETAINED_NO_CHECKED_OBSTRUCTION", "source_spans": [span(source, 971, 1005), span(source, 1067, 1090)], "missing_for_native_physics": ["Original ensemble/filling, chemical-potential convention and selected representation", "Specific admitted transform catalog and route-specific obstruction certificate", "Physical adapter/native request and verification receipt"], "next_retrieval": "The recovered 1790207568 raw trace contains six assertions and an OPEN_SIGN_OBSTRUCTION claim. Class-name hardness and witness refusal do not prove obstruction of this two-site task. Retrieve a concrete carrier/certificate from the original host, if it ever existed."},
        {"id": "R5_TRIANGULAR_HUBBARD", "status": "THREE_RAW_MODEL_TRACE_FILES_RETAINED_NO_ORIGINAL_NATIVE_PACKET", "source_spans": [span(source, 1156, 1193), span(source, 1254, 1274)], "missing_for_native_physics": ["Original ensemble, beta, chemical potential and finite representation", "Signed paths with exact weights or another licensed representation-specific witness", "Physical preservation obligations, native request and replayable certificate"], "next_retrieval": "Recovered qwen, ChatGPT and DeepSeek traces retain literal C3 t=1 U=2 inputs and proposed witnesses. They do not specify beta=1/4 or mu=0. The prior exact_fock_gap computation remains a separate explicitly declared finite fixture; its additional parameters cannot be retroactively attributed to these bouts."},
    ]
    loop_evidence = [span("progression_v1/original_symbol_game_runner.py", 187, 191), span("progression_v1/original_symbol_game_runner.py", 250, 278), span("progression_v1/original_symbol_game_runner.py", 342, 367), span("progression_v1/original_symbol_game_runner.py", 405, 410)]
    # Keep every original source term dictionary without evaluating provider code.
    source_raw = (ROOT / source).read_bytes()
    terms = {}
    for node in ast.parse(source_raw).body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id in {"R3_HAMILTONIAN_TERMS", "R4_HAMILTONIAN_TERMS", "R5_HAMILTONIAN_TERMS"}:
            terms[node.targets[0].id] = ast.literal_eval(node.value)
    joins = first["dialogue_audit"]["joins"]
    report = {"schema": "paper011.original-semantic-obligations.v1", "source_recovery_self_sha256": first_self, "source_recovery_raw_sha256": first_raw, "original_progression_self_sha256": final_self, "original_progression_raw_sha256": final_raw, "named_physics_bouts": bouts, "original_hubbard_terms": terms, "original_R2_hopping": first["original_R2_hopping"], "eight_beat_source_evidence": loop_evidence, "dialogue_outcomes": {"rounds": len(joins), "roles": 120, "all_original_template_comparisons_match": all(row["text_equal"] for row in final["all_role_comparisons"]), "task_alias_labeled_packet_id": sum(row["audit_id_is_task_alias"] for row in joins), "nonzero_AST_false_exact_action": sum(row["exact_action_with_nonzero_displayed_obstruction"] for row in joins), "wrong_emitted_child_instruction": sum(row["child_instruction_matches"] is False for row in joins), "instruction_without_emitted_child": sum(row["child_instruction_without_emitted_child"] for row in joins), "native_measurements_verified": 0}, "remaining_eight_beat_native_obligations": ["The original historical sources synthesize scores and hash task/count/final-Phi text; they retain no native matrices or certificate. Source/template recreation is complete, but native mathematical recreation cannot be established from this mechanism.", "A faithful new native adaptation would require separately licensed actual AST/module or specimen carrier state, exact d0/d1/residual, source interpretation and callback composition, then independently bound evaluation/verification. Do not substitute those new inputs into the historical sessions.", "Original source generator provenance is recoverable from the commit introducing the traces; original source-event digests in all fifteen packet rows remain null. Exact source consistency does not establish historical live-call authentication."], "authority_effect": "None"}
    report["self_sha256"] = sha(canonical(report))
    (ROOT / "original_semantic_obligations.json").write_bytes(canonical(report) + b"\n")
    print(json.dumps({"self_sha256": report["self_sha256"], "dialogue_outcomes": report["dialogue_outcomes"]}))


if __name__ == "__main__":
    main()

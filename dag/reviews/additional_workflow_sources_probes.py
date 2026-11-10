"""Offline audit reproductions on synthetic fixtures; no legacy module imports.

The selected AST definitions are compiled unchanged with future annotations.
This avoids the legacy miner's import-time reads of a sibling repository.
These are reproductions of acceptance gaps, not production regression fixes.
"""
from __future__ import annotations

import ast
import copy
import json
import time
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LEGACY = ROOT / "workflows/wf20_derivation_loop_with_lift_grants/pilots/finite_qm_derivation_pfp"


def extract(relative, names, namespace):
    path = (LEGACY / relative).resolve()
    raw = path.read_bytes()
    tree = ast.parse(raw.decode("utf-8-sig"))
    chosen = [node for node in tree.body if getattr(node, "name", None) in names]
    assert {node.name for node in chosen} == set(names)
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *chosen], type_ignores=[])
    ast.fix_missing_locations(module)
    exec(compile(module, str(path), "exec"), namespace)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(raw).hexdigest(),
            "extracted_definitions": [{"name": n.name, "lines": [n.lineno, n.end_lineno]} for n in chosen]}


def main():
    namespace = dict(globals(), DEFAULT_DAG_PATH=Path("SYNTHETIC_UNUSED"), DEFAULT_OPERADS_PATH=Path("SYNTHETIC_UNUSED"))
    sources = [extract("gates/gate_engine.py", ["FiniteQmGateReceipt", "_is_exact_int", "verify_dag_prompt_node_reply", "verify_dag_work_unit_reply"], namespace)]
    expected = dict(derived_under_policy="SPK-001", authority_effect="None", firewall_status="HONEST",
        node_id="SYNTHETIC_NODE", stage="SYNTHETIC_STAGE", dag_status="UNPROVED", operad_family_id="SYNTHETIC_FAMILY",
        p_star_tree_potentials=[0, 1, 2], p_star_chord_potential=1, p_star_holonomy_gamma2=1,
        cochain_d1_d0_exact_zero=True, finite_shadow_witness_int=7, countermodel_witness_int=9,
        unpaid_import_count=0, unconditional_promotion_refused=True,
        lean4_theorem_anchor="synthetic.not_checked", rust_witness_anchor="synthetic_not_checked", should_continue=False)
    check = namespace["verify_dag_prompt_node_reply"]
    assert check(expected, expected).all_gates_passed
    unchecked = {}
    for field in ("node_id", "stage", "dag_status", "operad_family_id", "firewall_status", "should_continue"):
        candidate = copy.deepcopy(expected)
        candidate[field] = {"arbitrary_nested_value": "UNVALIDATED"}
        receipt = check(expected, candidate)
        unchecked[field] = receipt.all_gates_passed
        assert receipt.all_gates_passed
    alias = copy.deepcopy(expected)
    alias.update(p_star_tree_potentials=[False, True, 2], p_star_chord_potential=True,
                 p_star_holonomy_gamma2=True, unpaid_import_count=False)
    assert check(expected, alias).all_gates_passed
    wrong = copy.deepcopy(expected)
    wrong["finite_shadow_witness_int"] = -999
    failure = check(expected, wrong)
    assert not failure.all_gates_passed
    assert any("exp=7" in x for x in failure.failures)

    sources.append(extract("operad_mining/miner.py", ["MinedOperadCompositionRule", "MinedDerivationWorkUnit", "FiniteQmOperadMiner"], namespace))
    miner = namespace["FiniteQmOperadMiner"].__new__(namespace["FiniteQmOperadMiner"])
    miner.operads_data = {"operad_families": [{"id": "EMPTY", "routes": []}, {"id": "THREE", "routes": ["a", "b", "c"]}]}
    rules = miner.mine_all_operad_rules()
    arities = [{"id": r.operad_id, "arity": r.arity, "input_color_count": len(r.source_colours)} for r in rules]
    assert all(x["arity"] != x["input_color_count"] for x in arities)
    miner.dag_data = {"nodes": [{"id": "PUBLIC_SYNTHETIC_NODE", "statement": "A synthetic statement."}],
                      "routes": [{"id": "PUBLIC_SYNTHETIC_UNRELATED_ROUTE", "nodes": ["OTHER_NODE"]}]}
    unit = miner.generate_derivation_work_units(1)[0]
    assert unit.status == "PROVED_LEAN"
    miner.dag_data["nodes"][0]["statement"] = "A contradictory synthetic statement."
    changed = miner.generate_derivation_work_units(1)[0]
    assert changed.witness_invariant_int == unit.witness_invariant_int
    sources.append(extract("prompts/prompt_compiler.py", ["CompiledFiniteQmPrompt", "dag_work_unit_json_schema", "compile_dag_work_unit_prompt", "compile_coupled_slice_prompt"], namespace))
    compiled = namespace["compile_dag_work_unit_prompt"](unit)
    assert f"= {unit.witness_invariant_int}" in compiled.user_prompt
    copied = namespace["verify_dag_work_unit_reply"](compiled.expected_ground_truth, unit.to_expected_ground_truth())
    assert copied.all_gates_passed
    sources.append(extract("../derivation_dag_pfp_staged_benchmark.py", ["CarrierDerivationProjection"], namespace))
    projection = namespace["CarrierDerivationProjection"].__new__(namespace["CarrierDerivationProjection"])
    object.__setattr__(projection, "expected_certificate", {})
    try:
        namespace["compile_coupled_slice_prompt"](projection)
    except TypeError as exc:
        coupled_error = str(exc)
    else:
        raise AssertionError("Expected the declared dictionary/callable contract mismatch")
    result = {"scope": "Selected exact source definitions, synthetic public fixtures, no complete legacy import or provider call.",
        "sources": sources, "baseline_18_field_gate_passed": True,
        "arbitrary_nested_values_accepted": unchecked,
        "bool_integer_aliases_accepted": True,
        "wrong_witness_rejected_with_expected_value_in_feedback": list(failure.failures),
        "nominal_arity_mismatches": arities,
        "missing_node_status_defaults_to": unit.status,
        "unrelated_route_pairing_accepted_by_generator": True,
        "numeric_witness_unchanged_after_statement_replacement": True,
        "compiled_prompt_contains_precomputed_numeric_answer": True,
        "copied_expected_work_unit_accepted": copied.all_gates_passed,
        "coupled_compiler_declared_dictionary_field_called_as_function": coupled_error}
    output = Path(__file__).with_name("additional_workflow_sources_probe_results.json")
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

"""Public synthetic schema/runtime boundary probes; no provider or benchmark input."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from pfp_lab.core.contracts import PACK_IDS, CutIn, ScenarioIn, admit_json, get_pack
from pfp_lab.core.session import ReceiptOut, build_receipt, receipt_digest, run_scenario, verify_receipt

ROOT = Path(__file__).resolve().parents[2]


def main():
    schema = json.loads((ROOT / 'contracts/schema/scenario.v1.schema.json').read_text())
    receipt_schema = json.loads((ROOT / 'contracts/schema/receipt.v1.schema.json').read_text())
    validator = Draft202012Validator(schema)
    receipt_validator = Draft202012Validator(receipt_schema)
    cases = []
    base = {'schema': 'pfp-lab.scenario.v1', 'vertices': ['a', 'b'],
            'edges': [{'source': 'a', 'target': 'b', 'weight': 1}], 'moves': []}
    variants = {'valid_carrier': base,
                'negative_weight': {**base, 'edges': [{'source': 'a', 'target': 'b', 'weight': -1}]},
                'duplicate_vertices': {**base, 'vertices': ['a', 'a', 'b']},
                'unknown_endpoint': {**base, 'edges': [{'source': 'a', 'target': 'z'}]},
                'invalid_rational': {**base, 'moves': [{'move': 'ASSERT', 'source': 'a', 'target': 'b', 'value': 'not a rational'}]},
                'unknown_field': {**base, 'unrecognized': 1}}
    for name, value in variants.items():
        try:
            admit_json(ScenarioIn, json.dumps(value))
            accepted = True
        except ValueError:
            accepted = False
        cases.append({'name': name, 'json_schema_accepts': validator.is_valid(value),
                      'runtime_admission_accepts': accepted})
    scenario = admit_json(ScenarioIn, json.dumps(base))
    receipt = build_receipt(run_scenario(scenario))
    changed = copy.deepcopy(receipt.model_dump(mode='json', by_alias=True))
    changed['final']['section']['a'] = '999'
    candidate = admit_json(ReceiptOut, json.dumps(changed))
    candidate = candidate.model_copy(update={'digest': receipt_digest(candidate)})
    cases.append({'name': 'resealed_invented_final_state',
                  'json_schema_accepts': receipt_validator.is_valid(changed),
                  'runtime_model_accepts': True, 'replay_accepts': verify_receipt(candidate).valid})
    versioned = receipt.model_copy(update={'core_version': 'invented-version'})
    versioned = versioned.model_copy(update={'digest': receipt_digest(versioned)})
    cases.append({'name': 'resealed_invented_core_version', 'replay_accepts': verify_receipt(versioned).valid,
                  'interpretation': 'Replay establishes agreement with the current implementation, not authenticity of the claimed historic version.'})
    selected = next((name, move) for name in PACK_IDS for move in get_pack(name).moves
                    if isinstance(move, CutIn) and move.section)
    pack_id, move = selected
    key = next(iter(move.section))
    old = move.section[key]
    try:
        move.section[key] = 'unvalidated mutation'
        repeated = get_pack(pack_id)
        leaked = any(isinstance(m, CutIn) and m.section and m.section.get(key) == 'unvalidated mutation'
                     for m in repeated.moves)
        cases.append({'name': 'cached_frozen_pack_nested_mutation', 'pack_id': pack_id,
                      'nested_dictionary_write_succeeded': True, 'next_get_pack_exposes_mutation': leaked,
                      'interpretation': 'Pydantic frozen is shallow for a dict; cached pack state can be changed through the public returned object in this process.'})
    finally:
        move.section[key] = old
    expected = [(True, True), (True, False), (True, False), (True, False), (True, False), (False, False)]
    assert [(r['json_schema_accepts'], r['runtime_admission_accepts']) for r in cases[:6]] == expected
    assert cases[6]['replay_accepts'] is False
    assert cases[7]['replay_accepts'] is True
    assert cases[8]['next_get_pack_exposes_mutation'] is True
    result = {'status': 'nine_bounded_observations_reproduced', 'cases': cases,
              'scope': 'Synthetic public cases only. Cached mutation restored before exit. No source edits, provider calls, private benchmark access or full-suite claim.'}
    (ROOT / 'dag/reviews/additional_contracts_and_packaging_probe.json').write_text(
        json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'observations': len(cases)}))


if __name__ == '__main__':
    main()

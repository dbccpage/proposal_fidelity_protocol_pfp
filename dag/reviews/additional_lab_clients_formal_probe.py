"""Offline bounded counterexamples and custody checks; never invokes a provider."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pfp_lab.core.contracts import ScenarioIn, admit_json
from pfp_lab.core.session import build_receipt, run_scenario, verify_receipt

scenario = {'schema':'pfp-lab.scenario.v1','vertices':['a','b'],
            'edges':[{'source':'a','target':'b','weight':1000}],
            'moves':[{'move':'ASSERT','source':'a','target':'b','value':'9'*64}]}
receipt = build_receipt(run_scenario(admit_json(ScenarioIn,json.dumps(scenario))))
outdir = ROOT / 'dag/reviews/additional_lab_clients_formal_probe'
outdir.mkdir(exist_ok=True)
(outdir/'receipt.json').write_text(receipt.model_dump_json(by_alias=True),encoding='utf-8')
checks = {'scenario_admitted':True,'input_rational_chars':64,
          'output_defect_chars':len(receipt.final.defect),
          'output_defect':receipt.final.defect,
          'python_receipt_replays':verify_receipt(receipt).valid,
          'old_oracle_path_exists':(ROOT/'papers/005_pfp_practitioners_field_manual/code/l1_symbol_game_governor.py').is_file(),
          'relocated_oracle_path_exists':(ROOT/'papers/pfp/005_pfp_practitioners_field_manual/code/l1_symbol_game_governor.py').is_file()}
inventory=json.loads((ROOT/'dag/file_inventory.json').read_text(encoding='utf-8'))['files']
checks['score_source_hash_mismatches']=[]
checks['score_current_evidence_hash_mismatches']=[]
checks['score_files_checked']=0
for row in inventory:
    path=row['path']
    if not path.startswith(('csharp/','pfp_lab/')) or not path.endswith('.contract.score.json'): continue
    checks['score_files_checked']+=1
    data=json.loads((ROOT/path).read_text(encoding='utf-8'))
    target=data['contract']['artifact']
    actual=hashlib.sha256((ROOT/target['path']).read_bytes()).hexdigest()
    if actual!=target['sha256']:
        checks['score_source_hash_mismatches'].append({'score':path,'source':target['path'],'recorded':target['sha256'],'actual':actual})
    evidence=list(data['score']['evidence'])
    if data['score'].get('mutation_accounting'): evidence.append(data['score']['mutation_accounting']['report'])
    for item in evidence:
        p=ROOT/item['path']
        actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
        if actual!=item['sha256']:
            checks['score_current_evidence_hash_mismatches'].append({'score':path,'evidence':item['path'],'recorded':item['sha256'],'actual':actual})
checks['lean_provenance_hashes_match']=all(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256'] for r in json.loads((ROOT/'lean4/provenance.json').read_text())['files'])
from pfp_lab.tests.test_boundaries import FORBIDDEN, NEW_TREES
checks['naming_policy_hits']=[]
for root in NEW_TREES:
    for p in (ROOT/root).rglob('*'):
        if p.is_file() and not {'bin','obj','__pycache__','node_modules','.vs'}.intersection(p.parts):
            if FORBIDDEN.search(p.read_text(encoding='utf-8',errors='replace')) or FORBIDDEN.search(p.name):
                checks['naming_policy_hits'].append(p.relative_to(ROOT).as_posix())
dest=ROOT/'dag/reviews/additional_lab_clients_formal_probe.json'
dest.write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
print(json.dumps(checks,indent=2))

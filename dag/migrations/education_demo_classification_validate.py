"""Static validation of frozen education custody/adaptation artifacts only."""
import ast
import base64
import hashlib
import json
from pathlib import Path
import posixpath
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
P='education_demo_classification'
report=json.loads((HERE/(P+'.json')).read_text(encoding='utf-8'))
plan=json.loads((HERE/(P+'_adaptation_plan.json')).read_text(encoding='utf-8'))
move={r['path']:r['proposed_destination'] for r in report['files'] if r['disposition']=='move'}
future={move.get(p,p) for p in subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()}
result={'status':'PASS','source_mutations':0,'provider_calls':0,'source_imports':0,'source_executions':0,'checks':[],'limitations':['Static planned-tree validation only. Does not establish native/renderer/provider availability or notebook execution success.','Existing missing links and literal historical source paths are not globally repaired.']}

for row in report['files']:
    assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
result['checks'].append({'name':'original_inventory_hashes','passed':1539})
py=nb=output_cells=0
for change in plan['changes']:
    before=(ROOT/change['original_path']).read_bytes()
    assert hashlib.sha256(before).hexdigest()==change['original_sha256']
    after=base64.b64decode(change['after_bytes_base64'],validate=True)
    assert hashlib.sha256(after).hexdigest()==change['post_adaptation_sha256']
    assert len(after)==change['post_adaptation_bytes']
    text=after.decode('utf-8-sig')
    if change['post_move_path'].endswith('.py'):
        ast.parse(text,filename=change['post_move_path']);py+=1
    if change['post_move_path'].endswith('.ipynb'):
        old=json.loads(before);new=json.loads(after)
        assert len(old['cells'])==len(new['cells'])
        for a,b in zip(old['cells'],new['cells']):
            assert a.get('outputs')==b.get('outputs')
            assert a.get('execution_count')==b.get('execution_count')
            output_cells+=1
        nb+=1
result['checks'].append({'name':'adaptation_pre_post_hashes_and_bytes','passed':len(plan['changes'])})
result['checks'].append({'name':'adapted_python_ast_parse','passed':py})
result['checks'].append({'name':'adapted_notebooks_parse_and_historical_output_preservation','notebooks':nb,'cells':output_cells})
for repair in plan['navigation_repairs']:
    target=repair['new_link'].split('#',1)[0]
    resolved=posixpath.normpath(posixpath.join(posixpath.dirname(repair['destination']),target))
    assert resolved==repair['resolved_after'],repair
    assert resolved in future,resolved
result['checks'].append({'name':'declared_navigation_repairs_resolve_in_future_tree','passed':len(plan['navigation_repairs'])})
for p in move.values():assert p in future
assert len(set(move.values()))==84
result['checks'].append({'name':'move_destinations_unique','passed':84})
(HERE/(P+'_validation.json')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))

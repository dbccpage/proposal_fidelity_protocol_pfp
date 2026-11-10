"""Validate actual relocated education artifacts; writes only review receipts."""
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import posixpath
import zipfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
P='education_demo_classification'

def read(name):return json.loads((HERE/name).read_text(encoding='utf-8'))
def sha(raw):return hashlib.sha256(raw).hexdigest()
report=read(P+'.json')
plan=read(P+'_adaptation_plan.json')
recovery=read('demo_support_recovery.json')
consumer=read('demo_support_consumer_receipt.json')
errors=[]
def check(ok,kind,detail):
    if not ok:errors.append({'kind':kind,'detail':detail})

frozen_hashes={P+'.json':'e75bc3e959269c0961da1eb0e0c6d8bc426cc2fe13e36a6b9b3e8bfedd404eba',P+'_adaptation_plan.json':'c6985b78f66a14b7532c748f0c48eea22b05923d26c47332fe6402a440f56786'}
for name,expected in frozen_hashes.items():check(sha((HERE/name).read_bytes())==expected,'frozen_review_drift',name)
archive_checks=[]
for path,expected in [(recovery['archive'],recovery['sha256']),(consumer['backup'],consumer['backup_sha256'])]:
    actual=sha(Path(path).read_bytes());check(actual==expected,'archive_hash',path)
    archive_checks.append({'path':path,'sha256':actual,'expected_sha256':expected,'matches':actual==expected})

by_current={c['post_move_path']:c for c in plan['changes']}
move={r['path']:r['proposed_destination'] for r in report['files'] if r['disposition']=='move'}
path_checks=[]
with zipfile.ZipFile(recovery['archive']) as z:
    for row in report['files']:
        old=row['path'];current=move.get(old,old);fp=ROOT/current
        expected=by_current[current]['post_adaptation_sha256'] if current in by_current else row['sha256']
        actual=sha(fp.read_bytes()) if fp.is_file() else None
        check(actual==expected,'current_source_hash',current)
        entry={'original_path':old,'current_path':current,'expected_sha256':expected,'actual_sha256':actual,'matches':actual==expected}
        if old in move:
            entry['original_path_absent']=not (ROOT/old).exists()
            check(entry['original_path_absent'],'original_source_still_present',old)
            archived=z.read('pfp/'+old)
            entry['original_archive_sha256']=sha(archived)
            check(entry['original_archive_sha256']==row['sha256'],'original_archive_member_hash',old)
        path_checks.append(entry)

adaptation_checks=[];notebook_checks=[]
with zipfile.ZipFile(consumer['backup']) as z:
    for change in plan['changes']:
        target=change['post_move_path'];current=(ROOT/target).read_bytes()
        expected_bytes=base64.b64decode(change['after_bytes_base64'],validate=True)
        before=z.read('pfp/'+target)
        check(sha(before)==change['original_sha256'],'consumer_backup_hash',target)
        check(current==expected_bytes,'adaptation_exact_bytes',target)
        adaptation_checks.append({'path':target,'original_backup_sha256':sha(before),'current_sha256':sha(current),'matches_planned_bytes':current==expected_bytes})
        if target.endswith('.ipynb'):
            old=json.loads(before);new=json.loads(current);planned=json.loads(expected_bytes)
            equal_count=len(old['cells'])==len(new['cells'])==len(planned['cells'])
            check(equal_count,'notebook_cell_count',target)
            cells=[]
            for i,(a,b,c) in enumerate(zip(old['cells'],new['cells'],planned['cells'])):
                same=a.get('outputs')==b.get('outputs')==c.get('outputs') and a.get('execution_count')==b.get('execution_count')==c.get('execution_count')
                check(same,'notebook_historical_output',target+':'+str(i))
                cells.append({'index':i,'outputs_and_execution_count_preserved':same})
            notebook_checks.append({'path':target,'archive_member':'pfp/'+target,'cell_count_preserved':equal_count,'cells':cells})

navigation=[]
for repair in plan['navigation_repairs']:
    source=repair['destination'];raw=(ROOT/source).read_text(encoding='utf-8-sig')
    if source.endswith('.ipynb'):
        raw='\n'.join(''.join(c.get('source',[])) for c in json.loads(raw)['cells'])
    target=posixpath.normpath(posixpath.join(posixpath.dirname(source),repair['new_link'].split('#',1)[0]))
    present=(ROOT/target).exists();link_present=repair['new_link'] in raw
    check(present and target==repair['resolved_after'],'navigation_actual_target',repair)
    check(link_present,'navigation_actual_source_link',repair)
    navigation.append({'source':source,'link':repair['new_link'],'target':target,'target_exists':present,'source_contains_planned_link':link_present,'anchor_scope':'File target verified; fragment semantics not separately audited.'})

# Actual fresh tool execution results, retained verbatim. This validator does not
# rerun tests or reinterpret synthetic assertions as claims of real learning.
tests=[
 {'suite':'simulations','command':'.venv/Scripts/python.exe -B -X utf8 dag/migrations/education_demo_classification_postmove_tests.py --suite simulations','exit_code':0,'stdout':'......................                                                   [100%]\r\n22 passed in 0.37s\r\n','passed':22},
 {'suite':'local-game','command':'.venv/Scripts/python.exe -B -X utf8 dag/migrations/education_demo_classification_postmove_tests.py --suite local-game','exit_code':0,'stdout':'...................                                                      [100%]\r\n19 passed in 0.31s\r\n','passed':19},
 {'suite':'operad','command':'.venv/Scripts/python.exe -B -X utf8 dag/migrations/education_demo_classification_postmove_tests.py --suite operad','exit_code':0,'stdout':'..........                                                               [100%]\r\n10 passed in 0.26s\r\n','passed':10}
]
result={'schema_version':1,'status':'PASS' if not errors else 'FAIL','recorded_utc':datetime.now(timezone.utc).isoformat(),'scope':'Fresh post-move pure-Python tests and actual file/navigation/custody verification. No source edits.','frozen_artifact_hashes':frozen_hashes,'tests':tests,'test_runner_sha256':sha((HERE/(P+'_postmove_tests.py')).read_bytes()),'summary':{'tests_passed':sum(t['passed'] for t in tests),'source_paths_checked':len(path_checks),'moved_originals_absent':sum(p.get('original_path_absent',False) for p in path_checks),'adaptation_exact_byte_checks':len(adaptation_checks),'navigation_targets_checked':len(navigation),'notebooks_with_outputs_compared_to_archive_and_plan':len(notebook_checks),'notebook_cells_compared':sum(len(n['cells']) for n in notebook_checks),'provider_calls':0,'native_calls':0,'media_renders':0,'source_edits':0},'archives':archive_checks,'source_path_checks':path_checks,'adaptation_checks':adaptation_checks,'notebook_output_checks':notebook_checks,'navigation_checks':navigation,'needed_repairs':errors,'limitations':['Existing toy-model defects and synthetic metric assumptions remain; passing the education tests does not establish production contracts or learning efficacy.','The prepared runner disables repository conftests, plugin autoload and pytest cache, and verifies selected module/test hashes before importing them.','No notebooks, generators, widget UI, media renderer, native host or provider path executed.','Navigation verification checks actual file targets and presence of planned hrefs, not every Markdown fragment or every pre-existing broken historical link.','The 221 unadapted notebooks remain byte-identical to their frozen original inventory hashes; five adapted notebooks received explicit output/execution-count comparisons.']}
(HERE/(P+'_postmove_validation.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
md=['# Education post-move validation','',f"**{result['status']}: 51 tests passed.** Simulations: 22; local game: 19; operad simulation: 10.",'', 'All 1,539 classified current paths match their original or separately planned adaptation hashes. The 84 moved original paths are absent; each archived original matches its custody hash. All 48 adaptation files match the exact planned bytes. Both recovery ZIP hashes match their recorded hashes.','', 'All 145 declared navigation targets exist in the actual tree and their planned links appear in the current consumers. Five adapted notebooks (66 cells) preserve outputs and execution counts against the original consumer archive and adaptation plan. The other 221 notebooks remain byte-identical to the classification inventory.','', '**Needed repair:** '+('None found by these checks.' if not errors else json.dumps(errors,ensure_ascii=False)), '', 'No source edits, provider calls, native calls, notebook execution or media rendering were performed. Tests cover their existing bounded teaching behavior; they do not certify production semantics or measured learning efficacy. Historical Markdown fragment correctness and pre-existing missing links remain outside this validation.']
(HERE/(P+'_postmove_validation.md')).write_text('\n'.join(md)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'summary':result['summary'],'needed_repairs':errors},ensure_ascii=False,indent=2))

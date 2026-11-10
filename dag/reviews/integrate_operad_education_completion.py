"""Close the80-path teaching partition without rewriting its pinned checkpoints."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT/'dag/reviews'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
load = lambda stem: json.loads((REV/(stem+'.json')).read_text())

with contextlib.redirect_stdout(io.StringIO()):
    runpy.run_path(str(REV/'additional_operads_education_atlas_validate.py'))
scope = load('additional_operads_education_remaining_scope')
parent = load('additional_operads_education_remaining')
child = load('additional_operads_education_atlas')
validation = load('additional_operads_education_atlas_validation')
assert sha(REV/'additional_operads_education_remaining.json') == '7670e4cbe15afbdd355a27c0e08ff7fc3f098ffa3417c0262411d7dedd92181e'
assert sha(REV/'additional_operads_education_atlas.json') == 'f1bcd86f77f3f183fe5a69e03db244174152b7637aeeca1fa19ecd7b18cf6a12'
rows = {}
for stem, report in [('additional_operads_education_remaining',parent),('additional_operads_education_atlas',child)]:
    for row in report['file_reviews']:
        assert row['path'] not in rows
        if not row.get('supporting_source_outside_52'):
            assert sha(ROOT/row['path']) == row['sha256']
        rows[row['path']] = {'path':row['path'],'sha256':row['sha256'],
                            'reading_report':'dag/reviews/'+stem+'.json',
                            'full_source_read':row['full_source_read'],
                            'supporting_source':row.get('supporting_source_outside_52',False)}
assert {r['path'] for r in scope['files']} == {p for p,r in rows.items() if not r['supporting_source']}
assert len(rows)==81 and sum(r['full_source_read'] for r in rows.values())==76
integration = {'status':'parent_review_and_integrity_validation_pass',
 'report':'dag/reviews/additional_operads_education_atlas.json','report_sha256':sha(REV/'additional_operads_education_atlas.json'),
 'claims':5,'findings':14,'full_frozen_text_bodies':47,'supporting_original_full_bodies':1,
 'bounded_whole_image_reviews':5,'source_evidence_rows_checked':validation['source_evidence_rows_checked'],
 'controls_attributed_to_agent':8,
 'parent_review_basis':'Read all compact claims, findings, limits and dependency context; complete check and validation source; all eight check results. Revalidated source/archive/prior-report pins and evidence ranges using the reviewed validator.',
 'limits':['Agent body and visual reviews remain attributed; parent did not independently reread every source or PNG.',
           'The initial unabridged claims dump was truncated; the later compact statement dump was complete.',
           'No native, provider or original-code execution. Prior production reviews and historical receipts are not new executions.']}
(REV/'additional_operads_education_atlas_parent_integration.json').write_text(json.dumps(integration,indent=2)+'\n')
completion={'status':'complete_declared_80_file_scope_plus_one_supporting_original',
 'source_commit':scope['source_commit'],'scope_manifest':'dag/reviews/additional_operads_education_remaining_scope.json',
 'source_reports':[{'path':'dag/reviews/'+stem+'.json','sha256':sha(REV/(stem+'.json'))}
                   for stem in ('additional_operads_education_remaining','additional_operads_education_atlas')],
 'counts':{'frozen_scope':80,'full_text_frozen_scope':75,'bounded_png_visual':5,'supporting_original_full_text':1,
           'pending':0,'claims':len(parent['claims'])+len(child['claims']),'findings':len(parent['findings'])+len(child['findings'])},
 'file_reading_map':sorted(rows.values(),key=lambda r:r['path']),
 'claims':[],'findings':[],
 'limits':['Full text, whole-image visual assessment and supporting migration custody are distinct dispositions.',
           'Frozen28-file parent checkpoint remains unchanged because the atlas report pins its hash.',
           'Completes this education partition, not the repository review or an operadic semantic-soundness theorem.']}
(REV/'additional_operads_education_completion.json').write_text(json.dumps(completion,indent=2)+'\n')
manifest_path=ROOT/'dag/swarm_manifest.json'
manifest=json.loads(manifest_path.read_text())
completed=manifest['completed_followup_slices']
for path in ['dag/reviews/additional_operads_education_atlas.json','dag/reviews/additional_operads_education_completion.json']:
    if path not in completed: completed.append(path)
manifest['parent_active_slice'].pop('awaiting_operad_education_integration',None)
# Keep the current parent and other agent assignments intact.
assignments=manifest['active_audit_slices']
assignment=next(a for a in assignments if a['agent']=='audit_imported_pilots')
assignment.update({'status':'in_progress','scope':'198 remaining operad pattern bodies',
 'scope_manifest':'dag/reviews/additional_operad_patterns_remaining_scope.json',
 'files':198,'report':'dag/reviews/additional_operad_patterns_remaining.json',
 'completed_scope_manifest':'dag/reviews/additional_operads_education_atlas_scope.json',
 'description':'Contextual review of helpful/anti pattern prose and templates; source labels alone do not establish implementation or efficacy.'})
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(completion['counts']))

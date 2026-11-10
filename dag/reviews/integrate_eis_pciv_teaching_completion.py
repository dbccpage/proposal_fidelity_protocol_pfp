"""Close the126-file teaching scope while preserving the referenced95-file checkpoint."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT/'dag/reviews'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk(value):
    if isinstance(value,dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value,list):
        for child in value:
            yield from walk(child)


source_reports = ['additional_eis_pciv_education_remaining','additional_eis_pciv_teaching_scripts']
data = {stem:json.loads((REV/(stem+'.json')).read_text()) for stem in source_reports}
scope = json.loads((REV/'additional_eis_pciv_education_remaining_scope.json').read_text())
frozen = {r['path']:r for r in scope['files']}
rows = {}
for stem,report in data.items():
    for row in report['file_reviews']:
        assert row['path'] not in rows
        assert row['full_source_read']
        raw = (ROOT/row['path']).read_bytes()
        assert sha(ROOT/row['path']) == row['sha256'] == frozen[row['path']]['sha256']
        assert row['reviewed_lines'] == [[1,len(raw.decode('utf-8').splitlines())]]
        rows[row['path']] = {'path':row['path'],'sha256':row['sha256'],
                            'reading_report':'dag/reviews/'+stem+'.json','reviewed_lines':row['reviewed_lines']}
assert set(rows) == set(frozen) and len(rows) == 126
child = data['additional_eis_pciv_teaching_scripts']
validation = json.loads((REV/'additional_eis_pciv_teaching_scripts_validation.json').read_text())
assert validation['json_sha256'] == sha(REV/'additional_eis_pciv_teaching_scripts.json')
pins = set()
ranges = 0
for item in walk(child):
    if isinstance(item.get('path'),str) and isinstance(item.get('sha256'),str):
        path = (ROOT/item['path']).resolve()
        assert path.is_relative_to(ROOT) and sha(path) == item['sha256'],item['path']
        pins.add(item['path'])
        bounds = item.get('reviewed_lines',item.get('lines',[]))
        if bounds:
            if isinstance(bounds[0],int):bounds=[bounds]
            count = len(path.read_text(encoding='utf-8').splitlines())
            for first,last in bounds:
                assert 1<=first<=last<=count
                ranges += 1
integration = {'status':'parent_review_and_integrity_validation_pass',
 'report':'dag/reviews/additional_eis_pciv_teaching_scripts.json',
 'report_sha256':sha(REV/'additional_eis_pciv_teaching_scripts.json'),
 'full_body_receipts':31,'claims':4,'findings':10,'unique_source_and_prior_report_pins':len(pins),
 'ranges_checked':ranges,'fresh_controls_attributed_to_agent':5,
 'review_basis':'Parent read all compact claims/findings and the complete check source plus all five results. Agent full-body readings are attributed, not represented as parent rereads.',
 'truncation_limit':'The long per-file Markdown appendix was not fully reread by parent; only the explicit agent receipts establish its body coverage.'}
(REV/'additional_eis_pciv_teaching_scripts_parent_integration.json').write_text(json.dumps(integration,indent=2)+'\n')

prefix = 'education/010_oepciv/'
evidence_paths = [prefix+'levels/level_07_ecological_reserves_and_population.md',
 prefix+'curriculum/420_population_reserves_persistence/scripts/lesson_420_07_ecological_reserves_and_population.md',
 prefix+'curriculum/420_population_reserves_persistence/notebooks/lesson_420_07_ecological_reserves_and_population.ipynb']
completion = {'status':'complete_declared_126_file_source_scope','source_commit':scope['source_commit'],
 'scope_manifest':'dag/reviews/additional_eis_pciv_education_remaining_scope.json',
 'source_reports':[{'path':'dag/reviews/'+stem+'.json','sha256':sha(REV/(stem+'.json'))} for stem in source_reports],
 'counts':{'scope':126,'parent_full_bodies':95,'agent_full_bodies':31,'pending':0,
           'parent_claims':6,'agent_claims':4,'parent_findings':13,'agent_findings':10,'cross_document_findings':1},
 'file_reading_map':sorted(rows.values(),key=lambda r:r['path']),
 'claims':[],
 'findings':[{'id':'EPE-X01','severity':'medium',
   'statement':'The population reserve lesson has different quota policies and bucket meanings: the level/notebook use60/25/15 for Frontier/Unmeasured/Baseline, while narration uses60/30/10 for exploited/maturing/unmeasured with explicit small-capacity cases. At capacity20 their respective exact outputs are [12,5,3] and [12,6,2], without a declared coordinate mapping. This is separate from the notebook tie/float defects; the three surfaces do not specify one common policy.',
   'evidence':[{'path':p,'sha256':frozen[p]['sha256']} for p in evidence_paths],
   'recommended_action':'Name each policy/version and bucket semantics, supply any intended mapping, and align examples to their actual owner before comparing exploration outcomes; do not assume the shared lesson title makes these equivalent.'}],
 'limits':['This closes the frozen126-file remaining teaching slice, not the full repository or relocated EIS/PCIV demo code.',
           'The95-file parent report remains a frozen checkpoint because the agent explicitly references its hash; this completion receipt resolves its previously pending31 paths.',
           'No additional provider, native or notebook execution. Independent prior control populations are not pooled into model accuracy.']}
(REV/'additional_eis_pciv_education_completion.json').write_text(json.dumps(completion,indent=2)+'\n')
manifest_path = ROOT/'dag/swarm_manifest.json'
manifest = json.loads(manifest_path.read_text())
for relative in ['dag/reviews/'+stem+'.json' for stem in source_reports]+['dag/reviews/additional_eis_pciv_education_completion.json','dag/reviews/additional_migrated_operad_teaching.json']:
    if relative not in manifest['completed_followup_slices']:
        manifest['completed_followup_slices'].append(relative)
for row in manifest['active_audit_slices']:
    if row.get('agent','').endswith('audit_imported_pilots'):
        row.update(scope='52 remaining operad atlas/level/diagram sources plus one revised supporting chapter',
                   files=52,status='in_progress',scope_manifest='dag/reviews/additional_operads_education_remaining_scope.json',
                   report='dag/reviews/additional_operads_education_atlas.json',
                   completed_scope_manifest='dag/reviews/additional_eis_pciv_teaching_scripts_scope.json',
                   description='Excludes28 parent_initial_paths; supporting chapter23 has separate original/current custody.')
manifest['parent_active_slice'] = {'status':'in_progress','scope_manifest':'dag/reviews/additional_operads_education_remaining_scope.json',
 'scope_files':80,'report':'dag/reviews/additional_operads_education_remaining.json','full_body_reads':28,
 'delegated_remaining_files':52,'delegated_remaining_report':'dag/reviews/additional_operads_education_atlas.json',
 'separate_migrated_source_completion':'dag/reviews/additional_migrated_operad_teaching.json'}
manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'completion':completion['counts'],'agent_validation':integration}))

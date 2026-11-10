"""Metadata-only reconciliation of legacy test paths against original inventory and authorized move."""
import sys
sys.dont_write_bytecode=True
import json,collections
import additional_pfp_tests_remaining_audit as a
ip=a.ROOT/'dag/file_inventory.json';mp=a.ROOT/'dag/migrations/demo_support_move_plan.json'
inv=json.loads(ip.read_text(encoding='utf8'));plan=json.loads(mp.read_text(encoding='utf8'))
prefix='education/documentation/014_normal_forms'
matches=[x['path'] for x in inv['files'] if x['path'].startswith(prefix)]
edu=[x for x in plan['entries'] if x['source_relative_path'].startswith('education/')]
moved=[x['source_relative_path'] for x in edu if 'normal_forms' in x['source_relative_path']]
assert not matches and not moved and len(edu)==84
out={'method':'Originalinventory and demo-support moveplan pathmetadata only; no movedbody/import/execution','frozen_inventory':{'path':'dag/file_inventory.json','sha256':a.sha(ip),'prefix':prefix,'matched_files':matches},'move_plan':{'path':'dag/migrations/demo_support_move_plan.json','sha256':a.sha(mp),'education_entries':len(edu),'prefix_counts':dict(collections.Counter('/'.join(x['source_relative_path'].split('/')[:3]) for x in edu)),'normal_forms_entries':moved},'conclusion':'Pre-existing stale cross-repository import paths, not a regression from the authorized84-file education move.'}
a.write('_legacy_path_migration_reconciliation.json',out)
n=a.read('_notes.json');f=next(x for x in n['findings'] if x['id']=='PFPTESTS-F043')
f['statement']='Two property suites retain pre-existing stale cross-repository paths and fail before collection.'
f['reason']+=' MetadatareconciliationC036 findszerofrozenoriginalfiles undereducation/documentation/014_normal_forms andzero normal_forms entriesinthe84-fileauthorizededucationmove. Thisispre-existing stale cross-repository import, notmigrationregression.'
f['limits']+=' No repairrequested orperformed; historicalsourcepinsretained.'
n['controls'].append({'id':'PFPTESTS-C036','rule':'frozen_inventory_vs_authorized_education_move_path_reconciliation','status':'preexisting_stale_paths_confirmed','evidence':f['evidence'],'receipt':{'path':'dag/reviews/additional_pfp_tests_remaining_legacy_path_migration_reconciliation.json','sha256':a.sha(a.file('_legacy_path_migration_reconciliation.json'))},'helper':{'path':'dag/reviews/additional_pfp_tests_remaining_checkpoint23.py','sha256':a.sha(a.file('_checkpoint23.py'))},'limits':'Pathmetadataonly. Originalinventoryhasno014_normal_formsbody; moved84entriesareothereducationtrees.'})
n['external_dependencies_consulted'].extend([{'path':'dag/file_inventory.json','sha256':a.sha(ip),'purpose':'Bounded pathmetadata census of missing legacy prefix, no body credit.'},{'path':'dag/migrations/demo_support_move_plan.json','sha256':a.sha(mp),'purpose':'Bounded source_relative_path metadata for84educationentries; no foreignmovedbody access or execution.'}])
a.write('_notes.json',n);a.report();print(json.dumps(out))

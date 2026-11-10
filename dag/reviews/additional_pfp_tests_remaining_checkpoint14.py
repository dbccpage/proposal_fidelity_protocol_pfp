import sys,difflib,hashlib,zipfile
sys.dont_write_bytecode=True
import additional_pfp_tests_remaining_audit as a
p='pfp/tests/types/test_taxonomy_task_families_yaml.py'
a.record(p,1,130,'Parent-authorized current migration adaptation fully read, plus complete unified delta against preserved139line original. One matrix path now pilots/anomalon_woland/matrix/max_pilot_matrix.yaml; removes obsolete second assignment and identical repeated bedrock set. Remaining body unchanged. Current path fix does not resolve catalog ordering/token mismatch reported by parent targeted2pass/1fail run; no tests or imported pilot reads repeated here.',current=True)
archive=a.ROOT/'dag/migrations/taxonomy_matrix_consumer_original.zip'
with zipfile.ZipFile(archive) as z:b=z.read(p)
assert hashlib.sha256(b).hexdigest()==a.row(p)['sha256']
assert b==a.file('_original_taxonomy_task_families_yaml.py.txt').read_bytes()
receipt=a.ROOT/'dag/migrations/taxonomy_matrix_consumer_verification.json'
n=a.read('_notes.json');n['external_dependencies_consulted'].append({'path':str(receipt.relative_to(a.ROOT)).replace('\\','/'),'sha256':a.sha(receipt),'purpose':'Fully read parent-owned migration verification receipt; targeted2pass/1fail and unchanged baseline ordering failure, plus100matrix tokens/one mismatch are attributed parent observations, not rerun or pilot-body credit.'})
n['controls'].append({'id':'PFPTESTS-C011','rule':'authorized_taxonomy_consumer_current_original_binding','status':'original_archive_and_git_capture_match_current_delta_reviewed','source_evidence':[{'path':p,'sha256':a.row(p)['sha256'],'lines':[1,139]}],'current_sha256':a.row(p)['current_sha256'],'current_full_read_lines':[1,130],'archive_sha256':a.sha(archive),'archive_member':p,'parent_verification_receipt_sha256':a.sha(receipt),'test_result_attribution':'Parent receipt only:2pass/1fail, same catalog ordering failure on original. Separate matrix coverage missing woland_tribunal_dialectic. No test suite pass claim.','limits':'Archive compared only this member, no wholearchive body credit or matrix source access.'})
f=next(x for x in n['findings'] if x['id']=='PFPTESTS-F009');f['current_resolution']={'status':'path_adapted_by_parent','current_sha256':a.row(p)['current_sha256'],'control':'PFPTESTS-C011','remaining_limits':'Historical original finding retained. Targeted current test remains failing catalog ordering, and parent separately reports one unmatched renamed matrix token.'}
a.write('_notes.json',n);a.report()

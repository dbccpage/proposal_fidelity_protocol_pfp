import sys
sys.dont_write_bytecode=True
import additional_pfp_tests_remaining_audit as a
old=a.file('_final_validation_revision0.json.snapshot');assert not old.exists();old.write_bytes(a.file('_final_validation.json').read_bytes())
n=a.read('_notes.json');f=next(x for x in n['findings'] if x['id']=='PFPTESTS-F035')
assert 'body substantive review remains pending' in f['limits']
f['limits']='The current body matches the frozen original inventory, so this is a retained historical custody inconsistency, not audit-caused drift. The historical prechange bytes and reason remain unknown. The retained solver, checker and Q40 test bodies have now all been fully reviewed; CL045/CL046 and F111 record their mathematical and malformed-input assessments. Completed body review does not repair the manifest mismatch or authenticate a historical run.'
a.write('_notes.json',n)

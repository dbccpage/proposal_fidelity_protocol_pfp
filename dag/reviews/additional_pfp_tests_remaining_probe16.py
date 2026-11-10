"""Frozen inventory versus read mutation-catalogue selection; metadata only."""
import sys
sys.dont_write_bytecode=True
import ast
import json
from pathlib import Path
import additional_pfp_tests_remaining_audit as a
p='pfp/tests/mutation_catalogue.py'
t=ast.parse('\n'.join(a.source(p)))
values={}
for n in t.body:
 if isinstance(n,ast.Assign):
  for target in n.targets:
   if isinstance(target,ast.Name) and target.id in {'DEFAULT_TESTS','EXCLUDE_FROM_RUNS'}:values[target.id]=ast.literal_eval(n.value)
inventory_path=Path('dag/file_inventory.json')
inventory=json.loads(inventory_path.read_text(encoding='utf-8'))
original={r['path'] for r in inventory['files'] if r['path'].startswith('pfp/tests/test_') and r['path'].endswith('.py') and r['path'].count('/')==2}
declared=set(values['DEFAULT_TESTS']);excluded=set(values['EXCLUDE_FROM_RUNS'])
missing=sorted(original-declared-excluded)
stale=sorted(declared-original)
assert missing
a.write('_probe16.json',{'runtime':sys.version,'source':{'path':p,'sha256':a.row(p)['sha256'],'lines':[38,193]},'inventory':{'path':str(inventory_path).replace('\\','/'),'sha256':a.sha(inventory_path)},'original_root_test_files':len(original),'declared_selection_count':len(declared),'explicit_exclusions':sorted(excluded),'missing_original_files':missing,'declared_not_in_original_root_tests':stale,'limits':['Metadata-only comparison with pinned original inventory, not current glob or test execution.','No mutation targets read or changed; no native builds, provider calls, fixture contents or external inputs.','The catalogue guard would catch omissions when run; this receipt does not establish any mutation kill/survival result.']})
print(json.dumps({'original_root_tests':len(original),'declared':len(declared),'missing':len(missing),'stale':len(stale)}))

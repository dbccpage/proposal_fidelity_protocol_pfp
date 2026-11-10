"""C060 test source reference, original inventory/current path metadata only."""
import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
import additional_pfp_tests_remaining_audit as a
ip=Path('dag/file_inventory.json');inv=json.loads(ip.read_text(encoding='utf-8'))
p='c060_self_verifying_checker_synthesis/run_c060_matrix.py'
rows=[r['path'] for r in inv['files']]
result={'path':p,'in_original_inventory':p in rows,'current_exists':Path(p).is_file(),'original_same_basename':[x for x in rows if x.endswith('/run_c060_matrix.py')]}
assert not result['in_original_inventory'] and not result['current_exists']
a.write('_probe20.json',{'source':{'path':'pfp/tests/test_c060_accounted_runner.py','sha256':a.row('pfp/tests/test_c060_accounted_runner.py')['sha256'],'lines':[21,23]},'inventory':{'path':str(ip).replace('\\','/'),'sha256':a.sha(ip)},'result':result,'limits':['No task/runner/fixture bodies or external/private data consulted.','Existing import aliases cannot create this absolute file path; no test or imported runner execution.']})
print('C060 absolute runner reference absent from original inventory and current checkout')

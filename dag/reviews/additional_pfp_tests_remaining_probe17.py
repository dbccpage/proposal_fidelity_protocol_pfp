"""Legacy pilot references reconciled using paths only, without pilot bodies."""
import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
import additional_pfp_tests_remaining_audit as a
ip=Path('dag/file_inventory.json');inv=json.loads(ip.read_text(encoding='utf-8'));paths={r['path'] for r in inv['files']}
targets=['adversary/tests/pilots/dimensions/dimension_register.yaml','adversary/tests/pilots/matrix/max_pilot_matrix.yaml','documentation/030_the_symbol_game_proposal_fidelity_protocol_pfp/pilots/pilot_output/__init__.py']
rows=[{'path':p,'in_original_inventory':p in paths,'current_exists':Path(p).is_file()} for p in targets]
assert all(not r['in_original_inventory'] and not r['current_exists'] for r in rows)
a.write('_probe17.json',{'inventory':{'path':str(ip).replace('\\','/'),'sha256':a.sha(ip)},'references':rows,'original_inventory_suffix_matches':sorted(p for p in paths if p.endswith('/dimension_register.yaml') or p.endswith('/max_pilot_matrix.yaml')),'sources':[{'path':'pfp/tests/'+name,'sha256':a.row('pfp/tests/'+name)['sha256']} for name in ['test_dimension_register_models.py','test_pilot_models.py']],'limits':['Path metadata only; no pilot, matrix, key, answer or provider body consulted.','Absent in original inventory means pre-existing stale reference/explicit retirement, not caused by the authorized84-file education move.']})
print('three legacy references absent in both frozen inventory and current path metadata')

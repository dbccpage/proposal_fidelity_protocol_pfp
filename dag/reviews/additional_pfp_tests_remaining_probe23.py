import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
import additional_pfp_tests_remaining_audit as a
inventory=Path('dag/file_inventory.json')
paths={row['path'] for row in json.loads(inventory.read_text(encoding='utf-8'))['files']}
prefix='atlas/coda_atlas/F004_papers/015_pfp/002_pfp_signed_presentations_and_search_frontier/code/genesis_alpha/'
rows=[{'path':prefix+name,'in_original_inventory':prefix+name in paths,'current_file_exists':Path(prefix+name).is_file()} for name in ('sign_graph.py','frontier_search.py')]
assert all(not row['in_original_inventory'] and not row['current_file_exists'] for row in rows)
p='pfp/tests/test_finite_gauge_workbench.py';a.source(p)
a.write('_probe23.json',{'status':'observed','rule':'historical_finite_gauge_reference_path_custody','inventory_sha256':a.sha(inventory),'source_binding':{'path':p,'sha256':a.row(p)['sha256'],'lines':[59,73]},'paths':rows,'limits':'Original inventory and current path metadata only. No historical/current implementation body reading or execution; absent before the authorized education move, not attributed to it.'})
print('Recorded two absent historical path references.')

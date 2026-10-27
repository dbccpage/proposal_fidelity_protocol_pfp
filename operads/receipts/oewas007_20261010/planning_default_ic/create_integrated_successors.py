"""Compose current-main planning custody without rewriting historical receipts."""
from __future__ import annotations
import copy,hashlib,json
from pathlib import Path
ROOT=Path.cwd(); PRE='product_planning_office/receipts/'
OUT=ROOT/'workflows_agents_skills/receipts/oewas007_20261010/planning_default_ic'
def sha(raw): return hashlib.sha256(raw).hexdigest()
nav=json.loads((OUT/'command_navigation.json').read_bytes())
command_paths={r['path'] for r in nav['changes'] if '/epic_' in r['path']}
core={'product_planning_office/plans/epics/oewas/epic_oe_oewas_007_american_ic_partition_and_typed_schema_plan.md', 'product_planning_office/plans/epics/oewas/epic_oe_oewas_009_cross_engine_ingress_parity_oewas_oeeis_oeadversary_plan.md'}
links={'product_planning_office/plans/epics/oegov/epic_oe_oegov_004_blackrod_warrants_and_observed_enforcement_plan.md','product_planning_office/plans/epics/oegov/epic_oe_oegov_005_four_e_situated_governance_plan.md','product_planning_office/plans/epics/oeos/epic_oe_oeos_001_immutable_diagnostic_custody_plan.md'}
results=[]
for stem,key in [('epic_obstruction_walk','epics'),('prior_art_epic_map','prior_epic_inventory')]:
 oldpath=PRE+stem+'_20261010_oewas002_successor.json'; raw=(ROOT/oldpath).read_bytes(); old=json.loads(raw); new=copy.deepcopy(old)
 earlierpath=PRE+stem+'_20261010_oewas007_default_ic_successor.json'; earlierraw=(ROOT/earlierpath).read_bytes(); earlier=json.loads(earlierraw)
 earlierrows={r['path']:r for r in earlier[key]}; deltas=[]
 for row in new[key]:
  path=row['path']; actual=sha((ROOT/path).read_bytes())
  if actual==row['sha256']:continue
  assert path in core|command_paths|links,path
  reason=[];previous=row['sha256'];row['sha256']=actual
  if path in core:
   reason.append('User-directed default canonical _ic and bounded DEV-data/historical-reader integration; full epic remains RESEARCH_HOLD.')
   for field in ('retained_residuals','test_plan_status_scope','review_provenance','review_scope','bounded_implementation'):
    if field in earlierrows[path]:row[field]=copy.deepcopy(earlierrows[path][field])
   row['bounded_implementation']['final_inventory_sha256']='1f992ce4ec935b7a774fad256332435a948a41fb14492f1036265d15a31e5ca5'
   row['bounded_implementation']['upstream_amendment_evidence']='receipts/oewas007_20261010/upstream_inclusion.json'
   row['bounded_implementation']['amendment_limit']='Original6672 executor cutover and five-file upstream inclusion are distinct evidence; not a public-executor replay of6677.'
  if path in command_paths:reason.append('Only audit CLI module navigation changes to injected filesystem composition; research/status unchanged.')
  if path in links:reason.append('Earlier narrowly verified OEOS flattened-path link repair; no implementation completion promotion.')
  deltas.append({'path':path,'immediate_predecessor_current_sha256':previous,'current_sha256':actual,'reasons':reason})
 assert set(core)<={r['path'] for r in deltas}
 new['immediate_predecessor']={'path':oldpath,'sha256':sha(raw),'scope':'Latest merged main002 planning successor retained byte-exact, including governance source/base metadata.'}
 new['immediate_predecessor_review']=copy.deepcopy(old['successor_review'])
 new['additional_oewas007_custody_predecessor']={'path':earlierpath,'sha256':sha(earlierraw),'scope':'Earlier default-IC planning candidate retained unchanged; its own predecessors preserve opt-in planning and exact source inputs.'}
 new['successor_review']={'work_base_revision':'4d207641277ef3d3af16e11aafb411ada1ee10ed','integrated_main_revision':'d47c98402a42fd189acd7cf6ccd23d7a0d09c120','authority_effect':'None','scope':'Default canonical DEV storage and exact historical readback; bounded implementation distinct from full research/admission obligations. Scientific source interpretation inherited.','changed_inventory_rows':deltas,'all_other_inventory_rows_unchanged':True,'command_only_change_custody':'workflows_agents_skills/receipts/oewas007_20261010/planning_default_ic/command_navigation.json','execution_evidence':'workflows_agents_skills/receipts/oewas007_20261010/receipt.json','planning_evidence':'workflows_agents_skills/receipts/oewas007_20261010/planning_default_ic/receipt.json','full_epic_status':'RESEARCH_HOLD'}
 for a,b in zip(old[key],new[key],strict=True):
  assert a['path']==b['path']
  if a['sha256']==b['sha256']:assert a==b
  for f in ('base_sha256','predecessor_sha256'):
   if f in a:assert a[f]==b[f]
 for f in old:
  if f not in {key,'immediate_predecessor','successor_review'}:assert old[f]==new[f]
 target=PRE+stem+'_20261010_oewas007_integrated_ic_successor.json'; assert not (ROOT/target).exists()
 (ROOT/target).write_bytes((json.dumps(new,indent=2,ensure_ascii=False)+'\n').encode())
 assert (ROOT/oldpath).read_bytes()==raw and (ROOT/earlierpath).read_bytes()==earlierraw
 results.append({'path':target,'sha256':sha((ROOT/target).read_bytes()),'changed_rows':len(deltas),'immediate_predecessor':new['immediate_predecessor']})
for rel,oldname,newname in [
 ('product_planning_office/use_cases/epic_tdd_plan_audit.py','epic_obstruction_walk_20261010_oewas002_successor.json','epic_obstruction_walk_20261010_oewas007_integrated_ic_successor.json'),
 ('product_planning_office/use_cases/prior_art_epic_audit.py','prior_art_epic_map_20261010_oewas002_successor.json','prior_art_epic_map_20261010_oewas007_integrated_ic_successor.json')]:
 p=ROOT/rel;raw=p.read_bytes();assert raw.count(oldname.encode())==1;p.write_bytes(raw.replace(oldname.encode(),newname.encode()))
(OUT/'integrated_successors.json').write_bytes((json.dumps({'authority_effect':'None','successors':results},indent=2,sort_keys=True)+'\n').encode());print(json.dumps(results,indent=2))
import hashlib,json,pathlib
root=pathlib.Path.cwd()
receipts=root/'omega_engine_product_planning_office/receipts'
epic='omega_engine_product_planning_office/plans/epics/oewas/epic_oe_oewas_002_planar_tree_substitution_and_workflow_dag_plan.md'
epic_hash=hashlib.sha256((root/epic).read_bytes()).hexdigest()
updates=[]
for old_name,new_name,key,module,constant in [
 ('epic_obstruction_walk_20261010_oegov_successor.json','epic_obstruction_walk_20261010_oewas002_successor.json','epics','epic_tdd_plan_audit.py','RECEIPT'),
 ('prior_art_epic_map_20261010_oegov_successor.json','prior_art_epic_map_20261010_oewas002_successor.json','prior_epic_inventory','prior_art_epic_audit.py','MAP_PATH'),
]:
    old_path=receipts/old_name
    data=json.loads(old_path.read_bytes())
    rows=[row for row in data[key] if row['path']==epic]
    assert len(rows)==1
    prior_hash=rows[0]['sha256']
    rows[0]['sha256']=epic_hash
    data['immediate_predecessor']={'path':old_path.relative_to(root).as_posix(),'sha256':hashlib.sha256(old_path.read_bytes()).hexdigest()}
    data['successor_review']={'reviewed_base_commit':'c4de2f6e4c76e7d6ef7495daae9360255bd7133e','changed_epic':epic,'previous_sha256':prior_hash,'current_sha256':epic_hash,'scope':'Only the reviewed OEWAS-002 plan revision; all other source, inventory and original-base pins retained. Bounded implementation evidence is separate from full-plan proposed acceptance.','implementation_evidence':'omega_engine_workflows_agents_skills/receipts/oewas_002_20261010/main_integration/amendment.json','full_epic_status':'RESEARCH_HOLD','authority_effect':'None'}
    new_path=receipts/new_name
    new_path.write_bytes((json.dumps(data,indent=2,ensure_ascii=False)+'\n').encode('utf-8'))
    source=root/'omega_engine_product_planning_office/use_cases'/module
    text=source.read_text(encoding='utf-8')
    assert text.count(old_name)==1
    source.write_bytes(text.replace(old_name,new_name).encode('utf-8'))
    updates.append({'old':data['immediate_predecessor'],'new_path':new_path.relative_to(root).as_posix(),'new_sha256':hashlib.sha256(new_path.read_bytes()).hexdigest(),'constant':constant,'only_existing_row_delta':{'epic':epic,'prior_sha256':prior_hash,'new_sha256':epic_hash}})
(root/'omega_engine_workflows_agents_skills/receipts/oewas_002_20261010/planning_integration/successor_updates.json').write_bytes((json.dumps(updates,indent=2,sort_keys=True)+'\n').encode('utf-8'))
print(json.dumps(updates,indent=2))

import hashlib,json,pathlib
root=pathlib.Path.cwd()
out=root/'omega_engine_workflows_agents_skills/receipts/oewas_002_20261010/planning_integration'
epic=root/'omega_engine_product_planning_office/plans/epics/oewas/epic_oe_oewas_002_planar_tree_substitution_and_workflow_dag_plan.md'
text=epic.read_text(encoding='utf-8')
needle='Run the same finite valid/invalid topology cases through the real native port before recording topology parity.\n'
assert text.count(needle)==1
text=text.replace(needle,needle+'5. **REFACTOR:** only after the relevant controls are GREEN, simplify duplicated boundary handling while retaining the pure domain and existing native/candidate ports. Replay the same positive, negative and mutation controls after each behavioral change; retain fresh source and restoration pins.\n')
epic.write_bytes(text.encode('utf-8'))
epic_hash=hashlib.sha256(epic.read_bytes()).hexdigest()
evidence=root/'omega_engine_workflows_agents_skills/receipts/oewas_002_20261010/main_integration/amendment.json'
evidence_ref={'path':evidence.relative_to(root).as_posix(),'sha256':hashlib.sha256(evidence.read_bytes()).hexdigest(),'scope':'Bounded implemented slice; full epic obligations remain held. Historical premerge plan pins are retained in their original receipts.'}
updates=json.loads((out/'successor_updates.json').read_bytes())
for update in updates:
    path=root/update['new_path']
    data=json.loads(path.read_bytes())
    key='epics' if 'epic_obstruction_walk' in path.name else 'prior_epic_inventory'
    row=next(row for row in data[key] if row['path']==epic.relative_to(root).as_posix())
    row['sha256']=epic_hash
    if key=='epics':
        row['retained_residuals']=['Full typed native parity remains unimplemented; source graph tests and existing host replay have different evidence grades.','Shared-output/fanout and effect-aware execution semantics remain held.','External runtime admission and full estate compatibility remain separately owned obligations.']
        row['test_plan_status_scope']='PROPOSED_NOT_EXECUTED applies to remaining full-epic acceptance. The bounded slice has executed source-bound checks in the separately pinned evidence.'
        row['bounded_slice_implementation_evidence']=evidence_ref
        row['review_provenance']='Current bounded plan revision reviewed during Woland collaboration. All other semantic reviews remain inherited historical review; structural audit does not certify semantic purity.'
    data['successor_review']['current_sha256']=epic_hash
    data['successor_review']['implementation_evidence']=evidence_ref
    path.write_bytes((json.dumps(data,indent=2,ensure_ascii=False)+'\n').encode('utf-8'))
    update['new_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    update['only_existing_row_delta']['new_sha256']=epic_hash
    update['row_metadata_delta']='Only the OEWAS-002 walk row gains current residual/evidence/scope metadata; unrelated rows remain byte-value identical.' if key=='epics' else 'Only OEWAS-002 inventory sha256 changes; original base hash remains unchanged.'
(out/'successor_updates.json').write_bytes((json.dumps(updates,indent=2,sort_keys=True)+'\n').encode('utf-8'))
print(epic_hash)

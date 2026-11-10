"""Verify the final audit accounting and pins without running audited programs."""
import sys,json,hashlib
sys.dont_write_bytecode=True
import additional_pfp_tests_remaining_audit as a
import additional_pfp_tests_remaining_validate as v

def main():
 r=a.read('.json');assert r['status']=='complete' and r['analysis_complete'] and not r['repository_wide_audit_complete']
 assert r['scope']=={'files':440,'original_bytes':4248364,'original_lines':102095,'full_source_reads':415,'partial_source_reads':0,'bounded_data_dispositions':25,'reviewed_original_lines':99337,'pending_files':0}
 assert not r['remaining_unsupported_files']
 s={x['path']:x for x in a.scope()['files']};full={x['path']:x for x in r['file_reviews']};data={x['path']:x for x in r['automated_reviews']}
 assert set(full).isdisjoint(data) and set(full)|set(data)==set(s)
 assert len(full)==415 and len(data)==25
 assert all(x['full_source_read'] for x in full.values()) and all(not x['full_source_read'] for x in data.values())
 assert all(p.endswith('.json') for p in data)
 inv={x['path']:x for x in json.loads((a.ROOT/'dag/file_inventory.json').read_text(encoding='utf8'))['files']}
 assert all(s[p]['sha256']==inv[p]['sha256'] for p in s)
 revisions=[];unchanged=0
 for p in s:
  b=a.row(p);current=a.sha(a.ROOT/p)
  if current==s[p]['sha256']:unchanged+=1
  else:
   assert b.get('original_git_object') and current==b['current_sha256']
   orig=a.file(b.get('preserved_original_suffix','_original_consistency_teaching.py.txt'))
   assert a.sha(orig)==s[p]['sha256']
   parts=full[p]['current_adapted_reads'];covered=[i for x in parts for i in range(x['lines'][0],x['lines'][1]+1)]
   assert sorted(covered)==list(range(1,len(a.source(p,True))+1))
   revisions.append({'path':p,'original_sha256':s[p]['sha256'],'current_sha256':current,'original_preserved':str(orig.relative_to(a.ROOT)).replace('\\','/'),'original_and_current_bodies_complete':True})
 assert unchanged==438 and len(revisions)==2
 for group in ('claims','findings','controls'):
  for x in r[group]:
   for e in x.get('evidence',x.get('source_evidence',[])):
    assert e['path'] in full or e['path'] in data
    assert e['sha256']==s[e['path']]['sha256']
 for p in r['final_artifact_bindings']:assert a.sha(a.ROOT/p['path'])==p['sha256']
 cm=a.read('_control_artifact_manifest.json');assert cm['control_ids']==[c['id'] for c in r['controls']]
 for p in cm['artifacts']:assert a.sha(a.ROOT/p['path'])==p['sha256']
 assert len(r['findings'])==126 and len(r['claims'])==61 and len(r['controls'])==81
 assert a.sha(a.file('.json')) in a.file('.md').read_text(encoding='utf8')
 label=sys.argv[1] if len(sys.argv)>1 else 'final'
 v.validate(label)
 out=a.read('_'+label+'_validation.json');out.update(current_original_hash_matches=unchanged,authorized_current_revisions=revisions,full_source_partition_exact=True,bounded_json_partition_exact=True,all_control_artifact_pins_match=True,all_final_artifact_pins_match=True,findings=126,claims=61,controls=81,markdown_sha256=a.sha(a.file('.md')),control_artifact_manifest_sha256=a.sha(a.file('_control_artifact_manifest.json')),validator_sha256=a.sha(a.file('_final_validation.py')),original_inventory_sha256=a.sha(a.ROOT/'dag/file_inventory.json'))
 a.write('_'+label+'_validation.json',out)
 if label!='final':a.write('_final_validation.json',out)
 print(json.dumps({'validation_path':str(a.file('_final_validation.json').relative_to(a.ROOT)).replace('\\','/'),'validation_sha256':a.sha(a.file('_final_validation.json')),'report_sha256':out['report_sha256'],'markdown_sha256':out['markdown_sha256'],'control_artifact_manifest_sha256':out['control_artifact_manifest_sha256'],'status':out['status']}))

if __name__=='__main__':main()

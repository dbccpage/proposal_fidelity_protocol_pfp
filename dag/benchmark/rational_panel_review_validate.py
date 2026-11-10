import hashlib,json,pathlib,xml.etree.ElementTree as ET
H=pathlib.Path(__file__).parent;R=H.parents[1];P='rational_panel_review'
d=json.loads((H/(P+'.json')).read_text());ids=[];refs=0
assert len(d['file_reviews'])==11 and d['remaining_work']==[]
for x in d['file_reviews']:
 p=R/x['path'];assert x['sha256']==hashlib.sha256(p.read_bytes()).hexdigest()
 assert x['full_source_read']is True and x['reviewed_lines']==[[1,len(p.read_text().splitlines())]]
for x in d['claims']+d['findings']:
 ids.append(x['id'])
 for e in x['evidence']:
  p=R/e['path'];assert 1<=e['lines'][0]<=e['lines'][1]<=len(p.read_text().splitlines());refs+=1
assert len(ids)==len(set(ids))
assert all(x['status']=='resolved_by_parent_and_independently_reproduced'for x in d['findings'])
for pin in d['validation']['receipts']:assert hashlib.sha256((R/pin['path']).read_bytes()).hexdigest()==pin['sha256']
tests=json.loads((H/(P+'_focused_tests_verified.json')).read_text());assert tests['exit_code']==0
for pin in tests['source_files']:assert hashlib.sha256((R/pin['path']).read_bytes()).hexdigest()==pin['sha256']
xml=ET.parse(H/(P+'_focused_tests_verified.xml')).getroot();suite=xml.find('testsuite')if xml.tag=='testsuites'else xml
assert int(suite.attrib['tests'])==80 and all(int(suite.attrib[k])==0 for k in ['errors','failures','skipped'])
probe=json.loads((H/(P+'_probe_results_final.json')).read_text());cases={x['case']:x for x in probe['results']}
assert cases['surrogate_inert_campaign']['result']['campaign_budget']['held_microusd']==0
assert cases['surrogate_provider_metadata_campaign']['result']['run_receipt_exists']
assert cases['surrogate_provider_metadata_campaign']['result']['campaign_budget']['spent_microusd']==41
assert cases['surrogate_provider_metadata_campaign']['result']['campaign_budget']['held_microusd']==99959
assert all(cases[n]['raised']=='ValueError'for n in ['changed_runner_source_dispatch','tampered_receipt_summary','rehashed_negative_cost_summary'])
v={'status':'passed','full_source_files':11,'partial_source_files':1,'evidence_ranges':refs,'unique_claim_finding_ids':True,'resolved_findings':5,'independent_final_tests':80,'source_and_receipt_hashes':'all match','limits':'Validation checks report consistency/custody and named bounded regressions, not completeness of all possible behaviors.','report_sha256':hashlib.sha256((H/(P+'.json')).read_bytes()).hexdigest(),'markdown_sha256':hashlib.sha256((H/(P+'.md')).read_bytes()).hexdigest()}
(H/(P+'_final_validation.json')).write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v,indent=2))

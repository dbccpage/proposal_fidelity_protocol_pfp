"""Seal finite planning integration and immutable predecessor custody."""
from __future__ import annotations
import hashlib,json,subprocess,time
from pathlib import Path
ROOT=Path.cwd();OUT=ROOT/'omega_engine_workflows_agents_skills/receipts/oewas007_20261010/planning_default_ic'
assert not (OUT/'receipt.json').exists()
def digest(raw):return hashlib.sha256(raw).hexdigest()
def record(path):
 raw=path.read_bytes();return {'sha256':digest(raw),'size_bytes':len(raw)}
def load(rel):return json.loads((ROOT/rel).read_bytes())
attrs=OUT/'.gitattributes';raw=attrs.read_bytes()
for line in (b'command_navigation_before/** -text -diff\n',b'integrated_documentation_before/** -text -diff\n'):
 if line not in raw:raw+=line
attrs.write_bytes(raw)
versions={}
for name,argv in [
 ('uv',['C:/Users/a343o/.local/bin/uv.exe','--version']),
 ('ruff',['C:/Users/a343o/.local/bin/uv.exe','run','--offline','--no-project','--python','C:/Users/a343o/AppData/Roaming/uv/python/cpython-3.13.11-windows-x86_64-none/python.exe','--with','ruff','ruff','--version']),
 ('markdownlint',['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File','C:/Users/a343o/AppData/Roaming/npm/markdownlint.ps1','--version'])]:
 result=subprocess.run(argv,cwd=ROOT,capture_output=True,timeout=45,check=False);assert result.returncode==0
 for stream,data in [('stdout',result.stdout),('stderr',result.stderr)]:(OUT/('version_'+name+'.'+stream+'.log')).write_bytes(data)
 versions[name]={'command_argv':argv,'exit_code':result.returncode,'stdout_sha256':digest(result.stdout),'stderr_sha256':digest(result.stderr),'reported_version':result.stdout.decode('utf8').strip()}
(OUT/'tool_versions.json').write_bytes((json.dumps(versions,indent=2,sort_keys=True)+'\n').encode())
checks={}
for family,expected in [('koroviev','83123ff485c6261a234d7b010774c7555a17196c65e8ab37fb14cbc42c187fb8'),('planning','e72493704da8eea71875646e5968871c8174ecae154a1f9a7a2c95660434b396')]:
 p=OUT.parent/family/'receipt.json';assert digest(p.read_bytes())==expected
 d=json.loads(p.read_bytes());verified=[]
 entries=d['artifacts']
 pairs=entries.items() if isinstance(entries,dict) else ((item['path'],{k:item[k] for k in ('sha256','size_bytes')}) for item in entries)
 for rel,pin in pairs:
  assert record(ROOT/rel)==pin,rel
  verified.append(rel)
 checks[family]={'receipt_sha256':expected,'unchanged_sealed_artifacts':len(verified)}
nav=json.loads((OUT/'command_navigation.json').read_bytes())
for change in nav['changes']:
 before=(ROOT/change['before_path']).read_bytes();after=(ROOT/change['path']).read_bytes()
 assert digest(before)==change['before_sha256'] and digest(after)==change['after_sha256']
 assert before.replace(nav['old_module'].encode(),nav['new_module'].encode())==after
registry=ROOT/'omega_engine_product_planning_office/plans/epics/epic_relevance_5_prior_art.yaml'
assert digest(registry.read_bytes())=='995ca04f8ef001c50f8816051f263b16cfa8b6a0223b59ba07ddfcc9dc2e28cf'
comparisons=[]
for stem,key in [('epic_obstruction_walk','epics'),('prior_art_epic_map','prior_epic_inventory')]:
 base='omega_engine_product_planning_office/receipts/'
 oldrel=base+stem+'_20261010_oewas002_successor.json';newrel=base+stem+'_20261010_oewas007_integrated_ic_successor.json';old=load(oldrel);new=load(newrel)
 assert new['immediate_predecessor']['sha256']==digest((ROOT/oldrel).read_bytes())
 delta={r['path'] for r in new['successor_review']['changed_inventory_rows']}; unchanged=0
 for a,b in zip(old[key],new[key],strict=True):
  assert a['path']==b['path']
  if a['path'] not in delta:assert a==b;unchanged+=1
  for f in ('base_sha256','predecessor_sha256'):
   if f in a:assert a[f]==b[f]
 for f in old:
  if f not in {key,'immediate_predecessor','successor_review'}:assert old[f]==new[f]
 if key=='epics':
  p='omega_engine_product_planning_office/plans/epics/oewas/epic_oe_oewas_002_planar_tree_substitution_and_workflow_dag_plan.md'
  assert next(r for r in old[key] if r['path']==p)==next(r for r in new[key] if r['path']==p)
 comparisons.append({'successor':newrel,**record(ROOT/newrel),'changed_rows':len(delta),'unchanged_rows':unchanged,'all_original_base_and_source_metadata_preserved':True,'upstream002_row_unchanged':True})
(OUT/'integrated_custody_comparison.json').write_bytes((json.dumps({'authority_effect':'None','earlier_seals':checks,'registry_sha256':digest(registry.read_bytes()),'navigation_changes_are_exact_module_replacements':True,'successors':comparisons},indent=2,sort_keys=True)+'\n').encode())
labels=['integrated_manifest','integrated_planning','integrated_historical','integrated_cli','integrated_versions','integrated_ruff','integrated_markdownlint']
for label in labels:
 d=json.loads((OUT/(label+'.json')).read_bytes());assert d['exit_code']==0
 assert not set(d['changed_inputs'])-set(d['allowed_changed_inputs'])
 for stream in ('stdout','stderr'):assert digest((OUT/(label+'.'+stream+'.log')).read_bytes())==d[stream+'_sha256']
final=json.loads((OUT/'integrated_planning.json').read_bytes())
for rel,pin in final['source_pins_after'].items():assert record(ROOT/rel)==pin,rel
inventory=ROOT/'_ic/odni/migrations/oewas007/inventory.json';assert digest(inventory.read_bytes())=='1f992ce4ec935b7a774fad256332435a948a41fb14492f1036265d15a31e5ca5'
review='''# OEWAS007 integrated planning and historical-source review

**AuthorityEffect:** None. **Scope:** canonical development migration planning and finite prior-art navigation controls; full OEWAS007/009 research and native-admission obligations remain `RESEARCH_HOLD`.

The current main002 planning successor is the immediate predecessor. Its OEWAS002 row, original research/source pins and all unchanged inventory rows are retained. The earlier opt-in and default-IC007 receipts remain byte-exact. Thirty-two epic documents and the index change only the executable audit module path; their exact before bytes and replacement ledger are preserved. Three earlier OEOS link repairs are separately identified.007/009 describe the implemented bounded slice without promoting full acceptance.

The real data relocation exposed one missing legacy PDF in the unchanged880-row registry. The first integrated planning batch recorded98PASS/1FAIL. A domain historical-source port and thin filesystem composition now reuse the existing strict portable reader. Only missing contained `_intelligence/` sources invoke it; unlisted locators, malformed or transplanted bindings, unavailable matching bytes and escaping results refuse. No outward storage import is added to the use case and no replacement source registry is invented.

Actual evidence is retained: focused new-port RED1FAIL then minimal GREEN1PASS on the same initial test bytes;18 expanded controls; three production guard mutants killed and exactly restored; final fresh18PASS0.65s. The final three-file planning replay passes99 cases in62.23s with no source drift. The actual filesystem-composed CLI reports880 registry rows,15 assigned systems and32 epics. Required manifest generation reports61 epics/0 source snapshots. Scoped F/I Ruff and Markdownlint over38 current documents pass. Exact commands, versions, exits, raw outputs and before/after pins are linked by `receipt.json`.

Earlier genuine refusals remain visible: stale planning pins, exact-status manifest cardinality, missing historical PDF, the first new-port RED and a capture-script error with retained raw output. They are not rewritten as successful executions. The final manifest content-set digest is `f78fc95e77f395ef0c6cd1209aae3fe74a1bb98daf6a53cf878c0456a248e758`.

The original6672-file executor cutover and five-file upstream inclusion are different evidence. Final inventory is6677 files/236594766 bytes, source revision `d47c98402a42fd189acd7cf6ccd23d7a0d09c120`, SHA256 `1f992ce4ec935b7a774fad256332435a948a41fb14492f1036265d15a31e5ca5`. Parent execution ledgers own raw source/canonical/snapshot parity; they do not become a public-executor replay of the amended set. Root separately owns the staged/committed Git-blob oracle. This review does not claim that index check has run, broader producer/native parity, arbitrary future-estate automation, power-loss durability, external exactly-once effects, authentication, detector admission or scientific-source verification.
'''
# Keep human-facing custody readable without changing its evidence numbers.
for a,b in [('identified.007','identified. 007'),('unchanged880','unchanged 880'),('recorded98','recorded 98'),('RED1FAIL','RED 1FAIL'),('GREEN1PASS','GREEN 1PASS'),('bytes;18','bytes; 18'),('fresh18PASS','fresh 18PASS'),('passes99','passes 99'),('in62.23','in 62.23'),('reports880','reports 880'),('rows,15','rows, 15'),('and32','and 32'),('reports61','reports 61'),('over38','over 38'),('original6672','original 6672'),('is6677','is 6677')]:review=review.replace(a,b)
(OUT/'review.md').write_bytes(review.encode())
artifacts={p.relative_to(ROOT).as_posix():record(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='receipt.json'}
# Preserve nested predecessor receipt snapshots too; only this exact receipt is excluded.
for p in sorted(OUT.rglob('receipt.json')):
 if p!=OUT/'receipt.json':artifacts[p.relative_to(ROOT).as_posix()]=record(p)
receipt={'schema':'oewas007.planning.integrated-ic.v1','authority_effect':'None','work_base_revision':'4d207641277ef3d3af16e11aafb411ada1ee10ed','integrated_main_revision':'d47c98402a42fd189acd7cf6ccd23d7a0d09c120','status':'PASS_BOUNDED','full_epic_status':'RESEARCH_HOLD','certifies_scientific_sources':False,'certifies_full_producer_or_native_parity':False,'certifies_staged_git_blob_parity':False,'earlier_seals_unchanged':checks,'final_commands':{label:record(OUT/(label+'.json')) for label in labels},'actual_controls':{'planning_cases':99,'historical_reader_cases':18,'production_mutants_killed_then_restored':3,'cli_registry_rows':880,'cli_direct_systems':15,'cli_epics':32,'manifest_epics':61,'manifest_source_snapshots':0,'markdown_documents':38},'source_pins':final['source_pins_after'],'final_inventory':{'path':inventory.relative_to(ROOT).as_posix(),**record(inventory),'files':6677,'source_revision':'d47c98402a42fd189acd7cf6ccd23d7a0d09c120','scope':'Original executor cutover plus separately recorded five-file upstream amendment; raw-blob parity and final index check owned by parent receipts.'},'artifacts':artifacts,'claim_ceiling':'Finite source/navigation and portable-byte controls; no full automation/native admission/scientific theorem or independent authenticity claim.'}
(OUT/'receipt.json').write_bytes((json.dumps(receipt,indent=2,sort_keys=True)+'\n').encode());print(json.dumps({'receipt':record(OUT/'receipt.json'),'review':record(OUT/'review.md'),'artifact_count':len(artifacts),'successors':comparisons},indent=2))
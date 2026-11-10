"""Synthetic custody controls; historical files and Git objects are not read."""
import sys,os,json,hashlib,importlib.util,datetime,contextlib,io
from pathlib import Path
sys.dont_write_bytecode=True
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
import additional_paper_011_core_audit as a
code=a.ROOT/'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code'
temp=a.file('_custody_temp_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'));temp.mkdir()
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
test=load('paper011_custody_control_tests',code/'tests/test_paper011_source_custody.py')
paper=temp/'copies';paper.mkdir();paper,manifest,pin=test.snapshot.__wrapped__(paper)
custody=test.custody;entry=manifest['entries'][0]
other=b'different content in the pinned Git tree'
entry['git_blob_oid']=hashlib.sha1(b'blob '+str(len(other)).encode()+b'\0'+other).hexdigest()
pin=test.write_manifest(paper,manifest)
source=temp/'source';target=source/entry['source_path'];target.parent.mkdir(parents=True);data=(paper/entry['copy_path']).read_bytes();target.write_bytes(data)
actual_blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
custody.tracked_sources=lambda *args:{entry['source_path']:(entry['git_mode'],entry['git_blob_oid'])}
got=custody.verify_source_copies(paper,expected_manifest_sha256=pin,source_repo=source)
assert got['status']=='VERIFIED_BYTE_COPIES' and got['source_inventory_checked'] is True and actual_blob!=entry['git_blob_oid']
tests=load('paper011_findings_control_tests',code/'tests/test_paper011_findings_audit.py')
f=temp/'findings';f.mkdir();p,s,inventory=tests.fixture.__wrapped__(f);inventory['aggregate_demo_families'].append(dict(inventory['aggregate_demo_families'][0]))
observed=tests.auditor.audit(p,s,tests.write(p,inventory));assert observed['aggregate_families']==13
result={'method':'Read-vetted modules with independently constructed synthetic bytes. Git inventory lookup is replaced by explicit pinned-tree metadata; no Git objects, historical source or provider accessed.','checks':[{'rule':'git_metadata_does_not_bind_captured_bytes','status':'observed','verdict':got['status'],'source_inventory_checked':got['source_inventory_checked'],'declared_git_blob_oid':entry['git_blob_oid'],'actual_captured_git_blob_oid':actual_blob,'limits':'The mocked lookup returns metadata for different bytes; all source/copy SHA256 and trusted manifest pin agree. Demonstrates absent bridge, not an incorrect real Git executable.'},{'rule':'aggregate_families_accepts_duplicate_rows','status':'observed','rows':len(inventory['aggregate_demo_families']),'reported_families':observed['aggregate_families'],'verdict':observed['status'],'limits':'Inventory pin is recomputed for synthetic input. No bypass of an independently fixed external pin.'}]}
a.write('_custody_probes.json',result)
config=a.file('_pytest.ini');config.write_text('[pytest]\n',encoding='utf8')
import pytest
output=io.StringIO()
with contextlib.redirect_stdout(output),contextlib.redirect_stderr(output):
    status=pytest.main(['-q','-c',str(config),'--noconftest','-p','no:cacheprovider','--basetemp',str(temp/'pytest'),*[str(code/'tests'/n) for n in ['test_paper011_source_custody.py','test_paper011_findings_audit.py','test_paper011_runtime_environment.py']]])
a.file('_custody_pytest.txt').write_text(output.getvalue(),encoding='utf8')
result['pytest']={'exit_code':status,'log':'dag/reviews/additional_paper_011_core_custody_pytest.txt','scope':'Three fully read synthetic-only test modules, no conftest or plugin autoload; temp files confined to this review prefix.'}
a.write('_custody_probes.json',result)
print(json.dumps({'checks':len(result['checks']),'pytest_exit':status,'pytest_output':output.getvalue()}))

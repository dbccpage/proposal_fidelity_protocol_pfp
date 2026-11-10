"""Direct-owner finite probes and Python wire comparison; cached dependencies only."""
import hashlib
import importlib.util
import importlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
PREFIX='additional_rust_pfp_foundations'
HERE=Path(__file__).parent
deps=ROOT/'code/rust/target/debug/deps'
prior=json.loads((HERE/(PREFIX+'_algorithm_validation.json')).read_text())
libraries={Path(row['path']).name.split('-')[0][3:]:ROOT/row['path'] for row in prior['libraries']}
for name in ['sha2','hex']:
    libraries[name]=max(deps.glob('lib'+name+'-*.rlib'),key=lambda path:path.stat().st_mtime)
source=HERE/(PREFIX+'_foundation_probe.rs')
foundation=ROOT/'code/rust/pfp/src/foundation.rs'
owner_bytes=foundation.read_bytes()
owner_text=owner_bytes.decode('utf-8')
adaptations=[]
for name in ['dda','extension','packet','repair']:
    original='mod '+name+';'
    replacement='#[path = "'+(foundation.parent/'foundation'/f'{name}.rs').as_posix()+'"]\n'+original
    assert owner_text.count(original)==1
    owner_text=owner_text.replace(original,replacement)
    adaptations.append({'original':original,'replacement':replacement})
owner_copy=HERE/(PREFIX+'_foundation_owner.rs')
owner_copy.write_text(owner_text,encoding='utf-8',newline='')
exe=source.with_suffix('.exe')
command=['rustc','--edition=2021','-C','overflow-checks=yes','-L','dependency='+str(deps)]
for name,path in libraries.items(): command+=['--extern',name+'='+str(path)]
command += [str(source),'-o',str(exe)]
built=subprocess.run(command,capture_output=True,text=True,timeout=60)
report={'command':command,'compile_exit':built.returncode,'compile_output':built.stdout+built.stderr,
        'probe_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'foundation_module_path_adapter':{'source':foundation.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(owner_bytes).hexdigest(),'adapter_sha256':hashlib.sha256(owner_copy.read_bytes()).hexdigest(),'changes':adaptations,'limit':'Only explicit module paths added for standalone rustc compilation; all owner function bodies unchanged.'},
        'cached_libraries':[{'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for path in libraries.values()]}
if built.returncode==0:
    executed=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
    report.update(exit_code=executed.returncode,output=executed.stdout+executed.stderr)
    owner=ROOT/'pfp/domain/shared_kernel/canonical.py'
    sys.path.insert(0,str(ROOT))
    module=importlib.import_module('pfp.domain.shared_kernel.canonical')
    comparisons=[]
    for line in executed.stdout.splitlines():
        if not line.startswith('wire:'): continue
        _,name,wire=line.split(':',2)
        try: module.canonical_unwire(json.loads(wire))
        except module.CanonicalizationError as error:
            comparisons.append({'case':name,'native_accepts':True,'python_accepts':False,'python_refusal':str(error)})
        else: comparisons.append({'case':name,'native_accepts':True,'python_accepts':True})
    report.update(python_owner={'path':owner.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(owner.read_bytes()).hexdigest()},comparisons=comparisons)
(HERE/(PREFIX+'_foundation_validation.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in {'command','cached_libraries'}},indent=2))

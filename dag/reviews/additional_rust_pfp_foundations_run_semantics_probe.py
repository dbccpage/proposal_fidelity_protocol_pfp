"""Bounded direct-source probes, existing cached dependency artifacts only."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
PREFIX='additional_rust_pfp_foundations'
deps=ROOT/'code/rust/target/debug/deps'
wire=json.loads((ROOT/f'dag/reviews/{PREFIX}_wire_validation.json').read_text())
libraries={Path(r['path']).name.split('-')[0][3:]:ROOT/r['path'] for r in wire['cached_libraries']}
for name in ['sha2','hex','nalgebra']:
    libraries[name]=max(deps.glob(f'lib{name}-*.rlib'),key=lambda p:p.stat().st_mtime)
source=ROOT/f'dag/reviews/{PREFIX}_semantics_probe.rs'
exe=ROOT/f'dag/reviews/{PREFIX}_semantics_probe.exe'
command=['rustc','--edition=2021','-C','overflow-checks=yes','-L','dependency='+str(deps)]
for name,path in libraries.items():command+=['--extern',name+'='+str(path)]
command += [str(source),'-o',str(exe)]
r=subprocess.run(command,capture_output=True,text=True,timeout=60)
log={'probe_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'command':command,'compile_exit':r.returncode,'compile_output':r.stdout+r.stderr,'libraries':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in libraries.values()]}
if r.returncode==0:
    run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
    log.update(exit_code=run.returncode,output=run.stdout+run.stderr)
(ROOT/f'dag/reviews/{PREFIX}_semantics_validation.json').write_text(json.dumps(log,indent=2)+'\n')
print(json.dumps({k:v for k,v in log.items() if k not in ['command','libraries']},indent=2))

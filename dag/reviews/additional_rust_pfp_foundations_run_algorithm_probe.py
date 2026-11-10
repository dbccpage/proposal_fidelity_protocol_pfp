"""Bounded owner probes using already-installed libraries, no Cargo or network."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PREFIX='additional_rust_pfp_foundations'
deps=ROOT/'code/rust/target/debug/deps'
wire=json.loads((ROOT/f'dag/reviews/{PREFIX}_wire_validation.json').read_text())
libraries={Path(r['path']).name.split('-')[0][3:]:ROOT/r['path'] for r in wire['cached_libraries']}
for name in ['num_bigint','num_rational','num_traits','nalgebra','core_types']:
    libraries[name]=max(deps.glob(f'lib{name}-*.rlib'),key=lambda p:p.stat().st_mtime)
fingerprints=deps.parent/'.fingerprint'
core_name=libraries['core_types'].stem[3:]
core=json.loads((fingerprints/core_name/'lib-core_types.json').read_text())
for name in ['num_bigint','num_rational','num_traits','serde']:
    identity=next(d[3] for d in core['deps'] if d[1]==name)
    for fp in fingerprints.glob(name.replace('_','-')+'-*/lib-'+name):
        if int.from_bytes(bytes.fromhex(fp.read_text()),'little')==identity:
            libraries[name]=deps/('lib'+name+'-'+fp.parent.name.rsplit('-',1)[1]+'.rlib')
            assert libraries[name].exists()
            break
    else:raise RuntimeError('No cached exact dependency '+name)
source=ROOT/f'dag/reviews/{PREFIX}_algorithm_probe.rs'
exe=source.with_suffix('.exe')
command=['rustc','--edition=2021','-C','overflow-checks=yes','-L','dependency='+str(deps)]
for name,path in libraries.items():command+=['--extern',name+'='+str(path)]
command += [str(source),'-o',str(exe)]
attempts=[]
for traits in [libraries['num_traits']]:
    libraries['num_traits']=traits
    command=['rustc','--edition=2021','-C','overflow-checks=yes','-L','dependency='+str(deps)]
    for name,path in libraries.items():command+=['--extern',name+'='+str(path)]
    command += [str(source),'-o',str(exe)]
    r=subprocess.run(command,capture_output=True,text=True,timeout=60)
    attempts.append({'traits':str(traits),'exit':r.returncode,'output':r.stdout+r.stderr})
    if r.returncode==0:break
log={'probe_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'command':command,'compile_exit':r.returncode,'compile_output':r.stdout+r.stderr,'cached_artifact_compatibility_attempts':attempts,'libraries':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in libraries.values()]}
if r.returncode==0:
    run=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
    log.update(exit_code=run.returncode,output=run.stdout+run.stderr)
    unchecked=exe.with_name(exe.stem+'_unchecked.exe')
    command_unchecked=[('overflow-checks=no' if x=='overflow-checks=yes' else str(unchecked) if x==str(exe) else x) for x in command]
    built=subprocess.run(command_unchecked,capture_output=True,text=True,timeout=60)
    release={'command':command_unchecked,'compile_exit':built.returncode,'compile_output':built.stdout+built.stderr}
    if built.returncode==0:
        run=subprocess.run([str(unchecked)],capture_output=True,text=True,timeout=15)
        release.update(exit_code=run.returncode,output=run.stdout+run.stderr)
    log['overflow_unchecked']=release
(ROOT/f'dag/reviews/{PREFIX}_algorithm_validation.json').write_text(json.dumps(log,indent=2)+'\n')
print(json.dumps({k:v for k,v in log.items() if k not in ['command','libraries','cached_artifact_compatibility_attempts']},indent=2))

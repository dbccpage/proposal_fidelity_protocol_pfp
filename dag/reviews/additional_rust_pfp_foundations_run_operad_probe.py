"""Original runtime operad source, with explicit cached-kernel validation limits."""
import pathlib,hashlib,json,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]; HERE=pathlib.Path(__file__).parent; PREFIX='additional_rust_pfp_foundations'
deps=ROOT/'code/rust/target/debug/deps'; fp=deps.parent/'.fingerprint'
def choices(name):
    for p in sorted(fp.glob(name+'-*/lib-'+name+'.json')):
        obj=json.loads(p.read_text()); core=next((x for x in obj['deps'] if x[1]=='serde_core'),None); lib=deps/('lib'+p.parent.name+'.rlib')
        if core and lib.exists():yield lib,core[3]
pair=next(((a,b) for a,x in choices('serde') for b,y in choices('serde_json') if x==y),None);assert pair
libraries={'serde':pair[0],'serde_json':pair[1],'core_operad_theory':max(deps.glob('libcore_operad_theory-*.rlib'),key=lambda p:p.stat().st_mtime)}
source=HERE/(PREFIX+'_operad_probe.rs');exe=HERE/(PREFIX+'_operad_probe.exe')
cmd=['rustc','--edition=2021','-Awarnings','-C','overflow-checks=yes','-L','dependency='+str(deps)]
for n,p in libraries.items():cmd+=['--extern',n+'='+str(p)]
cmd += [str(source),'-o',str(exe)]
built=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
log={'source_path':'code/rust/pfp_runtime/src/operad.rs','source_sha256':hashlib.sha256((ROOT/'code/rust/pfp_runtime/src/operad.rs').read_bytes()).hexdigest(),'probe_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'libraries':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in libraries.values()],'command':cmd,'compile_exit':built.returncode,'compile_output':built.stdout+built.stderr,'limits':'Runtime owner included verbatim. Four local predicate failures do not execute the cached kernel. Tree conversion uses a cached core_operad_theory binary; current kernel terms.rs source was separately checked for flattened-leaf substitution semantics, but no full rebuild/source-binary equivalence is claimed.'}
if built.returncode==0:
    ran=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15);log.update(exit_code=ran.returncode,output=ran.stdout+ran.stderr)
(HERE/(PREFIX+'_operad_validation.json')).write_text(json.dumps(log,indent=2)+'\n')
print(json.dumps(log,indent=2))

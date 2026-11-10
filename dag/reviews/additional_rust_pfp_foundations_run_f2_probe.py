"""Bounded direct-source F2 validation, cached libraries only; no Cargo invocation."""
import hashlib,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]
HERE=pathlib.Path(__file__).parent
PREFIX='additional_rust_pfp_foundations'
deps=ROOT/'code/rust/target/debug/deps'
fp=deps.parent/'.fingerprint'
def choices(name):
    for p in sorted(fp.glob(name+'-*/lib-'+name+'.json')):
        obj=json.loads(p.read_text()); core=next((x for x in obj['deps'] if x[1]=='serde_core'),None)
        lib=deps/('lib'+p.parent.name+'.rlib')
        if core and lib.exists(): yield lib,core[3]
pair=next(((a,b) for a,x in choices('serde') for b,y in choices('serde_json') if x==y),None)
assert pair,'No compatible cached libraries; do not download.'
err=max(deps.glob('libthiserror-*.rlib'),key=lambda p:p.stat().st_mtime)
source=HERE/(PREFIX+'_f2_probe.rs')
base=['rustc','--edition=2021','-Awarnings','-L','dependency='+str(deps),'--extern','serde='+str(pair[0]),'--extern','serde_json='+str(pair[1]),'--extern','thiserror='+str(err),str(source)]
log={'source_path':'code/rust/pfp_runtime/src/f2.rs','source_sha256':hashlib.sha256((ROOT/'code/rust/pfp_runtime/src/f2.rs').read_bytes()).hexdigest(),'probe_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'libraries':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (*pair,err)],'runs':[]}
for mode in ['yes','no']:
    exe=HERE/(PREFIX+'_f2_'+mode+'.exe')
    cmd=base+['-C','overflow-checks='+mode,'-o',str(exe)]
    built=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
    row={'command':cmd,'overflow_checks':mode,'compile_exit':built.returncode,'compile_output':built.stdout+built.stderr}
    if built.returncode==0:
        ran=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
        row.update(exit_code=ran.returncode,output=ran.stdout+ran.stderr)
    log['runs'].append(row)
(HERE/(PREFIX+'_f2_validation.json')).write_text(json.dumps(log,indent=2)+'\n')
print(json.dumps(log['runs'],indent=2))

"""Bounded source-inclusion probe; uses existing compatible cached libraries only."""
import hashlib
import json
import pathlib
import subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]
PREFIX='additional_rust_pfp_foundations'
def main():
    deps=ROOT/'code/rust/target/debug/deps'; fingerprints=ROOT/'code/rust/target/debug/.fingerprint'
    def choices(name):
        out=[]
        for path in sorted(fingerprints.glob(name+'-*/lib-'+name+'.json')):
            item=json.loads(path.read_text())
            core=next((x for x in item['deps'] if x[1]=='serde_core'),None)
            lib=deps/('lib'+path.parent.name+'.rlib')
            if core and lib.exists(): out.append((lib,core[3]))
        return out
    pair=next(((a,b) for a,x in choices('serde') for b,y in choices('serde_json') if x==y),None)
    assert pair,'No compatible cached serde pair; no download permitted.'
    err=max(deps.glob('libthiserror-*.rlib'),key=lambda p:p.stat().st_mtime)
    libraries=[*pair,err]
    source=ROOT/('dag/reviews/'+PREFIX+'_wire_probe.rs')
    base=['rustc','--edition=2021','-L','dependency='+str(deps),'--extern','serde='+str(pair[0]),'--extern','serde_json='+str(pair[1]),'--extern','thiserror='+str(err),str(source)]
    log={'probe_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'cached_libraries':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in libraries],'runs':[], 'initial_attempt':'Latest serde/json pair failed compilation with different serde_core artifact identities. Compatible libraries selected by fingerprint dependency identity; no product defect attributed to setup failure.'}
    for checks in ['yes','no']:
        exe=ROOT/('dag/reviews/'+PREFIX+'_wire_'+checks+'.exe')
        command=base+['-C','overflow-checks='+checks,'-o',str(exe)]
        result=subprocess.run(command,capture_output=True,text=True,timeout=45)
        row={'overflow_checks':checks,'command':command,'compile_exit':result.returncode,'compile_output':result.stdout+result.stderr}
        if result.returncode==0:
            executed=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
            row.update(exit_code=executed.returncode,output=executed.stdout+executed.stderr)
        log['runs'].append(row)
    (ROOT/('dag/reviews/'+PREFIX+'_wire_validation.json')).write_text(json.dumps(log,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([{'overflow_checks':r['overflow_checks'],'compile_exit':r['compile_exit'],'exit_code':r.get('exit_code'),'output':r.get('output',r['compile_output'])} for r in log['runs']],indent=2))
if __name__=='__main__': main()

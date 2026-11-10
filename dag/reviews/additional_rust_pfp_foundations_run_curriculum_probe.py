"""One direct-source counterexample; no crate build or downloads."""
import pathlib,hashlib,json,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]; HERE=pathlib.Path(__file__).parent; PREFIX='additional_rust_pfp_foundations'
deps=ROOT/'code/rust/target/debug/deps'
libraries={name:max(deps.glob('lib'+name+'-*.rlib'),key=lambda p:p.stat().st_mtime) for name in ['serde','sha2','hex','thiserror']}
source=HERE/(PREFIX+'_curriculum_probe.rs'); exe=HERE/(PREFIX+'_curriculum_probe.exe')
cmd=['rustc','--edition=2021','-Awarnings','-C','overflow-checks=yes','-L','dependency='+str(deps)]
for name,p in libraries.items():cmd+=['--extern',name+'='+str(p)]
cmd += [str(source),'-o',str(exe)]
ran=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
log={'source_path':'code/rust/pfp_runtime/src/curriculum.rs','source_sha256':hashlib.sha256((ROOT/'code/rust/pfp_runtime/src/curriculum.rs').read_bytes()).hexdigest(),'probe_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'libraries':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in libraries.values()],'command':cmd,'compile_exit':ran.returncode,'compile_output':ran.stdout+ran.stderr}
if ran.returncode==0:
    result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15);log.update(exit_code=result.returncode,output=result.stdout+result.stderr)
(HERE/(PREFIX+'_curriculum_validation.json')).write_text(json.dumps(log,indent=2)+'\n')
print(json.dumps(log,indent=2))

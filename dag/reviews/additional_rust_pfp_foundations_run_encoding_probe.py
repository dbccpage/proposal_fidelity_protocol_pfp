"""Exact owner encoding probes using cached dependencies only."""
import json,pathlib,hashlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=pathlib.Path(__file__).parent;P='additional_rust_pfp_foundations';deps=ROOT/'code/rust/target/debug/deps'
prior=json.loads((HERE/(P+'_f2_validation.json')).read_text());libs={}
for x in prior['libraries']:
 q=ROOT/x['path']; name=q.name[3:].split('-')[0];libs[name]=q
libs['sha2']=max(deps.glob('libsha2-*.rlib'),key=lambda p:p.stat().st_mtime)
owner=ROOT/'code/rust/core_contracts/src/improvement_canonical_json.rs';b64owner=ROOT/'code/rust/core_contracts/src/improvement_types.rs'
b64=''.join(b64owner.read_text(encoding='utf-8').splitlines(keepends=True)[530:570]);assert b64.lstrip().startswith('fn b64_decode(')
source=HERE/(P+'_encoding_probe.rs');source.write_text('#[path='+json.dumps(owner.as_posix())+'] mod canonical;\n'+b64+'''
fn main(){
 for n in [f64::NAN,f64::INFINITY,f64::NEG_INFINITY] { let result=canonical::dumps_canonical_v1(&n).unwrap(); assert_eq!(result,b"null"); }
 assert!(canonical::dumps_canonical_v1(&1.5f64).is_err());
 assert_eq!(canonical::hash_canonical_v1(&f64::NAN).unwrap(),canonical::hash_canonical_v1(&Option::<u8>::None).unwrap());
 println!("three_nonfinite_floats_accepted_as_null=true; finite_float_refused=true");
 for s in ["AA=A","AB==","AA==AAAA"] {let result=b64_decode(s).unwrap();println!("invalid_or_noncanonical_base64_accepted={s}:{result:?}");}
}
''',encoding='utf-8')
exe=source.with_suffix('.exe');cmd=['rustc','--edition=2021','-Awarnings','-L','dependency='+str(deps)]
for name,q in libs.items():cmd+=['--extern',name+'='+str(q)]
cmd+=[str(source),'-o',str(exe)];r=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
log={'source_files':[{'path':q.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in [owner,b64owner]],'b64_extracted_lines':[531,570],'b64_function_sha256':hashlib.sha256(b64.encode()).hexdigest(),'probe_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'libraries':[{'path':q.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in libs.values()],'command':cmd,'compile_exit':r.returncode,'compile_output':r.stdout+r.stderr,'limits':'Canonical JSON owner included verbatim; base64 decoder complete original function extracted without changes. No full-crate compile, provider or source mutation.'}
if not r.returncode:
 q=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15);log.update(exit_code=q.returncode,output=q.stdout+q.stderr)
(HERE/(P+'_encoding_validation.json')).write_text(json.dumps(log,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:log[k] for k in ['compile_exit','compile_output','exit_code','output'] if k in log},indent=2))

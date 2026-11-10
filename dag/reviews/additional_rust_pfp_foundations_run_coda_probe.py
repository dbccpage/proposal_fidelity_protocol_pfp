"""Bounded unchanged CODA source probe; no dispatch or external effects."""
import hashlib,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]
HERE=pathlib.Path(__file__).parent
P='additional_rust_pfp_foundations'
deps=ROOT/'code/rust/target/debug/deps'
prior=json.loads((HERE/(P+'_f2_validation.json')).read_text())
libs={pathlib.Path(x['path']).name[3:].split('-')[0]:ROOT/x['path'] for x in prior['libraries']}
for name in ['core_pipelines','core_policy','core_solvers','core_types','pfp_runtime','num_bigint','num_rational','num_traits']:
    libs[name]=max(deps.glob('lib'+name+'-*.rlib'),key=lambda p:p.stat().st_mtime)
fingerprints=deps.parent/'.fingerprint'
parent=max(deps.glob('libpfp-*.rlib'),key=lambda p:p.stat().st_mtime)
fingerprint=json.loads((fingerprints/parent.stem[3:]/'lib-pfp.json').read_text())
for name in list(libs):
    identity=next((d[3] for d in fingerprint['deps'] if d[1]==name),None)
    if identity is None: continue
    for fp in fingerprints.glob('*/lib-'+name):
        if int.from_bytes(bytes.fromhex(fp.read_text()),'little')==identity:
            libs[name]=deps/('lib'+name+'-'+fp.parent.name.rsplit('-',1)[1]+'.rlib')
            break
owner=ROOT/'code/rust/pfp/src/coda.rs'
src=HERE/(P+'_coda_probe.rs')
src.write_text('mod protocol { pub fn canonical_json(v: &serde_json::Value)->Vec<u8>{serde_json::to_vec(v).unwrap()} }\n#[path='+json.dumps(owner.as_posix())+'] mod coda;\n'+r'''
fn main(){
 use num_bigint::BigInt; use num_rational::BigRational; use num_traits::ToPrimitive;
 let q=|x:i64| BigRational::from_integer(BigInt::from(x));
 let d0=vec![vec![q(2)],vec![q(3)]];
 let target=vec![q(0),q(1)];
 let cert=core_solvers::solver_cohomology_simplicial_l1::solve_l1_quotient(&d0,&target).unwrap();
 assert_eq!(cert.distance,BigRational::new(BigInt::from(2),BigInt::from(3)));
 assert_eq!(cert.distance.to_u64(),Some(0));
 let payload=serde_json::json!({"input_id":"synthetic-fractional-distance","sieve_non_empty":true,"refinement_consistent":true,"gluing_succeeded":true,"phi1_distance":0,"gamma2_distance":0,"license_granted":false,"matrices":{"d0":[[2],[3]],"d1":[],"cochain":[0,1]}});
 let receipt=coda::evaluate_coda(&payload).unwrap();
 println!("exact_distance={}; truncated_distance=0; accepted_receipt={}",cert.distance,serde_json::to_string(&receipt).unwrap());
}
''',encoding='utf-8')
exe=HERE/(P+'_coda_probe.exe')
cmd=['rustc','--edition=2021','-Awarnings','-L','dependency='+str(deps)]
for name,path in libs.items(): cmd+=['--extern',name+'='+str(path)]
cmd +=[str(src),'-o',str(exe)]
c=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
run={'command':cmd,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
if c.returncode==0:
 r=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
 run.update(exit_code=r.returncode,output=r.stdout+r.stderr)
receipt={'source_files':[{'path':owner.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(owner.read_bytes()).hexdigest()}],'libraries':[{'path':q.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(q.read_bytes()).hexdigest()}for q in libs.values()],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'runs':[run],'limits':'Unchanged CODA source and cached solver libraries. Only canonical JSON helper shimmed using serde serialization; distance path unmodified. In-memory two-coordinate rational optimization; no provider, filesystem dispatch or private input.'}
receipt_path=HERE/(P+'_coda_validation.json')
if receipt_path.exists():
 old=json.loads(receipt_path.read_text())
 receipt['previous_attempts']=old.get('previous_attempts',[])+old['runs']
receipt_path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in run.items() if k!='command'},indent=2))

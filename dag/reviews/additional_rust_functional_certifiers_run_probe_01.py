"""Offline tiny exact-LP and floating diagnostic probes against unchanged source."""
import hashlib,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=pathlib.Path(__file__).parent
P='additional_rust_functional_certifiers';deps=ROOT/'code/rust/target/debug/deps';fp=deps.parent/'.fingerprint'
# Cargo fingerprint metadata is read only; no build scripts or downloads.
prior=json.loads((HERE/'additional_rust_pfp_foundations_final_validation.json').read_text())
libs={pathlib.Path(x['path']).name[3:].split('-')[0]:ROOT/x['path']for x in prior['libraries']}
def resolve(name,owner):
 tag=libs[owner].stem.removeprefix('lib')
 metadata=json.loads((fp/tag/('lib-'+owner+'.json')).read_text())
 identity=next(x[3]for x in metadata['deps']if x[1]==name)
 matches=[p for p in fp.glob('*/lib-'+name)if int.from_bytes(bytes.fromhex(p.read_text()),'little')==identity]
 assert len(matches)==1,(name,matches)
 libs[name]=deps/('lib'+name+'-'+matches[0].parent.name.rsplit('-',1)[1]+'.rlib')
resolve('core_kernel','pfp');resolve('nalgebra','core_functional')
owners={
 'phi1':ROOT/'code/rust/core_functional/src/phi1.rs',
 'binary_degree':ROOT/'code/rust/core_functional/src/binary_degree.rs',
 'phi1_certifier':ROOT/'code/rust/core_certifiers/src/phi1_certifier.rs',
}
head=''.join('#[path='+json.dumps(p.as_posix())+'] pub mod '+n+';\n'for n,p in owners.items())
src=HERE/(P+'_probe_01.rs')
src.write_text(head+r'''
fn main(){
 use num_rational::BigRational as Q;
 let one=Q::from_integer(1.into());let raw=Q::new_raw(1.into(),0.into());
 let outcome=std::panic::catch_unwind(||phi1_certifier::Phi1Verifier::verify([one.clone()],[one.clone()],[vec![raw]],[one.clone()],[one.clone()]));
 println!("generic_lp_raw_denominator_panics={}",outcome.is_err());
 if let Ok(value)=outcome {println!("generic_lp_raw_denominator_result={:?}",value);}
 let d=nalgebra::DMatrix::from_row_slice(2,1,&[f64::MAX,f64::MAX]);
 let omega=nalgebra::DVector::from_vec(vec![0.0,0.0]);
 let alpha=nalgebra::DVector::from_vec(vec![0.0]);
 let dual=nalgebra::DVector::from_vec(vec![f64::MAX,-f64::MAX]);
 let boundary=d.transpose()*&dual;assert!(boundary[0].is_nan());
 let result=phi1::Phi1Functional::diagnose_primal_dual(&d,&omega,&alpha,&dual).unwrap();
 assert_eq!(result.dual_boundary_defect,0.0);
 println!("nan_boundary_reported_as_zero_defect=true");
 let invalid=Q::new_raw(1.into(),0.into());
 assert_eq!(phi1::Phi1Functional::unweighted_l1_rational(&[invalid]),None);
 println!("full_phi1_denominator_guard_control=true");
}
''',encoding='utf-8')
base=['rustc','--edition=2021','-Awarnings','-L','dependency='+str(deps)]
for name,path in libs.items():base+=['--extern',name+'='+str(path)]
runs=[]
for mode in ['yes','no']:
 exe=HERE/(P+'_probe_01_'+mode+'.exe');cmd=base+['-C','overflow-checks='+mode,str(src),'-o',str(exe)]
 c=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
 r={'command':cmd,'overflow_checks':mode,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
 if c.returncode==0:
  x=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15);r.update(exit_code=x.returncode,output=x.stdout+x.stderr)
 runs.append(r)
receipt={'source_files':[{'path':x.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(x.read_bytes()).hexdigest()}for x in owners.values()],'libraries':[{'path':x.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(x.read_bytes()).hexdigest()}for x in libs.values()],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'runs':runs,'limits':'Complete unchanged source modules with cached offline dependencies. Synthetic in-memory public inputs only; no full suite or authority claim.'}
(HERE/(P+'_validation_01.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items()if k!='command'}for r in runs],indent=2))

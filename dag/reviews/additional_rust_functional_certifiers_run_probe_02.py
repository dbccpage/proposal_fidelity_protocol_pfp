"""Offline direct-source malformed-native/serde diagnostic controls."""
import hashlib,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=pathlib.Path(__file__).parent;P='additional_rust_functional_certifiers'
prior=json.loads((HERE/(P+'_validation_01.json')).read_text())
libs={pathlib.Path(r['path']).name[3:].split('-')[0]:ROOT/r['path']for r in prior['libraries']}
owners={n:ROOT/('code/rust/core_functional/src/'+n+'.rs')for n in ['phi1','binary_degree','weighted_l1_norm','residual']}
src=HERE/(P+'_probe_02.rs')
head=''.join('#[path='+json.dumps(p.as_posix())+'] pub mod '+n+';\n'for n,p in owners.items())
src.write_text(head+r'''
pub use phi1::Phi1Functional;
fn main(){
 use weighted_l1_norm::WeightedL1Norm;
 let negative:WeightedL1Norm=serde_json::from_str(r#"{"weights":[-1.0]}"#).unwrap();
 assert_eq!(negative.evaluate(&[1.0]).unwrap(),-1.0);
 assert!(WeightedL1Norm::new(vec![-1.0]).is_err());
 let good=WeightedL1Norm::new(vec![2.0]).unwrap();
 assert!(good.evaluate(&[f64::NAN]).unwrap().is_nan());
 assert!(good.evaluate(&[f64::MAX]).unwrap().is_infinite());
 println!("weighted_norm_wire_bypass_negative=true;nan_and_finite_overflow_are_ok=true");
 let bad=core_kernel::exact::Exact::new_raw(1.into(),0.into());
 let result=std::panic::catch_unwind(||residual::Residual::new(vec![bad]));
 assert!(result.is_err());
 assert!(serde_json::from_str::<residual::Residual>(r#"{"vector":["1/0"],"l1":"0"}"#).is_err());
 println!("residual_native_raw_denominator_panics=true;wire_guard_control=true");
}
''',encoding='utf-8')
base=['rustc','--edition=2021','-Awarnings','-L','dependency='+str(ROOT/'code/rust/target/debug/deps')]
for name,path in libs.items():base+=['--extern',name+'='+str(path)]
runs=[]
for mode in ['yes','no']:
 exe=HERE/(P+'_probe_02_'+mode+'.exe');cmd=base+['-C','overflow-checks='+mode,str(src),'-o',str(exe)]
 c=subprocess.run(cmd,capture_output=True,text=True,timeout=45);r={'command':cmd,'overflow_checks':mode,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
 if c.returncode==0:
  x=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15);r.update(exit_code=x.returncode,output=x.stdout+x.stderr)
 runs.append(r)
receipt={'source_files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in owners.values()],'libraries':prior['libraries'],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'runs':runs,'limits':'Unchanged owner source, hash-pinned cached offline dependencies. Synthetic inputs and caught expected panic; not full suite or exact-certificate/authority exploit.'}
(HERE/(P+'_validation_02.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items()if k!='command'}for r in runs],indent=2))

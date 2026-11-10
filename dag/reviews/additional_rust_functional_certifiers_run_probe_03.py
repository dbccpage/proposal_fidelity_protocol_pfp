"""Offline native boundary probes for higher-degree certificates and helpers."""
import hashlib,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=pathlib.Path(__file__).parent;P='additional_rust_functional_certifiers'
prior=json.loads((HERE/(P+'_validation_01.json')).read_text());libs={pathlib.Path(r['path']).name[3:].split('-')[0]:ROOT/r['path']for r in prior['libraries']}
owners={n:ROOT/('code/rust/core_functional/src/'+n+'.rs')for n in ['phi1','binary_degree','gamma2','wire','phi2','phi3','phi4','residual_splitting','observer_gauge']}
src=HERE/(P+'_probe_03.rs');head=''.join('#[path='+json.dumps(p.as_posix())+'] pub mod '+n+';\n'for n,p in owners.items())
src.write_text(head+r'''
pub use phi1::Phi1Functional;
fn q(n:i64)->num_rational::BigRational{num_rational::BigRational::from_integer(n.into())}
fn main(){
 let out=std::panic::catch_unwind(||residual_splitting::splitting_from_parameter(&[vec![q(1),q(1)]],&[vec![]],&[vec![q(1)]],&[vec![],vec![]]));
 assert!(out.is_err());println!("splitting_wide_basis_panics=true");
 use observer_gauge::{ObserverGauge,ScalarGauge,VectorGauge,TraceGauge};
 assert!(ScalarGauge::new(vec![-1.0]).is_err());
 assert_eq!((ScalarGauge{weights:vec![-1.0]}).evaluate(&[1.0]).unwrap(),-1.0);
 assert_eq!((VectorGauge{weights:vec![-1.0]}).evaluate(&[vec![1.0]]).unwrap(),-1.0);
 assert_eq!((TraceGauge{weights:vec![-1.0]}).evaluate(&[vec![2.0]]).unwrap(),-1.0);
 println!("all_three_observer_gauges_accept_negative_weights=true");
 let bad=num_rational::BigRational::new_raw(1.into(),0.into());
 assert!(std::panic::catch_unwind(||observer_gauge::rational_squared_l2(&[bad.clone()])).is_err());
 assert!(std::panic::catch_unwind(||phi3::Phi3Functional::evaluate_bianchi_defect(&[vec![bad.clone()]],&[q(1)],&[q(1)])).is_err());
 assert!(phi4::Phi4Functional::evaluate_curvature_defect(&[vec![bad]],&[q(1)],None).is_err());
 println!("unguarded_squared_l2_and_phi3_bianchi_panics=true;phi4_guard_control=true");
 let c2=phi2::ExactPhi2Certificate{flux_b:vec![q(0)],d1:vec![vec![q(0)]],d0:None,weights:vec![q(1)],potential_a:vec![q(0)],primal_residual:vec![q(0)],dual_witness:vec![q(0)],reported_value:q(0)};
 assert!(phi2::Phi2Functional::verify_exact_certificate(c2.clone()).is_ok());
 assert!(serde_json::from_str::<phi2::ExactPhi2Certificate>(&serde_json::to_string(&c2).unwrap()).is_err());
 let c3=phi3::ExactPhi3Certificate{flux_h:vec![q(0)],d2:vec![vec![q(0)]],d1:None,d0:None,weights:vec![q(1)],potential_b:vec![q(0)],primal_residual:vec![q(0)],dual_witness:vec![q(0)],reported_value:q(0)};
 assert!(phi3::Phi3Functional::verify_exact_certificate(c3.clone()).is_ok());
 assert!(serde_json::from_str::<phi3::ExactPhi3Certificate>(&serde_json::to_string(&c3).unwrap()).is_err());
 let c4=phi4::ExactPhi4Certificate{flux_g:vec![q(0)],d3:vec![vec![q(0)]],d2:vec![vec![q(0)]],d1:None,d0:None,weights:vec![q(1)],potential_c:vec![q(0)],primal_residual:vec![q(0)],dual_witness:vec![q(0)],reported_value:q(0)};
 assert!(phi4::Phi4Functional::verify_exact_certificate(c4.clone()).is_ok());
 assert!(serde_json::from_str::<phi4::ExactPhi4Certificate>(&serde_json::to_string(&c4).unwrap()).is_err());
 println!("valid_phi2_phi3_phi4_serialize_deserialize_roundtrips_fail=true");
}
''',encoding='utf-8')
base=['rustc','--edition=2021','-Awarnings','-L','dependency='+str(ROOT/'code/rust/target/debug/deps')]
for name,path in libs.items():base+=['--extern',name+'='+str(path)]
runs=[]
for mode in ['yes','no']:
 exe=HERE/(P+'_probe_03_'+mode+'.exe');cmd=base+['-C','overflow-checks='+mode,str(src),'-o',str(exe)]
 c=subprocess.run(cmd,capture_output=True,text=True,timeout=45);r={'command':cmd,'overflow_checks':mode,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
 if c.returncode==0:
  x=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15);r.update(exit_code=x.returncode,output=x.stdout+x.stderr)
 runs.append(r)
receipt={'source_files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in owners.values()],'libraries':prior['libraries'],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'runs':runs,'limits':'Unchanged owner source; cached offline dependencies; synthetic public inputs. Expected panics caught; no full-suite or authority claim.'}
(HERE/(P+'_validation_03.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps([{k:v for k,v in r.items()if k!='command'}for r in runs],indent=2))

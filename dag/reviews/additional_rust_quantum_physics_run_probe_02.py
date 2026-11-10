import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_quantum_physics';D=R/'code/rust/target/debug/deps'
prior=json.loads((H/(P+'_validation_01.json')).read_text());libs={pathlib.Path(x['path']).name[3:].split('-')[0]:R/x['path']for x in prior['libraries']}
owners={pathlib.Path(x['path']).stem:R/x['path']for x in prior['source_files']}
for n in ['dagger_category','frobenius_algebra','classical_structure','local_operator_algebra','algebraic_qft','coherent_interference','cancellation_certificates','heisenberg_picture']:owners[n]=R/('code/rust/core_quantum_physics/src/'+n+'.rs')
src=H/(P+'_probe_02.rs');src.write_text(''.join('#[path='+json.dumps(p.as_posix())+'] pub mod '+n+';\n'for n,p in owners.items())+r'''
use linear_algebra::backend::basic_matrix::BasicMatrix as M;
use linear_algebra::exact_field::matrix as mx;
use core_number_theory::cyclotomic::GaussianRat as G;
use core_number_theory::rational::{ri,Rational};
fn report<T:std::fmt::Debug,F:FnOnce()->T+std::panic::UnwindSafe>(name:&str,f:F){match std::panic::catch_unwind(f){Ok(x)=>println!("{}={:?}",name,x),Err(_)=>println!("{}=PANIC",name)}}
fn main(){
 std::panic::set_hook(Box::new(|_|{}));
 report("frobenius_extreme_shape",||frobenius_algebra::FrobeniusAlgebra::from_trace_form(M::from_row_major(usize::MAX,0,vec![]).unwrap(),M::from_row_major(0,0,vec![]).unwrap(),M::from_row_major(0,0,vec![]).unwrap()));
 let bad=G{re:Rational::new_raw(1.into(),0.into()),im:ri(0)};
 report("classical_bad_scalar",||classical_structure::ClassicalStructure::from_basis(vec![vec![bad.clone()]]));
 report("cayley_bad_scalar",||heisenberg_picture::cayley_jet(&mx::identity(1).unwrap(),&bad.re));
 for d in 1..=3{assert_eq!(dagger_category::DaggerCategory::zigzag(d).unwrap(),mx::identity(d).unwrap());let a=frobenius_algebra::FrobeniusAlgebra::copy(d).unwrap();assert!(a.is_commutative()&&a.is_dagger());assert_eq!(a.special_scalar(),Some(G::from_ints(1,0)));}
 println!("dagger_snake_and_copy_frobenius_dimensions1_3=PASS");
 let net=algebraic_qft::AlgebraicQft::qubit_chain(2).unwrap();assert!(net.defects(true).unwrap().is_empty());println!("two_qubit_net_isotony_locality_duality=PASS");
 let c=[G::from_ints(1,0),G::from_ints(1,0),G::from_ints(0,1)];let twin=coherent_interference::diagonal_twin(&c).unwrap().unwrap();assert_ne!(coherent_interference::interfered_weight(&c).unwrap(),coherent_interference::interfered_weight(&twin.twin).unwrap());
 assert_eq!(coherent_interference::sorkin_interference(&c,&[vec![0],vec![1],vec![2]],8).unwrap(),ri(0));println!("diagonal_twin_and_quadratic_order3_zero=PASS");
 let mut cert=cancellation_certificates::certify_phase_cancellation(3,&[0,1,2]).unwrap().unwrap();assert!(cert.reflected_pairs.is_none());assert!(cancellation_certificates::verify_phase_cancellation(&cert).unwrap());cert.reflected_pairs=Some(vec![(0,1)]);assert!(!cancellation_certificates::verify_phase_cancellation(&cert).unwrap());println!("odd_polygon_cancellation_and_invalid_pairing_refusal=PASS");
}
''',encoding='utf-8')
base=['rustc','--edition=2021','-Awarnings','-L','dependency='+str(D)]
for n,p in libs.items():base+=['--extern',n+'='+str(p)]
runs=[]
for mode in ['yes','no']:
 exe=H/(P+'_probe_02_'+mode+'.exe');cmd=base+['-C','overflow-checks='+mode,str(src),'-o',str(exe)]
 c=subprocess.run(cmd,capture_output=True,text=True,timeout=60);r={'command':cmd,'overflow_checks':mode,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
 if not c.returncode:
  x=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30);r.update(exit_code=x.returncode,output=x.stdout+x.stderr)
 runs.append(r)
receipt={'source_files':[{'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in owners.values()],'libraries':prior['libraries'],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'runs':runs,'limits':'Small source-inclusion controls, cached pinned dependencies, no complete native build or theorem claim.'}
(H/(P+'_validation_02.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps([{k:v for k,v in r.items()if k!='command'}for r in runs],indent=2))

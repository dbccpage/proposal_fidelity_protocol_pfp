import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_quantum_physics';D=R/'code/rust/target/debug/deps'
prior=json.loads((H/(P+'_validation_06.json')).read_text());libs={x['extern_name']:R/x['path']for x in prior['libraries']}
owners={n:R/('code/rust/core_quantum_physics/src/'+n+'.rs')for n in ['hermitian_spectral','instruments','observable']}
src=H/(P+'_probe_08.rs');src.write_text(''.join('#[path='+json.dumps(p.as_posix())+'] pub mod '+n+';\n'for n,p in owners.items())+r'''
pub use cached_quantum::{exact_hermitian,exact_operator,exact_channel,trace_norm_certificate,density_matrix,quantum_state,pauli};
use core_number_theory::rational::ri;
fn main(){
 use hermitian_spectral::*;
 let mut demo=HermitianMatrix::try_float64_demo(1,vec![(7.0,0.0)]).unwrap();demo.carrier=ScalarCarrier::Rational;assert!(spectral_decompose(&demo).is_err());let v=block_diagonal_eigenvalues(&demo,&BlockStructure{block_sizes:vec![1]}).unwrap();assert_eq!(v[0].re,ri(0));println!("mutated_float7_block_spectrum_returns_exact0=true");
 let mut tiny=HermitianMatrix::try_diagonal_rational(&[ri(1)],ScalarCarrier::Rational).unwrap();tiny.n=2;assert!(spectral_decompose(&tiny).is_err());let v=block_diagonal_eigenvalues(&tiny,&BlockStructure{block_sizes:vec![2]}).unwrap();assert_eq!(v.iter().map(|z|z.re.clone()).collect::<Vec<_>>(),vec![ri(1),ri(0)]);println!("mutated_dimension_block_spectrum_fabricates_zero=true");
 use instruments::*;
 let ev=SpectralEvidence{certificate_id:"unsupported assertion".into(),dim:1,eigenvalues:vec![ri(0)],hypotheses_paid:true};assert!(ev.require_paid().is_ok());let p=Povm{dim:1,effects:vec![PovmEffect{outcome_id:"only".into(),diagonal:vec![ri(4)]}],label:String::new()};let l=LudersInstrument::try_new(ev,p,"").unwrap();let o=l.apply_diagonal_state(&[ri(1)]).unwrap();assert_eq!(o.outcome_probs[0].1,ri(4));println!("legacy_Luders_accepted_single_outcome_probability=4");
 let effect=linear_algebra::exact_field::matrix::from_fn(1,1,|_,_|core_number_theory::cyclotomic::GaussianRat::from_ints(4,0)).unwrap();assert!(ExactPovm::try_new(vec![effect]).is_err());println!("full_exact_POVM_rejects_same_effect=PASS");
 let mut s=quantum_state::QuantumState::computational_basis(&cached_quantum::hilbert_space::HilbertSpace::try_new(1,"").unwrap(),0,"").unwrap();s.amplitudes[0].re=2.0;assert_eq!(observable::Observable::identity(1).unwrap().expectation_value_state(&s).unwrap(),4.0);println!("floating_identity_expectation_on_mutable_unnormalized_state=4");
 let valid=HermitianMatrix::try_diagonal_rational(&[ri(3),ri(-1)],ScalarCarrier::Rational).unwrap();assert_eq!(spectral_decompose(&valid).unwrap().distinct_eigenvalues(),vec![ri(-1),ri(3)]);println!("valid_diagonal_spectrum_control=PASS");
}
''',encoding='utf-8')
cmd=['rustc','--edition=2021','-Awarnings','-L','dependency='+str(D)]
for n,p in libs.items():cmd+=['--extern',n+'='+str(p)]
exe=H/(P+'_probe_08.exe');cmd +=[str(src),'-o',str(exe)];c=subprocess.run(cmd,capture_output=True,text=True,timeout=60);run={'command':cmd,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
if not c.returncode:
 x=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30);run.update(exit_code=x.returncode,output=x.stdout+x.stderr)
receipt={'source_files':[{'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in owners.values()],'libraries':[{'extern_name':n,'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for n,p in libs.items()],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'run':run,'limits':'Three unchanged current owners, genuine pinned cached arithmetic/carrier dependencies; tiny public-input boundary controls only.'}
(H/(P+'_validation_08.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in run.items()if k!='command'},indent=2))

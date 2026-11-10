import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_quantum_physics';D=R/'code/rust/target/debug/deps'
prior=json.loads((H/(P+'_validation_01.json')).read_text());libs={pathlib.Path(x['path']).name[3:].split('-')[0]:R/x['path']for x in prior['libraries']};libs['cached_quantum']=D/'libcore_quantum_physics-f9c328b190a84659.rlib'
owners={pathlib.Path(x['path']).stem:R/x['path']for x in prior['source_files']}
for n in ['measurement','measurement_update','kraus_operators','quantum_channel','stinespring_dilation']:owners[n]=R/('code/rust/core_quantum_physics/src/'+n+'.rs')
src=H/(P+'_probe_04.rs');src.write_text(''.join('#[path='+json.dumps(p.as_posix())+'] pub mod '+n+';\n'for n,p in owners.items())+r'''
pub mod entanglement{pub use cached_quantum::entanglement::{Entanglement,EntanglementError};}
use linear_algebra::linear_algebra::complex_matrix::{CMatrix,C64};
use quantum_state::QuantumState;
use core_number_theory::cyclotomic::GaussianRat as G;
use core_number_theory::rational::Rational;
fn report<T:std::fmt::Debug,F:FnOnce()->T+std::panic::UnwindSafe>(name:&str,f:F){match std::panic::catch_unwind(f){Ok(x)=>println!("{}={:?}",name,x),Err(_)=>println!("{}=PANIC",name)}}
fn main(){
 std::panic::set_hook(Box::new(|_|{}));
 let m=measurement::Measurement::computational_basis(1);
 for a in [2.0,f64::NAN]{report("measurement_unvalidated_state",||m.probabilities_state(&QuantumState{dim:1,amplitudes:vec![C64::new(a,0.0)],label:String::new()}));}
 let two=measurement::Measurement::computational_basis(2);let rho=CMatrix::from_diagonal(&nalgebra::DVector::from_vec(vec![C64::new(1e-320,0.0),C64::new(1.0,0.0)]));
 report("positive_tiny_outcome_update",||measurement_update::MeasurementUpdate::update_density(&two,&rho,0).map(|r|r.iter().all(|x|x.re.is_finite()&&x.im.is_finite())));
 let k=kraus_operators::KrausOperators::try_from_cmatrices(1,vec![CMatrix::from_element(1,1,C64::new(1.0,0.0)),CMatrix::from_element(1,1,C64::new(1e-200,0.0))],"").unwrap();
 println!("rounded_zero_residual_is_trace_preserving={}",k.is_trace_preserving(0.0));assert!(k.is_trace_preserving(0.0));
 let tiny=Rational::from_float(1e-200).unwrap();let mat=|q|linear_algebra::backend::basic_matrix::BasicMatrix::from_row_major(1,1,vec![G::from_rational(q)]).unwrap();
 report("same_binary_float_coefficients_exact_TP_control",||exact_channel::ExactKrausChannel::try_new(1,1,vec![mat(Rational::from_integer(1.into())),mat(tiny)],""));
 let bad=quantum_channel::QuantumChannel{dim:1,source:quantum_channel::StateSpace::new(2),target:quantum_channel::StateSpace::new(1),kraus:kraus_operators::KrausOperators::identity(1,"").unwrap(),label:String::new()};
 report("stinespring_mismatched_source",||stinespring_dilation::StinespringDilation::from_quantum_channel(&bad,1e-6));
}
''',encoding='utf-8')
cmd=['rustc','--edition=2021','-Awarnings','-L','dependency='+str(D)]
for n,p in libs.items():cmd+=['--extern',n+'='+str(p)]
exe=H/(P+'_probe_04.exe');cmd +=[str(src),'-o',str(exe)];c=subprocess.run(cmd,capture_output=True,text=True,timeout=60);run={'command':cmd,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
if not c.returncode:
 x=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15);run.update(exit_code=x.returncode,output=x.stdout+x.stderr)
receipt={'source_files':[{'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in owners.values()],'libraries':[{'extern_name':n,'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for n,p in libs.items()],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'run':run,'limits':'Tiny diagnostic controls, unchanged owners and pinned cached dependency artifacts; genuine cached entanglement dependency not reached in controls. No full suite or certification claim.'}
(H/(P+'_validation_04.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in run.items()if k!='command'},indent=2))

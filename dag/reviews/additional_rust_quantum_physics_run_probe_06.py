import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_quantum_physics';D=R/'code/rust/target/debug/deps';F=D.parent/'.fingerprint'
prior=json.loads((H/(P+'_validation_01.json')).read_text());libs={pathlib.Path(x['path']).name[3:].split('-')[0]:R/x['path']for x in prior['libraries']}
meta=json.loads((F/'core_quantum_physics-f9c328b190a84659/lib-core_quantum_physics.json').read_text())
for _,name,_,identity in meta['deps']:
 if name!='core_finite_probability':continue
 found=[p for p in F.glob('*/lib-'+name)if int.from_bytes(bytes.fromhex(p.read_text().strip()),'little')==identity];assert len(found)==1
 libs[name]=D/('lib'+name+'-'+found[0].parent.name.rsplit('-',1)[1]+'.rlib')
libs['cached_quantum']=D/'libcore_quantum_physics-f9c328b190a84659.rlib'
owners={n:R/('code/rust/core_quantum_physics/src/'+n+'.rs')for n in ['entropy','fidelity','trace_norm_certificate','entanglement','purification','quantum_relative_entropy']}
src=H/(P+'_probe_06.rs');src.write_text(''.join('#[path='+json.dumps(p.as_posix())+'] pub mod '+n+';\n'for n,p in owners.items())+r'''
pub use cached_quantum::{density_matrix,quantum_state,hilbert_space,exact_operator,exact_hermitian,exact_channel,pauli};
use core_number_theory::rational::ri;
fn main(){
 let empty_mass=entropy::Entropy::shannon(&[0.0,0.0]).unwrap();assert_eq!(empty_mass,0.0);println!("zero_mass_Shannon_Ok={empty_mass}");
 let overflow=entropy::Entropy::shannon(&[1e308,1e308]).unwrap();assert!(overflow.is_nan());println!("finite_weights_overflow_Shannon_Ok_NaN=true");
 let ray=quantum_state::RayVector::from_ints(&[(1,0),(0,0),(0,0),(1,0)]).unwrap();let rho=density_matrix::ExactDensityMatrix::pure(&ray).unwrap();
 assert_eq!(entanglement::Entanglement::concurrence_exact(&rho,10000).unwrap(),ri(1));let enc=entanglement::Entanglement::concurrence_enclosure(&rho,16,10000).unwrap();assert!(enc.lo()<=&ri(1)&&enc.hi()>=&ri(1));println!("Bell_concurrence_exact_and_enclosure=PASS");
 let p=purification::WeightedPurification::of(&rho).unwrap();assert_eq!(p.reduced_state().unwrap(),*rho.matrix());assert_eq!(purification::Purification::fidelity_exact(&rho,&rho,10000).unwrap(),ri(1));println!("weighted_purification_replay_and_self_fidelity=PASS");
 let y=pauli::Pauli::Y.to_operator();let cert=trace_norm_certificate::sign_from_spectrum(y.as_matrix(),&[ri(-1),ri(1)]).unwrap();assert_eq!(cert.trace_norm(),&ri(2));let zero=linear_algebra::exact_field::matrix::zeros(2,2).unwrap();assert!(trace_norm_certificate::TraceNormCertificate::try_new(y.as_matrix().clone(),cert.positive_part().clone(),cert.negative_part().clone(),zero).is_err());println!("trace_norm_dual_gap_control=PASS");
 let other=density_matrix::ExactDensityMatrix::pure(&quantum_state::RayVector::basis(4,0).unwrap()).unwrap();assert!(!quantum_relative_entropy::QuantumRelativeEntropy::support_included(&rho,&other).unwrap());println!("noncommuting_pure_support_refusal=PASS");
}
''',encoding='utf-8')
cmd=['rustc','--edition=2021','-Awarnings','-L','dependency='+str(D)]
for n,p in libs.items():cmd+=['--extern',n+'='+str(p)]
exe=H/(P+'_probe_06.exe');cmd +=[str(src),'-o',str(exe)];c=subprocess.run(cmd,capture_output=True,text=True,timeout=60);run={'command':cmd,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
if not c.returncode:
 x=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30);run.update(exit_code=x.returncode,output=x.stdout+x.stderr)
receipt={'source_files':[{'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in owners.values()],'libraries':[{'extern_name':n,'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for n,p in libs.items()],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'run':run,'limits':'Six unchanged current owners, with genuine pinned cached quantum carrier and arithmetic dependencies; only tiny synthetic controls. No whole crate build or broad suite.'}
(H/(P+'_validation_06.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in run.items()if k!='command'},indent=2))

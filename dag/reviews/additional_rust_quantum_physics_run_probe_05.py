import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_quantum_physics';D=R/'code/rust/target/debug/deps'
prior=json.loads((H/(P+'_validation_01.json')).read_text());libs={pathlib.Path(x['path']).name[3:].split('-')[0]:R/x['path']for x in prior['libraries']};owners={pathlib.Path(x['path']).stem:R/x['path']for x in prior['source_files']}
for n in ['kraus_operators','quantum_channel','completely_positive_map','cptp_channels_stinespring']:owners[n]=R/('code/rust/core_quantum_physics/src/'+n+'.rs')
src=H/(P+'_probe_05.rs');src.write_text(''.join('#[path='+json.dumps(p.as_posix())+'] pub mod '+n+';\n'for n,p in owners.items())+r'''
use linear_algebra::linear_algebra::complex_matrix::{CMatrix,C64};
use quantum_channel::{QuantumChannel,StateSpace};
use completely_positive_map::CompletelyPositiveMap;
use core_number_theory::rational::{Rational,rq};
fn candidate(k:CMatrix)->QuantumChannel{let d=k.nrows();QuantumChannel{dim:d,source:StateSpace::new(d),target:StateSpace::new(d),kraus:kraus_operators::KrausOperators::try_from_cmatrices(d,vec![k],"").unwrap(),label:String::new()}}
fn main(){
 let huge=candidate(CMatrix::from_element(1,1,C64::new(1e200,0.0)));let cp=CompletelyPositiveMap::from_quantum_channel(&huge,"").unwrap();println!("CP_from_finite_Kraus_nonfinite_Choi={}",cp.choi_matrix().iter().any(|z|!z.re.is_finite()||!z.im.is_finite()));
 let k=CMatrix::from_row_slice(2,2,&[C64::new(0.3,0.0),C64::new(0.0,0.0),C64::new(0.7,0.0),C64::new(0.0,0.0)]);let cp=CompletelyPositiveMap::from_quantum_channel(&candidate(k),"").unwrap();
 let a=Rational::from_float(cp.choi_matrix()[(0,0)].re).unwrap();let b=Rational::from_float(cp.choi_matrix()[(0,1)].re).unwrap();let c=Rational::from_float(cp.choi_matrix()[(1,1)].re).unwrap();let determinant=a*c-&b*&b;assert!(determinant<Rational::from_integer(0.into()));println!("CP_from_Kraus_exact_negative_principal_minor={}",determinant);
 println!("same_Choi_exact_admission_refuses={}",CompletelyPositiveMap::try_from_choi_matrix(2,2,cp.choi_matrix().clone(),"",1.0).is_err());
 let ch=exact_channel::ExactKrausChannel::depolarizing_qubit(rq(1,3),"").unwrap();let w=cptp_channels_stinespring::WeightedStinespring::from_channel(&ch).unwrap();assert!(w.verify().unwrap());let rho=linear_algebra::exact_field::matrix::identity(2).unwrap();assert_eq!(w.apply(&rho).unwrap(),ch.apply(&rho).unwrap());println!("weighted_Stinespring_gram_and_independent_application=PASS");
}
''',encoding='utf-8')
cmd=['rustc','--edition=2021','-Awarnings','-L','dependency='+str(D)]
for n,p in libs.items():cmd+=['--extern',n+'='+str(p)]
exe=H/(P+'_probe_05.exe');cmd +=[str(src),'-o',str(exe)];c=subprocess.run(cmd,capture_output=True,text=True,timeout=60);run={'command':cmd,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
if not c.returncode:
 x=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30);run.update(exit_code=x.returncode,output=x.stdout+x.stderr)
receipt={'source_files':[{'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in owners.values()],'libraries':prior['libraries'],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'run':run,'limits':'Twelve unchanged source modules and pinned cached dependencies, tiny finite contrast and weighted-isometry controls only.'}
(H/(P+'_validation_05.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in run.items()if k!='command'},indent=2))

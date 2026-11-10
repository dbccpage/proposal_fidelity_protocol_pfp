"""Bounded source-inclusion probe; offline cached libraries, no Cargo/build scripts."""
import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_quantum_physics'
D=R/'code/rust/target/debug/deps';F=D.parent/'.fingerprint'
m=json.loads((F/'core_quantum_physics-f9c328b190a84659/lib-core_quantum_physics.json').read_text())
wanted={'serde','thiserror','num_rational','core_number_theory','core_kernel','core_lie_theory','num_traits','linear_algebra','num_bigint','num_complex','core_functional','nalgebra'};libs={}
for _,name,_,identity in m['deps']:
 if name not in wanted:continue
 matches=[p for p in F.glob('*/lib-'+name)if int.from_bytes(bytes.fromhex(p.read_text().strip()),'little')==identity]
 assert len(matches)==1,(name,matches)
 libs[name]=D/('lib'+name+'-'+matches[0].parent.name.rsplit('-',1)[1]+'.rlib')
owners={n:R/('code/rust/core_quantum_physics/src/'+n+'.rs')for n in ['hilbert_space','exact_hermitian','exact_operator','pauli','quantum_state','exact_channel','density_matrix','engine_bridge']}
src=H/(P+'_probe_01.rs')
src.write_text(''.join('#[path='+json.dumps(p.as_posix())+'] pub mod '+n+';\n'for n,p in owners.items())+r'''
use core_number_theory::rational::{Rational,ri};
use core_number_theory::cyclotomic::GaussianRat as G;
use linear_algebra::backend::basic_matrix::BasicMatrix as M;
use linear_algebra::exact_field::matrix as mx;
use quantum_state::{RayVector,QuantumState};
fn bad()->Rational{Rational::new_raw(1.into(),0.into())}
fn bg()->G{G{re:bad(),im:ri(0)}}
fn report<T:std::fmt::Debug,F:FnOnce()->T+std::panic::UnwindSafe>(name:&str,f:F){
 match std::panic::catch_unwind(f){Ok(x)=>println!("{}={:?}",name,x),Err(_)=>println!("{}=PANIC",name)}
}
fn main(){
 std::panic::set_hook(Box::new(|_|{}));
 report("ray_bad_admission",||RayVector::try_new(vec![bg()]));
 report("ray_bad_norm",||RayVector::try_new(vec![bg()]).unwrap().norm_sq());
 report("operator_bad_admission",||exact_operator::ExactOperator::try_new(M::from_row_major(1,1,vec![bg()]).unwrap()));
 report("hermitian_bad_control",||exact_hermitian::check_hermitian(&M::from_row_major(1,1,vec![bg()]).unwrap()));
 report("eigenpair_bad_scalar",||exact_hermitian::eigen_residual(&mx::identity(1).unwrap(),&bg(),&[G::from_ints(1,0)]));
 report("weighted_bad_scalar",||exact_channel::ExactKrausChannel::try_weighted(1,1,vec![(bad(),mx::identity(1).unwrap())],"bad"));
 report("weighted_budgeted_bad_control",||{let mut b=linear_algebra::exact_field::rational_bareiss::RationalBudget::new(linear_algebra::exact_field::rational_bareiss::RationalLimits{max_scalar_ops:100,max_elements:4,max_bits:16});exact_channel::ExactKrausChannel::try_weighted_with_budget(1,1,vec![(bad(),mx::identity(1).unwrap())],"bad",&mut b)});
 report("state_public_shape_projector",||QuantumState{dim:1,amplitudes:vec![],label:String::new()}.to_projector_cmatrix());
 report("state_index_overflow",||QuantumState::computational_basis(&hilbert_space::HilbertSpace::try_new(1,"").unwrap(),usize::MAX,""));
 let q=Rational::new(1.into(),num_bigint::BigInt::from(1)<<2000usize);
 report("ray_tiny_f64",||RayVector::try_new(vec![G::from_rational(q.clone())]).unwrap().to_f64_amplitudes());
 report("bridge_tiny_control",||engine_bridge::rational_to_c64(&q));
 for x in [1e-300,1e300]{let z=QuantumState::try_normalized_with_norm(&hilbert_space::HilbertSpace::try_new(1,"").unwrap(),vec![num_complex::Complex::new(x,0.0)],"").unwrap();println!("normalization_{x}_reported_norm={:?};valid={:?}",z.1,z.0.validate());}
 report("stinespring_nonisometry_application",||exact_channel::apply_stinespring(&M::from_row_major(1,1,vec![G::from_ints(2,0)]).unwrap(),1,1,&mx::identity(1).unwrap()));
}
''',encoding='utf-8')
base=['rustc','--edition=2021','-Awarnings','-L','dependency='+str(D)]
for n,p in libs.items():base+=['--extern',n+'='+str(p)]
runs=[]
for mode in ['yes','no']:
 exe=H/(P+'_probe_01_'+mode+'.exe');cmd=base+['-C','overflow-checks='+mode,str(src),'-o',str(exe)]
 c=subprocess.run(cmd,capture_output=True,text=True,timeout=60);r={'command':cmd,'overflow_checks':mode,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
 if not c.returncode:
  x=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15);r.update(exit_code=x.returncode,output=x.stdout+x.stderr)
 runs.append(r)
receipt={'source_files':[{'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in owners.values()],'libraries':[{'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in libs.values()],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'runs':runs,'limits':'Unchanged full source modules included with cached compiled dependencies; dependency binaries are pinned, not rebuilt or verified against current dependency source. Synthetic finite public inputs only; not full suite, complete crate build or theorem proof.'}
(H/(P+'_validation_01.json')).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items()if k!='command'}for r in runs],indent=2))

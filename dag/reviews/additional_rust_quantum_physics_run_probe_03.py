import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_quantum_physics';D=R/'code/rust/target/debug/deps';F=D.parent/'.fingerprint'
prior=json.loads((H/(P+'_validation_01.json')).read_text());libs={pathlib.Path(x['path']).name[3:].split('-')[0]:R/x['path']for x in prior['libraries']}
meta=json.loads((F/'core_quantum_physics-f9c328b190a84659/lib-core_quantum_physics.json').read_text())
for _,name,_,identity in meta['deps']:
 if name not in {'num_integer','core_fusion_categories'}:continue
 found=[p for p in F.glob('*/lib-'+name)if int.from_bytes(bytes.fromhex(p.read_text().strip()),'little')==identity];assert len(found)==1
 libs[name]=D/('lib'+name+'-'+found[0].parent.name.rsplit('-',1)[1]+'.rlib')
libs['cached_quantum']=D/'libcore_quantum_physics-f9c328b190a84659.rlib'
owners={pathlib.Path(x['path']).stem:R/x['path']for x in prior['source_files']}
for n in ['relative_state_branching','branch_finegraining','everett','no_cloning']:owners[n]=R/('code/rust/core_quantum_physics/src/'+n+'.rs')
src=H/(P+'_probe_03.rs');src.write_text(''.join('#[path='+json.dumps(p.as_posix())+'] pub mod '+n+';\n'for n,p in owners.items())+r'''
// Genuine cached owner for an unused tomography dependency; no dummy implementation.
pub mod composition_tomography{pub use cached_quantum::composition_tomography::complex_hermitian_basis;}
use core_number_theory::cyclotomic::GaussianRat as G;
use core_number_theory::rational::{ri,rq,Rational};
fn report<T:std::fmt::Debug,F:FnOnce()->T+std::panic::UnwindSafe>(name:&str,f:F){match std::panic::catch_unwind(f){Ok(x)=>println!("{}={:?}",name,x),Err(_)=>println!("{}=PANIC",name)}}
fn main(){
 std::panic::set_hook(Box::new(|_|{}));
 let mut f=vec![G::from_ints(0,0);1025];f[0]=G::from_ints(1,0);
 let packet=relative_state_branching::RelativeStatePacket::with_system_family(vec![f],vec![G::from_ints(1,0)],vec![vec![G::from_ints(1,0)]]).unwrap();
 println!("relative_packet_dimension1025_admitted=true");report("relative_reduced_state_budget",||packet.reduced_state());
 let raw=Rational::new_raw(2.into(),4.into());let count=branch_finegraining::BranchCounting::new(&[raw.clone(),raw],None).unwrap();println!("unreduced_minimal_multiplicity={}",count.multiplicity);
 let minimal=branch_finegraining::BranchCounting::new(&[rq(1,2),rq(1,2)],None).unwrap();println!("canonical_minimal_multiplicity={}",minimal.multiplicity);assert_eq!(minimal.multiplicity,2.into());assert_eq!(count.multiplicity,4.into());
 let node=everett::EverettForkingNode{dimension:1,branches:vec![everett::Branch{index:0,amplitude_re:ri(1),amplitude_im:ri(0),born_weight:ri(1),count_weight:ri(0),is_active:true}]};let (dec,_,uniform)=node.measure_decoupling_theorem();println!("mutable_everett_asserted_theorem_holds={}",dec==!uniform);assert!(dec&&uniform);
 let u=quantum_state::RayVector::from_ints(&[(1,0),(0,0)]).unwrap();let v=quantum_state::RayVector::from_ints(&[(1,0),(1,0)]).unwrap();assert_eq!(no_cloning::NoCloning::exact_obstruction(&u,&v).unwrap(),rq(1,4));assert_eq!(no_cloning::NoCloning::universal_cloning_fidelity(2,1,2).unwrap(),rq(5,6));println!("exact_clone_obstruction_and_declared_fidelity_formula=PASS");
}
''',encoding='utf-8')
base=['rustc','--edition=2021','-Awarnings','-L','dependency='+str(D)]
for n,p in libs.items():base+=['--extern',n+'='+str(p)]
exe=H/(P+'_probe_03.exe');cmd=base+[str(src),'-o',str(exe)];c=subprocess.run(cmd,capture_output=True,text=True,timeout=60);run={'command':cmd,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
if not c.returncode:
 x=subprocess.run([str(exe)],capture_output=True,text=True,timeout=30);run.update(exit_code=x.returncode,output=x.stdout+x.stderr)
receipt={'source_files':[{'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in owners.values()],'libraries':[{'extern_name':n,'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for n,p in libs.items()],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'run':run,'limits':'Unchanged current owners, cached genuine tomography import unused in executed controls. No broad native build, expensive dense allocation, provider or private input.'}
(H/(P+'_validation_03.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in run.items()if k!='command'},indent=2))

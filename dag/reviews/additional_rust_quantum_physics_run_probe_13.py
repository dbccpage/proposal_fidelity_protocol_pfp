import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_quantum_physics';D=R/'code/rust/target/debug/deps';F=D.parent/'.fingerprint'
prior=json.loads((H/(P+'_validation_06.json')).read_text());libs={x['extern_name']:R/x['path']for x in prior['libraries']}
meta=json.loads((F/'core_quantum_physics-f9c328b190a84659/lib-core_quantum_physics.json').read_text())
for _,name,_,identity in meta['deps']:
 if name not in ['num_integer','core_solvers','core_homology','core_policy']:continue
 found=[p for p in F.glob('*/lib-'+name)if int.from_bytes(bytes.fromhex(p.read_text().strip()),'little')==identity];assert len(found)==1
 libs[name]=D/('lib'+name+'-'+found[0].parent.name.rsplit('-',1)[1]+'.rlib')
owners={n:R/('code/rust/core_quantum_physics/src/'+n+'.rs')for n in ['kochen_specker','contextuality_obstruction','parity_context_packet','pauli_context_table','separating_predictions']}
scope={x['path']:x['sha256']for x in json.loads((H/(P+'_scope.json')).read_text())['files']}
for p in owners.values():assert hashlib.sha256(p.read_bytes()).hexdigest()==scope[p.relative_to(R).as_posix()]
src=H/(P+'_probe_13.rs');src.write_text(''.join('#[path='+json.dumps(p.as_posix())+'] pub mod '+n+';\n'for n,p in owners.items())+r'''
pub use cached_quantum::exact_hermitian;
fn main(){
 use core_number_theory::rational::ri;use kochen_specker::RaySystem;
 let rays=vec![vec![ri(1),ri(0)],vec![ri(0),ri(1)]];assert!(RaySystem::new(rays.clone(),vec![vec![0,1]]).is_ok());
 let hook=std::panic::take_hook();std::panic::set_hook(Box::new(|_|{}));let short=std::panic::catch_unwind(||RaySystem::new(rays.clone(),vec![vec![0]])).is_err();let index=std::panic::catch_unwind(||RaySystem::new(rays,vec![vec![0,2]])).is_err();std::panic::set_hook(hook);assert!(short&&index);println!("KS_short_context_and_out_of_range_index_panics=true");
 use parity_context_packet::*;let p=ParityContextPacket::new(1,&[vec![0],vec![0]],&[1,0]).unwrap();let d1=vec![vec![1,1]];let c=ParityAdmission::ClosureFailure{defect:vec![1]};assert!(p.verify_admission(1,&d1,&c).unwrap());assert!(p.admit_with_d1(5,&d1).is_err());assert!(p.verify_admission(5,&d1,&c).unwrap());println!("closure_failure_replay_accepts_out_of_domain_bit=true");
 let table=pauli_context_table::PauliContextTable::mermin();assert!(table.observables_are_hermitian_involutions());assert_eq!(table.sign_table().unwrap(),vec![1,1,1,1,1,-1]);let p=table.packet().unwrap();let cert=p.certificate(p.targets()).unwrap();assert!(matches!(cert,ImageCertificate::Separator(_)));assert!(p.verify_certificate(p.targets(),cert).unwrap());assert!(!p.satisfiable(p.all_contexts()).unwrap());assert!(p.is_minimally_unsatisfiable().unwrap());println!("Pauli_operator_products_and_replayed_parity_obstruction=PASS");
 let x1=contextuality_obstruction::construct_cabello_scenario();let o1=contextuality_obstruction::compute_obstruction_class(&x1).unwrap();assert!(!o1.obstruction_class_is_zero);let x2=contextuality_obstruction::construct_product_scenario();let o2=contextuality_obstruction::compute_obstruction_class(&x2).unwrap();assert!(o2.obstruction_class_is_zero);assert!(contextuality_obstruction::verify_global_section(&x2,&o2.exhibited_global_section.unwrap()).0);println!("Cabello_nonzero_and_product_zero_cochain_controls=PASS");
 let s=separating_predictions::MerminPeresSquare::standard();assert!(s.verify_no_noncontextual_assignment().unwrap());println!("independent_Mermin_exhaustive_assignment_control=PASS");
}
''',encoding='utf-8')
cmd=['rustc','--edition=2021','-Awarnings','-C','overflow-checks=yes','-L','dependency='+str(D)]
for n,p in libs.items():cmd+=['--extern',n+'='+str(p)]
exe=H/(P+'_probe_13.exe');cmd +=[str(src),'-o',str(exe)];c=subprocess.run(cmd,capture_output=True,text=True,timeout=60);run={'command':cmd,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
if not c.returncode:
 x=subprocess.run([str(exe)],capture_output=True,text=True,timeout=45);run.update(exit_code=x.returncode,output=x.stdout+x.stderr)
receipt={'source_files':[{'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in owners.values()],'libraries':[{'extern_name':n,'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for n,p in libs.items()],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'run':run,'limits':'Five unchanged scoped owners; pinned cached lower arithmetic and solver libraries. Tiny malformed controls plus exact Mermin/Cabello/product examples; no broad suite or empirical/physical test.'}
(H/(P+'_validation_13.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in run.items()if k!='command'},indent=2))

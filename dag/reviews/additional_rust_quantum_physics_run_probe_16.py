import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_quantum_physics';D=R/'code/rust/target/debug/deps';F=D.parent/'.fingerprint'
libs={x['extern_name']:R/x['path'] for x in json.loads((H/(P+'_validation_15.json')).read_text())['libraries']}
meta=json.loads((F/'core_quantum_physics-f9c328b190a84659/lib-core_quantum_physics.json').read_text())
for _,name,_,identity in meta['deps']:
 if name!='core_general_relativity':continue
 found=[p for p in F.glob('*/lib-'+name)if int.from_bytes(bytes.fromhex(p.read_text().strip()),'little')==identity];assert len(found)==1
 libs[name]=D/('lib'+name+'-'+found[0].parent.name.rsplit('-',1)[1]+'.rlib')
owners={n:R/('code/rust/core_quantum_physics/src/'+n+'.rs')for n in ['derivation_dag_witnesses','pairing_audit','quantum_regge_bridge','regge_gravity_ghz_chern_finite_maps']}
helper=R/'code/rust/core_quantum_physics/src/quantum_import_finite_maps/page_wootters_tsirelson_wigner/cyclotomic_rings.rs'
scope={x['path']:x['sha256']for x in json.loads((H/(P+'_scope.json')).read_text())['files']}
for p in list(owners.values())+[helper]:assert hashlib.sha256(p.read_bytes()).hexdigest()==scope[p.relative_to(R).as_posix()]
src=H/(P+'_probe_16.rs');src.write_text(''.join('#[path='+json.dumps(p.as_posix())+'] pub mod '+n+';\n'for n,p in owners.items())+'pub mod quantum_import_finite_maps { pub use cached_quantum::quantum_import_finite_maps::*; pub fn q(n:i64,d:i64)->Q { num_rational::Ratio::new(n,d) } pub mod page_wootters_tsirelson_wigner { #[path='+json.dumps(helper.as_posix())+'] pub mod cyclotomic_rings; }}\n'+r'''
pub use cached_quantum::{composition_tomography,density_matrix,exact_channel,exact_hermitian,hilbert_space,kraus_operators,quantum_channel,spin_area_spectrum};
use core_number_theory::rational::{ri,rq};
fn main(){
 use regge_gravity_ghz_chern_finite_maps::*; use quantum_import_finite_maps::Qi;
 let mut ghz=build_ghz_mermin_audit().unwrap();assert!(ghz.passed());ghz.ghz=vec![Qi::zero();8];assert!(ghz.passed());println!("zero_GHZ_state_stale_audit_passes=true");
 let mut chern=build_chern_parity_audit();assert!(chern.passed());for(_,c)in &mut chern.haldane_grid{*c=Some(99);}assert!(chern.passed());println!("Chern_grid_all_99_passes=true");
 let ev=exact_eigenvalue(&vec![vec![Qi::one()]],&[Qi::one(),Qi::one()]).unwrap();assert_eq!(ev,Qi::one());println!("one_dimensional_operator_two_dimensional_eigenvector_accepted=true");
 let hook=std::panic::take_hook();std::panic::set_hook(Box::new(|_|{}));let malformed=std::panic::catch_unwind(||exact_eigenvalue(&vec![vec![Qi::one(),Qi::zero()],vec![Qi::zero(),Qi::one()]],&[Qi::one()])).is_err();std::panic::set_hook(hook);assert!(malformed);println!("short_eigenvector_panics=true");
 use quantum_regge_bridge::*;use linear_algebra::linear_algebra::complex_matrix::{CMatrix,NComplex};
 let wdw=DiscreteMiniSuperspaceWheelerDeWitt::new(1.,1.,0.,0.,1.,3).unwrap();assert_eq!(wdw.apply_hamiltonian(&[1.,1.,1.]).unwrap(),vec![1.,0.,1.]);assert_eq!(wdw.compute_residual_norm(&[1.,1.,1.]).unwrap(),0.);println!("WDW_nonzero_boundary_Hpsi=[1,0,1]; reported_residual=0");
 let basis=CMatrix::from_element(1,1,NComplex::new(2.,0.));let thermal=simplicial_dirac_thermal_cmatrix(&[0.],&basis,1.).unwrap();assert_eq!(thermal[(0,0)],NComplex::new(4.,0.));println!("unnormalized_thermal_basis_accepted_trace=4");
 let awdw=AnisotropicBianchiWheelerDeWitt::new(1.,1.,0.,[0.;3],[1.;3],[2;3]).unwrap();let mut psi=vec![0.;8];psi[0]=1.;let invalid=awdw.apply_anisotropic_decoherence(&psi,[-1.,f64::NAN,0.]).unwrap();assert_eq!(invalid,awdw.wavefunction_to_density_matrix(&psi).unwrap());println!("negative_NaN_directional_probabilities_accepted=true");
 use pairing_audit::*;use linear_algebra::backend::basic_matrix::BasicMatrix;
 for row in declared_registry().unwrap(){println!("registry {}: {:?}",row.name,audit_row(&row).unwrap());}
 assert_eq!(audit_row(&transport_gram_row().unwrap()).unwrap(),PairingTerminal::Passes);assert_eq!(audit_row(&noisy_born_row().unwrap()).unwrap(),PairingTerminal::Passes);
 let e1=vec![ri(1),ri(0)];let e2=vec![ri(0),ri(1)];let vectors=vec![e1.clone(),e2.clone()];let gram=BasicMatrix::from_row_major(2,2,vec![rq(1,2);4]).unwrap();let packet=PairingPacket::new(vectors.clone(),vectors,vec![vec![0,1]],Pairing::Bilinear(gram),vec![]).unwrap();for e in 0..2{assert_eq!(packet.value(e,&e1).unwrap(),packet.value(e,&e2).unwrap());}assert_eq!(packet.product_effect_rank().unwrap(),4);
 let table=JointTable{measurement_a:0,measurement_b:0,marginal_a:e1.clone(),marginal_b:e1,probabilities:vec![vec![rq(1,4);2];2]};let row=PairingRow{name:"degenerate_gram",origin:PairingOrigin::Imported,packet,composite:CompositeTier::Declared{joint_effect_dim:4,tables:vec![table]}};assert_eq!(audit_row(&row).unwrap(),PairingTerminal::Passes);println!("degenerate_pairing_identical_state_statistics_raw_rank4_passes=true");
 let mut empty=classical_simplex_row().unwrap();empty.composite=CompositeTier::Declared{joint_effect_dim:4,tables:vec![]};assert_eq!(audit_row(&empty).unwrap(),PairingTerminal::Passes);empty.composite=CompositeTier::Declared{joint_effect_dim:0,tables:vec![]};assert_eq!(audit_row(&empty).unwrap(),PairingTerminal::Passes);println!("empty_composite_tables_and_declared_dimension0_pass=true");
 let receipt=derivation_dag_witnesses::build_derivation_dag_master_witness_receipt();assert_eq!(receipt.families.len(),33);assert!(receipt.all_passed);let mut names=std::collections::BTreeSet::new();for family in &receipt.families{assert!(family.passed);for n in &family.covered_nodes{names.insert(n);}}println!("fixed_DAG_master_families=33; all_passed=true; distinct_labels={}",names.len());
}
''',encoding='utf-8')
cmd=['rustc','--edition=2021','-Awarnings','-C','overflow-checks=yes','-L','dependency='+str(D)]
for n,p in libs.items():cmd+=['--extern',n+'='+str(p)]
exe=H/(P+'_probe_16.exe');cmd +=[str(src),'-o',str(exe)];c=subprocess.run(cmd,capture_output=True,text=True,timeout=60);run={'command':cmd,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
if not c.returncode:
 x=subprocess.run([str(exe)],capture_output=True,text=True,timeout=45);run.update(exit_code=x.returncode,output=x.stdout+x.stderr)
receipt={'source_files':[{'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in list(owners.values())+[helper]],'libraries':[{'extern_name':n,'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for n,p in libs.items()],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'run':run,'limits':'Four unchanged scoped owners plus current cyclotomic helper with cached lower libraries. Tiny counterexamples and fixed positive controls only. Adapter supplies the exact Ratio::new q constructor and cached parent quantum imports. No whole crate build, formal proof or physical validation.'}
(H/(P+'_validation_16.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in run.items()if k!='command'},indent=2))

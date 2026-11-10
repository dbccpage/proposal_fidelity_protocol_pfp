import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_quantum_physics';D=R/'code/rust/target/debug/deps';F=D.parent/'.fingerprint'
prior=json.loads((H/(P+'_validation_13.json')).read_text());libs={x['extern_name']:R/x['path']for x in prior['libraries']}
meta=json.loads((F/'core_quantum_physics-f9c328b190a84659/lib-core_quantum_physics.json').read_text())
for _,name,_,identity in meta['deps']:
 if name!='core_holonomy':continue
 found=[p for p in F.glob('*/lib-'+name)if int.from_bytes(bytes.fromhex(p.read_text().strip()),'little')==identity];assert len(found)==1
 libs[name]=D/('lib'+name+'-'+found[0].parent.name.rsplit('-',1)[1]+'.rlib')
owners={n:R/('code/rust/core_quantum_physics/src/'+n+'.rs')for n in ['u1_graph_connection','holonomy_interference','quaternion_gauge_shadow']}
scope={x['path']:x['sha256']for x in json.loads((H/(P+'_scope.json')).read_text())['files']}
for p in owners.values():assert hashlib.sha256(p.read_bytes()).hexdigest()==scope[p.relative_to(R).as_posix()]
src=H/(P+'_probe_14.rs');src.write_text(''.join('#[path='+json.dumps(p.as_posix())+'] pub mod '+n+';\n'for n,p in owners.items())+r'''
pub use cached_quantum::exact_hermitian;
use core_solvers::data_cochain_packet::FiniteCochainPacket;
fn packet(edges:&[(&str,&str)])->FiniteCochainPacket{let mut c=core_holonomy::CellComplex::new(core_kernel::resource_limits::OperationLimits::holonomy());for v in["a","b","c"]{c.add_vertex(v).unwrap();}for&(a,b)in edges{c.add_edge(a,b).unwrap();}FiniteCochainPacket::with_unit_weights(c).unwrap()}
fn main(){use core_number_theory::cyclotomic::GaussianRat as G;use core_number_theory::rational::ri;use u1_graph_connection::*;use holonomy_interference::*;
 let p=packet(&[("a","b")]);let q=packet(&[("a","c")]);let bigger=packet(&[("a","b"),("b","c")]);let a=U1Connection::trivial(&p);let psi=[G::from_ints(1,0),G::from_ints(2,0),G::from_ints(4,0)];assert_eq!(a.covariant_difference(&p,&psi).unwrap(),vec![G::one()]);assert!(a.try_covariant_difference_matrix(&q).is_ok());assert!(a.try_covariant_difference_matrix(&bigger).is_err());let wrong=a.covariant_difference(&q,&psi).unwrap();assert_eq!(wrong,vec![G::from_ints(3,0)]);assert_eq!(a.dirichlet_energy(&q,&psi).unwrap(),ri(9));println!("foreign_packet_direct_difference_accepted=3; same_count_matrix_path_also_accepts=true; foreign_energy=9");
 let hook=std::panic::take_hook();std::panic::set_hook(Box::new(|_|{}));let p1=std::panic::catch_unwind(||a.covariant_difference(&bigger,&psi)).is_err();let large=U1Connection::trivial(&bigger);let p2=std::panic::catch_unwind(||large.to_holonomy_connection(&p)).is_err();std::panic::set_hook(hook);assert!(p1&&p2);println!("foreign_packet_size_mismatches_panic=true");
 let walk=OrientedWalk::new(&p,"a",&[(0,1)]).unwrap();let fam=CoherentPathFamily::new(&p,&a,&[walk.clone(),walk],&[ri(1),ri(1)]).unwrap();assert_eq!(fam.sink_intensity(),ri(4));assert_eq!(fam.holonomy_expansion(),ri(4));assert!(matches!(holonomy_verdict(&p,&a).unwrap(),HolonomyVerdict::GaugeTrivial));let gauge=VertexGauge::new(&p,vec![G::i(),G::one(),G::one()]).unwrap();let transformed=a.gauge_transform(&p,&gauge).unwrap();let transport=gauge_equivalence(&p,&a,&transformed).unwrap().unwrap();assert_eq!(a.gauge_transform(&p,&transport).unwrap(),transformed);println!("valid_interference_expansion_and_gauge_equivalence_replay=PASS");
}
''',encoding='utf-8')
cmd=['rustc','--edition=2021','-Awarnings','-C','overflow-checks=yes','-L','dependency='+str(D)]
for n,p in libs.items():cmd+=['--extern',n+'='+str(p)]
exe=H/(P+'_probe_14.exe');cmd +=[str(src),'-o',str(exe)];c=subprocess.run(cmd,capture_output=True,text=True,timeout=60);run={'command':cmd,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
if not c.returncode:
 x=subprocess.run([str(exe)],capture_output=True,text=True,timeout=45);run.update(exit_code=x.returncode,output=x.stdout+x.stderr)
receipt={'source_files':[{'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in owners.values()],'libraries':[{'extern_name':n,'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for n,p in libs.items()],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'run':run,'limits':'Three unchanged scoped owners; tiny three-vertex carriers and cached lower dependencies. No universal gauge theorem or empirical interference claim.'}
(H/(P+'_validation_14.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in run.items()if k!='command'},indent=2))

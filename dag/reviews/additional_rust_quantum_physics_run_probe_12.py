import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_quantum_physics';D=R/'code/rust/target/debug/deps'
owner=R/'code/rust/core_quantum_physics/src/quantum_import_finite_maps.rs'
assert hashlib.sha256(owner.read_bytes()).hexdigest()=='4f693fe671c5e812db57998a7a6ee7cde4fbef26dfa955b2e233a5908df3ecce'
text=owner.read_text(encoding='utf-8');fragment=''.join(text.splitlines(keepends=True)[:1791]);assert fragment.rstrip().endswith('}')
src=H/(P+'_probe_12.rs');src.write_text(fragment+r'''
fn main(){
 let graph=CarrierGraph::bubble();let phases=[0,1];let got=cycle_invariant_exponents(&graph,&phases,12);assert_eq!(got,vec![0]);assert_ne!(got,vec![1]);
 let bad=dress_cochain_on_tree(&graph,&phases,12,&[1]);assert_ne!(bad[1],0);let good=dress_cochain_on_tree(&graph,&phases,12,&[0]);assert_eq!(good[0],0);
 println!("parallel_edge_holonomy={:?}; expected_chord_holonomy=1; selected_tree1_phase={}",got,bad[1]);
 let truncated=f2_eliminate(&[vec![0]],&[]);let full=f2_eliminate(&[vec![0]],&[1]);assert!(truncated.consistent);assert!(!full.consistent);println!("short_rhs_drops_inconsistent_constraint=true");
 let pi_bad=pi_big_interval(1);let pi_good=pi_big_interval(20);assert!(pi_bad.lo>pi_good.hi);let z_bad=zeta3_big_interval(1);let z_good=zeta3_big_interval(20);assert!(z_bad.lo>z_good.hi);println!("odd_term_pi_and_zeta3_intervals_disjoint_from_valid_even_controls=true");
 let i2=mat24_id(2);let (mult,count,valid)=spectral_multiplicities_and_roots(&i2,1);assert_eq!(mult,vec![2]);assert_eq!(count,2);assert!(valid);let mut mixed=i2.clone();mixed[1][1]=Cyclo24::from_rat(q(-1,1));assert_eq!(mat24_mul(&mixed,&mixed),i2);assert_eq!(mat24_mul(&mat24_dagger(&mixed),&mixed),i2);assert_ne!(mixed,i2);assert_ne!(mixed,mat24_scale(&i2,Cyclo24::from_rat(q(-1,1))));println!("identity2_reported_square_root_count=2; explicit_third_unitary_root=true");
 let r=evaluate_qm211_clock_tower();assert_eq!(r.fourier_d4_square_root_count,8);assert!(r.all_square_roots_unitary_and_square_to_u);println!("fixed_clock_positive_control=true");
}
''',encoding='utf-8')
prior=json.loads((H/(P+'_validation_06.json')).read_text());libs={x['extern_name']:R/x['path']for x in prior['libraries']if x['extern_name']in ['num_bigint','num_rational','num_traits']}
cmd=['rustc','--edition=2021','-Awarnings','-C','overflow-checks=yes','-L','dependency='+str(D)]
for n,p in libs.items():cmd+=['--extern',n+'='+str(p)]
exe=H/(P+'_probe_12.exe');cmd +=[str(src),'-o',str(exe)];c=subprocess.run(cmd,capture_output=True,text=True,timeout=60);run={'command':cmd,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
if not c.returncode:
 x=subprocess.run([str(exe)],capture_output=True,text=True,timeout=60);run.update(exit_code=x.returncode,output=x.stdout+x.stderr)
receipt={'source_files':[{'path':owner.relative_to(R).as_posix(),'sha256':hashlib.sha256(owner.read_bytes()).hexdigest(),'compiled_lines':[1,1791]}],'libraries':[{'extern_name':n,'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for n,p in libs.items()],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'source_excerpt_sha256':hashlib.sha256(fragment.encode()).hexdigest(),'run':run,'limits':'Exact complete source prefix lines1-1791 compiled unchanged with appended main; later import owners and whole crate not compiled. Fixed tiny controls only, no providers/downloads or external numerical constants. Rational alternating-series even controls independently justify disjoint interval counterexamples; root count is a primary-function count, not all unitary roots.'}
(H/(P+'_validation_12.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in run.items()if k!='command'},indent=2))

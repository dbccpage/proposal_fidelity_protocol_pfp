import hashlib,json,pathlib,subprocess,re
R=pathlib.Path(__file__).resolve().parents[2];H=pathlib.Path(__file__).parent;P='additional_rust_quantum_physics';D=R/'code/rust/target/debug/deps'
prior=json.loads((H/(P+'_validation_06.json')).read_text());libs={x['extern_name']:R/x['path']for x in prior['libraries']}
owner=R/'code/rust/core_quantum_physics/src/mub.rs';owners=[owner]+sorted((owner.parent/'mub').glob('*.rs'))
scope={x['path']:x['sha256']for x in json.loads((H/(P+'_scope.json')).read_text())['files']}
for p in owners:assert hashlib.sha256(p.read_bytes()).hexdigest()==scope[p.relative_to(R).as_posix()]
old=H/(P+'_validation_11.json')
if old.exists() and json.loads(old.read_text())['run']['compile_exit']:
 (H/(P+'_validation_11_probe_error.json')).write_bytes(old.read_bytes())
elif old.exists() and json.loads(old.read_text())['run'].get('exit_code'):
 (H/(P+'_validation_11_probe_assumption_error.json')).write_bytes(old.read_bytes())
original=owner.read_text(encoding='utf-8');adapted=re.sub(r'^pub mod (\w+);$',lambda m:'#[path='+json.dumps((owner.parent/'mub'/(m[1]+'.rs')).as_posix())+']\n'+m[0],original,flags=re.M)
assert re.sub(r'^#\[path=.*\]\n','',adapted,flags=re.M)==original
copy=H/(P+'_probe_11_mub.rs');copy.write_text(adapted,encoding='utf-8')
src=H/(P+'_probe_11.rs');src.write_text('#[path='+json.dumps(copy.as_posix())+'] pub mod mub;\npub use cached_quantum::exact_hermitian;\n'+r'''
fn main(){
 use mub::*;use core_number_theory::rational::{rq,ri};use core_number_theory::cyclotomic::Cyc24;
 use linear_algebra::exact_field::matrix as m;
 let d2=MubSystem::mub_d2();assert_eq!(d2.verify_projector_algebra().status,algebra::ProjectorAlgebraStatus::AlgebraVerified);assert!(d2.verify_two_design());
 let rho=m::from_rows(vec![vec![Cyc24::one(),Cyc24::zero()],vec![Cyc24::zero(),Cyc24::zero()]]).unwrap();assert!(d2.verify_exact_reconstruction(&rho));assert_eq!(d2.deterministic_valuation_purity(&[0,0,0]).unwrap(),Cyc24::rat(ri(2)));println!("d2_projector_two_design_reconstruction_and_obstruction=PASS");
 let generic=char_two::build_char_two_mub(2,320).unwrap();assert_eq!(algebra::verify_mub_projector_algebra(&generic,4).status,algebra::ProjectorAlgebraStatus::AlgebraVerified);assert!(char_two::build_char_two_mub(2,319).is_err());
 let odd=odd_prime::build_odd_prime_power_mub::<3>(1,108).unwrap();assert_eq!(algebra::verify_mub_projector_algebra(&odd,3).status,algebra::ProjectorAlgebraStatus::AlgebraVerified);println!("generic_char_two_and_odd_prime_builders=PASS");
 use composite_completion_gate::*;let fabricated=verify_composite_completion_gate(CompositeCompletionInputs{target:CompositeCompletionTarget::Mub6,lower_control_basis_count:None,complete_witness_replayed:true,no_go_certificate_replayed:true});assert_eq!(fabricated.status,CompositeCompletionStatus::CompleteWitnessAccepted);assert!(fabricated.missing_obligations.is_empty());println!("contradictory_boolean_completion_without_witness={:?}",fabricated.status);
 let board=char_two_weyl_board::verify_char_two_weyl_board_schema(2);assert_eq!(board.status,char_two_weyl_board::CharTwoWeylBoardStatus::BoardSchemaVerified);
 let spectral=spectral_lift::verify_char_two_board_spectral_lift(&board);let algebra=projector_algebra::verify_char_two_projector_algebra(&board);let transport=hilbert_transport::verify_char_two_hilbert_transport(&board);
 let ledger=gtmur_projector_ledger::verify_gtmur_projector_ledger(&board,Some(&spectral),Some(&algebra),Some(&transport));assert_eq!(ledger.status,gtmur_projector_ledger::GtmurProjectorLedgerStatus::FiniteLedgerClosed);
 assert_eq!(finite_projector_control::verify_finite_projector_control(&transport,Some(&ledger)).status,finite_projector_control::FiniteProjectorControlStatus::CompleteProjectorMubVerified);println!("q4_board_symbolic_Hilbert_ledger_control=PASS");
 let mut fake_transport=transport.clone();fake_transport.exponent=0;fake_transport.positive_factor_matrix_checks=0;fake_transport.error=Some("not a verified transport".into());let mut fake_ledger=ledger.clone();fake_ledger.exponent=99;fake_ledger.zero_rel_alignment_checks=0;fake_ledger.terminalizer_alignment_checks=0;fake_ledger.error=Some("not a verified ledger".into());let accepted=finite_projector_control::verify_finite_projector_control(&fake_transport,Some(&fake_ledger));assert_eq!(accepted.status,finite_projector_control::FiniteProjectorControlStatus::CompleteProjectorMubVerified);println!("inconsistent_report_control={:?}; exponent={}; zero_rel_checks={}",accepted.status,accepted.exponent,accepted.gtmur_zero_rel_alignment_checks);
 let mut bad=board.clone();bad.dimension=0;let old_hook=std::panic::take_hook();std::panic::set_hook(Box::new(|_|{}));let panics=std::panic::catch_unwind(||spectral_lift::verify_char_two_board_spectral_lift(&bad)).is_err();let overflow=std::panic::catch_unwind(||dimension_stratification::stratify_dimension_with(usize::MAX,&std::collections::BTreeSet::new())).is_err();std::panic::set_hook(old_hook);assert!(panics&&overflow);println!("malformed_spectral_zero_and_dimension_max_panics=PASS");
 use non_cyclic_falser::*;let f=MubAdversarialFalser::try_new().unwrap();let mixed=m::scale(&m::identity::<Cyc12Field>(6).unwrap(),&Cyc12Field::rational(rq(1,6))).unwrap();assert!(f.attack(&vec![mixed;6]).is_err());let tao=build_tao_s6_matrix().unwrap();assert!(verify_chm(&tao).unwrap());assert!(matches!(f.attack(&projectors_from_chm(&tao).unwrap()).unwrap(),FalsificationVerdict::Falsified{..}));println!("MUB6_mixed_effect_refusal_and_Tao_finite_falsification=PASS");
}
''',encoding='utf-8')
cmd=['rustc','--edition=2021','-Awarnings','-C','overflow-checks=yes','-L','dependency='+str(D)]
for n,p in libs.items():cmd+=['--extern',n+'='+str(p)]
exe=H/(P+'_probe_11.exe');cmd +=[str(src),'-o',str(exe)];c=subprocess.run(cmd,capture_output=True,text=True,timeout=60);run={'command':cmd,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
if not c.returncode:
 try:
  x=subprocess.run([str(exe)],capture_output=True,text=True,timeout=60);run.update(exit_code=x.returncode,output=x.stdout+x.stderr)
 except subprocess.TimeoutExpired as e:run.update(timed_out=True,output=str(e.stdout)+str(e.stderr))
receipt={'source_files':[{'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for p in owners],'libraries':[{'extern_name':n,'path':p.relative_to(R).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for n,p in libs.items()],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'module_path_adapter':{'path':copy.relative_to(R).as_posix(),'sha256':hashlib.sha256(copy.read_bytes()).hexdigest(),'only_change':'Inserted absolute path attributes for unchanged original submodules; stripping those attributes reconstructs original mub.rs decoded text exactly. No function/body change.'},'run':run,'limits':'Focused current MUB owner and its submodules compiled by rustc against pinned cached arithmetic/exact-Hermitian dependencies; only q2/q3/q4 and one Tao candidate, no broad Cargo build or exhaustive MUB6 search. Initial out-of-crate module-path setup failure preserved separately, not a source defect.'}
(H/(P+'_validation_11.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in run.items()if k!='command'},indent=2))

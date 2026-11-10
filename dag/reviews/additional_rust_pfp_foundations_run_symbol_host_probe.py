"""Constructor/host invariant boundary with original source and cached libraries."""
import pathlib,json,hashlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=pathlib.Path(__file__).parent;P='additional_rust_pfp_foundations';deps=ROOT/'code/rust/target/debug/deps'
libs={}
for receipt in ['f2','algorithm']:
 for x in json.loads((HERE/(P+'_'+receipt+'_validation.json')).read_text())['libraries']:
  q=ROOT/x['path'];libs[q.name[3:].split('-')[0]]=q
libs['sha2']=max(deps.glob('libsha2-*.rlib'),key=lambda q:q.stat().st_mtime)
owner=ROOT/'code/rust/pfp_runtime/src/symbol_game_host.rs';src=HERE/(P+'_symbol_host_probe.rs');src.write_text('#[path='+json.dumps(owner.as_posix())+'] mod owner;\n'+r'''
use owner::*;use num_rational::BigRational;use num_bigint::BigInt;
fn q(n:i64)->BigRational{BigRational::from_integer(BigInt::from(n))}
fn main(){
 let mut p=SymbolGameProblem::new("synthetic".into(),vec!["a".into(),"b".into()],vec![ProblemEdge{u:"a".into(),v:"b".into(),weight:q(1)}],vec![q(1)]).unwrap();
 p.edges[0].weight=q(-1);p.digest=p.compute_digest();let host=SymbolGameHost::try_new(p).unwrap();assert_eq!(host.section_defect(),q(-1));println!("self_consistent_negative_weight_problem_admitted_with_negative_defect=true");
 let p=SymbolGameProblem::new("synthetic".into(),vec!["a".into(),"b".into()],vec![ProblemEdge{u:"a".into(),v:"b".into(),weight:q(1)}],vec![q(1)]).unwrap();let mut host=SymbolGameHost::try_new(p).unwrap();let pinned=host.problem.digest.clone();host.problem.initial_claims[0]=q(0);assert_ne!(host.problem.compute_digest(),pinned);
 let post=SymbolGameHost::calculate_state_digest(&pinned,&host.current_state_digest,1,&host.section,&q(0));let r=host.process_proposal(&UntrustedProposal{proposer_id:"synthetic".into(),problem_digest:pinned,parent_state_digest:host.current_state_digest.clone(),op:HostMoveOp::Verify,proposed_section:None,dual_witness:None,target_property:Some("ZERO_OBSTRUCTION".into()),target_event_id:None,claimed_post_state_digest:post,claimed_defect:None,rationale:"synthetic".into()});assert!(r.admitted);println!("changed_problem_claim_admitted_under_original_digest=true");
}
''',encoding='utf-8');exe=src.with_suffix('.exe');cmd=['rustc','--edition=2021','-Awarnings','-L','dependency='+str(deps)]
for name,q in libs.items():cmd+=['--extern',name+'='+str(q)]
cmd += [str(src),'-o',str(exe)];c=subprocess.run(cmd,capture_output=True,text=True,timeout=45);attempts=[]
if c.returncode:
 attempts.append({'serde_json':str(libs['serde_json']),'exit':c.returncode,'output':c.stdout+c.stderr})
 slot=next(i for i,s in enumerate(cmd) if s.startswith('serde_json='))
 for q in sorted(deps.glob('libserde_json-*.rlib')):
  if q==libs['serde_json']:continue
  cmd[slot]='serde_json='+str(q);c=subprocess.run(cmd,capture_output=True,text=True,timeout=45);attempts.append({'serde_json':str(q),'exit':c.returncode,'output':c.stdout+c.stderr})
  if not c.returncode:libs['serde_json']=q;break
log={'source_path':owner.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(owner.read_bytes()).hexdigest(),'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'libraries':[{'path':q.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in libs.values()],'command':cmd,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr,'cached_dependency_matching_attempts':attempts,'limits':'Original whole owner included unchanged. Synthetic exact rationals only; public API/in-process caller mutations, not a demonstrated remote mutation path. No provider or original source edits.'}
if not c.returncode:
 r=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15);log.update(exit_code=r.returncode,output=r.stdout+r.stderr)
(HERE/(P+'_symbol_host_validation.json')).write_text(json.dumps(log,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:log[k] for k in ['compile_exit','compile_output','exit_code','output'] if k in log},indent=2))

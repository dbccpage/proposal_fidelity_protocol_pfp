"""Read-only finite public type checks; no stored benchmark input."""
import hashlib,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2]; HERE=pathlib.Path(__file__).parent
P='additional_rust_pfp_foundations';deps=ROOT/'code/rust/target/debug/deps'
prior=json.loads((HERE/(P+'_coda_validation.json')).read_text())
libs={pathlib.Path(x['path']).name[3:].split('-')[0]:ROOT/x['path'] for x in prior['libraries']}
parent=max(deps.glob('libpfp-*.rlib'),key=lambda p:p.stat().st_mtime);libs['pfp']=parent
fps=deps.parent/'.fingerprint'; fp=json.loads((fps/parent.stem[3:]/'lib-pfp.json').read_text())
for name in ['core_wdp','blake3']:
 ident=next(d[3] for d in fp['deps'] if d[1]==name)
 for item in fps.glob('*/lib-'+name):
  if int.from_bytes(bytes.fromhex(item.read_text()),'little')==ident:
   libs[name]=deps/('lib'+name+'-'+item.parent.name.rsplit('-',1)[1]+'.rlib');break
owners=[ROOT/'code/rust/pfp/src/genesis.rs',ROOT/'code/rust/pfp/src/prime.rs']
src=HERE/(P+'_genesis_probe.rs');exe=src.with_suffix('.exe')
src.write_text('mod foundation { pub use pfp::foundation::PrimitiveDifference; }\n'+''.join('#[path='+json.dumps(x.as_posix())+'] mod '+x.stem+';\n'for x in owners)+r'''
fn main(){
 use genesis::*;
 let selfloop=ExaminerChallenge::new(1,[(0,0)]).unwrap();
 assert!(verify_examiner(&selfloop).is_asymmetric());
 println!("self_loop_is_asymmetric=true");
 let triangle=ExaminerChallenge::new(3,[(0,1),(1,2),(2,0)]).unwrap();
 assert!(verify_examiner(&triangle).is_strict());
 println!("directed_three_cycle_is_strict=true; transitivity_is_not_checked");
 let codec=PresentationCodec::with_glyphs(0x80,0x81).unwrap();
 assert!(codec.scan(&codec.render(OpaqueDatum::new(),1)).is_err());
 println!("admitted_nonascii_codec_refuses_own_render=true");
 let regime=ObserverRegime::admit_contexts(vec![ObserverContext::new("a",1),ObserverContext::new("b",1)],evaluate_depth).unwrap();
 assert_eq!(regime.contexts().len(),2);
 println!("same_wrap_different_names_count_twice=true");
 static COUNTER:std::sync::atomic::AtomicUsize=std::sync::atomic::AtomicUsize::new(0);
 fn impure(_: &AdmittedContext)->num_rational::BigRational {
  num_rational::BigRational::from_integer(COUNTER.fetch_add(1,std::sync::atomic::Ordering::SeqCst).into())
 }
 let regime=ObserverRegime::admit_contexts(vec![ObserverContext::new("context",1)],impure).unwrap();
 assert!(!regime.equivalent(OpaqueDatum::new(),OpaqueDatum::new()).unwrap());
 println!("stateful_evaluator_breaks_reflexivity=true");
 let out=prime::prime_replay_decide(&serde_json::json!({"steps":[{"prime_step":255,"op":"CRT","executed":false,"message":"not executed"}]})).unwrap();
 assert!(out.conforms);assert_eq!(out.decision,"Terminalized");
 println!("unexecuted_compound_operation_conforms_and_terminalizes=true");
 let out=prime::prime_replay_decide(&serde_json::json!({"receipt":{"letter_tape":"CRT","terminal":"CallerChosen"}})).unwrap();
 assert!(out.conforms);assert_eq!(out.decision,"CallerChosen");
 println!("receipt_without_gamma_or_step_evidence_conforms=true");
}
''',encoding='utf-8')
cmd=['rustc','--edition=2021','-Awarnings','-L','dependency='+str(deps)]
for name,path in libs.items():cmd+=['--extern',name+'='+str(path)]
cmd += [str(src),'-o',str(exe)]
c=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
run={'command':cmd,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
if c.returncode==0:
 r=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15);run.update(exit_code=r.returncode,output=r.stdout+r.stderr)
receipt={'source_files':[{'path':x.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(x.read_bytes()).hexdigest()}for x in owners],'libraries':[{'path':x.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(x.read_bytes()).hexdigest()}for x in libs.values()],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'runs':[run],'limits':'Unchanged genesis and prime modules, actual PrimitiveDifference reexported from cached PFP. Only constructed finite values and an atomic counter; no generator seed, stored cases, provider, filesystem dispatch or private input. Directed cycle result concerns missing transitivity, not the narrower asymmetric predicate.'}
(HERE/(P+'_genesis_validation.json')).write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in run.items()if k!='command'},indent=2))

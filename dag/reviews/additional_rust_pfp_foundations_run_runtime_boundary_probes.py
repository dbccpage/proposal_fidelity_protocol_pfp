"""Small synthetic counterexamples against complete original runtime owners."""
import pathlib,json,hashlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[2];HERE=pathlib.Path(__file__).parent;P='additional_rust_pfp_foundations';deps=ROOT/'code/rust/target/debug/deps'
prior=json.loads((HERE/(P+'_f2_validation.json')).read_text());libs={pathlib.Path(x['path']).name[3:].split('-')[0]:ROOT/x['path'] for x in prior['libraries']}
for name in ['sha2','hex','ryu']:libs[name]=max(deps.glob('lib'+name+'-*.rlib'),key=lambda p:p.stat().st_mtime)
names=['research_evidence','synthesis_dag','diff_parser','lean_verify','jcs'];owners=[ROOT/'code/rust/pfp_runtime/src'/ (n+'.rs') for n in names]
src=HERE/(P+'_runtime_boundary_probe.rs');src.write_text('\n'.join('#[path='+json.dumps(q.as_posix())+'] mod '+n+';' for n,q in zip(names,owners))+r'''
fn main(){
 use research_evidence::*;
 let intake=IntakeResearchSourcesUseCase;let a=intake.execute("a",&[("id-a".into(),"a.rs".into(),b"same".to_vec())]);let mut b=intake.execute("b",&[("id-b".into(),"b.rs".into(),b"same".to_vec())]);assert_eq!(a.source_manifest_root,b.source_manifest_root);
 b.receipts[0].observed_sha256=None;b.receipts[0].observed_byte_count=None;b.source_manifest_root="wrong".into();assert!(VerifyResearchClaimUseCase.execute(&b));println!("research_manifest_omits_identity_and_verifier_accepts_inconsistent_receipt=true");
 let mut dag=synthesis_dag::ModuleDagV1::new();dag.add_module("a",&["missing"]);assert!(dag.next_schedulable_module().is_none());dag.freeze_module("a","not valid code").unwrap();assert!(dag.is_all_frozen());println!("synthesis_freezes_missing_dependency_without_oracle=true");
 for (label,patch) in [("nonnumeric_hunk_position","--- a/x\n+++ b/x\n@@ -wrong,1 +wrong,1 @@\n-a\n+b\n"),("unsafe_binary_metadata","diff --git a/x b/x\nBinary files a/../escape and b/../escape differ\n"),("header_only_second_section","--- a/x\n+++ b/x\n@@ -1 +1 @@\n-a\n+b\n--- a/y\n+++ b/y\n")]{let r=diff_parser::parse_unified_diff(patch);assert!(r.is_valid,"{label}: {r:?}");println!("diff_accepts_{label}={:?}",r.touched_paths);}
 let r=lean_verify::scan_lean_sources(&[lean_verify::SourceFileEntry{file:"synthetic.lean".into(),content:"theorem t : False := by/- comment -/sorry".into()}],&[]);assert!(r.clean);println!("lean_comment_boundary_hides_sorry=true");
 let req=lean_verify::LeanAuditRequest{axioms_output:"'t' depends on axioms: [sorryAx]\\n".replace("\\n","\n")+"'t' does not depend on any axioms",policy:vec![],required_declarations:vec!["t".into()],build_success:true,harness_elaborated:true,forbidden_findings:vec![]};assert_eq!(lean_verify::audit_lean_verification(&req).status,"PASS");println!("lean_duplicate_declaration_overwrites_disallowed_axiom=true");
 for raw in ["01","1.","1e01","\\u000bnull"] {let text=raw.replace("\\u000b","\u{000b}"); let j=jcs::canonicalize_str(&text);let strict=serde_json::from_str::<serde_json::Value>(&text);println!("jcs_raw={raw:?}: jcs={j:?}; strict={}",strict.is_ok());}
 let raw="\"a\nb\"";assert!(jcs::canonicalize_str(raw).is_ok());assert!(serde_json::from_str::<serde_json::Value>(raw).is_err());println!("jcs_accepts_raw_newline_in_string=true");
 let huge="100000000000000000000000000000000000000000000000000";assert!(jcs::canonicalize_str(huge).is_ok());println!("jcs_skips_integer_ceiling_beyond_i128=true");
 let result=std::panic::catch_unwind(||jcs::canonicalize_value(&serde_json::json!(i64::MIN)));println!("jcs_i64_min={result:?}");
 let mut out=String::new();jcs::serialize_jcs(&jcs::JcsValue::Object(vec![("z".into(),jcs::JcsValue::Null),("a".into(),jcs::JcsValue::Null),("z".into(),jcs::JcsValue::Null)]),&mut out).unwrap();assert_eq!(out,"{\"z\":null,\"a\":null,\"z\":null}");println!("jcs_public_serializer_keeps_unsorted_duplicate_keys=true");
}
''',encoding='utf-8')
runs=[]
for mode in ['yes','no']:
 exe=HERE/(P+'_runtime_boundary_probe_'+mode+'.exe');cmd=['rustc','--edition=2021','-Awarnings','-C','overflow-checks='+mode,'-L','dependency='+str(deps)]
 for name,q in libs.items():cmd+=['--extern',name+'='+str(q)]
 cmd += [str(src),'-o',str(exe)];c=subprocess.run(cmd,capture_output=True,text=True,timeout=45);row={'overflow_checks':mode,'command':cmd,'compile_exit':c.returncode,'compile_output':c.stdout+c.stderr}
 if not c.returncode:
  r=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15);row.update(exit_code=r.returncode,output=r.stdout+r.stderr)
 runs.append(row)
receipt={'source_files':[{'path':q.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in owners],'libraries':[{'path':q.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in libs.values()],'probe_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'runs':runs,'limits':'Complete original modules included unchanged. Only synthetic in-memory inputs; no patch application, filesystem source changes, Lean compiler, provider or full-crate test. serde_json comparison checks parser discrepancy only; no claim of complete RFC conformance testing.'}
(HERE/(P+'_runtime_boundary_validation.json')).write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps([{k:v for k,v in r.items() if k!='command'} for r in runs],indent=2))

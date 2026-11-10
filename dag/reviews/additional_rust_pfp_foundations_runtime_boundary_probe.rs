#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/pfp_runtime/src/research_evidence.rs"] mod research_evidence;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/pfp_runtime/src/synthesis_dag.rs"] mod synthesis_dag;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/pfp_runtime/src/diff_parser.rs"] mod diff_parser;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/pfp_runtime/src/lean_verify.rs"] mod lean_verify;
#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/pfp_runtime/src/jcs.rs"] mod jcs;
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

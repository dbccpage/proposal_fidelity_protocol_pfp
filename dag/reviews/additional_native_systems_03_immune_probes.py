"""Public synthetic PCIV counterexamples; no benchmark, model, or credential access."""
import importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location("runner",Path(__file__).with_name("additional_native_systems_probes.py"))
runner=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
runner.RUST=r'''
use core_prompt_civilization::{immune::{clonal::DetectorClone,mhc::{MhcPresentationWindow,slice_count}},forge::MetaProposalRegistryV1,lamarckian::LamarckianCochainTrackerV1,matching::ReferenceTrailEvaporationCalculatorV1,civilization,antimorphism::{HarvestRow,JudgeSuiteExporter}};
use num_rational::Rational64;
use serde_json::json;
fn main(){
 std::panic::set_hook(Box::new(|_|{}));
 let clone=DetectorClone::new("synthetic".into(),1,1,0);
 let a=clone.compute_decayed_affinity(60,1);let b=clone.compute_decayed_affinity(61,1);
 println!("{}",json!({"probe":"clonal_halving_cap","generation60":a.to_string(),"generation61":b.to_string(),"equal":a==b,"expected61":"1/2305843009213693952"}));
 let window=MhcPresentationWindow::new(1,10);
 println!("{}",json!({"probe":"mhc_slice_count","actual":window.present_slices("abc").len(),"claimed":slice_count(3,1,10).unwrap()}));
 let mut reg=MetaProposalRegistryV1::new(5);reg.register_proposal(5,"synthetic-new-checker");
 println!("{}",json!({"probe":"same_epoch_meta_proposal","active":reg.get_active_checker_set(5).unwrap(),"external_enactment_called":false}));
 let overflow=std::panic::catch_unwind(||LamarckianCochainTrackerV1::verify_mutation(Rational64::from_integer(i64::MAX),Rational64::from_integer(-2),1,b"x",b"x",&[(0,1)]));
 println!("{}",json!({"probe":"rational64_descent_overflow","panicked":overflow.is_err()}));
 let zero=std::panic::catch_unwind(||ReferenceTrailEvaporationCalculatorV1::compute_evaporated_weight(&[0],1,0));
 println!("{}",json!({"probe":"zero_halflife","panicked":zero.is_err()}));
 let reviewed=civilization::execute(&json!({"operation":"promote_reviewed","prompt_id":"p","state":{"p":{"prompt_id":"p","content":"synthetic","tier":"CANDIDATE","pagerank_score":"0"}}})).unwrap();
 println!("{}",json!({"probe":"reviewed_without_holdout","result":reviewed["value"],"holdout_evidence_supplied":false}));
 let row=HarvestRow{task_id:"synthetic-a".into(),probe_id:"toy-probe".into(),domain_id:"toy".into(),model:"none".into(),mode:"replay".into(),raw_response:"toy-response".into(),disposition:"A".into(),confirmed:true,classifier_digest:"toy-classifier".into(),billed_cost_micro_usd:None};
 for partition in 0..32 {
  let first=JudgeSuiteExporter::export(&[row.clone()],partition,false).unwrap();
  if first.hidden_suite.len()!=1 {continue;}
  let mut changed=row.clone();changed.disposition="B".into();changed.classifier_digest="different-classifier".into();
  let second=JudgeSuiteExporter::export(&[changed],partition,false).unwrap();
  println!("{}",json!({"probe":"suite_commitment_omits_labels","hidden_rows":1,"labels_and_classifier_changed":true,"commitment_unchanged":first.hidden_commitment_sha256==second.hidden_commitment_sha256}));
  break;
 }
}
'''
if __name__=="__main__": print(json.dumps(runner.run(),indent=2))


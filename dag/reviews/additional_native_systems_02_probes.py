"""Public synthetic API probes for the second native audit; no production edits.

Reuses the first checkpoint's offline Cargo/rustc runner, replacing only the
temporary program. No historical probes are rerun by this script.
"""
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "native_audit_runner", Path(__file__).with_name("additional_native_systems_probes.py")
)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
runner.RUST = r'''
use core_epistemic_immune_system::activation_ports::DigestQuorum;
use core_epistemic_immune_system::anti_skill::{AntiSkillSpecV2,FailureClass};
use core_operad_theory::kernel::*;
use core_operad_theory::foundation::{SpanOperand,OperadColour};
use core_prompt_civilization::fitness::reduce_selected_attempt_outcome;
use serde_json::json;
const D:&str="sha256:0000000000000000000000000000000000000000000000000000000000000000";
fn op(id:&str, version:&str, grade:InvocationGrade)->OperationSpec {
 OperationSpec::new(OperationSpecInput {
  operation_id:id,version,input_ports:vec![PortSpec::new("in","State","any").unwrap()],
  output_port:PortSpec::new("out","State","any").unwrap(),executor_ref:"executor",executor_digest:D,
  tool_refs:vec![],effects:vec![],invocation_grade:grade,authority_effect:AuthorityEffect::None,authority_ceiling:AuthorityEffect::None
 }).unwrap()
}
fn license(keys:Vec<String>)->AgentLicense {
 AgentLicense::new("agent",keys,vec!["State".into()],vec!["executor".into()],vec![],vec![],AuthorityEffect::None,"active",D).unwrap()
}
fn main(){
 let quorum=DigestQuorum::try_new(&["aa","aa","aa","bb","bb"],2);
 println!("{}",json!({"probe":"two_threshold_leaders","result":format!("{quorum:?}"),"expected":"SplitBrain"}));
 let one=AntiSkillSpecV2::propose("a",FailureClass::BoundaryLeakage,"bBoundaryLeakagec","first",1);
 let two=AntiSkillSpecV2::propose("aBoundaryLeakageb",FailureClass::BoundaryLeakage,"c","second",1);
 println!("{}",json!({"probe":"anti_skill_hash_framing","equal_ids":one.id==two.id,"id":one.id,"different_pattern":one.pattern!=two.pattern,"different_scope":one.target_scope!=two.target_scope}));
 let entry=OperationTerm::Primitive(op("entry","v1",InvocationGrade::Entry));
 let middle=OperationTerm::Primitive(op("middle","v1",InvocationGrade::Discipline));
 let nested=substitute(&middle,0,&entry).unwrap();
 let outer=substitute(&entry,0,&term_from_normalized(&nested)).unwrap();
 let allowed=license(vec!["entry@v1".into(),"middle@v1".into()]);
 let accepted=authorize_normalized_term(&allowed,&outer);
 println!("{}",json!({"probe":"entry_over_discipline_over_entry","authorized":accepted.is_ok(),"result":accepted.err().map(|x|x.code)}));
 let one=op("a@b","c",InvocationGrade::Discipline);
 let two=op("a","b@c",InvocationGrade::Discipline);
 let allowed=license(vec![one.key()]);
 println!("{}",json!({"probe":"operation_license_key_framing","equal_keys":one.key()==two.key(),"key":one.key(),"different_canonical_ids":one.canonical_id().unwrap()!=two.canonical_id().unwrap(),"second_authorized":authorize_term(&allowed,&OperationTerm::Primitive(two)).is_ok()}));
 let bad=SpanOperand::new("synthetic.txt",1,1,0,999,OperadColour::new("State").unwrap(),"not-a-digest","a",None);
 println!("{}",json!({"probe":"span_constructor_integrity","accepted":bad.is_ok(),"integrity":bad.as_ref().map(|x|x.verify_integrity()).ok()}));
 let event=ExecutionEvent::new(ExecutionEventInput {
  run_id:"run".into(),sequence:0,plan_digest:D.into(),operation_spec_digest:D.into(),executor_digest:D.into(),policy_digest:D.into(),environment_digest:D.into(),validator_ref:"validator".into(),validator_digest:D.into(),verifier_ref:"verifier".into(),verifier_digest:D.into(),admission_receipt_refs:vec![],inputs:vec![],outputs:vec![],parent_event_refs:vec![],budget:BudgetTransition{before:1,after:2},outcome_code:"ok".into(),outcome_digest:D.into(),authority_effect:AuthorityEffect::None
 });
 println!("{}",json!({"probe":"execution_event_budget_increase","budget_constructor_refuses":BudgetTransition::new(1,2).is_err(),"event_constructor_accepts":event.is_ok()}));
 println!("{}",json!({"probe":"empty_mandatory_outcome","outcome":reduce_selected_attempt_outcome(&[],"AllowedTask",None),"unknown_outcome_with_refusal":reduce_selected_attempt_outcome(&["unrecognized"],"RefusalRequired",Some("ValidRefusal"))}));
}
'''

if __name__ == "__main__":
    print(json.dumps(runner.run(), indent=2))

#[path="../../code/rust/pfp_runtime/src/canonical.rs"] mod canonical;
#[path="../../code/rust/pfp_runtime/src/rewriting/mod.rs"] mod rewriting;
use rewriting::*;
fn main(){
    let presentation=Presentation{signature:vec!["a".into()],rules:vec![Rule{name:"shrink".into(),lhs:"aa".into(),rhs:"a".into()}]};
    let mut claim=CriticalPeakClaim{source:"aaa".into(),left:ReductionPath{steps:vec![ReductionStep{rule:"shrink".into(),position:0}],endpoint:"aa".into()},right:ReductionPath{steps:vec![ReductionStep{rule:"shrink".into(),position:1}],endpoint:"aa".into()},join:None,steps_inspected:0,step_budget:100};
    let mut pins=PresentationPins::empty();pins.pin("shrink",&presentation);
    let silent=evaluate_peak_pinned(&presentation,&claim,&pins);assert!(matches!(silent.verdict,PeakVerdict::Joined{..}));
    assert_eq!(apply(&presentation.rules[0],"aa",0),Some("a".into()));
    claim.join=Some("a".into());let spoken=evaluate_peak_pinned(&presentation,&claim,&pins);assert!(matches!(spoken.verdict,PeakVerdict::NeedsEvidence{..}));
    println!("{{\"identical_endpoints_later_common_reduct_refused\":true,\"without_declaration\":\"{}\",\"with_true_declaration\":\"{}\"}}",silent.token(),spoken.token());
    println!("verdict={:?}",spoken.verdict);
}

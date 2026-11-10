#[path="../../code/rust/pfp_runtime/src/operad.rs"] mod operad;
use operad::*;
use std::collections::BTreeMap;
fn col(x:&str)->PromptColour{PromptColour::Custom(x.into())}
fn leaf(x:&str)->OperadTree{OperadTree::leaf(LeafTextSpan::new(x,col(x),"",[0,0]).unwrap())}
fn main(){
    std::panic::set_hook(Box::new(|_|{}));
    let span=LeafTextSpan::new("utf8",PromptColour::RawTextSpan,"",[1,2]).unwrap();
    let utf8=std::panic::catch_unwind(||span.verify_against_document("é")).is_err();assert!(utf8);
    let bindings=BTreeMap::from([("x".into(),"1".into())]);
    let false_witness=RefutationWitness{equation:"unrelated".into(),evaluation:"1 != 1".into(),action:"ignored".into()};
    let decoy=AnnihilatorDecoy{id:"d".into(),description:"d".into(),decoy_candidate:DecoyCandidate{bindings:bindings.clone(),claimed_sum:None},refutation_witness:false_witness.clone()};
    let false_refutation=matches!(decoy.evaluate(&bindings,Some(&false_witness)),Ok(AnnihilatorDisposition::Neutralized{..}));assert!(false_refutation);
    let op=PromptOperator::new("outer",vec![col("A"),col("B")],col("R"),"").unwrap();
    let inner=PromptOperator::new("inner",vec![col("X"),col("Y")],col("A"),"").unwrap();
    let inner_tree=OperadTree::node(inner,vec![leaf("X"),leaf("Y")]).unwrap();
    let tree=OperadTree::node(op.clone(),vec![inner_tree,leaf("B")]).unwrap();
    let conversion=tree.to_operation_term();assert!(conversion.is_err());
    let null=OperadTree::null_tree("ideal","reason",col("A"));
    let absorbed=OperadTree::node(op.clone(),vec![null.clone(),leaf("B")]).unwrap();assert_eq!(absorbed.output_colour(),col("A"));assert_ne!(absorbed.output_colour(),op.target_colour);
    let oob_null=tree.graft(999,&null);assert!(oob_null.is_ok());
    println!("{{\"utf8_boundary_panics\":{utf8},\"false_refutation_neutralized\":{false_refutation},\"valid_expanding_tree_conversion_refused\":true,\"null_absorption_changes_output_colour\":true,\"null_graft_ignores_slot_bounds\":true}}");
    println!("conversion_refusal={:?}",conversion.unwrap_err());
}

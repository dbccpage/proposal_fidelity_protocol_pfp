#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/pfp_runtime/src/decode_control.rs"] mod owner;

fn main(){let receipt=owner::DecodeControlReceiptV1{schema_version:owner::DECODE_RECEIPT_SCHEMA.into(),receipt_id:"synthetic".into(),case_id:"synthetic".into(),control_kind:"LOGIT_BIAS".into(),allowed_tokens:vec![],output_tokens:vec![],logit_biases:vec![(1,i32::MIN)],grammar_sha256:None,authority_effect:"None".into()};
let r=std::panic::catch_unwind(||owner::verify_decode_receipt(&receipt)); match r {Err(_)=>println!("i32_min=panic"),Ok(owner::DecodeVerificationVerdict::Pass{..})=>println!("i32_min=pass"),Ok(other)=>println!("i32_min={other:?}")}}

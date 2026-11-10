#[path="C:/Users/a343o/source/repos/proposal_fidelity_protocol_pfp/code/rust/core_contracts/src/authorization_basis.rs"] mod owner;

use owner::*;use std::collections::{HashMap,HashSet};
fn transcript(start:u64,end:u64)->CollectionTranscript {let mut obs=HashMap::new();for id in MANDATORY_SOURCE_SET{obs.insert(id.into(),SourceObservation::new(id,[0;32],0,9999));}CollectionTranscript{epoch_start:start,epoch_end:end,observations:obs}}
fn main(){
 let cut=ConsistentAuthorizationCut::construct(transcript(100,1),transcript(2,0)).unwrap();
 assert!(cut.transcript_1().epoch_start>cut.transcript_1().epoch_end);println!("reversed_intervals_and_outside_observation_epochs_admitted=true");
 let mut leases=LeaseStore::new(0);leases.register_lease("t".into(),"me".into(),"base".into(),HashSet::new());let fence=leases.acquire_landing_fence("t","me",&HashSet::new()).unwrap();
 let forged=VerifiedOperatorSignature{operator_id:"never-verified".into(),sealed_commit_sha:"sealed".into(),base_sha:"base".into(),tree_delta_digest:[0;32],policy_digest:[0;32]};
 let mut permit=Lander::admit(fence.clone(),AuthorizationBasis::OperatorSignature{cut:cut.clone(),verified_signature:forged},"unbound-candidate","sealed").unwrap();
 let cloned=permit.clone();permit.candidate_sha="changed-after-admission".into();assert_ne!(permit.candidate_sha,cloned.candidate_sha);println!("public_signature_fabrication_and_cloneable_mutable_permit=true");
 let mut trust=TrustStore::new();let key=[7;32];trust.register_trusted_key("op",key.to_vec());let mut mac=blake3::Hasher::new_keyed(&key);mac.update(b"abc");mac.update(&[1;32]);mac.update(&[2;32]);let tag=mac.finalize();
 let a=trust.verify_signature("op","ab","c",&[1;32],&[2;32],tag.as_bytes()).unwrap();let b=trust.verify_signature("op","a","bc",&[1;32],&[2;32],tag.as_bytes()).unwrap();assert_ne!(a,b);println!("distinct_commit_base_pairs_accept_same_mac=true");
}

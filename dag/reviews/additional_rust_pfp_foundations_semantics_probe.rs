#![allow(dead_code)]
#[path = "../../code/rust/core_types/src/q_continuum.rs"] mod q_continuum;
#[path = "../../code/rust/core_solvers/src/router_plan_grammar.rs"] mod router_plan_grammar;
#[path = "../../code/rust/core_solvers/src/solver_cohomology_sheaf.rs"] mod solver_cohomology_sheaf;
#[path = "../../code/rust/core_solvers/src/solver_cohomology_mayer_vietoris.rs"] mod solver_cohomology_mayer_vietoris;
#[path = "../../code/rust/core_solvers/src/solver_fixpoint_operator.rs"] mod solver_fixpoint_operator;
#[path = "../../code/rust/core_solvers/src/solver_descent_gradient.rs"] mod solver_descent_gradient;
#[path = "../../code/rust/core_solvers/src/solver_sat_multiscale_repair.rs"] mod solver_sat_multiscale_repair;
fn main() {
 use q_continuum::*;
 let scope=AuthorityScope::new("finite");
 let mut result=DescentResult::supported("o",scope.clone(),Witness::new("w","test","supplied","supplied"));
 result.residual=Some(Residual::new("r","o",ObstructionKind::MissingWitness,"unresolved"));
 let mut trace=AuthorityTrace::new("c",scope);
 trace.record_descent_result(result);
 println!("supported_with_residual_is_terminal={}",trace.strength==AuthorityStrength::TerminalWithinScope);
 println!("same_result_residual_dropped={}",trace.residuals.is_empty());
 use router_plan_grammar::*;
 let grammar=FinitePlanGrammarV1{grammar_id:"g".into(),plan_kind:PlanKind::SameLevelRepair,cost_order:CostOrder::Lexicographic,cost_dimension:1,candidate_plan_ids:vec!["unevaluated".into()],authority_effect:"None".into()};
 let declaration=SearchDeclarationV1::new("g","wrong-digest","p",CostOrder::Lexicographic,1,2).unwrap();
 let frontier=route_declared_finite_grammar(&declaration,&grammar,&[]).unwrap();
 println!("unevaluated_wrong_digest_grammar_gets_no_verified_plan={}",frontier.terminal==FrontierTerminal::NoVerifiedPlan);
 let outsider=DeclaredPlanEvaluationV1{grammar_id:"g".into(),plan_id:"outside-grammar".into(),status:EvaluationStatus::Verified,cost:vec![0],replay_receipt_ref:String::new(),rejection_reason:String::new(),authority_effect:"None".into()};
 println!("unreplayed_outside_candidate_admitted={}",route_declared_finite_grammar(&declaration,&grammar,&[outsider]).unwrap().terminal==FrontierTerminal::VerifiedFrontier);
 use solver_cohomology_sheaf::*;
 let invalid=SheafCochainComplex{cochain_dimensions:vec![1,1,1],coboundaries:vec![nalgebra::DMatrix::identity(1,1),nalgebra::DMatrix::identity(1,1)]};
 println!("nonzero_chain_with_nan_tolerance_admitted={}",validate_complex(&invalid,f64::NAN).is_ok());
 println!("nonzero_chain_with_valid_tolerance_refused={}",validate_complex(&invalid,1e-9).is_err());
 use solver_cohomology_mayer_vietoris::domain_hash_vertex;
 println!("domain_boundary_collision={}",domain_hash_vertex(b"bc",b"a")==domain_hash_vertex(b"c",b"ab"));
 use solver_sat_multiscale_repair::*;
 struct Lower;
 impl CandidateGenerator<Level,Level> for Lower{fn generate(&self,_:&Level)->Vec<Level>{vec![Level{phi:0.0}]}}
 let p=run_alternating_projection_loop(Level{phi:1.0},&[Box::new(Lower)]);
 println!("repair_is_unchanged_resolution={}",p.phi_star==1.0 && p.dichotomy==ProjectionDichotomy::Resolution);
 println!("finished_nonempty_repair_reports_not_converged={}",!p.converged);
}

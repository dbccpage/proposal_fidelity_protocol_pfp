#![allow(dead_code)]
#[path = "../../code/rust/core_solvers/src/solver_crn_deficiency.rs"]
mod solver_crn_deficiency;
#[path = "../../code/rust/core_solvers/src/solver_fixpoint_operator.rs"]
mod solver_fixpoint_operator;
#[path = "../../code/rust/core_solvers/src/solver_quantum_lefschetz_thimble.rs"]
mod solver_quantum_lefschetz_thimble;
#[path = "../../code/rust/core_solvers/src/solver_gauge_yang_mills.rs"]
mod solver_gauge_yang_mills;
#[path = "../../code/rust/core_solvers/src/cert_phi1_distribution.rs"]
mod cert_phi1_distribution;
#[path = "../../code/rust/core_solvers/src/compliance.rs"]
mod compliance;
#[path = "../../code/rust/core_solvers/src/solver_spectrum_laplacian.rs"]
mod solver_spectrum_laplacian;
use solver_crn_deficiency::{Complex, Reaction, ReactionNetwork};
use solver_fixpoint_operator::FixpointConverge;
use solver_quantum_lefschetz_thimble::{Action,C64,LefschetzThimbleSolver};
struct Quadratic;
impl Action for Quadratic {
    fn gradient(&self,p:&[C64])->Option<Vec<C64>> {Some(p.to_vec())}
    fn hessian(&self,_:&[C64])->Option<Vec<Vec<C64>>> {None}
    fn action_value_complex(&self,p:&[C64])->Option<C64> {Some(p[0]*p[0]/2.0)}
}
fn main(){
    let a=Complex::single("A",1);
    let network=ReactionNetwork::new(vec![Reaction::new(a.clone(),a.clone()),Reaction::new(Complex::zero(),a)]);
    let report=network.evaluate();
    // N=[0,1] has rational rank1; the implementation consumes its only row on the zero column.
    assert_eq!(report.stoichiometric_rank,0);
    println!("zero_first_column_rank_underestimated=true");
    println!("reported_deficiency={}",report.deficiency);
    let action=Quadratic;
    let solver=LefschetzThimbleSolver::new(&action,0.01,0.0);
    let first=solver.step(solver.initial_state(vec![C64::new(1.0,1.0)]));
    let second=solver.step(first);
    assert!((second.im_s-0.99980001).abs()<1e-12);
    assert!(second.im_s_drift<0.00000002);
    assert!((1.0-second.im_s).abs()>0.00019);
    println!("origin_drift_erased_by_repeated_negative_changes=true");
    // This uses an actual holomorphic quadratic with its correct gradient.
    use solver_gauge_yang_mills::{GaugeGroup,Manifold,YangMillsProblem,analyze_yang_mills};
    let abelian=GaugeGroup::Product(Box::new(GaugeGroup::U1),Box::new(GaugeGroup::U1));
    assert!(!abelian.is_abelian());
    println!("product_of_two_u1_groups_classified_nonabelian=true");
    let single=analyze_yang_mills(&YangMillsProblem::su_n(2,Manifold::s4()));
    let mut product=YangMillsProblem::su_n(2,Manifold::s4());
    product.group=GaugeGroup::Product(Box::new(GaugeGroup::SU(2)),Box::new(GaugeGroup::SU(2)));
    let doubled=analyze_yang_mills(&product);
    assert_eq!(single.instanton_moduli_dim,Some(5));
    assert_eq!(doubled.instanton_moduli_dim,Some(34));
    println!("product_dimension_not_sum_of_factors=true");
    use cert_phi1_distribution::*;
    use num_bigint::BigInt;
    use num_rational::BigRational;
    let receipt=||Obl1aTheoremReceipt::from_source_hashes(OBL1A_LEAN_SOURCE_SHA256,OBL1A_LEAN_AUDIT_SHA256).unwrap();
    let valid=DistributionBoundVerifier::verify(BigRational::from_integer(BigInt::from(1)),vec![BigRational::from_integer(BigInt::from(1))],receipt());
    assert!(valid.is_ok());
    let bad=std::panic::catch_unwind(|| DistributionBoundVerifier::verify(BigRational::new_raw(BigInt::from(1),BigInt::from(0)),vec![BigRational::from_integer(BigInt::from(1))],receipt()));
    println!("distribution_zero_denominator_panics={}",bad.is_err());
    assert!(bad.is_err());
    use solver_spectrum_laplacian::*;
    use compliance::Solver;
    let parity=std::panic::catch_unwind(||parity_shadow_check(&[vec![1i128<<126]],&[vec![4]],&[vec![1i128<<126]]));
    println!("parity_integer_overflow_panics={}",parity.is_err());
    println!("parity_wraparound_false_zero={}",parity.as_ref().is_ok_and(|r|r.delta1_delta0_zero));
    assert!(parity.is_err() || parity.unwrap().delta1_delta0_zero);
    let negative=QObstructionSolver::default().solve(&QObstructionInput{coboundary:nalgebra::DMatrix::zeros(0,1),defect_potential:nalgebra::DMatrix::from_row_slice(1,1,&[-1000.0])}).unwrap();
    let evolved=imaginary_time_evolve(&negative.value,&[1.0],1.0).unwrap();
    assert!(evolved[0].is_infinite());
    println!("valid_negative_potential_evolution_returns_infinity=true");
    let shifted=QObstructionSolver::default().solve(&QObstructionInput{coboundary:nalgebra::DMatrix::zeros(0,2),defect_potential:nalgebra::DMatrix::from_row_slice(2,2,&[1000.0,0.0,0.0,1001.0])}).unwrap();
    let ratio=s3_excited_ground_ratio(&shifted.value,&[1.0,1.0],1.0).unwrap();
    assert!(ratio.0.is_nan() && ratio.1.is_finite());
    println!("positive_shift_ratio_returns_nan=true");
}

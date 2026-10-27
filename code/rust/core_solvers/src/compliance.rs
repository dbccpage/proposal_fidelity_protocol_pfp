use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

// -----------------------------
// 1) FACT-ONLY SOLVER INTERFACE
// -----------------------------

pub(crate) mod sealed {
    pub trait SolverSealed {}
}

#[derive(Debug, Clone, PartialEq)]
pub struct SolverDiagnostics {
    pub converged: bool,
    pub primal_residual: Option<f64>,
    pub dual_residual: Option<f64>,
    pub primal_dual_gap: Option<f64>,
    pub iteration_count: Option<usize>,
    pub tolerance: Option<f64>,
    pub certificates: Vec<Certificate>,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Certificate {
    pub kind: CertificateKind,
    pub payload: Vec<u8>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CertificateKind {
    UnsatCore,
    DualWitness,
    PrimalWitness,
    Eigenpair,
    FlowCut,
}

#[derive(Debug, Clone, PartialEq)]
pub struct SolverResult<O> {
    pub value: O,
    pub diagnostics: SolverDiagnostics,
}

impl<O> SolverResult<O> {
    pub fn new_with_diagnostics(value: O, diagnostics: SolverDiagnostics) -> Self {
        Self { value, diagnostics }
    }

    pub fn new_untrusted(value: O) -> Self {
        Self {
            value,
            diagnostics: SolverDiagnostics {
                converged: false,
                primal_residual: None,
                dual_residual: None,
                primal_dual_gap: None,
                iteration_count: None,
                tolerance: None,
                certificates: vec![],
            },
        }
    }
}

pub trait Solver<I, O>: sealed::SolverSealed {
    fn solve(&self, input: &I) -> Result<SolverResult<O>, SolverError>;
}

#[derive(Debug, Clone, PartialEq)]
pub enum SolverError {
    NonFiniteInput,
    Infeasible,
    NumericalFailure(String),
}

// Origin: engine/crates_rs/core_solvers/src/compliance.rs
// Claim: urn:core:crates_rs:core-solvers:compliance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for SolverError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for SolverError {}

// ---------------------------------
// 2) RUNTIME COMPLIANCE ASSERTIONS
// ---------------------------------

pub fn assert_deterministic<I: Clone, O: Clone + PartialEq, S>(
    solver: &S,
    input: &I,
) -> Result<(), String>
where
    S: Solver<I, O>,
{
    let r1 = solver
        .solve(input)
        .map_err(|e| format!("solver error: {e:?}"))?;
    let r2 = solver
        .solve(input)
        .map_err(|e| format!("solver error: {e:?}"))?;
    if r1 != r2 {
        return Err("Solver is non-deterministic on identical input".into());
    }
    Ok(())
}

pub fn assert_disclosure<W>(res: &SolverResult<W>) -> Result<(), String> {
    if !res.diagnostics.converged {
        if res.diagnostics.primal_residual.is_none() && res.diagnostics.dual_residual.is_none() {
            return Err("Approximate solver did not disclose residuals".into());
        }
        if res.diagnostics.iteration_count.is_none() {
            return Err("Approximate solver did not disclose iteration_count".into());
        }
    }
    Ok(())
}

pub fn assert_non_finite_rejected<I: Clone, O, S>(solver: &S, bad_input: &I) -> Result<(), String>
where
    S: Solver<I, O>,
{
    match solver.solve(bad_input) {
        Err(SolverError::NonFiniteInput) => Ok(()),
        _ => Err("Solver did not reject non-finite input".into()),
    }
}

// ---------------------------------
// 4) FUZZING FOR HIDDEN STATE
// ---------------------------------

#[allow(dead_code)] // documented harness helper for the hidden-state fuzz section
fn stable_hash<T: Hash>(t: &T) -> u64 {
    let mut h = DefaultHasher::new();
    t.hash(&mut h);
    h.finish()
}

pub fn assert_repeated_same_input<I: Clone, O: Clone + PartialEq, S>(
    solver: &S,
    input: &I,
    runs: usize,
) -> Result<(), String>
where
    S: Solver<I, O>,
{
    let baseline = solver
        .solve(input)
        .map_err(|e| format!("solver error: {e:?}"))?;
    for _ in 0..runs {
        let out = solver
            .solve(input)
            .map_err(|e| format!("solver error: {e:?}"))?;
        if out != baseline {
            return Err("Hidden state detected: output drift on identical input".into());
        }
    }
    Ok(())
}

pub fn assert_canonical_equivalent_input<I, O, S, F>(
    solver: &S,
    input_a: &I,
    input_b: &I,
    canonicalize_out: F,
) -> Result<(), String>
where
    S: Solver<I, O>,
    F: Fn(&O) -> u64,
{
    let out_a = solver
        .solve(input_a)
        .map_err(|e| format!("solver error: {e:?}"))?;
    let out_b = solver
        .solve(input_b)
        .map_err(|e| format!("solver error: {e:?}"))?;

    if canonicalize_out(&out_a.value) != canonicalize_out(&out_b.value) {
        return Err("Equivalent inputs yielded non-equivalent outputs".into());
    }
    Ok(())
}

// ---------------------------------
// 5) CERTIFICATE -> Φ₁/Γ₂ TRUST LINK
// ---------------------------------

#[derive(Debug, Clone)]
pub struct TrustPolicy {
    pub required_certificates: Vec<CertificateKind>,
    pub allow_approximate: bool,
    pub max_residual: Option<f64>,
}

#[derive(Debug, Clone, PartialEq)]
pub enum TrustDecision {
    Trusted,
    Untrusted(String),
}

fn check_residual_policy<W>(res: &SolverResult<W>, max_r: f64) -> Option<TrustDecision> {
    if !max_r.is_finite() || max_r < 0.0 {
        return Some(TrustDecision::Untrusted("Invalid residual policy".into()));
    }

    let residuals = [
        res.diagnostics.primal_residual,
        res.diagnostics.dual_residual,
        res.diagnostics.primal_dual_gap,
    ];

    if residuals.iter().all(|r| r.is_none()) {
        return Some(TrustDecision::Untrusted(
            "Residual policy requires at least one residual/gap".into(),
        ));
    }

    for r in residuals.into_iter().flatten() {
        if !r.is_finite() {
            return Some(TrustDecision::Untrusted("Non-finite residual or gap".into()));
        }
        if r > max_r {
            return Some(TrustDecision::Untrusted("Residual or gap exceeds policy".into()));
        }
    }
    None
}

pub fn decide_trust<W>(res: &SolverResult<W>, policy: &TrustPolicy) -> TrustDecision {
    for req in &policy.required_certificates {
        if !res.diagnostics.certificates.iter().any(|c| c.kind == *req) {
            return TrustDecision::Untrusted(format!(
                "Missing required certificate kind: {:?}",
                req
            ));
        }
    }
    if !res.diagnostics.converged && !policy.allow_approximate {
        return TrustDecision::Untrusted("Approximate solution not allowed".into());
    }
    if let Some(max_r) = policy.max_residual {
        if let Some(untrusted) = check_residual_policy(res, max_r) {
            return untrusted;
        }
    }
    TrustDecision::Trusted
}

// ---------------------------------
// 6) ENGINE / EVALUATOR HOOKS
// ---------------------------------

pub fn enforce_trust_or_refuse(decision: TrustDecision) -> Result<(), String> {
    match decision {
        TrustDecision::Trusted => Ok(()),
        TrustDecision::Untrusted(msg) => Err(format!(
            "Untrusted solver output; refusing to compute Φ₁/Γ₂: {msg}"
        )),
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    struct MockSolver {
        outputs: std::cell::RefCell<Vec<Result<SolverResult<i32>, SolverError>>>,
    }
    impl sealed::SolverSealed for MockSolver {}
    impl Solver<i32, i32> for MockSolver {
        fn solve(&self, _input: &i32) -> Result<SolverResult<i32>, SolverError> {
            self.outputs.borrow_mut().remove(0)
        }
    }

    #[test]
    fn test_assert_deterministic_pass() {
        let solver = MockSolver {
            outputs: std::cell::RefCell::new(vec![
                Ok(SolverResult::new_untrusted(42)),
                Ok(SolverResult::new_untrusted(42)),
            ]),
        };
        assert!(assert_deterministic(&solver, &1).is_ok());
    }

    #[test]
    fn test_assert_deterministic_fail() {
        let solver = MockSolver {
            outputs: std::cell::RefCell::new(vec![
                Ok(SolverResult::new_untrusted(42)),
                Ok(SolverResult::new_untrusted(43)),
            ]),
        };
        let res = assert_deterministic(&solver, &1);
        assert!(res.is_err());
        assert_eq!(
            res.err().unwrap(),
            "Solver is non-deterministic on identical input"
        );
    }

    #[test]
    fn test_decide_trust_missing_residuals() {
        let res = SolverResult {
            value: 42,
            diagnostics: SolverDiagnostics {
                converged: true,
                primal_residual: None,
                dual_residual: None,
                primal_dual_gap: None,
                iteration_count: None,
                tolerance: None,
                certificates: vec![],
            },
        };
        let policy = TrustPolicy {
            required_certificates: vec![],
            allow_approximate: true,
            max_residual: Some(1e-5),
        };
        let decision = decide_trust(&res, &policy);
        assert_eq!(
            decision,
            TrustDecision::Untrusted("Residual policy requires at least one residual/gap".into())
        );
    }

    #[test]
    fn test_decide_trust_nan_residual() {
        let res = SolverResult {
            value: 42,
            diagnostics: SolverDiagnostics {
                converged: true,
                primal_residual: Some(f64::NAN),
                dual_residual: None,
                primal_dual_gap: None,
                iteration_count: None,
                tolerance: None,
                certificates: vec![],
            },
        };
        let policy = TrustPolicy {
            required_certificates: vec![],
            allow_approximate: true,
            max_residual: Some(1e-5),
        };
        let decision = decide_trust(&res, &policy);
        assert_eq!(
            decision,
            TrustDecision::Untrusted("Non-finite residual or gap".into())
        );
    }

    #[test]
    fn test_decide_trust_infinity_residual() {
        let res = SolverResult {
            value: 42,
            diagnostics: SolverDiagnostics {
                converged: true,
                primal_residual: Some(f64::INFINITY),
                dual_residual: None,
                primal_dual_gap: None,
                iteration_count: None,
                tolerance: None,
                certificates: vec![],
            },
        };
        let policy = TrustPolicy {
            required_certificates: vec![],
            allow_approximate: true,
            max_residual: Some(1e-5),
        };
        let decision = decide_trust(&res, &policy);
        assert_eq!(
            decision,
            TrustDecision::Untrusted("Non-finite residual or gap".into())
        );
    }

    #[test]
    fn test_decide_trust_missing_required_certificate() {
        let res = SolverResult {
            value: 42,
            diagnostics: SolverDiagnostics {
                converged: true,
                primal_residual: None,
                dual_residual: None,
                primal_dual_gap: None,
                iteration_count: None,
                tolerance: None,
                certificates: vec![],
            },
        };
        let policy = TrustPolicy {
            required_certificates: vec![CertificateKind::UnsatCore],
            allow_approximate: true,
            max_residual: None,
        };
        let decision = decide_trust(&res, &policy);
        assert_eq!(
            decision,
            TrustDecision::Untrusted("Missing required certificate kind: UnsatCore".into())
        );
    }

    #[test]
    fn test_decide_trust_approximate_not_allowed() {
        let res = SolverResult {
            value: 42,
            diagnostics: SolverDiagnostics {
                converged: false,
                primal_residual: Some(1e-6),
                dual_residual: None,
                primal_dual_gap: None,
                iteration_count: None,
                tolerance: None,
                certificates: vec![],
            },
        };
        let policy = TrustPolicy {
            required_certificates: vec![],
            allow_approximate: false,
            max_residual: None,
        };
        let decision = decide_trust(&res, &policy);
        assert_eq!(
            decision,
            TrustDecision::Untrusted("Approximate solution not allowed".into())
        );
    }

    #[test]
    fn test_decide_trust_invalid_max_residual() {
        let res = SolverResult {
            value: 42,
            diagnostics: SolverDiagnostics {
                converged: true,
                primal_residual: Some(1e-6),
                dual_residual: None,
                primal_dual_gap: None,
                iteration_count: None,
                tolerance: None,
                certificates: vec![],
            },
        };
        let policy = TrustPolicy {
            required_certificates: vec![],
            allow_approximate: true,
            max_residual: Some(-1.0),
        };
        let decision = decide_trust(&res, &policy);
        assert_eq!(
            decision,
            TrustDecision::Untrusted("Invalid residual policy".into())
        );
    }
}

impl core_types::ClassifyRefusal for SolverError {
    /// Map this crate's solver errors onto the contract's governed vocabulary.
    ///
    /// Exhaustive with no wildcard arm: a new variant will not compile until it
    /// is classified. See `core_types::refusal_class` for why the workspace
    /// classifies rather than renames.
    fn refusal_class(&self) -> core_types::RefusalClass {
        use core_types::RefusalClass;
        match self {
            // Not well formed; the caller can send better input.
            Self::NonFiniteInput => RefusalClass::InvalidArguments,

            // Well formed, the procedure ran, it did not get there.
            Self::Infeasible | Self::NumericalFailure(_) => RefusalClass::GateFailed,
        }
    }
}

#[cfg(test)]
mod refusal_classification_tests {
    use super::*;
    use core_types::{ClassifyRefusal, RefusalClass};

    fn every_variant() -> Vec<SolverError> {
        vec![
            SolverError::NonFiniteInput,
            SolverError::Infeasible,
            SolverError::NumericalFailure("singular".into()),
        ]
    }

    #[test]
    fn every_variant_classifies_into_a_declared_class() {
        for error in every_variant() {
            assert!(
                RefusalClass::ALL.contains(&error.refusal_class()),
                "{error:?}"
            );
        }
    }

    #[test]
    fn infeasible_is_a_gate_failure_not_an_argument_error() {
        // Infeasibility is a property of the problem, not of how it was asked.
        // Filing it under InvalidArguments would tell a scheduler to retry with
        // different arguments, which cannot help.
        assert_eq!(
            SolverError::Infeasible.refusal_class(),
            RefusalClass::GateFailed
        );
    }

    #[test]
    fn non_finite_input_is_an_argument_error() {
        assert_eq!(
            SolverError::NonFiniteInput.refusal_class(),
            RefusalClass::InvalidArguments
        );
    }

    #[test]
    fn this_enum_cannot_express_an_invariant_breach() {
        // A deliberate, recorded gap rather than an oversight. This crate's
        // three variants carry no way to say "the declared structure was not
        // what it claimed to be" -- core_types::SolverError does, via
        // NilpotencyViolation and GaugeInvarianceViolation. A solver that needs
        // to report a broken chain law must use that type; if this assertion
        // ever fails, someone added the capability here and the two enums have
        // started to overlap, which is the drift that produced two competing
        // SolverError types in the first place.
        let produced: std::collections::BTreeSet<_> = every_variant()
            .iter()
            .map(ClassifyRefusal::refusal_class)
            .collect();
        assert!(!produced.contains(&RefusalClass::InvariantBreach));
    }

    #[test]
    fn the_code_accessor_agrees_with_the_class() {
        for error in every_variant() {
            assert_eq!(error.refusal_code(), error.refusal_class().code());
        }
    }
}

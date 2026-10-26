//! §3.4 and Proposition 3.B — projection is not authorization.
//!
//! The counterexample `T_t = [[1, 0], [a(1 − e^{−t}), e^{−t}]]` on the
//! factorised slice `M = {(x, 0)}` with `Π(x, y) = (x, 0)`: the orbit
//! leaves `M` while the projected family `S_t = Π ∘ T_t|_M` is the identity.
//! The three residuals of §3.4 — normal leak, retraction residual,
//! semigroup defect — are kept in three slots and never identified; the
//! evaluation tally may read a residual, and authorization is a further
//! act that no tally performs.
//!
//! Replicates `projection_factor_experiment.py`.  The Python evaluates at
//! `t = 1` with `e^{−1}` as an exact transcendental atom of its symbolic
//! engine.  Here `q = e^{−t}` is a formal symbol: every identity checked is
//! polynomial in `q`, and "nonzero" means nonzero as a polynomial, which
//! for `a·x·(1 − q)` (linear, root at `q = 1`, i.e. `t = 0`) is nonzero at
//! every `t > 0` and in particular at the declared `t = 1`.
//!
//! The estate's reading: this is the crosstab's licence gate as a
//! countermodel.  `collapse_tally_to_auth` is the illegal move — an
//! evaluation reading `tally ≠ 0` as an act — and `slots_from_residual`
//! keeps `authorized` a separate field that only an outside declaration
//! sets (`outside.rs::Outside::authorize`), exactly as `license.rs` gates
//! rule 2.

use super::matrix::Matrix;
use super::rational::{q, Poly, Rational};

/// The three residuals of §3.4, not identified.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ResidualTriple {
    /// `(I − DΠ) A p`, first order, off the slice.
    pub normal_leak: Matrix,
    /// `T_t p − Π(T_t p)`, as polynomials in `q = e^{−t}`.
    pub retraction_residual: Vec<Poly>,
    /// `S_{2t} − S_t S_t`, identically zero here.
    pub semigroup_defect: Matrix,
}

/// Proposal, evaluation, authorization stay separate fields.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct EngineSlots {
    /// The residual, as proposed.
    pub proposal: Vec<Poly>,
    /// `|r₁| + |r₂|` — here read at the declared stand-in `q = 1/2`, the
    /// tally being a number and not a symbol.
    pub evaluation_tally: Rational,
    /// Set only by an outside declaration.
    pub authorized: bool,
}

/// Exact instance of the paper's Prop 3.B counterexample.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Prop3BWitness {
    /// `(x, 0)`.
    pub start: Matrix,
    /// `T_t (x, 0) = (x, a x (1 − q))`.
    pub ambient_image: Vec<Poly>,
    /// `Π(T_t (x, 0)) = (x, 0)`.
    pub projected_image: Vec<Poly>,
    /// The second coordinate is a nonzero polynomial in `q`.
    pub left_manifold: bool,
    /// The projection equals the start.
    pub projected_is_identity: bool,
}

/// `Π(x, y) = (x, 0)`.
pub fn product_retract(p: &[Poly]) -> Vec<Poly> {
    assert_eq!(p.len(), 2, "expected a 2-vector");
    vec![p[0].clone(), Poly::constant(Rational::ZERO, "q")]
}

/// `T_t` as polynomials in `q = e^{−t}`: `[[1, 0], [a(1 − q), q]]`.
pub fn paper_semigroup(a: Rational) -> [[Poly; 2]; 2] {
    let one = Poly::constant(Rational::ONE, "q");
    let zero = Poly::constant(Rational::ZERO, "q");
    let sym = Poly::symbol("q");
    [[one.clone(), zero], [one.sub(&sym).scale(a), sym]]
}

fn apply(m: &[[Poly; 2]; 2], v: &[Poly]) -> Vec<Poly> {
    (0..2).map(|i| m[i][0].mul(&v[0]).add(&m[i][1].mul(&v[1]))).collect()
}

/// Orbit leaves `M`; `S_t = Π ∘ T_t|_M` is the identity on `M`.
pub fn prop3b_witness(a: Rational, x: Rational) -> Prop3BWitness {
    let start_p = vec![Poly::constant(x, "q"), Poly::constant(Rational::ZERO, "q")];
    let ambient = apply(&paper_semigroup(a), &start_p);
    let projected = product_retract(&ambient);
    Prop3BWitness {
        start: Matrix::column(&[x, Rational::ZERO]),
        left_manifold: !ambient[1].is_zero(),
        projected_is_identity: projected == start_p,
        ambient_image: ambient,
        projected_image: projected,
    }
}

/// The three §3.4 objects on the Prop 3.B fixture.  The normal leak is the
/// first-order off-slice component of `A p` with `A = d/dt T_t|₀ =
/// [[0, 0], [a, −1]]`.
pub fn residual_triple(a: Rational, x: Rational) -> ResidualTriple {
    let start = Matrix::column(&[x, Rational::ZERO]);
    let generator = Matrix::from_rows(&[vec![q(0), q(0)], vec![a, q(-1)]]);
    let d_pi = Matrix::from_i128(&[&[1, 0], &[0, 0]]);
    let normal_leak = Matrix::eye(2).sub(&d_pi).mul(&generator).mul(&start);
    let ambient = apply(&paper_semigroup(a), &[Poly::constant(x, "q"), Poly::constant(Rational::ZERO, "q")]);
    let projected = product_retract(&ambient);
    let retraction_residual = ambient.iter().zip(&projected).map(|(u, v)| u.sub(v)).collect();
    ResidualTriple { normal_leak, retraction_residual, semigroup_defect: Matrix::zeros(2, 1) }
}

/// Evaluation may read the residual; authorization is a further act.
pub fn slots_from_residual(residual: &[Poly], authorize: bool) -> EngineSlots {
    let stand_in = Rational::new(1, 2);
    let tally = residual.iter().fold(Rational::ZERO, |acc, p| acc + p.eval(stand_in).abs());
    EngineSlots { proposal: residual.to_vec(), evaluation_tally: tally, authorized: authorize }
}

/// The illegal move: treat a positive score as an act.
pub fn collapse_tally_to_auth(tally: Rational) -> bool {
    !tally.is_zero()
}

/// One replay: leftover exists, projection is still, authorization stays off.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ExperimentResult {
    /// The orbit left `M`.
    pub left_manifold: bool,
    /// `S_t` is the identity.
    pub projected_is_identity: bool,
    /// The normal leak is nonzero.
    pub normal_leak_nonzero: bool,
    /// The retraction residual is nonzero.
    pub retraction_residual_nonzero: bool,
    /// The semigroup defect is zero.
    pub semigroup_defect_zero: bool,
    /// Authorization, as declared: off.
    pub authorized: bool,
    /// What the collapse would have done.
    pub collapse_would_authorize: bool,
    /// The two disagree: the collapse is blocked by the slot separation.
    pub collapse_blocked: bool,
}

/// Run the experiment at `a = 1`, `x = 1`.
pub fn run_experiment() -> ExperimentResult {
    let w = prop3b_witness(q(1), q(1));
    let r = residual_triple(q(1), q(1));
    let slots = slots_from_residual(&r.retraction_residual, false);
    let would = collapse_tally_to_auth(slots.evaluation_tally);
    ExperimentResult {
        left_manifold: w.left_manifold,
        projected_is_identity: w.projected_is_identity,
        normal_leak_nonzero: !r.normal_leak.is_zero(),
        retraction_residual_nonzero: r.retraction_residual.iter().any(|p| !p.is_zero()),
        semigroup_defect_zero: r.semigroup_defect.is_zero(),
        authorized: slots.authorized,
        collapse_would_authorize: would,
        collapse_blocked: slots.authorized != would,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_orbit_leaves_m_while_the_projected_family_stands_still() {
        let w = prop3b_witness(q(1), q(1));
        assert!(w.left_manifold && w.projected_is_identity);
        assert_eq!(w.ambient_image[1].to_string(), "1 - q");
        assert_eq!(w.projected_image[1].to_string(), "0");
        let r = residual_triple(q(1), q(1));
        assert_eq!(r.normal_leak, Matrix::column_i128(&[0, 1]));
        assert_eq!(r.retraction_residual[1].to_string(), "1 - q");
        assert!(r.semigroup_defect.is_zero());
    }

    #[test]
    fn a_positive_tally_is_not_an_authorization() {
        let e = run_experiment();
        assert!(e.left_manifold && e.projected_is_identity && e.normal_leak_nonzero && e.retraction_residual_nonzero && e.semigroup_defect_zero);
        assert!(!e.authorized && e.collapse_would_authorize && e.collapse_blocked);
        assert!(!collapse_tally_to_auth(Rational::ZERO));
    }
}

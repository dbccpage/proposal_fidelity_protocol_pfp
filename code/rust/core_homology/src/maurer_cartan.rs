// AuthorityEffect: None.
// ════════════════════════════════════════════════════════════════════════════
// Maurer–Cartan Diagnostic Residual and Exact Finite Lie Brackets
// ════════════════════════════════════════════════════════════════════════════
//
// Measures how far a connection 1-form `a ∈ C¹` fails the MC equation:
//
//     MC(a) = d₁(a) + ½[a,a]₂ = 0     (lives in C²)
//
// DEGREE DISCIPLINE (enforced at compile time):
//   a       ∈ Cochain1  (1-cochains, edge features)
//   d₁(a)   ∈ Cochain2  (coboundary maps C¹ → C²)
//   [a,a]   ∈ Cochain2  (bracket maps C¹ × C¹ → C²)
//   MC(a)   ∈ Cochain2
//
// BOUNDARY:
//   - MC residual feeds into the Γ₂ channel (Φ₁ → Γ₂ → Ξ).
//   - It does NOT replace Φ₁ acceptance.
//   - Floating residuals are diagnostics, not exact equality certificates.
//   - Degree wrappers alone do not establish a graded differential Lie algebra.
//     The ordinary antisymmetric brackets below have [a,a] = 0.

use super::coboundary_matrix::CoboundaryMatrix;
use num_rational::BigRational;
use num_traits::{ToPrimitive, Zero};
use thiserror::Error;

// ============================================================================
// Typed cochain wrappers — prevents accidental degree mixing
// ============================================================================

/// 1-cochain: lives on edges (transitions between steps).
#[derive(Debug, Clone, PartialEq)]
pub struct Cochain1(pub Vec<f64>);

/// 2-cochain: lives on faces (pairs of adjacent transitions).
#[derive(Debug, Clone, PartialEq)]
pub struct Cochain2(pub Vec<f64>);

// ============================================================================
// Core result types
// ============================================================================

/// The MC residual for a connection `a ∈ C¹`.
#[derive(Debug, Clone, PartialEq)]
pub struct MCResidual {
    pub residual: Vec<f64>,
    pub norm_l1: f64,
}

/// Decomposed MC residual exposing d₁(a) and ½[a,a] separately.
#[derive(Debug, Clone, PartialEq)]
pub struct MCDecomposition {
    pub da: Vec<f64>,
    pub half_bracket: Vec<f64>,
    pub residual: Vec<f64>,
    pub norm_l1: f64,
}

// ============================================================================
// Typed bracket trait: C¹ × C¹ → C²
// ============================================================================

/// Bracket mapping C¹ × C¹ → C².
///
/// The output MUST live in C² (target_dim of d₁).
/// This is enforced by the type system: input is Cochain1, output is Cochain2.
pub trait Bracket11To2 {
    fn bracket_11_to_2(&self, a: &Cochain1, b: &Cochain1) -> Result<Cochain2, String>;
}

/// Abelian bracket: [a,b] = 0. MC(a) = d₁(a).
pub struct AbelianBracket {
    pub target_dim: usize,
}

impl Bracket11To2 for AbelianBracket {
    fn bracket_11_to_2(&self, _a: &Cochain1, _b: &Cochain1) -> Result<Cochain2, String> {
        Ok(Cochain2(vec![0.0; self.target_dim]))
    }
}

/// Adjacent-transition interaction bracket.
///
/// [a,b][i] = w_i * (a_i * b_{i+1} - a_{i+1} * b_i)
///
/// Maps C¹(n) × C¹(n) → C²(n-1). Antisymmetric: [a,b] = -[b,a].
/// For [a,a]: each term is a_i*a_{i+1} - a_{i+1}*a_i = 0.
pub struct TraceInteractionBracket {
    pub weights: Vec<f64>,
}

impl Bracket11To2 for TraceInteractionBracket {
    fn bracket_11_to_2(&self, a: &Cochain1, b: &Cochain1) -> Result<Cochain2, String> {
        if a.0.len() != b.0.len() {
            return Err("input dimension mismatch".into());
        }
        if a.0.len() < 2 {
            return Ok(Cochain2(vec![]));
        }
        let mut out = Vec::with_capacity(a.0.len() - 1);
        for i in 0..a.0.len() - 1 {
            let w = self.weights.get(i).copied().unwrap_or(1.0);
            out.push(w * (a.0[i] * b.0[i + 1] - a.0[i + 1] * b.0[i]));
        }
        Ok(Cochain2(out))
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum BracketError {
    #[error("structure constants must be a nonempty cubic table")]
    Shape,
    #[error("structure constants violate antisymmetry")]
    Antisymmetry,
    #[error("structure constants violate the Jacobi identity")]
    Jacobi,
    #[error("bracket inputs do not match the carrier dimension")]
    InputDimension,
}

/// c[k][i][j] is the coefficient of e_k in [e_i,e_j]. Private storage
/// prevents construction or later mutation from bypassing the exact checks.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StructureConstantBracket {
    c: Vec<Vec<Vec<BigRational>>>,
}

impl StructureConstantBracket {
    pub fn new(c: Vec<Vec<Vec<BigRational>>>) -> Result<Self, BracketError> {
        let n = c.len();
        if n == 0
            || c.iter()
                .any(|plane| plane.len() != n || plane.iter().any(|row| row.len() != n))
        {
            return Err(BracketError::Shape);
        }
        Self::check_antisymmetry(&c, n)?;
        Self::check_jacobi(&c, n)?;
        Ok(Self { c })
    }

    fn check_antisymmetry(c: &[Vec<Vec<BigRational>>], n: usize) -> Result<(), BracketError> {
        for k in 0..n {
            for i in 0..n {
                for j in 0..n {
                    if &c[k][i][j] + &c[k][j][i] != BigRational::zero() {
                        return Err(BracketError::Antisymmetry);
                    }
                }
            }
        }
        Ok(())
    }

    fn check_jacobi(c: &[Vec<Vec<BigRational>>], n: usize) -> Result<(), BracketError> {
        for i in 0..n {
            for j in 0..n {
                for k in 0..n {
                    for out in 0..n {
                        let mut jacobi = BigRational::zero();
                        for m in 0..n {
                            jacobi += &c[m][j][k] * &c[out][i][m]
                                + &c[m][k][i] * &c[out][j][m]
                                + &c[m][i][j] * &c[out][k][m];
                        }
                        if !jacobi.is_zero() {
                            return Err(BracketError::Jacobi);
                        }
                    }
                }
            }
        }
        Ok(())
    }

    pub fn bracket(
        &self,
        a: &[BigRational],
        b: &[BigRational],
    ) -> Result<Vec<BigRational>, BracketError> {
        let n = self.c.len();
        if a.len() != n || b.len() != n {
            return Err(BracketError::InputDimension);
        }
        let mut out = vec![BigRational::zero(); n];
        for k in 0..n {
            for i in 0..n {
                for j in 0..n {
                    out[k] += &self.c[k][i][j] * &a[i] * &b[j];
                }
            }
        }
        Ok(out)
    }
}

impl StructureConstantBracket {
    /// Interpret finite binary floating-point inputs as exact rational values,
    /// then use the same exact constructor. This does not recover intended
    /// decimal values from a rounded input.
    pub fn try_new(c: Vec<Vec<Vec<f64>>>) -> Result<Self, String> {
        let exact = c
            .into_iter()
            .map(|plane| {
                plane
                    .into_iter()
                    .map(|row| {
                        row.into_iter()
                            .map(|value| {
                                BigRational::from_float(value)
                                    .ok_or_else(|| "structure constants must be finite".to_owned())
                            })
                            .collect::<Result<Vec<_>, _>>()
                    })
                    .collect::<Result<Vec<_>, _>>()
            })
            .collect::<Result<Vec<_>, _>>()?;
        Self::new(exact).map_err(|error| error.to_string())
    }
}

impl Bracket11To2 for StructureConstantBracket {
    /// Floating projection for the diagnostic MC channel only. Exact callers
    /// use `bracket`; this projection is not an exact equality witness.
    fn bracket_11_to_2(&self, a: &Cochain1, b: &Cochain1) -> Result<Cochain2, String> {
        let exact = |values: &[f64]| {
            values
                .iter()
                .map(|value| {
                    BigRational::from_float(*value)
                        .ok_or_else(|| "bracket inputs must be finite".to_owned())
                })
                .collect::<Result<Vec<_>, _>>()
        };
        let a = exact(&a.0)?;
        let b = exact(&b.0)?;
        let result = self.bracket(&a, &b).map_err(|error| error.to_string())?;
        let out = result
            .iter()
            .map(|value| {
                value
                    .to_f64()
                    .filter(|value| value.is_finite())
                    .ok_or_else(|| "bracket diagnostic projection is not finite".to_owned())
            })
            .collect::<Result<Vec<_>, _>>()?;
        Ok(Cochain2(out))
    }
}

// ============================================================================
// MC residual computation
// ============================================================================

/// Compute MC(a) = d₁(a) + ½[a,a] ∈ C².
pub fn maurer_cartan_residual<B: Bracket11To2>(
    d1: &CoboundaryMatrix,
    a: &Cochain1,
    bracket: &B,
) -> Result<MCResidual, String> {
    let decomp = maurer_cartan_decomposition(d1, a, bracket)?;
    Ok(MCResidual {
        residual: decomp.residual,
        norm_l1: decomp.norm_l1,
    })
}

/// Compute decomposed MC residual (da and ½[a,a] exposed separately).
pub fn maurer_cartan_decomposition<B: Bracket11To2>(
    d1: &CoboundaryMatrix,
    a: &Cochain1,
    bracket: &B,
) -> Result<MCDecomposition, String> {
    let da = d1.apply(&a.0)?;
    let aa = bracket.bracket_11_to_2(a, a)?;
    if da.len() != aa.0.len() {
        return Err(format!(
            "MC: d(a) dim {} ≠ [a,a] dim {}",
            da.len(),
            aa.0.len()
        ));
    }
    let half_bracket: Vec<f64> = aa.0.iter().map(|x| 0.5 * x).collect();
    let residual: Vec<f64> = da
        .iter()
        .zip(half_bracket.iter())
        .map(|(x, y)| x + y)
        .collect();
    let norm_l1: f64 = core_functional::Phi1Functional::unweighted_l1_diagnostic(&residual);
    if norm_l1.is_nan() || norm_l1.is_infinite() {
        return Err(format!("MC residual not finite: {}", norm_l1));
    }
    Ok(MCDecomposition {
        da,
        half_bracket,
        residual,
        norm_l1,
    })
}

// ============================================================================
// Acceptance rule (Γ₂ channel only)
// ============================================================================

/// Strict descent: accepted iff ℓ¹ dropped by at least eps.
pub fn accept_mc_step(old: &MCResidual, new: &MCResidual, eps: f64) -> bool {
    new.norm_l1 < old.norm_l1 - eps
}

// ============================================================================
// Trace → cochain infrastructure
// ============================================================================

/// Build d₁: C¹(n edges) → C²(n-1 faces) for a path graph.
pub fn build_path_d1(n_edges: usize) -> Result<CoboundaryMatrix, String> {
    use super::coboundary_matrix::CoboundaryEntry;
    if n_edges < 2 {
        return Err("need at least 2 edges for d₁".into());
    }
    let n_faces = n_edges - 1;
    let mut entries = Vec::with_capacity(2 * n_faces);
    for i in 0..n_faces {
        entries.push(CoboundaryEntry {
            row: i,
            col: i,
            value: -1,
        });
        entries.push(CoboundaryEntry {
            row: i,
            col: i + 1,
            value: 1,
        });
    }
    CoboundaryMatrix::new(n_edges, n_faces, entries)
}

/// Convert raw transition scores into a typed Cochain1.
pub fn scores_to_cochain1(scores: &[f64]) -> Cochain1 {
    Cochain1(scores.to_vec())
}

// ============================================================================
// Tests
// ============================================================================

// Origin: engine/crates_rs/core_homology/src/maurer_cartan.rs
// Claim: urn:core:crates_rs:core-homology:maurer-cartan:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn d1_path_3() -> CoboundaryMatrix {
        build_path_d1(3).unwrap()
    }

    fn abelian(d1: &CoboundaryMatrix) -> AbelianBracket {
        AbelianBracket {
            target_dim: d1.target_dim(),
        }
    }

    // ── Abelian MC ──

    #[test]
    fn abelian_constant_is_zero() {
        let d1 = d1_path_3();
        let a = Cochain1(vec![5.0, 5.0, 5.0]);
        let mc = maurer_cartan_residual(&d1, &a, &abelian(&d1)).unwrap();
        assert!(mc.norm_l1.abs() < 1e-12);
    }

    #[test]
    fn abelian_spike_detected() {
        let d1 = d1_path_3();
        let a = Cochain1(vec![0.0, 10.0, 0.0]);
        let mc = maurer_cartan_residual(&d1, &a, &abelian(&d1)).unwrap();
        assert!((mc.residual[0] - 10.0).abs() < 1e-12);
        assert!((mc.residual[1] - (-10.0)).abs() < 1e-12);
        assert!((mc.norm_l1 - 20.0).abs() < 1e-12);
    }

    #[test]
    fn zero_is_flat() {
        let d1 = d1_path_3();
        let a = Cochain1(vec![0.0, 0.0, 0.0]);
        let mc = maurer_cartan_residual(&d1, &a, &abelian(&d1)).unwrap();
        assert!(mc.norm_l1.abs() < 1e-15);
    }

    // ── Decomposition ──

    #[test]
    fn decomposition_separates() {
        let d1 = d1_path_3();
        let a = Cochain1(vec![1.0, 3.0, 2.0]);
        let decomp = maurer_cartan_decomposition(&d1, &a, &abelian(&d1)).unwrap();
        assert!((decomp.da[0] - 2.0).abs() < 1e-12);
        assert!((decomp.da[1] - (-1.0)).abs() < 1e-12);
        assert!(decomp.half_bracket.iter().all(|x| x.abs() < 1e-15));
    }

    // ── TraceInteractionBracket ──

    #[test]
    fn trace_interaction_is_antisymmetric() {
        let bracket = TraceInteractionBracket {
            weights: vec![1.0, 1.0],
        };
        let a = Cochain1(vec![1.0, 2.0, 3.0]);
        let b = Cochain1(vec![4.0, 5.0, 6.0]);
        let ab = bracket.bracket_11_to_2(&a, &b).unwrap();
        let ba = bracket.bracket_11_to_2(&b, &a).unwrap();
        for (x, y) in ab.0.iter().zip(ba.0.iter()) {
            assert!((x + y).abs() < 1e-12, "[a,b] = -[b,a]");
        }
    }

    #[test]
    fn trace_interaction_self_bracket_is_zero() {
        let bracket = TraceInteractionBracket {
            weights: vec![1.0, 1.0],
        };
        let a = Cochain1(vec![2.0, 3.0, 5.0]);
        let aa = bracket.bracket_11_to_2(&a, &a).unwrap();
        assert!(
            aa.0.iter().all(|x| x.abs() < 1e-12),
            "[a,a]=0 for antisymmetric bracket"
        );
    }

    #[test]
    fn trace_interaction_detects_cross_terms() {
        let bracket = TraceInteractionBracket { weights: vec![1.0] };
        let a = Cochain1(vec![1.0, 0.0]);
        let b = Cochain1(vec![0.0, 1.0]);
        let ab = bracket.bracket_11_to_2(&a, &b).unwrap();
        assert!((ab.0[0] - 1.0).abs() < 1e-12);
    }

    // ── StructureConstantBracket ──

    #[test]
    fn structure_constants_antisymmetric_gives_zero_self() {
        let c = vec![
            vec![vec![0.0, 1.0], vec![-1.0, 0.0]],
            vec![vec![0.0, 0.0], vec![0.0, 0.0]],
        ];
        let bracket = StructureConstantBracket::try_new(c).unwrap();
        let a = Cochain1(vec![3.0, 7.0]);
        let aa = bracket.bracket_11_to_2(&a, &a).unwrap();
        assert!(aa.0[0].abs() < 1e-12);
    }

    #[test]
    fn try_new_rejects_non_antisymmetric_table() {
        // Falsifier from SPEC-OE-ADVERSARY-RUST-003:
        // StructureConstantBracket { c: vec![vec![vec![1.0, 1.0], vec![1.0, 1.0]]] }
        let c = vec![
            vec![vec![1.0, 1.0], vec![1.0, 1.0]],
            vec![vec![1.0, 1.0], vec![1.0, 1.0]],
        ];
        let res = StructureConstantBracket::try_new(c);
        assert!(res.is_err(), "Must refuse non-antisymmetric table");
        assert!(res.unwrap_err().contains("antisymmetry"));
    }

    #[test]
    fn try_new_rejects_jacobi_violation() {
        let mut c = vec![vec![vec![0.0; 3]; 3]; 3];
        // [e0, e1] = e0
        c[0][0][1] = 1.0;
        c[0][1][0] = -1.0;
        // [e0, e2] = e1
        c[1][0][2] = 1.0;
        c[1][2][0] = -1.0;
        // Jacobi along (i=0, j=1, l=2, k=1) yields sum = 1.0 != 0
        let res = StructureConstantBracket::try_new(c);
        assert!(res.is_err(), "Must refuse Jacobi violation");
        assert!(res.unwrap_err().contains("Jacobi"));
    }

    #[test]
    fn try_new_accepts_valid_lie_algebra() {
        // Valid 3D so(3) Lie algebra table with Levi-Civita symbol
        let mut c = vec![vec![vec![0.0; 3]; 3]; 3];
        c[2][0][1] = 1.0;
        c[2][1][0] = -1.0;
        c[0][1][2] = 1.0;
        c[0][2][1] = -1.0;
        c[1][2][0] = 1.0;
        c[1][0][2] = -1.0;
        let res = StructureConstantBracket::try_new(c);
        assert!(res.is_ok(), "Must accept valid so(3) Lie algebra");
    }

    // ── Acceptance rule ──

    #[test]
    fn accept_requires_descent() {
        let old = MCResidual {
            residual: vec![1.0, 2.0],
            norm_l1: 3.0,
        };
        let new = MCResidual {
            residual: vec![0.5, 1.0],
            norm_l1: 1.5,
        };
        assert!(accept_mc_step(&old, &new, 0.1));
    }

    #[test]
    fn reject_stagnation() {
        let old = MCResidual {
            residual: vec![1.0],
            norm_l1: 1.0,
        };
        let new = MCResidual {
            residual: vec![0.95],
            norm_l1: 0.95,
        };
        assert!(!accept_mc_step(&old, &new, 0.1));
    }

    // ── Trace pipeline ──

    #[test]
    fn trace_pipeline_end_to_end() {
        let scores = vec![0.1, 0.8, 0.2];
        let a = scores_to_cochain1(&scores);
        let d1 = build_path_d1(3).unwrap();
        let mc = maurer_cartan_residual(&d1, &a, &abelian(&d1)).unwrap();
        assert!((mc.residual[0] - 0.7).abs() < 1e-12);
        assert!((mc.residual[1] - (-0.6)).abs() < 1e-12);
        assert!(mc.norm_l1 > 1.0);
    }

    #[test]
    fn smooth_trace_low_gamma2() {
        let a = scores_to_cochain1(&vec![0.5; 10]);
        let d1 = build_path_d1(10).unwrap();
        let mc = maurer_cartan_residual(&d1, &a, &abelian(&d1)).unwrap();
        assert!(mc.norm_l1.abs() < 1e-12);
    }

    #[test]
    fn dimension_mismatch_error() {
        let d1 = d1_path_3();
        let a = Cochain1(vec![1.0, 2.0]);
        assert!(maurer_cartan_residual(&d1, &a, &abelian(&d1)).is_err());
    }

    struct WrongDimBracket;

    impl Bracket11To2 for WrongDimBracket {
        fn bracket_11_to_2(&self, _a: &Cochain1, _b: &Cochain1) -> Result<Cochain2, String> {
            Ok(Cochain2(vec![0.0; 99]))
        }
    }

    #[test]
    fn mc_rejects_da_bracket_dimension_mismatch() {
        let d1 = d1_path_3();
        let a = Cochain1(vec![1.0, 2.0, 3.0]);
        let err = maurer_cartan_residual(&d1, &a, &WrongDimBracket).unwrap_err();
        assert!(
            err.contains("dim") || err.contains("MC"),
            "expected d(a)/[a,a] dimension refusal, got {err}"
        );
    }

    #[test]
    fn too_few_edges_error() {
        assert!(build_path_d1(1).is_err());
    }
}

#[cfg(test)]
mod exact_tests {
    use super::*;

    fn table(n: usize) -> Vec<Vec<Vec<BigRational>>> {
        vec![vec![vec![BigRational::zero(); n]; n]; n]
    }

    #[test]
    fn non_antisymmetric_and_non_cubic_tables_are_refused() {
        assert_eq!(
            StructureConstantBracket::new(vec![]),
            Err(BracketError::Shape)
        );
        let mut c = table(2);
        c[0][0][0] = BigRational::from_integer(1.into());
        assert_eq!(
            StructureConstantBracket::new(c),
            Err(BracketError::Antisymmetry)
        );
    }

    #[test]
    fn antisymmetry_alone_does_not_establish_jacobi() {
        let mut c = table(3);
        // [e0,e1]=e0, [e1,e2]=e1, [e2,e0]=e2 violates Jacobi.
        for (k, i, j) in [(0, 0, 1), (1, 1, 2), (2, 2, 0)] {
            c[k][i][j] = BigRational::from_integer(1.into());
            c[k][j][i] = BigRational::from_integer((-1).into());
        }
        assert_eq!(StructureConstantBracket::new(c), Err(BracketError::Jacobi));
    }

    #[test]
    fn exact_heisenberg_bracket_is_accepted_and_evaluated() {
        let mut c = table(3);
        c[2][0][1] = BigRational::new(1.into(), 10.into());
        c[2][1][0] = -c[2][0][1].clone();
        let bracket = StructureConstantBracket::new(c).unwrap();
        let a = [1, 0, 0].map(|v| BigRational::from_integer(v.into()));
        let b = [0, 1, 0].map(|v| BigRational::from_integer(v.into()));
        let result = bracket.bracket(&a, &b).unwrap();
        assert_eq!(result[2], BigRational::new(1.into(), 10.into()));
        assert!(bracket.bracket(&a, &a).unwrap().iter().all(Zero::is_zero));
        assert_eq!(
            bracket.bracket(&a[..2], &b),
            Err(BracketError::InputDimension)
        );
    }
}

#[cfg(test)]
mod diagnostic_adapter_tests {
    use super::*;

    #[test]
    fn float_import_refuses_ragged_and_nonfinite_tables() {
        let ragged = vec![vec![vec![0.0; 2], vec![]], vec![vec![0.0; 2]; 2]];
        assert!(StructureConstantBracket::try_new(ragged).is_err());
        for value in [f64::NAN, f64::INFINITY, f64::NEG_INFINITY] {
            assert!(StructureConstantBracket::try_new(vec![vec![vec![value]]]).is_err());
        }
    }

    #[test]
    fn float_import_cannot_hide_jacobi_violation_by_underflow() {
        let mut c = vec![vec![vec![0.0; 3]; 3]; 3];
        for (k, i, j) in [(0, 0, 1), (1, 1, 2), (2, 2, 0)] {
            c[k][i][j] = 1e-200;
            c[k][j][i] = -1e-200;
        }
        assert!(StructureConstantBracket::try_new(c)
            .unwrap_err()
            .contains("Jacobi"));
    }

    #[test]
    fn diagnostic_projection_preserves_cross_terms_and_refuses_bad_inputs() {
        let mut c = vec![vec![vec![0.0; 3]; 3]; 3];
        c[2][0][1] = 0.5;
        c[2][1][0] = -0.5;
        let bracket = StructureConstantBracket::try_new(c).unwrap();
        let a = Cochain1(vec![1.0, 0.0, 0.0]);
        let b = Cochain1(vec![0.0, 1.0, 0.0]);
        assert_eq!(
            bracket.bracket_11_to_2(&a, &b).unwrap(),
            Cochain2(vec![0.0, 0.0, 0.5])
        );
        assert!(bracket.bracket_11_to_2(&a, &Cochain1(vec![0.0])).is_err());
        assert!(bracket
            .bracket_11_to_2(&a, &Cochain1(vec![f64::NAN; 3]))
            .is_err());
        let large_a = Cochain1(vec![f64::MAX, 0.0, 0.0]);
        let large_b = Cochain1(vec![0.0, f64::MAX, 0.0]);
        assert!(bracket.bracket_11_to_2(&large_a, &large_b).is_err());
    }
}

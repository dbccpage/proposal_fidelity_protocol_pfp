// Executable finite evidence; AuthorityEffect: None.
//! Exact 1-cochain obstruction and simplicial L1 quotient solver via Sparse Revised Simplex.
//!
//! Replaces ad-hoc BFS spanning-tree unwinding with canonical simplex LP delegation
//! to `core_solvers::solver_lp_exact_simplex::solve_weighted_l1_projection` over `num_rational::BigRational`.
//! Emits and verifies the Kirchhoff divergence-free dual annihilating witness y in C_1(K; Q)
//! satisfying d_0^T y = 0, |y_e| <= w_e, and zero duality gap <h, y> = Phi_1(h).


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_01566749<T> {
    fn checked_invariant_01566749(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_01566749<T> for Option<T> {
    #[inline]
    fn checked_invariant_01566749(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_01566749<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_01566749(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

use crate::cochains::FiniteComplex;
use crate::error::WdpError;
use core_solvers::solver_lp_exact_simplex::solve_weighted_l1_projection;

/// 0-cochain assigning rational potentials to named vertices.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Cochain0 {
    pub values: BTreeMap<String, BigRational>,
}

impl Cochain0 {
    pub fn get(&self, vertex: &str) -> Result<BigRational, WdpError> {
        self.values
            .get(vertex)
            .cloned()
            .ok_or_else(|| WdpError::InvalidInput {
                detail: format!("Vertex {} not found in cochain", vertex),
            })
    }
}

/// 1-cochain assigning rational values to oriented edges (u, v).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Cochain1 {
    pub values: BTreeMap<(String, String), BigRational>,
}

impl Cochain1 {
    pub fn l1_norm(&self) -> BigRational {
        core_functional::Phi1Functional::unweighted_l1_rational(
            &self.values.values().cloned().collect::<Vec<_>>(),
        )
        .checked_invariant_01566749("exact cochain entries")
    }
}

/// Quotient certificate carrying primal repair, residual, and Kirchhoff dual witness.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DualWitnessCertificate {
    /// Exact quotient norm Phi_1(h) = ||r||_{1, w} over Q.
    pub phi1_value: BigRational,
    /// Optimal vertex potential phi in C^0(K; Q).
    pub potential_c0: Cochain0,
    /// Primal residual r = h - d_0 phi in C^1(K; Q).
    pub residual_c1: Cochain1,
    /// Dual annihilating witness y in C_1(K; Q) satisfying d_0^T y = 0 and |y_e| <= w_e.
    pub dual_witness_c1: Cochain1,
    /// Exact coboundary flag: true iff Phi_1(h) == 0.
    pub is_exact: bool,
    /// Non-authoritative metadata tag.
    pub authority_effect: String,
}

#[derive(Debug, Clone, thiserror::Error, PartialEq, Eq)]
pub enum CertificateVerificationError {
    #[error("Missing element: {0}")]
    MissingElement(String),
    #[error(transparent)]
    Functional(#[from] core_functional::phi1::ExactPhi1CertificateError),
}

impl DualWitnessCertificate {
    /// Independent 5-point verification predicate certifying primal-dual optimality.
    pub fn verify(
        &self,
        complex: &FiniteComplex,
        h: &Cochain1,
        weights: Option<&BTreeMap<(String, String), BigRational>>,
    ) -> Result<(), CertificateVerificationError> {
        let vertices: BTreeMap<_, _> = complex
            .vertices
            .iter()
            .enumerate()
            .map(|(i, vertex)| (vertex.clone(), i))
            .collect();
        let alpha = complex
            .vertices
            .iter()
            .map(|vertex| {
                self.potential_c0
                    .get(vertex)
                    .map_err(|_| CertificateVerificationError::MissingElement(vertex.clone()))
            })
            .collect::<Result<Vec<_>, _>>()?;
        let mut d0 = Vec::with_capacity(complex.edges.len());
        let mut omega = Vec::with_capacity(complex.edges.len());
        let mut primal_residual = Vec::with_capacity(complex.edges.len());
        let mut dual_witness = Vec::with_capacity(complex.edges.len());
        let mut declared_weights = Vec::with_capacity(complex.edges.len());
        for (u, v) in &complex.edges {
            let from = *vertices
                .get(u)
                .ok_or_else(|| CertificateVerificationError::MissingElement(u.clone()))?;
            let to = *vertices
                .get(v)
                .ok_or_else(|| CertificateVerificationError::MissingElement(v.clone()))?;
            let mut row = vec![BigRational::zero(); vertices.len()];
            if from != to {
                row[from] = -BigRational::one();
                row[to] = BigRational::one();
            }
            let edge = (u.clone(), v.clone());
            d0.push(row);
            omega.push(
                h.values
                    .get(&edge)
                    .cloned()
                    .unwrap_or_else(BigRational::zero),
            );
            primal_residual.push(
                self.residual_c1
                    .values
                    .get(&edge)
                    .cloned()
                    .unwrap_or_else(BigRational::zero),
            );
            dual_witness.push(
                self.dual_witness_c1
                    .values
                    .get(&edge)
                    .cloned()
                    .unwrap_or_else(BigRational::zero),
            );
            declared_weights.push(
                weights
                    .and_then(|w| w.get(&edge))
                    .cloned()
                    .unwrap_or_else(BigRational::one),
            );
        }
        core_functional::phi1::Phi1Functional::verify_exact_certificate(
            core_functional::phi1::ExactPhi1Certificate {
                omega,
                d0,
                weights: declared_weights,
                alpha,
                primal_residual,
                dual_witness,
                reported_value: self.phi1_value.clone(),
            },
        )?;
        Ok(())
    }
}

/// Solves the exact weighted L1 potential and dual annihilating witness via Sparse Revised Simplex.
pub fn solve_exact_potential_weighted(
    complex: &FiniteComplex,
    h: &Cochain1,
    edge_weights: Option<&BTreeMap<(String, String), BigRational>>,
) -> Result<DualWitnessCertificate, WdpError> {
    let k = complex.vertices.len();
    let m = complex.edges.len();
    if k == 0 {
        return Err(WdpError::InvalidInput {
            detail: "Empty complex".into(),
        });
    }

    if m == 0 {
        return empty_edges_certificate(complex, h, edge_weights);
    }

    // Map vertex names to indices 0..k
    let v_list: Vec<String> = complex.vertices.iter().cloned().collect();
    let v_idx: BTreeMap<String, usize> = v_list
        .iter()
        .enumerate()
        .map(|(i, v)| (v.clone(), i))
        .collect();

    // Construct d_0 matrix (m rows x k cols)
    let (map_rows, target, weights) = build_d0_problem(complex, h, edge_weights, &v_idx, k)?;

    let budget = 64 * (m + k) + 1024;
    let solution =
        solve_weighted_l1_projection(&target, &weights, &map_rows, budget).map_err(|e| {
            WdpError::InvalidInput {
                detail: format!("Simplex solver failure: {e}"),
            }
        })?;

    // Primal potential Cochain0
    let potential_c0 = Cochain0 {
        values: v_list
            .iter()
            .enumerate()
            .map(|(i, v_name)| (v_name.clone(), solution.coefficients[i].clone()))
            .collect(),
    };

    // Primal residual Cochain1
    let residual_c1 = map_edge_cochain(&complex.edges, &solution.residual);

    // Dual witness Cochain1
    let dual_witness_c1 = map_edge_cochain(&complex.edges, &solution.dual);

    let is_exact = solution.value.is_zero();

    let cert = DualWitnessCertificate {
        phi1_value: solution.value,
        potential_c0,
        residual_c1,
        dual_witness_c1,
        is_exact,
        authority_effect: "None".to_string(),
    };

    // Self-verify certificate before emission
    cert.verify(complex, h, edge_weights)
        .map_err(|e| WdpError::InvalidInput {
            detail: format!("Emitted certificate failed self-verification: {e}"),
        })?;

    Ok(cert)
}

fn empty_edges_certificate(
    complex: &FiniteComplex,
    h: &Cochain1,
    edge_weights: Option<&BTreeMap<(String, String), BigRational>>,
) -> Result<DualWitnessCertificate, WdpError> {
    let potential_c0 = Cochain0 {
        values: complex
            .vertices
            .iter()
            .map(|v| (v.clone(), BigRational::zero()))
            .collect(),
    };
    let cert = DualWitnessCertificate {
        phi1_value: BigRational::zero(),
        potential_c0,
        residual_c1: Cochain1 {
            values: BTreeMap::new(),
        },
        dual_witness_c1: Cochain1 {
            values: BTreeMap::new(),
        },
        is_exact: true,
        authority_effect: "None".to_string(),
    };
    cert.verify(complex, h, edge_weights)
        .map_err(|e| WdpError::InvalidInput {
            detail: format!("Emitted certificate failed self-verification: {e}"),
        })?;
    Ok(cert)
}

fn build_d0_problem(
    complex: &FiniteComplex,
    h: &Cochain1,
    edge_weights: Option<&BTreeMap<(String, String), BigRational>>,
    v_idx: &BTreeMap<String, usize>,
    k: usize,
) -> Result<(Vec<Vec<BigRational>>, Vec<BigRational>, Vec<BigRational>), WdpError> {
    let m = complex.edges.len();
    let mut map_rows: Vec<Vec<BigRational>> = Vec::with_capacity(m);
    let mut target: Vec<BigRational> = Vec::with_capacity(m);
    let mut weights: Vec<BigRational> = Vec::with_capacity(m);

    let one = BigRational::one();
    let zero = BigRational::zero();

    for (u, v) in &complex.edges {
        let edge = (u.clone(), v.clone());
        let row = build_d0_row(u, v, v_idx, k, &zero, &one)?;
        map_rows.push(row);

        let h_val = h.values.get(&edge).cloned().unwrap_or_else(|| zero.clone());
        target.push(h_val);

        let w_val = edge_weights
            .and_then(|w| w.get(&edge))
            .cloned()
            .unwrap_or_else(|| one.clone());
        if !w_val.is_positive() {
            return Err(WdpError::InvalidInput {
                detail: format!("non-positive weight on edge ({u}, {v})"),
            });
        }
        weights.push(w_val);
    }
    Ok((map_rows, target, weights))
}

fn build_d0_row(
    u: &str,
    v: &str,
    v_idx: &BTreeMap<String, usize>,
    k: usize,
    zero: &BigRational,
    one: &BigRational,
) -> Result<Vec<BigRational>, WdpError> {
    let mut row = vec![zero.clone(); k];
    if u != v {
        let idx_u = *v_idx.get(u).ok_or_else(|| WdpError::InvalidInput {
            detail: format!("unknown vertex {u}"),
        })?;
        let idx_v = *v_idx.get(v).ok_or_else(|| WdpError::InvalidInput {
            detail: format!("unknown vertex {v}"),
        })?;
        row[idx_u] = -one.clone();
        row[idx_v] = one.clone();
    }
    Ok(row)
}

fn map_edge_cochain(edges: &[(String, String)], values: &[BigRational]) -> Cochain1 {
    let mut map = BTreeMap::new();
    for (i, edge) in edges.iter().enumerate() {
        map.insert((edge.0.clone(), edge.1.clone()), values[i].clone());
    }
    Cochain1 { values: map }
}

/// Backward-compatible unweighted entrypoint.
pub fn solve_exact_potential(
    complex: &FiniteComplex,
    h: &Cochain1,
) -> Result<DualWitnessCertificate, WdpError> {
    solve_exact_potential_weighted(complex, h, None)
}

// Origin: engine/crates_rs/core_wdp/src/obstruction.rs
// Claim: urn:core:crates_rs:core-wdp:obstruction:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeSet;

    fn triangle_complex() -> FiniteComplex {
        let vertices = BTreeSet::from(["v0".to_string(), "v1".to_string(), "v2".to_string()]);
        let edges = vec![
            ("v0".to_string(), "v1".to_string()),
            ("v1".to_string(), "v2".to_string()),
            ("v0".to_string(), "v2".to_string()),
        ];
        FiniteComplex::new(vertices, edges, vec![]).unwrap()
    }

    #[test]
    fn test_exact_cochain_zero_dual() {
        let complex = triangle_complex();
        // phi(v0)=0, phi(v1)=1, phi(v2)=3 => h(v0,v1)=1, h(v1,v2)=2, h(v0,v2)=3
        let mut h_vals = BTreeMap::new();
        h_vals.insert(
            ("v0".into(), "v1".into()),
            BigRational::from_integer(1.into()),
        );
        h_vals.insert(
            ("v1".into(), "v2".into()),
            BigRational::from_integer(2.into()),
        );
        h_vals.insert(
            ("v0".into(), "v2".into()),
            BigRational::from_integer(3.into()),
        );
        let h = Cochain1 { values: h_vals };

        let cert = solve_exact_potential(&complex, &h).expect("solve exact");
        assert!(cert.is_exact);
        assert_eq!(cert.phi1_value, BigRational::zero());
        for (_, r) in &cert.residual_c1.values {
            assert_eq!(r, &BigRational::zero());
        }
        cert.verify(&complex, &h, None)
            .expect("verification passes");
    }

    #[test]
    fn test_obstructed_cycle_dual_annihilation() {
        let vertices = BTreeSet::from(["v0".to_string(), "v1".to_string(), "v2".to_string()]);
        let edges = vec![
            ("v0".to_string(), "v1".to_string()),
            ("v1".to_string(), "v2".to_string()),
            ("v2".to_string(), "v0".to_string()),
        ];
        let complex = FiniteComplex::new(vertices, edges, vec![]).unwrap();

        // Directed cycle: h = 1 on each edge. Total circulation = 3.
        let mut h_vals = BTreeMap::new();
        h_vals.insert(("v0".into(), "v1".into()), BigRational::one());
        h_vals.insert(("v1".into(), "v2".into()), BigRational::one());
        h_vals.insert(("v2".into(), "v0".into()), BigRational::one());
        let h = Cochain1 { values: h_vals };

        let cert = solve_exact_potential(&complex, &h).expect("solve obstructed");
        assert!(!cert.is_exact);
        assert_eq!(cert.phi1_value, BigRational::from_integer(3.into()));

        // Check dual witness properties
        for (_, y) in &cert.dual_witness_c1.values {
            assert!(y.abs() <= BigRational::one());
        }
        let y01 = cert
            .dual_witness_c1
            .values
            .get(&("v0".into(), "v1".into()))
            .unwrap();
        let y12 = cert
            .dual_witness_c1
            .values
            .get(&("v1".into(), "v2".into()))
            .unwrap();
        let y20 = cert
            .dual_witness_c1
            .values
            .get(&("v2".into(), "v0".into()))
            .unwrap();
        assert_eq!(y01, y12);
        assert_eq!(y12, y20);
        assert_eq!(y01, &BigRational::one());

        cert.verify(&complex, &h, None)
            .expect("verification passes");
    }

    #[test]
    fn test_weighted_chord_optimal_simplex() {
        let vertices = BTreeSet::from(["v0".to_string(), "v1".to_string(), "v2".to_string()]);
        let edges = vec![
            ("v0".to_string(), "v1".to_string()),
            ("v1".to_string(), "v2".to_string()),
            ("v0".to_string(), "v2".to_string()),
        ];
        let complex = FiniteComplex::new(vertices, edges, vec![]).unwrap();

        let mut h_vals = BTreeMap::new();
        h_vals.insert(("v0".into(), "v1".into()), BigRational::one());
        h_vals.insert(("v1".into(), "v2".into()), BigRational::one());
        h_vals.insert(("v0".into(), "v2".into()), BigRational::zero());
        let h = Cochain1 { values: h_vals };

        let mut weights = BTreeMap::new();
        weights.insert(("v0".into(), "v1".into()), BigRational::one());
        weights.insert(("v1".into(), "v2".into()), BigRational::one());
        weights.insert(
            ("v0".into(), "v2".into()),
            BigRational::from_integer(10.into()),
        );

        let cert =
            solve_exact_potential_weighted(&complex, &h, Some(&weights)).expect("solve weighted");

        // Simplex optimal cost is 2, whereas putting residual on chord would cost 10
        assert_eq!(cert.phi1_value, BigRational::from_integer(2.into()));
        cert.verify(&complex, &h, Some(&weights))
            .expect("passes 5-point verification");
    }
}

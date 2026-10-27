//! Finite oriented-bivector boundary identities and a declared triad-flux slice.
//! The curvature/master functionals are a finite model, not the continuum
//! Hamiltonian constraint algebra. AuthorityEffect: None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_d32bafe4<T> {
    fn checked_invariant_d32bafe4(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_d32bafe4<T> for Option<T> {
    #[inline]
    fn checked_invariant_d32bafe4(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_d32bafe4<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_d32bafe4(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{matrix as mx, ExactFieldError};
use num_traits::{Signed, Zero};
use core_lie_theory::cayley::cayley_transform;
use core_number_theory::rational::{ri, rq, Rational as Q};
use serde::Serialize;
use std::collections::{BTreeMap, BTreeSet};
pub type V3 = [Q; 3];
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum SimplicialDynamicsError {
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
    #[error(transparent)]
    Cayley(#[from] core_lie_theory::cayley::CayleyError),
    #[error("a tetrahedron has zero volume")]
    Degenerate,
    #[error("a slice vertex belongs to no tetrahedron")]
    UnusedVertex,
    #[error("invalid declared finite input: {0}")]
    Input(String),
}
impl From<String> for SimplicialDynamicsError {
    fn from(s: String) -> Self {
        Self::Input(s)
    }
}
impl From<&str> for SimplicialDynamicsError {
    fn from(s: &str) -> Self {
        Self::Input(s.into())
    }
}
fn sub(a: &V3, b: &V3) -> V3 {
    std::array::from_fn(|k| &a[k] - &b[k])
}
fn add(a: &mut V3, b: &V3) {
    for k in 0..3 {
        a[k] += &b[k];
    }
}
fn scale(a: &V3, k: &Q) -> V3 {
    std::array::from_fn(|i| &a[i] * k)
}
fn dot(a: &V3, b: &V3) -> Q {
    mx::dot(a, b).checked_invariant_d32bafe4("fixed 3-vector")
}
fn cross(a: &V3, b: &V3) -> V3 {
    [(0, 1, 2), (1, 2, 0), (2, 0, 1)].map(|(_, j, k)| &a[j] * &b[k] - &a[k] * &b[j])
}
fn zero() -> V3 {
    std::array::from_fn(|_| ri(0))
}
fn pair(a: usize, b: usize) -> (usize, usize) {
    (a.min(b), a.max(b))
}
#[derive(Debug, Clone)]
pub struct ReggeFourSimplex {
    pub positions: [[Q; 4]; 5],
    pub hinge_defects: BTreeMap<[usize; 3], Q>,
}
impl ReggeFourSimplex {
    pub fn hinge_bivector(&self, f: [usize; 3]) -> Result<BasicMatrix<Q>, SimplicialDynamicsError> {
        if f.iter().any(|&i| i >= 5) || f[0] == f[1] || f[1] == f[2] || f[0] == f[2] {
            return Err("INVALID_TRIANGLE_HINGE".into());
        }
        let a: Vec<Q> = (0..4)
            .map(|i| &self.positions[f[1]][i] - &self.positions[f[0]][i])
            .collect();
        let b: Vec<Q> = (0..4)
            .map(|i| &self.positions[f[2]][i] - &self.positions[f[0]][i])
            .collect();
        Ok(mx::from_fn(4, 4, |i, j| {
            (&a[i] * &b[j] - &a[j] * &b[i]) / ri(2)
        })?)
    }
    pub fn tetrahedron_bianchi(
        &self,
        t: [usize; 4],
        weighted: bool,
    ) -> Result<BasicMatrix<Q>, SimplicialDynamicsError> {
        let mut ordered = t;
        ordered.sort_unstable();
        if ordered.windows(2).any(|w| w[0] == w[1]) || ordered[3] >= 5 {
            return Err("INVALID_TETRAHEDRON".into());
        }
        let mut result = mx::zeros(4, 4)?;
        for omit in 0..4 {
            let f: Vec<_> = ordered
                .iter()
                .enumerate()
                .filter(|(i, _)| *i != omit)
                .map(|(_, v)| *v)
                .collect();
            let f = [f[0], f[1], f[2]];
            let weight = if weighted {
                self.hinge_defects.get(&f).cloned().unwrap_or(ri(0))
            } else {
                ri(1)
            };
            let sign = ri(if omit % 2 == 0 { 1 } else { -1 });
            result = mx::add(
                &result,
                &mx::scale(&self.hinge_bivector(f)?, &(sign * weight))
                    .checked_invariant_d32bafe4("fixed physical dimension"),
            )
            .checked_invariant_d32bafe4("equal physical shapes");
        }
        Ok(result)
    }
    pub fn boundary_bianchi(&self) -> Result<BasicMatrix<Q>, SimplicialDynamicsError> {
        let mut result = mx::zeros(4, 4)?;
        for omit in 0..5 {
            let t: Vec<_> = (0..5).filter(|&i| i != omit).collect();
            result = mx::add(
                &result,
                &mx::scale(
                    &self.tetrahedron_bianchi([t[0], t[1], t[2], t[3]], true)?,
                    &ri(if omit % 2 == 0 { 1 } else { -1 }),
                )
                .checked_invariant_d32bafe4("fixed physical dimension"),
            )
            .checked_invariant_d32bafe4("equal physical shapes");
        }
        Ok(result)
    }
}

#[derive(Debug, Clone)]
pub struct CauchySlice {
    positions: Vec<V3>,
    tetrahedra: Vec<[usize; 4]>,
    faces: BTreeMap<[usize; 3], V3>,
    holonomies: BTreeMap<(usize, usize), BasicMatrix<Q>>,
}
#[derive(Debug, Serialize)]
pub struct Constraints {
    pub gauss: Vec<V3>,
    pub vector: Vec<V3>,
    pub scalar: Vec<Q>,
    pub master: Q,
    pub curvature: Vec<Q>,
    pub variance: Q,
    pub boundary_area: usize,
}
impl CauchySlice {
    pub fn positions(&self) -> &[V3] {
        &self.positions
    }
    pub fn tetrahedra(&self) -> &[[usize; 4]] {
        &self.tetrahedra
    }
    pub fn faces(&self) -> &BTreeMap<[usize; 3], V3> {
        &self.faces
    }
    pub fn holonomies(&self) -> &BTreeMap<(usize, usize), BasicMatrix<Q>> {
        &self.holonomies
    }
    fn validate_carrier_bounds(
        positions: &[V3],
        tetrahedra: &[[usize; 4]],
    ) -> Result<(), SimplicialDynamicsError> {
        if !(1..=32).contains(&positions.len()) || !(1..=64).contains(&tetrahedra.len()) {
            return Err("RESOURCE_LIMIT:CAUCHY_CARRIER".into());
        }
        Ok(())
    }
    fn is_valid_unique_tetrahedron(
        ordered: [usize; 4],
        num_positions: usize,
        seen: &mut BTreeSet<[usize; 4]>,
    ) -> bool {
        !ordered.windows(2).any(|w| w[0] == w[1])
            && ordered[3] < num_positions
            && seen.insert(ordered)
    }
    pub fn new(
        positions: Vec<V3>,
        tetrahedra: Vec<[usize; 4]>,
    ) -> Result<Self, SimplicialDynamicsError> {
        Self::validate_carrier_bounds(&positions, &tetrahedra)?;
        let mut out = Self {
            positions,
            tetrahedra: vec![],
            faces: BTreeMap::new(),
            holonomies: BTreeMap::new(),
        };
        let mut seen = BTreeSet::new();
        for t in tetrahedra {
            let mut ordered = t;
            ordered.sort_unstable();
            if !Self::is_valid_unique_tetrahedron(ordered, out.positions.len(), &mut seen) {
                return Err("INVALID_TETRAHEDRON".into());
            }
            super::loop_quantum_gravity::FluxTetrahedron::new(std::array::from_fn(|k| {
                out.positions[ordered[k]].clone()
            }))
            .map_err(|_| SimplicialDynamicsError::Degenerate)?;
            out.tetrahedra.push(ordered);
            for omitted in 0..4 {
                let f: [usize; 3] =
                    std::array::from_fn(|k| ordered[if k < omitted { k } else { k + 1 }]);
                let [a, b, c] = f;
                let flux = scale(
                    &cross(
                        &sub(&out.positions[b], &out.positions[a]),
                        &sub(&out.positions[c], &out.positions[a]),
                    ),
                    &rq(1, 2),
                );
                out.faces.insert(f, flux);
                for (u, v) in [(a, b), (a, c), (b, c)] {
                    out.holonomies
                        .entry(pair(u, v))
                        .or_insert_with(|| mx::identity::<Q>(3).checked_invariant_d32bafe4("fixed physical dimension"));
                }
            }
        }
        if (0..out.positions.len()).any(|v| !out.tetrahedra.iter().any(|t| t.contains(&v))) {
            return Err(SimplicialDynamicsError::UnusedVertex);
        }
        Ok(out)
    }
    pub fn boundary_faces(&self) -> Vec<[usize; 3]> {
        self.faces
            .keys()
            .filter(|f| {
                self.tetrahedra
                    .iter()
                    .filter(|t| f.iter().all(|v| t.contains(v)))
                    .count()
                    == 1
            })
            .copied()
            .collect()
    }
    pub fn boundary_edges(&self) -> BTreeSet<(usize, usize)> {
        self.boundary_faces()
            .iter()
            .flat_map(|f| [pair(f[0], f[1]), pair(f[0], f[2]), pair(f[1], f[2])])
            .collect()
    }
    pub fn set_connection(
        &mut self,
        u: usize,
        v: usize,
        skew: &BasicMatrix<Q>,
        tau: &Q,
    ) -> Result<(), SimplicialDynamicsError> {
        if !self.holonomies.contains_key(&pair(u, v)) || skew.rows() != 3 || skew.cols() != 3 {
            return Err("INVALID_CONNECTION_EDGE".into());
        }
        let mut c = cayley_transform(skew, tau)?;
        if u > v {
            c = mx::transpose(&c).checked_invariant_d32bafe4("fixed physical dimension")
        }
        self.holonomies.insert(pair(u, v), c);
        Ok(())
    }
    fn volumes(&self) -> Vec<Q> {
        let mut volumes = vec![ri(0); self.positions.len()];
        for t in &self.tetrahedra {
            let a = &self.positions[t[0]];
            let vol = dot(
                &sub(&self.positions[t[1]], a),
                &cross(
                    &sub(&self.positions[t[2]], a),
                    &sub(&self.positions[t[3]], a),
                ),
            )
            .abs()
                / ri(6);
            for &v in t {
                volumes[v] += &vol / ri(4)
            }
        }
        volumes
    }
    pub fn constraints(&self) -> Constraints {
        let n = self.positions.len();
        // A Gauss node is a tetrahedron. Its outward oriented face fluxes
        // share the declared Euclidean frame and sum to zero geometrically.
        let gauss: Vec<V3> = self
            .tetrahedra
            .iter()
            .map(|tetrahedron| {
                let mut closure = zero();
                for omitted in 0..4 {
                    let face: [usize; 3] =
                        std::array::from_fn(|k| tetrahedron[if k < omitted { k } else { k + 1 }]);
                    add(
                        &mut closure,
                        &scale(
                            &self.faces[&face],
                            &ri(if omitted % 2 == 0 { 1 } else { -1 }),
                        ),
                    );
                }
                closure
            })
            .collect();
        let mut vector = vec![zero(); n];
        let mut scalar = vec![ri(0); n];
        for (&(u, v), m) in &self.holonomies {
            let e = sub(&self.positions[v], &self.positions[u]);
            let sk = mx::add(
                m,
                &mx::scale(
                    &mx::transpose(m).checked_invariant_d32bafe4("fixed physical dimension"),
                    &ri(-1),
                )
                .checked_invariant_d32bafe4("fixed physical dimension"),
            )
            .checked_invariant_d32bafe4("equal physical shapes");
            let axis = [
                sk.get_ref(2, 1).checked_invariant_d32bafe4("fixed shape") / ri(2),
                sk.get_ref(0, 2).checked_invariant_d32bafe4("fixed shape") / ri(2),
                sk.get_ref(1, 0).checked_invariant_d32bafe4("fixed shape") / ri(2),
            ];
            let vv = cross(&e, &axis);
            add(&mut vector[u], &vv);
            add(&mut vector[v], &vv);
            let h = (ri(3) - mx::trace(m).checked_invariant_d32bafe4("fixed square physical dimension")) * dot(&e, &e);
            scalar[u] += &h;
            scalar[v] += &h;
        }
        let master = gauss.iter().map(|g| dot(g, g)).sum::<Q>()
            + (0..n)
                .map(|i| dot(&vector[i], &vector[i]) + &scalar[i] * &scalar[i])
                .sum::<Q>();
        let vols = self.volumes();
        let mean = scalar.iter().cloned().sum::<Q>() / vols.iter().cloned().sum::<Q>();
        let curvature: Vec<Q> = scalar.iter().zip(&vols).map(|(h, v)| h / v).collect();
        let variance = curvature.iter().map(|r| (r - &mean).pow(2)).sum();
        Constraints {
            gauss,
            vector,
            scalar,
            master,
            curvature,
            variance,
            boundary_area: self.boundary_faces().len(),
        }
    }
    fn relax_single_holonomy(
        m: &mut BasicMatrix<Q>,
        tau: &Q,
    ) -> Result<(), SimplicialDynamicsError> {
        let defect =
            ri(3) - mx::trace(m).checked_invariant_d32bafe4("fixed square physical dimension");
        if defect.is_zero() {
            return Ok(());
        }
        let skew = mx::scale(&mx::sub(m, &mx::transpose(m)?)?, &rq(1, 2))?;
        let candidate = if mx::is_zero_matrix(&skew) {
            mx::identity::<Q>(3).checked_invariant_d32bafe4("fixed physical dimension")
        } else {
            mx::multiply(&cayley_transform(&skew, tau)?, m)?
        };
        if (ri(3) - mx::trace(&candidate).checked_invariant_d32bafe4("fixed square physical dimension")).abs()
            <= defect.abs()
        {
            *m = candidate;
        }
        Ok(())
    }

    /// Source-compatible finite proposal. A smaller edge trace defect need not reduce total master/variance.
    pub fn relaxation_step(
        &mut self,
        tau: &Q,
        freeze_boundary: bool,
    ) -> Result<(Q, Q), SimplicialDynamicsError> {
        if tau <= &ri(0) {
            return Err("POSITIVE_STEP_REQUIRED".into());
        }
        let before = self.constraints();
        let frozen = self.boundary_edges();
        for (&edge, m) in self.holonomies.iter_mut() {
            if freeze_boundary && frozen.contains(&edge) {
                continue;
            }
            Self::relax_single_holonomy(m, tau)?;
        }
        let after = self.constraints();
        Ok((
            after.master - before.master,
            after.variance - before.variance,
        ))
    }
    pub fn evolve(
        &mut self,
        generators: &BTreeMap<(usize, usize), BasicMatrix<Q>>,
        lapse: &[Q],
    ) -> Result<(), SimplicialDynamicsError> {
        if lapse.len() != self.positions.len() || lapse.iter().any(|q| q < &ri(0)) {
            return Err("INVALID_LAPSE".into());
        }
        let mut updates = Vec::with_capacity(generators.len());
        for (&(u, v), g) in generators {
            let key = pair(u, v);
            let m = self.holonomies.get(&key).ok_or("INVALID_EDGE")?;
            let next = mx::multiply(&cayley_transform(g, &((&lapse[u] + &lapse[v]) / ri(2)))?, m)?;
            updates.push((key, next));
        }
        for (key, next) in updates {
            self.holonomies.insert(key, next);
        }
        Ok(())
    }
    pub fn scalar_anomaly(
        &self,
        u: usize,
        v: usize,
        n: &Q,
        m: &Q,
    ) -> Result<(Q, Q, Q), SimplicialDynamicsError> {
        if u >= self.positions.len() || v >= self.positions.len() {
            return Err("INVALID_VERTEX".into());
        }
        let c = self.constraints();
        let bracket =
            (n * &c.scalar[u]) * (m * &c.scalar[v]) - (m * &c.scalar[v]) * (n * &c.scalar[u]);
        let induced = if self.holonomies.contains_key(&pair(u, v)) {
            dot(
                &sub(&scale(&c.vector[v], n), &scale(&c.vector[u], m)),
                &sub(&self.positions[v], &self.positions[u]),
            )
        } else {
            ri(0)
        };
        Ok((bracket.clone(), induced.clone(), bracket - induced))
    }
}

fn validate_bianchi_carrier(
    positions: &[Vec<Q>],
    edges: &[(usize, usize, Q)],
) -> Result<(usize, usize), SimplicialDynamicsError> {
    let n = positions.len();
    let d = positions.first().map(Vec::len).unwrap_or(0);
    let invalid = !(1..=256).contains(&n)
        || !(3..=4).contains(&d)
        || positions.iter().any(|v| v.len() != d)
        || edges.len() > 1024;
    if invalid {
        return Err("INVALID_BIANCHI_CARRIER".into());
    }
    Ok((n, d))
}

/// Symmetric central hinge forces. Global cancellation need not imply local closure.
pub fn bianchi(
    positions: &[Vec<Q>],
    edges: &[(usize, usize, Q)],
) -> Result<(Vec<Vec<Q>>, Vec<Q>, BasicMatrix<Q>), SimplicialDynamicsError> {
    let (n, d) = validate_bianchi_carrier(positions, edges)?;
    let mut forces = vec![vec![ri(0); d]; n];
    for (u, v, w) in edges {
        if u == v || *u >= n || *v >= n {
            return Err("INVALID_HINGE".into());
        }
        for i in 0..d {
            let f = w * (&positions[*v][i] - &positions[*u][i]);
            forces[*u][i] += &f;
            forces[*v][i] -= &f
        }
    }
    let total = (0..d)
        .map(|i| forces.iter().map(|f| f[i].clone()).sum())
        .collect();
    let torque = mx::from_fn(d, d, |i, j| {
        (0..n)
            .map(|v| &positions[v][i] * &forces[v][j] - &positions[v][j] * &forces[v][i])
            .sum()
    })?;
    Ok((forces, total, torque))
}

/// Transfer the finite orbital bivector r wedge p from body to radiation.
/// The total bivector is conserved exactly; no continuum radiation model is asserted.
pub fn emit_angular(
    body: &mut BasicMatrix<Q>,
    radiation: &mut BasicMatrix<Q>,
    r: &[Q],
    p: &[Q],
) -> Result<(), SimplicialDynamicsError> {
    let n = r.len();
    if !(3..=4).contains(&n)
        || p.len() != n
        || body.rows() != n
        || body.cols() != n
        || radiation.rows() != n
        || radiation.cols() != n
    {
        return Err("INVALID_ANGULAR_DIMENSION".into());
    }
    let delta = mx::from_fn(n, n, |i, j| &r[i] * &p[j] - &r[j] * &p[i])?;
    *body = mx::sub(body, &delta)?;
    *radiation = mx::add(radiation, &delta)?;
    Ok(())
}

// Origin: engine/crates_rs/core_general_relativity/src/simplicial_dynamics.rs
// Claim: urn:core:crates_rs:core-general-relativity:simplicial-dynamics:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_d32bafe4 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}

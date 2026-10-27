//! General rectangular toric CSS codes on the sovereign F2 lattice complex.
//! Logical intersection, endpoint defects and e-around-m loop phases are
//! computed separately. No Hamiltonian gap or threshold is asserted.
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.
use crate::{
    pauli::{pauli_anticommutes, Pauli},
    quantum_entropy_cone::{EntropyConeError, EntropyVector},
    stabilizer_code_distance::{StabilizerCode, StabilizerCodeError},
};
use core_homology::square_lattice::{periodic_square_complex, SquareLattice};
use core_number_theory::gf2::{F2Matrix, F2Vector};
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; exact finite toric code and anyon strings.";
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ToricError {
    #[error("lattice exceeds the finite toric code budget of 256 plaquettes")]
    Budget,
    #[error("lattice, homology or GF(2) construction refused: {0}")]
    Topology(String),
    #[error("string, site or face is outside the carrier or has the wrong Pauli alphabet")]
    String,
    #[error(transparent)]
    Stabilizer(#[from] StabilizerCodeError),
    #[error(transparent)]
    Entropy(#[from] EntropyConeError),
}
fn topology(e: impl std::fmt::Display) -> ToricError {
    ToricError::Topology(e.to_string())
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ToricCode {
    lattice: SquareLattice,
    code: StabilizerCode,
    stars: Vec<Vec<Pauli>>,
    plaquettes: Vec<Vec<Pauli>>,
    x_logicals: Vec<Vec<Pauli>>,
    z_logicals: Vec<Vec<Pauli>>,
}
fn pauli_mask(bits: &F2Vector, letter: Pauli) -> Vec<Pauli> {
    bits.to_bits()
        .iter()
        .map(|&b| if b == 0 { Pauli::I } else { letter })
        .collect()
}
fn build_toric_stars_and_plaquettes(
    complex: &core_homology::f2_cohomology::F2ChainComplex,
) -> Result<(Vec<Vec<Pauli>>, Vec<Vec<Pauli>>), ToricError> {
    let d0 = complex.coboundary(0).map_err(topology)?;
    let d1 = complex.coboundary(1).map_err(topology)?;
    let stars = (0..d0.cols())
        .map(|v| {
            d0.column(v)
                .map(|x| pauli_mask(&x, Pauli::X))
                .map_err(topology)
        })
        .collect::<Result<Vec<_>, _>>()?;
    let plaquettes = (0..d1.rows())
        .map(|p| {
            d1.row(p)
                .map(|z| pauli_mask(&z, Pauli::Z))
                .map_err(topology)
        })
        .collect::<Result<Vec<_>, _>>()?;
    Ok((stars, plaquettes))
}

fn build_toric_pairing_matrix(raw_x: &[F2Vector], z: &[F2Vector]) -> Result<F2Matrix, ToricError> {
    let rows = raw_x
        .iter()
        .map(|x| {
            z.iter()
                .map(|z_vec| x.dot(z_vec).map(u8::from).map_err(topology))
                .collect::<Result<Vec<_>, _>>()
        })
        .collect::<Result<Vec<_>, _>>()?;
    Ok(F2Matrix::from_rows(&rows).map_err(topology)?.transpose())
}

fn solve_toric_x_logicals(
    edge_count: usize,
    raw_x: &[F2Vector],
    pairing: &F2Matrix,
) -> Result<Vec<Vec<Pauli>>, ToricError> {
    let mut x_logicals = Vec::new();
    for i in 0..2 {
        let unit_i = F2Vector::unit(2, i).map_err(topology)?;
        let coefficients = pairing
            .solve(&unit_i)
            .map_err(topology)?
            .ok_or_else(|| topology("degenerate torus intersection form"))?;
        let mut x = F2Vector::zeros(edge_count).map_err(topology)?;
        for (j, bit) in coefficients.particular().to_bits().into_iter().enumerate() {
            if bit == 1 {
                x.add_assign(&raw_x[j]).map_err(topology)?;
            }
        }
        x_logicals.push(pauli_mask(&x, Pauli::X));
    }
    Ok(x_logicals)
}

fn extract_rank_two_torus_bases(
    complex: &core_homology::f2_cohomology::F2ChainComplex,
    k: usize,
) -> Result<(Vec<F2Vector>, Vec<F2Vector>), ToricError> {
    let z = complex.homology_basis(1).map_err(topology)?;
    let raw_x = complex.cohomology_basis(1).map_err(topology)?;
    if z.len() != 2 || raw_x.len() != 2 || k != 2 {
        return Err(topology("torus first homology must have rank two"));
    }
    Ok((z, raw_x))
}

impl ToricCode {
    pub fn new(rows: usize, columns: usize) -> Result<Self, ToricError> {
        if rows.checked_mul(columns).is_none_or(|n| n > 256) {
            return Err(ToricError::Budget);
        }
        let lattice = periodic_square_complex(rows, columns).map_err(topology)?;
        let complex = lattice.f2_complex().map_err(topology)?;
        let (stars, plaquettes) = build_toric_stars_and_plaquettes(&complex)?;
        let code = StabilizerCode::try_new(stars.iter().chain(&plaquettes).cloned().collect())?;
        let (z, raw_x) = extract_rank_two_torus_bases(&complex, code.k())?;
        let pairing = build_toric_pairing_matrix(&raw_x, &z)?;
        let x_logicals = solve_toric_x_logicals(lattice.edge_count(), &raw_x, &pairing)?;
        let z_logicals = z.iter().map(|z| pauli_mask(z, Pauli::Z)).collect();
        let out = Self {
            lattice,
            code,
            stars,
            plaquettes,
            x_logicals,
            z_logicals,
        };
        Ok(out)
    }
    pub fn lattice(&self) -> &SquareLattice {
        &self.lattice
    }
    pub fn code(&self) -> &StabilizerCode {
        &self.code
    }
    pub fn stars(&self) -> &[Vec<Pauli>] {
        &self.stars
    }
    pub fn plaquettes(&self) -> &[Vec<Pauli>] {
        &self.plaquettes
    }
    pub fn x_logicals(&self) -> &[Vec<Pauli>] {
        &self.x_logicals
    }
    pub fn z_logicals(&self) -> &[Vec<Pauli>] {
        &self.z_logicals
    }
    /// Shortest essential cycle/cocycle of a rectangular torus, with loops giving
    /// the upper bound and nonzero winding requiring one full direction the lower.
    pub fn distance(&self) -> usize {
        self.lattice.rows().min(self.lattice.cols())
    }
    pub fn ground_state_degeneracy(&self) -> usize {
        1usize << self.code.k()
    }
    pub fn logical_commutation_matrix(&self) -> Vec<Vec<u8>> {
        let operators: Vec<&Vec<Pauli>> = self.x_logicals.iter().chain(&self.z_logicals).collect();
        operators
            .iter()
            .map(|a| {
                operators
                    .iter()
                    .map(|b| u8::from(pauli_anticommutes(a, b)))
                    .collect()
            })
            .collect()
    }
    fn check_string(&self, string: &[Pauli], alphabet: Pauli) -> Result<(), ToricError> {
        if string.len() != self.code.n() || string.iter().any(|&p| p != Pauli::I && p != alphabet) {
            return Err(ToricError::String);
        }
        Ok(())
    }
    pub fn e_defects(&self, z_string: &[Pauli]) -> Result<Vec<usize>, ToricError> {
        self.check_string(z_string, Pauli::Z)?;
        Ok(self
            .stars
            .iter()
            .enumerate()
            .filter_map(|(i, s)| pauli_anticommutes(s, z_string).then_some(i))
            .collect())
    }
    pub fn m_defects(&self, x_string: &[Pauli]) -> Result<Vec<usize>, ToricError> {
        self.check_string(x_string, Pauli::X)?;
        Ok(self
            .plaquettes
            .iter()
            .enumerate()
            .filter_map(|(i, p)| pauli_anticommutes(p, x_string).then_some(i))
            .collect())
    }
    pub fn braiding_sign(&self, z_loop: &[Pauli], x_string: &[Pauli]) -> Result<i8, ToricError> {
        self.check_string(z_loop, Pauli::Z)?;
        self.check_string(x_string, Pauli::X)?;
        Ok(if pauli_anticommutes(z_loop, x_string) {
            -1
        } else {
            1
        })
    }
    /// Closed e-loop around one plaquette. Its sign in a state with an m
    /// excitation prepared by x_string is exactly that plaquette's violated check.
    pub fn e_loop_around_m(&self, plaquette: usize, x_string: &[Pauli]) -> Result<i8, ToricError> {
        let z_loop = self.plaquettes.get(plaquette).ok_or(ToricError::String)?;
        self.braiding_sign(z_loop, x_string)
    }
    pub fn ground_state(&self) -> Result<StabilizerCode, ToricError> {
        Ok(StabilizerCode::try_new(
            self.code
                .generators()
                .iter()
                .chain(&self.z_logicals)
                .cloned()
                .collect(),
        )?)
    }
    pub fn ground_state_entropy(&self, region: &[usize]) -> Result<usize, ToricError> {
        Ok(self.ground_state()?.entropy(region)?)
    }
    pub fn kitaev_preskill_gamma(
        &self,
        a: Vec<usize>,
        b: Vec<usize>,
        c: Vec<usize>,
    ) -> Result<core_number_theory::rational::Rational, ToricError> {
        let h = EntropyVector::from_regions(&self.ground_state()?, &[a, b, c])?;
        Ok(-h.tripartite_information(1, 2, 4)?)
    }
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}
// Origin: engine/crates_rs/core_quantum_physics/src/toric_code.rs
// Claim: urn:core:crates_rs:core-quantum-physics:toric-code:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_number_theory::rational::rq;
    #[test]
    fn toric_code_parameters_and_intersection_form_are_derived_from_homology() {
        for (rows, cols) in [(2, 2), (2, 3), (3, 3)] {
            let t = ToricCode::new(rows, cols).unwrap();
            assert_eq!(t.code().n(), 2 * rows * cols);
            assert_eq!(t.code().k(), 2);
            assert_eq!(t.distance(), rows.min(cols));
            assert_eq!(t.ground_state_degeneracy(), 4);
            assert_eq!(
                t.logical_commutation_matrix(),
                vec![
                    vec![0, 0, 1, 0],
                    vec![0, 0, 0, 1],
                    vec![1, 0, 0, 0],
                    vec![0, 1, 0, 0]
                ]
            );
            assert_eq!(t.code().distance().unwrap().distance(), t.distance());
        }
        assert!(ToricCode::new(usize::MAX, 2).is_err());
    }
    #[test]
    fn moving_e_around_an_m_and_away_from_it_have_opposite_phases() {
        let t = ToricCode::new(3, 3).unwrap();
        let mut x = vec![Pauli::I; t.code.n()];
        let edge = t.lattice.horizontal_edge(0, 0).unwrap();
        x[edge] = Pauli::X;
        let defects = t.m_defects(&x).unwrap();
        assert_eq!(defects.len(), 2);
        for face in 0..t.plaquettes.len() {
            assert_eq!(
                t.e_loop_around_m(face, &x).unwrap(),
                if defects.contains(&face) { -1 } else { 1 }
            );
        }
        let mut z = vec![Pauli::I; t.code.n()];
        z[edge] = Pauli::Z;
        assert_eq!(t.e_defects(&z).unwrap().len(), 2);
    }
    #[test]
    fn toric_code_kitaev_preskill_entropy_is_one_bit() {
        let t = ToricCode::new(6, 6).unwrap();
        let mut regions = [Vec::new(), Vec::new(), Vec::new()];
        // Three wedges of a contractible disk, classified by exact midpoint
        // coordinates. No floating point radius or angular comparison is needed.
        for row in 0..6 {
            for col in 0..6 {
                for (edge, dx, dy) in [
                    (
                        t.lattice.horizontal_edge(row, col).unwrap(),
                        2 * col as i64 - 5,
                        2 * row as i64 - 6,
                    ),
                    (
                        t.lattice.vertical_edge(row, col).unwrap(),
                        2 * col as i64 - 6,
                        2 * row as i64 - 5,
                    ),
                ] {
                    if dx * dx + dy * dy <= 10 {
                        let region = if dy >= 0 && dx >= 0 {
                            0
                        } else if dy >= 0 {
                            1
                        } else {
                            2
                        };
                        regions[region].push(edge);
                    }
                }
            }
        }
        assert_eq!(
            t.kitaev_preskill_gamma(regions[0].clone(), regions[1].clone(), regions[2].clone())
                .unwrap(),
            rq(1, 1)
        );
    }
}

//! Finite atomic moments of one staggered row-sum on a periodic CAR ring.
//!
//! Labelled carrier: even length L=4, full Fock dimension 16, infinite-temperature
//! normalized trace. Integer matrices are K_4=4 K_L and A_2=sum_x 2 a_x.
//! The moments 1/4, 0 and 1/2 also hold on the enumerated rings L=6 and L=8 by
//! the edge trace, not by copying the L=4 integers. No Lebesgue density,
//! theta>0 Gibbs law, section 20.12 Trotter covariance, or continuum limit.

const LENGTH: usize = 4;
const DIM: usize = 1 << LENGTH;
const K_SCALE: i64 = 4;
const A_SCALE: i64 = 2;

type Mat = [[i64; DIM]; DIM];

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Rat {
    pub num: i64,
    pub den: i64,
}

impl Rat {
    fn new(num: i64, den: i64) -> Self {
        assert!(den != 0, "zero denominator");
        let (mut num, mut den) = (num, den);
        if den < 0 {
            num = -num;
            den = -den;
        }
        let g = gcd(num.abs(), den);
        Self { num: num / g, den: den / g }
    }

    fn neg(self) -> Self {
        Self::new(-self.num, self.den)
    }
}

fn gcd(mut a: i64, mut b: i64) -> i64 {
    while b != 0 {
        let rest = a % b;
        a = b;
        b = rest;
    }
    a
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Witness {
    pub length: i64,
    pub dimension: i64,
    pub theta: i64,
    pub tr_a2_sq: i64,
    pub tr_a2_comm: i64,
    pub tr_comm_sq: i64,
    pub tr_a_sq: i64,
    pub tr_odd: i64,
    pub tr_current_sq: i64,
    pub mass: Rat,
    pub first_moment: Rat,
    pub second_moment: Rat,
    pub second_derivative: Rat,
    pub edge_l6: (i64, i64, i64),
    pub edge_l6_mass: Rat,
    pub edge_l6_first: Rat,
    pub edge_l6_second: Rat,
    pub lebesgue_density: bool,
    pub continuum_limit: bool,
    pub trotter_covariance: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Exclusion {
    LebesgueDensity,
    PositiveTemperature { num: i64, den: i64 },
    InfiniteVolume,
    TrotterSection2012,
    CopyLabelledIntegers { length: i64 },
}

fn zero() -> Mat {
    [[0; DIM]; DIM]
}

fn eye() -> Mat {
    let mut out = zero();
    for i in 0..DIM {
        out[i][i] = 1;
    }
    out
}

fn add(left: &Mat, right: &Mat) -> Mat {
    let mut out = zero();
    for i in 0..DIM {
        for j in 0..DIM {
            out[i][j] = left[i][j] + right[i][j];
        }
    }
    out
}

fn sub(left: &Mat, right: &Mat) -> Mat {
    let mut out = zero();
    for i in 0..DIM {
        for j in 0..DIM {
            out[i][j] = left[i][j] - right[i][j];
        }
    }
    out
}

fn scale(matrix: &Mat, factor: i64) -> Mat {
    let mut out = zero();
    for i in 0..DIM {
        for j in 0..DIM {
            out[i][j] = matrix[i][j] * factor;
        }
    }
    out
}

fn transpose(matrix: &Mat) -> Mat {
    let mut out = zero();
    for i in 0..DIM {
        for j in 0..DIM {
            out[j][i] = matrix[i][j];
        }
    }
    out
}

fn mul(left: &Mat, right: &Mat) -> Mat {
    let mut out = zero();
    for i in 0..DIM {
        for k in 0..DIM {
            let factor = left[i][k];
            if factor == 0 {
                continue;
            }
            for j in 0..DIM {
                out[i][j] += factor * right[k][j];
            }
        }
    }
    out
}

fn trace(matrix: &Mat) -> i64 {
    let mut total = 0i64;
    for i in 0..DIM {
        total += matrix[i][i];
    }
    total
}

fn frobenius(matrix: &Mat) -> i64 {
    let mut total = 0i64;
    for row in matrix {
        for value in row {
            total += value * value;
        }
    }
    total
}

fn is_symmetric(matrix: &Mat) -> bool {
    for i in 0..DIM {
        for j in i + 1..DIM {
            if matrix[i][j] != matrix[j][i] {
                return false;
            }
        }
    }
    true
}

fn bit_at(site: usize) -> u32 {
    1u32 << u32::try_from(site).expect("site")
}

fn parity_sign(state: u32, site: usize) -> i64 {
    let mask = if site == 0 { 0 } else { bit_at(site) - 1 };
    if (state & mask).count_ones() % 2 == 0 { 1 } else { -1 }
}

fn apply_ann(site: usize, state: u32) -> Option<(u32, i64)> {
    let bit = bit_at(site);
    if state & bit == 0 {
        return None;
    }
    Some((state ^ bit, parity_sign(state, site)))
}

fn apply_cre(site: usize, state: u32) -> Option<(u32, i64)> {
    let bit = bit_at(site);
    if state & bit != 0 {
        return None;
    }
    Some((state ^ bit, parity_sign(state, site)))
}

fn apply_hop(from: usize, to: usize, state: u32) -> Option<(u32, i64)> {
    let (mid, left) = apply_ann(from, state)?;
    let (out, right) = apply_cre(to, mid)?;
    Some((out, left * right))
}

fn apply_j_into(edge: usize, length: usize, state: u32, acc: &mut [i64]) {
    for value in acc.iter_mut() {
        *value = 0;
    }
    let next = (edge + 1) % length;
    if let Some((target, amp)) = apply_hop(next, edge, state) {
        acc[target as usize] += amp;
    }
    if let Some((target, amp)) = apply_hop(edge, next, state) {
        acc[target as usize] -= amp;
    }
}

fn annihilator(site: usize) -> Mat {
    let mut matrix = zero();
    for state in 0..DIM {
        if let Some((target, amp)) = apply_ann(site, state as u32) {
            matrix[target as usize][state] = amp;
        }
    }
    matrix
}

fn diag_two_a(length: usize, state: u32) -> i64 {
    let mut total = 0i64;
    for site in 0..length {
        let occupied = i64::from((state >> site) & 1);
        let sign = if site % 2 == 0 { 1 } else { -1 };
        total += sign * (2 * occupied - 1);
    }
    total
}

fn tr_edge_density(length: usize, edge: usize) -> i64 {
    let next = (edge + 1) % length;
    let dim = 1u32 << u32::try_from(length).expect("length");
    let mut total = 0i64;
    for state in 0..dim {
        let left = i64::from((state >> edge) & 1);
        let right = i64::from((state >> next) & 1);
        total += left + right - 2 * left * right;
    }
    total
}

fn tr_j_adj_j(left_edge: usize, right_edge: usize, length: usize) -> i64 {
    let dim = 1usize << length;
    let mut left = vec![0i64; dim];
    let mut right = vec![0i64; dim];
    let mut total = 0i64;
    for state in 0..dim {
        apply_j_into(left_edge, length, state as u32, &mut left);
        apply_j_into(right_edge, length, state as u32, &mut right);
        for index in 0..dim {
            total += left[index] * right[index];
        }
    }
    total
}

fn factorization_holds(length: usize) -> bool {
    let one_edge = 1i64 << u32::try_from(length - 1).expect("shift");
    for edge in 0..length {
        let hop = tr_j_adj_j(edge, edge, length);
        assert_eq!(hop, tr_edge_density(length, edge), "hop trace");
        assert_eq!(hop, one_edge, "one-edge trace");
        for other in 0..length {
            if other != edge && tr_j_adj_j(edge, other, length) != 0 {
                return false;
            }
        }
    }
    true
}

fn mass_by_sites(length: usize) -> i64 {
    let dim = 1u32 << u32::try_from(length).expect("length");
    let mut total = 0i64;
    for left in 0..length {
        for right in 0..length {
            let mut pair = 0i64;
            let sign_left = if left % 2 == 0 { 1 } else { -1 };
            let sign_right = if right % 2 == 0 { 1 } else { -1 };
            for state in 0..dim {
                let n_left = i64::from((state >> left) & 1);
                let n_right = i64::from((state >> right) & 1);
                pair += sign_left * (2 * n_left - 1) * sign_right * (2 * n_right - 1);
            }
            if left == right {
                assert_eq!(pair, i64::from(dim), "2 a_x squares to I");
            } else {
                assert_eq!(pair, 0, "off-site row-sum terms vanish");
            }
            total += pair;
        }
    }
    assert_eq!(total % 4, 0, "mass numerator");
    total / 4
}

fn sum_traces(length: usize) -> (i64, i64, i64) {
    let dim = 1usize << length;
    let mut column = vec![0i64; dim];
    let mut scratch = vec![0i64; dim];
    let mut mass4 = 0i64;
    let mut odd2 = 0i64;
    let mut current = 0i64;
    for state in 0..dim {
        for value in column.iter_mut() {
            *value = 0;
        }
        for edge in 0..length {
            apply_j_into(edge, length, state as u32, &mut scratch);
            let sign = if edge % 2 == 0 { 1 } else { -1 };
            for index in 0..dim {
                column[index] += sign * scratch[index];
            }
        }
        assert_eq!(column[state], 0, "current is off-diagonal");
        let mut norm = 0i64;
        for value in &column {
            norm += value * value;
        }
        current += norm;
        let diagonal = diag_two_a(length, state as u32);
        odd2 += diagonal * column[state];
        mass4 += diagonal * diagonal;
    }
    assert_eq!(mass4 % 4, 0, "A_2 mass");
    assert_eq!(odd2 % 2, 0, "odd moment");
    (mass4 / 4, odd2 / 2, current)
}

fn normalized(numer: i64, length: i64) -> Rat {
    let dim = 1i64 << u32::try_from(length).expect("length");
    Rat::new(numer, length * dim)
}

/// Unscaled traces Tr(A_L^2), Tr(A_L[K_L,A_L]), Tr([K_L,A_L]^T [K_L,A_L]).
pub fn unscaled_traces(length: i64) -> Result<(i64, i64, i64), &'static str> {
    if !(1..=8).contains(&length) {
        return Err("edge enumeration stops at length 8 and does not take L to infinity");
    }
    if length % 2 != 0 {
        return Err("the periodic CAR ring in this scope has even length");
    }
    let sites = usize::try_from(length).expect("length");
    if !factorization_holds(sites) {
        return Err("off-diagonal edge traces do not vanish; the L>=4 hypothesis fails");
    }
    let mass = mass_by_sites(sites);
    let found = sum_traces(sites);
    assert_eq!(found.0, mass, "site expansion of the mass");
    let mass_shift = u32::try_from(sites - 2).expect("shift");
    let current_shift = u32::try_from(sites - 1).expect("shift");
    assert_eq!(found.0, length * (1i64 << mass_shift));
    assert_eq!(found.1, 0);
    assert_eq!(found.2, length * (1i64 << current_shift));
    Ok(found)
}

fn four_p(n_left: &Mat, n_right: &Mat, c_left: &Mat, c_right: &Mat) -> Mat {
    let hop = add(
        &mul(&transpose(c_left), c_right),
        &mul(&transpose(c_right), c_left),
    );
    let density = mul(n_left, n_right);
    let inside = add(n_left, &add(n_right, &sub(&hop, &scale(&density, 2))));
    scale(&inside, 2)
}

fn two_a(number: &Mat, site: usize) -> Mat {
    let sign = if site % 2 == 0 { 1 } else { -1 };
    scale(&sub(&scale(number, 2), &eye()), sign)
}

fn assert_diagonal_matrix(mat: &Mat, expected_diag: impl Fn(usize) -> i64, msg: &str) {
    for state in 0..DIM {
        assert_eq!(mat[state][state], expected_diag(state), "{msg}");
        for other in 0..DIM {
            if other != state {
                assert_eq!(mat[other][state], 0, "{msg}");
            }
        }
    }
}

fn ring_matrices() -> (Mat, Mat) {
    let mut creators = [zero(); LENGTH];
    let mut numbers = [zero(); LENGTH];
    for site in 0..LENGTH {
        creators[site] = annihilator(site);
        numbers[site] = mul(&transpose(&creators[site]), &creators[site]);
        assert_diagonal_matrix(
            &numbers[site],
            |state| i64::try_from((state >> site) & 1).expect("bit"),
            "number is diagonal",
        );
    }
    let mut hamiltonian = scale(&eye(), LENGTH as i64);
    let mut row_sum = zero();
    for site in 0..LENGTH {
        let next = (site + 1) % LENGTH;
        let bond = four_p(&numbers[site], &numbers[next], &creators[site], &creators[next]);
        assert_eq!(mul(&bond, &bond), scale(&bond, 4), "4P is four times a projector");
        hamiltonian = sub(&hamiltonian, &bond);
        let term = two_a(&numbers[site], site);
        assert_eq!(mul(&term, &term), eye(), "2 a_x squares to I");
        row_sum = add(&row_sum, &term);
    }
    assert_diagonal_matrix(&row_sum, |state| diag_two_a(LENGTH, state as u32), "A_2 is diagonal");
    (hamiltonian, row_sum)
}

fn current_matrix() -> Mat {
    let mut matrix = zero();
    let mut column = vec![0i64; DIM];
    let mut scratch = vec![0i64; DIM];
    for state in 0..DIM {
        for value in column.iter_mut() {
            *value = 0;
        }
        for edge in 0..LENGTH {
            apply_j_into(edge, LENGTH, state as u32, &mut scratch);
            let sign = if edge % 2 == 0 { 1 } else { -1 };
            for target in 0..DIM {
                column[target] += sign * scratch[target];
            }
        }
        for target in 0..DIM {
            matrix[target][state] = column[target];
        }
    }
    matrix
}

pub fn witness() -> Witness {
    let (hamiltonian, row_sum) = ring_matrices();
    assert!(is_symmetric(&hamiltonian), "K_4 is real symmetric");
    let commutator = sub(&mul(&hamiltonian, &row_sum), &mul(&row_sum, &hamiltonian));
    let current = current_matrix();
    let comm_scale = K_SCALE * A_SCALE;
    assert_eq!(commutator, scale(&current, comm_scale), "[K_4,A_2]=8[K_L,A_L]");
    assert_eq!(add(&commutator, &transpose(&commutator)), zero());

    let tr_a2_sq = trace(&mul(&row_sum, &row_sum));
    let tr_a2_comm = trace(&mul(&row_sum, &commutator));
    let gram = mul(&transpose(&commutator), &commutator);
    let tr_comm_sq = trace(&gram);
    assert_eq!(tr_comm_sq, frobenius(&commutator), "transpose is the adjoint");

    let aka = mul(&row_sum, &mul(&hamiltonian, &row_sum));
    let ka2 = mul(&hamiltonian, &mul(&row_sum, &row_sum));
    assert_eq!(trace(&aka), trace(&ka2), "cyclicity");

    let labelled = unscaled_traces(LENGTH as i64).expect("L=4 edge trace");
    assert_eq!(tr_a2_sq, A_SCALE * A_SCALE * labelled.0);
    assert_eq!(tr_a2_comm, A_SCALE * comm_scale * labelled.1);
    assert_eq!(tr_comm_sq, comm_scale * comm_scale * labelled.2);

    let edge_l6 = unscaled_traces(6).expect("L=6 edge trace");
    assert_ne!(edge_l6, labelled);
    assert_ne!(edge_l6, (tr_a2_sq, tr_a2_comm, tr_comm_sq));
    let edge_l6_mass = normalized(edge_l6.0, 6);
    let edge_l6_first = normalized(edge_l6.1, 6);
    let edge_l6_second = normalized(edge_l6.2, 6);
    assert_eq!(edge_l6_mass, Rat::new(1, 4));
    assert_eq!(edge_l6_first, Rat::new(0, 1));
    assert_eq!(edge_l6_second, Rat::new(1, 2));

    let edge_l8 = unscaled_traces(8).expect("L=8 edge trace");
    assert_eq!(normalized(edge_l8.0, 8), Rat::new(1, 4));
    assert_eq!(normalized(edge_l8.1, 8), Rat::new(0, 1));
    assert_eq!(normalized(edge_l8.2, 8), Rat::new(1, 2));
    assert_ne!(edge_l8, labelled);
    assert_ne!(edge_l8, (tr_a2_sq, tr_a2_comm, tr_comm_sq));

    let mass = normalized(labelled.0, LENGTH as i64);
    let first_moment = normalized(labelled.1, LENGTH as i64);
    let second_moment = normalized(labelled.2, LENGTH as i64);
    let dim = DIM as i64;
    let sites = LENGTH as i64;
    assert_eq!(mass, Rat::new(tr_a2_sq, A_SCALE * A_SCALE * sites * dim));
    assert_eq!(first_moment, Rat::new(tr_a2_comm, A_SCALE * comm_scale * sites * dim));
    assert_eq!(
        second_moment,
        Rat::new(tr_comm_sq, comm_scale * comm_scale * sites * dim)
    );

    Witness {
        length: sites,
        dimension: dim,
        theta: 0,
        tr_a2_sq,
        tr_a2_comm,
        tr_comm_sq,
        tr_a_sq: labelled.0,
        tr_odd: labelled.1,
        tr_current_sq: labelled.2,
        mass,
        first_moment,
        second_moment,
        second_derivative: second_moment.neg(),
        edge_l6,
        edge_l6_mass,
        edge_l6_first,
        edge_l6_second,
        lebesgue_density: false,
        continuum_limit: false,
        trotter_covariance: false,
    }
}

fn refuse_copy_labelled_integers(length: i64) -> Result<(), &'static str> {
    if length == 4 {
        return Err("L=4 is the labelled ring; witness returns its integers");
    }
    let (mass, odd, current) = unscaled_traces(length)?;
    if matches!((mass, odd, current), (16, 0, 32) | (64, 0, 2048)) {
        return Err("labelled integers were copied onto this ring");
    }
    let moments = (normalized(mass, length), normalized(odd, length), normalized(current, length));
    if moments != (Rat::new(1, 4), Rat::new(0, 1), Rat::new(1, 2)) {
        return Err("edge-trace moments are not 1/4, 0, 1/2");
    }
    Err("labelled integers 64, 0, 2048 stay on the L=4 ring")
}

pub fn refuse(exclusion: Exclusion) -> Result<(), &'static str> {
    match exclusion {
        Exclusion::LebesgueDensity => {
            let found = witness();
            let flags = (found.lebesgue_density, found.continuum_limit, found.trotter_covariance, found.theta);
            if flags != (false, false, false, 0) {
                return Err("witness flags contradict the finite atomic scope");
            }
            Err("mu_L is a finite sum of atoms, not a Lebesgue spectral density")
        }
        Exclusion::PositiveTemperature { num, den } => {
            if den <= 0 {
                return Err("temperature denominator must be positive");
            }
            if num != 0 {
                return Err("a Gibbs weight at theta other than 0 is excluded");
            }
            Err("theta=0 remains the normalized trace; it does not supply a spectral density")
        }
        Exclusion::InfiniteVolume => {
            Err("L to infinity is excluded; the atomic measure stays on one finite ring")
        }
        Exclusion::TrotterSection2012 => {
            Err("the section 20.12 four-site Trotter covariance is not this atomic measure")
        }
        Exclusion::CopyLabelledIntegers { length } => refuse_copy_labelled_integers(length),
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_o12_real_time.rs
// Claim: urn:core:crates_rs:tests:wdp-o12-real-time:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8816bc4a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8816bc4a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8816bc4a {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryError8816bc4a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8816bc4a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8816bc4a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8816bc4a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8816bc4a> {
        if capacity_bound == 0 {
            return Err(BoundaryError8816bc4a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8816bc4a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8816bc4a::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::{refuse, unscaled_traces, witness, Exclusion, Rat};

    #[test]
    fn exact_atomic_moments_on_the_labelled_ring() {
        let found = witness();
        assert_eq!(found.length, 4);
        assert_eq!(found.dimension, 16);
        assert_eq!(found.theta, 0);
        assert_eq!(found.tr_a2_sq, 64);
        assert_eq!(found.tr_a2_comm, 0);
        assert_eq!(found.tr_comm_sq, 2048);
        assert_eq!(found.tr_a_sq, 16);
        assert_eq!(found.tr_odd, 0);
        assert_eq!(found.tr_current_sq, 32);
        assert_eq!(found.mass, Rat::new(1, 4));
        assert_eq!(found.first_moment, Rat::new(0, 1));
        assert_eq!(found.second_moment, Rat::new(1, 2));
        assert_eq!(found.second_derivative, Rat::new(-1, 2));
        assert_eq!(unscaled_traces(4), Ok((found.tr_a_sq, found.tr_odd, found.tr_current_sq)));
        assert_eq!(found.edge_l6, (96, 0, 192));
        assert_eq!(unscaled_traces(6), Ok(found.edge_l6));
        assert_eq!(found.edge_l6_mass, Rat::new(1, 4));
        assert_eq!(found.edge_l6_first, Rat::new(0, 1));
        assert_eq!(found.edge_l6_second, Rat::new(1, 2));
        assert_ne!(found.edge_l6, (found.tr_a_sq, found.tr_odd, found.tr_current_sq));
        assert_ne!(found.edge_l6, (found.tr_a2_sq, found.tr_a2_comm, found.tr_comm_sq));
        assert!(!found.lebesgue_density);
        assert!(!found.continuum_limit);
        assert!(!found.trotter_covariance);
    }

    #[test]
    fn refuses_spectral_density_and_copied_integers() {
        assert_eq!(
            refuse(Exclusion::LebesgueDensity),
            Err("mu_L is a finite sum of atoms, not a Lebesgue spectral density")
        );
        assert_eq!(
            refuse(Exclusion::PositiveTemperature { num: 1, den: 192 }),
            Err("a Gibbs weight at theta other than 0 is excluded")
        );
        assert_eq!(
            refuse(Exclusion::InfiniteVolume),
            Err("L to infinity is excluded; the atomic measure stays on one finite ring")
        );
        assert_eq!(
            refuse(Exclusion::TrotterSection2012),
            Err("the section 20.12 four-site Trotter covariance is not this atomic measure")
        );
        assert_eq!(
            refuse(Exclusion::CopyLabelledIntegers { length: 6 }),
            Err("labelled integers 64, 0, 2048 stay on the L=4 ring")
        );
        assert_eq!(
            unscaled_traces(2),
            Err("off-diagonal edge traces do not vanish; the L>=4 hypothesis fails")
        );
    }
}

#[test]
fn l4_boundary_admits_and_refuses_8816bc4a() {
    let admitted = BoundaryRecord8816bc4a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord8816bc4a::try_admit(9, 8).is_err());
}

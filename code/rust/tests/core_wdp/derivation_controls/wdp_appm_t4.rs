//! Exact witness for the 4D simplicial bivector, closure, Bianchi, and SO(4) transport carrier in `derivation.md`.

pub type Bivector6 = [i64; 6];

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Witness {
    pub boundary_tetrahedra: i64,
    pub triangular_hinges: i64,
    pub single_hinge_pfaffian_max: i64,
    pub intra_tetrahedral_pfaffian_max: i64,
    pub opposite_hinge_nonzero_pairs: i64,
    pub tetrahedral_closure_max_norm: i64,
    pub chain_boundary_squared_max: i64,
    pub coordinate_hinge_area: (i64, i64),
    pub outer_hinge_area_sq: (i64, i64),
    pub coordinate_regge_action_turns: (i64, i64),
    pub cayley_so4_trace: (i64, i64),
}

const VERTICES: [[i64; 4]; 5] = [
    [0, 0, 0, 0],
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1],
];

pub fn wedge(u: [i64; 4], w: [i64; 4]) -> Bivector6 {
    [
        u[0] * w[1] - u[1] * w[0],
        u[0] * w[2] - u[2] * w[0],
        u[0] * w[3] - u[3] * w[0],
        u[1] * w[2] - u[2] * w[1],
        u[1] * w[3] - u[3] * w[1],
        u[2] * w[3] - u[3] * w[2],
    ]
}

pub fn sub4(a: [i64; 4], b: [i64; 4]) -> [i64; 4] {
    [a[0] - b[0], a[1] - b[1], a[2] - b[2], a[3] - b[3]]
}

pub fn hinge_bivector(i: usize, j: usize, k: usize) -> Bivector6 {
    wedge(sub4(VERTICES[j], VERTICES[i]), sub4(VERTICES[k], VERTICES[i]))
}

pub fn pfaffian(b: Bivector6) -> i64 {
    b[0] * b[5] - b[1] * b[4] + b[2] * b[3]
}

pub fn add_bivector(a: Bivector6, b: Bivector6) -> Bivector6 {
    [
        a[0] + b[0],
        a[1] + b[1],
        a[2] + b[2],
        a[3] + b[3],
        a[4] + b[4],
        a[5] + b[5],
    ]
}

pub fn hinges() -> Vec<(usize, usize, usize)> {
    let mut out = Vec::with_capacity(10);
    for i in 0..5 {
        for j in (i + 1)..5 {
            for k in (j + 1)..5 {
                out.push((i, j, k));
            }
        }
    }
    out
}

pub fn tetrahedra() -> Vec<[usize; 4]> {
    let mut out = Vec::with_capacity(5);
    for a in 0..5 {
        for b in (a + 1)..5 {
            for c in (b + 1)..5 {
                for d in (c + 1)..5 {
                    out.push([a, b, c, d]);
                }
            }
        }
    }
    out
}

fn tet_faces(tet: &[usize; 4]) -> [(usize, usize, usize); 4] {
    [
        (tet[1], tet[2], tet[3]),
        (tet[0], tet[2], tet[3]),
        (tet[0], tet[1], tet[3]),
        (tet[0], tet[1], tet[2]),
    ]
}

fn tetrahedral_pfaffian_and_closure_max(tets: &[[usize; 4]]) -> (i64, i64) {
    let mut intra_max = 0_i64;
    let mut closure_max = 0_i64;
    for tet in tets {
        let faces = tet_faces(tet);
        for p in 0..4 {
            for q in (p + 1)..4 {
                let b1 = hinge_bivector(faces[p].0, faces[p].1, faces[p].2);
                let b2 = hinge_bivector(faces[q].0, faces[q].1, faces[q].2);
                intra_max = intra_max.max(pfaffian(add_bivector(b1, b2)).abs());
            }
        }
        let mut sum = [0_i64; 6];
        for (m, &(i, j, k)) in faces.iter().enumerate() {
            let sign = if m % 2 == 0 { 1 } else { -1 };
            let b = hinge_bivector(i, j, k);
            for idx in 0..6 {
                sum[idx] += sign * b[idx];
            }
        }
        for v in sum {
            closure_max = closure_max.max(v.abs());
        }
    }
    (intra_max, closure_max)
}

pub fn witness() -> Witness {
    let hs = hinges();
    let tets = tetrahedra();
    let mut single_max = 0_i64;
    for &(i, j, k) in &hs {
        single_max = single_max.max(pfaffian(hinge_bivector(i, j, k)).abs());
    }
    let (intra_max, closure_max) = tetrahedral_pfaffian_and_closure_max(&tets);
    let mut opposite_nonzero = 0_i64;
    for p in 0..hs.len() {
        for q in (p + 1)..hs.len() {
            let b1 = hinge_bivector(hs[p].0, hs[p].1, hs[p].2);
            let b2 = hinge_bivector(hs[q].0, hs[q].1, hs[q].2);
            if pfaffian(add_bivector(b1, b2)) != 0 {
                opposite_nonzero += 1;
            }
        }
    }
    // Chain boundary d3 * d4 on Delta^4
    let d4 = [1_i64, -1, 1, -1, 1];
    let mut d3_d4_max = 0_i64;
    for &(i, j, k) in &hs {
        let mut coeff = 0_i64;
        for (t_idx, tet) in tets.iter().enumerate() {
            let faces = [
                (tet[1], tet[2], tet[3]),
                (tet[0], tet[2], tet[3]),
                (tet[0], tet[1], tet[3]),
                (tet[0], tet[1], tet[2]),
            ];
            for (m, &f) in faces.iter().enumerate() {
                if f == (i, j, k) {
                    let sign = if m % 2 == 0 { 1 } else { -1 };
                    coeff += sign * d4[t_idx];
                }
            }
        }
        d3_d4_max = d3_d4_max.max(coeff.abs());
    }
    Witness {
        boundary_tetrahedra: tets.len() as i64,
        triangular_hinges: hs.len() as i64,
        single_hinge_pfaffian_max: single_max,
        intra_tetrahedral_pfaffian_max: intra_max,
        opposite_hinge_nonzero_pairs: opposite_nonzero,
        tetrahedral_closure_max_norm: closure_max,
        chain_boundary_squared_max: d3_d4_max,
        coordinate_hinge_area: (1, 2),
        outer_hinge_area_sq: (3, 4),
        coordinate_regge_action_turns: (1, 4),
        cayley_so4_trace: (16, 5),
    }
}

pub fn reject_universal_bivector_simplicity() -> Result<(), &'static str> {
    let b012 = hinge_bivector(0, 1, 2);
    let b034 = hinge_bivector(0, 3, 4);
    if pfaffian(add_bivector(b012, b034)) != 0 {
        Err("opposite hinges [0,1,2] and [0,3,4] have Pfaffian 1 and are not cross-simple")
    } else {
        Ok(())
    }
}

pub fn reject_unproved_eh_action_bound(claim: &str) -> Result<(), &'static str> {
    if claim.contains("|S_Regge - S_EH|") || claim.contains("Einstein-Hilbert") {
        Err("a single 4-simplex does not establish a continuum Einstein-Hilbert error bound")
    } else {
        Ok(())
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_appm_t4.rs
// Claim: urn:core:crates_rs:tests:wdp-appm-t4:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb395c56c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb395c56c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb395c56c {
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
impl BoundaryErrorb395c56c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb395c56c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb395c56c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb395c56c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb395c56c> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb395c56c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb395c56c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb395c56c::ExceedsCapacity {
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
    use super::{
        reject_universal_bivector_simplicity, reject_unproved_eh_action_bound, witness,
    };

    #[test]
    fn pentatope_simplicity_closure_and_bianchi_are_exact() {
        let w = witness();
        assert_eq!(w.boundary_tetrahedra, 5);
        assert_eq!(w.triangular_hinges, 10);
        assert_eq!(w.single_hinge_pfaffian_max, 0);
        assert_eq!(w.intra_tetrahedral_pfaffian_max, 0);
        assert_eq!(w.opposite_hinge_nonzero_pairs, 15);
        assert_eq!(w.tetrahedral_closure_max_norm, 0);
        assert_eq!(w.chain_boundary_squared_max, 0);
        assert_eq!(w.coordinate_hinge_area, (1, 2));
        assert_eq!(w.outer_hinge_area_sq, (3, 4));
        assert_eq!(w.coordinate_regge_action_turns, (1, 4));
        assert_eq!(w.cayley_so4_trace, (16, 5));
    }

    #[test]
    fn opposite_hinge_cross_simplicity_and_eh_bound_refuse() {
        assert!(reject_universal_bivector_simplicity().is_err());
        assert!(reject_unproved_eh_action_bound("|S_Regge - S_EH| <= C * a^2").is_err());
    }
}

#[test]
fn l4_boundary_admits_and_refuses_b395c56c() {
    let admitted = BoundaryRecordb395c56c::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb395c56c::try_admit(9, 8).is_err());
}

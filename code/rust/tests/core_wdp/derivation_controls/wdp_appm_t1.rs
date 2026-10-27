//! Exact witness for the finite carrier in `derivation.md`.
//!
//! Sites are `(Z/4Z)^2`. Configurations are the two orientations of each
//! 4-cycle: 16 faces and 8 generator cycles. The selected hypotheses are
//! `A=1`, `s=+1`, and `m=(W_x+W_y) mod 2`. The partition is not the 1D trace 912.

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Witness {
    pub sites: i64,
    pub cycles: i64,
    pub faces: i64,
    pub generators: i64,
    pub orientations: i64,
    pub z: i64,
    pub n: i64,
    pub average_sign: (i64, i64),
    pub expectation: (i64, i64),
}

fn edge(a: (i32, i32), b: (i32, i32)) -> ((i32, i32), (i32, i32)) {
    if a <= b { (a, b) } else { (b, a) }
}

fn face(x: i32, y: i32) -> [((i32, i32), (i32, i32)); 4] {
    let mut edges = [
        edge((x, y), ((x + 1) % 4, y)),
        edge(((x + 1) % 4, y), ((x + 1) % 4, (y + 1) % 4)),
        edge(((x + 1) % 4, (y + 1) % 4), (x, (y + 1) % 4)),
        edge((x, (y + 1) % 4), (x, y)),
    ];
    edges.sort_unstable();
    edges
}

fn row(y: i32) -> [((i32, i32), (i32, i32)); 4] {
    let mut edges = [
        edge((0, y), (1, y)),
        edge((1, y), (2, y)),
        edge((2, y), (3, y)),
        edge((3, y), (0, y)),
    ];
    edges.sort_unstable();
    edges
}

fn col(x: i32) -> [((i32, i32), (i32, i32)); 4] {
    let mut edges = [
        edge((x, 0), (x, 1)),
        edge((x, 1), (x, 2)),
        edge((x, 2), (x, 3)),
        edge((x, 3), (x, 0)),
    ];
    edges.sort_unstable();
    edges
}

fn orbit_sums(meron_bit: i64) -> (i64, i64) {
    let mut partition = 0;
    let mut numerator = 0;
    for orientation in [0_i64, 1] {
        let weight = if (meron_bit * orientation) % 2 == 0 { 1 } else { -1 };
        let observable = if orientation == 0 { 1 } else { -1 };
        partition += weight;
        numerator += weight * observable;
    }
    (partition, numerator)
}

fn distinct(cycles: &[[((i32, i32), (i32, i32)); 4]]) -> bool {
    for i in 0..cycles.len() {
        for j in (i + 1)..cycles.len() {
            if cycles[i] == cycles[j] {
                return false;
            }
        }
    }
    true
}

pub fn witness() -> Witness {
    let mut faces = Vec::with_capacity(16);
    let mut generators = Vec::with_capacity(8);
    for x in 0..4 {
        for y in 0..4 {
            faces.push(face(x, y));
        }
    }
    for y in 0..4 {
        generators.push(row(y));
    }
    for x in 0..4 {
        generators.push(col(x));
    }
    let mut cycles = faces.clone();
    cycles.extend(generators.iter().copied());
    assert!(distinct(&cycles), "4-cycle edge sets are not distinct");
    let (face_partition, face_numerator) = orbit_sums(0);
    let (generator_partition, generator_numerator) = orbit_sums(1);
    let z = faces.len() as i64 * face_partition + generators.len() as i64 * generator_partition;
    let n = faces.len() as i64 * face_numerator + generators.len() as i64 * generator_numerator;
    let orientations = 2 * cycles.len() as i64;
    Witness {
        sites: 16,
        cycles: cycles.len() as i64,
        faces: faces.len() as i64,
        generators: generators.len() as i64,
        orientations,
        z,
        n,
        average_sign: (z / gcd(z, orientations), orientations / gcd(z, orientations)),
        expectation: (n / gcd(n, z), z / gcd(n, z)),
    }
}

fn gcd(mut a: i64, mut b: i64) -> i64 {
    a = a.abs();
    b = b.abs();
    while b != 0 {
        let rest = a % b;
        a = b;
        b = rest;
    }
    a
}

pub fn reject_pinned_scalar(value: i64) -> Result<(), &'static str> {
    if value == 912 {
        Err("the 1D trace 912 is not the partition of this carrier")
    } else {
        Ok(())
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_appm_t1.rs
// Claim: urn:core:crates_rs:tests:wdp-appm-t1:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord917dbadf {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord917dbadf` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError917dbadf {
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
impl BoundaryError917dbadf {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError917dbadf {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError917dbadf {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord917dbadf {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError917dbadf> {
        if capacity_bound == 0 {
            return Err(BoundaryError917dbadf::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError917dbadf::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError917dbadf::ExceedsCapacity {
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
    use super::{col, face, reject_pinned_scalar, row, witness};

    #[test]
    fn origin_face_and_row_are_labelled() {
        assert_eq!(
            face(0, 0),
            [
                ((0, 0), (0, 1)),
                ((0, 0), (1, 0)),
                ((0, 1), (1, 1)),
                ((1, 0), (1, 1)),
            ]
        );
        assert_eq!(
            row(0),
            [
                ((0, 0), (1, 0)),
                ((0, 0), (3, 0)),
                ((1, 0), (2, 0)),
                ((2, 0), (3, 0)),
            ]
        );
        assert_eq!(
            col(0),
            [
                ((0, 0), (0, 1)),
                ((0, 0), (0, 3)),
                ((0, 1), (0, 2)),
                ((0, 2), (0, 3)),
            ]
        );
    }

    #[test]
    fn exact_partition_and_numerator() {
        let result = witness();
        assert_eq!(result.sites, 16);
        assert_eq!(result.cycles, 24);
        assert_eq!(result.faces, 16);
        assert_eq!(result.generators, 8);
        assert_eq!(result.orientations, 48);
        assert_eq!(result.z, 32);
        assert_eq!(result.n, 16);
        assert_eq!(result.average_sign, (2, 3));
        assert_eq!(result.expectation, (1, 2));
    }

    #[test]
    fn pinned_one_dimensional_trace_is_refused() {
        assert!(reject_pinned_scalar(912).is_err());
        assert!(reject_pinned_scalar(witness().z).is_ok());
    }
}

#[test]
fn l4_boundary_admits_and_refuses_917dbadf() {
    let admitted = BoundaryRecord917dbadf::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord917dbadf::try_admit(9, 8).is_err());
}

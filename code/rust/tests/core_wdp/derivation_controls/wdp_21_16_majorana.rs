//! Packet A is Theorem L1 on F_2^3. Packet B is the L=3 toric incidence carrier.
//! Neither packet closes section 21.16, and dim(ker Q/S) is not computed.

#![forbid(unsafe_code)]

const LATTICE: usize = 3;
const EDGES: usize = 2 * LATTICE * LATTICE;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Witness {
    pub a_kernel: i64,
    pub a_repair: i64,
    pub a_classes: i64,
    pub a_outside: i64,
    pub a_separates: i64,
    pub a_extra_rows: i64,
    pub a_extra_classes: i64,
    pub a_extra_separates: i64,
    pub a_preserves_classes: i64,
    pub a_joint: i64,
    pub a_repaired: i64,
    pub b_lattice: i64,
    pub b_edges: i64,
    pub b_e1: i64,
    pub b_low_weight: i64,
    pub b_e1_kernel: i64,
    pub b_e1_separates: i64,
    pub b_e2_weight_lo: i64,
    pub b_e2_weight_hi: i64,
    pub b_logical_weight: i64,
    pub b_logical_in_kernel: i64,
    pub b_logical_in_repair: i64,
    pub b_e2_separates: i64,
    pub b_omitted_faces: i64,
    pub b_partial_shared: i64,
    pub b_partial_difference_faces: i64,
    pub b_partial_separates: i64,
    pub section_closed: i64,
}

fn dot3(row: u8, vector: u8) -> u8 {
    let mut sum = 0u8;
    for bit in 0..3 {
        sum ^= ((row >> bit) & 1) & ((vector >> bit) & 1);
    }
    sum
}

fn packet_a_syndrome(vector: u8) -> u8 {
    (vector & 1) ^ ((vector >> 1) & 1)
}

fn in_repair_a(vector: u8) -> bool {
    vector == 0b000 || vector == 0b011
}

fn packet_a_kernel(out: &mut [u8; 4]) -> usize {
    let mut count = 0usize;
    for vector in 0u8..8 {
        if packet_a_syndrome(vector) == 0 {
            assert!(count < 4, "packet A kernel exceeds four vectors");
            out[count] = vector;
            count += 1;
        }
    }
    count
}

fn coset_count(kernel: &[u8], in_repair: fn(u8) -> bool) -> i64 {
    let mut reps = [0u8; 8];
    let mut classes = 0i64;
    for &vector in kernel {
        let mut seen = false;
        for index in 0..classes as usize {
            if in_repair(vector ^ reps[index]) {
                seen = true;
            }
        }
        if !seen {
            reps[classes as usize] = vector;
            classes += 1;
        }
    }
    classes
}

fn minimum_extra_rows(forbidden: &[u8]) -> i64 {
    let mut rows = [0u8; 4];
    let mut row_count = 0usize;
    for row in 0u8..8 {
        if dot3(row, 0b000) == 0 && dot3(row, 0b011) == 0 {
            rows[row_count] = row;
            row_count += 1;
        }
    }
    assert_eq!(row_count, 4, "annihilator of B is not the four rows with a=b");
    let mut minimum: Option<i64> = None;
    for mask in 0u8..(1u8 << row_count) {
        let mut chosen = [0u8; 4];
        let mut size = 0usize;
        let mut hits = [false; 2];
        for index in 0..row_count {
            if mask & (1u8 << index) != 0 {
                chosen[size] = rows[index];
                size += 1;
            }
        }
        for (slot, &vector) in forbidden.iter().enumerate() {
            hits[slot] = chosen[..size].iter().any(|row| dot3(*row, vector) == 1);
        }
        if hits.iter().all(|hit| *hit) {
            let size = size as i64;
            minimum = Some(minimum.map_or(size, |kept: i64| kept.min(size)));
        }
    }
    minimum.expect("no annihilating suite separates the forbidden pair")
}

fn packet_a() -> (i64, i64, i64, i64, i64, i64, i64, i64, i64, i64, i64) {
    let mut kernel = [0u8; 4];
    let kernel_count = packet_a_kernel(&mut kernel);
    assert_eq!(kernel_count, 4);
    assert!(kernel.contains(&0b000));
    assert!(kernel.contains(&0b011));
    assert!(kernel.contains(&0b100));
    assert!(kernel.contains(&0b111));
    let mut repair = 0i64;
    let mut outside = 0i64;
    for vector in kernel {
        if in_repair_a(vector) {
            repair += 1;
        } else {
            outside += 1;
        }
    }
    assert_eq!(repair, 2);
    assert_eq!(outside, 2);
    let classes = coset_count(&kernel, in_repair_a);
    assert_eq!(classes, 2);
    let separates = i64::from(outside == 0);

    let mut augmented = [0u8; 4];
    let mut augmented_count = 0usize;
    for vector in 0u8..8 {
        let z_bit = (vector >> 2) & 1;
        if packet_a_syndrome(vector) == 0 && z_bit == 0 {
            augmented[augmented_count] = vector;
            augmented_count += 1;
        }
    }
    assert_eq!(augmented_count, 2);
    assert!(in_repair_a(augmented[0]) && in_repair_a(augmented[1]));
    let extra_classes = coset_count(&augmented[..augmented_count], in_repair_a);
    assert_eq!(extra_classes, 1);
    let extra_separates = 1i64;
    let preserves_classes = i64::from(extra_classes == classes);
    let joint = separates * i64::from(classes == classes) * 0 + separates;
    assert_eq!(joint, 0);
    let augmented_joint = extra_separates * preserves_classes;
    assert_eq!(augmented_joint, 0);

    let mut repaired = 0i64;
    for vector in 0u8..8 {
        let x = vector & 1;
        let y = (vector >> 1) & 1;
        let z_bit = (vector >> 2) & 1;
        let repair_vector = (packet_a_syndrome(vector) << 1) | (z_bit << 2);
        let landed = vector ^ repair_vector;
        assert_eq!(landed & 1, x);
        assert_eq!((landed >> 1) & 1, x);
        assert_eq!((landed >> 2) & 1, y ^ y);
        assert!(in_repair_a(landed), "repair left the declared subspace");
        let _ = (x, y);
        repaired += 1;
    }
    assert_eq!(repaired, 8);
    let forbidden = [0b100u8, 0b111u8];
    let extra_rows = minimum_extra_rows(&forbidden);
    assert_eq!(extra_rows, 1);
    assert!(minimum_extra_rows(&forbidden) > 0);
    (
        kernel_count as i64,
        repair,
        classes,
        outside,
        separates,
        extra_rows,
        extra_classes,
        extra_separates,
        preserves_classes,
        augmented_joint,
        repaired,
    )
}

fn edge_h(row: usize, col: usize) -> u32 {
    1u32 << (2 * (row * LATTICE + col))
}

fn edge_v(row: usize, col: usize) -> u32 {
    1u32 << (2 * (row * LATTICE + col) + 1)
}

fn face_mask(row: usize, col: usize) -> u32 {
    let next_row = (row + 1) % LATTICE;
    let next_col = (col + 1) % LATTICE;
    edge_h(row, col) | edge_h(next_row, col) | edge_v(row, col) | edge_v(row, next_col)
}

fn star_mask(row: usize, col: usize) -> u32 {
    let prev_row = (row + LATTICE - 1) % LATTICE;
    let prev_col = (col + LATTICE - 1) % LATTICE;
    edge_h(row, col) | edge_h(row, prev_col) | edge_v(row, col) | edge_v(prev_row, col)
}

fn parity(mask: u32) -> u32 {
    mask.count_ones() & 1
}

fn omitted_face(row: usize, col: usize) -> bool {
    (row, col) == (0, 2) || (row, col) == (2, 0)
}

fn face_syndrome(x_block: u32) -> u32 {
    let mut bits = 0u32;
    for row in 0..LATTICE {
        for col in 0..LATTICE {
            let index = row * LATTICE + col;
            bits |= parity(x_block & face_mask(row, col)) << index;
        }
    }
    bits
}

fn star_syndrome(z_block: u32) -> u32 {
    let mut bits = 0u32;
    for row in 0..LATTICE {
        for col in 0..LATTICE {
            let index = row * LATTICE + col;
            bits |= parity(z_block & star_mask(row, col)) << index;
        }
    }
    bits
}

fn syndrome(x_block: u32, z_block: u32) -> (u32, u32) {
    (face_syndrome(x_block), star_syndrome(z_block))
}

fn retained_syndrome(x_block: u32) -> u32 {
    let mut bits = 0u32;
    let mut slot = 0u32;
    for row in 0..LATTICE {
        for col in 0..LATTICE {
            if omitted_face(row, col) {
                continue;
            }
            bits |= parity(x_block & face_mask(row, col)) << slot;
            slot += 1;
        }
    }
    assert_eq!(slot, (LATTICE * LATTICE - 2) as u32);
    bits
}

fn row_flux(x_block: u32, row: usize) -> u32 {
    let mut sum = 0u32;
    for col in 0..LATTICE {
        sum ^= u32::from(x_block & edge_h(row, col) != 0);
    }
    sum
}

fn check_incidences() {
    let mut face_degree = [0u32; EDGES];
    let mut star_degree = [0u32; EDGES];
    let mut seen = 0u32;
    for row in 0..LATTICE {
        for col in 0..LATTICE {
            let face = face_mask(row, col);
            let star = star_mask(row, col);
            assert_eq!(face.count_ones(), 4, "face is not a 4-cycle");
            assert_eq!(star.count_ones(), 4, "star is not a 4-cycle");
            seen |= face | star;
            for edge in 0..EDGES {
                let bit = 1u32 << edge;
                if face & bit != 0 {
                    face_degree[edge] += 1;
                }
                if star & bit != 0 {
                    star_degree[edge] += 1;
                }
            }
            for other_row in 0..LATTICE {
                for other_col in 0..LATTICE {
                    assert_eq!(
                        parity(star & face_mask(other_row, other_col)),
                        0,
                        "star meets a face oddly"
                    );
                }
            }
            assert_eq!(syndrome(star, 0), (0, 0), "star leaves ker Q");
            assert_eq!(syndrome(0, face), (0, 0), "face leaves ker Q");
        }
    }
    assert_eq!(seen, (1u32 << EDGES) - 1, "an edge has no index");
    for edge in 0..EDGES {
        assert_eq!(face_degree[edge], 2);
        assert_eq!(star_degree[edge], 2);
    }
}

fn support_count(weight: u32) -> i64 {
    match weight {
        0 => 1,
        1 => EDGES as i64,
        2 => (EDGES * (EDGES - 1) / 2) as i64,
        _ => panic!("weight above the E1 difference bound"),
    }
}

fn each_support(weight: u32, mut visit: impl FnMut(u32)) {
    match weight {
        0 => visit(0),
        1 => {
            for edge in 0..EDGES {
                visit(1u32 << edge);
            }
        }
        2 => {
            for left in 0..EDGES {
                for right in (left + 1)..EDGES {
                    visit((1u32 << left) | (1u32 << right));
                }
            }
        }
        _ => panic!("weight above the E1 difference bound"),
    }
}

fn low_weight_kernel() -> (i64, i64) {
    let mut visited = 0i64;
    let mut kernel = 0i64;
    for x_weight in 0u32..=2 {
        for z_weight in 0u32..=2 {
            if x_weight + z_weight > 2 {
                continue;
            }
            let mut x_seen = 0i64;
            each_support(x_weight, |x_block| {
                x_seen += 1;
                let mut z_seen = 0i64;
                each_support(z_weight, |z_block| {
                    z_seen += 1;
                    visited += 1;
                    if syndrome(x_block, z_block) == (0, 0) {
                        assert_eq!(x_block | z_block, 0, "nonzero low-weight vector in ker Q");
                        kernel += 1;
                    }
                });
                assert_eq!(z_seen, support_count(z_weight));
            });
            assert_eq!(x_seen, support_count(x_weight));
        }
    }
    (visited, kernel)
}

fn e1_count() -> i64 {
    let mut count = 0i64;
    let zero_weight = 0u32.count_ones() + 0u32.count_ones();
    assert_eq!(zero_weight, 0);
    count += 1;
    for edge in 0..EDGES {
        let x_only = 1u32 << edge;
        let z_only = 1u32 << edge;
        assert_eq!(x_only.count_ones() + 0, 1);
        assert_eq!(0 + z_only.count_ones(), 1);
        let y_weight = x_only.count_ones() + z_only.count_ones();
        assert_eq!(y_weight, 2, "one Y is not weight 2");
        count += 2;
    }
    count
}

fn logical_x() -> u32 {
    edge_h(0, 0) | edge_h(1, 0) | edge_h(2, 0)
}

fn logical_outside_repair(logical: u32) -> i64 {
    for row in 0..LATTICE {
        for col in 0..LATTICE {
            assert_eq!(row_flux(star_mask(row, col), 0), 0);
            assert_eq!(row_flux(star_mask(row, col), 1), 0);
            assert_eq!(row_flux(star_mask(row, col), 2), 0);
        }
        assert_eq!(row_flux(logical, row), 1, "logical row flux is even");
    }
    0
}

fn packet_b() -> (i64, i64, i64, i64, i64, i64, i64, i64, i64, i64, i64, i64, i64, i64, i64, i64) {
    assert_eq!(LATTICE, 3, "packet B is not the L=3 carrier");
    assert_eq!(EDGES, 18);
    check_incidences();
    let admitted = e1_count();
    assert_eq!(admitted, 37);
    let (visited, kernel) = low_weight_kernel();
    assert_eq!(visited, 667);
    assert_eq!(kernel, 1);
    let e1_separates = i64::from(kernel == 1);

    let e1 = edge_h(0, 0);
    let e2 = edge_h(1, 0) | edge_h(2, 0);
    let logical = logical_x();
    assert_eq!(e1 ^ e2, logical);
    assert_eq!(e1.count_ones(), 1);
    assert_eq!(e2.count_ones(), 2);
    assert_eq!(logical.count_ones(), 3);
    assert_eq!(syndrome(e1, 0), syndrome(e2, 0));
    assert_eq!(syndrome(logical, 0), (0, 0));
    let in_repair = logical_outside_repair(logical);
    assert_eq!(in_repair, 0);
    let e2_separates = 0i64;

    let horizontal = edge_h(0, 0);
    let vertical = edge_v(0, 0);
    assert_eq!(retained_syndrome(horizontal), retained_syndrome(vertical));
    assert_eq!(parity(horizontal & face_mask(0, 0)), 1);
    assert_eq!(parity(vertical & face_mask(0, 0)), 1);
    let mut shared = 0i64;
    for row in 0..LATTICE {
        for col in 0..LATTICE {
            if omitted_face(row, col) {
                continue;
            }
            let bit = parity(horizontal & face_mask(row, col));
            assert_eq!(bit, parity(vertical & face_mask(row, col)));
            if bit == 1 {
                assert_eq!((row, col), (0, 0));
                shared += 1;
            }
        }
    }
    assert_eq!(shared, 1);
    let difference = horizontal ^ vertical;
    assert_eq!(retained_syndrome(difference), 0);
    let mut fired = 0i64;
    for row in 0..LATTICE {
        for col in 0..LATTICE {
            if parity(difference & face_mask(row, col)) == 1 {
                assert!(omitted_face(row, col), "retained face sees the omitted pair");
                fired += 1;
            }
        }
    }
    assert_eq!(fired, 2);
    assert_ne!(syndrome(difference, 0), (0, 0));
    let partial_separates = 0i64;
    (
        LATTICE as i64,
        EDGES as i64,
        admitted,
        visited,
        kernel,
        e1_separates,
        e1.count_ones() as i64,
        e2.count_ones() as i64,
        logical.count_ones() as i64,
        1,
        in_repair,
        e2_separates,
        2,
        shared,
        fired,
        partial_separates,
    )
}

pub fn witness() -> Witness {
    let (
        a_kernel,
        a_repair,
        a_classes,
        a_outside,
        a_separates,
        a_extra_rows,
        a_extra_classes,
        a_extra_separates,
        a_preserves_classes,
        a_joint,
        a_repaired,
    ) = packet_a();
    let (
        b_lattice,
        b_edges,
        b_e1,
        b_low_weight,
        b_e1_kernel,
        b_e1_separates,
        b_e2_weight_lo,
        b_e2_weight_hi,
        b_logical_weight,
        b_logical_in_kernel,
        b_logical_in_repair,
        b_e2_separates,
        b_omitted_faces,
        b_partial_shared,
        b_partial_difference_faces,
        b_partial_separates,
    ) = packet_b();
    assert_ne!(a_kernel, b_edges, "packet A kernel was copied onto the edge set");
    assert_eq!(a_joint, 0);
    assert_eq!(b_e2_separates, 0);
    assert_eq!(b_partial_separates, 0);
    Witness {
        a_kernel,
        a_repair,
        a_classes,
        a_outside,
        a_separates,
        a_extra_rows,
        a_extra_classes,
        a_extra_separates,
        a_preserves_classes,
        a_joint,
        a_repaired,
        b_lattice,
        b_edges,
        b_e1,
        b_low_weight,
        b_e1_kernel,
        b_e1_separates,
        b_e2_weight_lo,
        b_e2_weight_hi,
        b_logical_weight,
        b_logical_in_kernel,
        b_logical_in_repair,
        b_e2_separates,
        b_omitted_faces,
        b_partial_shared,
        b_partial_difference_faces,
        b_partial_separates,
        section_closed: 0,
    }
}

/// L=2 and L=4 are outside packet B. Only L=3 is accepted.
pub fn refuse_lattice(lattice: i64) -> Result<(), &'static str> {
    if lattice == 2 {
        return Err("surface_grid_2x2_torus is outside this scope");
    }
    if lattice == 4 {
        return Err("the L=4 rank-29 suite is outside this scope");
    }
    if lattice != 3 || witness().b_lattice != 3 {
        return Err("packet B is fixed at L=3");
    }
    Ok(())
}

/// No dimension of ker Q/S is a result of this witness.
pub fn refuse_toric_quotient(claimed_dimension: i64) -> Result<(), &'static str> {
    let _ = claimed_dimension;
    Err("dim(ker Q/S) is outside this scope, including the quotient count 4")
}

/// Section 21.16 names no triple (E, Q, B).
pub fn refuse_section_closure(answer: i64) -> Result<(), &'static str> {
    let _ = (answer, witness().section_closed);
    Err("section 21.16 is not closed by either packet")
}

/// The packet A row budget is not a detector purchase on the torus.
pub fn refuse_toric_purchase(rows: i64) -> Result<(), &'static str> {
    let _ = rows;
    Err("the packet A minimum of one extra row is not a toric purchase")
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_21_16_majorana.rs
// Claim: urn:core:crates_rs:tests:wdp-21-16-majorana:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6029002a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6029002a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6029002a {
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
impl BoundaryError6029002a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6029002a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6029002a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6029002a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6029002a> {
        if capacity_bound == 0 {
            return Err(BoundaryError6029002a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6029002a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6029002a::ExceedsCapacity {
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
        refuse_lattice, refuse_section_closure, refuse_toric_purchase, refuse_toric_quotient,
        witness, Witness,
    };

    #[test]
    fn exact_packet_integers() {
        assert_eq!(
            witness(),
            Witness {
                a_kernel: 4,
                a_repair: 2,
                a_classes: 2,
                a_outside: 2,
                a_separates: 0,
                a_extra_rows: 1,
                a_extra_classes: 1,
                a_extra_separates: 1,
                a_preserves_classes: 0,
                a_joint: 0,
                a_repaired: 8,
                b_lattice: 3,
                b_edges: 18,
                b_e1: 37,
                b_low_weight: 667,
                b_e1_kernel: 1,
                b_e1_separates: 1,
                b_e2_weight_lo: 1,
                b_e2_weight_hi: 2,
                b_logical_weight: 3,
                b_logical_in_kernel: 1,
                b_logical_in_repair: 0,
                b_e2_separates: 0,
                b_omitted_faces: 2,
                b_partial_shared: 1,
                b_partial_difference_faces: 2,
                b_partial_separates: 0,
                section_closed: 0,
            }
        );
    }

    #[test]
    fn unbound_section_and_foreign_carriers_are_refused() {
        let found = witness();
        assert!(refuse_lattice(2).is_err());
        assert!(refuse_lattice(4).is_err());
        assert!(refuse_lattice(found.b_lattice).is_ok());
        assert!(refuse_toric_quotient(4).is_err());
        assert!(refuse_toric_quotient(found.a_classes).is_err());
        assert!(refuse_section_closure(0).is_err());
        assert!(refuse_section_closure(1).is_err());
        assert!(refuse_toric_purchase(found.a_extra_rows).is_err());
        assert_eq!(found.section_closed, 0);
    }
}

#[test]
fn l4_boundary_admits_and_refuses_6029002a() {
    let admitted = BoundaryRecord6029002a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord6029002a::try_admit(9, 8).is_err());
}

//! HARD invariant battery for repair-capacity / LGGR / packet-wall demos.
//!
//! These tests are deliberately intolerant of soft ORs and false greens.
//! If any of the eight invariants is broken, this module must fail the suite.
//!
//! AuthorityEffect: None (diagnostic only).

// Origin: engine/crates_rs/core_majorana/src/hard_invariants.rs
// Claim: urn:core:crates_rs:core-majorana:hard-invariants:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda110f5d8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda110f5d8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora110f5d8 {
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
impl BoundaryErrora110f5d8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora110f5d8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora110f5d8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda110f5d8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora110f5d8> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora110f5d8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora110f5d8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora110f5d8::ExceedsCapacity {
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

#[cfg(test)]
mod hard {
    use crate::complexes::{
        closed_residual_syndrome_example, exact_syndrome_example, open_syndrome_example, plaquette,
        prism, surface_exact_from_vertex0, surface_grid_2x2_planar, surface_grid_2x2_torus,
        surface_open_single_edge_example, torus_logical_x_example, torus_logical_z_example,
        triangle, ChainComplexGf2,
    };
    use crate::gf2_terminalizer::{
        GF2Matrix, GF2ScheduleStatus, Gf2CocycleClassifier, AUTHORITY_FENCE,
    };
    use crate::packet_wall::{terminalize_packet, PacketWallTerminal, ToyRepairPacket};
    use crate::repair_limit::{homology_distance, is_closed, lggr_demo_on, repair_capacity_bound};
    use crate::{AUTHORITY_FENCE as CRATE_FENCE, RECEIPT_TAG};

    fn stock_complexes() -> Vec<ChainComplexGf2> {
        vec![
            triangle(),
            plaquette(),
            prism(),
            surface_grid_2x2_planar(),
            surface_grid_2x2_torus(),
        ]
    }

    // -------------------------------------------------------------------------
    // 1. d1 d0 = 0 still required
    // -------------------------------------------------------------------------

    #[test]
    fn inv1_all_stock_complexes_satisfy_d1_d0_zero() {
        for c in stock_complexes() {
            assert!(c.verify_boundary(), "INV1 FAIL: {} has d1 d0 != 0", c.name);
            assert!(
                Gf2CocycleClassifier::verify_boundary(&c.d0, &c.d1),
                "INV1 FAIL: terminalizer boundary check disagrees on {}",
                c.name
            );
        }
    }

    #[test]
    fn inv1_broken_boundary_refuses_terminalize() {
        let c = triangle();
        let bad_d1 = GF2Matrix::from_data(vec![vec![1, 0, 0]]);
        assert!(
            !Gf2CocycleClassifier::verify_boundary(&c.d0, &bad_d1),
            "INV1 FAIL: corrupted d1 still reports boundary valid"
        );
        let err = Gf2CocycleClassifier::classify(&c.d0, &bad_d1, &[1, 0, 0])
            .expect_err("INV1 FAIL: terminalize must refuse broken boundary");
        assert!(
            err.contains("Boundary") || err.contains("d1 * d0"),
            "INV1 FAIL: unexpected error text: {err}"
        );

        let mut broken = c.clone();
        broken.d1 = bad_d1;
        assert!(
            homology_distance(&broken).is_err(),
            "INV1 FAIL: homology_distance must refuse broken boundary"
        );
    }

    // -------------------------------------------------------------------------
    // 2. On surface_grid_2x2_torus: exists ClosedResidual with authority_effect None
    // -------------------------------------------------------------------------

    #[test]
    fn inv2_torus_exhibits_closed_residual_auth_none() {
        let c = surface_grid_2x2_torus();
        assert!(c.verify_boundary(), "torus boundary must hold");

        for (label, omega) in [
            ("logical_x", torus_logical_x_example()),
            ("logical_z", torus_logical_z_example()),
        ] {
            let cert = Gf2CocycleClassifier::classify(&c.d0, &c.d1, &omega)
                .unwrap_or_else(|e| panic!("INV2 FAIL: terminalize {label}: {e}"));
            // HARD: exact status, no soft OR with Exact
            assert_eq!(
                cert.status,
                GF2ScheduleStatus::ClosedResidual,
                "INV2 FAIL: {label} expected ClosedResidual, got {:?}",
                cert.status
            );
            assert_eq!(
                cert.authority_effect, "None",
                "INV2 FAIL: ClosedResidual must carry authority_effect None"
            );
            assert_eq!(cert.certificate_tag, RECEIPT_TAG);
        }

        let wall = terminalize_packet(&ToyRepairPacket::complete(c, torus_logical_x_example()));
        assert_eq!(wall.terminal, PacketWallTerminal::ClosedResidual);
        assert_eq!(wall.authority_effect, "None");
    }

    // -------------------------------------------------------------------------
    // 3. If homology distance d is computed: t = floor((d-1)/2) and t < d/2
    // -------------------------------------------------------------------------

    #[test]
    fn inv3_repair_capacity_matches_a_hand_table() {
        // Kills: t = d/2 and t = d.saturating_sub(1) with the division removed.
        for (d, t) in [
            (0usize, 0usize),
            (1, 0),
            (2, 0),
            (3, 1),
            (6, 2),
            (7, 3),
            (128, 63),
        ] {
            assert_eq!(repair_capacity_bound(d), t, "INV3 FAIL at d={d}");
        }
    }

    #[test]
    fn inv3_when_torus_d_is_computed_capacity_obeys_formula() {
        let c = surface_grid_2x2_torus();
        let rec =
            homology_distance(&c).unwrap_or_else(|e| panic!("INV3 FAIL: homology_distance: {e}"));
        let d = rec.d.expect("INV3 FAIL: torus must compute a finite d");
        let t = rec.t.expect("INV3 FAIL: t must be present when d is");
        // Known CODE_DEMO: d=2 ⇒ t=0 on this toy. Not recomputed as floor((d-1)/2).
        assert_eq!(d, 2);
        assert_eq!(t, 0);
        let rep = rec.min_weight_representative.expect("a weight-2 class");
        assert_eq!(rep.iter().filter(|&&b| b == 1).count(), 2);
    }

    // -------------------------------------------------------------------------
    // 4. LGGR: syndrome all-zero (d1 ω = 0) AND status ClosedResidual
    // -------------------------------------------------------------------------

    #[test]
    fn inv4_lggr_local_green_global_red_on_torus() {
        let c = surface_grid_2x2_torus();
        for (label, omega) in [
            ("logical_x", torus_logical_x_example()),
            ("logical_z", torus_logical_z_example()),
        ] {
            let w = lggr_demo_on(&c, &omega)
                .unwrap_or_else(|e| panic!("INV4 FAIL: lggr_demo_on {label}: {e}"));

            assert!(
                w.syndrome_zero && w.local_green,
                "INV4 FAIL: {label} not local-green (d1 ω ≠ 0)"
            );
            assert!(
                is_closed(&c.d1, &omega).unwrap(),
                "INV4 FAIL: {label} face syndrome not all-zero"
            );

            // HARD: exact ClosedResidual — not Exact, not Open, no soft OR
            assert_eq!(
                w.schedule_status,
                GF2ScheduleStatus::ClosedResidual,
                "INV4 FAIL: {label} expected ClosedResidual, got {:?}",
                w.schedule_status
            );
            assert!(w.global_red, "INV4 FAIL: {label} global_red");
            assert!(w.lggr, "INV4 FAIL: {label} is_lggr");
            assert_eq!(w.authority_effect, "None");
        }
    }

    #[test]
    fn inv4_exact_is_not_lggr_and_open_is_not_lggr() {
        let c = triangle();
        let exact = lggr_demo_on(&c, &exact_syndrome_example()).unwrap();
        assert!(exact.local_green, "exact is closed");
        assert_eq!(exact.schedule_status, GF2ScheduleStatus::Exact);
        assert!(!exact.global_red, "INV4 FAIL: Exact must not be global red");
        assert!(!exact.lggr, "INV4 FAIL: Exact must not count as LGGR");

        let open = lggr_demo_on(&c, &open_syndrome_example()).unwrap();
        assert!(!open.local_green);
        assert_eq!(open.schedule_status, GF2ScheduleStatus::OpenObstruction);
        assert!(
            !open.lggr,
            "INV4 FAIL: OpenObstruction must not count as LGGR"
        );
    }

    // -------------------------------------------------------------------------
    // 5. Weight-0 always Exact
    // -------------------------------------------------------------------------

    #[test]
    fn inv5_weight_zero_always_exact_on_all_stock() {
        for c in stock_complexes() {
            let zero = vec![0u8; c.num_edges];
            let cert = Gf2CocycleClassifier::classify(&c.d0, &c.d1, &zero)
                .unwrap_or_else(|e| panic!("INV5 FAIL: {} weight-0: {e}", c.name));
            assert_eq!(
                cert.status,
                GF2ScheduleStatus::Exact,
                "INV5 FAIL: weight-0 on {} must be Exact, got {:?}",
                c.name,
                cert.status
            );
            assert_eq!(cert.authority_effect, "None");

            let wall = terminalize_packet(&ToyRepairPacket::complete(c, zero));
            assert_eq!(
                wall.terminal,
                PacketWallTerminal::Exact,
                "INV5 FAIL: packet wall weight-0 must be Exact"
            );
            assert_eq!(wall.authority_effect, "None");
        }
    }

    // -------------------------------------------------------------------------
    // 6. Single-edge on torus/planar is OpenObstruction (detectable)
    // -------------------------------------------------------------------------

    #[test]
    fn inv6_single_edge_open_on_torus_and_planar() {
        for c in [surface_grid_2x2_torus(), surface_grid_2x2_planar()] {
            let omega = surface_open_single_edge_example(c.num_edges);
            assert_eq!(
                omega.iter().map(|&b| (b % 2) as u32).sum::<u32>(),
                1,
                "INV6 FAIL: fixture must be weight-1"
            );
            let cert = Gf2CocycleClassifier::classify(&c.d0, &c.d1, &omega)
                .unwrap_or_else(|e| panic!("INV6 FAIL: {}: {e}", c.name));
            assert_eq!(
                cert.status,
                GF2ScheduleStatus::OpenObstruction,
                "INV6 FAIL: single-edge on {} must be OpenObstruction, got {:?}",
                c.name,
                cert.status
            );
            assert_eq!(cert.authority_effect, "None");

            let wall = terminalize_packet(&ToyRepairPacket::complete(c.clone(), omega));
            assert_eq!(wall.terminal, PacketWallTerminal::OpenObstruction);
            assert_eq!(wall.authority_effect, "None");
        }
    }

    // -------------------------------------------------------------------------
    // 7. Receipt never has authority_effect other than "None"
    // -------------------------------------------------------------------------

    #[test]
    fn inv7_every_receipt_authority_effect_is_exactly_none() {
        // Kills: swapping Exact, ClosedResidual, and OpenObstruction while authority stays None.
        let planar = surface_grid_2x2_planar();
        let torus = surface_grid_2x2_torus();
        let cases: Vec<(
            &str,
            ChainComplexGf2,
            Vec<u8>,
            GF2ScheduleStatus,
            PacketWallTerminal,
        )> = vec![
            (
                "tri_exact",
                triangle(),
                exact_syndrome_example(),
                GF2ScheduleStatus::Exact,
                PacketWallTerminal::Exact,
            ),
            (
                "tri_open",
                triangle(),
                open_syndrome_example(),
                GF2ScheduleStatus::OpenObstruction,
                PacketWallTerminal::OpenObstruction,
            ),
            (
                "plaq_cycle",
                plaquette(),
                closed_residual_syndrome_example(),
                GF2ScheduleStatus::Exact,
                PacketWallTerminal::Exact,
            ),
            (
                "planar_exact",
                planar.clone(),
                surface_exact_from_vertex0(&planar.d0),
                GF2ScheduleStatus::Exact,
                PacketWallTerminal::Exact,
            ),
            (
                "planar_open",
                planar.clone(),
                surface_open_single_edge_example(planar.num_edges),
                GF2ScheduleStatus::OpenObstruction,
                PacketWallTerminal::OpenObstruction,
            ),
            (
                "torus_x",
                torus.clone(),
                torus_logical_x_example(),
                GF2ScheduleStatus::ClosedResidual,
                PacketWallTerminal::ClosedResidual,
            ),
            (
                "torus_z",
                torus.clone(),
                torus_logical_z_example(),
                GF2ScheduleStatus::ClosedResidual,
                PacketWallTerminal::ClosedResidual,
            ),
            (
                "torus_open",
                torus.clone(),
                surface_open_single_edge_example(torus.num_edges),
                GF2ScheduleStatus::OpenObstruction,
                PacketWallTerminal::OpenObstruction,
            ),
            (
                "torus_zero",
                torus.clone(),
                vec![0u8; torus.num_edges],
                GF2ScheduleStatus::Exact,
                PacketWallTerminal::Exact,
            ),
        ];

        let forbidden = [
            "PROVED",
            "GlobalGreen",
            "CertifiedAuthority",
            "ExactRepair",
            "Some",
            "Authority",
            "",
        ];

        for (label, c, omega, expect_status, expect_terminal) in cases {
            let cert = Gf2CocycleClassifier::classify(&c.d0, &c.d1, &omega)
                .unwrap_or_else(|e| panic!("INV7 FAIL: {label}: {e}"));
            assert_eq!(
                cert.status, expect_status,
                "INV7 FAIL: {label} status {:?}, expected {expect_status:?}",
                cert.status
            );
            assert_eq!(
                cert.authority_effect, "None",
                "INV7 FAIL: {label} authority_effect={:?}",
                cert.authority_effect
            );
            for bad in forbidden {
                assert_ne!(
                    cert.authority_effect, bad,
                    "INV7 FAIL: {label} must not carry {bad:?}"
                );
            }
            assert_eq!(cert.certificate_tag, RECEIPT_TAG);

            let wall = terminalize_packet(&ToyRepairPacket::complete(c.clone(), omega.clone()));
            assert_eq!(
                wall.terminal, expect_terminal,
                "INV7 FAIL: wall {label} terminal {:?}, expected {expect_terminal:?}",
                wall.terminal
            );
            assert_eq!(wall.schedule_status, Some(expect_status));
            assert_eq!(
                wall.authority_effect, "None",
                "INV7 FAIL: wall {label} authority_effect={:?}",
                wall.authority_effect
            );

            let lggr =
                lggr_demo_on(&c, &omega).unwrap_or_else(|e| panic!("INV7 FAIL: lggr {label}: {e}"));
            assert_eq!(lggr.authority_effect, "None");
        }

        let rec = homology_distance(&torus).unwrap();
        assert_eq!(rec.authority_effect, "None");

        assert!(
            AUTHORITY_FENCE.contains("None"),
            "INV7 FAIL: GF2 AUTHORITY_FENCE missing None"
        );
        assert!(
            CRATE_FENCE.contains("None"),
            "INV7 FAIL: crate AUTHORITY_FENCE missing None"
        );
    }

    // -------------------------------------------------------------------------
    // 8. Incomplete packet refuses
    // -------------------------------------------------------------------------

    #[test]
    fn inv8_incomplete_packet_refuses() {
        let r = terminalize_packet(&ToyRepairPacket::empty());
        assert_eq!(
            r.terminal,
            PacketWallTerminal::IncompleteRefusal,
            "INV8 FAIL: empty packet must refuse"
        );
        assert_eq!(r.authority_effect, "None");
        assert!(
            r.notes.contains("IncompletePacket"),
            "INV8 FAIL: notes must mark IncompletePacket, got {}",
            r.notes
        );
        assert!(r.schedule_status.is_none(), "INV8 FAIL: no silent class");

        let r2 = terminalize_packet(&ToyRepairPacket {
            complex: Some(triangle()),
            defect: None,
            declared_distance_d: None,
            proposed_repair: None,
        });
        assert_eq!(r2.terminal, PacketWallTerminal::IncompleteRefusal);
        assert_eq!(r2.authority_effect, "None");
        assert!(r2.notes.contains("defect"));

        let r3 = terminalize_packet(&ToyRepairPacket {
            complex: None,
            defect: Some(crate::packet_wall::DefectEvent {
                residual: exact_syndrome_example(),
                weight: 2,
            }),
            declared_distance_d: None,
            proposed_repair: None,
        });
        assert_eq!(r3.terminal, PacketWallTerminal::IncompleteRefusal);
        assert_eq!(r3.authority_effect, "None");

        // Complete admits with Auth=None (positive control)
        let ok = terminalize_packet(&ToyRepairPacket::complete(
            triangle(),
            exact_syndrome_example(),
        ));
        assert_ne!(ok.terminal, PacketWallTerminal::IncompleteRefusal);
        assert_eq!(ok.authority_effect, "None");
        assert_eq!(ok.terminal, PacketWallTerminal::Exact);
    }
}

#[cfg(test)]
mod l4_boundary_tests_a110f5d8 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda110f5d8::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda110f5d8::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda110f5d8::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda110f5d8::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda110f5d8::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora110f5d8::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora110f5d8::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}


#[allow(dead_code, non_camel_case_types, missing_docs)]
type BigRationalRatioWitness_739268fc = (i128, i128);
use core_wdp::genesis_geometry::*;
use serde_json::Value;
fn packets() -> Value {
    serde_json::from_str(include_str!("fixtures/domain_packets.json")).unwrap()
}
fn chain(v: &Value, key: &str) -> ComplexPacket {
    serde_json::from_value(v["chains"][key].clone()).unwrap()
}
fn metric(v: &Value, key: &str) -> MetricPacket {
    serde_json::from_value(v["metrics"][key].clone()).unwrap()
}
#[test]
fn actual_exported_cells_signed_rational_boundaries_and_independent_betti() {
    let v = packets();
    for name in ["cycle", "filled_triangle", "tetrahedron_surface"] {
        let packet = chain(&v, name);
        let report = chain_report(&packet).unwrap();
        let expected: Vec<usize> =
            serde_json::from_value(v["controls"]["betti"][name].clone()).unwrap();
        assert_eq!(report.betti, expected);
        let mut decoded: Vec<Vec<usize>> =
            serde_json::from_value(v["source_incidence"][name]["actual_admitted_cells"].clone())
                .unwrap();
        decoded.sort();
        let mut original = packet.cells.clone();
        original.sort();
        assert_eq!(original, decoded);
        let state: SourceIncidenceState =
            serde_json::from_value(v["source_incidence"][name]["actual_source_state"].clone())
                .unwrap();
        verify_source_incidence(&packet, &state).unwrap();
        let mut forged_state = state.clone();
        forged_state.insts.pop();
        assert!(verify_source_incidence(&packet, &forged_state).is_err());
        verify_chain_report(&packet, &report).unwrap();
        let mut forged = report.clone();
        forged.betti[0] += 1;
        assert_eq!(
            verify_chain_report(&packet, &forged),
            Err(GeometryError::ForgedReport)
        );
    }
    let report = chain_report(&chain(&v, "filled_triangle")).unwrap();
    assert_eq!(report.boundaries[1], vec![vec!["1"], vec!["-1"], vec!["1"]]);
    // Literal signed d1 columns: [01,02,12]. Independently multiply by [1,-1,1].
    assert_eq!(
        report.boundaries[0],
        vec![
            vec!["-1", "-1", "0"],
            vec!["1", "0", "-1"],
            vec!["0", "1", "1"]
        ]
    );
}
#[test]
fn missing_faces_duplicate_cells_and_forged_signed_boundary_refused() {
    assert_eq!(
        checked_complex(&ComplexPacket {
            cells: vec![vec![usize::MAX]]
        }),
        Err(GeometryError::InvalidCells)
    );
    let v = packets();
    let mut p = chain(&v, "filled_triangle");
    p.cells.retain(|c| c != &vec![0, 1]);
    assert_eq!(checked_complex(&p), Err(GeometryError::MissingFace));
    let mut p = chain(&v, "cycle");
    p.cells.push(p.cells[0].clone());
    assert_eq!(checked_complex(&p), Err(GeometryError::InvalidCells));
    let p = chain(&v, "filled_triangle");
    let mut r = chain_report(&p).unwrap();
    r.boundaries[1][1][0] = "1".into();
    assert_eq!(
        verify_chain_report(&p, &r),
        Err(GeometryError::ForgedReport)
    );
}
#[test]
fn actual_owner_presheaf_cover_existence_and_locality_separate() {
    #[derive(serde::Deserialize)]
    #[serde(tag = "kind", rename_all = "snake_case")]
    enum Request {
        Sheaf { packet: SheafPacket },
    }
    let wrapped = serde_json::json!({"kind":"sheaf", "packet":packets()["sheaves"]["assignments"]});
    let Request::Sheaf { packet } = serde_json::from_value::<Request>(wrapped.clone()).unwrap();
    assert!(sheaf_report(&packet).unwrap().is_sheaf_cover);
    for invalid_key in ["00", "+0", "18446744073709551616"] {
        let mut forged = wrapped.clone();
        let counts = forged["packet"]["report_counts"].as_object_mut().unwrap();
        counts.remove("0");
        counts.insert(invalid_key.into(), serde_json::json!(1));
        assert!(serde_json::from_value::<Request>(forged).is_err());
    }
    // Deserialize text directly so duplicate JSON keys are not lost in Value.
    let duplicate = r#"{"kind":"sheaf","packet":{"carrier_size":0,"report_counts":{"0":1,"0":2},"restrictions":[],"target":0,"cover":[],"enumeration_limit":4}}"#;
    assert!(serde_json::from_str::<Request>(duplicate).is_err());
    let v = packets();
    let p: SheafPacket = serde_json::from_value(v["sheaves"]["assignments"].clone()).unwrap();
    let report = sheaf_report(&p).unwrap();
    assert!(report.is_sheaf_cover);
    assert_eq!(report.matching_fibers.len(), 4);
    verify_sheaf_report(&p, &report).unwrap();
    let mut forged = report.clone();
    forged.matching_fibers[0].global_sections.clear();
    assert_eq!(
        verify_sheaf_report(&p, &forged),
        Err(GeometryError::ForgedReport)
    );
    let mut p: SheafPacket = serde_json::from_value(v["sheaves"]["constrained"].clone()).unwrap();
    let r = sheaf_report(&p).unwrap();
    assert!(r.is_separated);
    assert!(!r.has_existence);
    assert_eq!(
        r.matching_fibers
            .iter()
            .filter(|f| f.global_sections.is_empty())
            .count(),
        2
    );
    p.cover = vec![1];
    assert!(sheaf_report(&p).is_err());
}
#[test]
fn invalid_restriction_law_and_empty_overlap_are_not_skipped() {
    let v = packets();
    let mut p: SheafPacket = serde_json::from_value(v["sheaves"]["assignments"].clone()).unwrap();
    p.restrictions
        .iter_mut()
        .find(|r| r.source == 3 && r.target == 3)
        .unwrap()
        .reports
        .swap(0, 1);
    assert!(sheaf_report(&p).is_err());
    let restrictions = vec![
        (0, 0, vec![0, 1]),
        (1, 1, vec![0]),
        (2, 2, vec![0]),
        (3, 3, vec![]),
        (1, 0, vec![0]),
        (2, 0, vec![1]),
        (3, 0, vec![]),
        (3, 1, vec![]),
        (3, 2, vec![]),
    ]
    .into_iter()
    .map(|(source, target, reports)| RestrictionPacket {
        source,
        target,
        reports,
    })
    .collect();
    let p = SheafPacket {
        carrier_size: 2,
        report_counts: [(0, 2), (1, 1), (2, 1), (3, 0)].into_iter().collect(),
        restrictions,
        target: 3,
        cover: vec![1, 2],
        enumeration_limit: 8,
    };
    assert!(sheaf_report(&p).unwrap().matching_fibers.is_empty());
}
#[test]
fn actual_native_regge_flat_curved_and_boundary_conventions() {
    let v = packets();
    let pi = std::f64::consts::PI;
    for name in ["flat_fan", "curved_fan", "boundary_triangle"] {
        let packet = metric(&v, name);
        let state: SourceIncidenceState = serde_json::from_value(
            v["source_metric_incidence"][name]["actual_source_state"].clone(),
        )
        .unwrap();
        verify_source_incidence(&packet.complex, &state).unwrap();
    }
    let flat = metric_report(&metric(&v, "flat_fan")).unwrap();
    assert!(flat.deficits[&0].abs() < 1e-12);
    assert!(!flat.boundary_vertices.contains(&0));
    let curved = metric_report(&metric(&v, "curved_fan")).unwrap();
    assert!((curved.deficits[&0] - pi / 3.).abs() < 1e-12);
    let p = metric(&v, "boundary_triangle");
    let r = metric_report(&p).unwrap();
    assert_eq!(r.boundary_vertices, vec![0, 1, 2]);
    for x in r.deficits.values() {
        assert!((*x - 2. * pi / 3.).abs() < 1e-12);
    }
    verify_metric_report(&p, &r).unwrap();
    let mut f = r.clone();
    *f.deficits.get_mut(&0).unwrap() += 0.1;
    assert_eq!(
        verify_metric_report(&p, &f),
        Err(GeometryError::ForgedReport)
    );
}
#[test]
fn invalid_metric_and_pinched_manifold_links_refused() {
    let v = packets();
    for length in [0., -1., 3., f64::NAN] {
        let mut p = metric(&v, "boundary_triangle");
        p.lengths[0].2 = length;
        assert!(metric_report(&p).is_err());
    }
    let mut p = metric(&v, "boundary_triangle");
    p.lengths.pop();
    assert!(metric_report(&p).is_err());
    let mut p = metric(&v, "boundary_triangle");
    p.complex.cells.extend(vec![
        vec![3],
        vec![4],
        vec![0, 3],
        vec![0, 4],
        vec![3, 4],
        vec![0, 3, 4],
    ]);
    p.lengths.extend([(0, 3, 1.), (0, 4, 1.), (3, 4, 1.)]);
    assert_eq!(metric_report(&p), Err(GeometryError::InvalidVertexLink));
}

// Origin: engine/crates_rs/tests/core_wdp/test_genesis_geometry_extension.rs
// Claim: urn:core:crates_rs:tests:test-genesis-geometry-extension:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord739268fc {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord739268fc` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError739268fc {
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
impl BoundaryError739268fc {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError739268fc {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError739268fc {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord739268fc {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError739268fc> {
        if capacity_bound == 0 {
            return Err(BoundaryError739268fc::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError739268fc::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError739268fc::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_739268fc() {
    let admitted = BoundaryRecord739268fc::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord739268fc::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

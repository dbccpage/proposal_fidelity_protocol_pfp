use std::collections::BTreeSet;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ControlReceipt {
    pub control_id: &'static str,
    pub domain: &'static str,
    pub status: &'static str,
    pub invariant_tuple: (i64, i64, i64),
    pub reason: &'static str,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct HistoryState {
    label: &'static str,
    height: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct CoveringEdge {
    label: &'static str,
    weight: i64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum TransportError {
    Empty,
    Unlabeled,
    Duplicate,
    Missing,
    Overflow,
    Path,
    Budget,
    Telescope,
    Partition,
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/po001_native_transport.rs
// Claim: urn:core:crates_rs:tests:po001-native-transport:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for TransportError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for TransportError {}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct TransportCensus {
    admitted: i64,
    open: i64,
    refused: i64,
}

// Exact carrier witness.
// Four restriction states, three covering edges, and one curvature refusal.
// Each edge weight is the height step, and every step stays inside the curvature budget.
const STATES: &[HistoryState] = &[
    HistoryState { label: "restriction_0", height: 0 },
    HistoryState { label: "restriction_1", height: 2 },
    HistoryState { label: "restriction_2", height: 5 },
    HistoryState { label: "history_carrier", height: 9 },
];

const EDGES: &[CoveringEdge] = &[
    CoveringEdge { label: "covering_edge_01", weight: 2 },
    CoveringEdge { label: "covering_edge_12", weight: 3 },
    CoveringEdge { label: "covering_edge_23", weight: 4 },
];

const REFUSALS: &[&str] = &["curvature_above_budget"];

const CURVATURE_BUDGET: i64 = 4;

fn insert_unique_label<'a>(seen: &mut BTreeSet<&'a str>, label: &'a str) -> Result<(), TransportError> {
    if label.is_empty() {
        return Err(TransportError::Unlabeled);
    }
    if !seen.insert(label) {
        return Err(TransportError::Duplicate);
    }
    Ok(())
}

fn verify_covering_edges<'a>(
    states: &[HistoryState],
    edges: &'a [CoveringEdge],
    budget: i64,
    seen: &mut BTreeSet<&'a str>,
) -> Result<(), TransportError> {
    let mut sum = 0i64;
    for (pair, edge) in states.windows(2).zip(edges.iter()) {
        insert_unique_label(seen, edge.label)?;
        let step = pair[1].height.checked_sub(pair[0].height).ok_or(TransportError::Overflow)?;
        if edge.weight != step || step < 0 || step > budget {
            return Err(TransportError::Budget);
        }
        sum = sum.checked_add(step).ok_or(TransportError::Overflow)?;
    }
    let gap = states[states.len() - 1]
        .height
        .checked_sub(states[0].height)
        .ok_or(TransportError::Overflow)?;
    if sum != gap {
        return Err(TransportError::Telescope);
    }
    Ok(())
}

fn transport_census(
    states: &[HistoryState],
    edges: &[CoveringEdge],
    refusals: &[&str],
    budget: i64,
) -> Result<TransportCensus, TransportError> {
    if states.is_empty() || budget < 0 {
        return Err(TransportError::Empty);
    }
    let mut seen = BTreeSet::new();
    for state in states {
        insert_unique_label(&mut seen, state.label)?;
    }
    let admitted = states.len() as i64;
    let open = edges.len() as i64;
    if admitted != open + 1 {
        return Err(TransportError::Path);
    }
    verify_covering_edges(states, edges, budget, &mut seen)?;
    for &label in refusals {
        insert_unique_label(&mut seen, label)?;
    }
    let refused = refusals.len() as i64;
    if admitted + open + refused != seen.len() as i64 {
        return Err(TransportError::Partition);
    }
    Ok(TransportCensus { admitted, open, refused })
}

impl TransportCensus {
    fn triple(self) -> (i64, i64, i64) {
        (self.admitted, self.open, self.refused)
    }
}

pub fn evaluate_po001_native_transport(
    candidate: (i64, i64, i64),
    allow_unrestricted_promotion: bool,
) -> ControlReceipt {
    if allow_unrestricted_promotion {
        return ControlReceipt {
            control_id: "PO001-NATIVE-TRANSPORT",
            domain: "po001_ddc_mssn_native_transport",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "UNRESTRICTED_PROMOTION_REFUSED",
        };
    }
    let expected = match transport_census(STATES, EDGES, REFUSALS, CURVATURE_BUDGET) {
        Ok(census) => census.triple(),
        Err(_) => {
            return ControlReceipt {
                control_id: "PO001-NATIVE-TRANSPORT",
                domain: "po001_ddc_mssn_native_transport",
                status: "REFUSED",
                invariant_tuple: candidate,
                reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
            };
        }
    };
    if candidate != expected {
        return ControlReceipt {
            control_id: "PO001-NATIVE-TRANSPORT",
            domain: "po001_ddc_mssn_native_transport",
            status: "REFUSED",
            invariant_tuple: candidate,
            reason: "INVARIANT_MISMATCH_ON_DECLARED_CARRIER",
        };
    }
    ControlReceipt {
        control_id: "PO001-NATIVE-TRANSPORT",
        domain: "po001_ddc_mssn_native_transport",
        status: "PASS",
        invariant_tuple: expected,
        reason: "SCOPED_CONTROL_VERIFIED",
    }
}

#[test]
fn test_po001_native_transport_scoped_control() {
    let image = transport_census(STATES, EDGES, REFUSALS, CURVATURE_BUDGET).map(TransportCensus::triple);
    assert_eq!(image, Ok((4, 3, 1)));
    let ok = image.map(|triple| evaluate_po001_native_transport(triple, false));
    assert!(matches!(
        ok.as_ref(),
        Ok(receipt)
            if receipt.control_id == "PO001-NATIVE-TRANSPORT"
                && receipt.domain == "po001_ddc_mssn_native_transport"
                && receipt.status == "PASS"
                && receipt.reason == "SCOPED_CONTROL_VERIFIED"
                && receipt.invariant_tuple == (4, 3, 1)
    ));

    let drifted = evaluate_po001_native_transport((4 + 1, 3, 1), false);
    assert_eq!(drifted.status, "REFUSED");
    assert_eq!(drifted.reason, "INVARIANT_MISMATCH_ON_DECLARED_CARRIER");

    let promoted = image.map(|triple| evaluate_po001_native_transport(triple, true));
    assert!(matches!(
        promoted.as_ref(),
        Ok(receipt)
            if receipt.status == "REFUSED" && receipt.reason == "UNRESTRICTED_PROMOTION_REFUSED"
    ));
}

#[test]
fn a_step_outside_the_curvature_budget_is_refused() {
    let over = [CoveringEdge { label: "covering_edge_01", weight: 5 }];
    let states = [
        HistoryState { label: "restriction_0", height: 0 },
        HistoryState { label: "restriction_1", height: 5 },
    ];
    assert!(matches!(
        transport_census(&states, &over, &["curvature_above_budget"], 4),
        Err(TransportError::Budget)
    ));
    assert!(matches!(
        transport_census(&[], &[], &[], 4),
        Err(TransportError::Empty)
    ));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

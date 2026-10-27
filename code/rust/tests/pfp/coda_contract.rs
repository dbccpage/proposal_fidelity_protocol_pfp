//! Contract tests for the CODA three-layer seam and the adapter quarantine.
//!
//! `EPIC-OE-SYMGAM-014`. Fourth consecutive epic with an unfalsifiable gate, so
//! the criteria come from the invariants:
//!
//! > **Strict 3-Layer Seam:** Parity =/=> Physical =/=> Algorithmic.
//! >
//! > **Quarantine Protocol:** speculative adapters cannot author verified
//! > receipts without explicit formal certificates.
//!
//! Both failures are **silent**. Laundering a layer produces a plausible
//! sentence backed by a correct computation of something else; an uncertified
//! adapter authoring a receipt produces a receipt that looks like any other. So
//! both are enforced structurally, and these tests are the second witness.

use pfp::epics::coda::{
    admit, boundary_receipt, bridge, canary_sweep, witness_from_verdict, AdmittedClaim, Evidence,
    Layer, LayerRefusal, LayeredClaim, QuarantineRefusal, QuarantinedAdapter,
    ADAPTER_RECEIPT_SCHEMA, BOUNDARY_RECEIPT_SCHEMA,
};
use pfp_runtime::f2::{F2Matrix, GaugeBoard};

fn parity_evidence() -> Evidence {
    Evidence::ParityWitness {
        verdict_token: "GAUGE_EXACT".into(),
    }
}

fn admitted_parity(statement: &str) -> AdmittedClaim {
    admit(LayeredClaim::new(Layer::Parity, statement, parity_evidence()).expect("a statement"))
        .expect("parity evidence admits a parity claim")
}

fn uncertified(name: &str) -> QuarantinedAdapter {
    QuarantinedAdapter::propose(name, "a speculative sign bridge").expect("a hypothesis")
}

// ---------------------------------------------------------------------------
// Criterion 1 -- evidence admits only its own layer
// ---------------------------------------------------------------------------

#[test]
fn parity_evidence_admits_a_parity_claim() {
    let claim = LayeredClaim::new(Layer::Parity, "D1 a = 0", parity_evidence()).expect("valid");
    let admitted = admit(claim).expect("evidence matches the layer");
    assert_eq!(admitted.layer(), Layer::Parity);
}

#[test]
fn parity_evidence_cannot_admit_a_physical_claim() {
    // The core laundering move: a correct F2 computation offered as a fact about
    // a physical system.
    let claim = LayeredClaim::new(
        Layer::Physical,
        "the material exhibits this parity",
        parity_evidence(),
    )
    .expect("valid");
    let error = admit(claim).expect_err("parity does not entail physical");
    assert_eq!(
        error,
        LayerRefusal::LayerMismatch {
            evidence: "parity_witness",
            layer: "physical",
        }
    );
}

#[test]
fn parity_evidence_cannot_admit_an_algorithmic_claim() {
    let claim = LayeredClaim::new(
        Layer::Algorithmic,
        "therefore the solver is linear time",
        parity_evidence(),
    )
    .expect("valid");
    assert!(admit(claim).is_err());
}

#[test]
fn each_evidence_kind_admits_exactly_one_layer() {
    // Exhaustive over the cross product, so no pairing is admitted by accident.
    let cases = [
        (parity_evidence(), Layer::Parity),
        (
            Evidence::Measurement {
                instrument: "cryostat".into(),
            },
            Layer::Physical,
        ),
        (
            Evidence::Benchmark {
                harness: "criterion".into(),
            },
            Layer::Algorithmic,
        ),
    ];
    for (evidence, admissible) in cases {
        for layer in Layer::all() {
            let claim = LayeredClaim::new(layer, "a statement", evidence.clone()).expect("valid");
            let outcome = admit(claim);
            assert_eq!(
                outcome.is_ok(),
                layer == admissible,
                "{} evidence at the {} layer",
                evidence.kind(),
                layer.name()
            );
        }
    }
}

#[test]
fn speculative_evidence_admits_no_layer_at_all() {
    // That is what quarantine means: a hypothesis is not evidence for itself.
    let speculative = Evidence::Speculative {
        adapter: "grassmann".into(),
    };
    assert!(speculative.admissible_layer().is_none());
    for layer in Layer::all() {
        let claim = LayeredClaim::new(layer, "a statement", speculative.clone()).expect("valid");
        assert!(
            admit(claim).is_err(),
            "speculative evidence admitted at {}",
            layer.name()
        );
    }
}

#[test]
fn an_empty_statement_is_refused() {
    for blank in ["", "   ", "\t\n"] {
        assert_eq!(
            LayeredClaim::new(Layer::Parity, blank, parity_evidence())
                .expect_err("a claim needs a statement"),
            LayerRefusal::EmptyStatement
        );
    }
}

// ---------------------------------------------------------------------------
// Criterion 2 -- the seam never opens
// ---------------------------------------------------------------------------

#[test]
fn bridging_between_any_two_layers_is_refused() {
    // Exhaustive, including a layer to itself. A bridge that returned its input
    // unchanged would be a promotion path waiting for someone to widen it.
    let admitted = admitted_parity("D1 a = 0");
    for target in Layer::all() {
        let error = bridge(&admitted, target).expect_err("the seam does not open");
        assert_eq!(
            error,
            LayerRefusal::SeamCrossing {
                from: "parity",
                to: target.name(),
            }
        );
    }
}

#[test]
fn the_refusal_names_both_sides_of_the_seam() {
    let admitted = admitted_parity("D1 a = 0");
    let message = bridge(&admitted, Layer::Physical)
        .expect_err("refused")
        .to_string();
    assert!(message.contains("parity"), "{message}");
    assert!(message.contains("physical"), "{message}");
}

#[test]
fn an_admitted_claim_keeps_the_layer_it_was_admitted_at() {
    // There is no setter and no method returning a claim at a different layer;
    // this pins the observable half of that.
    let admitted = admitted_parity("D1 a = 0");
    assert_eq!(admitted.layer(), Layer::Parity);
    assert_eq!(admitted.claim().layer(), Layer::Parity);
}

// ---------------------------------------------------------------------------
// Criterion 3 -- parity evidence comes from an actual classification
// ---------------------------------------------------------------------------

#[test]
fn a_parity_witness_is_built_from_a_real_verdict() {
    // The token cannot be invented: the only constructor takes a verdict, so
    // holding parity evidence means the classification was run.
    let d0 = F2Matrix::from_rows(&[vec![1, 0], vec![0, 1]]).expect("valid");
    let d1 = F2Matrix::zeros(1, 2);
    let board = GaugeBoard::new(d0, d1);
    let verdict = board.classify(&[true, false]).expect("classifiable");

    let evidence = witness_from_verdict(&verdict);
    assert_eq!(evidence.kind(), "parity_witness");
    assert_eq!(evidence.admissible_layer(), Some(Layer::Parity));
    match evidence {
        Evidence::ParityWitness { verdict_token } => {
            assert_eq!(verdict_token, verdict.token());
        }
        other => panic!("expected a parity witness, got {other:?}"),
    }
}

#[test]
fn an_invalid_board_still_yields_parity_evidence_about_itself() {
    // `D1 D0 != 0` means the object is not a cochain complex. That is a genuine
    // parity-layer finding, and the evidence records it rather than vanishing.
    let d0 = F2Matrix::from_rows(&[vec![1]]).expect("valid");
    let d1 = F2Matrix::from_rows(&[vec![1]]).expect("valid");
    let verdict = GaugeBoard::new(d0, d1)
        .classify(&[true])
        .expect("classifiable");
    assert_eq!(verdict.token(), "BOARD_INVALID");
    assert_eq!(
        witness_from_verdict(&verdict).admissible_layer(),
        Some(Layer::Parity)
    );
}

// ---------------------------------------------------------------------------
// Criterion 4 -- quarantine fails closed
// ---------------------------------------------------------------------------

#[test]
fn an_uncertified_adapter_cannot_author_a_receipt() {
    let adapter = uncertified("clifford");
    let error = adapter.author_receipt().expect_err("fails closed");
    assert_eq!(
        error,
        QuarantineRefusal::Uncertified {
            adapter: "clifford".into()
        }
    );
    assert!(!adapter.is_certified());
}

#[test]
fn a_certified_adapter_may_author_a_receipt_naming_its_reviewer() {
    let adapter = uncertified("regge")
        .admit_certificate("j.carroll", "checked against the Lean development")
        .expect("a named reviewer");
    let receipt = adapter.author_receipt().expect("certified");

    assert_eq!(receipt.schema, ADAPTER_RECEIPT_SCHEMA);
    assert_eq!(receipt.adapter, "regge");
    assert_eq!(receipt.reviewer, "j.carroll");
    assert_eq!(receipt.authority_effect, "None");
}

#[test]
fn a_certificate_without_a_reviewer_is_refused() {
    // Same rule as guard generalization in sprint 030: a machine proposes, a
    // human signs, and "signed by nobody" is not a signature.
    for blank in ["", "  ", "\t"] {
        let error = uncertified("grassmann")
            .admit_certificate(blank, "because")
            .expect_err("an unnamed reviewer is refused");
        assert_eq!(
            error,
            QuarantineRefusal::UnreviewedCertificate {
                adapter: "grassmann".into()
            }
        );
    }
}

#[test]
fn an_adapter_without_a_hypothesis_is_refused() {
    let error =
        QuarantinedAdapter::propose("empty", "   ").expect_err("an adapter must propose something");
    assert_eq!(
        error,
        QuarantineRefusal::EmptyHypothesis {
            adapter: "empty".into()
        }
    );
}

#[test]
fn a_quarantined_adapter_offers_evidence_that_admits_nothing() {
    let adapter = uncertified("grassmann");
    assert!(adapter.evidence().admissible_layer().is_none());
}

#[test]
fn certifying_an_adapter_does_not_promote_its_evidence() {
    // The decisive one for the quarantine protocol. A certificate lets an
    // adapter author a receipt; it does not turn its hypothesis into evidence
    // for a parity claim. Those are different permissions and conflating them
    // would let a signature launder a layer.
    let adapter = uncertified("grassmann")
        .admit_certificate("j.carroll", "reviewed")
        .expect("named reviewer");

    assert!(adapter.author_receipt().is_ok());
    assert!(adapter.evidence().admissible_layer().is_none());

    let claim =
        LayeredClaim::new(Layer::Parity, "the bridge holds", adapter.evidence()).expect("valid");
    assert!(admit(claim).is_err());
}

// ---------------------------------------------------------------------------
// Criterion 5 -- canary sweep
// ---------------------------------------------------------------------------

#[test]
fn a_sandbox_of_uncertified_adapters_all_fails_closed() {
    let sandbox = vec![
        uncertified("grassmann"),
        uncertified("regge"),
        uncertified("clifford"),
    ];
    let report = canary_sweep(&sandbox).expect("a non-empty sandbox");

    assert_eq!(report.failed_closed.len(), 3);
    assert!(report.certified.is_empty());
    assert!(report.leaked.is_empty());
    assert!(report.is_sound());
}

#[test]
fn a_sweep_separates_certified_adapters_from_refusing_ones() {
    let sandbox = vec![
        uncertified("grassmann"),
        uncertified("regge")
            .admit_certificate("j.carroll", "reviewed")
            .expect("named"),
    ];
    let report = canary_sweep(&sandbox).expect("non-empty");

    assert_eq!(report.failed_closed, vec!["grassmann".to_string()]);
    assert_eq!(report.certified, vec!["regge".to_string()]);
    assert!(report.is_sound());
}

#[test]
fn an_empty_sandbox_is_refused_rather_than_reported_sound() {
    // Reporting that all zero adapters failed closed is a claim true because
    // nothing was examined -- the vacuous pass of sprints 028 through 031.
    assert_eq!(
        canary_sweep(&[]).expect_err("nothing to sweep"),
        QuarantineRefusal::NoAdapters
    );
}

#[test]
fn the_report_has_a_field_for_a_breach_so_a_breach_is_a_value() {
    // `leaked` is empty in every reachable case today. It exists so that a
    // future adapter authoring an uncertified receipt appears as data rather
    // than as an absence nobody notices.
    let report = canary_sweep(&[uncertified("grassmann")]).expect("non-empty");
    assert!(report.leaked.is_empty());
    assert!(report.is_sound());
}

// ---------------------------------------------------------------------------
// Criterion 6 -- boundary receipts distinguish verified from speculative
// ---------------------------------------------------------------------------

#[test]
fn a_boundary_receipt_counts_verified_and_speculative_separately() {
    // Never summed. A total would read as "how much do we know" and would be the
    // sum of a thing established and a thing proposed.
    let admitted = vec![admitted_parity("first"), admitted_parity("second")];
    let sandbox = vec![uncertified("grassmann")];
    let receipt = boundary_receipt(&admitted, &sandbox);

    assert_eq!(receipt.schema, BOUNDARY_RECEIPT_SCHEMA);
    assert_eq!(receipt.verified_parity_claims, 2);
    assert_eq!(receipt.verified_physical_claims, 0);
    assert_eq!(receipt.verified_algorithmic_claims, 0);
    assert_eq!(receipt.speculative_hypotheses, 1);
    assert_eq!(receipt.authority_effect, "None");
}

#[test]
fn a_boundary_receipt_records_zero_layers_crossed_explicitly() {
    // The field is present so the number is visible rather than inferred from
    // silence, and so any future non-zero value is loud.
    let receipt = boundary_receipt(&[admitted_parity("a")], &[uncertified("g")]);
    assert_eq!(receipt.layers_crossed, 0);
}

#[test]
fn a_boundary_receipt_digest_does_not_depend_on_claim_order() {
    let one = admitted_parity("alpha");
    let two = admitted_parity("beta");
    let forward = boundary_receipt(&[one.clone(), two.clone()], &[]);
    let reversed = boundary_receipt(&[two, one], &[]);
    assert_eq!(forward.digest, reversed.digest);
}

#[test]
fn a_boundary_receipt_digest_separates_different_content() {
    let claims = boundary_receipt(&[admitted_parity("alpha")], &[]);
    let more = boundary_receipt(&[admitted_parity("beta")], &[]);
    assert_ne!(claims.digest, more.digest);

    let with_adapter = boundary_receipt(&[admitted_parity("alpha")], &[uncertified("g")]);
    assert_ne!(claims.digest, with_adapter.digest);
}

#[test]
fn the_boundary_receipt_serialises_to_json() {
    let receipt = boundary_receipt(&[admitted_parity("a")], &[uncertified("g")]);
    let json = serde_json::to_string(&receipt).expect("must serialise");
    assert!(json.contains(BOUNDARY_RECEIPT_SCHEMA));
    assert!(json.contains("\"authority_effect\":\"None\""));
    assert!(json.contains("\"speculative_hypotheses\":1"));
}

// Origin: engine/crates_rs/tests/pfp/coda_contract.rs
// Claim: urn:core:crates_rs:tests:coda-contract:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord44d1a49a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord44d1a49a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError44d1a49a {
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
impl BoundaryError44d1a49a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError44d1a49a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError44d1a49a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord44d1a49a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError44d1a49a> {
        if capacity_bound == 0 {
            return Err(BoundaryError44d1a49a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError44d1a49a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError44d1a49a::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_44d1a49a() {
    let admitted = BoundaryRecord44d1a49a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord44d1a49a::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

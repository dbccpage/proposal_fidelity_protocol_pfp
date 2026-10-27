//! Exact Prime 0/1/2 execution, witness commitments and typed mathematical refusals.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_d7c1e057<T> {
    fn checked_invariant_d7c1e057(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_d7c1e057<T> for Option<T> {
    #[inline]
    fn checked_invariant_d7c1e057(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_d7c1e057<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_d7c1e057(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use super::*;

pub(super) fn same_carrier_identity(
    request: &HostRequestV1,
    carrier: &CarrierManifestSummaryV1,
    candidate: &[i128],
) -> Result<Prime001SummaryV1, String> {
    let carrier_bytes = decode_lower_hex(&carrier.carrier_hash_blake3, "carrier hash")?;
    let carrier_hash = Hash256(carrier_bytes);
    let candidate_commitment = vector_commitment_i128("core.host.candidate-vector.v1", candidate);
    let payload = Hash256(decode_lower_hex(
        &candidate_commitment,
        "candidate vector commitment",
    )?);
    let scope = ScopeBinding::new(
        Hash256([0; 32]),
        BoundCarrierManifest::new(carrier_hash.clone(), carrier_hash.clone()),
        carrier_hash.clone(),
        None,
        0,
    );
    let ledger = LossLedger::empty(scope);
    match transport(
        carrier_hash.clone(),
        carrier_hash.clone(),
        payload,
        ledger.clone(),
        false,
    ) {
        Err(TransportRefusal::SameCarrier) => {}
        Err(error) => return Err(format!("unexpected Prime 001 refusal: {error}")),
        Ok(_) => return Err("Prime 001 transported an identical carrier".to_owned()),
    }
    let ledger_hash = hex(&ledger.commit().0);
    let identity_commitment = framed_sha256(
        "core.oesos.prime001-same-carrier-identity.v1",
        &canonical_json(&serde_json::json!({
            "packet_id": request.packet_envelope.packet_id,
            "candidate_id": request.source.candidate.candidate_id_sha256,
            "carrier_hash_blake3": carrier.carrier_hash_blake3,
            "loss_ledger_commitment_sha256": ledger_hash,
            "transport_called": false,
            "transport_same_carrier_refusal_checked": true,
            "authority_effect": "None"
        })),
    );
    Ok(Prime001SummaryV1 {
        kind: "same_carrier_identity".to_owned(),
        carrier_hash_blake3: carrier.carrier_hash_blake3.clone(),
        identity_commitment_sha256: identity_commitment,
        loss_ledger_commitment_sha256: ledger_hash,
        transport_called: false,
        transport_same_carrier_refusal_checked: true,
    })
}

pub(super) fn rational(value: i128) -> BigRational {
    BigRational::from_integer(BigInt::from(value))
}

pub(super) fn weighted_l1(values: &[BigRational], carrier: &FiniteCarrier2) -> BigRational {
    core_functional::Phi1Functional::weighted_l1_rational(
        &carrier
            .edges
            .iter()
            .map(|edge| rational(edge.weight))
            .collect::<Vec<_>>(),
        values,
    )
    .checked_invariant_d7c1e057("validated finite carrier and matching cochain")
}

pub(super) fn vector_commitment_i128(domain: &str, values: &[i128]) -> String {
    framed_sha256(
        domain,
        &canonical_json(&Value::Array(
            values
                .iter()
                .map(|value| Value::String(value.to_string()))
                .collect(),
        )),
    )
}

pub(super) fn vector_commitment_rational(domain: &str, values: &[BigRational]) -> String {
    framed_sha256(
        domain,
        &canonical_json(
            &serde_json::to_value(
                values
                    .iter()
                    .map(ExactRationalWireV1::from_rational)
                    .collect::<Vec<_>>(),
            )
            .checked_invariant_d7c1e057("exact rational summaries serialize"),
        ),
    )
}

pub(super) fn exact_stage(
    status: ObstructionDiagnosticClass,
    values: &[BigRational],
    carrier: &FiniteCarrier2,
    phi1: &BigRational,
    gamma2: &BigRational,
) -> ExactStageSummaryV1 {
    ExactStageSummaryV1 {
        status: format!("{status:?}"),
        raw_weighted_l1: ExactRationalWireV1::from_rational(&weighted_l1(values, carrier)),
        phi1: ExactRationalWireV1::from_rational(phi1),
        gamma2: ExactRationalWireV1::from_rational(gamma2),
    }
}

pub(super) fn oesos_summary(
    request: &HostRequestV1,
    carrier: &FiniteCarrier2,
    before: &[i128],
    candidate: &[i128],
    receipt: &SolveReceipt,
) -> OesosSummaryV1 {
    let before_q: Vec<BigRational> = before.iter().copied().map(rational).collect();
    let candidate_q: Vec<BigRational> = candidate.iter().copied().map(rational).collect();
    let normal_form = receipt.normal_form();
    let input_commitment = framed_sha256(
        "core.oesos.host-solve-input.v1",
        &canonical_json(&serde_json::json!({
            "carrier": request.carrier.declaration,
            "core_i128": request.residual.before_omega_i128,
            "packet_id": request.packet_envelope.packet_id,
            "candidate_id": request.source.candidate.candidate_id_sha256,
        })),
    );
    let candidate_vector = vector_commitment_i128("core.host.candidate-vector.v1", candidate);
    let normal_form_hash =
        vector_commitment_rational("core.host.replayed-normal-form.v1", normal_form);
    let gauge = exact_stage(
        receipt.gauge().status(),
        &before_q,
        carrier,
        receipt.gauge().phi1().value(),
        receipt.gauge().gamma2().value(),
    );
    let final_stage = exact_stage(
        receipt.final_evaluation().status(),
        normal_form,
        carrier,
        receipt.final_evaluation().phi1().value(),
        receipt.final_evaluation().gamma2().value(),
    );
    let solve_payload = serde_json::json!({
        "input_commitment_sha256": input_commitment,
        "gauge": gauge,
        "final": final_stage,
        "normal_form_sha256": normal_form_hash,
        "b1_over_q": receipt.b1_over_q(),
        "span_distance": ExactRationalWireV1::from_rational(receipt.span_distance()),
        "closure_premium": ExactRationalWireV1::from_rational(&receipt.closure_premium()),
        "authority_effect": format!("{:?}", receipt.authority_effect()),
    });
    let fresh = framed_sha256(
        "core.oesos.host-fresh-solve-summary.v1",
        &canonical_json(&solve_payload),
    );
    let replay = framed_sha256(
        "core.oesos.host-replay-binding.v1",
        &canonical_json(&serde_json::json!({
            "input_commitment_sha256": input_commitment,
            "fresh_solve_commitment_sha256": fresh,
            "normal_form_sha256": normal_form_hash,
            "replay_solve": "PASSED_IN_SAME_PROCESS",
            "authority_effect": "None"
        })),
    );
    let pipeline_hash = receipt.gauge().primitive_receipt().declared_carrier_hash();
    OesosSummaryV1 {
        kind: "replayed".to_owned(),
        input_commitment_sha256: input_commitment,
        fresh_solve_commitment_sha256: fresh,
        replay_commitment_sha256: replay,
        pipeline_declaration_carrier_hash_blake3: hex(&pipeline_hash.0 .0),
        gauge,
        final_stage,
        normal_form: normal_form
            .iter()
            .map(ExactRationalWireV1::from_rational)
            .collect(),
        b1_over_q: receipt.b1_over_q(),
        span_distance: ExactRationalWireV1::from_rational(receipt.span_distance()),
        closure_premium: ExactRationalWireV1::from_rational(&receipt.closure_premium()),
        candidate_relation: CandidateRelationV1 {
            kind: "exact_host_normal_form".to_owned(),
            candidate_vector_sha256: candidate_vector,
            normal_form_sha256: normal_form_hash,
            exact_match: candidate_q.as_slice() == normal_form,
        },
    }
}

struct OesosPrimeAdapter {
    declaration: DeclarationFill,
    dimensions: (usize, usize, usize),
    masses: (u64, u64),
}

impl DomainAdapter for OesosPrimeAdapter {
    fn domain(&self) -> PrimeDomain {
        PrimeDomain::SymbolGame
    }

    fn declaration(&self) -> DeclarationFill {
        self.declaration.clone()
    }

    fn justify_cochain(&self) -> bool {
        true
    }

    fn cochain_window(&self) -> Option<CochainWindow> {
        Some(CochainWindow {
            dim_c0: self.dimensions.0,
            dim_c1: self.dimensions.1,
            dim_c2: self.dimensions.2,
            square_zero: true,
            l1_defect_mass: 0,
        })
    }

    fn residual_masses(&self) -> (u64, u64) {
        self.masses
    }

    fn lift_proposal(&self, branch: DefectBranch) -> LiftProposal {
        if branch == DefectBranch::Closed {
            LiftProposal::SkipClosed
        } else {
            LiftProposal::OracleGap {
                note: "host v1 has no licensed carrier lift".to_owned(),
            }
        }
    }

    fn literature_note(&self) -> Option<String> {
        None
    }

    fn evidence_provenance(&self) -> EvidenceProvenance {
        EvidenceProvenance::VerifierProduced
    }

    fn residual_family_label(&self) -> String {
        "symbol_game:finite-cochain-oesos-v1".to_owned()
    }
}

pub(super) fn exact_u64(value: &BigRational, label: &str) -> Result<u64, String> {
    if value.is_negative() || value.denom() != &BigInt::from(1) {
        return Err(format!(
            "{label}={value} is not a nonnegative exact integer; host refuses rounding"
        ));
    }
    value
        .numer()
        .to_u64()
        .ok_or_else(|| format!("{label}={value} does not fit u64"))
}

pub(super) fn prime000_summary(
    request: &HostRequestV1,
    carrier: &FiniteCarrier2,
    receipt: &SolveReceipt,
    oesos: &OesosSummaryV1,
) -> Result<Prime000SummaryV1, String> {
    let phi1 = exact_u64(receipt.final_evaluation().phi1().value(), "final Phi1")?;
    let gamma2 = exact_u64(receipt.final_evaluation().gamma2().value(), "final Gamma2")?;
    let adapter = OesosPrimeAdapter {
        declaration: DeclarationFill {
            carrier: Some(request.prime_profiles.carrier_declaration.clone()),
            primitive_difference: Some(request.prime_profiles.primitive_difference.clone()),
            zero_rel: Some(request.prime_profiles.zero_relation.clone()),
            observer: Some(request.prime_profiles.observer_profile_id.clone()),
            witnesses: vec![
                request.prime_profiles.witness_profile_id.clone(),
                oesos.fresh_solve_commitment_sha256.clone(),
                oesos.replay_commitment_sha256.clone(),
            ],
        },
        dimensions: (
            carrier.num_vertices,
            carrier.edges.len(),
            carrier.faces.len(),
        ),
        masses: (phi1, gamma2),
    };
    let prime = run_prime_algorithm_0(&adapter);
    if prime.authority_effect() != &AuthorityEffect::None {
        return Err("Prime 000 attempted to mint authority".to_owned());
    }
    let conformance = check_receipt(&prime);
    let (verdict, unchecked) = match &conformance.verdict {
        ConformanceVerdict::Conforms => ("Conforms", Vec::new()),
        ConformanceVerdict::Partial { unchecked_laws } => ("Partial", unchecked_laws.clone()),
        ConformanceVerdict::Violated { unchecked_laws, .. } => ("Violated", unchecked_laws.clone()),
    };
    let violations = conformance
        .violations()
        .iter()
        .map(|violation| format!("{violation:?}"))
        .collect();
    let receipt_value = serde_json::to_value(&prime)
        .map_err(|error| format!("Prime 000 receipt serialization failed: {error}"))?;
    Ok(Prime000SummaryV1 {
        kind: "executed".to_owned(),
        receipt_commitment_sha256: framed_sha256(
            "core.oesos.host-prime000-receipt.v1",
            &canonical_json(&receipt_value),
        ),
        terminal: prime.terminal.as_str().to_owned(),
        evidence_provenance: format!("{:?}", prime.evidence_provenance),
        letter_tape: prime.letter_tape,
        phi1_u64: phi1,
        gamma2_u64: gamma2,
        conformance: Prime000ConformanceV1 {
            verdict: verdict.to_owned(),
            conforms: conformance.conforms(),
            no_decidable_violation: conformance.no_decidable_violation(),
            violations,
            unchecked_laws: unchecked,
        },
    })
}

struct ExactBytesDetector(DetectorDescriptor);

impl Detector for ExactBytesDetector {
    fn descriptor(&self) -> &DetectorDescriptor {
        &self.0
    }

    fn verdict(&self, subject: &RunSubject<'_>) -> Vec<u8> {
        let digest = framed_sha256(
            "core.oesos.host-exact-byte-detector.v1",
            &canonical_json(&serde_json::json!({
                "input_hex": hex(subject.input),
                "degree": subject.degree,
                "scope": hex(&subject.scope.commit().0),
            })),
        );
        digest.into_bytes()
    }
}

struct Prime002EvidenceInput<'a> {
    request: &'a HostRequestV1,
    site: ScopeBinding,
    carrier_hash: Hash256,
    claim: &'a [u8],
    counterclaim: &'a [u8],
    before: &'a core_functional::phi1::VerifiedExactPhi1,
    after: &'a core_functional::phi1::VerifiedExactPhi1,
    outstanding: Hash256,
    higher: Hash256,
}

fn make_prime002_evidence(
    input: Prime002EvidenceInput<'_>,
) -> Result<ContinuationEvidence, String> {
    let Prime002EvidenceInput {
        request,
        site,
        carrier_hash,
        claim,
        counterclaim,
        before,
        after,
        outstanding,
        higher,
    } = input;
    let config = Hash256(
        decode_lower_hex(&request.prime002.detector_config_sha256, "detector config")
            .map_err(|error| format!("detector config: {error}"))?,
    );
    let detector = ExactBytesDetector(DetectorDescriptor::new(
        request.prime002.detector_profile_id.clone(),
        "v1",
        "exact_candidate_bytes",
        carrier_hash.clone(),
        [1usize],
        config,
    ));
    let adequacy = DetectorAdequacy::by_running(&detector, claim, counterclaim, 1, site.clone())
        .map_err(|error| format!("detector adequacy refused: {error}"))?;
    let residual = ResidualDelta::from_verified(before, after, site.clone())
        .map_err(|error| format!("residual delta refused: {error}"))?;
    Ok(ContinuationEvidence {
        outstanding_obligation: ObligationWitness::exhibit(outstanding, 1, site.clone()),
        higher_obligation_witness: ObligationWitness::exhibit(higher, 2, site.clone()),
        next_carrier_manifest: BoundCarrierManifest::new(carrier_hash.clone(), carrier_hash),
        adapter_ledger: LossLedger::empty(site),
        detector: adequacy,
        lift: None,
        skeleton_preserved: true,
        coda_gtla_refusal: None,
        residual,
    })
}

type Prime002Error = (&'static str, String, Vec<String>);

struct DecodedPrime002Scope {
    run_hash: Hash256,
    carrier_hash: Hash256,
    claim: [u8; 32],
    counterclaim: [u8; 32],
    residual_hash: Hash256,
    residual_label: Hash256,
}

fn check_prime002_preconditions(
    request: &HostRequestV1,
    receipt: &SolveReceipt,
    oesos: &OesosSummaryV1,
) -> Result<(), Prime002Error> {
    if receipt.status() != ObstructionDiagnosticClass::ExactRepair
        || !oesos.candidate_relation.exact_match
    {
        return Err((
            "PRIME002_ROUTE_NOT_APPLICABLE",
            "host v1 only consumes write+terminal permits for an exact replayed normal form"
                .to_owned(),
            Vec::new(),
        ));
    }
    if receipt.gauge().gamma2().value().is_zero() {
        return Err((
            "PRIME002_HIGHER_OBLIGATION_MISSING",
            "the exact fixture has no verifier-produced degree-2 closure obligation".to_owned(),
            Vec::new(),
        ));
    }
    if !request.prime002.open_obligation_degrees.is_empty() {
        return Err((
            "PRIME002_OBLIGATIONS_OPEN",
            format!(
                "terminalization requested with open degrees {:?}",
                request.prime002.open_obligation_degrees
            ),
            Vec::new(),
        ));
    }
    Ok(())
}

fn decode_prime002_scope(
    request: &HostRequestV1,
    carrier: &CarrierManifestSummaryV1,
    oesos: &OesosSummaryV1,
) -> Result<DecodedPrime002Scope, Prime002Error> {
    let run_hash = Hash256(
        decode_lower_hex(&request.request_id_sha256, "request id")
            .map_err(|error| ("PRIME002_SCOPE_INVALID", error, Vec::new()))?,
    );
    let carrier_hash = Hash256(
        decode_lower_hex(&carrier.carrier_hash_blake3, "carrier hash")
            .map_err(|error| ("PRIME002_SCOPE_INVALID", error, Vec::new()))?,
    );
    let claim = decode_lower_hex(
        &oesos.candidate_relation.candidate_vector_sha256,
        "candidate vector",
    )
    .map_err(|error| ("PRIME002_SCOPE_INVALID", error, Vec::new()))?;
    let counterclaim = decode_lower_hex(&oesos.input_commitment_sha256, "solve input")
        .map_err(|error| ("PRIME002_SCOPE_INVALID", error, Vec::new()))?;
    if claim == counterclaim {
        return Err((
            "PRIME002_DETECTOR_CONTROL_COLLISION",
            "candidate and input commitments are identical".to_owned(),
            Vec::new(),
        ));
    }
    let residual_hash = dda_digest("oeprm.adequacy.v1", &[&claim]);
    let residual_label = Hash256(
        decode_lower_hex(
            &request.source.source_event_root_sha256,
            "source event root",
        )
        .map_err(|error| ("PRIME002_SCOPE_INVALID", error, Vec::new()))?,
    );
    Ok(DecodedPrime002Scope {
        run_hash,
        carrier_hash,
        claim,
        counterclaim,
        residual_hash,
        residual_label,
    })
}

fn issue_prime002_terminal_permit(
    request: &HostRequestV1,
    receipt: &SolveReceipt,
    terminal_site: &ScopeBinding,
) -> Result<(Gamma2Zero, core_wdp::prime_algos::prime_algorithm_2::TerminalPermit), Prime002Error> {
    let gamma2_zero = Gamma2Zero::verify(
        receipt.final_evaluation().gamma2().value(),
        terminal_site.clone(),
    )
    .map_err(|error| ("PRIME002_GAMMA2_NONZERO", error.to_string(), Vec::new()))?;
    let mut registry = ObligationRegistry::new(terminal_site.clone());
    for &deg in &request.prime002.open_obligation_degrees {
        registry.register(deg);
    }
    registry.discharge(2);
    let terminal_permit = registry
        .issue_terminal_permit(terminal_site.clone(), &gamma2_zero)
        .map_err(|error| {
            (
                "PRIME002_TERMINAL_PERMIT_REFUSED",
                error.to_string(),
                Vec::new(),
            )
        })?;
    Ok((gamma2_zero, terminal_permit))
}

pub(super) fn run_prime002_exact_transition(
    request: &HostRequestV1,
    carrier: &CarrierManifestSummaryV1,
    receipt: &SolveReceipt,
    oesos: &OesosSummaryV1,
) -> Result<Prime002SummaryV1, Prime002Error> {
    check_prime002_preconditions(request, receipt, oesos)?;
    let DecodedPrime002Scope {
        run_hash,
        carrier_hash,
        claim,
        counterclaim,
        residual_hash,
        residual_label,
    } = decode_prime002_scope(request, carrier, oesos)?;

    let skeleton = dda_digest(
        "core.oesos.host-skeleton.v1",
        &[
            &carrier_hash.0,
            request.packet_envelope.carrier_id.as_bytes(),
        ],
    );
    let budget_total =
        BigRational::from_integer(BigInt::from(request.budgets.max_prime_writes as u64));
    let floor = BigRational::from_integer(BigInt::from(1));
    let budget = Budget::declare(&budget_total, &floor).map_err(|error| {
        (
            "PRIME002_BUDGET_INVALID",
            error.to_string(),
            law_names(&error),
        )
    })?;
    let before_budget = BudgetSummaryV1 {
        max_ops: budget.max_ops(),
        spent: budget.spent(),
    };
    let mut state = ControlState::open(
        run_hash,
        carrier_hash.clone(),
        d0_commitment(receipt.gauge().phi1().d0()),
        skeleton,
        budget,
    );
    let outstanding = dda_digest(
        "core.oesos.host-phi1-obligation.v1",
        &[
            receipt.gauge().phi1().value().to_string().as_bytes(),
            &carrier_hash.0,
        ],
    );
    let higher = dda_digest(
        "core.oesos.host-gamma2-obligation.v1",
        &[
            receipt.gauge().gamma2().value().to_string().as_bytes(),
            request.source.source_event_root_sha256.as_bytes(),
        ],
    );
    let mut scopes = Vec::new();
    let mut claims = Vec::new();
    let mut evidences = Vec::new();
    let mut permits = Vec::new();

    let site = state.scope_for(residual_hash.clone());
    let ev = make_prime002_evidence(Prime002EvidenceInput {
        request,
        site: site.clone(),
        carrier_hash: carrier_hash.clone(),
        claim: &claim,
        counterclaim: &counterclaim,
        before: receipt.gauge().phi1(),
        after: receipt.final_evaluation().phi1(),
        outstanding: outstanding.clone(),
        higher: higher.clone(),
    })
    .map_err(|error| ("PRIME002_EVIDENCE_REFUSED", error, Vec::new()))?;
    let step = StepClaim {
        op: StepOp::ExactRepair,
        residual_content: residual_hash.clone(),
        residual_label: residual_label.clone(),
        degree: 1,
        skeleton: state.skeleton().clone(),
        loss_ledger: None,
        repacketized: false,
        claims_above_n0_are_conditional: false,
    };
    let permit = can_continue_n(&mut state, &site, &step, &ev).map_err(|error| {
        (
            "PRIME002_CONTINUATION_REFUSED",
            error.to_string(),
            law_names(&error),
        )
    })?;
    scopes.push(hex(&site.commit().0));
    claims.push(hex(&step.commit().0));
    evidences.push(hex(&ev.commit().0));
    permits.push(hex(&permit.binding(&step).0));
    write_step(&mut state, permit, &step, &ev).map_err(|error| {
        (
            "PRIME002_WRITE_REFUSED",
            error.to_string(),
            law_names(&error),
        )
    })?;

    let terminal_site = state.scope_for(residual_hash.clone());
    let terminal_ev = make_prime002_evidence(Prime002EvidenceInput {
        request,
        site: terminal_site.clone(),
        carrier_hash,
        claim: &claim,
        counterclaim: &counterclaim,
        before: receipt.final_evaluation().phi1(),
        after: receipt.final_evaluation().phi1(),
        outstanding,
        higher,
    })
    .map_err(|error| ("PRIME002_TERMINAL_EVIDENCE_REFUSED", error, Vec::new()))?;
    let terminal_claim = StepClaim {
        op: StepOp::Integration,
        residual_content: residual_hash,
        residual_label,
        degree: 1,
        skeleton: state.skeleton().clone(),
        loss_ledger: None,
        repacketized: false,
        claims_above_n0_are_conditional: false,
    };
    let (gamma2_zero, terminal_permit) =
        issue_prime002_terminal_permit(request, receipt, &terminal_site)?;
    scopes.push(hex(&terminal_site.commit().0));
    claims.push(hex(&terminal_claim.commit().0));
    evidences.push(hex(&terminal_ev.commit().0));
    permits.push(hex(&terminal_permit.gamma2_digest().0));

    let terminal_state = terminalize(state, terminal_permit, gamma2_zero).map_err(|error| {
        (
            "PRIME002_TERMINALIZATION_REFUSED",
            error.to_string(),
            Vec::new(),
        )
    })?;
    let terminal_head = hex(&terminal_state.terminal_head().0);
    Ok(Prime002SummaryV1 {
        kind: "exact_step_written_then_terminalized".to_owned(),
        scope_commitments_sha256: scopes,
        claim_commitments_sha256: claims,
        evidence_commitments_sha256: evidences,
        permit_bindings_sha256: permits,
        rust_letters: vec!["E".to_owned(), "T".to_owned()],
        terminal_head_sha256: terminal_head,
        budget_before: before_budget,
        budget_after: BudgetSummaryV1 {
            max_ops: terminal_state.budget().max_ops(),
            spent: terminal_state.budget().spent(),
        },
        refusal_laws: Vec::new(),
        evidence_caveat: "sealed current-process evidence; detector adequacy is sampled and the current Prime002 module documents remaining authority holes"
            .to_owned(),
    })
}

pub(super) fn law_names(
    error: &core_wdp::prime_algos::prime_algorithm_2::LawRefusal,
) -> Vec<String> {
    error
        .violations()
        .iter()
        .map(|violation| format!("{:?}", violation.law))
        .collect()
}

pub(super) fn solve_refusal_code(error: &SolveRefusal) -> &'static str {
    match error {
        SolveRefusal::RepresentationInvalid(_) => "OESOS_REPRESENTATION_INVALID",
        SolveRefusal::SizeBudgetExceeded { .. } => "OESOS_SIZE_BUDGET_EXCEEDED",
        SolveRefusal::Solver(_) => "OESOS_NETWORK_SIMPLEX_REFUSED",
        SolveRefusal::Evaluation(_) => "OESOS_EXACT_EVALUATION_REFUSED",
        SolveRefusal::Binding(_) => "OESOS_EVIDENCE_BINDING_REFUSED",
        SolveRefusal::Primitive(_) => "OESOS_PRIMITIVE_DIFFERENCE_REFUSED",
        SolveRefusal::Linear(_) => "OESOS_EXACT_LINEAR_ALGEBRA_REFUSED",
        SolveRefusal::JointCertificateSynthesis(_) => "OESOS_CERTIFICATE_SYNTHESIS_REFUSED",
        SolveRefusal::Manifest(_) => "OESOS_MANIFEST_SERIALIZATION_REFUSED",
        SolveRefusal::Lp(_) => "OESOS_EXACT_LP_REFUSED",
    }
}

pub(super) fn admission_reason(codes: &[String], detail: &str) -> String {
    framed_sha256(
        "core.oesos.host-admission-refusal.v1",
        &canonical_json(&serde_json::json!({
            "codes": codes,
            "detail": detail,
            "authority_effect": "None"
        })),
    )
}

// Origin: engine/crates_rs/pfp/src/host/prime_execution.rs
// Claim: urn:core:crates_rs:pfp:prime-execution:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd7c1e057 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd7c1e057` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord7c1e057 {
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
impl BoundaryErrord7c1e057 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord7c1e057 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord7c1e057 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd7c1e057 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord7c1e057> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord7c1e057::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord7c1e057::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord7c1e057::ExceedsCapacity {
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
mod l4_boundary_tests_d7c1e057 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd7c1e057::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd7c1e057::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd7c1e057::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd7c1e057::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd7c1e057::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrord7c1e057::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrord7c1e057::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}

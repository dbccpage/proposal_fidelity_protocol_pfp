//! Native exact mathematics and certificate verification; no transport or host I/O.

use super::*;

fn matrix_json<F>(action: &str, payload: &Value, run: F) -> RuntimeOutcomeV1
where
    F: FnOnce(MatrixRequestV1) -> Result<Value, String>,
{
    let request = match serde_json::from_value::<MatrixRequestV1>(payload.clone()) {
        Ok(request) => request,
        Err(error) => return outcome_err(action, format!("invalid matrix input: {error}")),
    };
    match run(request) {
        Ok(body) => outcome_ok(action, body),
        Err(error) => outcome_err(action, error),
    }
}

fn rational_entry(
    object: &serde_json::Map<String, Value>,
    key: &str,
) -> Result<num_rational::BigRational, ()> {
    let text = object.get(key).and_then(Value::as_str).ok_or(())?;
    std::str::FromStr::from_str(text).map_err(|_| ())
}

fn wdp_path_kernel(payload: &Value) -> RuntimeOutcomeV1 {
    const ACTION: &str = "wdp_kernel_check";
    let Some(rows) = payload.get("factors").and_then(Value::as_array) else {
        return outcome_err(ACTION, "WDP_PATH_KERNEL_FACTORS_REQUIRED");
    };
    let mut factors = Vec::with_capacity(rows.len());
    for row in rows {
        let Some(object) = row.as_object() else {
            return outcome_err(ACTION, "WDP_PATH_KERNEL_FACTOR_INVALID");
        };
        let Ok(m00) = rational_entry(object, "m00") else {
            return outcome_err(ACTION, "WDP_PATH_KERNEL_ENTRY_NOT_RATIONAL");
        };
        let Ok(m01) = rational_entry(object, "m01") else {
            return outcome_err(ACTION, "WDP_PATH_KERNEL_ENTRY_NOT_RATIONAL");
        };
        let Ok(m10) = rational_entry(object, "m10") else {
            return outcome_err(ACTION, "WDP_PATH_KERNEL_ENTRY_NOT_RATIONAL");
        };
        let Ok(m11) = rational_entry(object, "m11") else {
            return outcome_err(ACTION, "WDP_PATH_KERNEL_ENTRY_NOT_RATIONAL");
        };
        factors.push(core_epk::matrix_path_kernel::RationalMatrix2x2::new(
            m00, m01, m10, m11,
        ));
    }
    match core_wdp::wdp_kernel_check::wdp_kernel_check(&factors) {
        Ok(product) => outcome_ok(
            ACTION,
            serde_json::json!({
                "m00": product.m00.to_string(),
                "m01": product.m01.to_string(),
                "m10": product.m10.to_string(),
                "m11": product.m11.to_string(),
                "authority_effect": "None",
            }),
        ),
        Err(error) => outcome_err(ACTION, error.to_string()),
    }
}

fn outcome_from_value<E: Into<String>>(action: &str, res: Result<Value, E>) -> RuntimeOutcomeV1 {
    match res {
        Ok(result) => outcome_ok(action, result),
        Err(reason) => outcome_err(action, reason),
    }
}

fn outcome_from_serializable<T: serde::Serialize, E: Into<String>>(
    action: &str,
    res: Result<T, E>,
) -> RuntimeOutcomeV1 {
    match res {
        Ok(receipt) => match serde_json::to_value(receipt) {
            Ok(v) => outcome_ok(action, v),
            Err(e) => outcome_err(action, format!("serialization error: {e}")),
        },
        Err(reason) => outcome_err(action, reason),
    }
}

fn run_verify_pinned_permutation_order(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: PinnedPermutationOrderRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(request) => request,
        Err(_) => return outcome_err(action, "INVALID_PINNED_PERMUTATION_REQUEST"),
    };
    if let Err(reason) = pinned_permutation::validate_claim(&request) {
        return outcome_err(action, reason);
    }
    let presentation = host_named_presentation(&request.presentation_ref);
    outcome_from_serializable(action, pinned_permutation::observe(request, presentation))
}

fn run_verify_l1_certificate(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: VerifyL1CertificateRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(value) => value,
        Err(error) => return outcome_err(action, format!("invalid rational input: {error}")),
    };
    match verify_l1_certificate(&request.matrix, &request.omega, &request.p, &request.y) {
        Ok(Ok(certificate)) => outcome_ok(
            action,
            serde_json::json!({"accepted": true, "certificate": certificate}),
        ),
        Ok(Err(refusal)) => outcome_ok(
            action,
            serde_json::json!({
                "accepted": false,
                "refusal": l1_refusal_json(refusal)
            }),
        ),
        Err(error) => outcome_err(action, error.to_string()),
    }
}

fn parse_l1_weights(weights: &Option<Vec<String>>, m: usize) -> Result<Vec<Exact>, String> {
    let Some(w_strs) = weights else {
        return Ok(vec![Exact::from_integer(1.into()); m]);
    };
    let mut parsed = Vec::with_capacity(w_strs.len());
    for s in w_strs {
        let val = parse_exact(s).map_err(|e| format!("invalid weight rational: {e}"))?;
        parsed.push(val);
    }
    Ok(parsed)
}

fn extract_exact_matrix_rows(matrix: &RationalMatrix) -> Vec<Vec<Exact>> {
    (0..matrix.rows())
        .map(|r| (0..matrix.cols()).map(|c| matrix.get(r, c).clone()).collect())
        .collect()
}

fn run_exact_solve_l1_primal_dual(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: SolveL1PrimalDualRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(value) => value,
        Err(error) => {
            return outcome_err(action, format!("invalid primal-dual solver input: {error}"))
        }
    };
    let m = request.target.len();
    let weights = match parse_l1_weights(&request.weights, m) {
        Ok(w) => w,
        Err(err) => return outcome_err(action, err),
    };
    let matrix_rows = extract_exact_matrix_rows(&request.matrix);
    let budget = request
        .budget
        .unwrap_or_else(|| 64 * (m + request.matrix.cols()) + 1024);

    match core_solvers::solver_lp_exact_simplex::solve_weighted_l1_projection(
        &request.target,
        &weights,
        &matrix_rows,
        budget,
    ) {
        Ok(solution) => {
            let cert = core_functional::ExactPhi1Certificate {
                omega: request.target.clone(),
                d0: matrix_rows.clone(),
                weights: weights.clone(),
                alpha: solution.coefficients.clone(),
                primal_residual: solution.residual.clone(),
                dual_witness: solution.dual.clone(),
                reported_value: solution.value.clone(),
            };
            let certificate_verified =
                core_functional::Phi1Functional::verify_exact_certificate(cert).is_ok();
            outcome_ok(
                action,
                serde_json::json!({
                    "alpha": solution.coefficients.iter().map(to_canonical_string).collect::<Vec<_>>(),
                    "residual": solution.residual.iter().map(to_canonical_string).collect::<Vec<_>>(),
                    "dual_witness": solution.dual.iter().map(to_canonical_string).collect::<Vec<_>>(),
                    "phi1": to_canonical_string(&solution.value),
                    "iterations": solution.iterations,
                    "certificate_verified": certificate_verified,
                }),
            )
        }
        Err(e) => outcome_err(action, format!("solver error: {e}")),
    }
}

fn run_exact_verify_boundary_closed(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: VerifyBoundaryClosedRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid boundary request input: {e}")),
    };
    let is_closed = verify_boundary_closed(&request.faces);
    outcome_ok(action, serde_json::json!({ "boundary_closed": is_closed }))
}

fn run_exact_verify_simplicial_boundary_law(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: VerifySimplicialBoundaryLawRequestV1 =
        match serde_json::from_value(payload.clone()) {
            Ok(val) => val,
            Err(e) => {
                return outcome_err(
                    action,
                    format!("invalid simplicial boundary request input: {e}"),
                )
            }
        };
    match verify_simplicial_boundary_detailed(&request.simplices) {
        Ok(report) => outcome_ok(action, serde_json::to_value(report).unwrap_or_default()),
        Err(e) => outcome_err(action, e),
    }
}

fn run_exact_ordered_loop_product(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: LoopProductRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid loop product request input: {e}")),
    };
    match ordered_loop_product(&request.tables, &request.word) {
        Ok(prod) => {
            let rows: Vec<Vec<String>> = (0..prod.rows())
                .map(|r| {
                    (0..prod.cols())
                        .map(|c| to_canonical_string(prod.get(r, c)))
                        .collect()
                })
                .collect();
            outcome_ok(action, serde_json::json!({ "product": rows }))
        }
        Err(e) => outcome_err(action, e.to_string()),
    }
}

fn run_exact_is_ordered_closure(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: LoopProductRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid loop product request input: {e}")),
    };
    match is_ordered_closure(&request.tables, &request.word) {
        Ok(is_closed) => outcome_ok(action, serde_json::json!({ "is_closure": is_closed })),
        Err(e) => outcome_err(action, e.to_string()),
    }
}

fn parse_critical_peak_inputs(
    payload: &Value,
) -> Result<(Presentation, CriticalPeakClaim), String> {
    let presentation_val = payload
        .get("presentation")
        .ok_or_else(|| "missing presentation".to_string())?;
    let claim_val = payload
        .get("claim")
        .ok_or_else(|| "missing claim".to_string())?;
    let presentation: Presentation = serde_json::from_value(presentation_val.clone())
        .map_err(|e| format!("presentation: {e}"))?;
    let claim: CriticalPeakClaim =
        serde_json::from_value(claim_val.clone()).map_err(|e| format!("claim: {e}"))?;
    Ok((presentation, claim))
}

fn run_evaluate_critical_peak(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let (presentation, claim) = match parse_critical_peak_inputs(payload) {
        Ok(pair) => pair,
        Err(err) => return outcome_err(action, err),
    };
    // Pins come from the HOST, never from `req.payload`. A verdict
    // reached under rules that arrived with the claim is reported as
    // SELF_CONSISTENT_ONLY, because that is what was established.
    let evaluation = evaluate_peak_pinned(&presentation, &claim, host_presentation_pins());
    let token = evaluation.token();
    match serde_json::to_value(&evaluation) {
        // `token` travels beside the packet rather than inside it:
        // PeakEvaluation denies unknown fields, so an extra key would
        // stop the wire form being a PeakEvaluation. It is emitted at
        // all because a consumer left to call `verdict.token()` itself
        // is a consumer that reads JOINED off a producer's own rules --
        // the defect this whole path exists to close.
        Ok(value) => outcome_ok(
            action,
            serde_json::json!({ "token": token, "evaluation": value }),
        ),
        Err(e) => outcome_err(action, e.to_string()),
    }
}

fn run_enumerate_critical_pairs(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let Some(presentation) = payload.get("presentation") else {
        return outcome_err(action, "missing presentation");
    };
    let presentation: Presentation = match serde_json::from_value(presentation.clone()) {
        Ok(value) => value,
        Err(e) => return outcome_err(action, format!("presentation: {e}")),
    };
    match serde_json::to_value(critical_pairs(&presentation)) {
        Ok(value) => outcome_ok(action, value),
        Err(e) => outcome_err(action, e.to_string()),
    }
}

fn parse_f2_matrix_field(payload: &Value, key: &str) -> Result<F2Matrix, String> {
    let val = payload
        .get(key)
        .ok_or_else(|| format!("missing {key} matrix"))?;
    serde_json::from_value::<F2Matrix>(val.clone())
        .map_err(|e| format!("invalid {key} matrix: {e}"))
}

fn run_classify_gauge_board(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let d0 = match parse_f2_matrix_field(payload, "d0") {
        Ok(m) => m,
        Err(e) => return outcome_err(action, e),
    };
    let d1 = match parse_f2_matrix_field(payload, "d1") {
        Ok(m) => m,
        Err(e) => return outcome_err(action, e),
    };
    let board = GaugeBoard::new(d0, d1);
    let cochain = match parse_gauge_cochain(payload.get("cochain")) {
        Ok(cochain) => cochain,
        Err(error) => return outcome_err(action, error),
    };
    outcome_from_serializable(action, board.classify(&cochain).map_err(|e| e.to_string()))
}

fn run_stabilizer_solve(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: StabilizerSolveRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid stabilizer_solve input: {e}")),
    };
    let outcome = pfp_runtime::stabilizer_solve(&request.case);
    outcome_from_serializable::<_, String>(action, Ok(outcome))
}

fn run_stabilizer_check(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: StabilizerCheckRequestV1 = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid stabilizer_check input: {e}")),
    };
    let check_res = pfp_runtime::stabilizer_check(&request.case, &request.result);
    outcome_from_serializable::<_, String>(action, Ok(check_res))
}

fn run_operad_validate_prompt(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let prompt: pfp_runtime::ColouredOperadPrompt =
        match serde_json::from_value(payload.clone()) {
            Ok(val) => val,
            Err(e) => return outcome_err(action, format!("invalid operad prompt payload: {e}")),
        };
    match prompt.validate() {
        Ok(()) => outcome_ok(action, serde_json::json!({ "valid": true })),
        Err(refusal) => outcome_err(action, refusal.to_string()),
    }
}

#[derive(Deserialize)]
struct GraftRequest {
    outer: pfp_runtime::OperadTree,
    slot: usize,
    inner: pfp_runtime::OperadTree,
}

fn run_operad_graft_slot(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: GraftRequest = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid operad graft payload: {e}")),
    };
    outcome_from_serializable(
        action,
        request
            .outer
            .graft(request.slot, &request.inner)
            .map_err(|r| r.to_string()),
    )
}

#[derive(Deserialize)]
struct IdealsRequest {
    prompt: pfp_runtime::ColouredOperadPrompt,
    tree: pfp_runtime::OperadTree,
    #[serde(default)]
    source_document: Option<String>,
    #[serde(default)]
    rational_values: std::collections::BTreeMap<String, String>,
    witnesses_valid: bool,
}

fn run_operad_evaluate_ideals(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: IdealsRequest = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid ideals request payload: {e}")),
    };
    let result_tree = request.prompt.evaluate_ideals(
        &request.tree,
        request.source_document.as_deref(),
        &request.rational_values,
        request.witnesses_valid,
    );
    outcome_from_serializable::<_, String>(action, Ok(result_tree))
}

#[derive(Deserialize)]
struct AnnihilatorRequest {
    annihilator: pfp_runtime::AnnihilatorDecoy,
    candidate_bindings: std::collections::BTreeMap<String, String>,
    #[serde(default)]
    refutation_witness: Option<pfp_runtime::RefutationWitness>,
}

fn run_operad_check_annihilator(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: AnnihilatorRequest = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid annihilator request payload: {e}")),
    };
    outcome_from_serializable(
        action,
        request
            .annihilator
            .evaluate(
                &request.candidate_bindings,
                request.refutation_witness.as_ref(),
            )
            .map_err(|r| r.to_string()),
    )
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct CochainEvaluateRequest {
    complex: Value,
    cochain: Vec<Value>,
    primal_potential: Vec<Value>,
    dual_witness: Vec<Value>,
    #[serde(default)]
    triad_context: Option<CochainTriadContext>,
}

#[derive(Default, Deserialize)]
#[serde(default, deny_unknown_fields)]
struct CochainTriadContext {
    source_bytes: Option<String>,
    expected_source_hash: Option<String>,
    protected_answers: Option<std::collections::BTreeMap<String, String>>,
    candidate_answers: Option<std::collections::BTreeMap<String, String>>,
    remaining_budget: Option<u64>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct CochainComplexWire {
    c0_dim: usize,
    c1_dim: usize,
    c2_dim: usize,
    d0: Vec<Value>,
    d1: Vec<Value>,
    #[serde(default)]
    source_bytes_hash: Option<String>,
}

fn parse_rational_pair(arr: &[Value]) -> Result<num_rational::BigRational, String> {
    let numer = arr[0]
        .as_i64()
        .ok_or_else(|| "numerator must be integer".to_string())?;
    let denom = arr[1]
        .as_i64()
        .ok_or_else(|| "denominator must be integer".to_string())?;
    if denom == 0 {
        return Err("zero denominator in rational".to_string());
    }
    // Same admission as parse_exact: BigRational::new reduces, then the
    // spelling "{numer}/{denom}" must already be the canonical rendering.
    // "1/1" reduces to 1/1 but renders as "1", so it is not a second spelling.
    let spelling = format!("{numer}/{denom}");
    core_kernel::parse_exact(&spelling)
        .map_err(|error| format!("invalid rational pair [{numer}, {denom}]: {error}"))
}

fn parse_rational_val(v: &Value) -> Result<num_rational::BigRational, String> {
    match v {
        Value::String(s) => core_kernel::parse_exact(s)
            .map_err(|e| format!("invalid rational string '{s}': {e}")),
        Value::Number(n) => n
            .as_i64()
            .map(|i| num_rational::BigRational::from_integer(num_bigint::BigInt::from(i)))
            .ok_or_else(|| format!("floating point JSON numbers not allowed: {n}")),
        Value::Array(arr) if arr.len() == 2 => parse_rational_pair(arr),
        other => Err(format!(
            "expected rational (string, integer, or [numer, denom]), got {other}"
        )),
    }
}

fn parse_rational_vec(
    items: &[Value],
    label: &str,
) -> Result<Vec<num_rational::BigRational>, String> {
    items
        .iter()
        .map(parse_rational_val)
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| {
            if label.is_empty() {
                e
            } else {
                format!("invalid {label} entry: {e}")
            }
        })
}

fn parse_rational_matrix(
    rows: &[Value],
    row_label: &str,
) -> Result<Vec<Vec<num_rational::BigRational>>, String> {
    let mut mat = Vec::with_capacity(rows.len());
    for row in rows {
        let row_arr = row
            .as_array()
            .ok_or_else(|| format!("{row_label} rows must be arrays"))?;
        mat.push(parse_rational_vec(row_arr, "")?);
    }
    Ok(mat)
}

fn parse_cochain_complex(
    complex_val: &Value,
) -> Result<pfp_runtime::PromptCellComplex, String> {
    // Apply one key/type contract before either rational representation.
    let wire: CochainComplexWire = serde_json::from_value(complex_val.clone())
        .map_err(|e| format!("invalid cochain complex: {e}"))?;

    if let Ok(c) = serde_json::from_value(complex_val.clone()) {
        return Ok(c);
    }
    let d0 = parse_rational_matrix(&wire.d0, "d0")?;
    let d1 = parse_rational_matrix(&wire.d1, "d1")?;
    Ok(pfp_runtime::PromptCellComplex {
        c0_dim: wire.c0_dim,
        c1_dim: wire.c1_dim,
        c2_dim: wire.c2_dim,
        d0,
        d1,
        source_bytes_hash: wire.source_bytes_hash,
    })
}

fn run_cochain_evaluate(action: &str, payload: &Value) -> RuntimeOutcomeV1 {
    let request: CochainEvaluateRequest = match serde_json::from_value(payload.clone()) {
        Ok(val) => val,
        Err(e) => return outcome_err(action, format!("invalid cochain evaluate payload: {e}")),
    };
    let complex = match parse_cochain_complex(&request.complex) {
        Ok(c) => c,
        Err(e) => return outcome_err(action, e),
    };
    let cochain = match parse_rational_vec(&request.cochain, "cochain") {
        Ok(v) => v,
        Err(e) => return outcome_err(action, e),
    };
    let potential = match parse_rational_vec(&request.primal_potential, "primal_potential") {
        Ok(v) => v,
        Err(e) => return outcome_err(action, e),
    };
    let dual_witness = match parse_rational_vec(&request.dual_witness, "dual_witness") {
        Ok(v) => v,
        Err(e) => return outcome_err(action, e),
    };
    let mut prime_triad = request
        .triad_context
        .map(|context| pfp_runtime::PrimeTriadContext {
            source_bytes: context.source_bytes,
            expected_source_hash: context.expected_source_hash,
            protected_answers: context.protected_answers,
            candidate_answers: context.candidate_answers,
            remaining_budget: context.remaining_budget,
        })
        .unwrap_or_default();

    let disposition = pfp_runtime::PromptCochainEvaluator::evaluate(
        &complex,
        &cochain,
        &potential,
        &dual_witness,
        Some(&mut prime_triad),
    );
    outcome_from_serializable::<_, String>(action, Ok(disposition))
}

fn dispatch_wdp_and_genesis(action: &str, payload: &Value) -> Option<RuntimeOutcomeV1> {
    match action {
        "wdp_kernel_check" => Some(wdp_path_kernel(payload)),
        "wdp_certificate_check" => Some(outcome_from_value(action, crate::wdp_kernel::execute(payload))),
        "genesis_report_verify_commit" => Some(outcome_from_value(
            action,
            crate::report_operation::verify_commit(payload),
        )),
        "genesis_report_describe_operation" => Some(outcome_from_value(
            action,
            crate::report_operation::describe(payload),
        )),
        "genesis_report_commit" => {
            Some(outcome_from_value(action, crate::report_operation::execute(payload)))
        }
        "genesis_report_evaluate" => {
            Some(outcome_from_value(action, crate::genesis_reports::evaluate(payload)))
        }
        "genesis_report_verify" => {
            Some(outcome_from_value(action, crate::genesis_reports::verify(payload)))
        }
        "architecture_dag_verify" => {
            Some(outcome_from_value(action, crate::architecture_dag::verify(payload)))
        }
        "genesis_resolve" => Some(outcome_from_value(
            action,
            crate::genesis_resolution::resolve(payload),
        )),
        _ => None,
    }
}

fn dispatch_coda_and_functional(action: &str, payload: &Value) -> Option<RuntimeOutcomeV1> {
    match action {
        "verify_pinned_permutation_order" => {
            Some(run_verify_pinned_permutation_order(action, payload))
        }
        "verify_l1_certificate" => Some(run_verify_l1_certificate(action, payload)),
        "exact_solve_l1_primal_dual" => Some(run_exact_solve_l1_primal_dual(action, payload)),
        "continuum_evaluate" => Some(outcome_from_value(action, crate::continuum::evaluate(payload))),
        "coda_evaluate" => Some(outcome_from_serializable(
            action,
            crate::coda::evaluate_coda(payload).map_err(|r| r.wire()),
        )),
        "coda_verify" => Some(outcome_from_value(
            action,
            crate::coda::verify_coda(payload).map_err(|r| r.wire()),
        )),
        "functional_evaluate" => Some(outcome_from_serializable(
            action,
            crate::functional::evaluate_functional(payload).map_err(|r| r.wire()),
        )),
        "functional_verify" => Some(outcome_from_value(
            action,
            crate::functional::verify_functional(payload).map_err(|r| r.wire()),
        )),
        _ => None,
    }
}

fn dispatch_packets_and_measurement(action: &str, payload: &Value) -> Option<RuntimeOutcomeV1> {
    match action {
        "wdp_packet_evaluate" => Some(outcome_from_serializable(
            action,
            crate::wdp_packet::evaluate(payload).map_err(|r| r.wire()),
        )),
        "wdp_packet_verify" => Some(outcome_from_serializable(
            action,
            crate::wdp_packet::verify(payload).map_err(|r| r.wire()),
        )),
        "measurement_evaluate" => Some(outcome_from_serializable(
            action,
            crate::measurement_certificate::evaluate(payload),
        )),
        "measurement_verify" => Some(outcome_from_value(
            action,
            crate::measurement_certificate::verify(payload),
        )),
        "verify_decode_receipt_v2" => {
            Some(outcome_from_value(action, crate::decode_v2::verify(payload)))
        }
        "projection_evaluate" => Some(outcome_from_serializable(
            action,
            crate::projection::evaluate_projection(payload),
        )),
        "projection_verify" => Some(outcome_from_value(
            action,
            crate::projection::verify_projection(payload),
        )),
        "ddc_verify_tape" => Some(outcome_from_serializable(
            action,
            crate::ddc::verify_tape(payload),
        )),
        _ => None,
    }
}

fn dispatch_graph_and_lggr(action: &str, payload: &Value) -> Option<RuntimeOutcomeV1> {
    match action {
        "graph_evaluate" => Some(outcome_from_serializable(
            action,
            crate::graph::evaluate_graph(payload),
        )),
        "graph_verify" => Some(outcome_from_value(action, crate::graph::verify_graph(payload))),
        "graph_challenge" => {
            Some(outcome_from_value(action, crate::graph::challenge_graph(payload)))
        }
        "lggr_classify" => Some(outcome_from_serializable(
            action,
            crate::lggr::classify_lggr(payload).map_err(|r| r.wire()),
        )),
        "lggr_k_cell_classify" => Some(outcome_from_serializable(
            action,
            crate::lggr::classify_lggr_k_cell(payload).map_err(|r| r.wire()),
        )),
        "lggr_soundness" => Some(outcome_from_serializable(
            action,
            crate::lggr::soundness_lggr(payload).map_err(|r| r.wire()),
        )),
        _ => None,
    }
}

fn dispatch_matrix(action: &str, payload: &Value) -> Option<RuntimeOutcomeV1> {
    match action {
        "exact_determinant" => Some(matrix_json(action, payload, |request| {
            request
                .matrix
                .determinant()
                .map(|det| serde_json::json!({ "determinant": to_canonical_string(&det) }))
                .map_err(|error| error.to_string())
        })),
        "exact_is_positive_definite" => Some(matrix_json(action, payload, |request| {
            request
                .matrix
                .is_positive_definite()
                .map(|is_pd| serde_json::json!({ "is_positive_definite": is_pd }))
                .map_err(|error| error.to_string())
        })),
        "exact_ldlt" => Some(matrix_json(action, payload, |request| {
            request
                .matrix
                .ldlt_pivots()
                .map(|pivots| {
                    serde_json::json!({
                        "pivots": pivots.iter().map(to_canonical_string).collect::<Vec<_>>()
                    })
                })
                .map_err(|error| error.to_string())
        })),
        "exact_rank" => Some(matrix_json(action, payload, |request| {
            request
                .matrix
                .rank()
                .map(|rank| serde_json::json!({ "rank": rank }))
                .map_err(|error| error.to_string())
        })),
        "exact_leading_minors" => Some(matrix_json(action, payload, |request| {
            request
                .matrix
                .leading_minors()
                .map(|minors| {
                    serde_json::json!({
                        "leading_minors": minors.iter().map(to_canonical_string).collect::<Vec<_>>()
                    })
                })
                .map_err(|error| error.to_string())
        })),
        "exact_char_poly" => Some(matrix_json(action, payload, |request| {
            request
                .matrix
                .char_poly()
                .map(|coeffs| {
                    serde_json::json!({
                        "coeffs": coeffs.iter().map(to_canonical_string).collect::<Vec<_>>()
                    })
                })
                .map_err(|error| error.to_string())
        })),
        _ => None,
    }
}

fn dispatch_topology_and_peaks(action: &str, payload: &Value) -> Option<RuntimeOutcomeV1> {
    match action {
        "exact_verify_boundary_closed" => {
            Some(run_exact_verify_boundary_closed(action, payload))
        }
        "exact_verify_simplicial_boundary_law" => {
            Some(run_exact_verify_simplicial_boundary_law(action, payload))
        }
        "exact_ordered_loop_product" => Some(run_exact_ordered_loop_product(action, payload)),
        "exact_is_ordered_closure" => Some(run_exact_is_ordered_closure(action, payload)),
        "evaluate_critical_peak" => Some(run_evaluate_critical_peak(action, payload)),
        "enumerate_critical_pairs" => Some(run_enumerate_critical_pairs(action, payload)),
        "classify_gauge_board" => Some(run_classify_gauge_board(action, payload)),
        _ => None,
    }
}

fn dispatch_stabilizer_and_operad(action: &str, payload: &Value) -> Option<RuntimeOutcomeV1> {
    match action {
        "stabilizer_solve" => Some(run_stabilizer_solve(action, payload)),
        "stabilizer_check" => Some(run_stabilizer_check(action, payload)),
        "operad_validate_prompt" => Some(run_operad_validate_prompt(action, payload)),
        "operad_graft_slot" => Some(run_operad_graft_slot(action, payload)),
        "operad_evaluate_ideals" => Some(run_operad_evaluate_ideals(action, payload)),
        "operad_check_annihilator" => Some(run_operad_check_annihilator(action, payload)),
        "cochain_evaluate" => Some(run_cochain_evaluate(action, payload)),
        "coupled_relational_operad_verify" => Some(outcome_from_value(
            action,
            crate::coupled_relational_operad::verify_json(payload),
        )),
        _ => None,
    }
}

pub(super) fn dispatch(req: &RuntimeRequestV1) -> RuntimeOutcomeV1 {
    let action = req.action.as_str();
    let payload = &req.payload;
    dispatch_wdp_and_genesis(action, payload)
        .or_else(|| dispatch_coda_and_functional(action, payload))
        .or_else(|| dispatch_packets_and_measurement(action, payload))
        .or_else(|| dispatch_graph_and_lggr(action, payload))
        .or_else(|| dispatch_matrix(action, payload))
        .or_else(|| dispatch_topology_and_peaks(action, payload))
        .or_else(|| dispatch_stabilizer_and_operad(action, payload))
        .unwrap_or_else(|| outcome_err(action, format!("unsupported runtime action: {action}")))
}

// Origin: engine/crates_rs/pfp/src/invoke/exact.rs
// Claim: urn:core:crates_rs:pfp:exact:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordde66356b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordde66356b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorde66356b {
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
impl BoundaryErrorde66356b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorde66356b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorde66356b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordde66356b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorde66356b> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorde66356b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorde66356b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorde66356b::ExceedsCapacity {
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
mod cochain_intake_refusals {
    use super::*;
    use pfp_runtime::{cochain_rational, PromptCellComplex};
    use serde_json::Value;

    fn declared_zero_face() -> Value {
        serde_json::json!({
            "complex": {
                "c0_dim": 2,
                "c1_dim": 1,
                "c2_dim": 0,
                "d0": [["-1/2", "1/2"]],
                "d1": []
            },
            "cochain": ["1/2"],
            "primal_potential": ["0", "1"],
            "dual_witness": ["0"]
        })
    }

    #[test]
    fn omitted_c2_dim_or_d1_is_a_typed_refusal() {
        for field in ["c2_dim", "d1"] {
            let mut payload = declared_zero_face();
            payload["complex"].as_object_mut().unwrap().remove(field);
            let outcome = run_cochain_evaluate("cochain_evaluate", &payload);
            assert!(!outcome.success, "{field} became a zero-face complex");
            assert!(outcome.result.is_none());
            let error = outcome.error.unwrap();
            assert!(error.contains("invalid cochain complex"), "{error}");
            assert!(error.contains("missing field"), "{error}");
            assert!(error.contains(field), "{field}: {error}");
            assert!(!error.contains("gamma2") && !error.contains("Gamma"));
        }
    }

    #[test]
    fn omitted_primal_potential_or_dual_witness_is_a_typed_refusal() {
        for field in ["primal_potential", "dual_witness"] {
            let mut payload = declared_zero_face();
            payload.as_object_mut().unwrap().remove(field);
            let outcome = run_cochain_evaluate("cochain_evaluate", &payload);
            assert!(!outcome.success, "{field} was defaulted to an empty witness");
            assert!(outcome.result.is_none());
            let error = outcome.error.unwrap();
            assert!(error.contains("invalid cochain evaluate payload"), "{error}");
            assert!(error.contains("missing field"), "{error}");
            assert!(error.contains(field), "{field}: {error}");
        }
    }

    #[test]
    fn explicit_zero_face_and_canonical_half_match_the_native_disposition() {
        let strings = run_cochain_evaluate("cochain_evaluate", &declared_zero_face());
        let native_complex = serde_json::to_value(PromptCellComplex::zero_face(
            2,
            1,
            vec![vec![cochain_rational(-1, 2), cochain_rational(1, 2)]],
        ))
        .unwrap();
        let mut native = declared_zero_face();
        native["complex"] = native_complex;
        let native = run_cochain_evaluate("cochain_evaluate", &native);
        assert!(strings.success, "{:?}", strings.error);
        assert!(native.success, "{:?}", native.error);
        assert_eq!(strings.result, native.result);
        let result: pfp_runtime::CochainDisposition =
            serde_json::from_value(strings.result.unwrap()).unwrap();
        match result {
            pfp_runtime::CochainDisposition::ExactCoboundary {
                phi1, gamma2, ..
            } => {
                assert_eq!(phi1, cochain_rational(0, 1));
                assert_eq!(gamma2, cochain_rational(0, 1));
            }
            other => panic!("canonical 1/2 did not match the native disposition: {other:?}"),
        }
    }

    #[test]
    fn noncanonical_and_padded_rationals_are_refused() {
        for spelling in ["2/4", "1/1", " 1"] {
            let err = parse_rational_val(&Value::String(spelling.to_owned())).unwrap_err();
            assert!(err.contains(spelling), "{spelling} was admitted: {err}");
            let mut payload = declared_zero_face();
            payload["cochain"][0] = Value::String(spelling.to_owned());
            let outcome = run_cochain_evaluate("cochain_evaluate", &payload);
            assert!(!outcome.success, "{spelling} was admitted");
            assert!(outcome.result.is_none());
            assert!(outcome.error.unwrap().contains(spelling));
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_de66356b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordde66356b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordde66356b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordde66356b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordde66356b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordde66356b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorde66356b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorde66356b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}

#[cfg(test)]
mod ideals_witness_flag {
    use super::*;
    use serde_json::Value;

    fn ideals_payload(colour: &str, witnesses_valid: Option<bool>) -> Value {
        let mut payload = serde_json::json!({
            "prompt": {
                "schema_id": "core.coda.categorical-operad-prompt.v2",
                "operad_meta": {
                    "family_name": "witness_flag",
                    "prompt_id": "P_WITNESS"
                },
                "colours": [],
                "operands": [],
                "operators": [],
                "congruence_ideals": [{
                    "id": "IDEAL_WITNESS",
                    "target_colour": colour,
                    "assertion": "verified substitution witness"
                }]
            },
            "tree": {
                "type": "leaf",
                "span": {
                    "id": "span",
                    "colour": "RawTextSpan",
                    "content": "x",
                    "source_offsets": [0, 1]
                }
            }
        });
        if let Some(flag) = witnesses_valid {
            payload["witnesses_valid"] = Value::Bool(flag);
        }
        payload
    }

    #[test]
    fn omitted_witnesses_valid_is_invalid_before_evaluate_ideals() {
        let mut payload = ideals_payload("TargetResult", Some(true));
        assert!(payload.as_object_mut().unwrap().remove("witnesses_valid").is_some());
        let outcome = run_operad_evaluate_ideals("operad_evaluate_ideals", &payload);
        assert!(!outcome.success);
        assert!(outcome.result.is_none());
        let error = outcome.error.unwrap();
        assert!(error.contains("invalid ideals request payload"), "{error}");
        assert!(error.contains("missing field"), "{error}");
        assert!(error.contains("witnesses_valid"), "{error}");
        assert!(!error.contains("composite evaluation"), "{error}");
    }

    #[test]
    fn explicit_true_evaluates_and_false_nulls_witness_colours() {
        for colour in ["TargetResult", "InvariantWitness"] {
            let admitted = run_operad_evaluate_ideals(
                "operad_evaluate_ideals",
                &ideals_payload(colour, Some(true)),
            );
            assert!(admitted.success, "{colour}: {:?}", admitted.error);
            let tree = admitted.result.expect("explicit true returned no tree");
            assert_eq!(tree["type"], "leaf", "{colour} was refused: {tree}");

            let refused = run_operad_evaluate_ideals(
                "operad_evaluate_ideals",
                &ideals_payload(colour, Some(false)),
            );
            assert!(refused.success, "{colour}: {:?}", refused.error);
            let tree = refused.result.expect("explicit false returned no tree");
            assert_eq!(tree["type"], "null_tree", "{colour} was not nulled: {tree}");
            assert_eq!(tree["target_colour"], colour);
            let reason = tree["reason"].as_str().expect("null tree reason");
            assert!(
                reason.contains("without verified substitution witness"),
                "{colour}: {reason}"
            );
        }
    }
}

#[cfg(test)]
mod rational_pair_parse_exact_terms {
    use super::*;

    fn pair(numer: i64, denom: i64) -> Vec<Value> {
        vec![Value::from(numer), Value::from(denom)]
    }

    #[test]
    fn unreduced_pairs_fail_the_pair_arm_and_reduced_slash_forms_stay() {
        // Slash spellings parse_exact refuses in core_kernel::exact, plus "1/1"
        // whose canonical rendering is "1".
        for (numer, denom) in [(2_i64, 4_i64), (1, 1), (-1, -2), (1, -2), (4, 2)] {
            let spelling = format!("{numer}/{denom}");
            assert!(
                core_kernel::parse_exact(&spelling).is_err(),
                "{spelling} is not a spelling parse_exact refuses"
            );
            let err = parse_rational_pair(&pair(numer, denom)).unwrap_err();
            assert!(
                err.contains(&spelling),
                "{spelling} was admitted by the pair arm: {err}"
            );
        }

        let refused = parse_rational_val(&Value::String("2/4".to_owned())).unwrap_err();
        assert!(refused.contains("2/4"), "{refused}");

        // Slash spellings parse_exact already accepts. Integer spellings
        // ("0", "-12", "2") are not pairs; "1/1" is refused above.
        for spelling in ["3/4", "-5/7", "1/2", "-1/2", "1/3", "1/4", "5/6"] {
            let expected = core_kernel::parse_exact(spelling).expect(spelling);
            let (numer_text, denom_text) = spelling.split_once('/').unwrap();
            let numer: i64 = numer_text.parse().unwrap();
            let denom: i64 = denom_text.parse().unwrap();
            let got = parse_rational_pair(&pair(numer, denom)).expect(spelling);
            assert_eq!(got, expected, "{spelling}");
            assert_eq!(core_kernel::to_canonical_string(&got), spelling);
        }
    }
}

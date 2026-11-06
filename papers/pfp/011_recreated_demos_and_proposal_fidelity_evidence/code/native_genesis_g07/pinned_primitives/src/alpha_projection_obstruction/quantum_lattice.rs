//! §§5–6 — finite quantum-lattice numerical replays: a one-/two-local
//! Hamiltonian on finite local Hilbert spaces with a product initial
//! state; the full incident norm `g = max_v Σ_{X∋v} ‖h_X‖`; the reduced
//! derivative `L_e = Tr_{e^c}(−i[H, ρ₀])`, the product-retraction tangent
//! `P_e`, the normal part `n_e = Q_e L_e`, and the rate `ν_e = ‖n_e‖₁`;
//! the evolved edge defect `D_e(t) = ‖ρ_e(t) − ρ_a(t) ⊗ ρ_b(t)‖₁`; and the
//! signed, unclipped comparison with `ν_e t − 24 g² t²`.
//!
//! Replicates `quantum_lattice.py` and `worked_examples.py`.  Ledger A1
//! (Pass 45 premise inventory: `ν_e = 2`, isolated `g = 1`, full incident
//! `g = 101`), E2/E4 (the Pass 45 counterexample at `t = 0.03` and the
//! positive-RHS two-qubit check at `t = 0.01`), F1/F2 (the two-qubit XX
//! closed form `1/√2 + 1/4` at `t = π/8` and the four-site TFIM rates
//! `ν_e = 2|J|`), F3 (TFIM `g = 3.5 ≤ 2|J| + |h|`).
//!
//! Everything here is a floating-point replay; the tolerances travel with
//! the values.  The paper's Theorem 5.1 is not proved by any of it, and
//! Pass 45 is what it says: a counterexample to substituting the isolated
//! two-site `g` for the full incident `g`.

use std::collections::BTreeMap;

use super::numeric::{embed, evolution_operator, hermitian_eigen, min_eigenvalue_hermitian, operator_norm_hermitian, partial_trace, paulis, trace_norm_hermitian, CMatrix, C};

/// Validation tolerance for Hermiticity, trace, positivity.
pub const DEFAULT_VALIDATION_ATOL: f64 = 1.0e-10;
/// Comparison tolerance for the signed bound.
pub const DEFAULT_COMPARISON_ATOL: f64 = 1.0e-9;

/// One validated Hermitian one- or two-site Hamiltonian term; the matrix
/// tensor-factor order is exactly `support`.
#[derive(Clone, Debug, PartialEq)]
pub struct LocalHamiltonianTerm {
    /// Label.
    pub label: String,
    /// Sites, in tensor order.
    pub support: Vec<String>,
    /// The operator.
    pub operator: CMatrix,
}

impl LocalHamiltonianTerm {
    /// Build and validate.
    pub fn new(label: &str, support: &[&str], operator: CMatrix) -> Result<LocalHamiltonianTerm, String> {
        if label.trim().is_empty() {
            return Err("Hamiltonian term labels must be nonempty strings".into());
        }
        if !(1..=2).contains(&support.len()) {
            return Err("Hamiltonian terms must have support size one or two".into());
        }
        if support.iter().any(|s| s.is_empty()) {
            return Err("Hamiltonian supports must contain nonempty site identifiers".into());
        }
        if support.len() == 2 && support[0] == support[1] {
            return Err("a Hamiltonian support may not repeat a site".into());
        }
        if operator.rows != operator.cols {
            return Err(format!("term {label:?} must be square"));
        }
        if !operator.is_hermitian(DEFAULT_VALIDATION_ATOL) {
            return Err(format!("term {label:?} is not Hermitian; Frobenius defect={}", operator.hermiticity_defect()));
        }
        Ok(LocalHamiltonianTerm { label: label.to_string(), support: support.iter().map(|s| s.to_string()).collect(), operator })
    }
}

/// Numerical inventory for the paper's full incident norm `g`.
#[derive(Clone, Debug, PartialEq)]
pub struct IncidentNormReplay {
    /// `(label, ‖h_X‖_op)`.
    pub term_operator_norms: Vec<(String, f64)>,
    /// `(site, Σ_{X∋v} ‖h_X‖)`.
    pub per_site_loads: Vec<(String, f64)>,
    /// The maximum load.
    pub g: f64,
}

/// Numerical replay of `L_e`, `P_e L_e`, `n_e = Q_e L_e`, and `ν_e`.
#[derive(Clone, Debug, PartialEq)]
pub struct EdgeNormalRateReplay {
    /// The designated target edge.
    pub edge: (String, String),
    /// The terms used.
    pub term_labels: Vec<String>,
    /// `L_e`.
    pub l_e: CMatrix,
    /// `P_e L_e`.
    pub p_e_l_e: CMatrix,
    /// `n_e`.
    pub n_e: CMatrix,
    /// `‖n_e‖₁`.
    pub nu_e: f64,
    /// `|Tr L_e|`.
    pub l_e_trace_error: f64,
    /// `‖Tr_b n_e‖₁`.
    pub normal_marginal_a_norm: f64,
    /// `‖Tr_a n_e‖₁`.
    pub normal_marginal_b_norm: f64,
    /// `‖L_e − P_e L_e − n_e‖_F`.
    pub decomposition_error: f64,
}

/// Deterministic eigendecomposition replay for one reduced edge defect.
#[derive(Clone, Debug, PartialEq)]
pub struct EdgeEvolutionReplay {
    /// The designated target edge.
    pub edge: (String, String),
    /// `t`.
    pub t: f64,
    /// `ρ_e(t)`.
    pub rho_edge_t: CMatrix,
    /// `ρ_a(t)`.
    pub rho_a_t: CMatrix,
    /// `ρ_b(t)`.
    pub rho_b_t: CMatrix,
    /// `ρ_a(t) ⊗ ρ_b(t)`.
    pub product_of_marginals_t: CMatrix,
    /// `ρ_e(t) − ρ_a(t) ⊗ ρ_b(t)`.
    pub defect_operator: CMatrix,
    /// Its trace norm `D_e(t)`.
    pub defect: f64,
    /// `‖H V − V Λ‖_F`.
    pub eigendecomposition_residual: f64,
    /// `‖U†U − I‖_F`.
    pub unitarity_error: f64,
    /// `|Tr ρ(t) − 1|`.
    pub state_trace_error: f64,
    /// `‖ρ(t) − ρ(t)†‖_F`.
    pub state_hermiticity_error: f64,
    /// `min λ(ρ(t))`.
    pub state_minimum_eigenvalue: f64,
}

/// One finite numerical comparison with an unclipped signed theorem RHS.
#[derive(Clone, Debug, PartialEq)]
pub struct ShortTimeBoundReplay {
    /// The designated target edge.
    pub edge: (String, String),
    /// `t`.
    pub t: f64,
    /// `ν_e`.
    pub nu_e: f64,
    /// Full incident `g`.
    pub full_incident_g: f64,
    /// `D_e(t)`.
    pub observed_defect: f64,
    /// `ν_e t − 24 g² t²`, signed.
    pub signed_lower_bound_rhs: f64,
    /// `D_e(t) − rhs`.
    pub numerical_margin: f64,
    /// The tolerance used.
    pub comparison_tolerance: f64,
    /// `margin ≥ −tolerance`.
    pub bound_satisfied_with_tolerance: bool,
}

/// Validated finite one-/two-local Hamiltonian with a product initial state.
#[derive(Clone, Debug, PartialEq)]
pub struct FiniteQuantumLattice {
    /// Sites, in tensor order.
    pub site_order: Vec<String>,
    /// Site → local dimension.
    pub dimensions: BTreeMap<String, usize>,
    /// The terms.
    pub terms: Vec<LocalHamiltonianTerm>,
    /// Site → local density matrix.
    pub product_state: BTreeMap<String, CMatrix>,
    /// Validation tolerance.
    pub validation_atol: f64,
}

impl FiniteQuantumLattice {
    /// Build and validate every premise of the finite quantum host.
    pub fn new(site_order: &[&str], dimensions: BTreeMap<String, usize>, terms: Vec<LocalHamiltonianTerm>, product_state: BTreeMap<String, CMatrix>) -> Result<FiniteQuantumLattice, String> {
        let atol = DEFAULT_VALIDATION_ATOL;
        let sites: Vec<String> = site_order.iter().map(|s| s.to_string()).collect();
        if sites.is_empty() || sites.iter().any(String::is_empty) {
            return Err("site_order must contain nonempty site identifiers".into());
        }
        let mut sorted = sites.clone();
        sorted.sort();
        sorted.dedup();
        if sorted.len() != sites.len() {
            return Err("site_order contains duplicates".into());
        }
        if dimensions.keys().cloned().collect::<Vec<_>>() != sorted {
            return Err("dimensions must cover exactly site_order".into());
        }
        if dimensions.values().any(|&d| d == 0) {
            return Err("dimensions must be positive integers".into());
        }
        let mut labels: Vec<&str> = terms.iter().map(|t| t.label.as_str()).collect();
        labels.sort();
        labels.dedup();
        if labels.len() != terms.len() {
            return Err("Hamiltonian term labels must be unique".into());
        }
        for t in &terms {
            if let Some(u) = t.support.iter().find(|s| !dimensions.contains_key(*s)) {
                return Err(format!("term {:?} references unknown sites [{u:?}]", t.label));
            }
            let expected: usize = t.support.iter().map(|s| dimensions[s]).product();
            if t.operator.shape() != (expected, expected) {
                return Err(format!("term {:?} has shape {:?}, expected {:?}", t.label, t.operator.shape(), (expected, expected)));
            }
        }
        if product_state.keys().cloned().collect::<Vec<_>>() != sorted {
            return Err("product_state must cover exactly site_order".into());
        }
        for s in &sites {
            let st = &product_state[s];
            let d = dimensions[s];
            if st.shape() != (d, d) {
                return Err(format!("local state at {s:?} has shape {:?}, expected {:?}", st.shape(), (d, d)));
            }
            if !st.is_hermitian(atol) {
                return Err(format!("local state at {s:?} is not Hermitian"));
            }
            let trace_error = (st.trace() - C::ONE).abs();
            if trace_error > atol {
                return Err(format!("local state at {s:?} is not trace one; error={trace_error}"));
            }
            let min = min_eigenvalue_hermitian(st, atol)?;
            if min < -atol {
                return Err(format!("local state at {s:?} is not positive semidefinite; minimum eigenvalue={min}"));
            }
        }
        Ok(FiniteQuantumLattice { site_order: sites, dimensions, terms, product_state, validation_atol: atol })
    }

    fn dims(&self) -> Vec<usize> {
        self.site_order.iter().map(|s| self.dimensions[s]).collect()
    }

    fn position(&self, site: &str) -> Result<usize, String> {
        self.site_order.iter().position(|s| s == site).ok_or_else(|| format!("unknown site {site:?}"))
    }

    /// `Π_v d_v`.
    pub fn total_dimension(&self) -> usize {
        self.dims().iter().product()
    }

    /// `ρ₀ = ⊗_v ρ_v`.
    pub fn initial_state(&self) -> CMatrix {
        let mut out = CMatrix::eye(1);
        for s in &self.site_order {
            out = out.kron(&self.product_state[s]);
        }
        out
    }

    /// The edge with its sites in `site_order` position.
    pub fn canonical_edge(&self, a: &str, b: &str) -> Result<(String, String), String> {
        if a == b {
            return Err("an edge must contain two distinct sites".into());
        }
        let (pa, pb) = (self.position(a)?, self.position(b)?);
        Ok(if pa < pb { (a.to_string(), b.to_string()) } else { (b.to_string(), a.to_string()) })
    }

    /// Embed an operator on arbitrary, possibly nonadjacent, sites.
    pub fn embed_operator(&self, operator: &CMatrix, support: &[String]) -> Result<CMatrix, String> {
        let mut positions = Vec::new();
        for s in support {
            positions.push(self.position(s)?);
        }
        Ok(embed(operator, &positions, &self.dims()))
    }

    fn selected_terms(&self, labels: Option<&[&str]>) -> Result<Vec<&LocalHamiltonianTerm>, String> {
        let Some(labels) = labels else { return Ok(self.terms.iter().collect()) };
        let mut out = Vec::new();
        for l in labels {
            if !self.terms.iter().any(|t| t.label == *l) {
                return Err(format!("unknown Hamiltonian term labels [{l:?}]"));
            }
        }
        for t in &self.terms {
            if labels.contains(&t.label.as_str()) {
                out.push(t);
            }
        }
        Ok(out)
    }

    /// The global Hamiltonian for all or selected local terms.
    pub fn hamiltonian(&self, labels: Option<&[&str]>) -> Result<CMatrix, String> {
        let n = self.total_dimension();
        let mut h = CMatrix::zeros(n, n);
        for t in self.selected_terms(labels)? {
            h = h.add(&self.embed_operator(&t.operator, &t.support)?);
        }
        Ok(h)
    }

    /// Trace to `keep_sites`, factors in the requested order.
    pub fn partial_trace(&self, m: &CMatrix, keep_sites: &[&str]) -> Result<CMatrix, String> {
        let mut keep = Vec::new();
        for s in keep_sites {
            keep.push(self.position(s)?);
        }
        Ok(partial_trace(m, &self.dims(), &keep))
    }

    /// `g = max_v Σ_{X∋v} ‖h_X‖_op` over all terms.
    pub fn incident_norm_replay(&self) -> Result<IncidentNormReplay, String> {
        let mut norms = Vec::new();
        for t in &self.terms {
            norms.push((t.label.clone(), operator_norm_hermitian(&t.operator, self.validation_atol)?));
        }
        let loads: Vec<(String, f64)> = self
            .site_order
            .iter()
            .map(|s| (s.clone(), self.terms.iter().zip(&norms).filter(|(t, _)| t.support.contains(s)).map(|(_, n)| n.1).sum()))
            .collect();
        let g = loads.iter().fold(0.0_f64, |m, (_, l)| m.max(*l));
        Ok(IncidentNormReplay { term_operator_norms: norms, per_site_loads: loads, g })
    }

    /// `−i[H, ρ₀]` for selected finite terms.
    pub fn global_derivative(&self, labels: Option<&[&str]>) -> Result<CMatrix, String> {
        let h = self.hamiltonian(labels)?;
        let rho0 = self.initial_state();
        Ok(h.mul(&rho0).sub(&rho0.mul(&h)).scale(C::new(0.0, -1.0)))
    }

    /// The product-retraction tangent map `P_e` on a trace-zero tangent:
    /// `P_e(T) = Tr_b(T) ⊗ ρ_b + ρ_a ⊗ Tr_a(T)`.
    pub fn apply_p_e(&self, edge: (&str, &str), tangent: &CMatrix) -> Result<CMatrix, String> {
        let (a, b) = self.canonical_edge(edge.0, edge.1)?;
        let (da, db) = (self.dimensions[&a], self.dimensions[&b]);
        if tangent.shape() != (da * db, da * db) {
            return Err(format!("edge tangent has shape {:?}, expected {:?}", tangent.shape(), (da * db, da * db)));
        }
        let trace_error = tangent.trace().abs();
        if trace_error > 100.0 * self.validation_atol {
            return Err(format!("P_e is declared here on trace-zero tangents; trace error={trace_error}"));
        }
        let marginal_a = partial_trace(tangent, &[da, db], &[0]);
        let marginal_b = partial_trace(tangent, &[da, db], &[1]);
        Ok(marginal_a.kron(&self.product_state[&b]).add(&self.product_state[&a].kron(&marginal_b)))
    }

    /// `n_e = Q_e L_e` and `ν_e = ‖n_e‖₁`.
    pub fn normal_rate_replay(&self, edge: (&str, &str), labels: Option<&[&str]>) -> Result<EdgeNormalRateReplay, String> {
        let (a, b) = self.canonical_edge(edge.0, edge.1)?;
        let term_labels: Vec<String> = self.selected_terms(labels)?.iter().map(|t| t.label.clone()).collect();
        let l_e = self.partial_trace(&self.global_derivative(labels)?, &[&a, &b])?;
        let p_e_l_e = self.apply_p_e((&a, &b), &l_e)?;
        let n_e = l_e.sub(&p_e_l_e);
        let (da, db) = (self.dimensions[&a], self.dimensions[&b]);
        let marginal_a = partial_trace(&n_e, &[da, db], &[0]);
        let marginal_b = partial_trace(&n_e, &[da, db], &[1]);
        let atol = self.validation_atol;
        Ok(EdgeNormalRateReplay {
            edge: (a, b),
            term_labels,
            nu_e: trace_norm_hermitian(&n_e, atol)?,
            l_e_trace_error: l_e.trace().abs(),
            normal_marginal_a_norm: trace_norm_hermitian(&marginal_a, atol)?,
            normal_marginal_b_norm: trace_norm_hermitian(&marginal_b, atol)?,
            decomposition_error: l_e.sub(&p_e_l_e).sub(&n_e).frobenius(),
            l_e,
            p_e_l_e,
            n_e,
        })
    }

    /// The evolved edge defect through the Hermitian eigendecomposition.
    pub fn edge_evolution_replay(&self, edge: (&str, &str), t: f64) -> Result<EdgeEvolutionReplay, String> {
        if !t.is_finite() || t < 0.0 {
            return Err("t must be finite and nonnegative".into());
        }
        let (a, b) = self.canonical_edge(edge.0, edge.1)?;
        let h = self.hamiltonian(None)?;
        let (u, residual, unitarity) = evolution_operator(&h, t, self.validation_atol)?;
        let rho0 = self.initial_state();
        let rho_t = u.mul(&rho0).mul(&u.adjoint());
        let rho_edge = self.partial_trace(&rho_t, &[&a, &b])?;
        let (da, db) = (self.dimensions[&a], self.dimensions[&b]);
        let rho_a = partial_trace(&rho_edge, &[da, db], &[0]);
        let rho_b = partial_trace(&rho_edge, &[da, db], &[1]);
        let product = rho_a.kron(&rho_b);
        let defect_operator = rho_edge.sub(&product);
        let atol = self.validation_atol;
        Ok(EdgeEvolutionReplay {
            edge: (a, b),
            t,
            defect: trace_norm_hermitian(&defect_operator, atol)?,
            eigendecomposition_residual: residual,
            unitarity_error: unitarity,
            state_trace_error: (rho_t.trace() - C::ONE).abs(),
            state_hermiticity_error: rho_t.hermiticity_defect(),
            state_minimum_eigenvalue: hermitian_eigen(&rho_t, atol)?.values.iter().fold(f64::INFINITY, |m, x| m.min(*x)),
            rho_edge_t: rho_edge,
            rho_a_t: rho_a,
            rho_b_t: rho_b,
            product_of_marginals_t: product,
            defect_operator,
        })
    }

    /// Compare one observed defect with `ν_e t − 24 g² t²`, unclipped.
    pub fn short_time_bound_replay(&self, edge: (&str, &str), t: f64, tolerance: f64) -> Result<ShortTimeBoundReplay, String> {
        if tolerance <= 0.0 || !tolerance.is_finite() {
            return Err("comparison_tolerance must be strictly positive".into());
        }
        let evolution = self.edge_evolution_replay(edge, t)?;
        let normal = self.normal_rate_replay(edge, None)?;
        let g = self.incident_norm_replay()?.g;
        let rhs = normal.nu_e * evolution.t - 24.0 * g * g * evolution.t * evolution.t;
        let margin = evolution.defect - rhs;
        Ok(ShortTimeBoundReplay {
            edge: evolution.edge.clone(),
            t: evolution.t,
            nu_e: normal.nu_e,
            full_incident_g: g,
            observed_defect: evolution.defect,
            signed_lower_bound_rhs: rhs,
            numerical_margin: margin,
            comparison_tolerance: tolerance,
            bound_satisfied_with_tolerance: margin >= -tolerance,
        })
    }

    /// `ν_e / (48 g²)` for this finite replay, or zero.
    pub fn half_slope_window(&self, edge: (&str, &str)) -> Result<f64, String> {
        let nu = self.normal_rate_replay(edge, None)?.nu_e;
        let g = self.incident_norm_replay()?.g;
        if nu <= self.validation_atol || g <= self.validation_atol {
            return Ok(0.0);
        }
        Ok(nu / (48.0 * g * g))
    }
}

/// §6.1 — the two-qubit XX carrier `H = J X⊗X`, both qubits in `|0⟩`.
pub fn two_qubit_xx_lattice(coupling: f64) -> Result<FiniteQuantumLattice, String> {
    let (x, _, _) = paulis();
    let zero = CMatrix::density(&[C::ONE, C::ZERO]);
    FiniteQuantumLattice::new(
        &["a", "b"],
        BTreeMap::from([("a".to_string(), 2), ("b".to_string(), 2)]),
        vec![LocalHamiltonianTerm::new("ab", &["a", "b"], x.kron(&x).scale_real(coupling))?],
        BTreeMap::from([("a".to_string(), zero.clone()), ("b".to_string(), zero)]),
    )
}

/// §6.1 replayed at `t = π/(8|J|)`.
#[derive(Clone, Debug, PartialEq)]
pub struct TwoQubitXXExampleReplay {
    /// `J`.
    pub coupling: f64,
    /// `t`.
    pub t: f64,
    /// `D_e(t)` observed.
    pub observed_defect: f64,
    /// `2cs + 2c²s²` with `θ = |J|t`.
    pub closed_form_defect: f64,
    /// `|observed − closed form|`.
    pub absolute_error: f64,
    /// `1/√2 + 1/4`.
    pub expected_special_value: f64,
}

/// Replay §6.1 at `t = π/(8|J|)`.
pub fn two_qubit_xx_example(coupling: f64) -> Result<TwoQubitXXExampleReplay, String> {
    if coupling == 0.0 {
        return Err("the §6.1 special time requires nonzero coupling".into());
    }
    let lattice = two_qubit_xx_lattice(coupling)?;
    let t = std::f64::consts::PI / (8.0 * coupling.abs());
    let observed = lattice.edge_evolution_replay(("a", "b"), t)?.defect;
    let theta = coupling.abs() * t;
    let (c, s) = (theta.cos(), theta.sin());
    let closed = 2.0 * c * s + 2.0 * c * c * s * s;
    Ok(TwoQubitXXExampleReplay {
        coupling,
        t,
        observed_defect: observed,
        closed_form_defect: closed,
        absolute_error: (observed - closed).abs(),
        expected_special_value: 1.0 / 2.0f64.sqrt() + 0.25,
    })
}

/// §6.2 — the open-chain TFIM rates `ν_e = 2|J|`.
#[derive(Clone, Debug, PartialEq)]
pub struct TFIMNormalRateReplay {
    /// Sites.
    pub num_sites: usize,
    /// `J`.
    pub coupling: f64,
    /// `h`.
    pub field: f64,
    /// Per-bond rates.
    pub edge_rates: Vec<((String, String), f64)>,
    /// `2|J|`.
    pub expected_rate: f64,
    /// `max |ν_e − 2|J||`.
    pub maximum_rate_error: f64,
    /// Full incident `g`.
    pub full_incident_g: f64,
    /// `2|J| + |h|`.
    pub paper_g_upper_bound: f64,
    /// `g ≤ 2|J| + |h|`.
    pub g_within_paper_bound: bool,
    /// Every bond has a positive rate.
    pub all_edges_active: bool,
}

/// Replay the §6.2 open-chain rates.
pub fn tfim_normal_rate_example(num_sites: usize, coupling: f64, field: f64) -> Result<TFIMNormalRateReplay, String> {
    if num_sites < 2 {
        return Err("num_sites must be an integer at least two".into());
    }
    let (x, _, z) = paulis();
    let plus = CMatrix::density(&[C::real(std::f64::consts::FRAC_1_SQRT_2), C::real(std::f64::consts::FRAC_1_SQRT_2)]);
    let sites: Vec<String> = (0..num_sites).map(|i| format!("q{i}")).collect();
    let site_refs: Vec<&str> = sites.iter().map(String::as_str).collect();
    let mut terms = Vec::new();
    for (i, s) in sites.iter().enumerate() {
        terms.push(LocalHamiltonianTerm::new(&format!("field_{i}"), &[s], x.scale_real(-field))?);
    }
    for i in 0..num_sites - 1 {
        terms.push(LocalHamiltonianTerm::new(&format!("bond_{i}_{}", i + 1), &[&sites[i], &sites[i + 1]], z.kron(&z).scale_real(-coupling))?);
    }
    let lattice = FiniteQuantumLattice::new(
        &site_refs,
        sites.iter().map(|s| (s.clone(), 2)).collect(),
        terms,
        sites.iter().map(|s| (s.clone(), plus.clone())).collect(),
    )?;
    let mut rates = Vec::new();
    for i in 0..num_sites - 1 {
        let nu = lattice.normal_rate_replay((&sites[i], &sites[i + 1]), None)?.nu_e;
        rates.push(((sites[i].clone(), sites[i + 1].clone()), nu));
    }
    let expected = 2.0 * coupling.abs();
    let max_error = rates.iter().fold(0.0_f64, |m, (_, r)| m.max((r - expected).abs()));
    let paper_bound = 2.0 * coupling.abs() + field.abs();
    let g = lattice.incident_norm_replay()?.g;
    let tolerance = 100.0 * DEFAULT_COMPARISON_ATOL;
    Ok(TFIMNormalRateReplay {
        num_sites,
        coupling,
        field,
        g_within_paper_bound: g <= paper_bound + tolerance,
        all_edges_active: coupling != 0.0 && rates.iter().all(|(_, r)| *r > tolerance),
        edge_rates: rates,
        expected_rate: expected,
        maximum_rate_error: max_error,
        full_incident_g: g,
        paper_g_upper_bound: paper_bound,
    })
}

/// The three-qubit Pass 45 fixture: `H = Z⊗X` on `(u, v)` plus
/// `100·Y⊗Z` on `(u, w)`, state `|+⟩ ⊗ |+i⟩ ⊗ |0⟩`.
pub fn pass45_counterexample_lattice() -> Result<FiniteQuantumLattice, String> {
    let (x, y, z) = paulis();
    let h = std::f64::consts::FRAC_1_SQRT_2;
    let plus = CMatrix::density(&[C::real(h), C::real(h)]);
    let plus_i = CMatrix::density(&[C::real(h), C::new(0.0, h)]);
    let zero = CMatrix::density(&[C::ONE, C::ZERO]);
    FiniteQuantumLattice::new(
        &["u", "v", "w"],
        ["u", "v", "w"].iter().map(|s| (s.to_string(), 2)).collect(),
        vec![LocalHamiltonianTerm::new("uv", &["u", "v"], z.kron(&x))?, LocalHamiltonianTerm::new("uw", &["u", "w"], y.kron(&z).scale_real(100.0))?],
        BTreeMap::from([("u".to_string(), plus), ("v".to_string(), plus_i), ("w".to_string(), zero)]),
    )
}

/// The Pass 45 counterexample: isolated `g` versus full incident `g`.
#[derive(Clone, Debug, PartialEq)]
pub struct Pass45CounterexampleReplay {
    /// `t`.
    pub t: f64,
    /// `ν_e` on `(u, v)`.
    pub nu_e: f64,
    /// `‖h_uv‖_op`.
    pub isolated_two_site_g: f64,
    /// Full incident `g`.
    pub full_incident_g: f64,
    /// `D_e(t)`.
    pub observed_defect: f64,
    /// `ν_e t − 24 g_iso² t²`.
    pub isolated_signed_rhs: f64,
    /// `ν_e t − 24 g² t²`.
    pub full_signed_rhs: f64,
    /// The isolated bound is violated.
    pub isolated_bound_violated: bool,
    /// The full bound holds (trivially, its RHS being negative).
    pub full_bound_satisfied_with_tolerance: bool,
}

/// Replay the failure caused by substituting the isolated `g`.
pub fn pass45_counterexample_replay(t: f64, tolerance: f64) -> Result<Pass45CounterexampleReplay, String> {
    if t < 0.0 || !t.is_finite() {
        return Err("t must be nonnegative".into());
    }
    if tolerance <= 0.0 || !tolerance.is_finite() {
        return Err("comparison_tolerance must be strictly positive".into());
    }
    let lattice = pass45_counterexample_lattice()?;
    let normal = lattice.normal_rate_replay(("u", "v"), None)?;
    let evolution = lattice.edge_evolution_replay(("u", "v"), t)?;
    let uv = lattice.terms.iter().find(|x| x.label == "uv").expect("uv term");
    let isolated_g = operator_norm_hermitian(&uv.operator, lattice.validation_atol)?;
    let full_g = lattice.incident_norm_replay()?.g;
    let isolated_rhs = normal.nu_e * t - 24.0 * isolated_g * isolated_g * t * t;
    let full_rhs = normal.nu_e * t - 24.0 * full_g * full_g * t * t;
    Ok(Pass45CounterexampleReplay {
        t,
        nu_e: normal.nu_e,
        isolated_two_site_g: isolated_g,
        full_incident_g: full_g,
        observed_defect: evolution.defect,
        isolated_signed_rhs: isolated_rhs,
        full_signed_rhs: full_rhs,
        isolated_bound_violated: evolution.defect < isolated_rhs - tolerance,
        full_bound_satisfied_with_tolerance: evolution.defect >= full_rhs - tolerance,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    fn close(a: f64, b: f64, tol: f64) -> bool {
        (a - b).abs() <= tol
    }

    /// A1: `ν_e = 2`, isolated `g = 1`, full incident `g = 101`.
    #[test]
    fn pass45_premise_inventory() {
        let c = pass45_counterexample_replay(0.03, DEFAULT_COMPARISON_ATOL).unwrap();
        assert!(close(c.nu_e, 2.0, 1e-12), "nu_e={}", c.nu_e);
        assert!(close(c.isolated_two_site_g, 1.0, 1e-13));
        assert!(close(c.full_incident_g, 101.0, 1e-12));
    }

    /// E2/E4: at `t = 0.03` the observed defect is `0.00279503008110974`,
    /// the isolated RHS `0.0384` is violated, the full RHS `−220.2816`
    /// is trivially satisfied; the external term alone gives `ν_e ≈ 0`;
    /// at `t = 0.01` on the two-qubit carrier the RHS `0.0176` is positive
    /// and the observed `0.0201986400280886` satisfies it.
    #[test]
    fn the_pass45_counterexample_and_the_positive_rhs_check() {
        let c = pass45_counterexample_replay(0.03, DEFAULT_COMPARISON_ATOL).unwrap();
        assert!(close(c.observed_defect, 0.00279503008110974, 1e-11), "observed={}", c.observed_defect);
        assert!(close(c.isolated_signed_rhs, 0.0384, 1e-12));
        assert!(close(c.full_signed_rhs, -220.2816, 1e-9));
        assert!(c.isolated_bound_violated && c.full_bound_satisfied_with_tolerance);
        let lattice = pass45_counterexample_lattice().unwrap();
        let external = lattice.normal_rate_replay(("u", "v"), Some(&["uw"])).unwrap();
        assert!(external.nu_e < 1e-9, "external nu_e={}", external.nu_e);
        let all = lattice.normal_rate_replay(("u", "v"), None).unwrap();
        assert!(close(all.nu_e, 2.0, 1e-9));
        assert!(all.decomposition_error < 1e-14 && all.l_e_trace_error < 1e-12);
        let full = lattice.short_time_bound_replay(("u", "v"), 0.03, DEFAULT_COMPARISON_ATOL).unwrap();
        assert!(full.bound_satisfied_with_tolerance && full.signed_lower_bound_rhs < 0.0);
        let positive = two_qubit_xx_lattice(1.0).unwrap().short_time_bound_replay(("a", "b"), 0.01, DEFAULT_COMPARISON_ATOL).unwrap();
        assert!(close(positive.signed_lower_bound_rhs, 0.0176, 1e-12), "rhs={}", positive.signed_lower_bound_rhs);
        assert!(close(positive.observed_defect, 0.0201986400280886, 1e-11), "observed={}", positive.observed_defect);
        assert!(close(positive.nu_e, 2.0, 1e-12) && close(positive.full_incident_g, 1.0, 1e-13));
        assert!(positive.bound_satisfied_with_tolerance);
        let window = two_qubit_xx_lattice(1.0).unwrap().half_slope_window(("a", "b")).unwrap();
        assert!(close(window, 2.0 / 48.0, 1e-12));
    }

    /// F1/F2/F3: XX closed form `1/√2 + 1/4 ≈ 0.957106781186548`; TFIM
    /// rates `2|J|` on four sites; `g = 3.5 = 2|J| + |h|`.
    #[test]
    fn worked_examples_reproduce_the_closed_forms() {
        let xx = two_qubit_xx_example(1.0).unwrap();
        assert!(xx.absolute_error < 1e-12, "error={}", xx.absolute_error);
        assert!(close(xx.closed_form_defect, xx.expected_special_value, 1e-12));
        assert!(close(xx.observed_defect, 0.957106781186547, 1e-12));
        let tfim = tfim_normal_rate_example(4, 1.0, 1.5).unwrap();
        assert!(tfim.maximum_rate_error < 1e-10, "max error={}", tfim.maximum_rate_error);
        assert!(close(tfim.expected_rate, 2.0, 0.0));
        assert!(close(tfim.full_incident_g, 3.5, 1e-12) && close(tfim.paper_g_upper_bound, 3.5, 0.0));
        assert!(tfim.g_within_paper_bound && tfim.all_edges_active);
        assert_eq!(tfim.edge_rates.len(), 3);
    }

    #[test]
    fn premises_are_validated_at_construction() {
        let (x, _, _) = paulis();
        assert!(LocalHamiltonianTerm::new("bad", &["a", "b"], CMatrix::from_real_rows(&[&[0.0, 1.0], &[0.0, 0.0]])).is_err());
        assert!(LocalHamiltonianTerm::new("bad", &["a", "a"], x.kron(&x)).is_err());
        let not_a_state = CMatrix::from_real_rows(&[&[1.0, 0.0], &[0.0, 1.0]]);
        assert!(FiniteQuantumLattice::new(
            &["a"],
            BTreeMap::from([("a".to_string(), 2)]),
            vec![],
            BTreeMap::from([("a".to_string(), not_a_state)])
        )
        .unwrap_err()
        .contains("trace one"));
        let l = two_qubit_xx_lattice(1.0).unwrap();
        assert!(l.canonical_edge("b", "a").unwrap() == ("a".to_string(), "b".to_string()));
        assert!(l.canonical_edge("a", "a").is_err());
        assert!(l.apply_p_e(("a", "b"), &CMatrix::eye(4)).is_err(), "P_e refuses a tangent with trace");
    }
}

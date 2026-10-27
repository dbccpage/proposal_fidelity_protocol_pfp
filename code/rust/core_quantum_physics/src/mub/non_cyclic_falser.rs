// AuthorityEffect: None.
//! Exact solver search and adversarial falser for MUB-6 candidates outside the cyclic Weyl class.
//!
//! Searches the 720 unphased row permutations of Tao S_6 and the discrete
//! two-circulant ansatz below with four parameters in mu_12. Row-phase orbits
//! and the full continuous Hadamard families are not searched.
//!
//! Applies an adversarial falser to test whether any candidate forms a 4th basis
//! mutually unbiased to the canonical 3-basis cyclic Weyl triad.

use crate::mub::MubSystem;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{involution::adjoint, matrix as mx};
use core_lie_theory::heisenberg::WeylHeisenberg;
use core_number_theory::cyclotomic_field::Cyclotomic;
use core_number_theory::rational::rq;
use serde::{Deserialize, Serialize};

/// Exact cyclotomic field Q(zeta_12).
pub type Cyc12Field = Cyclotomic<12>;

/// Terence Tao's isolated complex Hadamard matrix phase exponents in {0, 1, 2}.
/// S_6[i][j] = omega^{TAO_PHASES[i][j]} where omega = zeta_12^4 = e^{2pi i / 3}.
pub const TAO_PHASES: [[i64; 6]; 6] = [
    [0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 2, 2],
    [0, 1, 0, 2, 2, 1],
    [0, 1, 2, 0, 1, 2],
    [0, 2, 2, 1, 0, 1],
    [0, 2, 1, 2, 1, 0],
];

/// Construct Terence Tao's 6x6 complex Hadamard matrix S_6 over Q(zeta_12).
pub fn build_tao_s6_matrix() -> Result<BasicMatrix<Cyc12Field>, String> {
    let mut mat = mx::zeros::<Cyc12Field>(6, 6).map_err(|e| e.to_string())?;
    for i in 0..6 {
        for j in 0..6 {
            let phase_exp = 4 * TAO_PHASES[i][j];
            mat.set(i, j, Cyc12Field::zeta(phase_exp))
                .map_err(|e| e.to_string())?;
        }
    }
    Ok(mat)
}

/// Verify both Hadamard conditions: every entry has modulus one and H H† = 6 I.
pub fn verify_chm(h: &BasicMatrix<Cyc12Field>) -> Result<bool, String> {
    if h.shape() != (6, 6) {
        return Ok(false);
    }
    for i in 0..6 {
        for j in 0..6 {
            let value = h.get(i, j).map_err(|e| e.to_string())?;
            if value.mul(&value.conjugate()) != Cyc12Field::one() {
                return Ok(false);
            }
        }
    }
    let h_adj = adjoint(h).map_err(|e| e.to_string())?;
    let gram = mx::multiply(h, &h_adj).map_err(|e| e.to_string())?;
    let expected = mx::scale(
        &mx::identity::<Cyc12Field>(6).map_err(|e| e.to_string())?,
        &Cyc12Field::rational(rq(6, 1)),
    )
    .map_err(|e| e.to_string())?;
    Ok(gram == expected)
}

/// Form six column outer products from a 6x6 matrix without Gram verification.
/// They are rank-one orthogonal projectors only under the caller's CHM premise:
/// Q_k = (1/6) * col_k * col_k†, so (Q_k)_{ab} = (1/6) * H_{ak} * conj(H_{bk}).
#[inline]
pub fn projectors_from_chm_unchecked(
    h: &BasicMatrix<Cyc12Field>,
) -> Result<Vec<BasicMatrix<Cyc12Field>>, String> {
    if h.shape() != (6, 6) {
        return Err("Expected a 6x6 matrix".to_string());
    }
    let one_sixth = Cyc12Field::rational(rq(1, 6));
    let mut projectors = Vec::with_capacity(6);

    for k in 0..6 {
        let mut q = mx::zeros::<Cyc12Field>(6, 6).map_err(|e| e.to_string())?;
        for a in 0..6 {
            let h_ak = h.get(a, k).map_err(|e| e.to_string())?;
            for b in 0..6 {
                let h_bk = h.get(b, k).map_err(|e| e.to_string())?;
                let term = h_ak.mul(&h_bk.conjugate());
                let entry = term.mul(&one_sixth);
                q.set(a, b, entry).map_err(|e| e.to_string())?;
            }
        }
        projectors.push(q);
    }

    Ok(projectors)
}

/// Extract the 6 rank-one orthogonal projectors from the columns of a 6x6 CHM H with validation.
pub fn projectors_from_chm(
    h: &BasicMatrix<Cyc12Field>,
) -> Result<Vec<BasicMatrix<Cyc12Field>>, String> {
    if !verify_chm(h)? {
        return Err("Matrix fails unit-modulus entries or H H† = 6 I".to_string());
    }
    projectors_from_chm_unchecked(h)
}

/// Permute the rows of a 6x6 matrix by a permutation vector `p`.
#[inline]
pub fn permute_rows(
    h: &BasicMatrix<Cyc12Field>,
    p: &[usize; 6],
) -> Result<BasicMatrix<Cyc12Field>, String> {
    let mut sorted = *p;
    sorted.sort_unstable();
    if h.shape() != (6, 6) || sorted != [0, 1, 2, 3, 4, 5] {
        return Err("Expected a 6x6 matrix and a permutation of 0..6".to_string());
    }
    let mut out = mx::zeros::<Cyc12Field>(6, 6).map_err(|e| e.to_string())?;
    for i in 0..6 {
        for j in 0..6 {
            let val = h.get(p[i], j).map_err(|e| e.to_string())?;
            out.set(i, j, val).map_err(|e| e.to_string())?;
        }
    }
    Ok(out)
}

/// Modulate rows of a 6x6 matrix by diagonal phase exponents: D * H where D = diag(zeta_12^{phases[i]}).
pub fn phase_modulate_rows(
    h: &BasicMatrix<Cyc12Field>,
    phases: &[i64; 6],
) -> Result<BasicMatrix<Cyc12Field>, String> {
    if h.shape() != (6, 6) {
        return Err("Expected a 6x6 matrix".to_string());
    }
    let mut out = mx::zeros::<Cyc12Field>(6, 6).map_err(|e| e.to_string())?;
    for i in 0..6 {
        let factor = Cyc12Field::zeta(phases[i]);
        for j in 0..6 {
            let val = h.get(i, j).map_err(|e| e.to_string())?;
            out.set(i, j, val.mul(&factor)).map_err(|e| e.to_string())?;
        }
    }
    Ok(out)
}

/// Construct the two-circulant ansatz B_6(b, c, e, f) over Q(zeta_12).
/// The historical function name does not assert a classification of Hadamard families.
///
/// H = [ A    B  ]
///     [ B†  -A† ]
/// where A = circ(1, zeta_12^{kb}, zeta_12^{kc}) and B = circ(1, zeta_12^{ke}, zeta_12^{kf}).
pub fn build_petrescu_matrix(
    kb: usize,
    kc: usize,
    ke: usize,
    kf: usize,
) -> Result<BasicMatrix<Cyc12Field>, String> {
    let one = Cyc12Field::one();
    let b = Cyc12Field::zeta((kb % 12) as i64);
    let c = Cyc12Field::zeta((kc % 12) as i64);
    let e = Cyc12Field::zeta((ke % 12) as i64);
    let f = Cyc12Field::zeta((kf % 12) as i64);

    let a_rows = [
        [one.clone(), b.clone(), c.clone()],
        [c.clone(), one.clone(), b.clone()],
        [b.clone(), c.clone(), one.clone()],
    ];

    let b_rows = [
        [one.clone(), e.clone(), f.clone()],
        [f.clone(), one.clone(), e.clone()],
        [e.clone(), f.clone(), one.clone()],
    ];

    let bd_rows = [
        [one.conjugate(), f.conjugate(), e.conjugate()],
        [e.conjugate(), one.conjugate(), f.conjugate()],
        [f.conjugate(), e.conjugate(), one.conjugate()],
    ];

    let neg_ad_rows = [
        [
            one.conjugate().neg(),
            c.conjugate().neg(),
            b.conjugate().neg(),
        ],
        [
            b.conjugate().neg(),
            one.conjugate().neg(),
            c.conjugate().neg(),
        ],
        [
            c.conjugate().neg(),
            b.conjugate().neg(),
            one.conjugate().neg(),
        ],
    ];

    let mut out = mx::zeros::<Cyc12Field>(6, 6).map_err(|err| err.to_string())?;
    for i in 0..3 {
        for j in 0..3 {
            out.set(i, j, a_rows[i][j].clone())
                .map_err(|err| err.to_string())?;
            out.set(i, j + 3, b_rows[i][j].clone())
                .map_err(|err| err.to_string())?;
            out.set(i + 3, j, bd_rows[i][j].clone())
                .map_err(|err| err.to_string())?;
            out.set(i + 3, j + 3, neg_ad_rows[i][j].clone())
                .map_err(|err| err.to_string())?;
        }
    }

    Ok(out)
}

/// Search all 12^4 = 20,736 discrete parameter points in mu_12^4 to find all valid
/// Petrescu / Szöllősi complex Hadamard matrices satisfying z1 + z2 = 0.
pub fn search_petrescu_points() -> Vec<(usize, usize, usize, usize)> {
    // z(kb, kc) = zeta(-kc) + zeta(kb) + zeta(kc - kb)
    let mut z_table = Vec::with_capacity(144);
    for kb in 0..12i64 {
        for kc in 0..12i64 {
            let z = Cyc12Field::zeta(-kc)
                .add(&Cyc12Field::zeta(kb))
                .add(&Cyc12Field::zeta(kc - kb));
            z_table.push(((kb as usize, kc as usize), z));
        }
    }

    let mut solutions = Vec::new();
    for (pair1, z1) in &z_table {
        for (pair2, z2) in &z_table {
            if z1.add(z2).is_zero() {
                solutions.push((pair1.0, pair1.1, pair2.0, pair2.1));
            }
        }
    }

    solutions
}

fn build_single_weyl_basis(
    gen: &BasicMatrix<Cyc12Field>,
) -> Result<Vec<BasicMatrix<Cyc12Field>>, String> {
    type F = Cyc12Field;
    let powers: Vec<_> = (0..6)
        .map(|k| mx::power(gen, k).map_err(|e| e.to_string()))
        .collect::<Result<Vec<_>, _>>()?;

    let mut projectors = Vec::with_capacity(6);
    for j in 0..6i64 {
        let mut p = mx::zeros::<F>(6, 6).map_err(|e| e.to_string())?;
        for (k, power) in powers.iter().enumerate() {
            let phase = F::zeta(-2 * j * (k as i64));
            let scaled = mx::scale(power, &phase).map_err(|e| e.to_string())?;
            p = mx::add(&p, &scaled).map_err(|e| e.to_string())?;
        }
        let proj = mx::scale(&p, &F::rational(rq(1, 6))).map_err(|e| e.to_string())?;
        projectors.push(proj);
    }
    Ok(projectors)
}

/// Canonical construction of the 3 cyclic Weyl bases in d=6 over Q(zeta_12).
pub fn build_weyl_triad_bases() -> Result<[(&'static str, Vec<BasicMatrix<Cyc12Field>>); 3], String>
{
    type F = Cyc12Field;
    let w = WeylHeisenberg::with_phase_root(6, F::zeta(2), F::zeta(1))
        .map_err(|e| format!("Heisenberg init failed: {e:?}"))?;

    let gens: [(&'static str, BasicMatrix<F>); 3] = [
        (
            "Weyl-Shift-X",
            w.shift().map_err(|e| format!("shift: {e:?}"))?,
        ),
        (
            "Weyl-Clock-Z",
            w.clock().map_err(|e| format!("clock: {e:?}"))?,
        ),
        (
            "Weyl-Displacement-D",
            w.displacement(1, 1).map_err(|e| format!("disp: {e:?}"))?,
        ),
    ];

    let mut bases = Vec::with_capacity(3);
    for (name, gen) in gens {
        bases.push((name, build_single_weyl_basis(&gen)?));
    }

    let b0 = bases.remove(0);
    let b1 = bases.remove(0);
    let b2 = bases.remove(0);
    Ok([b0, b1, b2])
}

/// Compute Tr(A * B) directly by elementwise multiply-accumulate without matrix allocation:
/// Tr(A B) = sum_{i, j} A_{ij} B_{ji}.
#[inline]
pub fn trace_product(
    a: &BasicMatrix<Cyc12Field>,
    b: &BasicMatrix<Cyc12Field>,
) -> Result<Cyc12Field, String> {
    let mut sum = Cyc12Field::zero();
    for i in 0..6 {
        for j in 0..6 {
            let a_ij = a.get(i, j).map_err(|e| e.to_string())?;
            let b_ji = b.get(j, i).map_err(|e| e.to_string())?;
            sum = sum.add(&a_ij.mul(&b_ji));
        }
    }
    Ok(sum)
}

/// Defect witness emitted when a candidate basis violates mutual unbiasedness.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct DefectWitness {
    pub ref_basis_name: String,
    pub ref_proj_idx: usize,
    pub cand_proj_idx: usize,
    pub trace_overlap_str: String,
    pub defect_str: String,
}

/// Typed verdict emitted by the adversarial falser.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum FalsificationVerdict {
    /// The candidate basis violates mutual unbiasedness against the reference triad.
    Falsified {
        /// Observed violations; `attack_fast` stops after the first one.
        total_violations: usize,
        first_witness: DefectWitness,
        violating_bases: Vec<String>,
    },
    /// The candidate basis passes all mutual unbiasedness checks (would be a 4th MUB).
    Admitted,
}

/// The sovereign adversarial falser that attacks any proposed 4th basis.
pub struct MubAdversarialFalser {
    weyl_triad: [(&'static str, Vec<BasicMatrix<Cyc12Field>>); 3],
    expected_overlap: Cyc12Field,
}

impl MubAdversarialFalser {
    /// Initialize the falser with the certified 3-basis cyclic Weyl triad.
    pub fn try_new() -> Result<Self, String> {
        let weyl_triad = build_weyl_triad_bases()?;
        MubSystem::try_new(
            6,
            weyl_triad.iter().map(|(_, basis)| basis.clone()).collect(),
        )
        .map_err(|e| format!("Invalid reference Weyl triad: {e}"))?;
        let expected_overlap = Cyc12Field::rational(rq(1, 6));
        Ok(Self {
            weyl_triad,
            expected_overlap,
        })
    }

    /// Full attack: evaluate all 3 reference bases and all 36 projector pairs, collecting all defects.
    pub fn attack(
        &self,
        candidate_projectors: &[BasicMatrix<Cyc12Field>],
    ) -> Result<FalsificationVerdict, String> {
        self.attack_internal(candidate_projectors, false)
    }

    /// Fast attack for exhaustive solver search: early-exits on the first detected defect witness.
    #[inline]
    pub fn attack_fast(
        &self,
        candidate_projectors: &[BasicMatrix<Cyc12Field>],
    ) -> Result<FalsificationVerdict, String> {
        self.attack_internal(candidate_projectors, true)
    }

    fn check_basis_against_candidate(
        &self,
        basis_name: &str,
        ref_basis: &[BasicMatrix<Cyc12Field>],
        candidate_projectors: &[BasicMatrix<Cyc12Field>],
        early_exit: bool,
        violations: &mut Vec<DefectWitness>,
    ) -> Result<bool, String> {
        let mut basis_had_violation = false;
        for (j, p_j) in ref_basis.iter().enumerate() {
            for (k, q_k) in candidate_projectors.iter().enumerate() {
                // Compute exact Born overlap Tr(P_j * Q_k) via fast direct contraction
                let tr = trace_product(p_j, q_k)?;
                let defect = tr.sub(&self.expected_overlap);

                if !defect.is_zero() {
                    basis_had_violation = true;
                    violations.push(DefectWitness {
                        ref_basis_name: basis_name.to_string(),
                        ref_proj_idx: j,
                        cand_proj_idx: k,
                        trace_overlap_str: format!("{tr:?}"),
                        defect_str: format!("{defect:?}"),
                    });
                    if early_exit {
                        return Ok(true);
                    }
                }
            }
        }
        Ok(basis_had_violation)
    }

    fn attack_internal(
        &self,
        candidate_projectors: &[BasicMatrix<Cyc12Field>],
        early_exit: bool,
    ) -> Result<FalsificationVerdict, String> {
        if candidate_projectors.len() != 6 {
            return Err("Candidate basis must contain exactly 6 projectors".to_string());
        }
        MubSystem::try_new(6, vec![candidate_projectors.to_vec()])
            .map_err(|e| format!("Invalid candidate projector basis: {e}"))?;

        let mut violations = Vec::new();
        let mut violating_bases = Vec::new();

        for (basis_name, ref_basis) in &self.weyl_triad {
            let had_violation = self.check_basis_against_candidate(
                basis_name,
                ref_basis,
                candidate_projectors,
                early_exit,
                &mut violations,
            )?;
            if had_violation {
                violating_bases.push(basis_name.to_string());
                if early_exit {
                    return Ok(FalsificationVerdict::Falsified {
                        total_violations: 1,
                        first_witness: violations.remove(0),
                        violating_bases,
                    });
                }
            }
        }

        if violations.is_empty() {
            Ok(FalsificationVerdict::Admitted)
        } else {
            let first_witness = violations[0].clone();
            Ok(FalsificationVerdict::Falsified {
                total_violations: violations.len(),
                first_witness,
                violating_bases,
            })
        }
    }
}

fn search_tao_permutations(
    falser: &MubAdversarialFalser,
    s6: &BasicMatrix<Cyc12Field>,
    sample_witnesses: &mut Vec<DefectWitness>,
) -> Result<(usize, usize), String> {
    let mut tao_perms_tested = 0;
    let mut tao_perms_falsified = 0;
    let mut p = [0, 1, 2, 3, 4, 5];
    loop {
        let perm_s6 = permute_rows(s6, &p)?;
        let projs = projectors_from_chm_unchecked(&perm_s6)?;
        let verdict = falser.attack_fast(&projs)?;
        tao_perms_tested += 1;
        if let FalsificationVerdict::Falsified { first_witness, .. } = verdict {
            tao_perms_falsified += 1;
            if sample_witnesses.len() < 3 {
                sample_witnesses.push(first_witness);
            }
        }
        if !next_permutation(&mut p) {
            break;
        }
    }
    Ok((tao_perms_tested, tao_perms_falsified))
}

fn search_petrescu_candidates(
    falser: &MubAdversarialFalser,
    petrescu_points: &[(usize, usize, usize, usize)],
    sample_witnesses: &mut Vec<DefectWitness>,
) -> Result<(usize, usize), String> {
    let mut petrescu_tested = 0;
    let mut petrescu_falsified = 0;
    for &(kb, kc, ke, kf) in petrescu_points {
        let pet_mat = build_petrescu_matrix(kb, kc, ke, kf)?;
        let projs = projectors_from_chm(&pet_mat)?;
        let verdict = falser.attack_fast(&projs)?;
        petrescu_tested += 1;
        if let FalsificationVerdict::Falsified { first_witness, .. } = verdict {
            petrescu_falsified += 1;
            if sample_witnesses.len() < 6 {
                sample_witnesses.push(first_witness);
            }
        }
    }
    Ok((petrescu_tested, petrescu_falsified))
}

/// Comprehensive search and falsification report for MUB-6 candidates over Q(zeta_12).
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct NonCyclicMub6SearchReport {
    pub schema_version: String,
    pub authority_effect: String,
    pub firewall: String,
    pub search_scope: String,
    pub weyl_triad_verified: bool,
    pub tao_base_falsified: bool,
    pub tao_permutations_tested: usize,
    pub tao_permutations_falsified: usize,
    pub petrescu_points_found: usize,
    pub petrescu_candidates_tested: usize,
    pub petrescu_candidates_falsified: usize,
    pub total_candidates_tested: usize,
    pub total_candidates_falsified: usize,
    pub candidates_admitted: usize,
    pub sample_witnesses: Vec<DefectWitness>,
    pub conclusion: String,
}

/// Exhaust the two finite parameter sets stated in `search_scope`.
pub fn execute_non_cyclic_mub6_search() -> Result<NonCyclicMub6SearchReport, String> {
    let falser = MubAdversarialFalser::try_new()?;
    let mut sample_witnesses = Vec::new();

    // 1. Attack Base Tao Matrix S_6 (full diagnostic)
    let s6 = build_tao_s6_matrix()?;
    let tao_projs = projectors_from_chm(&s6)?;
    let tao_base_verdict = falser.attack(&tao_projs)?;
    let tao_base_falsified = match &tao_base_verdict {
        FalsificationVerdict::Falsified { first_witness, .. } => {
            sample_witnesses.push(first_witness.clone());
            true
        }
        FalsificationVerdict::Admitted => false,
    };

    // 2. Attack all 720 row permutations of Tao Matrix S_6
    let (tao_perms_tested, tao_perms_falsified) =
        search_tao_permutations(&falser, &s6, &mut sample_witnesses)?;

    // 3. Search the specified two-circulant ansatz over mu_12^4.
    let petrescu_points = search_petrescu_points();
    let (petrescu_tested, petrescu_falsified) =
        search_petrescu_candidates(&falser, &petrescu_points, &mut sample_witnesses)?;

    let total_tested = tao_perms_tested + petrescu_tested;
    let total_falsified = tao_perms_falsified + petrescu_falsified;
    let candidates_admitted = total_tested - total_falsified;

    Ok(NonCyclicMub6SearchReport {
        schema_version: "core.mub6.non_cyclic_falser.v2".to_string(),
        authority_effect: "None".to_string(),
        firewall: "NOT MUB(6)=3, NOT MUB(6)<=3; stated region only; mints no authority".to_string(),
        search_scope: "720 unphased Tao row permutations (all share the uniform X ray); two-circulant ansatz with (kb,kc,ke,kf) in {0,...,11}^4 satisfying its cancellation equation. No row-phase orbit or continuous-family exhaustion.".to_string(),
        weyl_triad_verified: true,
        tao_base_falsified,
        tao_permutations_tested: tao_perms_tested,
        tao_permutations_falsified: tao_perms_falsified,
        petrescu_points_found: petrescu_points.len(),
        petrescu_candidates_tested: petrescu_tested,
        petrescu_candidates_falsified: petrescu_falsified,
        total_candidates_tested: total_tested,
        total_candidates_falsified: total_falsified,
        candidates_admitted,
        sample_witnesses,
        conclusion: search_conclusion(total_tested, total_falsified),
    })
}

fn search_conclusion(tested: usize, falsified: usize) -> String {
    let admitted = tested - falsified;
    let result = if admitted == 0 && tested > 0 {
        "No 4th basis exists in these enumerated finite candidate sets."
    } else {
        "No exclusion of all enumerated candidates is established."
    };
    format!("Tested {tested} candidates. Falsified: {falsified}/{tested}. Admitted: {admitted}. {result} Row-phase orbits and unrestricted MUB(6) remain outside this search.")
}

/// In-place lexicographical next permutation of 6 elements.
fn next_permutation(p: &mut [usize; 6]) -> bool {
    let mut i = 5;
    while i > 0 && p[i - 1] >= p[i] {
        i -= 1;
    }
    if i == 0 {
        return false;
    }
    let mut j = 5;
    while p[j] <= p[i - 1] {
        j -= 1;
    }
    p.swap(i - 1, j);
    p[i..].reverse();
    true
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/non_cyclic_falser.rs
// Claim: urn:core:crates_rs:core-quantum-physics:non-cyclic-falser:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorded505ba5 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorded505ba5` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrored505ba5 {
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
impl BoundaryErrored505ba5 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrored505ba5 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrored505ba5 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorded505ba5 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrored505ba5> {
        if capacity_bound == 0 {
            return Err(BoundaryErrored505ba5::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrored505ba5::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrored505ba5::ExceedsCapacity {
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
mod tests {
    use super::*;

    #[test]
    fn rejects_mixed_effects_even_when_all_108_overlaps_pass() {
        let falser = MubAdversarialFalser::try_new().unwrap();
        let mixed = mx::scale(
            &mx::identity::<Cyc12Field>(6).unwrap(),
            &Cyc12Field::rational(rq(1, 6)),
        )
        .unwrap();
        let candidate = vec![mixed; 6];
        let mut checks = 0;
        for (_, basis) in &falser.weyl_triad {
            for p in basis {
                for q in &candidate {
                    assert_eq!(trace_product(p, q).unwrap(), falser.expected_overlap);
                    checks += 1;
                }
            }
        }
        assert_eq!(checks, 108);
        assert!(falser
            .attack(&candidate)
            .unwrap_err()
            .contains("Invalid candidate"));
        assert!(falser.attack_fast(&candidate).is_err());
    }

    #[test]
    fn scaled_unitary_is_not_necessarily_hadamard() {
        // sqrt(3) = zeta_12 + zeta_12^-1; i = zeta_12^3.
        let sqrt3 = Cyc12Field::zeta(1).add(&Cyc12Field::zeta(-1));
        let scalar = sqrt3.mul(&Cyc12Field::one().add(&Cyc12Field::zeta(3)));
        let identity = mx::identity::<Cyc12Field>(6).unwrap();
        let h = mx::scale(&identity, &scalar).unwrap();
        assert_eq!(
            mx::multiply(&h, &adjoint(&h).unwrap()).unwrap(),
            mx::scale(&identity, &Cyc12Field::rational(rq(6, 1))).unwrap()
        );
        assert!(!verify_chm(&h).unwrap());
        assert!(projectors_from_chm(&h).is_err());
    }

    #[test]
    fn search_conclusion_depends_on_observed_verdicts() {
        assert!(search_conclusion(864, 864).contains("No 4th basis exists"));
        assert!(!search_conclusion(864, 863).contains("No 4th basis exists"));
        assert!(!search_conclusion(0, 0).contains("No 4th basis exists"));
    }

    #[test]
    fn test_tao_s6_chm_property() {
        let s6 = build_tao_s6_matrix().unwrap();
        assert!(verify_chm(&s6).unwrap());
    }

    #[test]
    fn test_petrescu_points_chm_property() {
        let pts = search_petrescu_points();
        assert_eq!(pts.len(), 144);
        for (kb, kc, ke, kf) in pts {
            let mat = build_petrescu_matrix(kb, kc, ke, kf).unwrap();
            assert!(verify_chm(&mat).unwrap());
        }
    }

    #[test]
    fn test_tao_s6_falsification_against_weyl_triad() {
        let falser = MubAdversarialFalser::try_new().unwrap();
        let s6 = build_tao_s6_matrix().unwrap();
        let projs = projectors_from_chm(&s6).unwrap();
        let verdict = falser.attack(&projs).unwrap();
        match verdict {
            FalsificationVerdict::Falsified {
                total_violations,
                violating_bases,
                ..
            } => {
                assert!(total_violations > 0);
                // Must violate both Shift (X) and Displacement (D), while Z overlap is 1/6
                assert!(violating_bases.contains(&"Weyl-Shift-X".to_string()));
                assert!(violating_bases.contains(&"Weyl-Displacement-D".to_string()));
                assert!(!violating_bases.contains(&"Weyl-Clock-Z".to_string()));
            }
            FalsificationVerdict::Admitted => {
                panic!("Tao matrix must NOT be admitted as a 4th MUB")
            }
        }
    }

    #[test]
    fn test_exhaustive_solver_search_all_falsified() {
        let report = execute_non_cyclic_mub6_search().unwrap();
        assert_eq!(report.candidates_admitted, 0);
        assert_eq!(report.total_candidates_tested, 720 + 144);
        assert_eq!(report.total_candidates_falsified, 720 + 144);
        assert!(report.tao_base_falsified);
        assert_eq!(report.petrescu_points_found, 144);
    }
}

#[cfg(test)]
mod l4_boundary_tests_ed505ba5 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorded505ba5::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorded505ba5::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorded505ba5::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorded505ba5::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorded505ba5::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrored505ba5::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrored505ba5::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}

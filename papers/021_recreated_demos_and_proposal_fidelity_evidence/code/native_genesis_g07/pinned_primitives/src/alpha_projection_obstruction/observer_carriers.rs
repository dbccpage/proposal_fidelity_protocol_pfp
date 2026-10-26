//! §7.4 — observer carriers over a covering-edge diagram: the raw tally
//! `I`, each observer's projected tally `J^α`, the visibility gap
//! `Λ = I − max_α J^α`, passivity (`J^α ≤ I_watched ≤ I`), the All-Green ⇔
//! joint-kernel characterisation, joint injectivity, the premise-gated
//! local-to-global implication, the three-patch Local-Green/Global-Red
//! witness with `I = 6λ` and every `J = 0`, the coupled carrier of
//! Proposition 7.4.7-B (joint kernels nontrivial, yet All-Green forces
//! `I = 0`), and the §7.4.12 quotient witness (`Φ([ω]) = 2 > 0`).
//!
//! Replicates `observer_carriers.py`, and adds the two inline replays the
//! Python package leaves to Lean (ledger H8, H9): both are finite linear
//! algebra and are computed here exactly.
//!
//! The estate's reading of §7.4 is the crosstab's *panel*: certification
//! up to the declared observers, never correspondence.  An All-Green report
//! is a statement about the observers' kernels as much as about the
//! section (§7.4.8 remark 4); the three-patch witness is the estate's
//! `ObserverIncomplete` terminal made concrete — every local observer is
//! green, the metatheory sees `I = 6`, and no `J` can be raised by refining
//! the section because the loss is in the kernels.

use std::collections::BTreeMap;

use super::cochain_presentation::{ExactnessCertificate, LinearRepairProblem, QuotientDistanceCertificate};
use super::covering_edge::{CoveringEdge, CoveringEdgeDiagram, Defects, Section};
use super::matrix::Matrix;
use super::rational::{q, Rational};

/// A nonempty finite edge domain with one contractive map per edge.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LocalObserverCarrier {
    /// Observer identifier.
    pub observer_id: String,
    /// Edge → contractive map (`rows × dim F_e`).
    pub maps: BTreeMap<String, Matrix>,
}

/// Exact values of the raw, observed, and lost defect tallies.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ObserverTallies {
    /// `I = Σ_e ‖Δ_e‖₁`, the raw coboundary tally.
    pub i: Rational,
    /// `J^α = Σ_{e watched by α} ‖q^α_e Δ_e‖₁`, the observed projected tallies per observer α.
    pub j: BTreeMap<String, Rational>,
    /// `Λ = I − max_α J^α`, the lost defect tally.
    pub lambda: Rational,
}

impl ObserverTallies {
    /// The raw coboundary tally `I`.
    pub fn raw_tally(&self) -> Rational {
        self.i
    }

    /// The observed projected tallies `J^α` keyed by observer identifier.
    pub fn projected_tallies(&self) -> &BTreeMap<String, Rational> {
        &self.j
    }

    /// The lost defect tally `Λ`.
    pub fn lost_defect_tally(&self) -> Rational {
        self.lambda
    }

    /// Recheck.
    pub fn verify(&self) -> bool {
        let Some(max) = self.j.values().copied().max() else { return false };
        self.i >= Rational::ZERO && self.j.values().all(|v| *v >= Rational::ZERO)
            && self.lambda == self.i - max && self.lambda >= Rational::ZERO
    }

    /// Every observer reports zero.
    pub fn all_green(&self) -> bool {
        self.verify() && self.j.values().all(|v| v.is_zero())
    }
}

/// One observer's row of the passivity table.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PassivityRow {
    /// Observer.
    pub observer_id: String,
    /// `J^α`.
    pub observed_j: Rational,
    /// The raw tally over the edges this observer watches.
    pub watched_raw_tally: Rational,
    /// `I`.
    pub raw_i: Rational,
    /// `J^α ≤ I_watched`.
    pub observed_le_watched: bool,
    /// `I_watched ≤ I`.
    pub watched_le_raw: bool,
}

/// Exact split of `Λ` into edgewise loss and observer fragmentation.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct VisibilityGapDecomposition {
    /// Declared observer carrier retained for replay.
    pub family: ObserverFamily,
    /// The exact supplied defect columns.
    pub defects: Defects,
    /// `p_e = max over watchers of ‖q Δ_e‖₁`.
    pub p_by_edge: BTreeMap<String, Rational>,
    /// `Σ_e (‖Δ_e‖₁ − p_e)`.
    pub edgewise_observation_loss: Rational,
    /// `Σ_e p_e − max_α J^α`.
    pub single_observer_fragmentation: Rational,
    /// `Λ`.
    pub lambda: Rational,
}

impl VisibilityGapDecomposition {
    /// Recheck.
    pub fn verify(&self) -> bool {
        let Ok(family) = ObserverFamily::new(self.family.edge_dimensions.clone(), self.family.observers.clone()) else { return false; };
        let Ok(defects) = family.normalize_defects(&self.defects) else { return false; };
        let Ok(tallies) = family.tallies(&defects) else { return false; };
        let projected: BTreeMap<String, Rational> = defects.iter().map(|(e, d)| {
            let value = family.watchers(e).iter().map(|o| o.maps[e].mul(d).l1_norm())
                .max().unwrap_or(Rational::ZERO);
            (e.clone(), value)
        }).collect();
        let loss = defects.iter().fold(Rational::ZERO, |a, (e, d)| a + d.l1_norm() - projected[e]);
        let fragmentation = projected.values().fold(Rational::ZERO, |a, v| a + *v)
            - tallies.j.values().copied().max().unwrap_or(Rational::ZERO);
        self.p_by_edge == projected && self.edgewise_observation_loss == loss
            && self.single_observer_fragmentation == fragmentation && self.lambda == tallies.lambda
            && loss >= Rational::ZERO && fragmentation >= Rational::ZERO && loss + fragmentation == self.lambda
    }
}

/// Finite exact check of `J^α ≤ I_watched ≤ I` (Proposition 7.4.3).
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct PassivityCertificate {
    /// Declared observer carrier retained for replay.
    pub family: ObserverFamily,
    /// The exact supplied defect columns.
    pub defects: Defects,
    /// One row per observer.
    pub rows: Vec<PassivityRow>,
    /// All rows pass.
    pub holds: bool,
}

impl PassivityCertificate {
    /// Recheck.
    pub fn verify(&self) -> bool {
        let Ok(family) = ObserverFamily::new(self.family.edge_dimensions.clone(), self.family.observers.clone()) else { return false; };
        let Ok(defects) = family.normalize_defects(&self.defects) else { return false; };
        let Ok(tallies) = family.tallies(&defects) else { return false; };
        let rows: Vec<PassivityRow> = family.observers.iter().map(|o| {
            let watched = o.maps.keys().fold(Rational::ZERO, |a, e| a + defects[e].l1_norm());
            let observed = tallies.j[&o.observer_id];
            PassivityRow { observer_id: o.observer_id.clone(), observed_j: observed,
                watched_raw_tally: watched, raw_i: tallies.i,
                observed_le_watched: observed <= watched, watched_le_raw: watched <= tallies.i }
        }).collect();
        self.rows == rows && !rows.is_empty() && self.holds
            && rows.iter().all(|r| r.observed_le_watched && r.watched_le_raw)
    }
}

/// Instance check of the All-Green ⇔ joint-kernel equivalence (7.4.4).
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct AllGreenKernelCertificate {
    /// Declared observer carrier retained for replay.
    pub family: ObserverFamily,
    /// The exact supplied defect columns.
    pub defects: Defects,
    /// Every `J^α = 0`.
    pub all_green: bool,
    /// Edge → `Δ_e ∈ K_e` (the joint kernel of its watchers).
    pub edgewise_joint_kernel_membership: BTreeMap<String, bool>,
    /// All memberships hold.
    pub joint_kernel_condition: bool,
    /// `all_green == joint_kernel_condition`.
    pub equivalent: bool,
}

impl AllGreenKernelCertificate {
    /// Recheck.
    pub fn verify(&self) -> bool {
        let Ok(family) = ObserverFamily::new(self.family.edge_dimensions.clone(), self.family.observers.clone()) else { return false; };
        let Ok(defects) = family.normalize_defects(&self.defects) else { return false; };
        let Ok(tallies) = family.tallies(&defects) else { return false; };
        let memberships: BTreeMap<String, bool> = family.edge_dimensions.keys()
            .map(|e| (e.clone(), family.combined_watcher_map(e).mul(&defects[e]).is_zero())).collect();
        let condition = memberships.values().all(|b| *b);
        self.edgewise_joint_kernel_membership == memberships && self.joint_kernel_condition == condition
            && self.all_green == tallies.all_green()
            && self.equivalent == (self.all_green == condition) && self.equivalent
    }
}

/// Rank certificate for the combined watcher map on every edge.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct JointInjectivityCertificate {
    /// Declared observer carrier retained for independent matrix checks.
    pub family: ObserverFamily,
    /// Every edge has a watcher.
    pub full_edge_coverage: bool,
    /// Edge → the stacked watcher map is injective.
    pub edgewise_injective: BTreeMap<String, bool>,
    /// Edge → rank of the stacked watcher map.
    pub edgewise_combined_rank: BTreeMap<String, usize>,
    /// Coverage and injectivity everywhere.
    pub premises_hold: bool,
}

impl JointInjectivityCertificate {
    /// Recheck.
    pub fn verify(&self) -> bool {
        let Ok(family) = ObserverFamily::new(self.family.edge_dimensions.clone(), self.family.observers.clone()) else { return false; };
        let ranks: BTreeMap<String, usize> = family.edge_dimensions.keys()
            .map(|e| (e.clone(), family.combined_watcher_map(e).rank())).collect();
        let injective: BTreeMap<String, bool> = family.edge_dimensions.iter()
            .map(|(e, d)| (e.clone(), ranks[e] == *d)).collect();
        let covered = family.full_edge_coverage();
        self.edgewise_combined_rank == ranks && self.edgewise_injective == injective
            && self.full_edge_coverage == covered
            && self.premises_hold == (covered && injective.values().all(|b| *b))
    }
}

/// Premise-gated finite implication check (Corollary 7.4.7); refusal is
/// explicit.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct LocalToGlobalCertificate {
    /// Declared observer carrier retained for replay.
    pub family: ObserverFamily,
    /// The exact supplied defect columns.
    pub defects: Defects,
    /// The premises held and the implication was evaluated.
    pub accepted: bool,
    /// Every observer green.
    pub all_green: bool,
    /// `I = 0`.
    pub global_green: bool,
    /// `all_green ⇒ global_green`, when accepted.
    pub implication_holds: Option<bool>,
    /// Why not, when not accepted.
    pub refusals: Vec<String>,
}

impl LocalToGlobalCertificate {
    /// Recheck.
    pub fn verify(&self) -> bool {
        let Ok(family) = ObserverFamily::new(self.family.edge_dimensions.clone(), self.family.observers.clone()) else { return false; };
        let Ok(defects) = family.normalize_defects(&self.defects) else { return false; };
        let Ok(injective) = family.joint_injectivity_certificate() else { return false; };
        let Ok(kernel) = family.all_green_kernel_certificate(&defects) else { return false; };
        let Ok(tallies) = family.tallies(&defects) else { return false; };
        let mut refusals = Vec::new();
        if !injective.full_edge_coverage { refusals.push("full_edge_coverage_not_supplied".to_string()); }
        let noninjective: Vec<&String> = injective.edgewise_injective.iter()
            .filter(|(_, ok)| !**ok).map(|(e, _)| e).collect();
        if !noninjective.is_empty() { refusals.push(format!("nontrivial_joint_kernels={noninjective:?}")); }
        let accepted = refusals.is_empty();
        let global_green = tallies.i.is_zero();
        self.accepted == accepted && self.refusals == refusals && self.all_green == kernel.all_green
            && self.global_green == global_green
            && self.implication_holds == accepted.then_some(!kernel.all_green || global_green)
    }
}

/// A nonempty family of exact finite observer carriers.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ObserverFamily {
    /// Edge → fiber dimension.
    pub edge_dimensions: BTreeMap<String, usize>,
    /// The observers, in declaration order.
    pub observers: Vec<LocalObserverCarrier>,
}

impl ObserverFamily {
    /// Build and validate: shapes, contractivity, unique ids.
    pub fn new(edge_dimensions: BTreeMap<String, usize>, observers: Vec<LocalObserverCarrier>) -> Result<ObserverFamily, String> {
        if edge_dimensions.is_empty() {
            return Err("an observer family needs at least one edge".into());
        }
        if edge_dimensions.values().any(|&d| d == 0) {
            return Err("edge dimensions must be positive integers".into());
        }
        if observers.is_empty() {
            return Err("an observer family must be nonempty".into());
        }
        let mut ids: Vec<&str> = observers.iter().map(|o| o.observer_id.as_str()).collect();
        ids.sort();
        ids.dedup();
        if ids.len() != observers.len() {
            return Err("observer identifiers must be unique".into());
        }
        for o in &observers {
            if o.observer_id.trim().is_empty() {
                return Err("observer_id must be nonempty".into());
            }
            if o.maps.is_empty() {
                return Err("an observer must watch at least one edge".into());
            }
            for (e, m) in &o.maps {
                let Some(&dim) = edge_dimensions.get(e) else {
                    return Err(format!("observer {:?} references unknown edges [{e:?}]", o.observer_id));
                };
                if !m.is_well_formed() || m.rows == 0 || m.cols != dim {
                    return Err(format!("observer {:?} map on {e:?} has shape {:?}, expected positive rows and {dim} columns", o.observer_id, m.shape()));
                }
                if m.l1_operator_norm() > Rational::ONE {
                    return Err(format!("observer {:?} map on {e:?} is not l1-contractive", o.observer_id));
                }
            }
        }
        Ok(ObserverFamily { edge_dimensions, observers })
    }

    /// Validate a defect family against the edge dimensions.
    pub fn normalize_defects(&self, defects: &Defects) -> Result<Defects, String> {
        let missing: Vec<&String> = self.edge_dimensions.keys().filter(|e| !defects.contains_key(*e)).collect();
        let extra: Vec<&String> = defects.keys().filter(|e| !self.edge_dimensions.contains_key(*e)).collect();
        if !missing.is_empty() || !extra.is_empty() {
            return Err(format!("defect domain mismatch; missing={missing:?}, extra={extra:?}"));
        }
        for (e, &dim) in &self.edge_dimensions {
            if !defects[e].is_well_formed() || defects[e].shape() != (dim, 1) {
                return Err(format!("defect on {e:?} has shape {:?}, expected {:?}", defects[e].shape(), (dim, 1)));
            }
        }
        Ok(defects.clone())
    }

    /// The observers watching an edge, in declaration order.
    pub fn watchers(&self, edge: &str) -> Vec<&LocalObserverCarrier> {
        self.observers.iter().filter(|o| o.maps.contains_key(edge)).collect()
    }

    /// Every edge has a watcher.
    pub fn full_edge_coverage(&self) -> bool {
        self.edge_dimensions.keys().all(|e| !self.watchers(e).is_empty())
    }

    /// The stacked watcher map on an edge (`0 × dim` when unwatched).
    pub fn combined_watcher_map(&self, edge: &str) -> Matrix {
        let ws = self.watchers(edge);
        if ws.is_empty() {
            return Matrix::zeros(0, self.edge_dimensions[edge]);
        }
        Matrix::vstack(&ws.iter().map(|w| w.maps[edge].clone()).collect::<Vec<_>>())
    }

    /// A basis of `K_e`, the joint kernel on an edge.
    pub fn joint_kernel_basis(&self, edge: &str) -> Vec<Matrix> {
        self.combined_watcher_map(edge).nullspace()
    }

    /// `K_e = 0`.
    pub fn jointly_injective(&self, edge: &str) -> bool {
        !self.watchers(edge).is_empty() && self.combined_watcher_map(edge).rank() == self.edge_dimensions[edge]
    }

    /// `I`, every `J^α`, and `Λ`.
    pub fn tallies(&self, defects: &Defects) -> Result<ObserverTallies, String> {
        let v = self.normalize_defects(defects)?;
        let i = v.values().fold(Rational::ZERO, |a, d| a + d.l1_norm());
        let j: BTreeMap<String, Rational> = self
            .observers
            .iter()
            .map(|o| (o.observer_id.clone(), o.maps.iter().fold(Rational::ZERO, |a, (e, m)| a + m.mul(&v[e]).l1_norm())))
            .collect();
        let lambda = i - j.values().copied().max().unwrap_or(Rational::ZERO);
        let t = ObserverTallies { i, j, lambda };
        if !t.verify() {
            return Err("observer tally failed internal exact recheck".into());
        }
        Ok(t)
    }

    /// `Λ` split into edgewise loss and fragmentation.
    pub fn visibility_gap_decomposition(&self, defects: &Defects) -> Result<VisibilityGapDecomposition, String> {
        let v = self.normalize_defects(defects)?;
        let t = self.tallies(&v)?;
        let p_by_edge: BTreeMap<String, Rational> = v
            .iter()
            .map(|(e, d)| {
                let watched: Vec<Rational> = self.watchers(e).iter().map(|o| o.maps[e].mul(d).l1_norm()).collect();
                (e.clone(), watched.into_iter().max().unwrap_or(Rational::ZERO))
            })
            .collect();
        let edgewise = v.iter().fold(Rational::ZERO, |a, (e, d)| a + d.l1_norm() - p_by_edge[e]);
        let fragmentation = p_by_edge.values().fold(Rational::ZERO, |a, b| a + *b) - t.j.values().copied().max().unwrap_or(Rational::ZERO);
        let c = VisibilityGapDecomposition { family: self.clone(), defects: v.clone(), p_by_edge, edgewise_observation_loss: edgewise, single_observer_fragmentation: fragmentation, lambda: t.lambda };
        if !c.verify() {
            return Err("visibility-gap decomposition failed internal exact recheck".into());
        }
        Ok(c)
    }

    /// Proposition 7.4.3 on this instance.
    pub fn passivity_certificate(&self, defects: &Defects) -> Result<PassivityCertificate, String> {
        let v = self.normalize_defects(defects)?;
        let t = self.tallies(&v)?;
        let rows: Vec<PassivityRow> = self
            .observers
            .iter()
            .map(|o| {
                let watched = o.maps.keys().fold(Rational::ZERO, |a, e| a + v[e].l1_norm());
                let observed = t.j[&o.observer_id];
                PassivityRow {
                    observer_id: o.observer_id.clone(),
                    observed_j: observed,
                    watched_raw_tally: watched,
                    raw_i: t.i,
                    observed_le_watched: observed <= watched,
                    watched_le_raw: watched <= t.i,
                }
            })
            .collect();
        let holds = rows.iter().all(|r| r.observed_le_watched && r.watched_le_raw);
        let c = PassivityCertificate { family: self.clone(), defects: v.clone(), rows, holds };
        if !c.verify() {
            return Err("passivity certificate failed internal exact recheck".into());
        }
        Ok(c)
    }

    /// Proposition 7.4.4 on this instance.
    pub fn all_green_kernel_certificate(&self, defects: &Defects) -> Result<AllGreenKernelCertificate, String> {
        let v = self.normalize_defects(defects)?;
        let t = self.tallies(&v)?;
        let all_green = t.all_green();
        let memberships: BTreeMap<String, bool> = self.edge_dimensions.keys().map(|e| (e.clone(), self.combined_watcher_map(e).mul(&v[e]).is_zero())).collect();
        let condition = memberships.values().all(|b| *b);
        let c = AllGreenKernelCertificate { family: self.clone(), defects: v.clone(), all_green, edgewise_joint_kernel_membership: memberships, joint_kernel_condition: condition, equivalent: all_green == condition };
        if !c.verify() {
            return Err("All-Green certificate failed internal exact recheck".into());
        }
        Ok(c)
    }

    /// The premises of Corollary 7.4.7 on this family.
    pub fn joint_injectivity_certificate(&self) -> Result<JointInjectivityCertificate, String> {
        let injective: BTreeMap<String, bool> = self.edge_dimensions.keys().map(|e| (e.clone(), self.jointly_injective(e))).collect();
        let ranks: BTreeMap<String, usize> = self.edge_dimensions.keys().map(|e| (e.clone(), self.combined_watcher_map(e).rank())).collect();
        let coverage = self.full_edge_coverage();
        let premises = coverage && injective.values().all(|b| *b);
        let c = JointInjectivityCertificate { family: self.clone(), full_edge_coverage: coverage, edgewise_injective: injective, edgewise_combined_rank: ranks, premises_hold: premises };
        if !c.verify() {
            return Err("joint-injectivity certificate failed internal recheck".into());
        }
        Ok(c)
    }

    /// Corollary 7.4.7 on this instance, gated by its premises.
    pub fn local_to_global_certificate(&self, defects: &Defects) -> Result<LocalToGlobalCertificate, String> {
        let v = self.normalize_defects(defects)?;
        let inj = self.joint_injectivity_certificate()?;
        let all_green = self.all_green_kernel_certificate(&v)?.all_green;
        let global_green = self.tallies(&v)?.i.is_zero();
        let mut refusals = Vec::new();
        if !inj.full_edge_coverage {
            refusals.push("full_edge_coverage_not_supplied".to_string());
        }
        let noninjective: Vec<&String> = inj.edgewise_injective.iter().filter(|(_, ok)| !**ok).map(|(e, _)| e).collect();
        if !noninjective.is_empty() {
            refusals.push(format!("nontrivial_joint_kernels={noninjective:?}"));
        }
        let accepted = refusals.is_empty();
        let c = LocalToGlobalCertificate { family: self.clone(), defects: v.clone(), accepted, all_green, global_green, implication_holds: accepted.then_some(!all_green || global_green), refusals };
        if !c.verify() {
            return Err("local-to-global certificate failed internal recheck".into());
        }
        Ok(c)
    }
}

/// Exact replay of Proposition 7.4.5 at one positive rational scale.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ThreePatchCertificate {
    /// `λ`.
    pub scale: Rational,
    /// The three observers.
    pub family: ObserverFamily,
    /// The six-edge diagram.
    pub diagram: CoveringEdgeDiagram,
    /// The section `s_λ`.
    pub section: Section,
    /// `Δ(s_λ)`.
    pub defects: Defects,
    /// `I, J, Λ`.
    pub tallies: ObserverTallies,
    /// Passivity rows.
    pub passivity: PassivityCertificate,
    /// All-Green ⇔ kernel.
    pub all_green_kernel: AllGreenKernelCertificate,
    /// Every edge watched.
    pub full_edge_coverage: bool,
    /// `I = 6λ`.
    pub raw_formula_holds: bool,
}

impl ThreePatchCertificate {
    /// Recheck everything from the section.
    pub fn verify(&self) -> bool {
        let Ok(diagram) = CoveringEdgeDiagram::new(self.diagram.fiber_dimensions.clone(), self.diagram.edges.clone()) else { return false; };
        let Ok(family) = ObserverFamily::new(self.family.edge_dimensions.clone(), self.family.observers.clone()) else { return false; };
        let Ok(derived) = diagram.coboundary(&self.section) else { return false; };
        let Ok(tallies) = family.tallies(&derived) else { return false; };
        let Ok(passivity) = family.passivity_certificate(&derived) else { return false; };
        let Ok(kernel) = family.all_green_kernel_certificate(&derived) else { return false; };
        self.scale > Rational::ZERO && derived == self.defects && tallies == self.tallies
            && passivity == self.passivity && kernel == self.all_green_kernel
            && self.full_edge_coverage == family.full_edge_coverage() && self.full_edge_coverage
            && self.raw_formula_holds == (tallies.i == q(6) * self.scale) && self.raw_formula_holds
            && tallies.all_green() && tallies.lambda == tallies.i && passivity.verify() && kernel.verify()
    }
}

/// A finite list of exact scaled three-patch instances (Corollary 7.4.6).
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ScalingFamilyCertificate {
    /// The instances.
    pub instances: Vec<ThreePatchCertificate>,
    /// `I(s_λ) = 6λ` and All-Green at every scale.
    pub exact_linear_scaling: bool,
}

impl ScalingFamilyCertificate {
    /// Recheck.
    pub fn verify(&self) -> bool {
        !self.instances.is_empty()
            && self.instances.iter().all(ThreePatchCertificate::verify)
            && self.exact_linear_scaling == self.instances.iter().all(|c| c.tallies.i == q(6) * c.scale && c.tallies.all_green())
    }
}

/// The observer that deletes one coordinate of `R³`.
pub fn coordinate_deletion(coordinate: usize) -> Matrix {
    match coordinate {
        0 => Matrix::from_i128(&[&[0, 1, 0], &[0, 0, 1]]),
        1 => Matrix::from_i128(&[&[1, 0, 0], &[0, 0, 1]]),
        2 => Matrix::from_i128(&[&[1, 0, 0], &[0, 1, 0]]),
        _ => panic!("coordinate must be 0, 1, or 2"),
    }
}

/// The six covering edges of the three-patch witness: `(edge, lower,
/// upper, watcher)`.
pub const THREE_PATCH_EDGES: [(&str, &str, &str, &str); 6] = [
    ("x12->u1", "x12", "u1", "C1"),
    ("x12->u2", "x12", "u2", "C2"),
    ("x23->u2", "x23", "u2", "C2"),
    ("x23->u3", "x23", "u3", "C3"),
    ("x31->u3", "x31", "u3", "C3"),
    ("x31->u1", "x31", "u1", "C1"),
];

/// Construct and recheck the exact six-edge Local-Green/Global-Red witness.
pub fn three_patch_certificate(scale: Rational) -> Result<ThreePatchCertificate, String> {
    if scale <= Rational::ZERO {
        return Err("the three-patch scaling parameter must be positive".into());
    }
    let fiber_dimensions: BTreeMap<String, usize> = ["x12", "x23", "x31", "u1", "u2", "u3"].iter().map(|n| (n.to_string(), 3)).collect();
    let edges: Vec<CoveringEdge> = THREE_PATCH_EDGES
        .iter()
        .map(|(id, lower, upper, _)| CoveringEdge { id: id.to_string(), lower: lower.to_string(), upper: upper.to_string(), restriction: Matrix::eye(3) })
        .collect();
    let diagram = CoveringEdgeDiagram::new(fiber_dimensions, edges)?;
    let z = Rational::ZERO;
    let section = Section::from([
        ("x12".to_string(), Matrix::zeros(3, 1)),
        ("x23".to_string(), Matrix::zeros(3, 1)),
        ("x31".to_string(), Matrix::zeros(3, 1)),
        ("u1".to_string(), Matrix::column(&[scale, z, z])),
        ("u2".to_string(), Matrix::column(&[z, scale, z])),
        ("u3".to_string(), Matrix::column(&[z, z, scale])),
    ]);
    let edge_dimensions: BTreeMap<String, usize> = THREE_PATCH_EDGES.iter().map(|(id, ..)| (id.to_string(), 3)).collect();
    let observers: Vec<LocalObserverCarrier> = ["C1", "C2", "C3"]
        .iter()
        .enumerate()
        .map(|(index, obs)| LocalObserverCarrier {
            observer_id: obs.to_string(),
            maps: THREE_PATCH_EDGES.iter().filter(|(_, _, _, w)| w == obs).map(|(id, ..)| (id.to_string(), coordinate_deletion(index))).collect(),
        })
        .collect();
    let family = ObserverFamily::new(edge_dimensions, observers)?;
    let defects = diagram.coboundary(&section)?;
    let tallies = family.tallies(&defects)?;
    let cert = ThreePatchCertificate {
        scale,
        passivity: family.passivity_certificate(&defects)?,
        all_green_kernel: family.all_green_kernel_certificate(&defects)?,
        full_edge_coverage: family.full_edge_coverage(),
        raw_formula_holds: tallies.i == q(6) * scale,
        family,
        diagram,
        section,
        defects,
        tallies,
    };
    if !cert.verify() {
        return Err("three-patch witness failed internal exact recheck".into());
    }
    Ok(cert)
}

/// Replay a nonempty finite list of positive rational scaling instances.
pub fn scaling_family_certificate(scales: &[Rational]) -> Result<ScalingFamilyCertificate, String> {
    if scales.is_empty() {
        return Err("at least one scaling instance is required".into());
    }
    let mut instances = Vec::new();
    for &s in scales {
        instances.push(three_patch_certificate(s)?);
    }
    let exact_linear_scaling = instances.iter().all(|c| c.tallies.i == q(6) * c.scale && c.tallies.all_green());
    let cert = ScalingFamilyCertificate { instances, exact_linear_scaling };
    if !cert.verify() {
        return Err("scaling-family certificate failed internal exact recheck".into());
    }
    Ok(cert)
}

/// Proposition 7.4.7-B (H8), computed: the coupled carrier where joint-kernel
/// triviality fails on every edge and All-Green still forces `I = 0`.
///
/// `P = {x, u1, u2}`, all fibers `R²`, both restriction maps zero, so
/// `Δ(s)_{x→u_i} = −s(x)` on both edges; observer 1 reads coordinate 2 of
/// the first edge, observer 2 reads coordinate 1 of the second.  Each
/// joint kernel is one-dimensional, yet the two observers jointly read
/// both coordinates of the one vector `s(x)` that every defect equals.
///
/// The global statement across sections is decided by linear algebra:
/// `ker(O ∘ D) ⊆ ker(D)` on `C⁰ = R⁶`, checked on a basis of the kernel.
///
/// ### Source correspondence (`po000_l004_observer_visibility.lean`)
/// These are source-level comparisons, not generated Lean bindings or a new build.
/// * `full_edge_coverage` ↔ `PO000.ObserverVisibility.Coupled.full_coverage`
/// * `joint_kernel_nontrivial` ↔ `PO000.ObserverVisibility.Coupled.joint_kernel_nontrivial`
/// * `all_green_forces_zero` ↔ `PO000.ObserverVisibility.Coupled.allGreen_forces_zero`
/// * Quantification correspondence:
///   - Lean establishes `allGreen_forces_zero` for all section-realized defects `coupledDefect(sx)` where `sx : Fib2` (`ℝ²`).
///   - Rust decides this algebraically across the full section space `C⁰ = ℝ⁶` by checking `ker(O ∘ D) ⊆ ker(D)`,
///     verifying that the 4-dimensional kernel of `O ∘ D` is contained in `ker(D)`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CoupledCarrierCertificate {
    /// The family.
    pub family: ObserverFamily,
    /// The diagram.
    pub diagram: CoveringEdgeDiagram,
    /// Every edge watched.
    pub full_edge_coverage: bool,
    /// Edge → `K_e ≠ 0`.
    pub joint_kernel_nontrivial: BTreeMap<String, bool>,
    /// `D : C⁰ → C¹` as a matrix over the sorted node/edge bases.
    pub defect_map: Matrix,
    /// `O : C¹ → outputs`, the stacked observer maps.
    pub observer_map: Matrix,
    /// Dimension of `ker(O ∘ D)`: the space of All-Green sections.
    pub all_green_section_dimension: usize,
    /// Under kernel containment `ker(O ∘ D) ⊆ ker(D)`, `D` vanishes on every All-Green section (Lean: `Coupled.allGreen_forces_zero`).
    pub all_green_forces_zero: bool,
    /// Corollary 7.4.7 refuses here (its premise fails), as it must.
    pub corollary_premise_refused: bool,
    /// An instance: `s(x) = (1, 2)`, `u`'s zero — not All-Green, `I = 6`.
    pub red_instance: ObserverTallies,
}

/// Build the coupled carrier and decide its claims.
pub fn coupled_carrier_certificate() -> Result<CoupledCarrierCertificate, String> {
    let fiber_dimensions: BTreeMap<String, usize> = ["x", "u1", "u2"].iter().map(|n| (n.to_string(), 2)).collect();
    let edges = vec![
        CoveringEdge { id: "x->u1".into(), lower: "x".into(), upper: "u1".into(), restriction: Matrix::zeros(2, 2) },
        CoveringEdge { id: "x->u2".into(), lower: "x".into(), upper: "u2".into(), restriction: Matrix::zeros(2, 2) },
    ];
    let diagram = CoveringEdgeDiagram::new(fiber_dimensions, edges)?;
    let edge_dimensions: BTreeMap<String, usize> = [("x->u1", 2), ("x->u2", 2)].iter().map(|(e, d)| (e.to_string(), *d)).collect();
    let observers = vec![
        LocalObserverCarrier { observer_id: "1".into(), maps: BTreeMap::from([("x->u1".to_string(), Matrix::from_i128(&[&[0, 1]]))]) },
        LocalObserverCarrier { observer_id: "2".into(), maps: BTreeMap::from([("x->u2".to_string(), Matrix::from_i128(&[&[1, 0]]))]) },
    ];
    let family = ObserverFamily::new(edge_dimensions, observers)?;
    // Bases: nodes and edges in sorted order, coordinates within.
    let nodes: Vec<&String> = diagram.fiber_dimensions.keys().collect();
    let mut node_offset = BTreeMap::new();
    let mut c0 = 0;
    for n in &nodes {
        node_offset.insert((*n).clone(), c0);
        c0 += diagram.fiber_dimensions[*n];
    }
    let mut edge_offset = BTreeMap::new();
    let mut c1 = 0;
    for e in &diagram.edges {
        edge_offset.insert(e.id.clone(), c1);
        c1 += diagram.fiber_dimensions[&e.lower];
    }
    let mut defect_map = Matrix::zeros(c1, c0);
    for e in &diagram.edges {
        let (ro, lo, uo) = (edge_offset[&e.id], node_offset[&e.lower], node_offset[&e.upper]);
        for i in 0..e.restriction.rows {
            defect_map.set(ro + i, lo + i, q(-1));
            for j in 0..e.restriction.cols {
                let v = defect_map.get(ro + i, uo + j) + e.restriction.get(i, j);
                defect_map.set(ro + i, uo + j, v);
            }
        }
    }
    let mut out_rows = 0;
    for o in &family.observers {
        for m in o.maps.values() {
            out_rows += m.rows;
        }
    }
    let mut observer_map = Matrix::zeros(out_rows, c1);
    let mut row = 0;
    for o in &family.observers {
        for (e, m) in &o.maps {
            for i in 0..m.rows {
                for j in 0..m.cols {
                    observer_map.set(row + i, edge_offset[e] + j, m.get(i, j));
                }
            }
            row += m.rows;
        }
    }
    let kernel = observer_map.mul(&defect_map).nullspace();
    let all_green_forces_zero = kernel.iter().all(|v| defect_map.mul(v).is_zero());
    let joint_kernel_nontrivial: BTreeMap<String, bool> = family.edge_dimensions.keys().map(|e| (e.clone(), !family.joint_kernel_basis(e).is_empty())).collect();
    let section = Section::from([
        ("x".to_string(), Matrix::column_i128(&[1, 2])),
        ("u1".to_string(), Matrix::zeros(2, 1)),
        ("u2".to_string(), Matrix::zeros(2, 1)),
    ]);
    let red_instance = family.tallies(&diagram.coboundary(&section)?)?;
    let corollary = family.local_to_global_certificate(&diagram.coboundary(&section)?)?;
    Ok(CoupledCarrierCertificate {
        full_edge_coverage: family.full_edge_coverage(),
        joint_kernel_nontrivial,
        defect_map,
        observer_map,
        all_green_section_dimension: kernel.len(),
        all_green_forces_zero,
        corollary_premise_refused: !corollary.accepted,
        red_instance,
        family,
        diagram,
    })
}

/// §7.4.12 (H9) — the fiber-level quotient witness: scalar fibers on the coupled
/// diagram, `im(d₀) = {(−α, −α)}`, `ω = (1, −1)`, `Φ([ω]) = 2 > 0`.
///
/// ### Source correspondence (`po000_l004_observer_visibility.lean`)
/// These are source-level comparisons, not generated Lean bindings or a new build.
/// * `exactness.accepted` (`ω ∉ im(d₀)`) ↔ `PO000.ObserverVisibility.QuotientWitness.omega_not_exact`
/// * `quotient.distance == 2` (lower bound) ↔ `PO000.ObserverVisibility.QuotientWitness.repair_mass_ge_two`
/// * `quotient.distance == 2` (Lean attainment at α=0; Rust may choose another minimizer) ↔ `PO000.ObserverVisibility.QuotientWitness.repair_mass_attained`
/// * Quantification correspondence:
///   - Lean establishes `2 ≤ massL1(omega - d0(alpha))` for all `alpha : ℝ` by the scalar triangle inequality.
///   - Rust solves the exact rational quotient dual linear program over `d₀ : ℝ³ → ℝ²`, yielding
///     a primal repair and a dual functional `[1, -1]ᵀ` with pairing `2`.
///     The separate exactness separator `[-1, 1]ᵀ` has pairing `-2`; its sign is reversed for the dual maximization.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct QuotientWitness {
    /// `d₀` over the sorted node basis `(u1, u2, x)`.
    pub d0: Matrix,
    /// `ω`.
    pub omega: Matrix,
    /// `ω ∉ im(d₀)`, with its separator.
    pub exactness: ExactnessCertificate,
    /// `Φ([ω]) = 2`, with primal and dual witnesses.
    pub quotient: QuotientDistanceCertificate,
}

/// Compute the §7.4.12 witness.
pub fn quotient_witness() -> Result<QuotientWitness, String> {
    // Nodes sorted: u1, u2, x.  Both restrictions are zero, so
    // (d0 s)_e = 0·s(u_i) − s(x) on each edge.
    let d0 = Matrix::from_i128(&[&[0, 0, -1], &[0, 0, -1]]);
    let omega = Matrix::column_i128(&[1, -1]);
    let problem = LinearRepairProblem::new(d0.clone());
    let exactness = problem.exactness_certificate(&omega)?;
    let quotient = problem.quotient_l1_distance(&omega)?;
    Ok(QuotientWitness { d0, omega, exactness, quotient })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::alpha_projection_obstruction::rational::r;

    /// H5: `I = 6`, every `J = 0`, `Λ = 6`; edgewise loss 6.
    #[test]
    fn the_three_patch_witness_is_locally_green_and_globally_red() {
        let c = three_patch_certificate(Rational::ONE).unwrap();
        assert!(c.verify());
        assert_eq!(c.tallies.i, q(6));
        assert!(c.tallies.j.values().all(|v| v.is_zero()));
        assert_eq!(c.tallies.j.keys().cloned().collect::<Vec<_>>(), vec!["C1", "C2", "C3"]);
        assert_eq!(c.tallies.lambda, q(6));
        let gap = c.family.visibility_gap_decomposition(&c.defects).unwrap();
        assert_eq!(gap.edgewise_observation_loss, q(6));
        assert_eq!(gap.single_observer_fragmentation, Rational::ZERO);
        assert!(c.full_edge_coverage);
        // Corollary 7.4.7 refuses: the joint kernels are nontrivial.
        let l2g = c.family.local_to_global_certificate(&c.defects).unwrap();
        assert!(!l2g.accepted && l2g.verify());
        assert!(l2g.refusals[0].starts_with("nontrivial_joint_kernels"));
    }

    /// H6: `I(s_λ) = 6λ` at `λ = 1/2, 7/3, 5` — `3, 14, 30`.
    #[test]
    fn the_scaling_family_is_exactly_linear() {
        let s = scaling_family_certificate(&[r(1, 2), r(7, 3), q(5)]).unwrap();
        assert!(s.verify() && s.exact_linear_scaling);
        let scaled: Vec<String> = s.instances.iter().map(|i| i.tallies.i.to_string()).collect();
        assert_eq!(scaled, vec!["3", "14", "30"]);
        assert!(three_patch_certificate(Rational::ZERO).is_err());
    }

    /// H1–H4, H7: the rank-two carrier is jointly injective and
    /// local-to-global is accepted; the fragmented family splits `Λ`.
    #[test]
    fn injectivity_and_fragmentation_fixtures() {
        let injective = ObserverFamily::new(
            BTreeMap::from([("e".to_string(), 2)]),
            vec![
                LocalObserverCarrier { observer_id: "x".into(), maps: BTreeMap::from([("e".to_string(), Matrix::from_i128(&[&[1, 0]]))]) },
                LocalObserverCarrier { observer_id: "y".into(), maps: BTreeMap::from([("e".to_string(), Matrix::from_i128(&[&[0, 1]]))]) },
            ],
        )
        .unwrap();
        let inj = injective.joint_injectivity_certificate().unwrap();
        assert!(inj.verify() && inj.premises_hold);
        assert_eq!(inj.edgewise_combined_rank["e"], 2);
        let l2g = injective.local_to_global_certificate(&Defects::from([("e".to_string(), Matrix::zeros(2, 1))])).unwrap();
        assert!(l2g.verify() && l2g.accepted && l2g.implication_holds == Some(true));
        let fragmented = ObserverFamily::new(
            BTreeMap::from([("e1".to_string(), 1), ("e2".to_string(), 1)]),
            vec![
                LocalObserverCarrier { observer_id: "left".into(), maps: BTreeMap::from([("e1".to_string(), Matrix::eye(1))]) },
                LocalObserverCarrier { observer_id: "right".into(), maps: BTreeMap::from([("e2".to_string(), Matrix::eye(1))]) },
            ],
        )
        .unwrap();
        let gap = fragmented.visibility_gap_decomposition(&Defects::from([("e1".to_string(), Matrix::column_i128(&[1])), ("e2".to_string(), Matrix::column_i128(&[1]))])).unwrap();
        assert!(gap.verify());
        assert_eq!((gap.edgewise_observation_loss, gap.single_observer_fragmentation), (Rational::ZERO, q(1)));
        let passivity = fragmented.passivity_certificate(&Defects::from([("e1".to_string(), Matrix::column_i128(&[1])), ("e2".to_string(), Matrix::column_i128(&[-2]))])).unwrap();
        assert!(passivity.verify() && passivity.holds);
    }

    /// H8: joint kernels nontrivial on both edges, All-Green forces `I = 0`.
    #[test]
    fn the_coupled_carrier_refutes_necessity_of_joint_kernel_triviality() {
        let c = coupled_carrier_certificate().unwrap();
        assert!(c.full_edge_coverage);
        assert!(c.joint_kernel_nontrivial.values().all(|b| *b));
        assert!(c.all_green_forces_zero);
        assert_eq!(c.all_green_section_dimension, 4);
        assert!(c.corollary_premise_refused);
        assert_eq!(c.red_instance.i, q(6));
        assert!(!c.red_instance.all_green());
        assert_eq!(c.defect_map.shape(), (4, 6));
        assert_eq!(c.observer_map.shape(), (2, 4));
    }

    /// H9: `Φ([ω]) = 2 > 0` and `ω ∉ im(d₀)`.
    #[test]
    fn the_quotient_witness_has_positive_quotient_mass() {
        let w = quotient_witness().unwrap();
        assert!(!w.exactness.is_exact_coboundary && w.exactness.verify());
        assert_eq!(w.quotient.distance, q(2));
        assert!(w.quotient.verify());
        assert_eq!(w.quotient.dual_witness, Matrix::column_i128(&[1, -1]));
        // The paper's inline grid replay: alpha = -8..8 in steps of 1/8, minimum 2.
        let min = (-64..=64).map(|a| (q(1) + r(a, 8)).abs() + (r(a, 8) - q(1)).abs()).min().unwrap();
        assert_eq!(min, q(2));
    }

    #[test]
    fn construction_refuses_bad_observers() {
        let dims = BTreeMap::from([("e".to_string(), 2)]);
        let bad = LocalObserverCarrier { observer_id: "o".into(), maps: BTreeMap::from([("e".to_string(), Matrix::from_i128(&[&[2, 0]]))]) };
        assert!(ObserverFamily::new(dims.clone(), vec![bad]).unwrap_err().contains("not l1-contractive"));
        let unknown = LocalObserverCarrier { observer_id: "o".into(), maps: BTreeMap::from([("zz".to_string(), Matrix::from_i128(&[&[1, 0]]))]) };
        assert!(ObserverFamily::new(dims, vec![unknown]).unwrap_err().contains("unknown edges"));
    }
}

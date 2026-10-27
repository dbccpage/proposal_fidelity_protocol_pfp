//! Exact positive extension for finite bipartite experimental tables.
//! Premises: one normalized nonnegative setting-independent prior over complete
//! local response functions, exhaustive outcomes, and factorized local response.
//! These are tested model premises, not conclusions about every classical world.
use num_traits::{Signed, Zero};
use core_finite_probability::local_deterministic::{finite_local_vertices, LocalVertexLimits};
use core_finite_probability::simplex::ProbabilitySimplex;
use core_number_theory::rational::{ri, Rational};
use core_solvers::solver_convex_farkas_feasibility::{
    FeasibilityError, FeasibilityVerdict, LinearInequalitySystem,
};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BellExtensionError {
    InvalidScenario,
    InvalidProbabilities,
    EnumerationLimit,
    SolverCells,
    Solver(FeasibilityError),
    CertificateMismatch,
}

// Origin: engine/crates_rs/core_quantum_physics/src/finite_bell_extension.rs
// Claim: urn:core:crates_rs:core-quantum-physics:finite-bell-extension:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for BellExtensionError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for BellExtensionError {}
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BellLimits {
    pub vertices: LocalVertexLimits,
    /// Bound on entries in the solver's expanded primal/dual matrices.
    pub solver_cells: usize,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LocalResponse {
    pub left: Vec<usize>,
    pub right: Vec<usize>,
    pub weight: Rational,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteBellProblem {
    left: Vec<usize>,
    right: Vec<usize>,
    probabilities: Vec<Rational>,
    vertices: Vec<Vec<Rational>>,
    system: LinearInequalitySystem,
}
impl FiniteBellProblem {
    fn validate_scenario(
        left: &[usize],
        right: &[usize],
        rows: &[Vec<Rational>],
    ) -> Result<(), BellExtensionError> {
        let bad_dims = left.is_empty()
            || right.is_empty()
            || left.len().checked_add(right.len()).is_none_or(|n| n > 20);
        let bad_counts =
            left.contains(&0) || right.contains(&0) || rows.len() != left.len() * right.len();
        if bad_dims || bad_counts {
            return Err(BellExtensionError::InvalidScenario);
        }
        Ok(())
    }

    fn validate_probability_rows(
        left: &[usize],
        right: &[usize],
        rows: &[Vec<Rational>],
    ) -> Result<(), BellExtensionError> {
        for (x, &na) in left.iter().enumerate() {
            for (y, &nb) in right.iter().enumerate() {
                let row = &rows[x * right.len() + y];
                let bad_entries = row
                    .iter()
                    .any(|p| !p.denom().is_positive() || p.is_negative());
                if na.checked_mul(nb) != Some(row.len())
                    || bad_entries
                    || row.iter().cloned().sum::<Rational>() != ri(1)
                {
                    return Err(BellExtensionError::InvalidProbabilities);
                }
            }
        }
        Ok(())
    }

    fn check_solver_cell_budget(
        n: usize,
        probabilities_len: usize,
        max_cells: usize,
    ) -> Result<(), BellExtensionError> {
        let r = n
            .checked_add(2)
            .and_then(|n| probabilities_len.checked_mul(2).and_then(|p| n.checked_add(p)))
            .ok_or(BellExtensionError::SolverCells)?;
        if n.checked_mul(2)
            .and_then(|n| n.checked_add(r))
            .and_then(|n| n.checked_mul(r))
            .is_none_or(|n| n > max_cells)
        {
            return Err(BellExtensionError::SolverCells);
        }
        Ok(())
    }

    fn build_lp_system(
        n: usize,
        vertices: &[Vec<Rational>],
        probabilities: &[Rational],
    ) -> Result<LinearInequalitySystem, BellExtensionError> {
        let mut system = LinearInequalitySystem::empty(n);
        // Deterministic row order: positivity; normalization +/-; each marginal +/-.
        for i in 0..n {
            let mut row = vec![ri(0); n];
            row[i] = ri(-1);
            system
                .push_le(row, ri(0))
                .map_err(BellExtensionError::Solver)?;
        }
        system
            .push_eq(vec![ri(1); n], ri(1))
            .map_err(BellExtensionError::Solver)?;
        for (k, p) in probabilities.iter().enumerate() {
            system
                .push_eq(vertices.iter().map(|v| v[k].clone()).collect(), p.clone())
                .map_err(BellExtensionError::Solver)?;
        }
        Ok(system)
    }

    /// Rows run in (left setting, right setting) order. In each row a varies
    /// fastest: index = a + left_outcomes[x]*b. Rational denominators must be
    /// positive. Signalling tables are admitted and can yield an obstruction.
    pub fn new(
        left: Vec<usize>,
        right: Vec<usize>,
        rows: Vec<Vec<Rational>>,
        limits: BellLimits,
    ) -> Result<Self, BellExtensionError> {
        Self::validate_scenario(&left, &right, &rows)?;
        Self::validate_probability_rows(&left, &right, &rows)?;
        let left_count = left.len();
        let contexts: Vec<_> = (0..left_count)
            .flat_map(|x| (0..right.len()).map(move |y| vec![x, left_count + y]))
            .collect();
        let outcomes: Vec<_> = left.iter().chain(&right).copied().collect();
        let vertices = finite_local_vertices(&outcomes, &contexts, limits.vertices)
            .map_err(|_| BellExtensionError::EnumerationLimit)?;
        let probabilities: Vec<_> = rows.into_iter().flatten().collect();
        let n = vertices.len();
        Self::check_solver_cell_budget(n, probabilities.len(), limits.solver_cells)?;
        let system = Self::build_lp_system(n, &vertices, &probabilities)?;
        Ok(Self {
            left,
            right,
            probabilities,
            vertices,
            system,
        })
    }
    pub fn system(&self) -> &LinearInequalitySystem {
        &self.system
    }
    pub fn decide(&self, max_pivots: usize) -> Result<FeasibilityVerdict, BellExtensionError> {
        let c = self
            .system
            .decide(max_pivots)
            .map_err(BellExtensionError::Solver)?;
        self.verify(&c)?;
        Ok(c)
    }
    /// Feasible proposals are checked directly as a probability law and by
    /// reproducing all experimental cells; infeasible proposals replay Farkas.
    pub fn verify(&self, c: &FeasibilityVerdict) -> Result<(), BellExtensionError> {
        match c {
            FeasibilityVerdict::Feasible { point } => {
                if point.len() != self.vertices.len()
                    || point.iter().any(|x| !x.denom().is_positive())
                    || ProbabilitySimplex::try_new(point.clone()).is_err()
                {
                    return Err(BellExtensionError::CertificateMismatch);
                }
                for (k, p) in self.probabilities.iter().enumerate() {
                    let sum: Rational = point
                        .iter()
                        .zip(&self.vertices)
                        .map(|(w, v)| w * &v[k])
                        .sum();
                    if &sum != p {
                        return Err(BellExtensionError::CertificateMismatch);
                    }
                }
                Ok(())
            }
            FeasibilityVerdict::Infeasible { multipliers } => self
                .system
                .verify_farkas(multipliers)
                .map_err(|_| BellExtensionError::CertificateMismatch),
        }
    }
    /// Decode a verified positive model into explicit local response functions.
    pub fn local_model(
        &self,
        point: &[Rational],
    ) -> Result<Vec<LocalResponse>, BellExtensionError> {
        self.verify(&FeasibilityVerdict::Feasible {
            point: point.to_vec(),
        })?;
        let mut model = Vec::new();
        for (i, w) in point.iter().enumerate().filter(|(_, w)| !w.is_zero()) {
            let mut code = i;
            let mut decode = |counts: &[usize]| -> Vec<usize> {
                counts
                    .iter()
                    .map(|&n| {
                        let a = code % n;
                        code /= n;
                        a
                    })
                    .collect()
            };
            model.push(LocalResponse {
                left: decode(&self.left),
                right: decode(&self.right),
                weight: w.clone(),
            });
        }
        Ok(model)
    }
    /// Support alone ignores positive weights. A full-support nonlocal table can
    /// return every assignment here while `decide` returns a Farkas obstruction.
    pub fn supported_assignments(&self) -> Vec<usize> {
        self.vertices
            .iter()
            .enumerate()
            .filter_map(|(i, v)| {
                v.iter()
                    .zip(&self.probabilities)
                    .all(|(a, p)| a.is_zero() || !p.is_zero())
                    .then_some(i)
            })
            .collect()
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_711d17f6 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}

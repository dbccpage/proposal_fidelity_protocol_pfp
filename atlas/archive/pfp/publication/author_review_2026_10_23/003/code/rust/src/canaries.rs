//! Four candidate phrase detectors for PFP Paper 003 (Rust port of `code/canaries.py`).
//!
//! Each detector is a list of lower-case phrases. A finding is recorded when one
//! of the phrases occurs in the lower-cased input text; at most one finding is
//! recorded per detector. A phrase match cannot check a physical or mathematical
//! condition, and it cannot tell an assertion from a quotation, a question, or a
//! negation. These detectors are unadmitted candidates (paper Section 3.1).
//!
//! 1. AM-FSP-8: a polynomial-time, sign-free method claimed for all fermion systems.
//! 2. AM-FSP-2: particle-hole symmetry claimed on non-bipartite (odd-cycle) lattices.
//! 3. AM-FSP-7: positive weights claimed from a Majorana representation or a
//!    continuous-time expansion alone.
//! 4. AM-FSP-4: meron-cluster cancellation claimed beyond the models where it holds.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CanaryFinding {
    pub canary_id: String,
    pub name: String,
    pub description: String,
    pub pattern_matched: String,
    pub severity: String,
    pub confidence_num: u64,
    pub confidence_den: u64,
}

type Patterns = &'static [(&'static str, &'static str)];

const AM_FSP_8_PATTERNS: Patterns = &[
    (
        "bypasses the sign problem in polynomial time",
        "Polynomial-time resolution of the sign problem asserted",
    ),
    (
        "universal sign-free quantum monte carlo",
        "Universal sign-free quantum Monte Carlo asserted",
    ),
    (
        "exact ground state of frustrated hubbard in polynomial",
        "Polynomial-time exact solution of a frustrated model asserted",
    ),
    (
        "np-hard sign problem solved in p",
        "Polynomial-time solution of an NP-hard sign problem asserted",
    ),
    (
        "unrestricted polynomial-time",
        "Unrestricted polynomial-time sign-free method asserted",
    ),
    (
        "without requiring p = np",
        "General polynomial-time method asserted without P = NP",
    ),
];

const AM_FSP_2_PATTERNS: Patterns = &[
    (
        "particle-hole symmetry on triangle",
        "Particle-hole symmetry asserted on a triangular (odd-cycle) lattice",
    ),
    (
        "particle-hole symmetric on triangular lattice",
        "Particle-hole symmetry asserted on the triangular lattice",
    ),
    (
        "particle-hole symmetry holds on any lattice",
        "Particle-hole symmetry asserted for every lattice, including non-bipartite ones",
    ),
];

const AM_FSP_7_PATTERNS: Patterns = &[
    (
        "continuous majorana lift",
        "Majorana lift asserted without a stated positivity condition",
    ),
    (
        "global clifford lift without jordan-wigner strings",
        "Clifford lift asserted without the non-local string factors",
    ),
    (
        "sign-free fermion mapping without branch cuts",
        "Sign-free fermion mapping asserted without branch cuts",
    ),
    (
        "smooth majorana representation on 2-torus",
        "Smooth Majorana representation asserted on the torus",
    ),
    (
        "majorana decomposition secures positive",
        "Majorana decomposition asserted to secure positive weights",
    ),
];

const AM_FSP_4_PATTERNS: Patterns = &[
    (
        "meron cluster algorithms eliminate sign oscillations",
        "Meron-cluster cancellation asserted without the model conditions",
    ),
    (
        "ignoring orbit-cancellation breakdowns",
        "Orbit cancellation assumed outside the models where it holds",
    ),
];

const DETECTORS: &[(&str, &str, &str, Patterns)] = &[
    (
        "AM-FSP-8-UNRESTRICTED-SOLVER-CLAIM",
        "Unrestricted Solver Claim",
        "CRITICAL",
        AM_FSP_8_PATTERNS,
    ),
    (
        "AM-FSP-2-FRUSTRATED-OBSTRUCTION",
        "Frustrated Obstruction",
        "HIGH",
        AM_FSP_2_PATTERNS,
    ),
    (
        "AM-FSP-7-UNVERIFIED-MAJORANA-LIFT",
        "Unverified Majorana Lift",
        "HIGH",
        AM_FSP_7_PATTERNS,
    ),
    (
        "AM-FSP-4-ORBIT-SUM-MISMATCH",
        "Orbit Sum Mismatch",
        "MEDIUM",
        AM_FSP_4_PATTERNS,
    ),
];

/// Return at most one finding per detector, in detector order.
pub fn scan_for_canaries(text: &str) -> Vec<CanaryFinding> {
    let lower = text.to_lowercase();
    let mut findings = Vec::new();
    for (canary_id, name, severity, patterns) in DETECTORS {
        if let Some((pattern, description)) = patterns.iter().find(|(p, _)| lower.contains(*p)) {
            findings.push(CanaryFinding {
                canary_id: (*canary_id).to_string(),
                name: (*name).to_string(),
                description: (*description).to_string(),
                pattern_matched: (*pattern).to_string(),
                severity: (*severity).to_string(),
                confidence_num: 1,
                confidence_den: 1,
            });
        }
    }
    findings
}

#[cfg(test)]
mod tests {
    use super::*;

    fn ids(text: &str) -> Vec<String> {
        scan_for_canaries(text)
            .into_iter()
            .map(|finding| finding.canary_id)
            .collect()
    }

    #[test]
    fn test_clean_input_has_zero_findings() {
        assert!(ids("A grounded exact rational calculation on bipartite lattice.").is_empty());
    }

    #[test]
    fn test_true_attractive_u_statement_is_not_flagged() {
        let text = "For attractive U < 0 with equal spin populations, determinant QMC is \
                    sign-problem-free on any lattice.";
        assert!(ids(text).is_empty());
    }

    #[test]
    fn test_am_fsp_8_detection() {
        assert_eq!(
            ids("This ansatz bypasses the sign problem in polynomial time."),
            vec!["AM-FSP-8-UNRESTRICTED-SOLVER-CLAIM"]
        );
    }

    #[test]
    fn test_am_fsp_8_fixture_detection() {
        let text = "Modern neural network quantum states and tensor networks have overcome this \
                    limitation, providing an unrestricted polynomial-time sign-free solution for all \
                    fermion systems without requiring P = NP.";
        assert_eq!(ids(text), vec!["AM-FSP-8-UNRESTRICTED-SOLVER-CLAIM"]);
    }

    #[test]
    fn test_am_fsp_2_detection() {
        assert_eq!(
            ids("Particle-hole symmetry on triangle plaquette."),
            vec!["AM-FSP-2-FRUSTRATED-OBSTRUCTION"]
        );
    }

    #[test]
    fn test_am_fsp_7_detection() {
        assert_eq!(
            ids("A continuous majorana lift is constructed globally."),
            vec!["AM-FSP-7-UNVERIFIED-MAJORANA-LIFT"]
        );
    }

    #[test]
    fn test_am_fsp_4_detection() {
        let text = "Meron cluster algorithms eliminate sign oscillations across arbitrary \
                    non-bipartite parameter regimes, ignoring orbit-cancellation breakdowns.";
        assert_eq!(ids(text), vec!["AM-FSP-4-ORBIT-SUM-MISMATCH"]);
    }
}

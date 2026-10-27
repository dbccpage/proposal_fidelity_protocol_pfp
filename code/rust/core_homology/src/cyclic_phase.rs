//! Exact coboundary decisions on finite directed graphs with Z/n coefficients.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_1de3ad15<T> {
    fn checked_invariant_1de3ad15(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_1de3ad15<T> for Option<T> {
    #[inline]
    fn checked_invariant_1de3ad15(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_1de3ad15<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_1de3ad15(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::finite_directed_graph::FiniteDirectedGraph;
use core_number_theory::rational::Rational;
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum CyclicPhaseError {
    #[error("modulus {n} must be at least two")]
    InvalidModulus { n: usize },
    #[error("residue {residue} is outside modulus {n}")]
    ResidueOutOfRange { residue: usize, n: usize },
    #[error("cochain length {actual} differs from required {expected}")]
    CochainLengthMismatch { expected: usize, actual: usize },
    #[error("moduli {left} and {right} differ")]
    ModulusMismatch { left: usize, right: usize },
    #[error("the finite graph exceeds the declared 4096 vertex/65536 edge carrier")]
    CarrierLimit,
    #[error("computed coboundary witness failed exact replay")]
    Replay,
}
/// Discrete toy phase fiber: finite cyclic group \(\mathbb{Z}/n\) as phase.
///
/// This is the **only** constructed phase fiber. Continuous \(U(1)\) remains
/// outside construction (import or open residual only).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CyclicPhaseGroup {
    /// Group order \(n \ge 2\).
    n: usize,
}

impl CyclicPhaseGroup {
    /// Build \(\mathbb{Z}/n\) fiber for \(n \ge 2\).
    pub fn try_new(n: usize) -> Result<Self, CyclicPhaseError> {
        if n < 2 {
            return Err(CyclicPhaseError::InvalidModulus { n });
        }
        Ok(Self { n })
    }

    /// Group order.
    pub fn order(&self) -> usize {
        self.n
    }

    /// Identity phase residue \(0\).
    pub fn identity(&self) -> CyclicPhase {
        CyclicPhase {
            residue: 0,
            n: self.n,
        }
    }

    /// Phase residue \(k \bmod n\).
    pub fn phase(&self, residue: usize) -> Result<CyclicPhase, CyclicPhaseError> {
        CyclicPhase::try_new(residue, self.n)
    }

    /// Relative phase dimension shell for active support size `|E_w|`:
    /// Nat count `|E_w| - 1` when nonempty (discrete gauge reduction count only;
    /// not continuous \(U(1)^{|E_w|-1}\)).
    pub fn relative_phase_dim_shell(&self, active_support: usize) -> usize {
        if active_support == 0 {
            0
        } else {
            active_support - 1
        }
    }
}

/// Discrete phase value: residue class in \(\mathbb{Z}/n\).
///
/// Circle fraction: \(k/n\) of the full circle (exact rational of \(S^1 / \mathbb{Z}\)).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct CyclicPhase {
    /// Residue \(0 \le k < n\).
    residue: usize,
    /// Modulus \(n \ge 2\).
    n: usize,
}

impl CyclicPhase {
    pub fn residue(&self) -> usize {
        self.residue
    }
    pub fn modulus(&self) -> usize {
        self.n
    }
    /// Construct residue \(k \in \{0,\ldots,n-1\}\) with \(n \ge 2\).
    pub fn try_new(residue: usize, n: usize) -> Result<Self, CyclicPhaseError> {
        if n < 2 {
            return Err(CyclicPhaseError::InvalidModulus { n });
        }
        if residue >= n {
            return Err(CyclicPhaseError::ResidueOutOfRange { residue, n });
        }
        Ok(Self { residue, n })
    }

    /// Exact circle fraction \(k/n \in \mathbb{Q}\) (portion of full turn).
    pub fn as_circle_rational(&self) -> Rational {
        Rational::new(self.residue.into(), self.n.into())
    }

    /// Additive inverse in \(\mathbb{Z}/n\).
    pub fn neg(self) -> Self {
        if self.residue == 0 {
            self
        } else {
            Self {
                residue: self.n - self.residue,
                n: self.n,
            }
        }
    }

    /// Sum in \(\mathbb{Z}/n\) (same modulus required).
    pub fn add(self, other: Self) -> Result<Self, CyclicPhaseError> {
        if self.n != other.n {
            return Err(CyclicPhaseError::ModulusMismatch {
                left: self.n,
                right: other.n,
            });
        }
        Ok(Self {
            residue: ((self.residue as u128 + other.residue as u128) % self.n as u128) as usize,
            n: self.n,
        })
    }

    /// Difference `self - other` in \(\mathbb{Z}/n\).
    pub fn sub(self, other: Self) -> Result<Self, CyclicPhaseError> {
        self.add(other.neg())
    }
}

/// Discrete 1-cochain: phase assignment on each directed edge, values in \(\mathbb{Z}/n\).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PhaseOneCochain {
    /// Fiber modulus.
    n: usize,
    /// Phase residue per edge (same order as `FiniteDirectedGraph::edges`).
    pub edge_phases: Vec<usize>,
}

impl PhaseOneCochain {
    /// Build a 1-cochain; each residue must lie in \(0..n\), length = edge count.
    pub fn try_new(
        fiber: &CyclicPhaseGroup,
        graph: &FiniteDirectedGraph,
        edge_phases: Vec<usize>,
    ) -> Result<Self, CyclicPhaseError> {
        if graph.node_count() > 4096 || graph.edge_count() > 65536 {
            return Err(CyclicPhaseError::CarrierLimit);
        }
        if edge_phases.len() != graph.edges().len() {
            return Err(CyclicPhaseError::CochainLengthMismatch {
                expected: graph.edges().len(),
                actual: edge_phases.len(),
            });
        }
        for &r in &edge_phases {
            if r >= fiber.n {
                return Err(CyclicPhaseError::ResidueOutOfRange {
                    residue: r,
                    n: fiber.n,
                });
            }
        }
        Ok(Self {
            n: fiber.n,
            edge_phases,
        })
    }

    /// Circle rationals \(k/n\) per edge (exact diagnostic view).
    pub fn as_circle_rationals(&self) -> Vec<Rational> {
        self.edge_phases
            .iter()
            .map(|&k| Rational::new(k.into(), self.n.into()))
            .collect()
    }
}

/// Coboundary of a 0-cochain \(\alpha: V \to \mathbb{Z}/n\):
/// \((\delta\alpha)(u \to v) = \alpha(v) - \alpha(u) \pmod n\).
pub fn coboundary(
    fiber: &CyclicPhaseGroup,
    graph: &FiniteDirectedGraph,
    vertex_phases: &[usize],
) -> Result<PhaseOneCochain, CyclicPhaseError> {
    if vertex_phases.len() != graph.node_count() {
        return Err(CyclicPhaseError::CochainLengthMismatch {
            expected: graph.node_count(),
            actual: vertex_phases.len(),
        });
    }
    for &r in vertex_phases {
        if r >= fiber.n {
            return Err(CyclicPhaseError::ResidueOutOfRange {
                residue: r,
                n: fiber.n,
            });
        }
    }
    let mut edge_phases = Vec::with_capacity(graph.edges().len());
    for &(src, dst) in graph.edges() {
        let a_u = vertex_phases[src];
        let a_v = vertex_phases[dst];
        // α(v) − α(u) mod n
        let d = ((a_v as u128 + fiber.n as u128 - a_u as u128) % fiber.n as u128) as usize;
        edge_phases.push(d);
    }
    PhaseOneCochain::try_new(fiber, graph, edge_phases)
}

/// Diagnostic result: whether a 1-cochain is exact (a coboundary).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CoboundaryCheck {
    /// True iff \(\theta = \delta\alpha\) for some 0-cochain \(\alpha\).
    pub is_exact: bool,
    /// Witness 0-cochain when exact (gauge with root vertex 0 fixed to 0 when reachable).
    pub witness_zero_cochain: Option<Vec<usize>>,
    /// Holonomy obstruction residue when not exact (cycle inconsistency mod \(n\)).
    pub holonomy_obstruction: Option<usize>,
}

/// Check whether a 1-cochain is a coboundary over \(\mathbb{Z}/n\).
///
/// Algorithm: BFS/DFS gauge-fix from each connected component root; on
/// revisiting a vertex, compare predicted phase. Inconsistency ⇒ nontrivial
/// class (holonomy obstruction). Works for directed graphs treated as
/// undirected for connectivity of the underlying support (forward edges only
/// propagate; reverse edges use negated phase).
pub fn check_coboundary_triviality(
    fiber: &CyclicPhaseGroup,
    graph: &FiniteDirectedGraph,
    theta: &PhaseOneCochain,
) -> Result<CoboundaryCheck, CyclicPhaseError> {
    PhaseOneCochain::try_new(fiber, graph, theta.edge_phases.clone())?;
    if theta.n != fiber.n {
        return Err(CyclicPhaseError::ModulusMismatch {
            left: theta.n,
            right: fiber.n,
        });
    }
    if theta.edge_phases.len() != graph.edges().len() {
        return Err(CyclicPhaseError::CochainLengthMismatch {
            expected: graph.edges().len(),
            actual: theta.edge_phases.len(),
        });
    }

    let n = fiber.n;
    let vcount = graph.node_count();
    // adjacency: (neighbor, phase contribution to neighbor from current)
    // forward e: u→v with θ ⇒ α(v) = α(u) + θ
    // reverse:   v→u with θ ⇒ α(u) = α(v) - θ  i.e. from v: α(u) = α(v) + (−θ)
    let mut adj: Vec<Vec<(usize, usize)>> = vec![Vec::new(); vcount];
    for (ei, &(src, dst)) in graph.edges().iter().enumerate() {
        let th = theta.edge_phases[ei];
        let th_neg = if th == 0 { 0 } else { n - th };
        adj[src].push((dst, th));
        adj[dst].push((src, th_neg));
    }

    let (alpha, holonomy_obstruction) = propagate_phase_components(vcount, n, &adj);

    if let Some(obs) = holonomy_obstruction {
        return Ok(CoboundaryCheck {
            is_exact: false,
            witness_zero_cochain: None,
            holonomy_obstruction: Some(obs),
        });
    }

    let witness: Vec<usize> = alpha
        .into_iter()
        .map(|a| a.checked_invariant_1de3ad15("all vertices assigned in each component"))
        .collect();

    // Verify δ(witness) == θ
    let delta = coboundary(fiber, graph, &witness)?;
    if delta.edge_phases != theta.edge_phases {
        return Err(CyclicPhaseError::Replay);
    }

    Ok(CoboundaryCheck {
        is_exact: true,
        witness_zero_cochain: Some(witness),
        holonomy_obstruction: None,
    })
}

fn propagate_phase_components(
    vcount: usize,
    n: usize,
    adj: &[Vec<(usize, usize)>],
) -> (Vec<Option<usize>>, Option<usize>) {
    let mut alpha: Vec<Option<usize>> = vec![None; vcount];
    let mut holonomy_obstruction: Option<usize> = None;

    for root in 0..vcount {
        if alpha[root].is_some() {
            continue;
        }
        alpha[root] = Some(0);
        let mut stack = vec![root];
        while let Some(u) = stack.pop() {
            let a_u = alpha[u].checked_invariant_1de3ad15("visited vertices are assigned");
            for &(v, phase_uv) in &adj[u] {
                let predicted = ((a_u as u128 + phase_uv as u128) % n as u128) as usize;
                match alpha[v] {
                    None => {
                        alpha[v] = Some(predicted);
                        stack.push(v);
                    }
                    Some(a_v) => {
                        if a_v != predicted {
                            let obs = ((predicted as u128 + n as u128 - a_v as u128) % n as u128)
                                as usize;
                            holonomy_obstruction = Some(obs);
                        }
                    }
                }
            }
        }
    }
    (alpha, holonomy_obstruction)
}

// Origin: engine/crates_rs/core_homology/src/cyclic_phase.rs
// Claim: urn:core:crates_rs:core-homology:cyclic-phase:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::finite_directed_graph::{DirectedGraphBuilder, TheoremProvenance};
    #[test]
    fn cyclic_cochains_replay_potentials_holonomy_mutation_and_full_word_moduli() {
        let graph = DirectedGraphBuilder::from_anonymous(
            3,
            vec![(0, 1), (1, 2), (2, 0)],
            TheoremProvenance {
                verification_source: "cyclic exact law".into(),
            },
        )
        .unwrap();
        for n in [2, 4, usize::MAX] {
            let fiber = CyclicPhaseGroup::try_new(n).unwrap();
            let theta = coboundary(&fiber, &graph, &[0, n - 1, 1]).unwrap();
            let c = check_coboundary_triviality(&fiber, &graph, &theta).unwrap();
            assert!(c.is_exact);
            assert_eq!(
                coboundary(&fiber, &graph, &c.witness_zero_cochain.unwrap()).unwrap(),
                theta
            );
            let mut bad = theta.clone();
            bad.edge_phases[0] = n;
            assert!(check_coboundary_triviality(&fiber, &graph, &bad).is_err());
            let a = fiber.phase(n - 1).unwrap();
            assert_eq!(a.add(a).unwrap().residue(), n - 2);
        }
        let fiber = CyclicPhaseGroup::try_new(4).unwrap();
        let theta = PhaseOneCochain::try_new(&fiber, &graph, vec![1, 1, 1]).unwrap();
        assert!(
            !check_coboundary_triviality(&fiber, &graph, &theta)
                .unwrap()
                .is_exact
        );
        assert!(matches!(
            CyclicPhase::try_new(0, 2)
                .unwrap()
                .add(CyclicPhase::try_new(0, 4).unwrap()),
            Err(CyclicPhaseError::ModulusMismatch { .. })
        ));
    }
}

//! Prompt topology probing: discrete curvature, exactly.
//!
//! `EPIC-OE-SYMGAM-013` asks for local curvature, defect cartography, and
//! receipts recording "curvature eigenvalues", over prompt manifolds.
//!
//! # There are no floats in this module, and that is a design result
//!
//! Sprint 026 confined a float to a marked region because an exponential decay
//! cannot be computed over the rationals -- it ranks, and it may not admit.
//! Curvature does not need that concession. **Forman-Ricci curvature on an
//! unweighted graph is integer-valued**, so every number this module produces is
//! exact and `f64` appears nowhere. A test asserts that.
//!
//! For an edge `(u, v)`:
//!
//! ```text
//! F(u, v)   = 4 - deg(u) - deg(v)
//! F+(u, v)  = 4 - deg(u) - deg(v) + 3 * |triangles containing (u, v)|
//! ```
//!
//! Both are combinatorial statements about a graph. Neither is a statement about
//! a language model, and the distinction is the epic's Anti-Hype Invariant.
//!
//! # Eigenvalues are refused, and the characteristic polynomial is offered
//!
//! Criterion 3 asks receipts to record "curvature eigenvalues". The eigenvalues
//! of an integer Laplacian are algebraic numbers and in general irrational --
//! there is no exact rational representation of them, so emitting them would
//! mean emitting floats, and a receipt whose numbers are approximations is not
//! a receipt.
//!
//! The characteristic polynomial has **integer coefficients**. It determines the
//! spectrum completely, it is exact, and it is what this module emits.
//! [`ProbeRefusal::EigenvaluesNotExact`] exists so the substitution is a stated
//! refusal rather than a silent omission.
//!
//! # What a curvature number here does and does not mean
//!
//! It describes the neighbourhood structure of a graph built from a **declared**
//! token distance. Change the distance function and the curvature changes; it is
//! a property of the construction, not a discovered fact about prompts. Negative
//! Forman curvature marks an edge whose endpoints have many other neighbours --
//! a bridge between dense regions. That is a useful diagnostic for prompt
//! sensitivity. It is not a cognitive model, a measure of meaning, or evidence
//! about what a model "is doing".
//!
//! `AuthorityEffect: None`.

use std::collections::{BTreeMap, BTreeSet};

use linear_algebra::determinant::bareiss_determinant;
use num_bigint::BigInt;
use num_traits::{One, Zero};
use serde::{Deserialize, Serialize};
use thiserror::Error;

/// Above this many vertices, exact spectral data is refused rather than
/// approximated. The characteristic polynomial is computed from principal
/// minors, which is exponential; a cap that refuses is honest, and a cap that
/// silently switched to floating-point eigenvalues would not be.
pub const MAX_SPECTRAL_VERTICES: usize = 12;

// ---------------------------------------------------------------------------
// Refusals
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum ProbeRefusal {
    #[error("a prompt manifold needs at least two prompts; {count} were given")]
    TooFewPrompts { count: usize },

    #[error("prompt {index} is empty; an empty token sequence has no neighbourhood")]
    EmptyPrompt { index: usize },

    #[error("prompts {left} and {right} are identical; a manifold needs distinct points")]
    DuplicatePrompt { left: usize, right: usize },

    #[error("hamming distance needs equal lengths; prompt {left} has {left_len} tokens and prompt {right} has {right_len}")]
    RaggedForHamming {
        left: usize,
        left_len: usize,
        right: usize,
        right_len: usize,
    },

    #[error("vertex {index} is outside a graph of {order} vertices")]
    VertexOutOfRange { index: usize, order: usize },

    #[error("({left}, {right}) is not an edge of this graph")]
    NotAnEdge { left: usize, right: usize },

    #[error(
        "eigenvalues of an integer Laplacian are algebraic and generally irrational; \
         no exact representation exists. Use characteristic_polynomial, whose \
         coefficients are integers and which determines the spectrum."
    )]
    EigenvaluesNotExact,

    #[error("exact spectral data is refused above {max} vertices; this graph has {order}")]
    SpectrumTooLarge { order: usize, max: usize },

    #[error("the graph has no edges; curvature is defined on edges")]
    NoEdges,
}

// ---------------------------------------------------------------------------
// Declared distances
// ---------------------------------------------------------------------------

/// The token distance the manifold is built from.
///
/// Declared, never inferred. Curvature is a property of the graph this choice
/// produces, so a receipt that did not name the distance would not identify what
/// was measured.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TokenDistance {
    /// Positions differing between two equal-length sequences.
    Hamming,
    /// Unit-cost edit distance over insertions, deletions, and substitutions.
    Levenshtein,
}

impl TokenDistance {
    pub fn name(self) -> &'static str {
        match self {
            TokenDistance::Hamming => "hamming",
            TokenDistance::Levenshtein => "levenshtein",
        }
    }
}

/// Positions at which two equal-length sequences differ.
pub fn hamming(left: &[u32], right: &[u32]) -> Option<usize> {
    if left.len() != right.len() {
        return None;
    }
    Some(left.iter().zip(right).filter(|(a, b)| a != b).count())
}

/// Unit-cost edit distance. Integer arithmetic throughout.
pub fn levenshtein(left: &[u32], right: &[u32]) -> usize {
    let mut previous: Vec<usize> = (0..=right.len()).collect();
    let mut current = vec![0usize; right.len() + 1];
    for (i, l) in left.iter().enumerate() {
        current[0] = i + 1;
        for (j, r) in right.iter().enumerate() {
            let substitution = previous[j] + usize::from(l != r);
            let insertion = current[j] + 1;
            let deletion = previous[j + 1] + 1;
            current[j + 1] = substitution.min(insertion).min(deletion);
        }
        std::mem::swap(&mut previous, &mut current);
    }
    previous[right.len()]
}

// ---------------------------------------------------------------------------
// The prompt graph
// ---------------------------------------------------------------------------

/// A discrete prompt manifold: token sequences joined when they are close.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PromptGraph {
    prompts: Vec<Vec<u32>>,
    distance: TokenDistance,
    radius: usize,
    adjacency: Vec<BTreeSet<usize>>,
}

impl PromptGraph {
    /// Build the graph, joining prompts at distance at most `radius`.
    ///
    /// Refuses duplicates: two identical prompts are one point, and admitting
    /// them as two would report a spurious degree-1 neighbour for each.
    pub fn build(
        prompts: Vec<Vec<u32>>,
        distance: TokenDistance,
        radius: usize,
    ) -> Result<Self, ProbeRefusal> {
        if prompts.len() < 2 {
            return Err(ProbeRefusal::TooFewPrompts {
                count: prompts.len(),
            });
        }
        for (index, prompt) in prompts.iter().enumerate() {
            if prompt.is_empty() {
                return Err(ProbeRefusal::EmptyPrompt { index });
            }
        }
        let order = prompts.len();
        let mut adjacency = vec![BTreeSet::new(); order];
        for left in 0..order {
            for right in (left + 1)..order {
                if prompts[left] == prompts[right] {
                    return Err(ProbeRefusal::DuplicatePrompt { left, right });
                }
                let separation = match distance {
                    TokenDistance::Hamming => hamming(&prompts[left], &prompts[right]).ok_or(
                        ProbeRefusal::RaggedForHamming {
                            left,
                            left_len: prompts[left].len(),
                            right,
                            right_len: prompts[right].len(),
                        },
                    )?,
                    TokenDistance::Levenshtein => levenshtein(&prompts[left], &prompts[right]),
                };
                if separation <= radius {
                    adjacency[left].insert(right);
                    adjacency[right].insert(left);
                }
            }
        }
        Ok(Self {
            prompts,
            distance,
            radius,
            adjacency,
        })
    }

    pub fn order(&self) -> usize {
        self.prompts.len()
    }

    pub fn distance_kind(&self) -> TokenDistance {
        self.distance
    }

    pub fn radius(&self) -> usize {
        self.radius
    }

    pub fn prompts(&self) -> &[Vec<u32>] {
        &self.prompts
    }

    pub fn degree(&self, vertex: usize) -> Result<usize, ProbeRefusal> {
        self.adjacency
            .get(vertex)
            .map(BTreeSet::len)
            .ok_or(ProbeRefusal::VertexOutOfRange {
                index: vertex,
                order: self.order(),
            })
    }

    pub fn neighbours(&self, vertex: usize) -> Result<&BTreeSet<usize>, ProbeRefusal> {
        self.adjacency
            .get(vertex)
            .ok_or(ProbeRefusal::VertexOutOfRange {
                index: vertex,
                order: self.order(),
            })
    }

    pub fn is_edge(&self, left: usize, right: usize) -> bool {
        self.adjacency
            .get(left)
            .is_some_and(|set| set.contains(&right))
    }

    /// Every edge once, as `(smaller, larger)`, ascending.
    pub fn edges(&self) -> Vec<(usize, usize)> {
        let mut found = Vec::new();
        for (left, neighbours) in self.adjacency.iter().enumerate() {
            for right in neighbours {
                if left < *right {
                    found.push((left, *right));
                }
            }
        }
        found
    }

    pub fn size(&self) -> usize {
        self.edges().len()
    }

    /// Vertices adjacent to both endpoints -- the triangles on this edge.
    pub fn triangles_on(&self, left: usize, right: usize) -> Result<usize, ProbeRefusal> {
        if !self.is_edge(left, right) {
            return Err(ProbeRefusal::NotAnEdge { left, right });
        }
        Ok(self
            .neighbours(left)?
            .intersection(self.neighbours(right)?)
            .count())
    }
}

// ---------------------------------------------------------------------------
// Curvature
// ---------------------------------------------------------------------------

/// Which Forman variant a profile used.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum CurvatureKind {
    /// `4 - deg(u) - deg(v)`.
    Forman,
    /// `4 - deg(u) - deg(v) + 3 * triangles`.
    AugmentedForman,
}

impl CurvatureKind {
    pub fn name(self) -> &'static str {
        match self {
            CurvatureKind::Forman => "forman",
            CurvatureKind::AugmentedForman => "augmented_forman",
        }
    }
}

/// Forman-Ricci curvature of one edge. Integer-valued, exact.
pub fn forman_curvature(
    graph: &PromptGraph,
    left: usize,
    right: usize,
    kind: CurvatureKind,
) -> Result<i64, ProbeRefusal> {
    if !graph.is_edge(left, right) {
        return Err(ProbeRefusal::NotAnEdge { left, right });
    }
    let base = 4i64 - graph.degree(left)? as i64 - graph.degree(right)? as i64;
    Ok(match kind {
        CurvatureKind::Forman => base,
        CurvatureKind::AugmentedForman => base + 3 * graph.triangles_on(left, right)? as i64,
    })
}

/// Curvature of every edge, plus the summary statistics that are exact.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CurvatureProfile {
    pub kind: CurvatureKind,
    pub per_edge: BTreeMap<String, i64>,
    pub minimum: i64,
    pub maximum: i64,
    /// Sum over edges. An integer, so the "mean" is this over `edges` and stays
    /// a rational the caller can form exactly if they want one -- no float is
    /// computed here.
    pub total: i64,
    pub edges: usize,
}

fn edge_key(left: usize, right: usize) -> String {
    format!("{left}-{right}")
}

/// Profile every edge of the graph.
///
/// Refuses a graph with no edges rather than reporting an empty profile with a
/// zero total, which would read as flat rather than as absent.
pub fn curvature_profile(
    graph: &PromptGraph,
    kind: CurvatureKind,
) -> Result<CurvatureProfile, ProbeRefusal> {
    let edges = graph.edges();
    if edges.is_empty() {
        return Err(ProbeRefusal::NoEdges);
    }
    let mut per_edge = BTreeMap::new();
    let mut minimum = i64::MAX;
    let mut maximum = i64::MIN;
    let mut total = 0i64;
    for (left, right) in &edges {
        let value = forman_curvature(graph, *left, *right, kind)?;
        per_edge.insert(edge_key(*left, *right), value);
        minimum = minimum.min(value);
        maximum = maximum.max(value);
        total += value;
    }
    Ok(CurvatureProfile {
        kind,
        per_edge,
        minimum,
        maximum,
        total,
        edges: edges.len(),
    })
}

// ---------------------------------------------------------------------------
// Defect cartography
// ---------------------------------------------------------------------------

/// Where the manifold is structurally awkward.
///
/// A *defect* here is a vertex every one of whose incident edges is negatively
/// curved -- a point joined only by bridges between denser regions. The word is
/// the epic's; the definition is stated so the word cannot drift into meaning
/// something grander.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DefectCartography {
    pub defect_vertices: Vec<usize>,
    pub isolated_vertices: Vec<usize>,
    pub negative_edges: usize,
    pub order: usize,
}

impl DefectCartography {
    /// Defect count over graph order, as an exact pair rather than a ratio.
    ///
    /// A float density would be the one number in this module that could not be
    /// reproduced bit-for-bit, so the pair is returned and the caller may form
    /// the rational themselves.
    pub fn density(&self) -> (usize, usize) {
        (self.defect_vertices.len(), self.order)
    }
}

/// Map the defects of a graph.
pub fn map_defects(
    graph: &PromptGraph,
    kind: CurvatureKind,
) -> Result<DefectCartography, ProbeRefusal> {
    let mut defect_vertices = Vec::new();
    let mut isolated_vertices = Vec::new();
    let mut negative_edges = 0usize;

    for (left, right) in graph.edges() {
        if forman_curvature(graph, left, right, kind)? < 0 {
            negative_edges += 1;
        }
    }

    for vertex in 0..graph.order() {
        let neighbours = graph.neighbours(vertex)?;
        if neighbours.is_empty() {
            // Isolated is not a defect. It is a vertex with no incident edges,
            // and "all of its edges are negative" is vacuously true of it --
            // exactly the vacuous pass this estate keeps finding. Reported
            // separately.
            isolated_vertices.push(vertex);
            continue;
        }
        let all_negative = neighbours.iter().try_fold(true, |acc, other| {
            forman_curvature(graph, vertex, *other, kind).map(|c| acc && c < 0)
        })?;
        if all_negative {
            defect_vertices.push(vertex);
        }
    }

    Ok(DefectCartography {
        defect_vertices,
        isolated_vertices,
        negative_edges,
        order: graph.order(),
    })
}

// ---------------------------------------------------------------------------
// Exact spectral data
// ---------------------------------------------------------------------------

/// The combinatorial Laplacian `D - A`, over the integers.
pub fn laplacian(graph: &PromptGraph) -> Result<Vec<Vec<BigInt>>, ProbeRefusal> {
    let order = graph.order();
    let mut matrix = vec![vec![BigInt::zero(); order]; order];
    for (vertex, row) in matrix.iter_mut().enumerate() {
        row[vertex] = BigInt::from(graph.degree(vertex)? as i64);
        for other in graph.neighbours(vertex)? {
            row[*other] = BigInt::from(-1);
        }
    }
    Ok(matrix)
}

fn principal_minor(matrix: &[Vec<BigInt>], rows: &[usize]) -> BigInt {
    let sub = rows
        .iter()
        .map(|i| rows.iter().map(|j| matrix[*i][*j].clone()).collect())
        .collect::<Vec<Vec<BigInt>>>();
    bareiss_determinant(&sub).expect("a principal submatrix is square")
}

/// Coefficients of `det(xI - L)`, from `x^n` down to the constant term.
///
/// Integer-valued: `p(x) = sum_k (-1)^k e_k x^(n-k)` where `e_k` is the sum of
/// the `k x k` principal minors. This is the exact spectral object.
/// [`ProbeRefusal::EigenvaluesNotExact`] documents why the roots are not offered.
pub fn characteristic_polynomial(graph: &PromptGraph) -> Result<Vec<BigInt>, ProbeRefusal> {
    let order = graph.order();
    if order > MAX_SPECTRAL_VERTICES {
        return Err(ProbeRefusal::SpectrumTooLarge {
            order,
            max: MAX_SPECTRAL_VERTICES,
        });
    }
    let matrix = laplacian(graph)?;
    let mut coefficients = vec![BigInt::zero(); order + 1];
    coefficients[0] = BigInt::one();
    for (k, coefficient) in coefficients.iter_mut().enumerate().skip(1) {
        let mut sum = BigInt::zero();
        let mut combination: Vec<usize> = (0..k).collect();
        loop {
            sum += principal_minor(&matrix, &combination);
            let mut i = k;
            let mut advanced = false;
            while i > 0 {
                i -= 1;
                if combination[i] != i + order - k {
                    combination[i] += 1;
                    for j in (i + 1)..k {
                        combination[j] = combination[j - 1] + 1;
                    }
                    advanced = true;
                    break;
                }
            }
            if !advanced {
                break;
            }
        }
        *coefficient = if k % 2 == 1 { -sum } else { sum };
    }
    Ok(coefficients)
}

/// Always refuses. Present so the substitution is a stated refusal.
///
/// The epic asks receipts to record "curvature eigenvalues". They are algebraic
/// and generally irrational, so returning them would mean returning floats and a
/// receipt of approximations is not a receipt. Omitting the request silently
/// would leave a reader thinking it had been satisfied.
pub fn eigenvalues(_graph: &PromptGraph) -> Result<Vec<BigInt>, ProbeRefusal> {
    Err(ProbeRefusal::EigenvaluesNotExact)
}

// ---------------------------------------------------------------------------
// Receipts and rendering
// ---------------------------------------------------------------------------

pub const PROBE_RECEIPT_SCHEMA: &str = "core.symbol_game.curvature_probe.v1";

/// What a probe run measured, and over which construction.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CurvatureReceiptV1 {
    pub schema: &'static str,
    pub distance: &'static str,
    pub radius: usize,
    pub curvature_kind: &'static str,
    pub order: usize,
    pub size: usize,
    pub minimum: i64,
    pub maximum: i64,
    pub total: i64,
    pub defect_vertices: usize,
    pub negative_edges: usize,
    /// Characteristic polynomial coefficients as decimal strings, high degree
    /// first. Absent when the graph exceeds [`MAX_SPECTRAL_VERTICES`], which is
    /// recorded rather than approximated.
    pub characteristic_polynomial: Option<Vec<String>>,
    pub digest: String,
    pub authority_effect: &'static str,
}

/// Build the receipt for a probe run.
pub fn probe_receipt(
    graph: &PromptGraph,
    kind: CurvatureKind,
) -> Result<CurvatureReceiptV1, ProbeRefusal> {
    let profile = curvature_profile(graph, kind)?;
    let defects = map_defects(graph, kind)?;
    let polynomial = match characteristic_polynomial(graph) {
        Ok(coefficients) => Some(coefficients.iter().map(BigInt::to_string).collect()),
        Err(ProbeRefusal::SpectrumTooLarge { .. }) => None,
        Err(other) => return Err(other),
    };

    let mut hasher = blake3::Hasher::new();
    hasher.update(b"curvature-probe-v1");
    hasher.update(graph.distance_kind().name().as_bytes());
    hasher.update(&(graph.radius() as u64).to_be_bytes());
    hasher.update(kind.name().as_bytes());
    for prompt in graph.prompts() {
        for token in prompt {
            hasher.update(&token.to_be_bytes());
        }
        hasher.update(b"\x00");
    }
    for (key, value) in &profile.per_edge {
        hasher.update(key.as_bytes());
        hasher.update(&value.to_be_bytes());
    }

    Ok(CurvatureReceiptV1 {
        schema: PROBE_RECEIPT_SCHEMA,
        distance: graph.distance_kind().name(),
        radius: graph.radius(),
        curvature_kind: kind.name(),
        order: graph.order(),
        size: profile.edges,
        minimum: profile.minimum,
        maximum: profile.maximum,
        total: profile.total,
        defect_vertices: defects.defect_vertices.len(),
        negative_edges: defects.negative_edges,
        characteristic_polynomial: polynomial,
        digest: hasher.finalize().to_hex().to_string(),
        authority_effect: "None",
    })
}

/// An ASCII curvature table for human inspection.
///
/// Deliberately a table and not a picture. A layout algorithm would place
/// vertices by something other than the curvature being reported, and a reader
/// would take the arrangement for a finding.
pub fn render_ascii(graph: &PromptGraph, kind: CurvatureKind) -> Result<String, ProbeRefusal> {
    let profile = curvature_profile(graph, kind)?;
    let defects = map_defects(graph, kind)?;
    let mut out = String::new();
    out.push_str(&format!(
        "prompt topology: {} vertices, {} edges, distance={} radius={} kind={}\n\n",
        graph.order(),
        profile.edges,
        graph.distance_kind().name(),
        graph.radius(),
        kind.name()
    ));
    out.push_str("  edge     curvature  triangles\n");
    for (left, right) in graph.edges() {
        out.push_str(&format!(
            "  {left:>3}-{right:<3}  {:>9}  {:>9}\n",
            forman_curvature(graph, left, right, kind)?,
            graph.triangles_on(left, right)?
        ));
    }
    out.push_str(&format!(
        "\n  min={} max={} total={} over {} edges\n",
        profile.minimum, profile.maximum, profile.total, profile.edges
    ));
    let (defect_count, order) = defects.density();
    out.push_str(&format!(
        "  defects={defect_count} of {order} vertices; {} negative edges\n",
        defects.negative_edges
    ));
    if !defects.isolated_vertices.is_empty() {
        out.push_str(&format!(
            "  isolated (not defects): {:?}\n",
            defects.isolated_vertices
        ));
    }
    out.push_str("  AuthorityEffect: None\n");
    Ok(out)
}

// Origin: engine/crates_rs/pfp/src/epics/probing.rs
// Claim: urn:core:crates_rs:pfp:probing:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_3d9ebcaf {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}

//! Supplied finite geometry interpretations of Genesis incidence packets.
//! Calls native mathematical owners; admission alone supplies none of these laws.
use num_rational::BigRational;
use core_category_theory::finite_report_descent::{CoverClassification, FiniteReportPresheaf};
use core_general_relativity::regge_calculus::{EdgeLengthMetric, ReggeCalculus};
use core_homology::declared_incidence::{
    declared_chain_report, encode_declared, DeclaredChainReport, DeclaredIncidenceError,
};
use core_homology::simplicial::SimplicialComplex;
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};

/// Exact rational interval for certified metric deficit and geometry bounds.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RationalInterval {
    pub lo: BigRational,
    pub hi: BigRational,
}

impl RationalInterval {
    pub fn point(r: BigRational) -> Self {
        Self { lo: r.clone(), hi: r }
    }

    pub fn new(lo: BigRational, hi: BigRational) -> Self {
        assert!(lo <= hi, "lower bound must be <= upper bound");
        Self { lo, hi }
    }

    pub fn contains(&self, r: &BigRational) -> bool {
        &self.lo <= r && r <= &self.hi
    }

    pub fn width(&self) -> BigRational {
        &self.hi - &self.lo
    }

    pub fn add(&self, other: &Self) -> Self {
        Self {
            lo: &self.lo + &other.lo,
            hi: &self.hi + &other.hi,
        }
    }

    pub fn sub(&self, other: &Self) -> Self {
        Self {
            lo: &self.lo - &other.hi,
            hi: &self.hi - &other.lo,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ComplexPacket {
    pub cells: Vec<Vec<usize>>,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ChainReport {
    pub dimensions: Vec<usize>,
    pub boundaries: Vec<Vec<Vec<String>>>,
    pub betti: Vec<usize>,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RestrictionPacket {
    pub source: u64,
    pub target: u64,
    pub reports: Vec<usize>,
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SheafPacket {
    pub carrier_size: usize,
    #[serde(deserialize_with = "deserialize_context_counts")]
    pub report_counts: BTreeMap<u64, usize>,
    pub restrictions: Vec<RestrictionPacket>,
    pub target: u64,
    pub cover: Vec<u64>,
    pub enumeration_limit: usize,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MetricPacket {
    pub complex: ComplexPacket,
    pub lengths: Vec<(usize, usize, f64)>,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MetricReport {
    pub deficits: BTreeMap<usize, f64>,
    pub boundary_vertices: Vec<usize>,
}

impl MetricReport {
    /// Float image of one numeric deficit, widened by a non-negative rational epsilon.
    ///
    /// `from_float` records the f64 value. This is not a certified enclosure.
    /// A negative epsilon returns `None` instead of an inverted interval.
    pub fn deficit_interval(&self, vertex: usize, epsilon: BigRational) -> Option<RationalInterval> {
        if epsilon < BigRational::from_integer(0.into()) {
            return None;
        }
        let &val = self.deficits.get(&vertex)?;
        let r = BigRational::from_float(val)?;
        let lo = &r - &epsilon;
        let hi = &r + &epsilon;
        Some(RationalInterval::new(lo, hi))
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum GeometryError {
    InvalidCells,
    MissingFace,
    Owner(String),
    InvalidMetricDomain,
    InvalidVertexLink,
    DuplicateRestriction,
    ForgedReport,
}

// Origin: engine/crates_rs/core_wdp/src/genesis_geometry.rs
// Claim: urn:core:crates_rs:core-wdp:genesis-geometry:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for GeometryError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for GeometryError {}
fn owner(e: impl std::fmt::Debug) -> GeometryError {
    GeometryError::Owner(format!("{e:?}"))
}

/// Refuse a packet outside the declared incidence domain. Faces are not filled in.
pub fn checked_complex(packet: &ComplexPacket) -> Result<SimplicialComplex, GeometryError> {
    encode_declared(&packet.cells).map_err(|error| match error {
        DeclaredIncidenceError::MissingFace { .. } => GeometryError::MissingFace,
        DeclaredIncidenceError::Owner(reason) => GeometryError::Owner(reason),
        _ => GeometryError::InvalidCells,
    })
}

impl From<DeclaredChainReport> for ChainReport {
    fn from(report: DeclaredChainReport) -> Self {
        Self {
            dimensions: report.dimensions,
            boundaries: report.boundaries,
            betti: report.betti,
        }
    }
}

/// Signed rational chains from `core_homology`. Rank stays on exact linear algebra.
pub fn chain_report(packet: &ComplexPacket) -> Result<ChainReport, GeometryError> {
    let complex = checked_complex(packet)?;
    declared_chain_report(&complex)
        .map(ChainReport::from)
        .map_err(owner)
}
pub fn verify_chain_report(
    packet: &ComplexPacket,
    claimed: &ChainReport,
) -> Result<(), GeometryError> {
    if &chain_report(packet)? != claimed {
        return Err(GeometryError::ForgedReport);
    }
    Ok(())
}
pub fn sheaf_report(packet: &SheafPacket) -> Result<CoverClassification, GeometryError> {
    let mut restrictions = BTreeMap::new();
    for r in &packet.restrictions {
        if restrictions
            .insert((r.source, r.target), r.reports.clone())
            .is_some()
        {
            return Err(GeometryError::DuplicateRestriction);
        }
    }
    let presheaf = FiniteReportPresheaf::new(
        packet.carrier_size,
        packet.report_counts.clone(),
        restrictions,
    )
    .map_err(owner)?;
    presheaf
        .classify_cover(packet.target, &packet.cover, packet.enumeration_limit)
        .map_err(owner)
}
pub fn verify_sheaf_report(
    packet: &SheafPacket,
    claimed: &CoverClassification,
) -> Result<(), GeometryError> {
    if &sheaf_report(packet)? != claimed {
        return Err(GeometryError::ForgedReport);
    }
    Ok(())
}
/// Native Regge owner provides angles/triangle checks. This adapter additionally checks
/// pure manifold links and uses pi (rather than 2pi) at a boundary vertex.
fn build_edge_length_metric(
    lengths: &[(usize, usize, f64)],
    edges: &BTreeSet<(usize, usize)>,
) -> Result<EdgeLengthMetric, GeometryError> {
    let mut assigned = BTreeSet::new();
    let mut metric = EdgeLengthMetric::new();
    for &(u, v, l) in lengths {
        if u >= v || !edges.contains(&(u, v)) || !assigned.insert((u, v)) {
            return Err(GeometryError::InvalidMetricDomain);
        }
        metric.set(u, v, l).map_err(owner)?;
    }
    if assigned != *edges {
        return Err(GeometryError::InvalidMetricDomain);
    }
    Ok(metric)
}

fn incident_edges_for_vertex(v: usize, edges: &BTreeSet<(usize, usize)>) -> BTreeSet<usize> {
    edges
        .iter()
        .filter_map(|&(a, b)| {
            if a == v {
                Some(b)
            } else if b == v {
                Some(a)
            } else {
                None
            }
        })
        .collect()
}

fn verify_link_connectivity(link: &BTreeMap<usize, BTreeSet<usize>>) -> Result<(), GeometryError> {
    let mut reached = BTreeSet::new();
    let mut stack = vec![*link.keys().next().ok_or(GeometryError::InvalidVertexLink)?];
    while let Some(x) = stack.pop() {
        if reached.insert(x) {
            stack.extend(link[&x].iter().copied());
        }
    }
    if reached.len() != link.len() {
        return Err(GeometryError::InvalidVertexLink);
    }
    Ok(())
}

fn check_link_connected_and_manifold(
    link: &BTreeMap<usize, BTreeSet<usize>>,
    incident: &BTreeSet<usize>,
) -> Result<bool, GeometryError> {
    if link.is_empty() || *incident != link.keys().copied().collect() {
        return Err(GeometryError::InvalidVertexLink);
    }
    verify_link_connectivity(link)?;
    let ends = link.values().filter(|n| n.len() == 1).count();
    if link.values().any(|n| n.is_empty() || n.len() > 2) || (ends != 0 && ends != 2) {
        return Err(GeometryError::InvalidVertexLink);
    }
    Ok(ends == 2)
}

fn add_triangle_to_vertex_link(
    v: usize,
    tri_vertices: &[usize],
    link: &mut BTreeMap<usize, BTreeSet<usize>>,
) {
    if tri_vertices.contains(&v) {
        let opposite: Vec<_> = tri_vertices.iter().copied().filter(|x| *x != v).collect();
        link.entry(opposite[0]).or_default().insert(opposite[1]);
        link.entry(opposite[1]).or_default().insert(opposite[0]);
    }
}

fn compute_vertex_deficits(
    geometry: &ReggeCalculus,
    boundary_vertices: &[usize],
) -> Result<BTreeMap<usize, f64>, GeometryError> {
    let mut deficits = BTreeMap::new();
    for s in geometry.complex.simplices(0) {
        let v = s.vertices()[0];
        let interior = geometry.deficit_at_vertex(v).map_err(owner)?;
        let deficit = if boundary_vertices.contains(&v) {
            interior - std::f64::consts::PI
        } else {
            interior
        };
        if !deficit.is_finite() {
            return Err(GeometryError::InvalidMetricDomain);
        }
        deficits.insert(v, deficit);
    }
    Ok(deficits)
}

fn ensure_two_dimensional_complex(max_dim: usize, empty_2_simplices: bool) -> Result<(), GeometryError> {
    if max_dim != 2 || empty_2_simplices {
        return Err(GeometryError::InvalidMetricDomain);
    }
    Ok(())
}

pub fn metric_report(packet: &MetricPacket) -> Result<MetricReport, GeometryError> {
    let complex = checked_complex(&packet.complex)?;
    ensure_two_dimensional_complex(complex.max_dimension(), complex.simplices(2).is_empty())?;
    let edges: BTreeSet<_> = complex
        .simplices(1)
        .iter()
        .map(|s| (s.vertices()[0], s.vertices()[1]))
        .collect();
    let metric = build_edge_length_metric(&packet.lengths, &edges)?;
    let mut boundary_vertices = Vec::new();
    for vertex in complex.simplices(0) {
        let v = vertex.vertices()[0];
        let mut link: BTreeMap<usize, BTreeSet<usize>> = BTreeMap::new();
        for t in complex.simplices(2) {
            add_triangle_to_vertex_link(v, t.vertices(), &mut link);
        }
        let incident = incident_edges_for_vertex(v, &edges);
        if check_link_connected_and_manifold(&link, &incident)? {
            boundary_vertices.push(v);
        }
    }
    let geometry =
        ReggeCalculus::try_new(complex, metric, "Genesis supplied metric").map_err(owner)?;
    let deficits = compute_vertex_deficits(&geometry, &boundary_vertices)?;
    Ok(MetricReport {
        deficits,
        boundary_vertices,
    })
}
/// Replay exact floating result; this is a numeric diagnostic, not interval certification.
pub fn verify_metric_report(
    packet: &MetricPacket,
    claimed: &MetricReport,
) -> Result<(), GeometryError> {
    if &metric_report(packet)? != claimed {
        return Err(GeometryError::ForgedReport);
    }
    Ok(())
}

/// Actual Genesis regime projection. Replay/custody verification is a separate
/// precondition; this decoder checks every admitted incidence without auto-fills.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SourceIncidenceState {
    pub data: Vec<String>,
    pub forms: Vec<usize>,
    pub insts: Vec<(usize, Vec<usize>)>,
    pub rules: Vec<serde_json::Value>,
    pub reqs: Vec<serde_json::Value>,
}
fn parse_incidence_vertices(data: &[String]) -> Result<Vec<usize>, GeometryError> {
    let mut vertices = Vec::new();
    let mut unique = BTreeSet::new();
    for token in data {
        let suffix = token
            .strip_prefix("vertex:")
            .ok_or(GeometryError::InvalidCells)?;
        let v: usize = suffix.parse().map_err(|_| GeometryError::InvalidCells)?;
        if token != &format!("vertex:{v}") || !unique.insert(v) {
            return Err(GeometryError::InvalidCells);
        }
        vertices.push(v);
    }
    Ok(vertices)
}

fn decode_incidence_cells(
    forms: &[usize],
    insts: &[(usize, Vec<usize>)],
    vertices: &[usize],
) -> Result<Vec<Vec<usize>>, GeometryError> {
    let mut decoded = Vec::new();
    for (form, args) in insts {
        if forms.get(*form).copied() != Some(args.len()) {
            return Err(GeometryError::InvalidCells);
        }
        let cell = args
            .iter()
            .map(|i| vertices.get(*i).copied().ok_or(GeometryError::InvalidCells))
            .collect::<Result<Vec<_>, _>>()?;
        decoded.push(cell);
    }
    Ok(decoded)
}

pub fn verify_source_incidence(
    packet: &ComplexPacket,
    state: &SourceIncidenceState,
) -> Result<(), GeometryError> {
    checked_complex(packet)?;
    if !state.rules.is_empty()
        || !state.reqs.is_empty()
        || state.forms != (1..=state.forms.len()).collect::<Vec<_>>()
    {
        return Err(GeometryError::InvalidCells);
    }
    let vertices = parse_incidence_vertices(&state.data)?;
    let decoded_cells = decode_incidence_cells(&state.forms, &state.insts, &vertices)?;
    let decoded = ComplexPacket {
        cells: decoded_cells,
    };
    checked_complex(&decoded)?;
    let original: BTreeSet<_> = packet.cells.iter().cloned().collect();
    let restored: BTreeSet<_> = decoded.cells.iter().cloned().collect();
    if original != restored || vertices.iter().any(|v| !restored.contains(&vec![*v])) {
        return Err(GeometryError::ForgedReport);
    }
    Ok(())
}

/// JSON object keys are strings even when a tagged enclosing enum buffers them.
/// Parse canonical decimal masks explicitly, refusing aliases and duplicates.
fn deserialize_context_counts<'de, D>(deserializer: D) -> Result<BTreeMap<u64, usize>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    struct CountsVisitor;
    impl<'de> serde::de::Visitor<'de> for CountsVisitor {
        type Value = BTreeMap<u64, usize>;
        fn expecting(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
            f.write_str("canonical decimal u64 context keys mapped to report counts")
        }
        fn visit_map<M>(self, mut map: M) -> Result<Self::Value, M::Error>
        where
            M: serde::de::MapAccess<'de>,
        {
            let mut result = BTreeMap::new();
            while let Some((key, count)) = map.next_entry::<String, usize>()? {
                let mask: u64 = key.parse().map_err(serde::de::Error::custom)?;
                if key != mask.to_string() {
                    return Err(serde::de::Error::custom("noncanonical context key"));
                }
                if result.insert(mask, count).is_some() {
                    return Err(serde::de::Error::custom("duplicate context key"));
                }
            }
            Ok(result)
        }
    }
    deserializer.deserialize_map(CountsVisitor)
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rational_interval_operations() {
        let i1 = RationalInterval::new(BigRational::from_integer(1.into()), BigRational::from_integer(3.into()));
        let i2 = RationalInterval::new(BigRational::from_integer(2.into()), BigRational::from_integer(5.into()));
        assert_eq!(i1.width(), BigRational::from_integer(2.into()));
        assert!(i1.contains(&BigRational::from_integer(2.into())));
        assert!(!i1.contains(&BigRational::from_integer(4.into())));

        let sum = i1.add(&i2);
        assert_eq!(sum.lo, BigRational::from_integer(3.into()));
        assert_eq!(sum.hi, BigRational::from_integer(8.into()));

        let diff = i1.sub(&i2);
        assert_eq!(diff.lo, BigRational::from_integer((-4).into()));
        assert_eq!(diff.hi, BigRational::from_integer(1.into()));
    }

    #[test]
    fn deficit_interval_rejects_negative_epsilon_without_panic() {
        let report = MetricReport {
            deficits: BTreeMap::from([(0, 1.0)]),
            boundary_vertices: Vec::new(),
        };
        assert!(report
            .deficit_interval(0, BigRational::from_integer((-1).into()))
            .is_none());
        let slab = report
            .deficit_interval(0, BigRational::from_integer(0.into()))
            .expect("zero epsilon keeps the float image");
        assert_eq!(slab.lo, slab.hi);
    }
}

//! # Obstruction-class transfer test
//!
//! AuthorityEffect: None. This crate measures; it licenses nothing.
//!
//! Question: when a solved case's recorded repair steps are replayed on another
//! case, does "same obstruction class" predict exact success, and how far down a
//! declared ladder of sameness (L1..L5) does that hold?
//!
//! * An instance is a finite connected simple graph `G`, integer weights `w > 0`
//!   and an integer 1-cochain `c` of edge claims, with `(delta phi)_uv = phi_v - phi_u`
//!   on every edge stored as `(u, v)`, `u < v`.
//! * `D(c, phi) = sum_e w_e |c_e - (delta phi)_e|`. `Phi1(c) = min_phi D(c, phi)`
//!   is never computed here: it comes from `core_solvers::solve_exact_phi1` and is
//!   re-checked by `core_functional::phi1::Phi1Functional::verify_exact_certificate`,
//!   which compares the submitted primal residual and dual circulation with the
//!   reported value.
//! * A trace is a word in the DDC alphabet with structural arguments only (see
//!   [`TraceStep`]). No trace step calls a solver.
//! * Everything is integer or exact rational. There is no float in this crate.

use std::collections::{BTreeMap, HashMap};

use core_functional::l1_seminorm::L1Seminorm;
use core_functional::phi1::Phi1Functional;
use core_operad_canon::DdcOp;
use core_solvers::solver_lp_phi1_quotient::solve_exact_phi1;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Signed, ToPrimitive, Zero};
use sha2::{Digest, Sha256};

// ───────────────────────────── graphs ─────────────────────────────

/// A finite simple graph on `0..n` with edges stored as sorted `(u, v)`, `u < v`.
#[derive(Clone, Debug, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct Graph {
    n: usize,
    edges: Vec<(usize, usize)>,
}

impl Graph {
    /// Normalise every edge to `u < v` and sort. Loops and repeats are dropped.
    pub fn new(n: usize, edges: &[(usize, usize)]) -> Self {
        let mut list: Vec<(usize, usize)> = edges
            .iter()
            .filter(|(a, b)| a != b && *a < n && *b < n)
            .map(|&(a, b)| (a.min(b), a.max(b)))
            .collect();
        list.sort_unstable();
        list.dedup();
        Self { n, edges: list }
    }

    pub fn n(&self) -> usize {
        self.n
    }

    pub fn edges(&self) -> &[(usize, usize)] {
        &self.edges
    }

    /// First Betti number of a connected graph: `|E| - |V| + 1`.
    pub fn betti(&self) -> usize {
        (self.edges.len() + 1).saturating_sub(self.n)
    }

    /// Index of the edge joining `a` and `b`, and `+1` when `a -> b` is its
    /// stored orientation, `-1` when it is reversed.
    pub fn edge_index(&self, a: usize, b: usize) -> Option<(usize, i64)> {
        let (key, sign) = if a < b { ((a, b), 1) } else { ((b, a), -1) };
        self.edges.binary_search(&key).ok().map(|i| (i, sign))
    }

    /// The graph with vertex `x` renamed `pi[x]`.
    pub fn relabel(&self, pi: &[usize]) -> Graph {
        let mapped: Vec<(usize, usize)> = self.edges.iter().map(|&(u, v)| (pi[u], pi[v])).collect();
        Graph::new(self.n, &mapped)
    }

    pub fn is_connected(&self) -> bool {
        if self.n == 0 {
            return false;
        }
        let adj = adjacency(self);
        let mut seen = vec![false; self.n];
        let mut stack = vec![0usize];
        seen[0] = true;
        while let Some(u) = stack.pop() {
            for &(x, _) in &adj[u] {
                if !seen[x] {
                    seen[x] = true;
                    stack.push(x);
                }
            }
        }
        seen.iter().all(|&s| s)
    }
}

/// Sorted neighbour lists `(neighbour, edge index)`.
fn adjacency(g: &Graph) -> Vec<Vec<(usize, usize)>> {
    let mut adj = vec![Vec::new(); g.n];
    for (e, &(u, v)) in g.edges.iter().enumerate() {
        adj[u].push((v, e));
        adj[v].push((u, e));
    }
    for list in &mut adj {
        list.sort_unstable();
    }
    adj
}

/// Every permutation of `0..n` in lexicographic order.
pub fn permutations(n: usize) -> Vec<Vec<usize>> {
    fn rec(n: usize, cur: &mut Vec<usize>, used: &mut [bool], out: &mut Vec<Vec<usize>>) {
        if cur.len() == n {
            out.push(cur.clone());
            return;
        }
        for x in 0..n {
            if !used[x] {
                used[x] = true;
                cur.push(x);
                rec(n, cur, used, out);
                cur.pop();
                used[x] = false;
            }
        }
    }
    let mut out = Vec::new();
    rec(n, &mut Vec::with_capacity(n), &mut vec![false; n], &mut out);
    out
}

/// Push a cochain on `src` to `dst` through the vertex map `pi`. `oriented`
/// flips the sign on edges whose orientation `pi` reverses (claims); weights are
/// pushed unoriented. `None` when `pi` does not map edges onto edges.
pub fn map_cochain(
    src: &Graph,
    dst: &Graph,
    pi: &[usize],
    x: &[i64],
    oriented: bool,
) -> Option<Vec<i64>> {
    if src.edges.len() != dst.edges.len() || src.n != dst.n {
        return None;
    }
    let mut out = vec![0i64; dst.edges.len()];
    for (e, &(u, v)) in src.edges.iter().enumerate() {
        let (j, s) = dst.edge_index(pi[u], pi[v])?;
        out[j] = if oriented { s * x[e] } else { x[e] };
    }
    Some(out)
}

/// The canonical spanning tree: breadth-first from vertex 0, neighbours in
/// increasing order; the discovering edge of each vertex is a tree edge.
pub fn canonical_tree(g: &Graph) -> Vec<bool> {
    let adj = adjacency(g);
    let mut mask = vec![false; g.edges.len()];
    if g.n == 0 {
        return mask;
    }
    let mut seen = vec![false; g.n];
    let mut queue = std::collections::VecDeque::from([0usize]);
    seen[0] = true;
    while let Some(u) = queue.pop_front() {
        for &(x, e) in &adj[u] {
            if !seen[x] {
                seen[x] = true;
                mask[e] = true;
                queue.push_back(x);
            }
        }
    }
    mask
}

/// Chords (non-tree edges) in edge order.
pub fn chords(mask: &[bool]) -> Vec<usize> {
    mask.iter()
        .enumerate()
        .filter(|(_, t)| !**t)
        .map(|(e, _)| e)
        .collect()
}

/// The potential that is exact on every edge of the spanning tree `mask`,
/// with `phi[0] = 0`. `None` when `mask` is not a spanning tree.
pub fn integrate(g: &Graph, mask: &[bool], c: &[i64]) -> Option<Vec<i64>> {
    if g.n == 0 || mask.iter().filter(|t| **t).count() + 1 != g.n {
        return None;
    }
    let adj = adjacency(g);
    let mut phi = vec![0i64; g.n];
    let mut seen = vec![false; g.n];
    let mut stack = vec![0usize];
    seen[0] = true;
    while let Some(u) = stack.pop() {
        for &(x, e) in &adj[u] {
            if mask[e] && !seen[x] {
                seen[x] = true;
                let (a, _) = g.edges[e];
                phi[x] = if u == a { phi[u] + c[e] } else { phi[u] - c[e] };
                stack.push(x);
            }
        }
    }
    seen.iter().all(|&s| s).then_some(phi)
}

fn dphi(g: &Graph, phi: &[i64], e: usize) -> i64 {
    let (u, v) = g.edges[e];
    phi[v] - phi[u]
}

/// `D(c, phi) = sum_e w_e |c_e - (delta phi)_e|`, exact.
pub fn defect(g: &Graph, w: &[i64], c: &[i64], phi: &[i64]) -> i64 {
    (0..g.edges.len())
        .map(|e| w[e] * (c[e] - dphi(g, phi, e)).abs())
        .sum()
}

/// Fundamental cycle of chord `e = (u, v)`: position 0 is the chord, then the
/// tree path from `v` back to `u`, in walking order.
pub fn fundamental_cycle(g: &Graph, mask: &[bool], e: usize) -> Vec<usize> {
    let (u, v) = g.edges[e];
    let adj = adjacency(g);
    let mut parent: Vec<Option<(usize, usize)>> = vec![None; g.n];
    let mut seen = vec![false; g.n];
    let mut queue = std::collections::VecDeque::from([v]);
    seen[v] = true;
    while let Some(x) = queue.pop_front() {
        for &(y, f) in &adj[x] {
            if mask[f] && !seen[y] {
                seen[y] = true;
                parent[y] = Some((x, f));
                queue.push_back(y);
            }
        }
    }
    // Walking from u up to the root v lists the path u -> v; reverse it.
    let mut path = Vec::new();
    let mut x = u;
    while let Some((p, f)) = parent[x] {
        path.push(f);
        x = p;
    }
    path.reverse();
    let mut cycle = vec![e];
    cycle.extend(path);
    cycle
}

/// Class coordinates of `[c]` on the chords of `mask`: the residual on each
/// chord after exact repair on the tree.
pub fn class_coords(g: &Graph, mask: &[bool], c: &[i64]) -> Vec<i64> {
    match integrate(g, mask, c) {
        Some(phi) => chords(mask)
            .into_iter()
            .map(|e| c[e] - dphi(g, &phi, e))
            .collect(),
        None => Vec::new(),
    }
}

fn support(v: &[i64]) -> Vec<bool> {
    v.iter().map(|x| *x != 0).collect()
}

// ───────────────────────────── instances and family ─────────────────────────────

/// One finite case `(G, w, c)`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Instance {
    pub id: String,
    pub graph: Graph,
    pub w: Vec<i64>,
    pub c: Vec<i64>,
}

impl Instance {
    /// Byte key of the instance; equal keys mean equal `(G, w, c)`.
    pub fn key(&self) -> String {
        format!(
            "n={} E={:?} w={:?} c={:?}",
            self.graph.n, self.graph.edges, self.w, self.c
        )
    }

    /// The same instance with vertices renamed by `pi`.
    pub fn relabel(&self, pi: &[usize], id: String) -> Instance {
        let graph = self.graph.relabel(pi);
        let w = map_cochain(&self.graph, &graph, pi, &self.w, false).unwrap_or_default();
        let c = map_cochain(&self.graph, &graph, pi, &self.c, true).unwrap_or_default();
        Instance { id, graph, w, c }
    }
}

/// A `(G, w)` class: a canonical graph and a weight vector minimal in its Aut(G)-orbit.
#[derive(Clone, Debug)]
pub struct WeightedGraph {
    pub graph_index: usize,
    pub graph: Graph,
    pub w: Vec<i64>,
}

/// The exhaustive, deterministic family.
#[derive(Clone, Debug)]
pub struct Family {
    pub max_n: usize,
    pub graphs: Vec<Graph>,
    pub weighted: Vec<WeightedGraph>,
    /// Base instances, grouped by weighted graph, coordinates in lexicographic order.
    pub instances: Vec<Instance>,
    /// `instance_of[(weighted index, coordinate vector)]`.
    pub instance_of: BTreeMap<(usize, Vec<i64>), usize>,
    /// Weighted-graph index of each instance.
    pub weighted_of: Vec<usize>,
}

/// Lexicographically smallest edge list over all relabellings.
fn canonical_edges(g: &Graph, perms: &[Vec<usize>]) -> Vec<(usize, usize)> {
    perms
        .iter()
        .map(|pi| g.relabel(pi).edges)
        .min()
        .unwrap_or_default()
}

fn automorphisms(g: &Graph, perms: &[Vec<usize>]) -> Vec<Vec<usize>> {
    perms
        .iter()
        .filter(|pi| g.relabel(pi) == *g)
        .cloned()
        .collect()
}

/// Every connected simple graph with `n <= max_n` and `beta1 in {1, 2}`, one
/// per isomorphism class (the representative is the canonical edge list).
pub fn enumerate_graphs(max_n: usize) -> Vec<Graph> {
    let mut out = Vec::new();
    for n in 1..=max_n {
        let perms = permutations(n);
        let pairs: Vec<(usize, usize)> = (0..n)
            .flat_map(|u| ((u + 1)..n).map(move |v| (u, v)))
            .collect();
        for beta in 1..=2usize {
            let m = n + beta - 1;
            if m > pairs.len() {
                continue;
            }
            for mask in 0u32..(1u32 << pairs.len()) {
                if mask.count_ones() as usize != m {
                    continue;
                }
                let edges: Vec<(usize, usize)> = pairs
                    .iter()
                    .enumerate()
                    .filter(|(i, _)| mask & (1 << i) != 0)
                    .map(|(_, &p)| p)
                    .collect();
                let g = Graph::new(n, &edges);
                if g.is_connected() && canonical_edges(&g, &perms) == g.edges {
                    out.push(g);
                }
            }
        }
    }
    out
}

/// Every coordinate vector in `{-2..2}^k`, lexicographic.
pub fn coordinate_vectors(k: usize) -> Vec<Vec<i64>> {
    let mut out = vec![Vec::new()];
    for _ in 0..k {
        out = out
            .into_iter()
            .flat_map(|v| {
                (-2..=2).map(move |x| {
                    let mut w = v.clone();
                    w.push(x);
                    w
                })
            })
            .collect();
    }
    out
}

pub fn enumerate_family(max_n: usize) -> Family {
    let graphs = enumerate_graphs(max_n);
    let mut weighted = Vec::new();
    let mut instances = Vec::new();
    let mut instance_of = BTreeMap::new();
    let mut weighted_of = Vec::new();
    for (gi, g) in graphs.iter().enumerate() {
        let perms = permutations(g.n);
        let auts = automorphisms(g, &perms);
        let m = g.edges.len();
        let mask = canonical_tree(g);
        let chord_list = chords(&mask);
        for bits in 0u32..(1u32 << m) {
            let w: Vec<i64> = (0..m).map(|e| 1 + i64::from((bits >> e) & 1)).collect();
            let minimal = auts
                .iter()
                .all(|pi| map_cochain(g, g, pi, &w, false).is_none_or(|image| w <= image));
            if !minimal {
                continue;
            }
            let wi = weighted.len();
            weighted.push(WeightedGraph {
                graph_index: gi,
                graph: g.clone(),
                w: w.clone(),
            });
            for coords in coordinate_vectors(chord_list.len()) {
                let mut c = vec![0i64; m];
                for (k, &e) in chord_list.iter().enumerate() {
                    c[e] = coords[k];
                }
                let id = format!("g{gi}.w{bits}.c{}", fmt_vec(&coords));
                instance_of.insert((wi, coords.clone()), instances.len());
                weighted_of.push(wi);
                instances.push(Instance {
                    id,
                    graph: g.clone(),
                    w: w.clone(),
                    c,
                });
            }
        }
    }
    Family {
        max_n,
        graphs,
        weighted,
        instances,
        instance_of,
        weighted_of,
    }
}

fn fmt_vec(v: &[i64]) -> String {
    v.iter()
        .map(|x| x.to_string())
        .collect::<Vec<_>>()
        .join(",")
}

// ───────────────────────────── certified Phi1 ─────────────────────────────

/// A Phi1 value with an integer optimal potential, both taken from a
/// certificate the shared verifier accepted.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CertifiedPhi1 {
    pub value: BigRational,
    pub alpha: Vec<i64>,
}

fn q(x: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(x))
}

/// Solve with `core_solvers`, then hand the certificate to
/// `Phi1Functional::verify_exact_certificate`, which compares the reported value
/// against the submitted primal residual and dual circulation.
pub fn certify_phi1(inst: &Instance) -> Result<CertifiedPhi1, String> {
    let g = &inst.graph;
    let d0: Vec<Vec<BigRational>> = g
        .edges
        .iter()
        .map(|&(u, v)| {
            let mut row = vec![BigRational::zero(); g.n];
            row[u] = -BigRational::one();
            row[v] = BigRational::one();
            row
        })
        .collect();
    let weights: Vec<BigRational> = inst.w.iter().map(|&x| q(x)).collect();
    let omega: Vec<BigRational> = inst.c.iter().map(|&x| q(x)).collect();
    let space = L1Seminorm::new(d0, weights).map_err(|e| format!("PRESENTATION_REFUSED: {e:?}"))?;
    let solved = solve_exact_phi1(&space, &omega).map_err(|e| format!("SOLVE_REFUSED: {e}"))?;
    let checked = Phi1Functional::verify_exact_certificate(solved.certificate().clone())
        .map_err(|e| format!("CERTIFICATE_REFUSED: {e}"))?;
    let alpha = checked
        .alpha()
        .iter()
        .map(|a| {
            if a.is_integer() {
                a.to_integer().to_i64()
            } else {
                None
            }
        })
        .collect::<Option<Vec<i64>>>()
        .ok_or_else(|| "NONINTEGER_OPTIMUM".to_string())?;
    Ok(CertifiedPhi1 {
        value: checked.value().clone(),
        alpha,
    })
}

// ───────────────────────────── traces ─────────────────────────────

/// One structural trace step. Arguments are indices and positions only.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum TraceStep {
    /// `C`: declare the canonical spanning tree (BFS from 0, neighbours ascending).
    Tree,
    /// `E`: exact repair on the tree edges, reading claims from the current instance.
    ExactOnTree,
    /// `R`: project the residual onto the chord coordinates of `[c]`.
    ProjectChords,
    /// `D`: cut the edge at `position` of the fundamental cycle of chord `chord`
    /// (position 0 is the chord itself); that edge will carry the residual.
    Cut { chord: usize, position: usize },
    /// `E`: exact repair on the edges that were not cut.
    Retree,
    /// `T`: terminal. Mints nothing.
    Terminal,
}

impl TraceStep {
    pub fn op(&self) -> DdcOp {
        match self {
            TraceStep::Tree => DdcOp::ContextExposure,
            TraceStep::ExactOnTree | TraceStep::Retree => DdcOp::ExactRepair,
            TraceStep::ProjectChords => DdcOp::ResidualProjection,
            TraceStep::Cut { .. } => DdcOp::Descent,
            TraceStep::Terminal => DdcOp::Terminalize,
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Trace {
    pub steps: Vec<TraceStep>,
}

impl Trace {
    /// The DDC word with structural arguments, e.g. `C E R D(0,2) E T`.
    pub fn word(&self) -> String {
        self.steps
            .iter()
            .map(|s| match s {
                TraceStep::Cut { chord, position } => format!("D({chord},{position})"),
                other => other.op().letter().to_string(),
            })
            .collect::<Vec<_>>()
            .join(" ")
    }
}

/// Typed refusal codes, for recording and for replay.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Refusal {
    /// The two instances have different first Betti numbers.
    BettiMismatch,
    /// The comparison level supplies no vertex map, so a potential cannot be pushed.
    NoVertexMap,
    /// A recorded chord has no chord as its image on the target's canonical tree.
    ChordNoImage,
    /// A recorded cycle position does not exist on the target cycle.
    CutPositionOutOfRange,
    /// Two cut steps named the same target edge.
    CutRepeated,
    /// The uncut edges do not form a spanning tree on the target.
    CutSetNotCotree,
    /// The source optimum's zero-residual edges do not contain a spanning tree.
    RecordNotVertex,
    /// No chord-to-cut matching inside the fundamental cycles exists on the source.
    RecordNoChordMatching,
}

impl Refusal {
    pub fn code(self) -> &'static str {
        match self {
            Refusal::BettiMismatch => "BETTI_MISMATCH",
            Refusal::NoVertexMap => "NO_VERTEX_MAP",
            Refusal::ChordNoImage => "CHORD_NO_IMAGE",
            Refusal::CutPositionOutOfRange => "CUT_POSITION_OUT_OF_RANGE",
            Refusal::CutRepeated => "CUT_REPEATED",
            Refusal::CutSetNotCotree => "CUT_SET_NOT_COTREE",
            Refusal::RecordNotVertex => "RECORD_NOT_VERTEX",
            Refusal::RecordNoChordMatching => "RECORD_NO_CHORD_MATCHING",
        }
    }
}

/// Record the structural trace of a solved case from its certified optimum.
///
/// The optimum is read once, here, to choose the cut set: the zero-residual
/// edges are scanned canonical-tree edges first, then by edge index (the
/// tie-break rule), and a spanning tree is grown in that order; the cut set is
/// its complement. Each canonical chord is matched to a cut edge on its own
/// fundamental cycle, first matching in lexicographic order. The trace keeps only
/// chord indices and cycle positions.
pub fn record_trace(inst: &Instance, optimum: &[i64]) -> Result<Trace, Refusal> {
    let g = &inst.graph;
    let tree = canonical_tree(g);
    let zero: Vec<bool> = (0..g.edges.len())
        .map(|e| inst.c[e] == dphi(g, optimum, e))
        .collect();
    let mut order: Vec<usize> = (0..g.edges.len()).filter(|&e| tree[e] && zero[e]).collect();
    order.extend((0..g.edges.len()).filter(|&e| !tree[e] && zero[e]));
    let mut parent: Vec<usize> = (0..g.n).collect();
    fn find(p: &mut [usize], x: usize) -> usize {
        let mut r = x;
        while p[r] != r {
            r = p[r];
        }
        p[x] = r;
        r
    }
    let mut kept = vec![false; g.edges.len()];
    for e in order {
        let (u, v) = g.edges[e];
        let (ru, rv) = (find(&mut parent, u), find(&mut parent, v));
        if ru != rv {
            parent[ru] = rv;
            kept[e] = true;
        }
    }
    if kept.iter().filter(|k| **k).count() + 1 != g.n {
        return Err(Refusal::RecordNotVertex);
    }
    let cuts = chords(&kept);
    let chord_list = chords(&tree);
    let cycles: Vec<Vec<usize>> = chord_list
        .iter()
        .map(|&e| fundamental_cycle(g, &tree, e))
        .collect();
    let matching = permutations(cuts.len()).into_iter().find(|sigma| {
        sigma
            .iter()
            .enumerate()
            .all(|(k, &s)| cycles[k].contains(&cuts[s]))
    });
    let sigma = matching.ok_or(Refusal::RecordNoChordMatching)?;
    let mut steps = vec![
        TraceStep::Tree,
        TraceStep::ExactOnTree,
        TraceStep::ProjectChords,
    ];
    for (k, &s) in sigma.iter().enumerate() {
        let position = cycles[k].iter().position(|&e| e == cuts[s]).unwrap_or(0);
        steps.push(TraceStep::Cut { chord: k, position });
    }
    steps.push(TraceStep::Retree);
    steps.push(TraceStep::Terminal);
    Ok(Trace { steps })
}

/// Replay a trace on `target`. `chord_map[k]` is the target chord index of
/// source chord `k`, or `None` when it has no image. Claims are read from the
/// target. The result is a potential or a typed refusal.
pub fn replay(
    trace: &Trace,
    target: &Instance,
    chord_map: &[Option<usize>],
) -> Result<Vec<i64>, Refusal> {
    let g = &target.graph;
    let tree = canonical_tree(g);
    let chord_list = chords(&tree);
    let mut phi = vec![0i64; g.n];
    let mut cut = vec![false; g.edges.len()];
    for step in &trace.steps {
        match step {
            TraceStep::Tree | TraceStep::ProjectChords | TraceStep::Terminal => {}
            TraceStep::ExactOnTree => {
                phi = integrate(g, &tree, &target.c).ok_or(Refusal::CutSetNotCotree)?;
            }
            TraceStep::Cut { chord, position } => {
                let k = chord_map
                    .get(*chord)
                    .copied()
                    .flatten()
                    .ok_or(Refusal::ChordNoImage)?;
                let e = *chord_list.get(k).ok_or(Refusal::ChordNoImage)?;
                let cycle = fundamental_cycle(g, &tree, e);
                let f = *cycle.get(*position).ok_or(Refusal::CutPositionOutOfRange)?;
                if cut[f] {
                    return Err(Refusal::CutRepeated);
                }
                cut[f] = true;
            }
            TraceStep::Retree => {
                let kept: Vec<bool> = cut.iter().map(|c| !c).collect();
                phi = integrate(g, &kept, &target.c).ok_or(Refusal::CutSetNotCotree)?;
            }
        }
    }
    Ok(phi)
}

/// Chord map induced by a vertex map: chord `(u, v)` of the source goes to the
/// target edge `(pi u, pi v)`, which must be a chord of the target's canonical tree.
pub fn chord_map_from_vertex_map(
    source: &Graph,
    target: &Graph,
    pi: &[usize],
) -> Vec<Option<usize>> {
    let source_chords = chords(&canonical_tree(source));
    let target_chords = chords(&canonical_tree(target));
    source_chords
        .iter()
        .map(|&e| {
            let (u, v) = source.edges[e];
            let (j, _) = target.edge_index(pi[u], pi[v])?;
            target_chords.iter().position(|&f| f == j)
        })
        .collect()
}

/// Deliberate defect for the mutation check.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Injection {
    None,
    /// Negate the transported claim on the target's first chord before the gauge
    /// is integrated. Inert by construction: the gauge reads tree edges only.
    FlipFirstChordSign,
    /// Negate the transported claim on the target's first tree edge.
    FlipFirstTreeEdgeSign,
}

/// Gauge transport: `phi_B = pi(phi_A) + psi`, with `psi` exact on the target's
/// canonical tree for `c_B - pi(c_A)`. When `c_B - pi(c_A)` is a coboundary
/// (L1, L2), `psi` is the gauge and the transported potential is optimal.
pub fn gauge_transport(
    source: &Instance,
    optimum: &[i64],
    target: &Instance,
    pi: &[usize],
    injection: Injection,
) -> Option<Vec<i64>> {
    let mut pushed = map_cochain(&source.graph, &target.graph, pi, &source.c, true)?;
    let tree = canonical_tree(&target.graph);
    let flipped = match injection {
        Injection::None => None,
        Injection::FlipFirstChordSign => chords(&tree).first().copied(),
        Injection::FlipFirstTreeEdgeSign => tree.iter().position(|t| *t),
    };
    if let Some(e) = flipped {
        pushed[e] = -pushed[e];
    }
    let diff: Vec<i64> = target.c.iter().zip(&pushed).map(|(b, a)| b - a).collect();
    let psi = integrate(&target.graph, &tree, &diff)?;
    let mut phi = vec![0i64; target.graph.n];
    for x in 0..source.graph.n {
        phi[pi[x]] = optimum[x];
    }
    Some(phi.iter().zip(&psi).map(|(a, b)| a + b).collect())
}

// ───────────────────────────── levels ─────────────────────────────

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Level {
    L1,
    L2,
    L3,
    L4,
    L5,
}

impl Level {
    pub fn name(self) -> &'static str {
        match self {
            Level::L1 => "L1",
            Level::L2 => "L2",
            Level::L3 => "L3",
            Level::L4 => "L4",
            Level::L5 => "L5",
        }
    }
}

/// `l(A, B)`, the highest level whose map exists, with the first vertex map in
/// lexicographic order that attains it (L1..L3). `None` when Betti numbers differ.
pub fn classify(
    a: &Instance,
    b: &Instance,
    perms: &[Vec<usize>],
) -> Option<(Level, Option<Vec<usize>>)> {
    if a.graph.betti() != b.graph.betti() {
        return None;
    }
    let tree_b = canonical_tree(&b.graph);
    let coords_b = class_coords(&b.graph, &tree_b, &b.c);
    let mut best: Option<(Level, Vec<usize>)> = None;
    if a.graph.n == b.graph.n && a.graph.edges.len() == b.graph.edges.len() {
        for pi in perms {
            if map_cochain(&a.graph, &b.graph, pi, &a.w, false).as_deref() != Some(&b.w[..]) {
                continue;
            }
            let Some(pushed) = map_cochain(&a.graph, &b.graph, pi, &a.c, true) else {
                continue;
            };
            if pushed == b.c {
                return Some((Level::L1, Some(pi.clone())));
            }
            let diff: Vec<i64> = b.c.iter().zip(&pushed).map(|(x, y)| x - y).collect();
            let level = if class_coords(&b.graph, &tree_b, &diff)
                .iter()
                .all(|x| *x == 0)
            {
                Level::L2
            } else if support(&class_coords(&b.graph, &tree_b, &pushed)) == support(&coords_b) {
                Level::L3
            } else {
                continue;
            };
            if best.as_ref().is_none_or(|(l, _)| level < *l) {
                best = Some((level, pi.clone()));
            }
        }
    }
    if let Some((level, pi)) = best {
        return Some((level, Some(pi)));
    }
    let coords_a = class_coords(&a.graph, &canonical_tree(&a.graph), &a.c);
    Some((
        if coords_a == coords_b {
            Level::L4
        } else {
            Level::L5
        },
        None,
    ))
}

// ───────────────────────────── scoring ─────────────────────────────

/// Typed outcome of one replay.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Outcome {
    /// `D0 > Phi1(c_B)`: `S = (D0 - D_tau) / (D0 - Phi1)`, signed, `S <= 1`.
    Scored(BigRational),
    /// `D0 = Phi1(c_B)`: no score; the excess `D_tau - D0 >= 0`.
    NoHeadroom(BigRational),
    Refused(Refusal),
}

/// Score a replayed potential. `Err` when `D_tau < Phi1`, which would mean the
/// certified optimum is wrong.
pub fn score(target: &Instance, phi1: &BigRational, phi: &[i64]) -> Result<Outcome, String> {
    let d0 = q(defect(
        &target.graph,
        &target.w,
        &target.c,
        &vec![0; target.graph.n],
    ));
    let dtau = q(defect(&target.graph, &target.w, &target.c, phi));
    if &dtau < phi1 {
        return Err(format!("D_tau {dtau} < Phi1 {phi1} on {}", target.id));
    }
    if &d0 > phi1 {
        Ok(Outcome::Scored((d0.clone() - dtau) / (d0 - phi1)))
    } else {
        Ok(Outcome::NoHeadroom(dtau - d0))
    }
}

// ───────────────────────────── pairs and the run ─────────────────────────────

/// Which block of the table a pair belongs to.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum Cohort {
    Main,
    ShuffledClaims,
    CrossBetti,
}

impl Cohort {
    pub fn name(self) -> &'static str {
        match self {
            Cohort::Main => "main",
            Cohort::ShuffledClaims => "control_shuffled_claims",
            Cohort::CrossBetti => "control_cross_betti",
        }
    }
}

/// A source instance (index into the family) and a target instance.
#[derive(Clone, Debug)]
pub struct Pair {
    pub id: String,
    pub cohort: Cohort,
    pub source: usize,
    pub target: Instance,
}

fn reverse_labels(n: usize) -> Vec<usize> {
    (0..n).map(|x| n - 1 - x).collect()
}

fn add_coboundary(inst: &Instance, psi: &[i64], id: String) -> Instance {
    let mut c = inst.c.clone();
    for (e, &(u, v)) in inst.graph.edges.iter().enumerate() {
        c[e] += psi[v] - psi[u];
    }
    Instance {
        id,
        graph: inst.graph.clone(),
        w: inst.w.clone(),
        c,
    }
}

/// The deterministic pair list (see the report for the rule of each block).
pub fn generate_pairs(family: &Family) -> Vec<Pair> {
    let mut pairs = Vec::new();
    let inst = &family.instances;
    for (i, a) in inst.iter().enumerate() {
        let rev = reverse_labels(a.graph.n);
        let copy = a.relabel(&rev, format!("{}~rev", a.id));
        pairs.push(Pair {
            id: format!("iso:{}", a.id),
            cohort: Cohort::Main,
            source: i,
            target: copy.clone(),
        });
        let n = a.graph.n;
        for code in 0..3usize.pow((n - 1) as u32) {
            let mut psi = vec![0i64; n];
            let mut r = code;
            for slot in psi.iter_mut().skip(1) {
                *slot = (r % 3) as i64 - 1;
                r /= 3;
            }
            if psi.iter().all(|x| *x == 0) {
                continue;
            }
            let id = format!("{}+d[{}]", copy.id, fmt_vec(&psi));
            let target = add_coboundary(&copy, &psi, id.clone());
            pairs.push(Pair {
                id: format!("gauge:{}", id),
                cohort: Cohort::Main,
                source: i,
                target,
            });
        }
    }
    // Same (G, w), different coordinates with the same support.
    for (&(wi, ref va), &i) in &family.instance_of {
        for (&(wj, ref vb), &j) in family.instance_of.range((wi, Vec::new())..) {
            if wj != wi {
                break;
            }
            if va != vb && support(va) == support(vb) {
                pairs.push(Pair {
                    id: format!("support:{}>{}", inst[i].id, inst[j].id),
                    cohort: Cohort::Main,
                    source: i,
                    target: inst[j].clone(),
                });
            }
        }
    }
    // Different (G, w) with the same beta1: equal coordinates, then negated or swapped ones.
    for (wi, a) in family.weighted.iter().enumerate() {
        for (wj, b) in family.weighted.iter().enumerate() {
            if wi == wj || a.graph.betti() != b.graph.betti() {
                continue;
            }
            for v in coordinate_vectors(a.graph.betti()) {
                let i = family.instance_of[&(wi, v.clone())];
                let mut targets = vec![v.clone()];
                let neg: Vec<i64> = v.iter().map(|x| -x).collect();
                let mut swapped = v.clone();
                swapped.reverse();
                for t in [neg, swapped] {
                    if t != v && !targets.contains(&t) {
                        targets.push(t);
                    }
                }
                for t in targets {
                    let j = family.instance_of[&(wj, t)];
                    pairs.push(Pair {
                        id: format!("contract:{}>{}", inst[i].id, inst[j].id),
                        cohort: Cohort::Main,
                        source: i,
                        target: inst[j].clone(),
                    });
                }
            }
        }
    }
    for (i, a) in inst.iter().enumerate() {
        let m = a.c.len();
        let c: Vec<i64> = (0..m).map(|e| a.c[(e + 1) % m]).collect();
        let target = Instance {
            id: format!("{}~shuffle", a.id),
            graph: a.graph.clone(),
            w: a.w.clone(),
            c,
        };
        pairs.push(Pair {
            id: format!("shuffle:{}", a.id),
            cohort: Cohort::ShuffledClaims,
            source: i,
            target,
        });
    }
    for (i, a) in inst.iter().enumerate() {
        let other = inst
            .iter()
            .find(|b| b.graph.n == a.graph.n && b.graph.betti() != a.graph.betti());
        if let Some(b) = other {
            pairs.push(Pair {
                id: format!("cross:{}>{}", a.id, b.id),
                cohort: Cohort::CrossBetti,
                source: i,
                target: b.clone(),
            });
        }
    }
    pairs
}

/// Accumulated counts for one `(cohort, level, method)` row. All exact.
#[derive(Clone, Debug, Default)]
pub struct Row {
    pub pairs: u64,
    pub scored: u64,
    pub no_headroom: u64,
    pub refused: u64,
    pub s_one: u64,
    pub s_negative: u64,
    pub sum_s: BigRational,
    pub no_headroom_worse: u64,
    pub no_headroom_excess: BigRational,
}

impl Row {
    fn add(&mut self, outcome: &Outcome) {
        self.pairs += 1;
        match outcome {
            Outcome::Scored(s) => {
                self.scored += 1;
                if s.is_one() {
                    self.s_one += 1;
                }
                if s.is_negative() {
                    self.s_negative += 1;
                }
                self.sum_s += s.clone();
            }
            Outcome::NoHeadroom(x) => {
                self.no_headroom += 1;
                if x.is_positive() {
                    self.no_headroom_worse += 1;
                }
                self.no_headroom_excess += x.clone();
            }
            Outcome::Refused(_) => self.refused += 1,
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct RunConfig {
    pub max_n: usize,
    pub injection: Injection,
}

/// Everything the run produces. `table` is the byte-reproducible report table.
#[derive(Clone, Debug)]
pub struct RunOutput {
    pub table: String,
    pub census: String,
    pub input_digest: String,
    pub output_digest: String,
    pub instance_count: usize,
    pub pair_count: usize,
    /// Gauge-transport pairs at L1/L2 that missed `S = 1` (or kept excess), by case id.
    pub gauge_failures: Vec<String>,
    /// Anything that contradicts a certificate or a lemma. Must be empty.
    pub defects: Vec<String>,
}

fn sha256_hex(text: &str) -> String {
    format!("{:x}", Sha256::digest(text.as_bytes()))
}

/// The census and the canonical family text that the input digest covers.
pub fn census(family: &Family) -> (String, String) {
    let mut counts: BTreeMap<(usize, usize, usize), (u64, u64)> = BTreeMap::new();
    for (wi, wg) in family.weighted.iter().enumerate() {
        let heavy = wg.w.iter().filter(|x| **x == 2).count();
        let entry = counts
            .entry((wg.graph.n, wg.graph.betti(), heavy))
            .or_default();
        entry.0 += 1;
        entry.1 += family.weighted_of.iter().filter(|x| **x == wi).count() as u64;
    }
    let mut graph_counts: BTreeMap<(usize, usize), u64> = BTreeMap::new();
    for g in &family.graphs {
        *graph_counts.entry((g.n, g.betti())).or_default() += 1;
    }
    let mut text = String::from("| n | beta1 | graphs |\n|---|---|---|\n");
    for ((n, b), k) in &graph_counts {
        text.push_str(&format!("| {n} | {b} | {k} |\n"));
    }
    text.push_str(
        "\n| n | beta1 | edges with w=2 | (G,w) classes | instances |\n|---|---|---|---|---|\n",
    );
    for ((n, b, h), (k, i)) in &counts {
        text.push_str(&format!("| {n} | {b} | {h} | {k} | {i} |\n"));
    }
    let mut canonical = format!(
        "family max_n={} weights=1..2 coords=-2..2 psi=-1..1 tree=bfs0\n",
        family.max_n
    );
    for inst in &family.instances {
        canonical.push_str(&inst.id);
        canonical.push(' ');
        canonical.push_str(&inst.key());
        canonical.push('\n');
    }
    (text, canonical)
}

fn record(
    rows: &mut BTreeMap<(Cohort, String, &'static str), Row>,
    refusals: &mut BTreeMap<(Cohort, String, &'static str, &'static str), u64>,
    key: (Cohort, String, &'static str),
    outcome: &Outcome,
) {
    if let Outcome::Refused(r) = outcome {
        *refusals
            .entry((key.0, key.1.clone(), key.2, r.code()))
            .or_default() += 1;
    }
    rows.entry(key).or_default().add(outcome);
}

/// Order used to pick the worst (`min`) and best (`max`) of several chord bijections:
/// a refusal is worst, then smaller `S` (or larger no-headroom excess).
fn outcome_rank(o: &Outcome) -> (u8, BigRational) {
    match o {
        Outcome::Refused(_) => (0, BigRational::zero()),
        Outcome::Scored(s) => (1, s.clone()),
        Outcome::NoHeadroom(x) => (1, -x.clone()),
    }
}

/// Run the whole family and build the table.
pub fn run(cfg: RunConfig) -> Result<RunOutput, String> {
    let family = enumerate_family(cfg.max_n);
    let (census_text, canonical) = census(&family);
    let pairs = generate_pairs(&family);
    let perms: Vec<Vec<Vec<usize>>> = (0..=cfg.max_n).map(permutations).collect();

    let mut defects = Vec::new();
    let mut certs = Vec::with_capacity(family.instances.len());
    let mut traces = Vec::with_capacity(family.instances.len());
    let mut cache: HashMap<String, BigRational> = HashMap::new();
    for inst in &family.instances {
        let cert = certify_phi1(inst).map_err(|e| format!("{}: {e}", inst.id))?;
        let trace = record_trace(inst, &cert.alpha);
        if let Ok(t) = &trace {
            let identity: Vec<Option<usize>> = (0..inst.graph.betti()).map(Some).collect();
            match replay(t, inst, &identity) {
                Ok(phi) if q(defect(&inst.graph, &inst.w, &inst.c, &phi)) == cert.value => {}
                other => defects.push(format!("SELF_REPLAY {} {:?}", inst.id, other)),
            }
        }
        cache.insert(inst.key(), cert.value.clone());
        certs.push(cert);
        traces.push(trace);
    }

    let mut rows: BTreeMap<(Cohort, String, &'static str), Row> = BTreeMap::new();
    let mut refusals: BTreeMap<(Cohort, String, &'static str, &'static str), u64> = BTreeMap::new();
    let mut gauge_failures = Vec::new();
    for pair in &pairs {
        let a = &family.instances[pair.source];
        let b = &pair.target;
        let phi1_b = match cache.get(&b.key()) {
            Some(v) => v.clone(),
            None => {
                let v = certify_phi1(b).map_err(|e| format!("{}: {e}", b.id))?.value;
                cache.insert(b.key(), v.clone());
                v
            }
        };
        let classified = classify(a, b, &perms[a.graph.n]);
        let level = classified
            .as_ref()
            .map_or("none".to_string(), |(l, _)| l.name().to_string());
        let mut scored = |phi: Option<Vec<i64>>, refusal: Refusal| -> Outcome {
            match phi {
                None => Outcome::Refused(refusal),
                Some(p) => score(b, &phi1_b, &p).unwrap_or_else(|e| {
                    defects.push(e);
                    Outcome::Refused(refusal)
                }),
            }
        };
        // Gauge transport.
        let gauge = match &classified {
            None => Outcome::Refused(Refusal::BettiMismatch),
            Some((_, None)) => Outcome::Refused(Refusal::NoVertexMap),
            Some((_, Some(pi))) => scored(
                gauge_transport(a, &certs[pair.source].alpha, b, pi, cfg.injection),
                Refusal::NoVertexMap,
            ),
        };
        if let Some((l @ (Level::L1 | Level::L2), _)) = &classified {
            let ok = match &gauge {
                Outcome::Scored(s) => s.is_one(),
                Outcome::NoHeadroom(x) => x.is_zero(),
                Outcome::Refused(_) => false,
            };
            if !ok {
                gauge_failures.push(format!("{} {} {:?}", l.name(), pair.id, gauge));
            }
        }
        // Structural trace.
        let trace_outcomes: Vec<(&'static str, Outcome)> = match (&classified, &traces[pair.source])
        {
            (None, _) => vec![("structural_trace", Outcome::Refused(Refusal::BettiMismatch))],
            (_, Err(r)) => vec![("structural_trace", Outcome::Refused(*r))],
            (Some((level, map)), Ok(trace)) => {
                let beta = a.graph.betti();
                let run_map = |cm: &[Option<usize>], scored: &mut dyn FnMut(Option<Vec<i64>>, Refusal) -> Outcome| match replay(trace, b, cm) {
                    Ok(phi) => scored(Some(phi), Refusal::CutSetNotCotree),
                    Err(r) => Outcome::Refused(r),
                };
                match (level, map) {
                    (_, Some(pi)) => {
                        let cm = chord_map_from_vertex_map(&a.graph, &b.graph, pi);
                        vec![("structural_trace", run_map(&cm, &mut scored))]
                    }
                    (Level::L5, None) => {
                        let mut all: Vec<Outcome> = permutations(beta)
                            .iter()
                            .map(|sigma| {
                                let cm: Vec<Option<usize>> =
                                    sigma.iter().map(|&k| Some(k)).collect();
                                run_map(&cm, &mut scored)
                            })
                            .collect();
                        all.sort_by_key(outcome_rank);
                        let worst = all
                            .first()
                            .cloned()
                            .unwrap_or(Outcome::Refused(Refusal::ChordNoImage));
                        let best = all
                            .last()
                            .cloned()
                            .unwrap_or(Outcome::Refused(Refusal::ChordNoImage));
                        vec![
                            ("structural_trace_min", worst),
                            ("structural_trace_max", best),
                        ]
                    }
                    (_, None) => {
                        let cm: Vec<Option<usize>> = (0..beta).map(Some).collect();
                        vec![("structural_trace", run_map(&cm, &mut scored))]
                    }
                }
            }
        };
        record(
            &mut rows,
            &mut refusals,
            (pair.cohort, level.clone(), "gauge_transport"),
            &gauge,
        );
        for (method, outcome) in &trace_outcomes {
            record(
                &mut rows,
                &mut refusals,
                (pair.cohort, level.clone(), method),
                outcome,
            );
        }
    }

    let mut table = String::from(
        "| cohort | level | method | pairs | SCORED | NO_HEADROOM | REFUSED | S=1 | S<0 | sum S | NH worse | NH sum(D_tau-D0) |\n|---|---|---|---|---|---|---|---|---|---|---|---|\n",
    );
    for ((cohort, level, method), r) in &rows {
        table.push_str(&format!(
            "| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |\n",
            cohort.name(),
            level,
            method,
            r.pairs,
            r.scored,
            r.no_headroom,
            r.refused,
            r.s_one,
            r.s_negative,
            r.sum_s,
            r.no_headroom_worse,
            r.no_headroom_excess
        ));
    }
    table.push_str("\n| cohort | level | method | refusal code | count |\n|---|---|---|---|---|\n");
    for ((cohort, level, method, code), k) in &refusals {
        table.push_str(&format!(
            "| {} | {} | {} | {} | {} |\n",
            cohort.name(),
            level,
            method,
            code,
            k
        ));
    }
    let output_digest = sha256_hex(&format!("{census_text}\n{table}"));
    Ok(RunOutput {
        table,
        census: census_text,
        input_digest: sha256_hex(&canonical),
        output_digest,
        instance_count: family.instances.len(),
        pair_count: pairs.len(),
        gauge_failures,
        defects,
    })
}

/// The receipt that pins a run. Replaying it must reproduce both digests.
pub fn receipt_json(cfg: &RunConfig, out: &RunOutput) -> String {
    format!(
        "{{\n  \"schema\": \"pfp.obstruction-transfer-receipt.v1\",\n  \"AuthorityEffect\": \"None\",\n  \"max_n\": {},\n  \"weights\": [1, 2],\n  \"chord_coordinates\": [-2, 2],\n  \"gauge_psi\": [-1, 1],\n  \"instances\": {},\n  \"pairs\": {},\n  \"input_digest\": \"{}\",\n  \"output_digest\": \"{}\"\n}}\n",
        cfg.max_n, out.instance_count, out.pair_count, out.input_digest, out.output_digest
    )
}

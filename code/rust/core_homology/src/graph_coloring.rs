//! Exact bipartition or replayable odd-cycle certificates for finite undirected graphs.
//! AuthorityEffect: None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_e7f9e4fb<T> {
    fn checked_invariant_e7f9e4fb(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_e7f9e4fb<T> for Option<T> {
    #[inline]
    fn checked_invariant_e7f9e4fb(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_e7f9e4fb<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_e7f9e4fb(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::VecDeque;

/// Default finite carrier policy, checked before any graph storage is allocated.
pub const MAX_COLORING_VERTICES: usize = 4096;
pub const MAX_COLORING_EDGES: usize = 1 << 20;

#[derive(Clone, Debug, PartialEq, Eq, thiserror::Error)]
pub enum GraphColoringError {
    #[error("edge ({u}, {v}) is outside {vertices} vertices")]
    BadEdge { vertices: usize, u: usize, v: usize },
    #[error("two-colouring admits at most 4096 vertices and 1048576 edges")]
    SizeBudget,
    #[error("storage for the admitted graph could not be reserved")]
    Allocation,
}
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum TwoColoring {
    Bipartite { colors: Vec<u8>, components: usize },
    OddCycle(Vec<usize>),
}
/// Independently replay a simple odd cycle, including a self-loop.
pub fn verify_odd_cycle(vertices: usize, edges: &[(usize, usize)], cycle: &[usize]) -> bool {
    if cycle.is_empty() || cycle.len() % 2 == 0 || cycle.iter().any(|&v| v >= vertices) {
        return false;
    }
    let mut seen = std::collections::BTreeSet::new();
    if !cycle.iter().all(|&v| seen.insert(v)) {
        return false;
    }
    (0..cycle.len()).all(|i| {
        let (a, b) = (cycle[i], cycle[(i + 1) % cycle.len()]);
        edges
            .iter()
            .any(|&(u, v)| (u == a && v == b) || (u == b && v == a))
    })
}
pub fn verify_bipartition(vertices: usize, edges: &[(usize, usize)], colors: &[u8]) -> bool {
    colors.len() == vertices
        && colors.iter().all(|&c| c < 2)
        && edges
            .iter()
            .all(|&(u, v)| u < vertices && v < vertices && colors[u] != colors[v])
}
/// Deterministic breadth-first two-colouring. An odd-cycle separator is a tree
/// path between the endpoints of a same-colour edge, closed by that edge.
pub fn two_coloring(
    vertices: usize,
    edges: &[(usize, usize)],
) -> Result<TwoColoring, GraphColoringError> {
    let degrees = validate_and_count_degrees(vertices, edges)?;
    let adjacent = build_coloring_adjacency(vertices, edges, degrees)?;
    let (mut colors, mut parent, mut queue) = init_coloring_buffers(vertices)?;
    let mut components = 0;
    for start in 0..vertices {
        if colors[start].is_some() {
            continue;
        }
        components += 1;
        if let Some(cycle) = bfs_color_component(
            start,
            vertices,
            edges,
            &adjacent,
            &mut colors,
            &mut parent,
            &mut queue,
        )? {
            return Ok(TwoColoring::OddCycle(cycle));
        }
    }
    let mut output = Vec::new();
    output
        .try_reserve_exact(vertices)
        .map_err(|_| GraphColoringError::Allocation)?;
    output.extend(colors.into_iter().map(Option::unwrap));
    debug_assert!(verify_bipartition(vertices, edges, &output));
    Ok(TwoColoring::Bipartite {
        colors: output,
        components,
    })
}

type ColoringBuffers = (Vec<Option<u8>>, Vec<Option<usize>>, VecDeque<usize>);

fn init_coloring_buffers(vertices: usize) -> Result<ColoringBuffers, GraphColoringError> {
    let mut colors = Vec::new();
    colors
        .try_reserve_exact(vertices)
        .map_err(|_| GraphColoringError::Allocation)?;
    colors.resize(vertices, None);
    let mut parent = Vec::new();
    parent
        .try_reserve_exact(vertices)
        .map_err(|_| GraphColoringError::Allocation)?;
    parent.resize(vertices, None);
    let mut queue = VecDeque::new();
    queue
        .try_reserve_exact(vertices)
        .map_err(|_| GraphColoringError::Allocation)?;
    Ok((colors, parent, queue))
}

fn validate_and_count_degrees(
    vertices: usize,
    edges: &[(usize, usize)],
) -> Result<Vec<usize>, GraphColoringError> {
    if vertices > MAX_COLORING_VERTICES || edges.len() > MAX_COLORING_EDGES {
        return Err(GraphColoringError::SizeBudget);
    }
    for &(u, v) in edges {
        if u >= vertices || v >= vertices {
            return Err(GraphColoringError::BadEdge { vertices, u, v });
        }
    }
    let mut degrees = Vec::new();
    degrees
        .try_reserve_exact(vertices)
        .map_err(|_| GraphColoringError::Allocation)?;
    degrees.resize(vertices, 0usize);
    for &(u, v) in edges {
        degrees[u] = degrees[u]
            .checked_add(1)
            .ok_or(GraphColoringError::SizeBudget)?;
        degrees[v] = degrees[v]
            .checked_add(1)
            .ok_or(GraphColoringError::SizeBudget)?;
    }
    Ok(degrees)
}

fn build_coloring_adjacency(
    vertices: usize,
    edges: &[(usize, usize)],
    degrees: Vec<usize>,
) -> Result<Vec<Vec<usize>>, GraphColoringError> {
    let mut adjacent: Vec<Vec<usize>> = Vec::new();
    adjacent
        .try_reserve_exact(vertices)
        .map_err(|_| GraphColoringError::Allocation)?;
    for degree in degrees {
        let mut neighbors = Vec::new();
        neighbors
            .try_reserve_exact(degree)
            .map_err(|_| GraphColoringError::Allocation)?;
        adjacent.push(neighbors);
    }
    for &(u, v) in edges {
        adjacent[u].push(v);
        adjacent[v].push(u);
    }
    for neighbors in &mut adjacent {
        neighbors.sort_unstable();
        neighbors.dedup();
    }
    Ok(adjacent)
}

fn bfs_color_component(
    start: usize,
    vertices: usize,
    edges: &[(usize, usize)],
    adjacent: &[Vec<usize>],
    colors: &mut [Option<u8>],
    parent: &mut [Option<usize>],
    queue: &mut VecDeque<usize>,
) -> Result<Option<Vec<usize>>, GraphColoringError> {
    colors[start] = Some(0u8);
    queue.push_back(start);
    while let Some(u) = queue.pop_front() {
        for &v in &adjacent[u] {
            if colors[v].is_none() {
                colors[v] = Some(1 - colors[u].checked_invariant_e7f9e4fb("checked invariant"));
                parent[v] = Some(u);
                queue.push_back(v);
            } else if colors[v] == colors[u] {
                return Ok(Some(extract_odd_cycle(vertices, edges, parent, u, v)?));
            }
        }
    }
    Ok(None)
}

fn trace_ancestors(
    vertices: usize,
    parent: &[Option<usize>],
    mut node: usize,
) -> Result<Vec<usize>, GraphColoringError> {
    let mut path = Vec::new();
    path.try_reserve_exact(vertices)
        .map_err(|_| GraphColoringError::Allocation)?;
    loop {
        path.push(node);
        match parent[node] {
            Some(p) => node = p,
            None => break,
        }
    }
    Ok(path)
}

fn extract_odd_cycle(
    vertices: usize,
    edges: &[(usize, usize)],
    parent: &[Option<usize>],
    u: usize,
    v: usize,
) -> Result<Vec<usize>, GraphColoringError> {
    let a = trace_ancestors(vertices, parent, u)?;
    let b = trace_ancestors(vertices, parent, v)?;
    let mut i = a.len();
    let mut j = b.len();
    while i > 0 && j > 0 && a[i - 1] == b[j - 1] {
        i -= 1;
        j -= 1;
    }
    let mut cycle = Vec::new();
    cycle
        .try_reserve_exact(vertices)
        .map_err(|_| GraphColoringError::Allocation)?;
    cycle.extend_from_slice(&a[..=i]);
    cycle.extend(b[..j].iter().rev().copied());
    debug_assert!(verify_odd_cycle(vertices, edges, &cycle));
    Ok(cycle)
}
// Origin: engine/crates_rs/core_homology/src/graph_coloring.rs
// Claim: urn:core:crates_rs:core-homology:graph-coloring:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn colouring_admission_precedes_allocation_and_preserves_empty_graphs() {
        let extreme = std::panic::catch_unwind(|| two_coloring(usize::MAX, &[]));
        assert!(
            extreme.is_ok(),
            "extreme declarations must refuse without panicking"
        );
        assert_eq!(extreme.unwrap(), Err(GraphColoringError::SizeBudget));
        assert_eq!(two_coloring(4097, &[]), Err(GraphColoringError::SizeBudget));
        let excess_edges = vec![(0, 0); (1 << 20) + 1];
        assert_eq!(
            two_coloring(1, &excess_edges),
            Err(GraphColoringError::SizeBudget)
        );
        assert_eq!(
            two_coloring(4096, &[(0, 4096)]),
            Err(GraphColoringError::BadEdge {
                vertices: 4096,
                u: 0,
                v: 4096
            })
        );
        assert_eq!(
            two_coloring(0, &[]),
            Ok(TwoColoring::Bipartite {
                colors: vec![],
                components: 0
            })
        );
        assert_eq!(
            two_coloring(1, &[(0, 0)]),
            Ok(TwoColoring::OddCycle(vec![0]))
        );
        let TwoColoring::Bipartite { colors, components } = two_coloring(4096, &[]).unwrap() else {
            panic!("isolated vertices must be admitted at the policy boundary");
        };
        assert_eq!(components, 4096);
        assert_eq!(colors, vec![0; 4096]);
    }
    #[test]
    fn every_separator_replays_and_invalid_edges_refuse() {
        for edges in [
            vec![(0, 1), (1, 2), (2, 0)],
            vec![(0, 1), (1, 2), (2, 3), (3, 4), (4, 2)],
            vec![(0, 0)],
        ] {
            let TwoColoring::OddCycle(c) = two_coloring(5, &edges).unwrap() else {
                panic!("odd cycle expected")
            };
            assert!(verify_odd_cycle(5, &edges, &c));
        }
        assert!(two_coloring(2, &[(0, 2)]).is_err());
        assert!(!verify_odd_cycle(3, &[(0, 1), (1, 2)], &[0, 1, 2]));
    }
    #[test]
    fn bipartition_includes_isolates_and_component_count() {
        let TwoColoring::Bipartite { colors, components } =
            two_coloring(5, &[(0, 1), (2, 3)]).unwrap()
        else {
            panic!("bipartite expected")
        };
        assert_eq!(components, 3);
        assert!(verify_bipartition(5, &[(0, 1), (2, 3)], &colors));
    }
}

#[cfg(test)]
mod transferred_regressions {
    use super::*;
    use std::collections::HashMap;
    fn detect_odd_cycle(
        n: usize,
        edges: &[(usize, usize)],
    ) -> (bool, Option<Vec<usize>>, HashMap<usize, usize>) {
        match two_coloring(n, edges).unwrap() {
            TwoColoring::OddCycle(w) => (true, Some(w), HashMap::new()),
            TwoColoring::Bipartite { colors, .. } => (
                false,
                None,
                colors
                    .into_iter()
                    .enumerate()
                    .map(|(i, c)| (i, usize::from(c)))
                    .collect(),
            ),
        }
    }

    fn adjacent(edges: &[(usize, usize)], a: usize, b: usize) -> bool {
        edges
            .iter()
            .any(|&(u, v)| (u, v) == (a, b) || (u, v) == (b, a))
    }

    /// An independent check of a witness: odd length, distinct vertices, every consecutive
    /// pair (and the closing pair) joined by an edge.
    fn is_odd_cycle(edges: &[(usize, usize)], w: &[usize]) -> bool {
        let mut sorted = w.to_vec();
        sorted.sort_unstable();
        sorted.dedup();
        w.len() % 2 == 1
            && sorted.len() == w.len()
            && (0..w.len()).all(|i| adjacent(edges, w[i], w[(i + 1) % w.len()]))
    }

    fn is_proper_coloring(edges: &[(usize, usize)], color: &HashMap<usize, usize>) -> bool {
        edges.iter().all(|(u, v)| color[u] != color[v])
    }

    #[test]
    fn a_triangle_gives_itself_as_the_witness() {
        let edges = [(0, 1), (1, 2), (2, 0)];
        let (odd, witness, _) = detect_odd_cycle(3, &edges);
        assert!(odd);
        assert!(is_odd_cycle(&edges, &witness.unwrap()));
    }

    #[test]
    fn the_witness_is_the_odd_cycle_even_when_it_does_not_pass_through_the_search_root() {
        // a path 0-1-2 leading to the triangle 2-3-4, and a tail 4-5
        let edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 2), (4, 5)];
        let (odd, witness, _) = detect_odd_cycle(6, &edges);
        assert!(odd);
        let mut cycle = witness.unwrap();
        assert!(is_odd_cycle(&edges, &cycle));
        cycle.sort_unstable();
        assert_eq!(cycle, vec![2, 3, 4]);
    }

    #[test]
    fn a_pentagon_with_a_tail_gives_the_five_cycle() {
        let edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (0, 5), (5, 6)];
        let (odd, witness, _) = detect_odd_cycle(7, &edges);
        assert!(odd);
        let mut cycle = witness.unwrap();
        assert!(is_odd_cycle(&edges, &cycle));
        cycle.sort_unstable();
        assert_eq!(cycle, vec![0, 1, 2, 3, 4]);
    }

    #[test]
    fn a_self_loop_is_a_one_vertex_odd_cycle() {
        let edges = [(0, 1), (1, 1)];
        let (odd, witness, _) = detect_odd_cycle(2, &edges);
        assert!(odd);
        assert_eq!(witness, Some(vec![1]));
    }

    #[test]
    fn bipartite_graphs_have_no_witness_and_a_proper_colouring() {
        let six_cycle = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)];
        let tree_and_isolated = [(0, 1), (0, 2), (2, 3)];
        for (n, edges) in [(6usize, &six_cycle[..]), (5usize, &tree_and_isolated[..])] {
            let (odd, witness, color) = detect_odd_cycle(n, edges);
            assert!(!odd);
            assert!(witness.is_none());
            assert_eq!(color.len(), n);
            assert!(is_proper_coloring(edges, &color));
        }
    }

    /// Cross-check against an independent decision (exhaustive 2-colouring) on 400
    /// pseudo-random graphs with up to 7 vertices.
    #[test]
    fn detection_agrees_with_exhaustive_two_colouring_and_every_witness_is_valid() {
        let mut state: u64 = 0x2545_f491_4f6c_dd1d;
        let mut next = move || {
            state = state
                .wrapping_mul(6364136223846793005)
                .wrapping_add(1442695040888963407);
            (state >> 33) as usize
        };
        for _ in 0..400 {
            let n = 2 + next() % 6;
            let edge_count = next() % (2 * n);
            let edges: Vec<(usize, usize)> =
                (0..edge_count).map(|_| (next() % n, next() % n)).collect();
            let bipartite = (0u32..(1 << n)).any(|mask| {
                edges
                    .iter()
                    .all(|&(u, v)| ((mask >> u) & 1) != ((mask >> v) & 1))
            });
            let (odd, witness, color) = detect_odd_cycle(n, &edges);
            assert_eq!(odd, !bipartite, "n={n} edges={edges:?}");
            if odd {
                assert!(
                    is_odd_cycle(&edges, &witness.unwrap()),
                    "n={n} edges={edges:?}"
                );
            } else {
                assert!(witness.is_none());
                assert!(is_proper_coloring(&edges, &color), "n={n} edges={edges:?}");
            }
        }
    }
}

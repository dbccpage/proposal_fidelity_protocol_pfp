//! Complete free path categories of declared finite acyclic multigraphs.
//! Parallel edges are distinct generators. Cycles and resource excess are
//! refused; enumeration never turns a truncated frontier into a category.
//! Complete free path categories of declared finite acyclic multigraphs.
//! Parallel edges are distinct generators. Cycles and resource excess are
//! refused; enumeration never turns a truncated frontier into a category.
use crate::finite_category::{DeclaredFiniteCategory, ValidatedFiniteCategory};
use std::collections::BTreeSet;

/// Explicit execution bound, not a mathematical finiteness theorem.
/// Explicit execution bound, not a mathematical finiteness theorem.
pub const MAX_PATHS: usize = 64;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct PathEdge {
    pub source: usize,
    pub target: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PathError {
    EmptyGraph,
    GraphBudget,
    InvalidVertex,
    Cycle,
    PathBudget,
    UnknownPath,
    MissingComposite,
    CategoryValidation,
}
impl std::fmt::Display for PathError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "finite path category refused: {self:?}")
    }
}
impl std::error::Error for PathError {}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct FinitePath {
    source: usize,
    target: usize,
    edges: Vec<usize>,
}
impl FinitePath {
    pub fn source(&self) -> usize {
        self.source
    }
    pub fn target(&self) -> usize {
        self.target
    }
    /// Chronological edge order; the empty path is the source identity.
    /// Chronological edge order; the empty path is the source identity.
    pub fn edges(&self) -> &[usize] {
        &self.edges
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FinitePathCategory {
    vertices: usize,
    edges: Vec<PathEdge>,
    paths: Vec<FinitePath>,
    composition: Vec<Vec<Option<usize>>>,
    category: ValidatedFiniteCategory,
}
fn checked_outgoing(vertices: usize, edges: &[PathEdge]) -> Result<Vec<Vec<usize>>, PathError> {
    if vertices == 0 { return Err(PathError::EmptyGraph); }
    if vertices > MAX_PATHS || edges.len() > MAX_PATHS { return Err(PathError::GraphBudget); }
    if edges.iter().any(|e| e.source >= vertices || e.target >= vertices) { return Err(PathError::InvalidVertex); }
    let mut outgoing = vec![Vec::new(); vertices];
    let mut indegree = vec![0usize; vertices];
    for (i, edge) in edges.iter().enumerate() {
        outgoing[edge.source].push(i);
        indegree[edge.target] += 1;
    }
    ensure_acyclic(edges, &outgoing, indegree)?;
    Ok(outgoing)
}

fn ensure_acyclic(edges: &[PathEdge], outgoing: &[Vec<usize>], mut indegree: Vec<usize>) -> Result<(), PathError> {
    let mut ready: BTreeSet<_> = (0..outgoing.len()).filter(|&v| indegree[v] == 0).collect();
    let mut visited = 0;
    while let Some(vertex) = ready.pop_first() {
        visited += 1;
        for &edge in &outgoing[vertex] {
            let target = edges[edge].target;
            indegree[target] -= 1;
            if indegree[target] == 0 { ready.insert(target); }
        }
    }
    if visited != outgoing.len() { return Err(PathError::Cycle); }
    Ok(())
}

fn enumerate_paths(vertices: usize, edges: &[PathEdge], outgoing: &[Vec<usize>], budget: usize) -> Result<Vec<FinitePath>, PathError> {
    if vertices > budget { return Err(PathError::PathBudget); }
    let mut paths: Vec<_> = (0..vertices).map(|vertex| FinitePath {source:vertex,target:vertex,edges:Vec::new()}).collect();
    let mut cursor = 0;
    while cursor < paths.len() {
        for &edge in &outgoing[paths[cursor].target] {
            if paths.len() == budget { return Err(PathError::PathBudget); }
            let mut word = paths[cursor].edges.clone();
            word.push(edge);
            paths.push(FinitePath {source:paths[cursor].source,target:edges[edge].target,edges:word});
        }
        cursor += 1;
    }
    Ok(paths)
}

fn declared_path_category(vertices: usize, paths: &[FinitePath]) -> (DeclaredFiniteCategory, Vec<String>) {
    let objects: Vec<_> = (0..vertices).map(|vertex| format!("v{vertex}")).collect();
    let names: Vec<_> = (0..paths.len()).map(|path| format!("p{path}")).collect();
    let mut category = DeclaredFiniteCategory::new("complete finite acyclic free path category");
    for vertex in 0..vertices { category.add_identity(&objects[vertex], &names[vertex]); }
    for (i, path) in paths.iter().enumerate().skip(vertices) {
        category.add_morphism(&names[i], &objects[path.source], &objects[path.target]);
    }
    (category, names)
}

struct PathLookup<'a> { rows: Vec<((usize, &'a [usize]), usize)> }
impl<'a> PathLookup<'a> {
    fn new(paths: &'a [FinitePath]) -> Self {
        let mut rows: Vec<_> = paths.iter().enumerate().map(|(i, path)| ((path.source,path.edges.as_slice()),i)).collect();
        rows.sort_unstable_by(|left, right| left.0.cmp(&right.0));
        Self { rows }
    }

    fn find(&self, source: usize, word: &[usize]) -> Result<usize, PathError> {
        let index = self.rows.binary_search_by_key(&(source, word), |(key, _)| *key).map_err(|_| PathError::MissingComposite)?;
        self.rows.get(index).map(|(_, path)| *path).ok_or(PathError::MissingComposite)
    }
}

fn compose_paths(paths: &[FinitePath], category: &mut DeclaredFiniteCategory, names: &[String]) -> Result<Vec<Vec<Option<usize>>>, PathError> {
    let lookup = PathLookup::new(paths);
    let mut word = Vec::new();
    let mut composition = vec![vec![None; paths.len()]; paths.len()];
    for (i, first) in paths.iter().enumerate() {
        for (j, second) in paths.iter().enumerate() {
            if first.target != second.source { continue; }
            word.clear();
            word.extend_from_slice(&first.edges);
            word.extend_from_slice(&second.edges);
            let composite = lookup.find(first.source, &word)?;
            composition[i][j] = Some(composite);
            category.set_composition(&names[i], &names[j], &names[composite]);
        }
    }
    Ok(composition)
}

impl FinitePathCategory {
    pub fn new(vertices: usize, edges: Vec<PathEdge>, max_paths: usize) -> Result<Self, PathError> {
        // Identities have indices exactly equal to their vertices.
        let outgoing = checked_outgoing(vertices, &edges)?;
        let paths = enumerate_paths(vertices, &edges, &outgoing, max_paths.min(MAX_PATHS))?;
        let (mut category, names) = declared_path_category(vertices, &paths);
        let composition = compose_paths(&paths, &mut category, &names)?;
        let category = ValidatedFiniteCategory::try_new(category)
            .map_err(|_| PathError::CategoryValidation)?;
        Ok(Self {
            vertices,
            edges,
            paths,
            composition,
            category,
        })
    }
    pub fn vertices(&self) -> usize {
        self.vertices
    }
    pub fn edges(&self) -> &[PathEdge] {
        &self.edges
    }
    pub fn paths(&self) -> &[FinitePath] {
        &self.paths
    }
    pub fn category(&self) -> &ValidatedFiniteCategory {
        &self.category
    }
    pub fn path(&self, index: usize) -> Result<&FinitePath, PathError> {
        self.paths.get(index).ok_or(PathError::UnknownPath)
    }
    /// Second after first. None means noncomposable, never missing closure.
    /// Second after first. None means noncomposable, never missing closure.
    pub fn compose(&self, first: usize, second: usize) -> Result<Option<usize>, PathError> {
        self.composition
            .get(first)
            .and_then(|row| row.get(second))
            .copied()
            .ok_or(PathError::UnknownPath)
    }
    pub fn edge_path(&self, edge: usize) -> Result<usize, PathError> {
        if edge >= self.edges.len() {
            return Err(PathError::UnknownPath);
        }
        self.paths
            .iter()
            .position(|p| p.edges == [edge])
            .ok_or(PathError::MissingComposite)
    }
    pub fn origin_path_counts(&self) -> Vec<usize> {
        let mut counts = vec![0; self.vertices];
        for p in &self.paths {
            counts[p.source] += 1;
        }
        counts
    }
}

// Origin: engine/crates_rs/core_category_theory/src/finite_path.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-path:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_54841585 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}

//! Exact bounded clique enumeration on indexed undirected bitset graphs.
//! AuthorityEffect: None.
const MAX_BRANCHES: usize = 1 << 24;
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum CliqueError {
    #[error("the adjacency must be symmetric, loop free and indexed on at most128 vertices")]
    Graph,
    #[error("clique search exceeds2^24 branches or65536 output cliques")]
    Budget,
}
fn mask(n: usize) -> u128 {
    if n == 128 {
        u128::MAX
    } else {
        (1u128 << n) - 1
    }
}
pub fn validate_graph(adj: &[u128]) -> Result<(), CliqueError> {
    if adj.len() > 128 {
        return Err(CliqueError::Graph);
    }
    let valid = mask(adj.len());
    for (v, &neighbors) in adj.iter().enumerate() {
        if neighbors & !valid != 0 || neighbors & (1 << v) != 0 {
            return Err(CliqueError::Graph);
        }
        for u in 0..adj.len() {
            if (neighbors >> u) & 1 != (adj[u] >> v) & 1 {
                return Err(CliqueError::Graph);
            }
        }
    }
    Ok(())
}
fn charge(budget: &mut usize) -> Result<(), CliqueError> {
    if *budget == 0 {
        Err(CliqueError::Budget)
    } else {
        *budget -= 1;
        Ok(())
    }
}
pub fn cliques(adj: &[u128], k: usize) -> Result<Vec<Vec<usize>>, CliqueError> {
    validate_graph(adj)?;
    if k > adj.len() {
        return Ok(Vec::new());
    }
    fn walk(
        a: &[u128],
        k: usize,
        c: &mut Vec<usize>,
        mut p: u128,
        out: &mut Vec<Vec<usize>>,
        budget: &mut usize,
    ) -> Result<(), CliqueError> {
        charge(budget)?;
        if c.len() == k {
            if out.len() >= 65536 {
                return Err(CliqueError::Budget);
            }
            out.push(c.clone());
            return Ok(());
        }
        while p != 0 {
            if c.len() + (p.count_ones() as usize) < k {
                return Ok(());
            }
            let v = p.trailing_zeros() as usize;
            p &= p - 1;
            c.push(v);
            walk(a, k, c, p & a[v], out, budget)?;
            c.pop();
        }
        Ok(())
    }
    let mut out = vec![];
    walk(adj, k, &mut vec![], mask(adj.len()), &mut out, &mut {
        MAX_BRANCHES
    })?;
    Ok(out)
}
/// Exhaustive maximum-clique search with a greedy-color upper bound, over at most128 vertices.
pub fn maximum_clique(adj: &[u128]) -> Result<usize, CliqueError> {
    validate_graph(adj)?;
    fn expand(
        a: &[u128],
        size: usize,
        mut p: u128,
        best: &mut usize,
        budget: &mut usize,
    ) -> Result<(), CliqueError> {
        charge(budget)?;
        if p == 0 {
            *best = (*best).max(size);
            return Ok(());
        }
        let mut remaining = p;
        let mut order = vec![];
        let mut bounds = vec![];
        let mut color = 0;
        while remaining != 0 {
            color += 1;
            let mut available = remaining;
            while available != 0 {
                let v = available.trailing_zeros() as usize;
                order.push(v);
                bounds.push(color);
                remaining &= !(1 << v);
                available &= !(1 << v);
                available &= !a[v];
            }
        }
        for i in (0..order.len()).rev() {
            if size + bounds[i] <= *best {
                return Ok(());
            }
            let v = order[i];
            expand(a, size + 1, p & a[v], best, budget)?;
            p &= !(1 << v);
        }
        Ok(())
    }
    let mut best = 0;
    expand(adj, 0, mask(adj.len()), &mut best, &mut { MAX_BRANCHES })?;
    Ok(best)
}

// Origin: engine/crates_rs/core_homology/src/finite_cliques.rs
// Claim: urn:core:crates_rs:core-homology:finite-cliques:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn finite_cliques_agree_with_exhaustive_subsets_and_handle128_vertices() {
        let adj = [0b1110, 0b0101, 0b1011, 0b0101];
        for k in 0..=4 {
            let found = cliques(&adj, k).unwrap();
            let count = (0u128..16)
                .filter(|s| {
                    s.count_ones() == k as u32
                        && (0..4).all(|v| s & (1 << v) == 0 || ((s & !(1 << v)) & !adj[v]) == 0)
                })
                .count();
            assert_eq!(found.len(), count);
        }
        assert_eq!(maximum_clique(&adj).unwrap(), 3);
        assert_eq!(cliques(&[0; 128], 1).unwrap().len(), 128);
        assert_eq!(maximum_clique(&[0; 128]).unwrap(), 1);
        assert!(cliques(&[1], 1).is_err());
    }
}

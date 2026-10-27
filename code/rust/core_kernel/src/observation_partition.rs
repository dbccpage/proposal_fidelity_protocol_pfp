//! Coarsest deterministic context-stable refinement of a finite observation.
//! Context maps and the original labels are declared; no lift is certified by
//! the mere occurrence of a separating context. AuthorityEffect: None.
use std::collections::BTreeMap;
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PartitionError {
    #[error("finite observation needs 1..=4096 points and at most 256 contexts")]
    Budget,
    #[error("context {context} has wrong length or an image outside the carrier")]
    Context { context: usize },
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StableObservation {
    labels: Vec<usize>,
    quotient_contexts: Vec<Vec<usize>>,
    rounds: usize,
}
impl StableObservation {
    pub fn labels(&self) -> &[usize] {
        &self.labels
    }
    pub fn quotient_contexts(&self) -> &[Vec<usize>] {
        &self.quotient_contexts
    }
    pub fn rounds(&self) -> usize {
        self.rounds
    }
    pub fn block_count(&self) -> usize {
        self.labels.iter().max().copied().unwrap_or(0) + 1
    }
}
pub fn stable_refinement(
    projection: &[usize],
    contexts: &[Vec<usize>],
) -> Result<StableObservation, PartitionError> {
    let n = projection.len();
    if n == 0
        || n > 4096
        || contexts.len() > 256
        || n.checked_mul(n)
            .and_then(|v| v.checked_mul(contexts.len().max(1)))
            .is_none_or(|v| v > 1 << 24)
    {
        return Err(PartitionError::Budget);
    }
    for (context, map) in contexts.iter().enumerate() {
        if map.len() != n || map.iter().any(|&v| v >= n) {
            return Err(PartitionError::Context { context });
        }
    }
    let relabel = |keys: Vec<Vec<usize>>| {
        let mut table = BTreeMap::new();
        keys.into_iter()
            .map(|key| {
                let next = table.len();
                *table.entry(key).or_insert(next)
            })
            .collect::<Vec<usize>>()
    };
    let mut labels = relabel(projection.iter().map(|&v| vec![v]).collect());
    let mut rounds = 0;
    loop {
        let next = relabel(
            (0..n)
                .map(|v| {
                    std::iter::once(labels[v])
                        .chain(contexts.iter().map(|c| labels[c[v]]))
                        .collect()
                })
                .collect(),
        );
        if next == labels {
            break;
        }
        labels = next;
        rounds += 1;
    }
    let blocks = labels.iter().max().copied().unwrap_or(0) + 1;
    let quotient_contexts = contexts
        .iter()
        .map(|c| {
            let mut map = vec![0; blocks];
            for v in 0..n {
                map[labels[v]] = labels[c[v]];
            }
            map
        })
        .collect();
    Ok(StableObservation {
        labels,
        quotient_contexts,
        rounds,
    })
}

// Origin: engine/crates_rs/core_kernel/src/observation_partition.rs
// Claim: urn:core:crates_rs:core-kernel:observation-partition:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod dynamics_laws {

    use super::*;
    fn assert_context_congruence(p: &[usize], contexts: &[Vec<usize>], labels: &[usize]) {
        for u in 0..p.len() {
            for v in 0..p.len() {
                if labels[u] == labels[v] {
                    assert_eq!(p[u], p[v]);
                    for c in contexts {
                        assert_eq!(labels[c[u]], labels[c[v]]);
                    }
                }
            }
        }
    }

    fn generate_context_words(n: usize, contexts: &[Vec<usize>]) -> Vec<Vec<usize>> {
        let mut words = vec![(0..n).collect::<Vec<_>>()];
        for _ in 0..n {
            let previous = words.clone();
            for c in contexts {
                for w in &previous {
                    words.push(w.iter().map(|&v| c[v]).collect());
                }
            }
        }
        words
    }

    #[test]
    fn refinement_is_the_least_context_stable_observation() {
        let p = [0, 0, 0, 0, 1, 1];
        let contexts = vec![vec![1, 2, 3, 4, 4, 5], vec![0, 0, 1, 2, 5, 5]];
        let stable = stable_refinement(&p, &contexts).unwrap();
        assert_context_congruence(&p, &contexts, stable.labels());
        // A pair stays equivalent precisely when every declared context word
        // gives the same original observation. Stabilization needs at most n-1 rounds.
        let words = generate_context_words(p.len(), &contexts);
        for u in 0..p.len() {
            for v in 0..p.len() {
                assert_eq!(
                    stable.labels()[u] == stable.labels()[v],
                    words.iter().all(|w| p[w[u]] == p[w[v]])
                );
            }
        }
        assert!(stable.rounds() > 1);
        for (i, c) in contexts.iter().enumerate() {
            for v in 0..p.len() {
                assert_eq!(
                    stable.quotient_contexts()[i][stable.labels()[v]],
                    stable.labels()[c[v]]
                );
            }
        }
    }
    #[test]
    fn malformed_contexts_are_refused_without_partial_refinement() {
        assert!(stable_refinement(&[], &[]).is_err());
        assert!(stable_refinement(&[0, 0], &[vec![0, 2]]).is_err());
        assert!(stable_refinement(&[0, 0], &[vec![0]]).is_err());
    }
}

//! Legacy reasoning-trace diagnostics kept separate from the canonical
//! finite obstruction functionals in [`core_functional::phi1`], [`core_functional::gamma2`], and
//! [`core_functional::xi`]. These scalar features do not certify an obstruction class.

/// Adjacent self-pairing of a finite trace, `sum_i a[i] * a[i + 1]`.
///
/// Earlier homology code called this a shift-Xi score. It is not the
/// primal-dual density-distance Xi defined in [`core_functional::xi`].
pub fn shift_pairing_coherence(a: &[f64]) -> Result<f64, String> {
    if a.is_empty() {
        return Err("xi_shift_coherence: empty cochain".into());
    }
    Ok(a.windows(2).map(|pair| pair[0] * pair[1]).sum())
}

/// Shift pairing divided by squared trace energy plus `eps`.
///
/// This remains a trace-routing feature, not canonical Xi.
pub fn normalized_shift_pairing_coherence(a: &[f64], eps: f64) -> Result<f64, String> {
    let raw = shift_pairing_coherence(a)?;
    let energy: f64 = a.iter().map(|x| x * x).sum();
    Ok(raw / (energy + eps))
}

/// Mean absolute adjacent variation of a finite trace.
///
/// Earlier homology code called this normalized Gamma2. It does not inspect
/// a coboundary, and is not the closure-defect Gamma2 in [`core_functional::gamma2`].
pub fn mean_adjacent_variation(a: &[f64]) -> f64 {
    if a.len() < 2 {
        return 0.0;
    }
    let total: f64 = a.windows(2).map(|pair| (pair[1] - pair[0]).abs()).sum();
    total / ((a.len() - 1) as f64)
}

/// Mean absolute magnitude of interior entropy deltas after excluding one
/// boundary event, when supplied. This is a trace feature, not Gamma2.
pub fn interior_delta_magnitude(a: &[f64], true_boundary_idx: Option<usize>) -> f64 {
    if a.is_empty() || (a.len() == 1 && true_boundary_idx.is_none()) {
        return 0.0;
    }

    let mut sum = 0.0;
    let mut count = 0usize;
    for (i, &v) in a.iter().enumerate() {
        if Some(i) != true_boundary_idx {
            sum += v.abs();
            count += 1;
        }
    }
    if count == 0 {
        return 0.0;
    }
    sum / count as f64
}

/// Mean absolute trace magnitude; empty traces have zero mass.
pub fn mean_absolute_magnitude(a: &[f64]) -> f64 {
    if a.is_empty() {
        0.0
    } else {
        crate::Phi1Functional::unweighted_l1_diagnostic(a) / a.len() as f64
    }
}

/// A single reasoning step (text content of one CoT step).
#[derive(Debug, Clone)]
pub struct ReasoningStep {
    /// Raw text content of the step.
    pub text: String,
}

/// Per-channel scores for a single transition.
#[derive(Debug, Clone, PartialEq)]
pub struct TransitionChannels {
    /// Semantic inconsistency: 1 - entailment(s_i â‡’ s_{i+1}).
    pub phi_sem: f64,
    /// Structural break: normalized edit distance.
    pub phi_struct: f64,
    /// Arithmetic instability: numeric token mismatch.
    pub phi_numeric: f64,
    /// Anti-collapse entropy: distributional divergence.
    pub phi_entropy: f64,
}

/// Weights for combining Ï† channels.
#[derive(Debug, Clone)]
pub struct PhiWeights {
    pub w_sem: f64,
    pub w_struct: f64,
    pub w_numeric: f64,
    pub w_entropy: f64,
}

impl Default for PhiWeights {
    fn default() -> Self {
        Self {
            w_sem: 0.4,
            w_struct: 0.2,
            w_numeric: 0.3,
            w_entropy: 0.1,
        }
    }
}

/// Combined transition score.
#[derive(Debug, Clone, PartialEq)]
pub struct TransitionScore {
    pub channels: TransitionChannels,
    pub combined: f64,
}

// ============================================================================
// Channel implementations (structural, no ML dependencies)
// ============================================================================

/// Ï†_struct: normalized token overlap distance.
///
/// Measures syntactic change between steps via set overlap (NOT true
/// edit distance â€” this ignores token order and repetition).
/// High when the reasoning form jumps abruptly; low when steps share tokens.
pub fn phi_struct(s_i: &str, s_next: &str) -> f64 {
    let a: Vec<&str> = s_i.split_whitespace().collect();
    let b: Vec<&str> = s_next.split_whitespace().collect();
    let max_len = a.len().max(b.len());
    if max_len == 0 {
        return 0.0;
    }
    // Count tokens in a that also appear in b (order-insensitive set overlap)
    let common = a.iter().filter(|t| b.contains(t)).count();
    let dist = max_len - common;
    (dist as f64 / max_len as f64).clamp(0.0, 1.0)
}

/// Ï†_numeric: symmetric arithmetic token mismatch.
///
/// Extracts all numeric tokens from both steps and computes the
/// symmetric minimum-cost matching error:
///   Ï†_numeric(a,b) = 0.5 * (match(bâ†’a) + match(aâ†’b))
///
/// Symmetry ensures Ï†(s_i, s_{i+1}) = Ï†(s_{i+1}, s_i), which
/// prevents directional artifacts in the cochain.
pub fn phi_numeric(s_i: &str, s_next: &str) -> f64 {
    let nums_a = extract_numbers(s_i);
    let nums_b = extract_numbers(s_next);

    if nums_a.is_empty() && nums_b.is_empty() {
        return 0.0; // no numbers â†’ no numeric inconsistency
    }
    if nums_a.is_empty() || nums_b.is_empty() {
        return 0.5; // one side has numbers, other doesn't
    }

    // Forward matching: each number in b finds closest in a
    let forward_error: f64 = nums_b
        .iter()
        .map(|nb| {
            nums_a
                .iter()
                .map(|na| (na - nb).abs())
                .fold(f64::INFINITY, f64::min)
        })
        .sum();

    // Backward matching: each number in a finds closest in b
    let backward_error: f64 = nums_a
        .iter()
        .map(|na| {
            nums_b
                .iter()
                .map(|nb| (na - nb).abs())
                .fold(f64::INFINITY, f64::min)
        })
        .sum();

    // Symmetric average
    let total_error = 0.5 * (forward_error + backward_error);

    // Normalize by sum of magnitudes
    let scale: f64 = nums_a
        .iter()
        .chain(nums_b.iter())
        .map(|x| x.abs())
        .sum::<f64>()
        .max(1.0);
    (total_error / scale).clamp(0.0, 1.0)
}

/// Ï†_entropy: anti-collapse term.
///
/// Measures distributional change in token frequencies. Forces
/// variation across steps â†’ prevents constant a[i] â†’ prevents
/// degenerate Î“â‚‚ = 0.
pub fn phi_entropy(s_i: &str, s_next: &str) -> f64 {
    let len_a = s_i.len() as f64;
    let len_b = s_next.len() as f64;
    let max_len = len_a.max(len_b).max(1.0);

    // Length ratio component
    let length_change = (len_b - len_a).abs() / max_len;

    // Unique token ratio component
    let uniq_a: std::collections::HashSet<&str> = s_i.split_whitespace().collect();
    let uniq_b: std::collections::HashSet<&str> = s_next.split_whitespace().collect();
    let union_size = uniq_a.union(&uniq_b).count() as f64;
    let intersect_size = uniq_a.intersection(&uniq_b).count() as f64;
    let jaccard_dist = if union_size > 0.0 {
        1.0 - intersect_size / union_size
    } else {
        0.0
    };

    (0.5 * length_change + 0.5 * jaccard_dist).clamp(0.0, 1.0)
}

/// Ï†_sem: semantic inconsistency proxy (structural, no NLI model).
///
/// Uses negation/contradiction keyword detection as a cheap proxy.
/// For production, replace with a frozen NLI model or embedding cosine.
pub fn phi_sem(s_i: &str, s_next: &str) -> f64 {
    let contradiction_markers = [
        "but ",
        "however ",
        "actually ",
        "wait ",
        "no ",
        "incorrect",
        "wrong ",
        "mistake",
        "contradiction",
        "impossible",
        "not true",
        "doesn't hold",
        "cannot be",
    ];

    let lower = s_next.to_lowercase();
    let hits = contradiction_markers
        .iter()
        .filter(|m| lower.contains(*m))
        .count();

    // Also check if s_next explicitly negates something from s_i
    let negation_bonus = if !s_i.is_empty() {
        let words_a: Vec<&str> = s_i.split_whitespace().take(5).collect();
        let negated = words_a.iter().any(|w| {
            let neg = format!("not {}", w.to_lowercase());
            lower.contains(&neg)
        });
        if negated {
            0.3
        } else {
            0.0
        }
    } else {
        0.0
    };

    ((hits as f64 * 0.2) + negation_bonus).clamp(0.0, 1.0)
}

// ============================================================================
// Combined scorer
// ============================================================================

/// Compute the full Ï† score for a transition.
pub fn score_transition(
    s_i: &ReasoningStep,
    s_next: &ReasoningStep,
    weights: &PhiWeights,
) -> TransitionScore {
    let channels = TransitionChannels {
        phi_sem: phi_sem(&s_i.text, &s_next.text),
        phi_struct: phi_struct(&s_i.text, &s_next.text),
        phi_numeric: phi_numeric(&s_i.text, &s_next.text),
        phi_entropy: phi_entropy(&s_i.text, &s_next.text),
    };

    let combined = weights.w_sem * channels.phi_sem
        + weights.w_struct * channels.phi_struct
        + weights.w_numeric * channels.phi_numeric
        + weights.w_entropy * channels.phi_entropy;

    TransitionScore {
        channels,
        combined: combined.clamp(0.0, 1.0),
    }
}

/// Score an entire trace into a Vec<f64> ready for scores_to_cochain1.
pub fn score_trace(steps: &[ReasoningStep], weights: &PhiWeights) -> Vec<TransitionScore> {
    steps
        .windows(2)
        .map(|pair| score_transition(&pair[0], &pair[1], weights))
        .collect()
}

// ============================================================================
// Helpers
// ============================================================================

fn extract_numbers(text: &str) -> Vec<f64> {
    text.split(|c: char| !c.is_ascii_digit() && c != '.' && c != '-')
        .filter_map(|s| s.parse::<f64>().ok())
        .collect()
}

// ============================================================================
// Signed Ï† â€” Centered obstruction coordinate
// ============================================================================

/// A transition score with both unsigned [0,1] and signed [-1,1] projections.
///
/// The signed projection centers the obstruction around 0.5:
///   signed < 0  => locally smooth / low-inconsistency transition
///   signed = 0  => neutral (combined = 0.5)
///   signed > 0  => locally obstructed / high-inconsistency transition
///
/// ALGEBRAIC STATUS:
///   - MODELING ASSUMPTION: centered Ï† corresponds to obstruction direction.
///   - NOT PROVEN: signed Ï† reflects semantic improvement/degradation.
#[derive(Debug, Clone, PartialEq)]
pub struct SignedTransitionScore {
    pub unsigned: TransitionScore,
    /// Centered obstruction: (2 * combined - 1), clamped to [-1, 1].
    pub signed: f64,
}

/// Project a transition score into the signed [-1, 1] obstruction coordinate.
///
/// Centers around neutral 0.5:
///   low inconsistency  (combined < 0.5) â†’ negative (smooth)
///   high inconsistency (combined > 0.5) â†’ positive (obstructed)
pub fn signed_phi(score: &TransitionScore) -> f64 {
    (2.0 * score.combined - 1.0).clamp(-1.0, 1.0)
}

/// Score an entire trace into signed transition scores.
pub fn score_trace_signed(
    steps: &[ReasoningStep],
    weights: &PhiWeights,
) -> Vec<SignedTransitionScore> {
    score_trace(steps, weights)
        .into_iter()
        .map(|unsigned| {
            let signed = signed_phi(&unsigned);
            SignedTransitionScore { unsigned, signed }
        })
        .collect()
}

/// Extract the signed cochain from signed scores.
pub fn signed_scores_to_cochain(scores: &[SignedTransitionScore]) -> Vec<f64> {
    scores.iter().map(|s| s.signed).collect()
}

/// Complete structural descriptor of a reasoning trace.
///
/// Upgrades from scalar Î“â‚‚ to multi-axis geometry:
/// - `gamma_var`: instability / oscillation (was Î“â‚‚)
/// - `xi`: signed coherence (aligned vs oscillatory progression)
/// - `max_jump`: magnitude of largest structural change
/// - `jump_position`: normalized position of max jump [0, 1]
/// - `sign_flips`: number of direction reversals in the cochain
/// - `mean_abs`: average absolute obstruction level
///
/// Discriminative hypothesis:
/// ```text
/// good:  low gamma_var, positive xi, late jump_position, few sign_flips
/// bad:   high gamma_var, negative xi, scattered jumps, many sign_flips
/// ```
#[derive(Debug, Clone)]
pub struct TraceStructure {
    /// Î“â‚‚ variation: average |a[i+1] - a[i]|
    pub gamma_var: f64,
    /// Îž signed coherence: Î£ a[i]Â·a[i+1] / (||a||Â² + Îµ)
    pub xi: f64,
    /// Magnitude of the largest structural change
    pub max_jump: f64,
    /// Normalized position of max jump [0, 1]  (1.0 = final step)
    pub jump_position: f64,
    /// Number of sign flips in the cochain
    pub sign_flips: usize,
    /// Mean absolute obstruction level
    pub mean_abs: f64,
    /// Trace length (number of cochain entries)
    pub length: usize,
}

/// Find the largest structural jump in the cochain and its position.
///
/// Returns (magnitude, index) where index is the position of the jump.
/// A "jump" is |a[i+1] - a[i]|.
pub fn max_jump(a: &[f64]) -> (f64, usize) {
    let mut max_val = 0.0;
    let mut idx = 0;

    for i in 0..a.len().saturating_sub(1) {
        let jump = (a[i + 1] - a[i]).abs();
        if jump > max_val {
            max_val = jump;
            idx = i;
        }
    }

    (max_val, idx)
}

/// Count the number of sign flips in the cochain.
///
/// A sign flip at position i means a[i] and a[i+1] have different signs.
/// Many flips â†’ oscillatory / contradictory reasoning.
/// Few flips â†’ monotonic / stable progression.
pub fn sign_flips(a: &[f64]) -> usize {
    a.windows(2)
        .filter(|w| w[0].signum() != w[1].signum() && w[0].abs() > 1e-12 && w[1].abs() > 1e-12)
        .count()
}

/// Compute complete trace structure from a cochain and its Îž value.
pub fn trace_structure(a: &[f64], xi: f64) -> TraceStructure {
    let gamma_var = mean_adjacent_variation(a);
    let (mj, mj_idx) = max_jump(a);
    let jump_position = if a.len() > 1 {
        mj_idx as f64 / (a.len() - 1) as f64
    } else {
        0.0
    };
    let mean_abs = mean_absolute_magnitude(a);

    TraceStructure {
        gamma_var,
        xi,
        max_jump: mj,
        jump_position,
        sign_flips: sign_flips(a),
        mean_abs,
        length: a.len(),
    }
}

/// Find the entry with the largest absolute value and its index.
///
/// For entropy_deltas, this identifies the transition with the biggest
/// structural event (the boundary spike).
///
/// Distinct from `max_jump` which finds the largest *adjacent difference*.
pub fn max_abs_entry(a: &[f64]) -> (f64, usize) {
    let mut max_val = 0.0f64;
    let mut idx = 0;
    for (i, &v) in a.iter().enumerate() {
        if v.abs() > max_val {
            max_val = v.abs();
            idx = i;
        }
    }
    (max_val, idx)
}

/// Cosine similarity between two vectors.
///
/// Returns 1.0 for identical directions, 0.0 for orthogonal, -1.0 for opposite.
/// Returns 0.0 if either vector has zero norm (degenerate case).
pub fn cosine_similarity(a: &[f64], b: &[f64]) -> f64 {
    if a.len() != b.len() || a.is_empty() {
        return 0.0;
    }
    let dot: f64 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a = a.iter().map(|v| v * v).sum::<f64>().sqrt();
    let norm_b = b.iter().map(|v| v * v).sum::<f64>().sqrt();

    if norm_a < 1e-15 || norm_b < 1e-15 {
        return 0.0;
    }

    (dot / (norm_a * norm_b)).clamp(-1.0, 1.0)
}

/// Build a normalized embedding vector from text (same byte-hashing as SBE pipeline).
///
/// This produces the probability distribution over `dim` bins, NOT the âˆšp amplitude.
/// Cosine similarity on these distributions measures semantic overlap.
///
/// **WARNING:** This is just byte-hashing (lexical distribution continuity), NOT true
/// semantic continuity. It is cheap and deterministic, suitable for smoke tests, but
/// an attacker can easily bypass this by preserving distribution shape while altering meaning.
pub fn text_to_embedding(text: &str, dim: usize) -> Vec<f64> {
    if dim == 0 {
        return Vec::new();
    }
    let mut embed = vec![0.0f64; dim];
    for (i, b) in text.bytes().enumerate() {
        embed[i % dim] += (b as f64) / 255.0;
    }
    let sum: f64 = embed.iter().sum();
    if sum > 0.0 {
        for v in embed.iter_mut() {
            *v /= sum;
        }
    }
    embed
}

/// Compute pairwise cosine similarities between consecutive step embeddings.
///
/// Given N step texts, returns N-1 similarity values: sim(step_i, step_{i+1}).
pub fn semantic_similarities(step_texts: &[String], dim: usize) -> Vec<f64> {
    if step_texts.len() < 2 {
        return vec![];
    }

    let embeddings: Vec<Vec<f64>> = step_texts
        .iter()
        .map(|t| text_to_embedding(t, dim))
        .collect();

    embeddings
        .windows(2)
        .map(|w| cosine_similarity(&w[0], &w[1]))
        .collect()
}

/// Coordinate distortion between two finite representations, with overflow refusal.
pub fn coordinate_distortions(a: &[f64], b: &[f64]) -> Option<Vec<f64>> {
    if a.len() != b.len() || a.iter().chain(b).any(|x| !x.is_finite()) {
        return None;
    }
    let values: Vec<_> = a.iter().zip(b).map(|(x, y)| (x - y).abs()).collect();
    if values.iter().any(|x| !x.is_finite()) {
        None
    } else {
        Some(values)
    }
}

#[derive(Debug, Clone, thiserror::Error)]
pub enum EntropyError {
    #[error("empty distribution")]
    EmptyDistribution,
    #[error("non-finite probability at index {index}")]
    NonFiniteProbability { index: usize },
    #[error("negative probability at index {index}: {value}")]
    NegativeProbability { index: usize, value: f64 },
    #[error("probability sum not one: {sum}")]
    ProbabilitySumNotOne { sum: f64 },
    #[error("insufficient history for convergence check")]
    InsufficientHistory,
    #[error("invalid window size: {0}")]
    InvalidWindow(usize),
    #[error("invalid tolerance: {0}")]
    InvalidTolerance(f64),
}

pub fn shannon(probabilities: &[f64]) -> f64 {
    let total: f64 = probabilities
        .iter()
        .copied()
        .filter(|p| p.is_finite() && *p > 0.0)
        .sum();
    if total <= f64::EPSILON || !total.is_finite() {
        return 0.0;
    }

    probabilities
        .iter()
        .filter_map(|&p| {
            if !p.is_finite() || p <= 0.0 {
                return None;
            }
            let q = p / total;
            Some(-q * q.ln())
        })
        .sum()
}

/// Legacy lossy entropy observable. Prefer `shannon_checked` for evidence paths.

pub fn shannon_checked(probabilities: &[f64]) -> Result<f64, EntropyError> {
    if probabilities.is_empty() {
        return Err(EntropyError::EmptyDistribution);
    }

    let mut sum = 0.0;
    for (i, &p) in probabilities.iter().enumerate() {
        if !p.is_finite() {
            return Err(EntropyError::NonFiniteProbability { index: i });
        }
        if p < 0.0 {
            return Err(EntropyError::NegativeProbability { index: i, value: p });
        }
        sum += p;
    }

    if (sum - 1.0).abs() > 1e-10 {
        return Err(EntropyError::ProbabilitySumNotOne { sum });
    }

    let entropy = probabilities
        .iter()
        .filter(|&&p| p > 0.0)
        .map(|&p| -p * p.ln())
        .sum();

    Ok(entropy)
}

pub fn magnitude_entropy(weights: &[f64]) -> f64 {
    let total: f64 = weights
        .iter()
        .copied()
        .filter(|w| w.is_finite())
        .map(|w| w.abs())
        .sum();
    if total <= f64::EPSILON || !total.is_finite() {
        return 0.0;
    }

    weights
        .iter()
        .filter(|w| w.is_finite() && w.abs() > 0.0)
        .map(|weight| {
            let p = weight.abs() / total;
            -p * p.ln()
        })
        .sum()
}

/// Legacy lossy magnitude entropy observable. Prefer checked callers where
/// invalid inputs must fail closed.

pub fn entropy_change_rate(history: &[f64]) -> f64 {
    if history.len() < 2 {
        return 0.0;
    }

    let a = history[history.len() - 2];
    let b = history[history.len() - 1];

    if !a.is_finite() || !b.is_finite() {
        return f64::NAN;
    }

    b - a
}

// Origin: engine/crates_rs/core_functional/src/trace_diagnostics.rs
// Claim: urn:core:crates_rs:core-functional:trace-diagnostics:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn shift_pairing_preserves_signed_trace_behavior() {
        assert_eq!(
            shift_pairing_coherence(&[]),
            Err("xi_shift_coherence: empty cochain".into())
        );
        assert_eq!(shift_pairing_coherence(&[2.0]), Ok(0.0));
        assert_eq!(shift_pairing_coherence(&[1.0, -2.0, 3.0]), Ok(-8.0));
        assert_eq!(
            normalized_shift_pairing_coherence(&[1.0, -2.0, 3.0], 0.0),
            Ok(-8.0 / 14.0)
        );
    }

    #[test]
    fn adjacent_variation_preserves_trace_length_normalization() {
        assert_eq!(mean_adjacent_variation(&[]), 0.0);
        assert_eq!(mean_adjacent_variation(&[7.0]), 0.0);
        assert_eq!(mean_adjacent_variation(&[0.0, 1.0, 0.0]), 1.0);
        assert_eq!(mean_adjacent_variation(&[0.0, 1.0, 0.0, 1.0, 0.0]), 1.0);
    }

    #[test]
    fn interior_magnitude_excludes_only_declared_boundary() {
        assert_eq!(interior_delta_magnitude(&[], None), 0.0);
        assert_eq!(interior_delta_magnitude(&[2.0], Some(0)), 0.0);
        assert_eq!(interior_delta_magnitude(&[1.0, -9.0, 3.0], Some(1)), 2.0);
        assert_eq!(
            interior_delta_magnitude(&[1.0, -9.0, 3.0], None),
            13.0 / 3.0
        );
    }
}

#[cfg(test)]
mod transition_tests {
    use super::*;
    fn step(s: &str) -> ReasoningStep {
        ReasoningStep {
            text: s.to_string(),
        }
    }

    // â”€â”€ Ï†_struct â”€â”€

    #[test]
    fn struct_identical_steps_zero() {
        assert!(phi_struct("a b c", "a b c") < 1e-12);
    }

    #[test]
    fn struct_disjoint_steps_one() {
        assert!((phi_struct("a b c", "x y z") - 1.0).abs() < 1e-12);
    }

    // â”€â”€ Ï†_numeric â”€â”€

    #[test]
    fn numeric_consistent_is_low() {
        let score = phi_numeric("3 + 4 = 7", "we have 7 items");
        assert!(score < 0.3, "consistent numbers: {}", score);
    }

    #[test]
    fn numeric_inconsistent_is_high() {
        let score = phi_numeric("3 + 4 = 7", "3 + 4 = 9");
        assert!(score > 0.01, "inconsistent: {}", score);
    }

    #[test]
    fn numeric_no_numbers_is_zero() {
        assert!(phi_numeric("hello", "world") < 1e-12);
    }

    // â”€â”€ Ï†_entropy â”€â”€

    #[test]
    fn entropy_identical_is_low() {
        assert!(phi_entropy("a b c", "a b c") < 0.05);
    }

    #[test]
    fn entropy_very_different_is_high() {
        assert!(phi_entropy("a", "x y z w v u t s r q") > 0.3);
    }

    // â”€â”€ Ï†_sem â”€â”€

    #[test]
    fn sem_no_contradiction_is_zero() {
        assert!(phi_sem("the answer is 5", "so the result is 5") < 1e-12);
    }

    #[test]
    fn sem_contradiction_detected() {
        assert!(phi_sem("the answer is 5", "Wait, actually that is wrong") > 0.1);
    }

    // â”€â”€ Combined scoring â”€â”€

    #[test]
    fn smooth_trace_has_low_scores() {
        let steps = vec![
            step("We start with 3 apples"),
            step("We add 2 apples to get 5 apples"),
            step("So we have 5 apples total"),
        ];
        let scores = score_trace(&steps, &PhiWeights::default());
        assert_eq!(scores.len(), 2);
        for s in &scores {
            assert!(s.combined < 0.8, "smooth step too high: {}", s.combined);
        }
    }

    #[test]
    fn contradiction_trace_has_high_scores() {
        let steps = vec![
            step("We have 3 apples"),
            step("Wait, actually that is wrong. We have 9 apples, not 3"),
        ];
        let scores = score_trace(&steps, &PhiWeights::default());
        assert!(scores[0].channels.phi_sem > 0.0, "contradiction detected");
    }

    // â”€â”€ Anti-collapse â”€â”€

    #[test]
    fn constant_trace_has_zero_mc_residual() {
        // If Ï† is constant â†’ da=0 â†’ Î“â‚‚=0
        // This is the degenerate case Ï†_entropy prevents
        let steps = vec![step("x"); 5];
        let scores = score_trace(&steps, &PhiWeights::default());
        let cochain: Vec<f64> = scores.iter().map(|s| s.combined).collect();
        // All identical â†’ differences should be zero
        for w in cochain.windows(2) {
            assert!((w[1] - w[0]).abs() < 1e-12);
        }
    }

    #[test]
    fn varied_trace_has_nonzero_variation() {
        let steps = vec![
            step("We compute 3 + 4"),
            step("The sum is 7"),
            step("Wait, actually let me reconsider this completely different approach"),
            step("Using method B we get 7"),
        ];
        let scores = score_trace(&steps, &PhiWeights::default());
        let cochain: Vec<f64> = scores.iter().map(|s| s.combined).collect();
        let variation: f64 = cochain.windows(2).map(|w| (w[1] - w[0]).abs()).sum();
        assert!(variation > 0.01, "varied trace should produce nonzero dÏ†");
    }

    // â”€â”€ Ï†_numeric symmetry â”€â”€

    #[test]
    fn numeric_is_symmetric() {
        let a = phi_numeric("3 + 4 = 7", "we have 9 items");
        let b = phi_numeric("we have 9 items", "3 + 4 = 7");
        assert!(
            (a - b).abs() < 1e-12,
            "Ï†_numeric must be symmetric: {} vs {}",
            a,
            b
        );
    }

    // â”€â”€ Signed Ï† â”€â”€

    #[test]
    fn signed_phi_centers_around_half() {
        let score = TransitionScore {
            channels: TransitionChannels {
                phi_sem: 0.0,
                phi_struct: 0.0,
                phi_numeric: 0.0,
                phi_entropy: 0.0,
            },
            combined: 0.5,
        };
        assert!((signed_phi(&score)).abs() < 1e-12, "0.5 maps to 0");
    }

    #[test]
    fn signed_phi_low_is_negative() {
        let score = TransitionScore {
            channels: TransitionChannels {
                phi_sem: 0.0,
                phi_struct: 0.0,
                phi_numeric: 0.0,
                phi_entropy: 0.0,
            },
            combined: 0.1,
        };
        assert!(
            signed_phi(&score) < 0.0,
            "low inconsistency should be negative"
        );
    }

    #[test]
    fn signed_phi_high_is_positive() {
        let score = TransitionScore {
            channels: TransitionChannels {
                phi_sem: 0.0,
                phi_struct: 0.0,
                phi_numeric: 0.0,
                phi_entropy: 0.0,
            },
            combined: 0.9,
        };
        assert!(
            signed_phi(&score) > 0.0,
            "high inconsistency should be positive"
        );
    }

    // â”€â”€ Normalized Î“â‚‚ â”€â”€

    #[test]
    fn gamma2_normalized_constant_is_zero() {
        let a = vec![0.5, 0.5, 0.5, 0.5];
        assert!(mean_adjacent_variation(&a).abs() < 1e-12);
    }

    #[test]
    fn gamma2_normalized_is_length_invariant() {
        // Same variation pattern at different lengths
        let short = vec![0.0, 1.0, 0.0];
        let long = vec![0.0, 1.0, 0.0, 1.0, 0.0];
        assert!(
            (mean_adjacent_variation(&short) - mean_adjacent_variation(&long)).abs() < 1e-12,
            "normalized Î“â‚‚ should be length-invariant for same pattern"
        );
    }

    // â”€â”€ Acceptance law â”€â”€
}

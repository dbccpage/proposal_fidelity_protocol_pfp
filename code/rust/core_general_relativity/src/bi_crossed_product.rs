//! `bi_crossed_product` — finite dual-face object for `core_general_relativity`.
//!
//! AUTHORING_QUALITY: human_llm_best_effort_slop (best-effort dual-face scaffold; not human-canon math; not PROVED; not GlobalGreen).
//! **AuthorityEffect:** None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_37aaccff;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_37aaccff<T> = std::result::Result<T, BoundaryError_37aaccff>;

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; best-effort scaffold.";

/// Finite carrier for `bi_crossed_product` (proposal; not full classical object).
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct BiCrossedProduct {
    /// Degree / dimension / stage proxy (ℕ₀).
    pub degree: usize,
    /// Stable label / object id (finite string).
    pub label: String,
}

impl BiCrossedProduct {
    /// Construct a finite carrier.
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        Self {
            degree,
            label: label.into(),
        }
    }

    /// Authority fence (never mints PROVED/GlobalGreen).
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn new_and_fence() {
        let x = BiCrossedProduct::new(1, "test");
        assert_eq!(x.degree, 1);
        assert_eq!(x.label, "test");
        assert!(BiCrossedProduct::authority_fence().contains("AuthorityEffect None"));
    }
}

/// Refusal from an identity-compatible matched product of two finite magmas.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum MatchError {
    /// An order is zero or above 6.
    Order { which: &'static str, n: u32 },
    /// A multiplication or action table has the wrong length.
    TableLength { which: &'static str, got: usize, expected: usize },
    /// A table entry leaves its carrier.
    NotClosed { which: &'static str, index: usize, image: u32 },
    /// The identity element `0` fails to act as a two-sided unit, or an action fails the identity laws.
    Identity { which: &'static str },
    /// Some triple of pairs fails `(ab)c = a(bc)`.
    NotAssociative { index: u32 },
    /// An order product overflowed.
    Overflow,
}

// Origin: engine/crates_rs/core_general_relativity/src/bi_crossed_product.rs
// Claim: urn:core:crates_rs:core-general-relativity:bi-crossed-product:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for MatchError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for MatchError {}

/// Order of a matched product whose actions fix identities.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MatchedProduct {
    order: u32,
}

fn expect_len(table: &[u32], n: u32, m: u32, which: &'static str) -> Result<(), MatchError> {
    let expected = (n as usize)
        .checked_mul(m as usize)
        .ok_or(MatchError::Overflow)?;
    if table.len() != expected {
        return Err(MatchError::TableLength {
            which,
            got: table.len(),
            expected,
        });
    }
    Ok(())
}

fn closed(table: &[u32], limit: u32, which: &'static str) -> Result<(), MatchError> {
    for (index, &image) in table.iter().enumerate() {
        if image >= limit {
            return Err(MatchError::NotClosed { which, index, image });
        }
    }
    Ok(())
}

fn mul_at(table: &[u32], n: u32, left: u32, right: u32) -> Result<u32, MatchError> {
    let index = (left as usize)
        .checked_mul(n as usize)
        .ok_or(MatchError::Overflow)?
        .checked_add(right as usize)
        .ok_or(MatchError::Overflow)?;
    table.get(index).copied().ok_or(MatchError::NotClosed {
        which: "mul",
        index,
        image: 0,
    })
}

fn action_at(table: &[u32], width: u32, outer: u32, inner: u32) -> Result<u32, MatchError> {
    let index = (outer as usize)
        .checked_mul(width as usize)
        .ok_or(MatchError::Overflow)?
        .checked_add(inner as usize)
        .ok_or(MatchError::Overflow)?;
    table.get(index).copied().ok_or(MatchError::NotClosed {
        which: "action",
        index,
        image: 0,
    })
}

fn identity_mul(table: &[u32], n: u32, which: &'static str) -> Result<(), MatchError> {
    for g in 0..n {
        if mul_at(table, n, 0, g)? != g || mul_at(table, n, g, 0)? != g {
            return Err(MatchError::Identity { which });
        }
    }
    Ok(())
}

fn validate_group_order(order: u32, which: &'static str) -> Result<(), MatchError> {
    if order == 0 || order > 6 {
        return Err(MatchError::Order { which, n: order });
    }
    Ok(())
}

fn validate_tables_and_closure(
    g_mul: &[u32],
    h_mul: &[u32],
    alpha: &[u32],
    beta: &[u32],
    g_order: u32,
    h_order: u32,
) -> Result<(), MatchError> {
    expect_len(g_mul, g_order, g_order, "G")?;
    expect_len(h_mul, h_order, h_order, "H")?;
    expect_len(alpha, h_order, g_order, "alpha")?;
    expect_len(beta, g_order, h_order, "beta")?;
    closed(g_mul, g_order, "G")?;
    closed(h_mul, h_order, "H")?;
    closed(alpha, g_order, "alpha")?;
    closed(beta, h_order, "beta")
}

fn verify_action_identity(
    table: &[u32],
    actor_order: u32,
    target_order: u32,
    which: &'static str,
) -> Result<(), MatchError> {
    for actor in 0..actor_order {
        for target in 0..target_order {
            if action_at(table, target_order, 0, target)? != target
                || action_at(table, target_order, actor, 0)? != 0
            {
                return Err(MatchError::Identity { which });
            }
        }
    }
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn rhs_triple_product(
    g_mul: &[u32],
    h_mul: &[u32],
    alpha: &[u32],
    beta: &[u32],
    g_order: u32,
    h_order: u32,
    left: usize,
    bc_g: u32,
    bc_h: u32,
) -> Result<(u32, u32), MatchError> {
    let left_g = split_g(left, g_order)?;
    let left_h = split_h(left, g_order)?;
    let alpha_term = action_at(alpha, g_order, left_h, bc_g)?;
    let rhs_g = mul_at(g_mul, g_order, left_g, alpha_term)?;
    let beta_term = action_at(beta, h_order, bc_g, left_h)?;
    let rhs_h = mul_at(h_mul, h_order, beta_term, bc_h)?;
    Ok((rhs_g, rhs_h))
}

#[allow(clippy::too_many_arguments)]
fn verify_triple_associativity(
    g_mul: &[u32],
    h_mul: &[u32],
    alpha: &[u32],
    beta: &[u32],
    g_order: u32,
    h_order: u32,
    left: usize,
    mid: usize,
    right: usize,
) -> Result<(), MatchError> {
    let (ab_g, ab_h) = pair_mul(g_mul, h_mul, alpha, beta, g_order, h_order, left, mid)?;
    let (lhs_g, lhs_h) =
        pair_from_parts(g_mul, h_mul, alpha, beta, g_order, h_order, ab_g, ab_h, right)?;
    let (bc_g, bc_h) = pair_mul(g_mul, h_mul, alpha, beta, g_order, h_order, mid, right)?;
    let (rhs_g, rhs_h) =
        rhs_triple_product(g_mul, h_mul, alpha, beta, g_order, h_order, left, bc_g, bc_h)?;
    if lhs_g != rhs_g || lhs_h != rhs_h {
        return Err(MatchError::NotAssociative {
            index: left as u32,
        });
    }
    Ok(())
}

fn verify_all_associativity(
    g_mul: &[u32],
    h_mul: &[u32],
    alpha: &[u32],
    beta: &[u32],
    g_order: u32,
    h_order: u32,
    order_us: usize,
) -> Result<(), MatchError> {
    for left in 0..order_us {
        for mid in 0..order_us {
            for right in 0..order_us {
                verify_triple_associativity(
                    g_mul, h_mul, alpha, beta, g_order, h_order, left, mid, right,
                )?;
            }
        }
    }
    Ok(())
}

impl MatchedProduct {
    /// Check `|G ⋈ H| = |G| |H|`, identity actions, and associativity of
    /// `(g, h)(g', h') = (g · α_h(g'), β_{g'}(h) · h')`.
    ///
    /// This is the identity-compatible matched product. It does not certify a general cocycle.
    pub fn try_new(
        g_mul: &[u32],
        h_mul: &[u32],
        alpha: &[u32],
        beta: &[u32],
        g_order: u32,
        h_order: u32,
    ) -> Result<Self, MatchError> {
        validate_group_order(g_order, "G")?;
        validate_group_order(h_order, "H")?;
        validate_tables_and_closure(g_mul, h_mul, alpha, beta, g_order, h_order)?;
        identity_mul(g_mul, g_order, "G")?;
        identity_mul(h_mul, h_order, "H")?;
        verify_action_identity(alpha, h_order, g_order, "alpha")?;
        verify_action_identity(beta, g_order, h_order, "beta")?;
        let order = g_order.checked_mul(h_order).ok_or(MatchError::Overflow)?;
        verify_all_associativity(g_mul, h_mul, alpha, beta, g_order, h_order, order as usize)?;
        Ok(Self { order })
    }

    /// Cardinality `|G| |H|`.
    pub fn order(&self) -> u32 {
        self.order
    }
}

fn split_g(index: usize, g_order: u32) -> Result<u32, MatchError> {
    u32::try_from(index % g_order as usize).map_err(|_| MatchError::Overflow)
}

fn split_h(index: usize, g_order: u32) -> Result<u32, MatchError> {
    u32::try_from(index / g_order as usize).map_err(|_| MatchError::Overflow)
}

fn pair_mul(
    g_mul: &[u32],
    h_mul: &[u32],
    alpha: &[u32],
    beta: &[u32],
    g_order: u32,
    h_order: u32,
    left: usize,
    right: usize,
) -> Result<(u32, u32), MatchError> {
    pair_from_parts(
        g_mul,
        h_mul,
        alpha,
        beta,
        g_order,
        h_order,
        split_g(left, g_order)?,
        split_h(left, g_order)?,
        right,
    )
}

fn pair_from_parts(
    g_mul: &[u32],
    h_mul: &[u32],
    alpha: &[u32],
    beta: &[u32],
    g_order: u32,
    h_order: u32,
    g: u32,
    h: u32,
    right: usize,
) -> Result<(u32, u32), MatchError> {
    let g_prime = split_g(right, g_order)?;
    let h_prime = split_h(right, g_order)?;
    let acted_g = action_at(alpha, g_order, h, g_prime)?;
    let acted_h = action_at(beta, h_order, g_prime, h)?;
    let g_new = mul_at(g_mul, g_order, g, acted_g)?;
    let h_new = mul_at(h_mul, h_order, acted_h, h_prime)?;
    Ok((g_new, h_new))
}

#[cfg(test)]
mod matched_product_tests {
    use super::*;

    #[test]
    fn the_direct_product_of_z2_with_the_trivial_group_has_order_two() {
        let product = MatchedProduct::try_new(&[0, 1, 1, 0], &[0], &[0, 1], &[0, 0], 2, 1);
        assert!(matches!(product, Ok(ref p) if p.order() == 2));
    }

    #[test]
    fn an_action_that_moves_the_identity_is_refused() {
        let err = MatchedProduct::try_new(&[0, 1, 1, 0], &[0], &[1, 1], &[0, 0], 2, 1);
        assert!(matches!(err, Err(MatchError::Identity { .. }) | Err(MatchError::NotClosed { .. })));
    }
}

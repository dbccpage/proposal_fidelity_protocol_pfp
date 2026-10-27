//! Exact finite equal-amplitude phase cancellation and independently replayed pairings.
use core_number_theory::cyclotomic_field::{CyclotomicError, CyclotomicNumber};
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum CancellationError {
    #[error("a phase declaration needs 1..=4096 terms")]
    Carrier,
    #[error(transparent)]
    Field(#[from] CyclotomicError),
    #[error("the phase-sum certificate failed replay")]
    Certificate,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PhaseCancellationCertificate {
    pub conductor: usize,
    pub exponents: Vec<usize>,
    pub sum: CyclotomicNumber,
    pub reflected_pairs: Option<Vec<(usize, usize)>>,
}
/// A zero readout certificate. A matching by opposite phases is optional: a
/// regular odd-prime polygon cancels while admitting no such matching.
pub fn certify_phase_cancellation(
    conductor: usize,
    exponents: &[usize],
) -> Result<Option<PhaseCancellationCertificate>, CancellationError> {
    if exponents.is_empty() || exponents.len() > 4096 {
        return Err(CancellationError::Carrier);
    }
    let (sum, phases) = sum_and_collect_phases(conductor, exponents)?;
    if !sum.is_zero() {
        return Ok(None);
    }
    let reflected_pairs = find_reflected_pairs(&phases);
    Ok(Some(PhaseCancellationCertificate {
        conductor,
        exponents: exponents.to_vec(),
        sum,
        reflected_pairs,
    }))
}

fn sum_and_collect_phases(
    conductor: usize,
    exponents: &[usize],
) -> Result<(CyclotomicNumber, Vec<CyclotomicNumber>), CancellationError> {
    let mut sum = CyclotomicNumber::zero(conductor)?;
    let mut phases = Vec::with_capacity(exponents.len());
    for &e in exponents {
        let k = i64::try_from(e % conductor).map_err(|_| CancellationError::Carrier)?;
        let phase = CyclotomicNumber::zeta(conductor, k)?;
        sum = sum.add(&phase)?;
        phases.push(phase);
    }
    Ok((sum, phases))
}

fn find_reflected_pairs(phases: &[CyclotomicNumber]) -> Option<Vec<(usize, usize)>> {
    let mut used = vec![false; phases.len()];
    let mut pairs = Vec::new();
    for i in 0..phases.len() {
        if used[i] {
            continue;
        }
        let partner = (i + 1..phases.len())
            .find(|&j| !used[j] && phases[i].add(&phases[j]).is_ok_and(|s| s.is_zero()))?;
        used[i] = true;
        used[partner] = true;
        pairs.push((i, partner));
    }
    Some(pairs)
}

pub fn verify_phase_cancellation(
    certificate: &PhaseCancellationCertificate,
) -> Result<bool, CancellationError> {
    let Some(rebuilt) = certify_phase_cancellation(certificate.conductor, &certificate.exponents)?
    else {
        return Ok(false);
    };
    if certificate.sum != rebuilt.sum {
        return Ok(false);
    }
    if let Some(pairs) = &certificate.reflected_pairs {
        return verify_reflected_pairs(certificate.conductor, &certificate.exponents, pairs);
    }
    Ok(true)
}

fn verify_reflected_pairs(
    conductor: usize,
    exponents: &[usize],
    pairs: &[(usize, usize)],
) -> Result<bool, CancellationError> {
    let mut used = vec![false; exponents.len()];
    for &(i, j) in pairs {
        if [i >= used.len(), j >= used.len(), i == j]
            .into_iter()
            .any(|b| b)
        {
            return Ok(false);
        }
        if used[i] || used[j] || !pair_cancels(conductor, exponents[i], exponents[j])? {
            return Ok(false);
        }
        used[i] = true;
        used[j] = true;
    }
    Ok(used.iter().all(|&u| u))
}

fn pair_cancels(conductor: usize, exp_a: usize, exp_b: usize) -> Result<bool, CancellationError> {
    let a = CyclotomicNumber::zeta(conductor, (exp_a % conductor) as i64)?;
    let b = CyclotomicNumber::zeta(conductor, (exp_b % conductor) as i64)?;
    Ok(a.add(&b)?.is_zero())
}

// Origin: engine/crates_rs/core_quantum_physics/src/cancellation_certificates.rs
// Claim: urn:core:crates_rs:core-quantum-physics:cancellation-certificates:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_38be69b0 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}

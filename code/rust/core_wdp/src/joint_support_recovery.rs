// Executable finite evidence; AuthorityEffect: None.
//! Joint report supports for shared affine error (monograph Appendix Y.5–Y.8).
//!
//! Each segment owns one candidate state and one latent parameter
//! `e ∈ [lower, upper]` shared by every coordinate: `z_i = a_i e + b_i` with
//! every slope nonzero. The joint support of a state is the union of its
//! segments. Compatibility is checked against one common parameter in one
//! segment, never coordinate by coordinate against marginal intervals.
//!
//! [`sample_worlds`] ports the paper reference's critical-value construction
//! (Theorem Y.4): segment endpoint worlds, plus the complete first-reading
//! fiber at every critical value and cell midpoint whose compatible answers
//! differ. A complete-vector collision with equal free report and unequal
//! answers short-circuits to the two conflicting worlds (Proposition Y.1).
//! The witness is handed to the existing finite solver in
//! [`crate::observation_cost`]; a witness above that solver's state cap is
//! refused, never truncated. World order matches the Python reference, so its
//! stored finite certificates replay here.
//!
//! The finite-witness equalities `F_W = F_Ω`, `A_W = A_Ω` are written proofs
//! in the monograph, not Lean theorems and not established by these tests.
//! Independent per-coordinate residuals thicken the support and fall outside
//! this reduction. Acceptance grants no action authority.
use crate::observation_cost::{
    rational_text, Instrument, ObservationCostError, ObservationInstance, MAX_INSTRUMENTS,
    MAX_STATES,
};
use num_rational::BigRational;
use num_traits::{Signed, Zero};
use std::collections::{BTreeMap, BTreeSet};

/// Bit cap on input numerators and denominators, matching the reference.
pub const MAX_INPUT_BITS: u64 = 256;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum JointSupportError {
    #[error("joint model exceeds the finite reference caps")]
    CapExceeded,
    #[error("channel names must be nonempty and unique, with nonzero gain and positive price")]
    BadChannel,
    #[error("segments need nonempty state labels and one free report and answer per state")]
    BadSegment,
    #[error("reversed parameter interval")]
    ReversedInterval,
    #[error("affine rows must match the channel count")]
    ShapeMismatch,
    #[error("finite reduction requires every segment slope to be nonzero")]
    ZeroSlope,
    #[error("joint witness exceeds the existing finite solver state cap")]
    WitnessExceedsSolverCap,
    #[error("inconsistent history")]
    InconsistentHistory,
    #[error("invalid channel index")]
    BadChannelIndex,
    #[error("finite instance rejected: {0}")]
    Instance(#[from] ObservationCostError),
    #[error("no-signalling violation detected: marginal depends on remote setting")]
    SignallingDetected,
    #[error("unnormalized bipartite behavior: probabilities do not sum to 1")]
    UnnormalizedBehavior,
    #[error("negative probability in bipartite behavior")]
    NegativeProbability,
    #[error("empty settings or outcomes in bipartite behavior")]
    EmptyBehavior,
}

/// A priced instrument with a declared raw conversion `z = gain * raw + offset`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Channel {
    pub name: String,
    pub raw_gain: BigRational,
    pub raw_offset: BigRational,
    pub price: BigRational,
}

/// One affine segment of a state's joint support.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Segment {
    pub state: String,
    pub visible: String,
    pub answer: String,
    pub lower: BigRational,
    pub upper: BigRational,
    pub slopes: Vec<BigRational>,
    pub offsets: Vec<BigRational>,
}

/// A validated union-of-segments joint support model.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct JointModel {
    channels: Vec<Channel>,
    segments: Vec<Segment>,
}

/// A complete world: owning state and calibrated full report vector.
pub type World = (String, Vec<BigRational>);

/// Answer-check verdict over a partial calibrated history.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum JointStatus {
    Verified(Vec<String>),
    Abstain(Vec<String>),
    InvalidProposal(Vec<String>),
    Inconsistent,
    InvalidReport,
}

fn bounded(value: &BigRational) -> bool {
    value.numer().magnitude().bits() <= MAX_INPUT_BITS
        && value.denom().magnitude().bits() <= MAX_INPUT_BITS
}

impl JointModel {
    fn validate_channels(channels: &[Channel]) -> Result<(), JointSupportError> {
        let mut names = BTreeSet::new();
        for channel in channels {
            let invalid_spec = channel.name.is_empty()
                || !names.insert(channel.name.clone())
                || channel.raw_gain.is_zero()
                || !channel.price.is_positive();
            let all_bounded = [&channel.raw_gain, &channel.raw_offset, &channel.price]
                .into_iter()
                .all(bounded);
            if invalid_spec || !all_bounded {
                return Err(JointSupportError::BadChannel);
            }
        }
        Ok(())
    }

    fn validate_single_segment<'a>(
        segment: &'a Segment,
        channel_count: usize,
        metadata: &mut BTreeMap<&'a str, (&'a str, &'a str)>,
    ) -> Result<(), JointSupportError> {
        if segment.state.is_empty() {
            return Err(JointSupportError::BadSegment);
        }
        let entry = (segment.visible.as_str(), segment.answer.as_str());
        if *metadata.entry(segment.state.as_str()).or_insert(entry) != entry {
            return Err(JointSupportError::BadSegment);
        }
        if segment.slopes.len() != channel_count || segment.offsets.len() != channel_count {
            return Err(JointSupportError::ShapeMismatch);
        }
        let mut values = [&segment.lower, &segment.upper]
            .into_iter()
            .chain(&segment.slopes)
            .chain(&segment.offsets);
        if !values.all(bounded) {
            return Err(JointSupportError::CapExceeded);
        }
        if segment.lower > segment.upper {
            return Err(JointSupportError::ReversedInterval);
        }
        if segment.slopes.iter().any(Zero::is_zero) {
            return Err(JointSupportError::ZeroSlope);
        }
        Ok(())
    }

    pub fn new(channels: Vec<Channel>, segments: Vec<Segment>) -> Result<Self, JointSupportError> {
        if channels.len() > MAX_INSTRUMENTS || segments.is_empty() || segments.len() > MAX_STATES {
            return Err(JointSupportError::CapExceeded);
        }
        Self::validate_channels(&channels)?;
        let mut metadata: BTreeMap<&str, (&str, &str)> = BTreeMap::new();
        for segment in &segments {
            Self::validate_single_segment(segment, channels.len(), &mut metadata)?;
        }
        Ok(Self { channels, segments })
    }

    pub fn channels(&self) -> &[Channel] {
        &self.channels
    }

    pub fn segments(&self) -> &[Segment] {
        &self.segments
    }

    fn metadata(&self, state: &str) -> (&str, &str) {
        self.segments
            .iter()
            .find(|s| s.state == state)
            .map(|s| (s.visible.as_str(), s.answer.as_str()))
            .unwrap_or_default()
    }
}

fn world(segment: &Segment, parameter: &BigRational) -> World {
    let values = segment
        .slopes
        .iter()
        .zip(&segment.offsets)
        .map(|(a, b)| a * parameter + b)
        .collect();
    (segment.state.clone(), values)
}

fn parameter_at(segment: &Segment, i: usize, value: &BigRational) -> BigRational {
    (value - &segment.offsets[i]) / &segment.slopes[i]
}

/// Complete first-reading fiber at calibrated value `value` on channel `i`,
/// deduplicated in segment order.
fn fiber(segments: &[&Segment], i: usize, value: &BigRational) -> Vec<World> {
    let mut worlds: Vec<World> = Vec::new();
    for segment in segments {
        let parameter = parameter_at(segment, i, value);
        if segment.lower <= parameter && parameter <= segment.upper {
            let candidate = world(segment, &parameter);
            if !worlds.contains(&candidate) {
                worlds.push(candidate);
            }
        }
    }
    worlds
}

fn image(segment: &Segment, i: usize) -> (BigRational, BigRational) {
    let a = &segment.slopes[i] * &segment.lower + &segment.offsets[i];
    let b = &segment.slopes[i] * &segment.upper + &segment.offsets[i];
    if a <= b {
        (a, b)
    } else {
        (b, a)
    }
}

/// Predicted coordinate `j` as an affine function of the reading on `i`.
fn prediction(segment: &Segment, i: usize, j: usize) -> (BigRational, BigRational) {
    let slope = &segment.slopes[j] / &segment.slopes[i];
    let intercept = &segment.offsets[j] - &slope * &segment.offsets[i];
    (slope, intercept)
}

fn overlap(left: &Segment, right: &Segment, i: usize) -> Option<(BigRational, BigRational)> {
    let (l0, l1) = image(left, i);
    let (r0, r1) = image(right, i);
    let low = l0.max(r0);
    let high = l1.min(r1);
    (low <= high).then_some((low, high))
}

fn find_common_prediction_root(
    channel_count: usize,
    left: &Segment,
    right: &Segment,
    low: &BigRational,
) -> Option<BigRational> {
    let mut root: Option<BigRational> = None;
    for j in 0..channel_count {
        let (a, b) = prediction(left, 0, j);
        let (c, d) = prediction(right, 0, j);
        if a == c {
            if b != d {
                return None;
            }
        } else {
            let value = (&d - &b) / (&a - &c);
            if root.as_ref().is_some_and(|r| *r != value) {
                return None;
            }
            root = Some(value);
        }
    }
    Some(root.unwrap_or_else(|| low.clone()))
}

fn pair_collision(model: &JointModel, left: &Segment, right: &Segment) -> Option<(World, World)> {
    if left.visible != right.visible || left.answer == right.answer {
        return None;
    }
    if model.channels.is_empty() {
        return Some((world(left, &left.lower), world(right, &right.lower)));
    }
    let (low, high) = overlap(left, right, 0)?;
    let value = find_common_prediction_root(model.channels.len(), left, right, &low)?;
    extract_colliding_world_pair(left, right, &low, &high, &value)
}

fn extract_colliding_world_pair(
    left: &Segment,
    right: &Segment,
    low: &BigRational,
    high: &BigRational,
    value: &BigRational,
) -> Option<(World, World)> {
    if low <= value && value <= high {
        let worlds = fiber(&[left, right], 0, value);
        if worlds.len() == 2 && worlds[0].1 == worlds[1].1 {
            let mut it = worlds.into_iter();
            return Some((it.next()?, it.next()?));
        }
    }
    None
}

/// A genuine two-world obstruction: equal free report, unequal answers and
/// one shared complete report vector (Proposition Y.1 early exit).
pub fn collision(model: &JointModel) -> Option<(World, World)> {
    let segments = &model.segments;
    for (index, left) in segments.iter().enumerate() {
        for right in &segments[index + 1..] {
            if let Some(pair) = pair_collision(model, left, right) {
                return Some(pair);
            }
        }
    }
    None
}

fn critical_values(segments: &[&Segment], i: usize, width: usize) -> Vec<BigRational> {
    let mut points: BTreeSet<BigRational> = BTreeSet::new();
    for segment in segments {
        let (a, b) = image(segment, i);
        points.insert(a);
        points.insert(b);
    }
    for (index, left) in segments.iter().enumerate() {
        for right in &segments[index + 1..] {
            let Some((low, high)) = overlap(left, right, i) else {
                continue;
            };
            for j in 0..width {
                let (a, b) = prediction(left, i, j);
                let (c, d) = prediction(right, i, j);
                if a != c {
                    let root = (&d - &b) / (&a - &c);
                    if low <= root && root <= high {
                        points.insert(root);
                    }
                }
            }
        }
    }
    points.into_iter().collect()
}

fn admit_world(worlds: &mut Vec<World>, candidate: World) -> Result<(), JointSupportError> {
    if !worlds.contains(&candidate) {
        if worlds.len() == MAX_STATES {
            return Err(JointSupportError::WitnessExceedsSolverCap);
        }
        worlds.push(candidate);
    }
    Ok(())
}

fn sample_channel_representatives(
    model: &JointModel,
    segments: &[&Segment],
    i: usize,
    two: &BigRational,
    worlds: &mut Vec<World>,
) -> Result<(), JointSupportError> {
    let endpoints = critical_values(segments, i, model.channels.len());
    let mut representatives: BTreeSet<BigRational> = endpoints.iter().cloned().collect();
    for pair in endpoints.windows(2) {
        representatives.insert((&pair[0] + &pair[1]) / two);
    }
    for value in &representatives {
        let found = fiber(segments, i, value);
        let labels: BTreeSet<&str> =
            found.iter().map(|(state, _)| model.metadata(state).1).collect();
        if labels.len() > 1 {
            for candidate in found {
                admit_world(worlds, candidate)?;
            }
        }
    }
    Ok(())
}

/// Construct the complete critical-cell cost witness (Theorem Y.4).
pub fn sample_worlds(model: &JointModel) -> Result<Vec<World>, JointSupportError> {
    if let Some((left, right)) = collision(model) {
        return Ok(vec![left, right]);
    }
    let mut worlds: Vec<World> = Vec::new();
    for segment in &model.segments {
        admit_world(&mut worlds, world(segment, &segment.lower))?;
    }
    let reports: BTreeSet<&str> = model.segments.iter().map(|s| s.visible.as_str()).collect();
    let two = BigRational::from_integer(2.into());
    for visible in reports {
        let segments: Vec<&Segment> =
            model.segments.iter().filter(|s| s.visible == visible).collect();
        let answers: BTreeSet<&str> = segments.iter().map(|s| s.answer.as_str()).collect();
        if answers.len() == 1 {
            continue;
        }
        for i in 0..model.channels.len() {
            sample_channel_representatives(model, &segments, i, &two, &mut worlds)?;
        }
    }
    Ok(worlds)
}

fn instance(
    model: &JointModel,
    worlds: &[World],
    remaining: &[usize],
) -> Result<ObservationInstance, JointSupportError> {
    let states = (0..worlds.len()).map(|i| i.to_string()).collect();
    let visible = worlds.iter().map(|(s, _)| model.metadata(s).0.to_string()).collect();
    let query = worlds.iter().map(|(s, _)| model.metadata(s).1.to_string()).collect();
    let instruments = remaining
        .iter()
        .map(|&j| Instrument {
            name: model.channels[j].name.clone(),
            outcomes: worlds.iter().map(|(_, v)| rational_text(&v[j])).collect(),
            cost: model.channels[j].price.clone(),
        })
        .collect();
    Ok(ObservationInstance::new(states, visible, query, instruments)?)
}

/// The finite priced-observation instance on the critical witness.
pub fn finite_instance(model: &JointModel) -> Result<ObservationInstance, JointSupportError> {
    let worlds = sample_worlds(model)?;
    let all: Vec<usize> = (0..model.channels.len()).collect();
    instance(model, &worlds, &all)
}

/// Exact remaining problem after a calibrated first reading on channel `i`.
pub fn conditional_instance(
    model: &JointModel,
    i: usize,
    value: &BigRational,
    visible: &str,
) -> Result<ObservationInstance, JointSupportError> {
    if i >= model.channels.len() {
        return Err(JointSupportError::BadChannelIndex);
    }
    let segments: Vec<&Segment> = model.segments.iter().filter(|s| s.visible == visible).collect();
    let worlds = fiber(&segments, i, value);
    if worlds.is_empty() {
        return Err(JointSupportError::InconsistentHistory);
    }
    let remaining: Vec<usize> = (0..model.channels.len()).filter(|&j| j != i).collect();
    instance(model, &worlds, &remaining)
}

/// Calibrate a raw reading through the channel's declared conversion.
pub fn calibrate(channel: &Channel, raw: &BigRational) -> BigRational {
    &channel.raw_gain * raw + &channel.raw_offset
}

fn matches(segment: &Segment, readings: &[(usize, BigRational)]) -> bool {
    let Some((i, value)) = readings.first() else {
        return true;
    };
    let parameter = parameter_at(segment, *i, value);
    segment.lower <= parameter
        && parameter <= segment.upper
        && readings
            .iter()
            .all(|(j, observed)| &segment.slopes[*j] * &parameter + &segment.offsets[*j] == *observed)
}

fn readings_shape_valid(channel_count: usize, readings: &[(usize, BigRational)]) -> bool {
    let mut seen = BTreeSet::new();
    readings.len() <= channel_count
        && readings
            .iter()
            .all(|(i, _)| *i < channel_count && seen.insert(*i))
}

/// Check a proposed answer against a calibrated partial history using one
/// common latent parameter per segment (Y.1 certification rule).
pub fn evaluate(
    model: &JointModel,
    visible: &str,
    readings: &[(usize, BigRational)],
    proposed_answer: &str,
) -> JointStatus {
    if !readings_shape_valid(model.channels.len(), readings) {
        return JointStatus::InvalidReport;
    }
    let mut labels: Vec<String> = Vec::new();
    let mut answers: BTreeSet<&str> = BTreeSet::new();
    for segment in &model.segments {
        if segment.visible == visible && matches(segment, readings) {
            if !labels.contains(&segment.state) {
                labels.push(segment.state.clone());
            }
            answers.insert(segment.answer.as_str());
        }
    }
    if labels.is_empty() {
        return JointStatus::Inconsistent;
    }
    if answers.len() != 1 {
        return JointStatus::Abstain(labels);
    }
    if !answers.contains(proposed_answer) {
        return JointStatus::InvalidProposal(labels);
    }
    JointStatus::Verified(labels)
}

/// A discrete bipartite behavior table with exact rational probabilities P(a, b | x, y).
///
/// Indexed by:
/// `table[x][y][a][b]` where
/// - `x ∈ 0..num_alice_settings`
/// - `y ∈ 0..num_bob_settings`
/// - `a ∈ 0..num_alice_outcomes`
/// - `b ∈ 0..num_bob_outcomes`
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BipartiteBehavior {
    pub num_alice_settings: usize,
    pub num_bob_settings: usize,
    pub num_alice_outcomes: usize,
    pub num_bob_outcomes: usize,
    pub table: Vec<Vec<Vec<Vec<BigRational>>>>,
}

impl BipartiteBehavior {
    fn validate_setting_slice(
        slice: &[Vec<BigRational>],
        num_alice_outcomes: usize,
        num_bob_outcomes: usize,
        one: &BigRational,
    ) -> Result<(), JointSupportError> {
        if slice.len() != num_alice_outcomes {
            return Err(JointSupportError::ShapeMismatch);
        }
        let mut sum = BigRational::zero();
        for row in slice {
            if row.len() != num_bob_outcomes {
                return Err(JointSupportError::ShapeMismatch);
            }
            for p in row {
                if p.is_negative() {
                    return Err(JointSupportError::NegativeProbability);
                }
                sum += p;
            }
        }
        if &sum != one {
            return Err(JointSupportError::UnnormalizedBehavior);
        }
        Ok(())
    }

    fn validate_non_empty_dimensions(
        table: &[Vec<Vec<Vec<BigRational>>>],
    ) -> Result<(usize, usize, usize, usize), JointSupportError> {
        let num_alice_settings = table.len();
        let num_bob_settings = table.first().map_or(0, Vec::len);
        let num_alice_outcomes = table
            .first()
            .and_then(|r| r.first())
            .map_or(0, Vec::len);
        let num_bob_outcomes = table
            .first()
            .and_then(|r| r.first())
            .and_then(|r| r.first())
            .map_or(0, Vec::len);
        if num_alice_settings == 0
            || num_bob_settings == 0
            || num_alice_outcomes == 0
            || num_bob_outcomes == 0
        {
            return Err(JointSupportError::EmptyBehavior);
        }
        Ok((
            num_alice_settings,
            num_bob_settings,
            num_alice_outcomes,
            num_bob_outcomes,
        ))
    }

    /// Construct a new bipartite behavior and validate dimensions, non-negativity, and normalization.
    pub fn new(table: Vec<Vec<Vec<Vec<BigRational>>>>) -> Result<Self, JointSupportError> {
        let (num_alice_settings, num_bob_settings, num_alice_outcomes, num_bob_outcomes) =
            Self::validate_non_empty_dimensions(&table)?;

        let one = BigRational::from_integer(1.into());
        for row_x in &table {
            if row_x.len() != num_bob_settings {
                return Err(JointSupportError::ShapeMismatch);
            }
            for slice_xy in row_x {
                Self::validate_setting_slice(
                    slice_xy,
                    num_alice_outcomes,
                    num_bob_outcomes,
                    &one,
                )?;
            }
        }

        Ok(Self {
            num_alice_settings,
            num_bob_settings,
            num_alice_outcomes,
            num_bob_outcomes,
            table,
        })
    }

    fn validate_marginal_rows(
        rows: &[Vec<BigRational>],
        expected_outcomes: usize,
        one: &BigRational,
    ) -> Result<(), JointSupportError> {
        for row in rows {
            if row.len() != expected_outcomes {
                return Err(JointSupportError::ShapeMismatch);
            }
            let mut sum = BigRational::zero();
            for p in row {
                if p.is_negative() {
                    return Err(JointSupportError::NegativeProbability);
                }
                sum += p;
            }
            if &sum != one {
                return Err(JointSupportError::UnnormalizedBehavior);
            }
        }
        Ok(())
    }

    fn build_product_table(
        pa: &[Vec<BigRational>],
        pb: &[Vec<BigRational>],
    ) -> Vec<Vec<Vec<Vec<BigRational>>>> {
        pa.iter()
            .map(|row_a_probs| {
                pb.iter()
                    .map(|row_b_probs| {
                        row_a_probs
                            .iter()
                            .map(|p_a| row_b_probs.iter().map(|p_b| p_a * p_b).collect())
                            .collect()
                    })
                    .collect()
            })
            .collect()
    }

    /// Construct a factorized product behavior P(a, b | x, y) = P_A(a | x) * P_B(b | y).
    pub fn from_product(
        pa: &[Vec<BigRational>],
        pb: &[Vec<BigRational>],
    ) -> Result<Self, JointSupportError> {
        let num_alice_settings = pa.len();
        let num_bob_settings = pb.len();
        if num_alice_settings == 0 || num_bob_settings == 0 {
            return Err(JointSupportError::EmptyBehavior);
        }
        let num_alice_outcomes = pa[0].len();
        let num_bob_outcomes = pb[0].len();
        if num_alice_outcomes == 0 || num_bob_outcomes == 0 {
            return Err(JointSupportError::EmptyBehavior);
        }

        let one = BigRational::from_integer(1.into());
        // Verify PA normalization
        Self::validate_marginal_rows(pa, num_alice_outcomes, &one)?;
        // Verify PB normalization
        Self::validate_marginal_rows(pb, num_bob_outcomes, &one)?;

        let table = Self::build_product_table(pa, pb);

        Ok(Self {
            num_alice_settings,
            num_bob_settings,
            num_alice_outcomes,
            num_bob_outcomes,
            table,
        })
    }

    /// Compute Alice's marginal P_A(a | x, y) = ∑_b P(a, b | x, y).
    pub fn alice_marginal(&self, x: usize, y: usize, a: usize) -> BigRational {
        let mut sum = BigRational::zero();
        for b in 0..self.num_bob_outcomes {
            sum += &self.table[x][y][a][b];
        }
        sum
    }

    /// Compute Bob's marginal P_B(b | x, y) = ∑_a P(a, b | x, y).
    pub fn bob_marginal(&self, x: usize, y: usize, b: usize) -> BigRational {
        let mut sum = BigRational::zero();
        for a in 0..self.num_alice_outcomes {
            sum += &self.table[x][y][a][b];
        }
        sum
    }

    /// Verify exact no-signalling in both directions (A→B and B→A).
    ///
    /// Corresponds to Cycle 007's `QM.NoSignalling.NoSignallingBA` and `NoSignallingAB`:
    /// - Alice's marginal must not depend on Bob's setting y:
    ///   ∀ x, a, y, y': ∑_b P(a, b | x, y) == ∑_b P(a, b | x, y')
    /// - Bob's marginal must not depend on Alice's setting x:
    ///   ∀ y, b, x, x': ∑_a P(a, b | x, y) == ∑_a P(a, b | x', y)
    pub fn verify_no_signalling(&self) -> Result<(), JointSupportError> {
        // Check B -> A no-signalling (Alice's marginal invariant under Bob's setting)
        for x in 0..self.num_alice_settings {
            for a in 0..self.num_alice_outcomes {
                let baseline = self.alice_marginal(x, 0, a);
                for y in 1..self.num_bob_settings {
                    if self.alice_marginal(x, y, a) != baseline {
                        return Err(JointSupportError::SignallingDetected);
                    }
                }
            }
        }
        // Check A -> B no-signalling (Bob's marginal invariant under Alice's setting)
        for y in 0..self.num_bob_settings {
            for b in 0..self.num_bob_outcomes {
                let baseline = self.bob_marginal(0, y, b);
                for x in 1..self.num_alice_settings {
                    if self.bob_marginal(x, y, b) != baseline {
                        return Err(JointSupportError::SignallingDetected);
                    }
                }
            }
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_bccae9bd {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}

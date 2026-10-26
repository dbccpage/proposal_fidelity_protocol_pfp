//! The **Omega engine**: a fold with four holes.
//!
//! `AuthorityEffect: None.`
//!
//! Source: crosstab §11.3 (the cycle with the gates in order), §11.7 (the
//! four architectural facts), §11.8 (the conformance checklist); Lean
//! `represented_progress`, `rule1_repair_or_extension`; the sealed
//! `build_tree` for the shape of a round.
//!
//! A declared local engine. No minimality theorem over engines or typed
//! correspondence to the cited Lean represented world is established.
//!
//! **What it does by itself, every round:**
//!
//! 1. replays the history from genesis and fingerprints the state (E8);
//! 2. observes: recomputes profiles, finds the violated requirements (E2);
//! 3. for the first violated, unrefused requirement, enumerates the
//!    declared menu — unpruned, within the bounds (block D);
//! 4. evaluates: the repair family, split into rule-1 repairs and rule-2
//!    augmentations, and kept split (§11.2);
//! 5. if the family is empty, emits the exhaustion certificate and records
//!    a refusal, which does not stop the run (E5, E7);
//! 6. prices every member under every declared measure (block G);
//! 7. quotients the minima by the canonical key and **retains every tied
//!    class** (E9, E10);
//! 8. gates: budget for rule 1, licence for rule 2 (E6);
//! 9. admits the response as an event, never by mutation (E1);
//! 10. certifies by replay and records the move with its support, price,
//!     role and scope (block I).
//!
//! **What it asks the outside for, and only these** (`outside.rs`): a
//! demand when nothing is violated and the closure policy has nothing to
//! reissue; a presentation when there is no demand; a choice when more than
//! one class is tied; a licence when the chosen class creates structure;
//! fuel when the budget is spent.  Every answer is recorded as an event.
//!
//! **What it never does:** invents a demand (OB-1), picks among ties
//! (`CL-NO-UNIVERSAL-PROPERTY`), authorizes itself, funds itself, reads a
//! truncated search as an obstruction, or reports a terminal without its
//! scope. The silent, closure-disabled fixtures make no response moves;
//! this is not a nonexistence theorem about event generators.
//!
//! The dispatch bound assumes callbacks and bounded searches return.
//! Checklist flags summarize construction, not independent verification.

use std::collections::BTreeMap;

use crate::bounds::Bounds;
use crate::candidate::{delta_events, is_structure_creating, Delta};
use crate::canonical::try_canonical;
use crate::certificate::Certificate;
use crate::closure::closure_challenge_orbits;
use crate::event::Event;
use crate::hash::regime_fingerprint;
use crate::mark::Pair;
use crate::measure::{Cost, Measure, MeasureKind};
use crate::menu::menu;
use crate::minima::{try_quotient, Class, MinResponses};
use crate::obstruction::obstructed;
use crate::outside::{Outside, Proposal};
use crate::panel::{cert_pos, Evaluator};
use crate::renaming::Key;
use crate::repair::repair_family;
use crate::role::{role, Role};
use crate::scope::Scope;
use crate::separability::{collapsed_pairs, witness};
use crate::support::Support;
use crate::terminal::{DeclaredTerminalizer, RunVerdict, Terminalizer, Terminated};
use crate::world::{Verdict, World, WorldEvent};

/// Where a demand came from.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DemandOrigin {
    /// The requirement was already recorded.
    Recorded,
    /// The declared closure policy reissued it.
    ClosurePolicy,
    /// The outside asked.
    Outside,
}

/// What happened at the gate.
#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Gate {
    /// The response was admitted.
    Passed,
    /// The family was empty; a refusal was recorded with its certificate.
    Obstructed,
    /// More than one class and the outside declined to choose.
    TieRetained,
    /// The licence was withheld for a structure-creating class.
    LicenceWithheld,
    /// The budget was spent and no more was funded.
    BudgetExhausted,
}

/// The engine's configuration.  Declared, and carried into the scope.
#[derive(Clone, Debug)]
pub struct Config {
    /// The candidate bounds.
    pub bounds: Bounds,
    /// The measures; the first breaks ties for the quotient the outside
    /// chooses from, and all are priced.
    pub measures: Vec<MeasureKind>,
    /// The round bound.
    pub max_rounds: usize,
    /// Outer dispatch limit, including outside demands and presentations.
    /// Assumes each callback and each bounded computation returns.
    pub max_steps: usize,
    /// Whether the declared closure policy may reissue demands.
    pub closure_policy: bool,
    /// The declared panel, if any; `None` means the full evaluator.
    pub panel: Option<Vec<Evaluator>>,
    /// The reading name, for the scope.
    pub reading: String,
}

impl Config {
    /// The sealed defaults for a reading.
    pub fn sealed(reading: &str) -> Config {
        Config {
            bounds: Bounds::default(),
            measures: MeasureKind::ALL.to_vec(),
            max_rounds: 15,
            max_steps: 512,
            closure_policy: true,
            panel: None,
            reading: reading.to_string(),
        }
    }
}

/// One recorded move.
#[derive(Clone, Debug)]
pub struct Move {
    /// Round number, from 1.
    pub round: usize,
    /// The requirement answered.
    pub target: Pair,
    /// Where the demand came from.
    pub origin: DemandOrigin,
    /// Menu size — every item examined.
    pub menu_size: usize,
    /// Rule-1 members of the family.
    pub repairs: usize,
    /// Rule-2 members of the family.
    pub augmentations: usize,
    /// Per measure: minimum cost and how many classes tie there.
    pub prices: Vec<(MeasureKind, Cost, usize)>,
    /// The retained classes under the tie-break measure.
    pub classes: Vec<Class>,
    /// Which class the outside chose, if any.
    pub chosen: Option<usize>,
    /// The gate verdict.
    pub gate: Gate,
    /// The role of the accepted response.
    pub role: Option<Role>,
    /// The certificate this move rests on.
    pub certificate: Option<Certificate>,
    /// Fingerprint before.
    pub fp_before: u64,
    /// Fingerprint after.
    pub fp_after: u64,
    /// History length after this move, for replay verification.
    pub history_len: usize,
    /// The support after this move.
    pub support: Support,
}

/// The report of a run.
#[derive(Clone, Debug)]
pub struct Report {
    /// The full represented history.
    pub history: Vec<WorldEvent>,
    /// The moves.
    pub moves: Vec<Move>,
    /// The terminal, with scope and certificate.
    pub terminated: Terminated,
    /// The final fingerprint.
    pub fingerprint: u64,
    /// Final key, absent when the declared permutation budget was exceeded.
    pub key: Option<Key>,
    /// Collapsed pairs at the end that nothing asked about: the blind spot.
    pub blind_spot: Vec<Pair>,
    /// One witness per satisfied requirement.
    pub witnesses: Vec<(Pair, String)>,
    /// What the run did not claim.
    pub not_claimed: Vec<String>,
    /// The conformance checklist of §11.8.
    pub checklist: Vec<(String, bool)>,
}

impl Report {
    /// Verify replay checkpoints and final state-derived fields, not
    /// independently recomputed prices/classes, before-fingerprints,
    /// attribution, panel, or terminal declaration payload.
    pub fn verify(&self, bounds: &Bounds) -> Result<(), String> {
        bounds.validate()?;
        if *bounds != self.terminated.scope.bounds {
            return Err("replay bounds differ from the recorded scope".into());
        }
        let mut previous = 0;
        for m in &self.moves {
            let prefix = self.history.get(..m.history_len).ok_or("move checkpoint exceeds history")?;
            if m.history_len < previous { return Err("move checkpoints are not ordered".into()); }
            previous = m.history_len;
            let (w, verdicts) = World::replay(prefix, bounds);
            if verdicts.iter().any(|v| matches!(v, Verdict::Refused(_))) {
                return Err("refused event in move history".into());
            }
            let fp = regime_fingerprint(&w.regime);
            if fp != m.fp_after {
                return Err(format!("round {}: recorded {:016x}, replayed {fp:016x}", m.round, m.fp_after));
            }
            if Support::of(&w) != m.support {
                return Err(format!("round {}: support differs on replay", m.round));
            }
        }
        let (w, verdicts) = World::replay(&self.history, bounds);
        if verdicts.iter().any(|v| matches!(v, Verdict::Refused(_))) {
            return Err("refused event in final history".into());
        }
        if regime_fingerprint(&w.regime) != self.fingerprint {
            return Err("final fingerprint differs on replay".into());
        }
        if try_canonical(&w.regime).ok() != self.key {
            return Err("final canonical key differs".into());
        }
        let blind: Vec<Pair> = collapsed_pairs(&w.regime).into_iter().filter(|p| !w.regime.reqs.contains(p)).collect();
        let witnesses: Vec<(Pair, String)> = w.regime.reqs.iter().filter_map(|p|
            witness(&w.regime, p.i, p.j).map(|c| (*p, format!("form {} slots {:?}", c.form, c.slots)))).collect();
        if blind != self.blind_spot || witnesses != self.witnesses {
            return Err("final blind spot or witnesses differ".into());
        }
        if self.terminated.terminal == crate::terminal::Terminal::Accepted
            && (w.regime.reqs.is_empty() || !w.quiescent()) {
            return Err("acceptance lacks nonempty satisfied requirements".into());
        }
        Ok(())
    }
}

/// The engine.
pub struct Omega<O: Outside> {
    /// The outside.
    pub outside: O,
    /// The configuration.
    pub config: Config,
}

impl<O: Outside> Omega<O> {
    /// Build.
    pub fn new(outside: O, config: Config) -> Omega<O> {
        Omega { outside, config }
    }

    fn scope(&self, population: &str) -> Scope {
        Scope {
            reading: self.config.reading.clone(),
            bounds: self.config.bounds,
            measures: self.config.measures.clone(),
            population: population.to_string(),
            notes: vec![
                "rule-free base at every round (the rule-removal lemma keeps it so)".into(),
                format!("round bound {}", self.config.max_rounds),
                format!("outer dispatch bound {}", self.config.max_steps),
                if self.config.closure_policy { "closure policy enabled".into() } else { "closure policy disabled".into() },
            ],
        }
    }

    fn panel_for(&self, regime: &crate::regime::Regime) -> Vec<Evaluator> {
        self.config.panel.clone().unwrap_or_else(|| vec![Evaluator::full(regime)])
    }

    /// Run from a genesis history until a terminal.
    pub fn run(&mut self, genesis: &[Event]) -> Report {
        let bounds = self.config.bounds;
        let config_error = bounds.validate().err().or_else(||
            self.config.measures.is_empty().then(|| "at least one measure is required".to_string()));
        let mut history: Vec<WorldEvent> = genesis.iter().cloned().map(WorldEvent::Carrier).collect();
        let mut moves: Vec<Move> = Vec::new();
        let terminalizer = DeclaredTerminalizer;
        // The outside's opening declarations are recorded, whatever they are.
        let (w0, _) = World::replay(&history, &bounds);
        let fuel = self.outside.fund(&w0.regime);
        history.push(WorldEvent::SetBudget(fuel));
        history.push(WorldEvent::SetLicense(false));
        let mut round = 0usize;
        // Who imposed each requirement.  A requirement in the genesis history
        // is `Recorded`; everything else is attributed at the moment it is
        // pushed, so the report says where each demand came in.
        let mut origins: BTreeMap<Pair, DemandOrigin> = BTreeMap::new();
        let mut steps = 0;
        let verdict: RunVerdict = 'engine: loop {
            if let Some(reason) = &config_error {
                break RunVerdict::InvalidInput { reason: reason.clone() };
            }
            let (world, verdicts) = World::replay(&history, &bounds);
            if !world.regime.rules.is_empty() {
                break RunVerdict::InvalidInput { reason: "Omega requires a rule-free carrier".into() };
            }
            if let Some(Verdict::Refused(reason)) = verdicts.iter().find(|v| matches!(v, Verdict::Refused(_))) {
                break RunVerdict::InvalidInput { reason: format!("invalid history: {reason}") };
            }
            if steps >= self.config.max_steps {
                break RunVerdict::OutOfBudget { which: "outer dispatch bound".into() };
            }
            steps += 1;
            let fp_before = regime_fingerprint(&world.regime);
            // 2. observe
            let violated: Vec<Pair> = world.violated().into_iter().filter(|p| !world.refused(*p)).collect();
            let (target, origin) = match violated.first() {
                Some(&p) => (p, origins.get(&p).copied().unwrap_or(DemandOrigin::Recorded)),
                None => {
                    if !world.violated().is_empty() {
                        // Everything left is refused.
                        let cert = world.refusals[0].certificate.clone();
                        break RunVerdict::Obstructed { certificate: cert };
                    }
                    if self.config.closure_policy {
                        match closure_challenge_orbits(&world.regime) {
                          Ok(orbits) => {
                            if let Some(&p) = orbits.first() {
                                history.push(WorldEvent::Carrier(Event::Impose(p)));
                                origins.insert(p, DemandOrigin::ClosurePolicy);
                                continue;
                            }
                          }
                          Err(e) => break RunVerdict::OutOfBudget { which: format!("closure search: {e}") },
                        }
                    }
                    if let Some(p) = self.outside.demand(&world.regime) {
                        if p.i >= p.j || !world.regime.has_mark(p.i) || !world.regime.has_mark(p.j) {
                            break RunVerdict::InvalidInput { reason: "outside demand is not an admitted ordered pair".into() };
                        }
                        if !world.regime.reqs.contains(&p) {
                            history.push(WorldEvent::Carrier(Event::Impose(p)));
                            origins.insert(p, DemandOrigin::Outside);
                            continue;
                        }
                    }
                    if let Some(tok) = self.outside.present(&world.regime) {
                        history.push(WorldEvent::Carrier(Event::Supply(tok.clone())));
                        history.push(WorldEvent::Carrier(Event::AdmitDatum(tok)));
                        continue;
                    }
                    // Quiescent and silent.
                    if world.regime.reqs.is_empty() {
                        break RunVerdict::NothingAsked;
                    }
                    let panel = self.panel_for(&world.regime);
                    let blind: Vec<Pair> = world.regime.reqs.iter().copied().filter(|p| !cert_pos(&panel, &world.regime, *p)).collect();
                    if !blind.is_empty() {
                        break RunVerdict::PanelBlind { pairs: blind };
                    }
                    let witnesses = world
                        .regime
                        .reqs
                        .iter()
                        .map(|p| (*p, witness(&world.regime, p.i, p.j).map_or("none".to_string(), |c| format!("{c:?}"))))
                        .collect();
                    break RunVerdict::Quiescent { witnesses };
                }
            };
            if round >= self.config.max_rounds {
                break RunVerdict::OutOfBudget { which: "round bound".into() };
            }
            round += 1;
            // 3–5. menu, family, obstruction
            let m = menu(&world.regime, &bounds);
            let fam = repair_family(&world.regime, target, &m);
            let base_move = |gate: Gate, cert: Option<Certificate>, classes: Vec<Class>, chosen: Option<usize>, prices: Vec<(MeasureKind, Cost, usize)>, w: &World, hist_len: usize, role: Option<Role>| Move {
                round,
                target,
                origin,
                menu_size: fam.examined,
                repairs: fam.repairs().len(),
                augmentations: fam.augmentations().len(),
                prices,
                classes,
                chosen,
                gate,
                role,
                certificate: cert,
                fp_before,
                fp_after: regime_fingerprint(&w.regime),
                history_len: hist_len,
                support: Support::of(w),
            };
            if fam.members.is_empty() {
                let cert = obstructed(&world.regime, target, &m).expect("empty family on a violated target is an obstruction");
                history.push(WorldEvent::Refuse { target, certificate: cert.clone() });
                let (w1, v) = World::replay(&history, &bounds);
                debug_assert!(matches!(v.last(), Some(Verdict::Applied)));
                moves.push(base_move(Gate::Obstructed, Some(cert), Vec::new(), None, Vec::new(), &w1, history.len(), None));
                continue; // non-absorbing
            }
            // 6–7. price under every measure; quotient; retain ties
            let mut prices: Vec<(MeasureKind, Cost, usize)> = Vec::new();
            let mut classes_by_measure: BTreeMap<MeasureKind, Vec<Class>> = BTreeMap::new();
            for &mk in &self.config.measures {
                let best = fam.members.iter().map(|d| mk.cost(d)).min().unwrap();
                let deltas: Vec<Delta> = fam.members.iter().filter(|d| mk.cost(d) == best).cloned().collect();
                let mr = MinResponses { measure: mk, cost: best, deltas, complete_within: bounds };
                let classes = match try_quotient(&world.regime, target, &mr) {
                    Ok(classes) => classes,
                    Err(e) => break 'engine RunVerdict::OutOfBudget { which: format!("quotient search: {e}") },
                };
                prices.push((mk, best, classes.len()));
                classes_by_measure.insert(mk, classes);
            }
            let tie_measure = self.config.measures[0];
            let classes = classes_by_measure.remove(&tie_measure).unwrap();
            let chosen = if classes.len() == 1 { Some(0) } else { self.outside.choose(&classes) };
            let Some(k) = chosen else {
                moves.push(base_move(Gate::TieRetained, None, classes.clone(), None, prices, &world, history.len(), None));
                break RunVerdict::TieRetained { classes: classes.len() };
            };
            let Some(class) = classes.get(k) else {
                break RunVerdict::InvalidInput { reason: "outside choice exceeds retained classes".into() };
            };
            let delta = class.representative.clone();
            let proposal = Proposal {
                target,
                delta: delta.clone(),
                structure_creating: is_structure_creating(&delta),
                prices: self.config.measures.iter().map(|mk| (*mk, mk.cost(&delta))).collect(),
                tie_classes: classes.len(),
            };
            // 8. gates
            if !world.budget.can_pay() {
                let more = self.outside.fund(&world.regime);
                if more == 0 {
                    moves.push(base_move(Gate::BudgetExhausted, None, classes.clone(), Some(k), prices, &world, history.len(), None));
                    break RunVerdict::OutOfBudget { which: "fuel".into() };
                }
                history.push(WorldEvent::SetBudget(more));
            }
            if proposal.structure_creating && !world.license.granted() {
                if self.outside.authorize(&proposal) {
                    history.push(WorldEvent::SetLicense(true));
                } else {
                    moves.push(base_move(Gate::LicenceWithheld, None, classes.clone(), Some(k), prices, &world, history.len(), None));
                    break RunVerdict::LicenceWithheld;
                }
            }
            // 9–10. admit as an event; certify by replay; record
            history.push(WorldEvent::Respond { target, delta: delta.clone() });
            let (w1, verdicts) = World::replay(&history, &bounds);
            match verdicts.last() {
                Some(Verdict::Applied) => {}
                other => panic!("an evaluated, gated response was refused on replay: {other:?}"),
            };
            let events = delta_events(&world.regime, &delta);
            let cert = Certificate::Witness {
                object: crate::certificate::ObjectId(format!("{} ({} event(s))", crate::role::delta_label(&world.regime, &delta), events.len())),
                check: crate::certificate::CheckId("response_valid_naive on replay".into()),
            };
            let r = role(false, &delta);
            moves.push(base_move(Gate::Passed, Some(cert), classes.clone(), Some(k), prices, &w1, history.len(), Some(r)));
        };
        // Terminalize with scope.
        let (world, _) = World::replay(&history, &bounds);
        let population = format!("{} data, {} forms, {} requirement(s), {} refusal(s)", world.regime.n_data(), world.regime.n_forms(), world.regime.reqs.len(), world.refusals.len());
        let mut terminated = terminalizer.terminalize(&verdict, &self.scope(&population));
        let blind_spot: Vec<Pair> = collapsed_pairs(&world.regime).into_iter().filter(|p| !world.regime.reqs.contains(p)).collect();
        let witnesses: Vec<(Pair, String)> = world
            .regime
            .reqs
            .iter()
            .filter_map(|p| witness(&world.regime, p.i, p.j).map(|c| (*p, format!("form {} slots {:?}", c.form, c.slots))))
            .collect();
        let fingerprint = regime_fingerprint(&world.regime);
        let key = match try_canonical(&world.regime) {
            Ok(key) => Some(key),
            Err(e) => {
                terminated = terminalizer.terminalize(&RunVerdict::OutOfBudget {
                    which: format!("final canonical search: {e}")
                }, &self.scope(&population));
                None
            }
        };
        let history_has = |f: &dyn Fn(&WorldEvent) -> bool| history.iter().any(f);
        let not_claimed = vec![
            "no demand was generated by the object language; every requirement came from the outside or from the declared closure policy, and the origin is recorded per move (OB-1)".into(),
            "no class was preferred; where more than one tied, the outside chose or the run stopped (CL-NO-UNIVERSAL-PROPERTY)".into(),
            "no obstruction was declared without an exhaustion certificate over the declared menu (incomplete_search_false_alarm)".into(),
            "no terminal is reported without the scope it was certified under (FW-SCOPE)".into(),
            "the fingerprint is FNV-1a over this crate's serialisation, not the sealed SHA-256, and compares only with itself".into(),
            "minimality is relative to the declared bounds; nothing is claimed beyond them (L10)".into(),
        ];
        let checklist = vec![
            ("genesis, full event history, and a replay whose fingerprint matches".to_string(), true),
            ("the declared observer panel and its printed blind spot".to_string(), true),
            ("per obstruction: the requirement, the menu size, the exhaustion certificate".to_string(), moves.iter().filter(|m| m.gate == Gate::Obstructed).all(|m| m.certificate.is_some())),
            ("repair family and augmentation proposals kept apart".to_string(), true),
            ("every price under every declared measure".to_string(), moves.iter().filter(|m| m.gate != Gate::Obstructed).all(|m| m.prices.len() == self.config.measures.len())),
            ("every tied minimum retained and named".to_string(), moves.iter().filter(|m| m.gate != Gate::Obstructed).all(|m| !m.classes.is_empty())),
            ("the canonical key of the final state".to_string(), key.is_some()),
            ("budget and licence as events in the history, not parameters".to_string(), history_has(&|e| matches!(e, WorldEvent::SetBudget(_))) && history_has(&|e| matches!(e, WorldEvent::SetLicense(_)))),
            ("every refusal with its certificate, and the run continuing past it".to_string(), world.refusals.iter().all(|r| matches!(r.certificate, Certificate::Exhaustion { .. }))),
            ("on success: the witnesses, not 'no defect found'".to_string(), terminated.terminal != crate::terminal::Terminal::Accepted || !witnesses.is_empty()),
            ("a statement of what the run did not claim".to_string(), true),
        ];
        Report { history, moves, terminated, fingerprint, key, blind_spot, witnesses, not_claimed, checklist }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::outside::{Scripted, Silent};
    use crate::reading::{READING_F, READING_L};
    use crate::replay::replay;
    use crate::terminal::Terminal;

    struct AdversarialOutside { mode: usize, presentations: usize }
    impl Outside for AdversarialOutside {
        fn present(&mut self, _: &crate::regime::Regime) -> Option<crate::token::Token> {
            if self.mode > 1 { return None; }
            self.presentations += 1;
            Some(crate::token::Token::new(if self.mode == 0 { "repeat".into() }
                else { format!("fresh{}", self.presentations) }))
        }
        fn demand(&mut self, _: &crate::regime::Regime) -> Option<Pair> {
            (self.mode == 2).then_some(Pair { i: crate::mark::Mark(1), j: crate::mark::Mark(0) })
        }
        fn choose(&mut self, _: &[Class]) -> Option<usize> { Some(usize::MAX) }
        fn authorize(&mut self, _: &Proposal) -> bool { true }
        fn fund(&mut self, _: &crate::regime::Regime) -> u32 { 10 }
    }

    #[test]
    fn presentation_dispatches_are_bounded_even_without_response_rounds() {
        let mut cfg = Config::sealed("input-loop regression");
        cfg.closure_policy = false;
        cfg.max_steps = 6;
        let mut engine = Omega::new(AdversarialOutside { mode: 0, presentations: 0 }, cfg);
        let report = engine.run(&[]);
        assert_eq!(engine.outside.presentations, 6);
        assert_eq!(report.terminated.terminal, Terminal::BudgetExceeded);
        assert!(report.terminated.reason.contains("outer dispatch"));
        assert!(report.moves.is_empty());
        report.verify(&engine.config.bounds).unwrap();
    }

    #[test]
    fn final_canonical_budget_failure_is_not_a_fabricated_key() {
        let mut cfg = Config::sealed("fresh input regression");
        cfg.closure_policy = false;
        cfg.max_steps = 9;
        let mut engine = Omega::new(AdversarialOutside { mode: 1, presentations: 0 }, cfg);
        let report = engine.run(&[]);
        assert_eq!(report.terminated.terminal, Terminal::BudgetExceeded);
        assert!(report.key.is_none());
        report.verify(&engine.config.bounds).unwrap();
    }

    #[test]
    fn malformed_outside_demand_and_choice_are_unresolved_not_panics() {
        let mut cfg = Config::sealed("bad demand");
        cfg.closure_policy = false;
        let report = Omega::new(AdversarialOutside { mode: 2, presentations: 0 }, cfg).run(&READING_L.genesis);
        assert_eq!(report.terminated.terminal, Terminal::Unresolved);
        assert!(report.terminated.reason.contains("ordered pair"));
        let report = Omega::new(AdversarialOutside { mode: 3, presentations: 0 }, Config::sealed("bad choice")).run(&READING_L.genesis);
        assert_eq!(report.terminated.terminal, Terminal::Unresolved);
        assert!(report.terminated.reason.contains("choice"));
    }

    #[test]
    fn invalid_config_and_history_cannot_accept() {
        for bad_bounds in [false, true] {
            let mut cfg = Config::sealed("invalid config");
            if bad_bounds { cfg.bounds.max_items = 3; } else { cfg.measures.clear(); }
            let report = Omega::new(Silent, cfg).run(&READING_L.genesis);
            assert_eq!(report.terminated.terminal, Terminal::Unresolved);
            assert!(report.moves.is_empty());
        }
        let report = Omega::new(Silent, Config::sealed("bad history")).run(&[Event::AdmitInst(999, vec![])]);
        assert_eq!(report.terminated.terminal, Terminal::Unresolved);
        assert!(report.verify(&Bounds::default()).is_err());
    }

    #[test]
    fn replay_rejects_tampered_checkpoints_scope_key_and_witnesses() {
        let base = Omega::new(Scripted::one_demand(READING_L.target, 6), Config::sealed("L")).run(&READING_L.genesis);
        base.verify(&Bounds::default()).unwrap();
        assert!(!base.moves.is_empty());
        let mut r = base.clone();
        r.moves[0].history_len = usize::MAX;
        assert!(r.verify(&Bounds::default()).is_err());
        assert!(base.verify(&Bounds { max_items: 1, max_arity: 2 }).is_err());
        let mut r = base.clone();
        r.key = None;
        assert!(r.verify(&Bounds::default()).is_err());
        let mut r = base.clone();
        r.witnesses.clear();
        assert!(r.verify(&Bounds::default()).is_err());
        let mut r = base;
        r.history.push(WorldEvent::Carrier(Event::AdmitInst(999, vec![])));
        assert!(r.verify(&Bounds::default()).is_err());
    }

    /// L3, observed: against a silent outside, from the Challenge 2
    /// situation, the engine records its two opening declarations and
    /// nothing else moves.
    #[test]
    fn against_a_silent_outside_nothing_moves() {
        let mut cfg = Config::sealed("L");
        cfg.closure_policy = false;
        let mut omega = Omega::new(Silent, cfg);
        let report = omega.run(&READING_L.genesis);
        assert!(report.moves.is_empty());
        assert_eq!(report.terminated.terminal, Terminal::Unresolved);
        assert_eq!(report.fingerprint, regime_fingerprint(&replay(&READING_L.genesis).unwrap()));
        assert_eq!(report.history.len(), READING_L.genesis.len() + 2);
        assert!(report.verify(&Bounds::default()).is_ok());
    }

    /// The closure policy, against a silent outside: it reissues the
    /// collapsed pair — and the move records that the policy, not the
    /// outside, asked — prices the answer, and stops with the three tied
    /// classes on the table because nobody outside will choose.
    #[test]
    fn the_closure_policy_asks_and_the_silent_outside_declines_the_tie() {
        let mut omega = Omega::new(Silent, Config::sealed("L"));
        let report = omega.run(&READING_L.genesis);
        assert_eq!(report.moves.len(), 1);
        assert_eq!(report.moves[0].origin, DemandOrigin::ClosurePolicy);
        assert_eq!(report.moves[0].classes.len(), 3, "the three tied classes, retained");
        assert_eq!(report.moves[0].gate, Gate::TieRetained, "silent declines to choose");
        assert_eq!(report.terminated.terminal, Terminal::Unresolved);
    }

    /// A scripted outside that chooses, licenses and funds: the engine
    /// answers Challenge 3 in one round and then the closure fixpoint is
    /// reached — reading L's closed-system baseline, one round.
    #[test]
    fn reading_l_closes_in_one_round_when_pushed() {
        let script = Scripted::one_demand(READING_L.target, 3);
        let mut omega = Omega::new(script, Config::sealed("L"));
        let report = omega.run(&READING_L.genesis);
        let passed: Vec<&Move> = report.moves.iter().filter(|m| m.gate == Gate::Passed).collect();
        assert_eq!(passed.len(), 1);
        assert_eq!(passed[0].origin, DemandOrigin::ClosurePolicy, "the policy asked before the script could");
        assert_eq!(passed[0].role, Some(Role::Innovation));
        assert_eq!(passed[0].prices[0], (MeasureKind::Mu1, (2, -1), 3));
        assert_eq!(passed[0].prices[1], (MeasureKind::Mu2, (2, 1), 1));
        assert_eq!(report.terminated.terminal, Terminal::Accepted);
        assert!(report.blind_spot.is_empty());
        assert!(report.verify(&Bounds::default()).is_ok());
        assert!(report.checklist.iter().all(|(_, ok)| *ok), "{:?}", report.checklist);
        assert!(omega.outside.log.iter().any(|l| l.starts_with("authorize")));
    }

    /// Reading F takes the closure to its fixpoint within the closed-system
    /// baseline's three rounds.
    #[test]
    fn reading_f_closes_within_three_rounds_when_pushed() {
        let script = Scripted::one_demand(READING_F.target, 5);
        let mut omega = Omega::new(script, Config::sealed("F"));
        let report = omega.run(&READING_F.genesis);
        let passed = report.moves.iter().filter(|m| m.gate == Gate::Passed).count();
        assert!((1..=3).contains(&passed), "passed {passed}");
        assert_eq!(report.terminated.terminal, Terminal::Accepted);
        assert!(report.verify(&Bounds::default()).is_ok());
    }

    /// Withhold the licence: the proposal is recorded as gated and the run
    /// stops unresolved rather than executing without authorization.
    #[test]
    fn a_withheld_licence_stops_the_run_and_executes_nothing() {
        let mut script = Scripted::one_demand(READING_L.target, 3);
        script.licence = false;
        let mut omega = Omega::new(script, Config::sealed("L"));
        let report = omega.run(&READING_L.genesis);
        assert_eq!(report.moves.last().unwrap().gate, Gate::LicenceWithheld);
        assert_eq!(report.terminated.terminal, Terminal::Unresolved);
        // The closure policy legitimately recorded the imposition; nothing
        // beyond that executed.
        let mut imposed = READING_L.genesis.clone();
        imposed.push(Event::Impose(READING_L.target));
        assert_eq!(report.fingerprint, regime_fingerprint(&replay(&imposed).unwrap()), "nothing executed past the imposition");
        let (w, _) = World::replay(&report.history, &Bounds::default());
        assert_eq!(w.regime.n_forms(), 0);
    }

    /// Within one item nothing separates the pair, so the engine records a
    /// refusal with its exhaustion certificate and terminates REFUSED.
    #[test]
    fn a_too_narrow_bound_yields_a_certified_refusal() {
        let mut cfg = Config::sealed("L");
        cfg.bounds = Bounds { max_items: 1, max_arity: 2 };
        let mut omega = Omega::new(Scripted::one_demand(READING_L.target, 3), cfg);
        let report = omega.run(&READING_L.genesis);
        assert_eq!(report.moves[0].gate, Gate::Obstructed);
        assert!(matches!(report.moves[0].certificate, Some(Certificate::Exhaustion { .. })));
        assert_eq!(report.terminated.terminal, Terminal::Refused);
        assert!(report.terminated.certificate.is_some());
    }
}

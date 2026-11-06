# OEEIS residual obligations

> Moved here on 2026-11-06 from the immune research repo. Paths and package names follow this repository's rename map; the recorded commands ran in the source repository and are kept as history.

AuthorityEffect: None.

The four OEEIS epic plans (EPIC-OE-EIS-001, -002, -003 and
EPIC-OE-OEEIS-PRIOR-ART-004) were retired on 2026-10-27 after their remaining
code slices were implemented. Their full text, including obstruction reviews
and TDD tables, is in Git history under
`ppo/plans/epics/oeeis/` at `82eab88b4b7ec3cd88367796971b3cda174ef0d5`.
The [closeout receipt](../receipts/oeeis_epic_closeout_20261027/README.md)
records what was implemented and checked. This file keeps what is still open,
so that retiring the plans does not retire the obligations.

None of the items below is a code slice an agent can close alone. Each needs an
operator act, real deployment data, or a research result.

## Operator and deployment obligations

| Obligation | Origin | Why an agent cannot close it |
| --- | --- | --- |
| Enroll production Ed25519 keys and map each signer to an authorized person | EIS-003 | Fixture keys verify bytes only; a person's authority is an operator fact. |
| Retain ledger tips (pins) in durable storage outside the database | EIS-003 | Storage choice and custody are deployment decisions. |
| Key rollover and migration policy | EIS-003 | No versioned rollover contract exists yet; it needs an operator decision first. |
| Deploy a real host-health observer and collect actual measurements | EIS-002, 004 | `SignedHostHealth` verifies reports; producing honest reports needs a real observer. |
| Continuous-health invariants (health between activations) | EIS-002 | The port checks health per activation; a continuous guarantee needs a monitoring design. |
| Concurrent or atomic multi-writer custody | EIS-003 | The ledger is single-writer by contract. |

## Empirical and research obligations

| Obligation | Origin | Status |
| --- | --- | --- |
| Quantified false-positive reduction of learned guards | EIS-002 | Needs a separately scoped empirical evaluation; finite controls are not a rate. |
| False-positive *rate* FP/(FP+TN) | EIS-003 | Telemetry carries no TN. A new versioned telemetry/policy contract is required; `core.eis.false-discovery-proportion.v1` stays FP/(TP+FP). |
| Statistical independence of observers | EIS-002, 004 | Distinct signed reports do not establish independent experiments. |
| Semantic completeness of the pharmacy detectors | EIS-001 | Twelve native classes plus the Python persona check are a finite panel. |
| Broader malformed-receipt fixture bank; source-theorem adoption from the PVG and hallucination papers | 004 | RESEARCH_HOLD. The finite experiment in `tests/test_prior_art_negative_selection_fixtures.py` stands; nothing more is claimed. |

## Known exactness debt

`DetectorRule.affinity_score` is a float in Python and in the native wire, and
the non-exact `stimulate` path in
`crates_rs/core_epistemic_immune_system/src/clonal_selection.rs`
adds f64 values. The exact path (`exact_boost`) refuses float boosts. Moving
affinity to exact rationals changes the Python value object, the native wire and
stored fixtures together; it was not done in the closeout and is recorded here
as open.

## Boundaries that stay in force

* A clean pharmacy report, a detector affinity score, a support count and a
  signed health report each answer one question. None admits a candidate.
* Learned rules carry only the declared rule fields; admission lives in the
  authenticated ledger and nowhere else.
* Adversary may route and challenge EIS findings; it cannot admit them.

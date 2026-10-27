# Antibody lifecycle

Part of [Epistemic Immune System](EIS.md). Previous: [Two-signal gate](EIS-Two-Signal-Gate.md) · Next: [Regulation and custody](EIS-Regulation-and-Custody.md)

An **antibody** is a recorded failure pattern with a detector, a description of
the failure and a fix, and a pair of fixtures: one example it must catch and one
it must leave alone. This page follows one from the moment it is farmed to the
moment it is admitted, or retired.

## What an antibody looks like

A real candidate from `eis/antibodies/`, shortened:

```json
{
  "antibody_id": "ab_checker_outage_is_not_certificate_refutation",
  "failure_class": "verification:checker_outage_conflated_with_certificate_refutation",
  "action": "refuse",
  "severity": "P0",
  "description": "An unavailable, timed-out or malfunctioning checker produces a
     verification-unavailable or resource refusal, never a certificate rejection.",
  "negative_fixture": "Checker binary not found, returning CERTIFICATE_MISMATCH for a valid certificate.",
  "positive_fixture": "Missing checker returns NO_RULE; timeout returns BUDGET_EXHAUSTED.",
  "times_seen": 1,
  "evidence_sha256": "4736f905…",
  "pharmacy_status": "candidate",
  "authority_effect": "None"
}
```

The collection of antibodies is called the **pharmacy**. Its status values are
`candidate`, `admitted`, `rejected` and `retired`.

## The stages

```text
farm ──▶ CANDIDATE ──▶ thymus screen ──▶ distinct observations ──▶ admission request
                                                                         │
                                         human decision, signed and scoped
                                                                         │
                                         ┌───────────────────────────────┴──────┐
                                      ADMITTED                        REJECTED or RETIRED
```

### 1. Farming: always a candidate

`external_admission.farm_candidate` has no status parameter, and the status
field refuses any value other than `CANDIDATE` at construction. This holds on
every path, including the local defect-harvesting path. Nothing self-admits.

### 2. Negative selection: the thymus

Before a detector rule can run, `thymus.py` runs it over a **self panel** of
known-clean inputs (code, proofs, prompts, candidate documents). If it matches
any of them it is refused, because it would fire on healthy input.

The thymus runs the predicate that will actually execute. When given the
matcher that will run the rule, it calls that matcher on each fixture, so a rule
whose matcher ignores its declared pattern cannot pass by declaring an innocent
one. A rule bound to an unsupported matcher is refused
(`THYMUS_MATCHER_UNBOUND`), and a rule bound to a different matcher than the
one supplied is refused (`MATCHER_BINDING_MISMATCH`).

Passing the panel shows only that the rule did not fire on those fixtures. It is
not a proof of zero false positives. Paper 003 shows how a reasonable-looking
phrase detector, as first written, matched a true statement.

### 3. Safe patterns: a rule cannot stall the screen

Detector rules run on Python's backtracking regular-expression engine, where
some patterns take exponential time on short inputs (`(a+)+b`). Even `\w*!`
took 14 seconds on 50,000 characters when measured. `re` has no timeout, so the
only guard is admission. `safe_pattern.compile_safe_pattern` admits a pattern
only if:

1. it is 1 to 256 characters and parses;
2. it has no backreference and no conditional group;
3. no repeat sits inside another repeat, and no alternation sits inside a
   repeat;
4. every repeat is bounded (`*`, `+` and `{m,}` are refused; write `{0,k}`),
   with every bound at most 64;
5. the product of choices over all repeats and alternations is at most 256;
6. it cannot match the empty string.

Under these rules a search over `n` characters takes at most
`(n + 1) · P · (L + B)` steps, linear in `n`. The code states this as an
argument, not a machine-checked proof.

### 4. Distinct observations

`external_admission.py` implements three criteria:

- **Nothing self-admits** (stage 1).
- **One observation cannot promote.** Distinctness is counted over observation
  identity, not list length, so replaying one defect ten times is one
  observation. This is the same mistake as `TWO_SIGNAL_COLLAPSE` in a different
  place: repetition is not independence.
- **The request binds everything it names**: candidate digest, producer system,
  source manifest digest and both fixture digests. A request missing its
  negative fixture is refused, because it asks to trust something nobody tested
  against a control.

How many distinct observations are required is deliberately not fixed in the
code: `is_promotable` takes `required_distinct` as a required argument with no
default, so the caller states it and the record shows who chose it. It does
refuse any threshold below 2, because a threshold of 1 lets a first sighting
promote, and a first sighting is exactly what a detector bug produces. The
separate provisional-promotion engine uses a support of at least 3, counted
with an exact maximum independent set over host-bound correlation keys, so
correlated observations cannot pose as independent ones.

The result is **eligibility for review**. The antibody stays `CANDIDATE`.

### 5. Admission

Admission is a separate human act, recorded with the exact rule bytes, scope,
fixtures and controls. A real example is
`antibodies/admissions/pilot035_admission_assessment_20261015.json`: one
antibody admitted for one prompt scope, with four inputs it must match and
several it must not, including two correct sentences about the same topic.
Admission decisions can be signed and checked; see
[Regulation and custody](EIS-Regulation-and-Custody.md).

Only admitted antibodies are ever injected. `admitted_antibody_query.py` is the
read side: candidates, rejected and retired entries are never returned, and an
entry that does not reconstruct as a valid antibody is reported, not returned.

## Retirement: named, not deleted

`retired_antibodies.py` keeps a register of antibodies that may never be farmed
again. The distinction matters:

| Status | Means |
| --- | --- |
| `REJECTED` | A real defect, judged not worth guarding |
| `RETIRED` | The defect never existed: the detector was wrong, and the antibody was an artifact of its bug |

Deleting the record would let the next run farm the same phantom with nothing to
say why it was wrong the first time. Retiring removes a guard; it promotes
nothing.

## Keeping the repertoire fresh

`clonal_selection.py` keeps an idle counter per rule. A match resets it; an
unmatched screening run increments it, and the rule is deactivated once the
counter reaches its limit. Despite the field name `half_life_runs` this is a
linear idle limit. A mutated child rule must pass the thymus like any new rule.

## Anti-skills

The `antiskills/` estate separates mined proposals (`ooutwire/`, inert data the
reviewer cannot load) from human-reviewed declarations (`admitted/`). Version 2
admission requires distinct contexts, a clean negative control, no loss of
protected fields, a replayed passing receipt and an explicit human decision. The
first admitted v2 registry is scoped to one engineering profile and grants no
global activation. A merged pull request, a legacy score, a repeated trace or
model consensus is never an admission label.

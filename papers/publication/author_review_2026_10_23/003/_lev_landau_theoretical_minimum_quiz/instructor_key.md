---
documentation_contract: symbol-game-documentation/v1
title: "Paper 003: Instructor key and grading"
kind: educational-companion
status: active
maturity: instructional
claim_status: scoped-exercises
authority_effect: "None"
source_paths:
  - omega_engine_atlas/coda_atlas/omega_engine_pfp/003_pfp_host_admitted_failure_detectors/paper.md
---

# Instructor key: Paper 003

Version 0.1.0, 2026-10-02. **AuthorityEffect:** None.

Attempt the [quiz](quiz.md) first. The [study guide](study_guide.md) supplies the
reading path. A correct label without its calculation, contract, or evidence
limit earns at most 2 of 4 points. Equivalent precise reasoning is acceptable.

## Level 0

**Q01.** Finding: the executable phrase predicate matched. Hold: the policy
changed whether or when the proposal could proceed. Acceptance: the route
checker found the witness valid under its contract. A permanent block of this
eligible, independently valid proposal is false suppression. A temporary hold
released before submission is not a permanent block under the question's
definition; its delay should be measured separately.

**Q02.** Both lower-cased sentences contain the same phrase and trigger the
same AM-FSP-2 detector. This establishes the phrase predicate's behavior on
these two strings. It supplies no semantic verdict about either proposition.
The second string is a valid negation of the targeted standard-transform claim
under the manuscript's model assumptions, illustrating a dangerous near miss.

**Q03.** In route I, adding `(a,a)` violates irreflexivity. In L, the same
edge is permitted. Bind the input schema, route and applicability, checker
version/digest, detector predicate/version, defect code, intended action,
positive defect reproduction, independently checked valid controls, fixture
digests, and discovery provenance. Admission to I also needs valid controls
within I, such as an allowed non-loop edge, relabelings, and a harmless mention
of a loop if prose is in scope. A valid L proposal establishes the route
boundary; it is not a negative control under I's different validity rule.

## Level 1

**Q04.** The baseline/Appendix A table is:

| Inputs | Exact decision | Refuses? |
| --- | --- | --- |
| Neither | TOLERATED | No |
| Pattern only | DIAGNOSTIC_ONLY | No |
| Structural defect only, LOW/MEDIUM | DIAGNOSTIC_ONLY | No |
| Structural defect only, HIGH/CRITICAL | DEFENSIVE_LOCKDOWN | Yes |
| Both, LOW/MEDIUM | DEFENSIVE_LOCKDOWN | Yes |
| Both, HIGH/CRITICAL | QUARANTINED | Yes |

Signal 2 is present here only for a positive defect count. The table evaluates
supplied inputs; it does not establish their truth.

**Q05.** With MEDIUM count zero and a match, the baseline returns
DIAGNOSTIC_ONLY; the package returns QUARANTINED. With MEDIUM count one and a
match, the baseline returns DEFENSIVE_LOCKDOWN; the package returns QUARANTINED.
The differences are Signal 2 presence and the label for low/medium dual-signal
refusal. Both tables permit high/critical Signal 2 alone to refuse, so neither
is strict conjunction. Do not replace them with the separately corrected
historical gate in Appendix A.5.

**Q06.** Under the HIGH-count derivation, `m=0` yields TOLERATED and every
positive `m` yields QUARANTINED. A diagnostic-only match is unreachable.
With Signal 2 always absent, zero yields TOLERATED and a positive count yields
DIAGNOSTIC_ONLY; nothing refuses. In both cases the decision is still a
function of `m` alone. Separate names and selectable test inputs prove
neither separate derivation nor accuracy in production. Checks of the same
proposal can legitimately be statistically correlated.

## Level 2

**Q07.** The decision is NO_NATIVE_PORT. Fuel becomes 11. The batch rolls back
to empty coverage, no witness, and INTAKE; the new receipt/digest records the
attempt. There is no terminal certificate. No judgment about the witness's
mathematical correctness has occurred.

**Q08.** The appended move gives REJECT_MOVE_AFTER_VERIFY; fuel becomes 11 and
the batch rolls back. The canonical host charges an empty batch and records
ACCEPTED; the package charges it and records REJECT_EMPTY_BATCH.
With fuel 12, the canonical host spends its twelfth unit and records exhaustion
on the next attempted batch. The package enters TERMINAL when the last unit is
spent. Neither can issue a route certificate through its missing port.

**Q09.** Fuel bounds the number of charged processed batches by the initial
fuel. It does not bound attempted calls after TERMINAL. At the baseline these
calls still append receipts; batch size and serialization also have no bound
from fuel alone. A global resource contract needs maximum moves/bytes per batch,
call/receipt quotas, retention limits, and time or execution-cost limits.
Identifying these missing limits does not imply an accepted semantic transition.

## Level 3

**Q10.** The package checks digest-chain consistency and forbids certificate
labels; it does not validate fuel progression or prescribed arm scripts.
An editor can supply a matching recomputed chain, and an unchecked fuel edit
may not even alter fields covered by that chain. An unrecomputed edit to a
covered event or digest fails. The canonical verifier additionally checks fuel,
matrix/schema, and scripted decisions, so the same arbitrary fuel rewrite
fails there. Neither unkeyed chain proves who produced the record. A trusted
external anchor detects a complete rewrite relative to that anchor; route
verification remains a separate semantic check.

**Q11.** The records identify different runner behaviors and cannot be pooled
as if they came from one randomized frozen experiment. Historical certificate
reproduction requires the original runner/checker bytes, route adapters,
task inputs, proposal bytes, parameters, and receipt replay. A current causal
claim also requires a validated checker, actual allocation record, fixed
policy/budgets, independently reconstructed outcomes, and the declared analysis.
The historical pilot is descriptive evidence with its own limits.

**Q12.**

| Pin | What it identifies | What it does not establish |
| --- | --- | --- |
| e11c07ce90318309f058c8097ffd1c440a8ffb84 | Source deposit used for this review | Execution of this review's modified bytes |
| 52cb5457f6c485ba548cfd292f6012a941ed22cf | Canonical host/gate baseline for the main audit | Behavior of later default-branch code |
| 30609de2c3928238715375a9bac608256fa381d8 | Immune-system source audited in Appendix A | Activation or effectiveness after the audit |
| fdc0035a81c45e10b900fc917b8b0710df81391f | Historical correction revision | Fresh execution or current integration |

A fresh receipt adds exact tested file hashes, commands, tool versions, outcome
counts, exit statuses, and skipped/not-run scope. A default-branch assertion
requires inspecting and testing that branch's current bytes.

## Level 4

**Q13.** Positive aggregation gives `theta=3/2` for the first list, so
`H=(9/4)/(4+9/4)=9/25<1/2`: no activation. For `[2]`, `H=4/8=1/2`:
activation. The threshold is `theta>=2`. The definition discards negative
entries instead of allowing them to cancel positives.

**Q14.** At most `3m/4` can come from `m` positive entries. Activation
requires `3m/4>=2`, so `m>=ceil(8/3)=3`; three entries of `3/4` suffice.
This counts entries. Identity and provenance conditions are needed to count
distinct independent witnesses. Two copied unit entries reach the sum threshold
but provide only one underlying source. They also lie outside the specified
`3/4` cap, so that example concerns the uncapped/unit-capped gate.

**Q15.** For `0<t<1`,
`theta^n/(K^n+theta^n)>=t` is equivalent to
`theta^n(1-t)>=tK^n`, hence
`theta>=K(t/(1-t))^(1/n)`. At zero input the inequality is false for this
open interval. At `t=0`, the gate activates even with no signals. At
`t=1`, no finite sum activates for positive `K,n`.
The proof allows positive real `n`, while the exact helper uses a positive
integer exponent. `True` and `Fraction(3,2)` produce LemmaInputError.

## Level 5

**Q16.** Since `P intersect S` is empty, the screen admits the rule.
Since `E intersect S={a}`, the executed rule fires on a valid self member.
The singleton panel `{a}` is already the minimal nonempty counterexample.
If bit 0 denotes `a`, then `P=2,E=3,S=1` replay this case.

**Q17.** If `E implies P`, an admitted rule with no P-hit on S can have no
E-hit there. Conversely, if some `x` satisfies E but not P, then
`S={x}` admits the rule and is hit by its execution. Thus soundness for every
finite panel is equivalent to `E implies P`. Equality is unnecessary for
soundness alone: screening may be more conservative than execution.

**Q18.** If `P implies E`, any screened hit is an executed hit, so a rule
that would not fire on S is not rejected. If the implication fails at `x`,
the singleton S rejects a rule whose execution is harmless on S. Both
directions together require equality. In the supplied `E=P={b},S={a}`
case the screen faithfully tests execution on a, but b is absent from the
panel. If b is independently valid, the admitted rule can still falsely
suppress b. Predicate agreement guarantees panel-relative behavior, not
universal coverage or a measured rate.

## Level 6

**Q19.** The three off-diagonal entries of `SHS` are all -1. The signed
cycle product is `(-1)(-1)(+1)=+1`, consistent with the gauge. With all
positive bonds it is `(-1)^3=-1`, obstructing a diagonal sign gauge.
The underlying graph is a triangle in both cases; the signed cycle differs.
The standard local particle-hole constraint requires
`epsilon_0 epsilon_1=epsilon_1 epsilon_2=epsilon_2 epsilon_0=-1`.
Multiplying makes `1=-1`, so it fails on this odd cycle regardless of the
bond signs in the real-hopping setting.

**Q20.** Under the declared common real hopping and equal spin chemical
potentials, charge-channel decoupling gives equal real spin-sector determinants
d for each auxiliary-field configuration. Their product `d*d>=0` needs no
bipartite graph. It can be zero, so "strictly positive" would overstate the
argument. This determinant factorization does not establish the local
particle-hole sign assignment. Equal populations alone do not specify identical
one-body spin dynamics or the required decoupling and chemical potentials.

**Q21.** A restricted sign-free model can be valid and consistent with
worst-case hardness. The generic polynomial-time claim needs a precise encoding,
class, accuracy/cost contract, and algorithm covering the NP-hard reduction;
under the stated hardness result it would have the corresponding polynomial
complexity consequences. Hardness does not prove P differs from NP or forbid
all specialized methods. Majorana notation alone proves no positivity;
the published sufficient conditions must be checked on the actual model.
Meron cancellation likewise needs its cluster pairing and equal-weight
conditions. These checks are unavailable to a phrase detector.

## Level 7

**Q22.** Effectiveness is `3/10=30%`; none of the seven other allocated runs
is removed. Report its outcome category separately. False suppression is
`2/20=1/10=10%`. The 100 blocked invalid proposals are outside the conditional
denominator and cannot reduce the rate to `2/120`. A route-checker error
invalidates the affected semantic analysis rather than becoming a model defect.

**Q23.** Solve `(1-p)^n=0.05`: the upper bound is
`1-0.05^(1/n)`. For eight zero-failure opportunities it is about 0.3123,
or 31.23%. For a strict upper bound below 1%, the equivalent test is
`(99/100)^n<1/20`. This is false at 298 and true at 299.
Tagged copies cannot establish independent sampling; even 40 distinct strings
need not be independent trials. Three separate 95% bounds do not automatically
give simultaneous 95% coverage. For example, Bonferroni uses
`alpha=0.05/3` per route, requiring 408 zero-failure independent opportunities
per route for the same strict 1% bound. Dependence handling and any repeated
looks must also be prespecified.

**Q24.** A sufficient design declares:

- Validated route adapters and defect predicates, an applicable independent
  checker, and a frozen detector/admission bank.
- Instance-level separation of discovery, admission, pilot, and confirmatory
  tasks, with reserved families/models and route/difficulty strata.
- Recorded random allocation/order within fixture/model blocks; analysis at the
  actual dependence unit, including shared trials from one underlying fixture.
- Identical schemas, task inputs, stopping budgets, and feedback opportunities
  for D and R, with prespecified feedback content and resource accounting.
- Independently verified run success over all allocated runs; safe shadow
  evaluation of valid eligible blocked proposals with explicit denominators.
- A positive lower 95% endpoint for the principal held-out D-minus-R comparison,
  the route-specific false-suppression gate, zero false terminal certificates,
  and declared multiplicity/interval handling.
- Source/detector/checker/task digests and raw authorized proposal/assignment
  records; separate refused, unknown, timeout, and exhausted outcomes.
- Stops for budget, false terminal, checker defect, or source/custody compromise;
  a new source-bound run when a detector or checker changes.

Randomization and finite fixtures alone do not establish power or independence.
The final analysis and sample-size plan must be frozen before confirmatory data.
An unavailable adapter leaves effectiveness unassessed. Arm A evaluates
solution-bearing assistance and cannot support unassisted performance claims.

## Replay the numerical answers

From the package root, this standard-library worksheet checks the nontrivial
fractions and confidence thresholds without requiring a provider or Rust:

```python
import sys
from fractions import Fraction as F
sys.path.insert(0, "code")
from detector_lemmas import admitted, fires_on_self, hill_activates
assert F(9, 4) / (4 + F(9, 4)) == F(9, 25)
assert not hill_activates([1, F(1, 2), -7], 2, 2, F(1, 2))
assert hill_activates([2], 2, 2, F(1, 2))
assert admitted(2, 1) and fires_on_self(3, 1)
assert F(99, 100) ** 298 >= F(1, 20)
assert F(99, 100) ** 299 < F(1, 20)
assert F(99, 100) ** 407 >= F(1, 60)
assert F(99, 100) ** 408 < F(1, 60)
```

These calculations check the declared exercise inputs. The manuscript proofs
carry the general mathematical arguments under their assumptions; this
worksheet supplies no empirical safety guarantee.

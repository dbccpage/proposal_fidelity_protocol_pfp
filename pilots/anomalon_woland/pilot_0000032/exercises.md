# Quiz 07, rewritten: normalization and a declared measurement rule

These four exercises run in [pilot_0000032](README.md). They use exact
three-sector arithmetic, not a model's agreement with a requested answer.
The original worksheet is retained in the migration research brief; its local
labels and broad uniqueness prose are not mathematical standards.

## 7.1 — Normalize the original weights

For weights `(2,1,0)`, compute the total `W=3` and probabilities
`(2/3,1/3,0)`. Check both `sum(p)=1` and `W*p_i=w_i`. The zero-weight sector
remains in the vector. Negative weights, boolean values and a zero total are
outside this exercise's domain.

The runner accepts any triple of integers from zero through `10^9`, provided
the total is positive. It returns reduced exact fractions, not rounded floats.

## 7.2 — Check a proposed square-root lift

A nonnegative square-root lift has coordinates `sqrt(p_i)`. Its squared
magnitudes are `p_i` by construction. Submit the following certificate:

```json
{"total":3,"probabilities":[[2,3],[1,3],[0,1]],"lift_radicands":[[2,3],[1,3],[0,1]]}
```

The checker binds all three fields to the original weights. Replacing the
radicands with `(4/5,1/5,0)` must fail even though they still sum to one.
Reproducing chosen-basis probabilities this way is an identity, not an
independent experiment or a derivation of a physical probability law.

## 7.3 — Separate a representation from its readout

Compare these two declared pairs:

| Representation | Readout | Result |
|---|---|---|
| `p` | Identity | `(2/3,1/3,0)` |
| Nonnegative `sqrt(p)` | Squared magnitude | `(2/3,1/3,0)` |

The first two coordinates of the representations differ: `p_i*p_i != p_i`
for `p_i` equal to `2/3` or `1/3`. Their readouts nevertheless agree.
This calculation does not establish a unique representation/readout pair or
derive the Born rule. The runner records `born_uniqueness: NOT_ESTABLISHED`.
It is not a counterexample to a quantum uniqueness theorem, nor is a refusal
label itself a proof. No Gleason theorem is used or claimed here.

## 7.4 — Make the external assumption visible

Use real amplitudes `(3/5,4/5,0)`, whose squared norm is one. Arithmetic gives
the squares `(9/25,16/25,0)` in either of the following cases:

- With the explicit assumption `Born rule in declared basis a,b,c`, the runner
  interprets these squares as probabilities and checks a submitted prediction.
- With `assumption: null`, it returns the same arithmetic squares but leaves
  the probability interpretation `NOT_SUPPLIED`; a submitted probability
  prediction is not accepted on that basis.

Negative amplitudes are allowed when the squared norm is one. This differs
from the nonnegative-weight domain in exercise 7.1. Importing an assumption
does not make `born_rule_derived` true or authorize an external action.

## Run and boundary

From the repository root:

```powershell
$pilot = "omega_engine_education/documentation/030_the_symbol_game_proposal_fidelity_protocol_pfp/pilots/pilot_0000032"
py -3.12 "$pilot/run.py"
py -3.12 "$pilot/run.py" --proposal "$pilot/lift_certificate.json"
py -3.12 "$pilot/run.py" --input "$pilot/amplitudes.json" --proposal "$pilot/amplitude_prediction.json"
```

No arguments compute all four cases. The [README](README.md) specifies the
input bounds, outputs, tests and rejection behavior. These are fixed-basis
examples; weights alone do not reconstruct phase. See the separate
[interference exercises](../pilot_0000031/exercises.md) for a declared basis
change with two different relative phases. No quantum-computing viability
claim follows from either pilot.

AuthorityEffect: None. GenesisEffect: None.

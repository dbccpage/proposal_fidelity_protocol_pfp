# Genesis rewriting: examples

Part of [Rewriting](Rewriting.md). See also: [Overview](Rewriting-Genesis.md) · [Strategies](Rewriting-Genesis-Strategies.md)

## Example 1: from nothing to one directed cut

| Step | Event | State after |
| --- | --- | --- |
| 0 | (start) | `regime<data:0,forms:0,insts:0,rules:0>` |
| 1 | `supply(<>)` | `regime<data:0,forms:0,insts:0,rules:0>` (G1: unchanged) |
| 2 | `admit_datum(<a>)` | `regime<data:1,forms:0,insts:0,rules:0>` |
| 3 | `admit_datum(<b>)` | `regime<data:2,forms:0,insts:0,rules:0>` |
| 4 | `admit_form(2)` (a binary form) | `regime<data:2,forms:1,insts:0,rules:0>` |
| 5 | `admit_inst(1,[1,2])` (form 1 on data 1 and 2) | `regime<data:2,forms:1,insts:1,rules:0>`; G6 yields `<a->b>` |

Receipt:

```text
<<cert><regime<data:2,forms:1,insts:1,rules:0>><<tokens><<a>><b>><<cut><a->b>>>>
```

**The point.** Step 1 changed nothing. Every later change came from a named
admission.

## Example 2: discharging a requirement

Start at `regime<data:2,forms:1,insts:0,rules:0>` and impose `impose(1,2)`:
data 1 and 2 must be connected.

1. **G8.** There are no instances, so the requirement fails: an active
   obstruction.
2. A candidate arrives: `delta<NewInst(1,[1,2])>`.
3. **G2.** Apply it. Instances go from 0 to 1.
4. **G8 again.** The instance is present, so the requirement holds.

```text
regime<data:2,forms:1,insts:1,rules:0>
```

**The point.** The candidate was accepted because the audit passed afterwards,
not because it was offered.

## Example 3: tied answers, two readings

For the first non-trivial separability requirement, count the items in each
candidate. The minimum is 3, and several candidates reach it, for example:

```text
Δ_A = delta<NewDatum;NewInst(1,[1,2]);NewInst(1,[2,1])>
Δ_B = delta<NewForm(2);NewInst(2,[1,1]);NewDatum>
Δ_C = delta<NewRuleAll(1);NewDatum;NewInst(1,[1,2])>
```

- Under **Reading L** the minimal candidates fall into **three** classes.
- Under **Reading F** they fall into **five**.

**G9** records the fork. Saying "the seed forces this continuation" would be the
error `ERR_UNEARNED_UNIQUENESS`.

## Example 4: a linear system as a candidate stream

A small pilot encoded the system *x + 2y = 5, 3x − y = 1* as one Genesis delta:

```text
delta<NewDatum;NewDatum;NewForm(1);NewForm(2);NewInst(1,[1,2]);NewInst(2,[3,1]);NewRuleAll(1)>
```

Two data stand for the unknowns, two instances carry the coefficients, and one
rule closes the system. Without explicit permission to do arithmetic, the
model's reasoning wandered through many guesses. The host checker marked the
answer as wrong. See [Dialects and pilot](Rewriting-PFP-Dialects.md) for the
full pilot record.

## Mistakes to refuse

| Mistake | What goes wrong | Error |
| --- | --- | --- |
| Presentation counted as admission | `supply(t)` changes the state | `ERR_SUPPLY_STATE_MUTATION` |
| Diagonal loop | A self-loop under an irreflexive relation | `ERR_DIAGONAL_VIOLATION` |
| Counter regression | A count goes down or is badly formatted | `ERR_REGIME_COUNTER_REGRESSION` |
| Unearned uniqueness | One tied branch is called forced | `ERR_UNEARNED_UNIQUENESS` |
| Silent reading | No statement of Reading L or F | `ERR_UNDECLARED_READING_PROFILE` |
| Smuggled form | An instance of a form never admitted | `ERR_UNADMITTED_FORM_ARITY` |
| Opaque token decomposition | Parsing inside `<ab>` before any relation is admitted | `ERR_UNLICENSED_DECOMPOSITION` |
| Unchecked seal | A certificate while a requirement still fails | `ERR_UNSATISFIED_OBSTRUCTION` |

## What this does not show

Genesis is not offered as a model of physical emergence, and no minimal
continuation is claimed to be unique without a declared selection rule.

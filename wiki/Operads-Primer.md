# Operad primer

Part of [Operads](Operads.md). Next: [Prompts as operad trees](Operads-Prompt-Trees.md)

This page builds a coloured operad from nothing, using the definitions in
[`operads/domain/operad/`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/operads/domain/operad).
No category theory is assumed.

## Colours

A **colour** is a type of thing that can flow between operations. The code
admits exactly ten:

```text
State  Proof  Paper  Code  Contract  Receipt  Ledger  Diagram  Audit  Post
```

This list is `ADMITTED_FINITE_COLOURS` in `colours.py`. Constructing a `Colour`
with any other name raises an error. The list must stay identical in every
place that declares it: when an earlier copy omitted `Contract` and `Diagram`,
16 skills that used them silently changed arity and output colour. That bug is
the reason the compiler now refuses unknown colours instead of repairing them.

## Operations

An **operation** has an ordered list of input colours and exactly one output
colour. Its **signature** is written `(inputs) -> output`:

```text
falsifier : (Contract)          -> Audit
audit     : (Audit, Contract)   -> Receipt
summarise : ()                  -> Paper      (nullary: no inputs)
```

The number of inputs is the **arity**. Order matters: `(Audit, Contract)` and
`(Contract, Audit)` are different signatures. Each operation also declares
whether it is `equivariant` (indifferent to input order) and a
`residual_effect` string describing what it does to outstanding obligations,
`"unknown"` by default.

## Partial composition, the one move

Plug the output of `g` into input slot `i` of `f`. This is written `f ∘_i g`.

**When it is allowed:** `0 <= i < arity(f)` and the output colour of `g` equals
the colour `f` expects at slot `i`.

**What it produces:** `f`'s inputs with slot `i` replaced, in place, by all of
`g`'s inputs, and `f`'s output.

```text
audit ∘_0 falsifier

   audit : (Audit, Contract) -> Receipt
              ▲
              └── falsifier : (Contract) -> Audit

result : (Contract, Contract) -> Receipt
```

The first `Contract` is the falsifier's input; the second is the audit's own.
`ColouredOperad.partial_compose` returns this as `Ok(...)`. If the colours
disagree it returns `Err(IllTypedCompositionError)`, and if the slot is out of
range, `Err(ArityMismatchError)`. Nothing is raised for an expected failure;
callers branch on the result.

## Units

Every colour `C` has an identity operation `id_C : (C) -> C`. Plugging it in
changes nothing: `f ∘_i id = f` and `id ∘_0 f = f`. `ensure_units()` adds an
identity for every admitted colour and refuses if the name `id_C` is already
taken by an operation that is not an identity.

## Two associativity laws

A tree of compositions can be bracketed in different orders. The operad laws
say the result does not depend on the order.

**Nested (sequential).** Plug `h` into `g`, then the composite into `f`; or plug
`g` into `f`, then `h` into the slot that `g`'s input now occupies:

```text
(f ∘_i g) ∘_(i+j) h  =  f ∘_i (g ∘_j h)
```

After `g` is spliced in at `i`, `g`'s input `j` sits at position `i + j`.

**Disjoint (parallel).** For two different original slots `i < k` of `f`:

```text
(f ∘_i g) ∘_(k + arity(g) − 1) h  =  (f ∘_k h) ∘_i g
```

Splicing `g` in at `i` shifts every later slot by `arity(g) − 1`. A nullary `g`
removes a slot, so `k` moves to `k − 1`; a unary `g` leaves it at `k`.

### Worked example

Take `f = audit : (Audit, Contract) -> Receipt`, `g = falsifier : (Contract) -> Audit`
and `h = cite : (Paper) -> Contract`.

| Law | Left side | Right side |
| --- | --- | --- |
| Nested, `i = 0`, `j = 0` | `(f ∘_0 g) ∘_0 h = (Paper, Contract) -> Receipt` | `g ∘_0 h = (Paper) -> Audit`, then `f ∘_0 (…) = (Paper, Contract) -> Receipt` |
| Disjoint, `i = 0`, `k = 1` | `f ∘_0 g = (Contract, Contract) -> Receipt`, then `∘_1 h` gives `(Contract, Paper) -> Receipt` | `f ∘_1 h = (Audit, Paper) -> Receipt`, then `∘_0 g` gives `(Contract, Paper) -> Receipt` |

`TreeCompositionWitness.verify_sequential_associativity` in `planar.py` computes
both bracketings of one nested instance and records the two composite
signatures. It certifies that one instance, at the level of colour signatures
only. It is not a proof of the law in general and says nothing about what the
operations do.

## Planar trees

A composite computation is a **planar tree**: each node is an operation, each
child fills one input slot, and the left-to-right order of the leaves is fixed.
`PlanarTree` counts its open inputs (its arity) by walking the tree. The
operads here are **planar** by default: inputs are ordered and nobody may
reorder them. An operation declared `equivariant` may additionally be permuted,
but that is a property of the registry entry, not something the planar tree
assumes.

## Agent slices

A **slice** restricts an agent to a subset of operations, optionally also to
allowed input and output colours. `verify_agent_permission` refuses an
operation outside the slice with `SliceViolationError`. Identity operations are
always allowed. A slice is a capability limit, not a grant of authority to run
anything.

## What the operad does not tell you

- That a composite does the right thing. Types only say the pieces fit.
- That two operations with equal signatures are interchangeable. Equal
  boundaries do not establish equivalence or permit swapping their effects.
- That a shared step runs once. The first typed workflow compiler refuses
  shared producers for this reason; see [Typed workflows](Operads-Typed-Workflows.md).

## Exercises

1. Is `falsifier ∘_0 audit` defined? *No: `audit` outputs `Receipt`, but slot 0
   of `falsifier` expects `Contract`.*
2. What is the signature of `audit ∘_1 summarise'` where
   `summarise' : () -> Contract`? *`(Audit) -> Receipt`: a nullary child removes
   the slot.*
3. Check the disjoint law with `g` nullary: `f = audit`, `g : () -> Audit`,
   `h = cite`, `i = 0`, `k = 1`. Which slot index does `h` use on the left side?
   *`k + 0 − 1 = 0`.*

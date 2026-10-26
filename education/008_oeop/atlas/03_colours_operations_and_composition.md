# Colours, Operations, and Composition

## Implemented colour universe

The local OEWAS operad uses ten colours:

```text
State  Proof  Paper  Code  Contract
Receipt  Ledger  Diagram  Audit  Post
```

An operation has an ordered input profile and one output colour. Its authority
effect cannot exceed its declared ceiling.

## Planar substitution

Composition substitutes a child output into a selected parent input slot. The slot
order matters and there is no implemented permutation action. The narrow accurate
mathematical description is therefore a **coloured non-symmetric multicategory**,
or a planar typed-operad scaffold.

```text
parent : (A, B, C) -> D
child  : (X, Y)    -> B

parent o_1 child : (A, X, Y, C) -> D
```

The implementation checks selected colour/profile compatibility and can construct
sequential associativity witnesses. Those witnesses re-evaluate structural typing;
they do not establish semantic equality of effects or implementations.

## Units and registries

Identity operations and registered operation maps exist. Current risks include:

- unit identifiers can be forged;
- an existing unit is not always checked against the requested signature;
- duplicate identifiers can overwrite prior entries;
- operands need not be proved members of the same operad;
- planar trees do not fully validate arity and boundary consistency.

These are invariant gaps, not merely missing documentation.

## Higher-operad adapter

The adapter checks a subset of slot/profile and schema conditions. It currently
accepts negative slots because it checks only an upper bound, and it does not fully
enforce duplicate slots, complete coverage, supplied child-operation identities,
expected boundaries, schema references, or validator identities. Empty bindings
can succeed.

`authorize_term` always refuses with `LICENSE_WITNESS_REQUIRED`. This is a sound
authority ceiling: a term can be structurally describable while remaining
unlicensed.

## Capability slices

Capability slices describe bounded families of operations. A slice is useful only
when every referenced operation is resolvable in the owning catalog. Migration code
currently constructs successor operations but returns slices without persisting all
those operations, so resolvability is not assured by the slice alone.

## Laws and their evidence state

| Property | State | Evidence ceiling |
| --- | --- | --- |
| Ordered typed profiles | `IMPLEMENTED` | Constructor and composition checks |
| Partial substitution | `IMPLEMENTED`, partly `TESTED` | Selected happy/refusal paths |
| Identity construction | `IMPLEMENTED` | Forgeability and signature gaps remain |
| Sequential association | `IMPLEMENTED`, partly `TESTED` | Structural typing witness only |
| Symmetric action | `NONCLAIM` | No permutation action |
| Equivariance | `NONCLAIM` | Cannot follow without an action |
| Behavioral equivalence | `NONCLAIM` | No execution semantics or equivalence relation |
| Contractivity | `NONCLAIM` | Residual observations are diagnostic only |

## Coordination conventions in operad profiles

Drawing on multi-agent action-space conventions (Paper 21, `LIB-CONVENTIONS-21`),
multi-agent workflow coordination requires explicit convention tokens $\kappa \in \mathcal{K}$
embedded into planar substitution slots:

```text
operation : (C_1, C_2, ..., C_n, Convention[kappa]) -> C_out
```

A convention slot enforces sequential barrier synchronization, preventing child
substitution from executing until predecessor turns establish explicit precommitment
witnesses.

## External mathematical context

Wiring-diagram operads offer a mature language for compositional syntax. Spivak’s
[operad of wiring diagrams](https://arxiv.org/abs/1305.0297), Yau’s
[book-length treatment](https://arxiv.org/abs/1512.01602), and work on
[normal forms for wiring diagrams](https://arxiv.org/abs/2101.12046) motivate
clear generators, equations, and normal forms. They do not prove that OEWAS
implements those theories. The immediate use is a test-design question: which
syntactic equations does this code claim, and what canonical forms make them
replayable?

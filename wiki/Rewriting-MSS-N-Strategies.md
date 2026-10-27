# MSS-N rewriting: strategies R1–R12

Part of [Rewriting](Rewriting.md). See also: [Overview](Rewriting-MSS-N.md) · [Examples](Rewriting-MSS-N-Examples.md)

The strategies sit on five layers:

| Layer | Objects | Typical rewrite |
| --- | --- | --- |
| 5. Protocol | Proposals, receipts, certificates, refusals | `W → <<cert><W_nf><receipt>>` or a refusal |
| 4. Homology | Simplices, chains, boundaries | `z → z − ∂(c) = 0` |
| 3. Packets | Trees, subterms, replacements | `<<op><arg1>…<argk>> → <result>` |
| 2. Arithmetic | Numerals and exact fractions | `<<add><n><m>> → <sum>` |
| 1. Lexical | Plain words | String rewriting `w1 ⇒ w2` |

| ID | Name | Layer | Input | Output |
| --- | --- | --- | --- | --- |
| R1 | Carrier declaration | 5 | A bare task | Task plus its declared carrier |
| R2 | Prose quarantine | 3 | Mixed prose and code | Pure packet plus a codebook |
| R3 | Epistemic abstention | 5 | A question with no admitted meaning | Empty answer, or a refusal |
| R4 | Collision audit | 3 | Two concepts sharing one token | A tagged lift, or a refusal |
| R5 | Local/global split | 4 | A locally valid step | A step held pending a global check |
| R6 | Dialect transpiler | 1–3 | Tier H or D | Strict Tier S |
| R7 | Role typing | 5 | A bare claim | A claim with a declared role |
| R8 | Typed refusal | 5 | Any failed check | A refusal packet |
| R9 | Boundary reduction | 4 | `∂_k` of a simplex | Its alternating sum of faces |
| R10 | Arithmetic normalisation | 2 | An arithmetic term | A reduced numeral or fraction |
| R11 | Critical peak join | 3 | A divergent peak | A common join, or a refusal |
| R12 | Receipt sealing | 5 | An irreducible normal form | A certificate |

## R1: Carrier declaration

A task must declare five things: alphabet, valid terms, rules, obstruction
detector and goal. If any is missing, fail.

```text
<<task><integrate>>
  →  <<decl><<alph><gamma38>><<dom><rat>><<rule><poly>><<obst><divzero>><<goal><exact>>>><<task><integrate>>>
```

## R2: Prose quarantine

Natural language moves into codebook slots `s0, s1, …`. Only Γ38 remains in the
packet; the codebook is kept with the receipt.

```text
P  →  <<p><v1><<q><s0>><<c><s1>>>
```

## R3: Epistemic abstention

A question about meaning, with no admitted valuation, gets an empty answer or a
refusal, never invented semantics.

```text
<<ask><meaning><x>>  →  <<ans><x><>>    or    <<refusal><errnointerpretation>>
```

## R4: Collision audit

If two different concepts map to one token, add a distinguishing tag or refuse.
Silent tie-breaking is not allowed.

```text
w  →  <<lift><w><tag1>>    or    <<refusal><errtokenconflict>>
```

## R5: Local/global split

A step that is only locally valid is held until it is checked against the
global goal. No `qed` before then.

```text
<<step><local><x>>  →  <<audit><<use><x>><<derive><y>><<matchgoal><pending>>>
```

## R6: Dialect transpiler

```text
Tier H:  op<arg1, arg2>      →  <<op><arg1><arg2>>
Tier D:  <assume p1 <x>>     →  <<assume><p1><x>>
```

It must be deterministic and round-trip on its domain.

## R7: Role typing

Wrap every claim in a role: `assume`, `derive`, `check` or `assert`.

## R8: Typed refusal

On a syntax error, an exhausted resource, an undeclared carrier or a peak that
will not join, stop and emit `<<refusal><code><context>>`. No heuristic recovery.

## R9: Boundary reduction

```text
∂k(<v0 … vk>)  →  Σ (−1)^i <v0 … (vi removed) … vk>
```

Applying it twice gives zero.

## R10: Arithmetic normalisation

```text
<<add><3><4>>  →  <7>
```

Exact only, no floating point. Overflow beyond a declared limit is refused.

## R11: Critical peak join

Reduce both sides of a peak until they meet:

```text
<<peak><s><t1><t2>>  →  <<joined><j>>
```

If they end in different normal forms, confluence fails (`ERR_CONFLUENCE_FAILED`).

## R12: Receipt sealing

```text
W_nf  →  <<cert><W_nf><steps k><hash h>>
```

The receipt carries `AuthorityEffect: None`. Replay checks the result; a
signature identifies the signer; permission to act is a separate decision.

Next: [worked examples](Rewriting-MSS-N-Examples.md).

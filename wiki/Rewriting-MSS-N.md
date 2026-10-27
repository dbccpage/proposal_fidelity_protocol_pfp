# MSS-N rewriting: overview

Part of [Rewriting](Rewriting.md). Next: [Strategies R1–R12](Rewriting-MSS-N-Strategies.md) · [Examples](Rewriting-MSS-N-Examples.md) · [Graph examples](Rewriting-MSS-N-Graph-Examples.md)

MSS-N (the Minimal Symbol System at stage N) is the wire language that proposals
are packetised into. It is where rewriting becomes term rewriting proper: rules,
redexes, normal forms and confluence.

## A 38-character alphabet

```text
Γ38 = { a … z }  ∪  { 0 … 9 }  ∪  { <, > }
        26 letters    10 digits     2 boundaries
```

No spaces, commas or other punctuation. Before a delimiter is admitted, not even
whitespace exists. That is enough to write:

| Structure | How |
| --- | --- |
| Trees | Balanced `<` `>` for nesting; siblings side by side: `<p1><p2>` |
| Whole numbers | Decimal digits |
| Exact fractions | A declared codec, such as `<<rat><pos><3><4>>` for +3/4 |
| Simplices | `<a>` a vertex, `<ab>` a directed edge, `<<2><a><b><c>>` a triangle |
| Rewrite rules | `<<rule><id><<lhs><rhs>>>` |
| Confluence peaks | `<<peak><apex><left><right><join>>` |
| Protocol roles | `<<assume><p><x>>`, `<<derive><p><y>>`, `<<refusal><errcode>>` |

## Packets

A **packet** is the ground `<>`, an atom `<w>` (a non-empty word of letters and
digits), or a composite `<p1 p2 … pk>` of packets. Every packet is balanced and
has no whitespace. The repository's current boundary parser
(`parse_boundary` in `pfp/domain/rewriting/rewrites.py`) is stricter than this
specification: it rejects the empty packet `<>`. Addresses into a packet are sequences of child indices, and
`t[s]_p` means "put `s` at address `p` in `t`".

## Three dialects

| Tier | Alphabet | Example | Used for |
| --- | --- | --- | --- |
| **S** strict boundary | Γ38 only | `<<op><1><<arg><a>>>` | Checked execution, canonical storage, receipts |
| **H** head-word | Γ38 plus space, newline, `, = + * -` | `lp<var<x>, dom<0,10>>` | Human-readable traces and teaching |
| **D** directive | Γ38 plus capitals, space, `_` | `<assume p1 <ab>>` | Host coordination and typed refusals |

Every rewrite declares its source and target tier. The target for checked
execution and receipts is Tier S.

## Rewriting vocabulary

- **Rule** `ℓ → r`: two packets; every variable in `r` also appears in `ℓ`.
- **One step**: at some address, the subterm matches `ℓ` under a substitution and
  is replaced by the matching `r`.
- **Joinable**: two terms reduce to a common term.
- **Confluent**: any two reducts of one term are joinable.
- **Locally confluent**: any two *one-step* reducts are joinable.
- **Terminating**: no infinite chain of steps.
- **Newman's lemma**: terminating and locally confluent together imply confluent.
  Then every term has a **unique normal form**.
- **Critical peak**: two rules overlap on one term and give two different
  results. Checking that every critical peak joins is how local confluence is
  tested. In the polygraph picture the peak is a 2-cell boundary and its join is
  a 3-cell.

## Homology as a rewrite target

Encode a simplicial complex as packets. Boundaries are:

```text
∂1(<ab>)  = <b> − <a>
∂2(<abc>) = <bc> − <ac> + <ab>          with  ∂1∘∂2 = 0
```

A 1-cycle `z` (with `∂1 z = 0`) that is not a boundary marks an **unfilled
hole**, an active obstruction. Injecting a 2-cell `c` with `∂2 c = z` repairs
it: `z − ∂2(c) = 0`.

## Source

[`rewriting_strategies_mssn_wire.md`](https://github.com/dbccpage/theory_of_finite_quantum_mechanics/blob/main/education/minimal_symbol_systems/rewriting/rewriting_strategies_mssn_wire.md)
in the theory repository. The strategies are design specifications. The
document does not supply an executable parser, a complete rewrite system or a
proof of termination and confluence.

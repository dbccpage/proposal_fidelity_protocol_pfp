# MSS-N rewriting: graph examples

Part of [Rewriting](Rewriting.md). See also: [Overview](Rewriting-MSS-N.md) · [Strategies](Rewriting-MSS-N-Strategies.md) · [Examples](Rewriting-MSS-N-Examples.md) · [S(n) graph examples](Rewriting-Sn-Graph-Examples.md)

You can write a great many prompt rewrites with nothing but graphs. The MSS-N
glyph grammar
([`mssn.ebnf`](https://github.com/dbccpage/theory_of_finite_quantum_mechanics/blob/main/education/minimal_symbol_systems/grammar/mssn.ebnf))
was built for exactly this: paths, cycles, weights, trees and rewrite rules over
the Γ38 alphabet. These examples start from the cycle `a>b>c>a` and climb
through MSS-N levels 00 to 03. The first three are simple; the last three are
moderately difficult.

Every accept or reject below was run against `mssn.ebnf` with the repository's
grammar recognizer. Case ids such as MSSN_007 refer to
[`mssn_conformance_cases.json`](https://github.com/dbccpage/theory_of_finite_quantum_mechanics/blob/main/education/minimal_symbol_systems/grammar/mssn_conformance_cases.json).

## Example 1 (simple): one string, three readings

| Text | `raw_glyphs` | `glyph_path` | `label_path` | `suffix_path` |
| --- | --- | --- | --- | --- |
| `a>b>c>a` | accepted (MSSN_003) | accepted (MSSN_007) | accepted | rejected |
| `a0>b2>c1>a0` | accepted (MSSN_004) | **rejected** (MSSN_008) | accepted (MSSN_011) | accepted (MSSN_013) |

`a0>b2>c1>a0` is rejected as a glyph path because `a0` would be two adjacent
vertices with no direction between them. As a label path, `a0` is one name. As a
suffix path, it is vertex `a` carrying the annotation `0`.

**The point.** Before rewriting a string, say which reading it is under. The same
bytes give a four-vertex cycle, a cycle with numbered labels, or a parse error.

## Example 2 (simple): a path becomes an edge list

```text
a>b>c>a     ⇝   a>b;b>c;c>a          accepted as path_list
a>b<c       ⇝   a>b;c>b              accepted as path_list
```

`<` reverses one step, so `a>b<c` means `a` to `b` and `c` to `b`. The repeated
`a` at both ends of the cycle names one vertex only under a declared identity
policy; the grammar keeps the repetition and does not merge it for you.

**The point.** This is the MSS-N form of the S(n) "path into cuts" rewrite:
lossless in one direction, an extra declaration in the other.

## Example 3 (simple): from path to Tier S packet

Rewrite the edge list into strict-boundary packets, the form used for checked
execution:

```text
<<e><a><b>><<e><b><c>><<e><c><a>>
```

MSS-N level 02 writes a single directed edge more compactly as `<ab>`, so the
cycle can also be `<ab><bc><ca>`. A diagonal such as `<aa>` is rejected at level
02 (`ERR_BOUNDARY_DEFECT`), because a cut needs two distinct endpoints.

**The point.** All three forms (`a>b>c>a`, the edge packets, `<ab><bc><ca>`) are
representation changes. Each needs a decoder that gets the original back.

## Example 4 (moderate): adding two cycles cancels the shared edge

Take a square `a, b, c, d` with the diagonal `a–c`. It holds two triangles:

```text
a>b>c>a;a>c>d>a          accepted as path_list
```

Treat each cycle as a chain, with `+1` for an edge used forwards and `−1` for
one used backwards (edges named in alphabetical order):

| Edge | `a>b>c>a` | `a>c>d>a` | Sum |
| --- | --- | --- | --- |
| `ab` | +1 | | +1 |
| `bc` | +1 | | +1 |
| `ac` | −1 | +1 | **0** |
| `cd` | | +1 | +1 |
| `ad` | | −1 | −1 |

The sum is exactly the outer loop `a>b>c>d>a`. The rewrite rule is "an edge used
once each way cancels". The graph has 5 edges and 4 vertices, so its cycle space
has dimension 5 − 4 + 1 = 2: these two triangles are a basis, and every other
cycle is a sum of them.

**The point.** Cycles add like vectors. A prompt that lists many loops can be
rewritten to a basis plus coefficients, which is shorter and checkable.

## Example 5 (moderate): a weighted cycle is a consistency test

Edge weights sit between matching marks: `>2>` is a forward step of weight 2,
and `<5<` is a step whose arrow points back.

```text
a>2>b>3>c<5<a        accepted as edge_weight_path
```

This says `a→b` weighs 2, `b→c` weighs 3, and `a→c` weighs 5. Going round the
cycle `a→b→c→a` gives `2 + 3 − 5 = 0`, so there is a **potential** that explains
every weight as a difference: `p(a)=0`, `p(b)=2`, `p(c)=5`.

Change the last weight:

```text
a>2>b>3>c<7<a        accepted as edge_weight_path
```

Now `2 + 3 − 7 = −2`. No potential exists. The smallest total change that
restores one is 2, and it can all go on one edge (for example, read `a→c` as 5).
The certificate is the cycle itself, `w = (+1, +1, −1)` on `(ab, bc, ac)`: every
entry is at most 1 in size, and pairing it with the weights gives `−2`, so no
repair smaller than 2 is possible.

**The point.** "Are these weights consistent?" has an exact answer and a
one-line witness. See [Residual repair](Rewriting-PFP-Residual-Repair.md) for
the rule that changing a weight is a new problem, not a solution of the old one.

## Example 6 (moderate): trees are not walks

The same edge, three ways:

```text
>ab     prefix_tree
ab>     postfix_tree
a>b     glyph_path
```

A larger tree does not flatten into a walk:

```text
><ab>cd     accepted as prefix_tree, rejected as glyph_path
```

As a prefix tree it is `>(<(a,b), >(c,d))`: one root joining two subtrees. Read
as a walk it is not even well formed. The grammar comment says it directly:
binary trees "do not silently flatten into graph walks".

**The point.** Switching between tree and path syntax is a representation
change with its own decoder. Do not let a model treat `><ab>cd` as a route from
`a` to `d`.

## What these examples do not show

The grammar checks are syntax only. Cancellation, potentials and the minimum
repair are calculations done on top of the parse, by hand here and by the
residual checkers in the PFP code. MSS-N levels 00 to 03 are research
specifications; their successor lifts are marked unlicensed in the source.

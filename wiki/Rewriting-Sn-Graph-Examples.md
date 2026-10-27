# S(n) rewriting: graph examples

Part of [Rewriting](Rewriting.md). See also: [Overview](Rewriting-Sn.md) · [Sections and retractions](Rewriting-Sn-Retraction.md) · [Examples](Rewriting-Sn-Examples.md) · [MSS-N graph examples](Rewriting-MSS-N-Graph-Examples.md)

The smallest interesting prompt is a cycle, `a>b>c>a`. It is small enough to
check by hand and already asks a real question: does the loop close? These
examples rewrite cycles and simplices with the S(n) flat grammar
([`sn.ebnf`](https://github.com/dbccpage/theory_of_finite_quantum_mechanics/blob/main/education/symmetric_group_presentations/grammar/sn.ebnf))
and the stage ideas of S(n) levels 00 to 03. The first three are simple; the
last three are moderately difficult.

Every accept or reject below was run against `sn.ebnf` with the repository's
grammar recognizer. Case ids such as SN_035 refer to
[`sn_conformance_cases.json`](https://github.com/dbccpage/theory_of_finite_quantum_mechanics/blob/main/education/symmetric_group_presentations/grammar/sn_conformance_cases.json).

## The four stages these examples use

| Level | What is present | S(n) token | What you cannot do yet |
| --- | --- | --- | --- |
| 00 ground | Nothing admitted | `<>` | Name anything |
| 01 mark | One supplied mark | `<a>` | Compare, order or connect |
| 02 pair | Two marks, possibly a cut between them | `<ab>`, `<a->b>` | Enclose an area |
| 03 simplices | Faces with boundaries | `[a,b]` and its boundary | Measure lengths |

## Example 1 (simple): a three-cycle is three cuts

The S(n) flat grammar has no path syntax. Both of these are rejected:

```text
a->b->c->a     rejected
<a->b->c>      rejected
```

The rewrite is *one path of k steps becomes k directed cuts*:

```text
a>b>c>a   ⇝   <a->b>  <b->c>  <c->a>
```

Each cut is accepted on its own (compare SN_035, `<a->b>`). Going back the
other way, from three cuts to one path, needs a stated **identity policy**: the
`a` in `<a->b>` and the `a` in `<c->a>` name the same vertex only because we say
so.

**The point.** Splitting a path into cuts is lossless. Joining cuts into a path
adds an identification, and that addition has to be declared.

## Example 2 (simple): the grammar accepts the diagonal; the meaning refuses it

```text
<aa>      accepted by sn.ebnf
<a->a>    accepted by sn.ebnf
```

The grammar only checks shape. Under the irreflexive reading of the binary germ,
`R(a,a)` is impossible, so `<a->a>` cannot be **admitted** as a cut. The
rewrite to apply is a refusal, not a repair:

```text
<a->a>   ⇝   refused: diagonal, a cut needs two distinct endpoints
```

**The point.** A syntax pass is not admission. A host that only runs the
grammar will let a self-loop through.

## Example 3 (simple): the boundary of the cycle is zero

Write the cycle with simplex cuts and give each edge its boundary,
`∂[x,y] = y − x`:

| Edge | Boundary |
| --- | --- |
| `[a,b]` | `b − a` |
| `[b,c]` | `c − b` |
| `[c,a]` | `a − c` |
| **Sum** | **0** |

The chain is closed: it is a **cycle**. Level 03 adds the warning that
coefficients and orientation are supplied, not read off the token: `[a,b]` is
written unoriented, and we chose to read it as `a` to `b`.

**The point.** "The loop closes" is a calculation with a definite answer, here
zero. A model that says "the triangle is connected" has answered a different
question.

## Example 4 (moderate): lift the cycle, retract it, and catch a stowaway

Lift each cut to stage 6, then retract at the same stage:

```text
u_6<a->b>   u_6<b->c>   u_6<c->a>        lifted cycle
r_6 of each lift   ⇝   <a->b>  <b->c>  <c->a>
```

All three come back exactly (`r̂ ∘ u = inl`). Now suppose a step at stage 6
added a chord `<a->c>` that was never lifted from below. Its retraction has
nothing to recover:

```text
r_6<a->c>   ⇝   NON_DESCENT
```

So retracting the four-edge stage-6 graph returns the three original cuts and
one typed refusal. The chord cannot be carried down silently.

**The point.** This is how S(n) keeps a rewrite honest across stages: whatever
was added upstairs is refused on the way down unless it came from below.

## Example 5 (moderate): an odd cycle needs more than one binary tag

An observation `q` gives the same answer, 7, on three admitted elements `a`,
`b`, `c`, and the task needs every pair told apart. The pairs that conflict form
the triangle `a–b`, `b–c`, `c–a`.

One binary tag is a 2-colouring, and an odd cycle has no 2-colouring. Try it:
`t(a)=0` forces `t(b)=1`, which forces `t(c)=0`, which collides with `a`. Two
binary tags are enough:

| Element | `q` | `t1` | `t2` | `q'` |
| --- | --- | --- | --- | --- |
| `a` | 7 | 0 | 0 | `(7,0,0)` |
| `b` | 7 | 1 | 0 | `(7,1,0)` |
| `c` | 7 | 0 | 1 | `(7,0,1)` |

Dropping both tags gives back `q`. Every constraint is still binary (one pair at
a time); what grew is the number of tags.

**The point.** The sn_guide's one-pair recipe ("two tag values suffice")
does not extend to cycles of odd length. The cycle itself is the obstruction.

## Example 6 (moderate): sorting is the symmetric group, and the peak joins

S(n) is named after the symmetric group. Its generators are adjacent swaps, and
they make a small rewrite system on words. Using the MSS-N rule syntax:

```text
ba=>ab    cb=>bc    ca=>ac
```

Start from `cba`. Two rules apply, so there is a **critical peak**. Follow both
branches:

```text
cba ⇝ bca ⇝ bac ⇝ abc        swaps at positions 1, 2, 1
cba ⇝ cab ⇝ acb ⇝ abc        swaps at positions 2, 1, 2
```

Both reach `abc`, and every complete path from `cba` takes exactly 3 steps, the
number of out-of-order pairs. Each rule removes one inversion, so the system
terminates, and its peaks join, so `abc` is the unique normal form. Read as
permutations, the two branches are the braid relation `s1 s2 s1 = s2 s1 s2`.

**The point.** A confluence diagram can be a theorem of group theory in
disguise. The rewrite system is checked the same way either way: every peak
must join.

## What these examples do not show

The grammar checks are syntax only; the refusals in Examples 2 and 4 are
meaning-level rules applied by hand, not productions of `sn.ebnf`. The
bubble-sort system in Example 6 was checked from `cba` only, not as a general
proof for longer words.

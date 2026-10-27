# Shells around a prompt's subtext

Part of [Rewriting](Rewriting.md). Next: [Worked example](Rewriting-Shells-Example.md) · See also: [Prompts as graphs](Rewriting-PFP-Graph-Prompts.md) · [S(n) retractions](Rewriting-Sn-Retraction.md)

A **shell** wraps a prompt's content in one mathematical discipline, with its own
vocabulary and its own check. Shells nest:

```text
Shell2( Shell1( Shell0( SubText ) ) )
```

| Layer | Discipline in the default stack | What it names | What its check asks |
| --- | --- | --- | --- |
| **SubText** | none | The bare data the prompt is about, for example `a>2>b>3>c<7<a` | Does it parse under the declared reading? |
| **Shell0** | Graph theory and linear algebra | Vertices, edges, weights, potentials | Is there a potential? If not, what is the smallest residual? |
| **Shell1** | Homology | Chains, cycles, boundaries, the class in H1 | What does each cycle pair to? Is the class zero? |
| **Shell2** | Category theory | Objects, morphisms, composites, functors, natural transformations | Does the diagram commute? What is the defect? |

Everything in every shell is written in Γ38 (`a–z`, `0–9`, `<`, `>`), as Tier S
packets. Category theory needs no extra symbols: an object is `<<obj><a>>`, a
morphism is `<<mor><f><a><b>>`, a composite is `<<comp><g><f>>`.

## Rules that make a shell a shell

1. **Declared vocabulary.** Each shell lists the packet heads it may use. A reply
   at Shell2 that uses an undeclared head, such as `<limit>`, is refused.
2. **A retraction down.** Each shell has a map to the one below, like the S(n)
   retraction `r̂_n`. Shell2 to Shell1 sends a morphism to its edge and a
   functor value to a cochain value. Anything with no image below is refused
   as `NON_DESCENT`.
3. **One check per shell.** Each shell's question has an answer a host can
   compute: a residual, a pairing, a commutativity defect.
4. **The shells must agree.** After retraction, every shell's answer has to be
   the same number on the same data. Disagreement is a refusal, not a vote.
5. **Shells add no facts.** A shell renames and reorganises the subtext. If a
   shell's answer depends on something not in the subtext, that is a problem
   change and needs its own provenance.

## Why do this: from L2 parrot to L1 sparse

An "L2 parrot" answer spreads itself thinly: a fluent paragraph that touches
every plausible point a little, the way a least-squares repair moves every edge
by a small amount. An "L1-sparse" answer concentrates on a few atoms that can
each be checked, the way an ℓ¹ repair puts the whole defect on one edge. The
[prompts-as-graphs page](Rewriting-PFP-Graph-Prompts.md) shows the two repairs
side by side on the same triangle.

Shells push the model toward the sparse kind of answer in three ways:

- **Each shell's answer is small.** One residual, one pairing, one defect. There
  is no room for a paragraph.
- **Fluency does not help.** A wrong number fails Shell0's check however well it
  is phrased.
- **Three independent checks must line up.** A guess that happens to pass one
  shell is unlikely to pass all three with the same value.

**Status: this is a design proposal, not a measured result.** Nothing in the
repository has yet compared shelled and unshelled prompts. The natural test is
a [PFP Lab](PFP-Lab.md) experiment: the same graph tasks posed as plain prose
and as `Shell2(Shell1(Shell0(SubText)))`, the same host checker, and counts of
accepted, wrong and refused replies per arm, read as single runs unless
repeated. The [dialect pilot](Rewriting-PFP-Dialects.md) is a warning that
more structure in the prompt can also make answers worse.

## Other stacks

Shell0 does not have to be graph theory. What matters is that each shell has
its own vocabulary, a check and a retraction to the shell below.

| Shell0 | Shell1 | Shell2 | Good for |
| --- | --- | --- | --- |
| Graph theory, linear algebra | Homology | Category theory (free category, functor to a group) | Consistency of weights, prices, potentials |
| Order theory (a finite poset) | Homology of the order complex | The poset as a category | Rankings, dependencies, scheduling |
| Finite probability (a Markov chain) | Cycle decomposition of flows | Categories of stochastic maps | Whether a process is reversible, where it circulates |

## Source

This page develops an idea from the project chat (2026-10-27). The
mathematics in each shell is standard; the S(n) retraction it borrows is in
[`sn_guide.md`](https://github.com/dbccpage/theory_of_finite_quantum_mechanics/blob/main/education/symmetric_group_presentations/grammar/sn_guide.md).

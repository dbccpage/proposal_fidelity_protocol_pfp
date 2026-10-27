# Rewriting

A **rewrite** replaces one expression with another under a declared rule. In
PFP every rewrite has to answer the same question: *which question does the
change preserve, and who checks that it did?* A rewrite that changes the
problem is not a repair, and a clearer prompt is not a proof.

This section follows rewriting through five layers, Pre-Genesis to PFP, plus
WDP, the mathematical foundation they rest on. Each has an overview, its
strategies or laws, and worked examples.

| Layer | What it adds | Pages |
| --- | --- | --- |
| **Pre-Genesis** | Four glyphs, no rules yet. Nothing rewrites unless something is supplied. | [Overview](Rewriting-Pre-Genesis.md) · [Strategies PG1–PG8](Rewriting-Pre-Genesis-Strategies.md) · [Examples](Rewriting-Pre-Genesis-Examples.md) |
| **Genesis** | A regime state that grows only through explicit admission events. | [Overview](Rewriting-Genesis.md) · [Strategies G1–G10](Rewriting-Genesis-Strategies.md) · [Examples](Rewriting-Genesis-Examples.md) |
| **S(n)** | Stage presentations with lifts up and typed retractions down. | [Overview](Rewriting-Sn.md) · [Sections and retractions](Rewriting-Sn-Retraction.md) · [Examples](Rewriting-Sn-Examples.md) · [Graph examples](Rewriting-Sn-Graph-Examples.md) |
| **MSS-N** | A 38-character wire language that can carry trees, numbers, complexes and rewrite rules. | [Overview](Rewriting-MSS-N.md) · [Strategies R1–R12](Rewriting-MSS-N-Strategies.md) · [Examples](Rewriting-MSS-N-Examples.md) · [Graph examples](Rewriting-MSS-N-Graph-Examples.md) |
| **PFP** | Proposals, checks and permission to use them, across all the layers above. | [Overview](Rewriting-PFP.md) · [Residual repair](Rewriting-PFP-Residual-Repair.md) · [Dialects and pilot](Rewriting-PFP-Dialects.md) · [Prompts as graphs](Rewriting-PFP-Graph-Prompts.md) |
| **Shells** | Nested disciplines around a prompt's subtext, each with its own vocabulary and check. | [Overview](Rewriting-Shells.md) · [Worked example](Rewriting-Shells-Example.md) |

**New here?** Start with the cycle `a>b>c>a`: the
[S(n) graph examples](Rewriting-Sn-Graph-Examples.md) and
[MSS-N graph examples](Rewriting-MSS-N-Graph-Examples.md) build everything else
from it, simple examples first.
| **WDP** | The mathematics underneath: what each repair, retention or measurement costs. | [Overview](Rewriting-WDP.md) · [DDC operations](Rewriting-WDP-DDC.md) · [Examples](Rewriting-WDP-Examples.md) |

## Five kinds of rewrite

Before applying any rule, name which kind of change it is. They carry different
obligations.

| Kind | Ask | A pass establishes |
| --- | --- | --- |
| Representation change | Can the declared decoder recover the original exactly? | A round trip on the stated domain, nothing more |
| Witness replacement | Does the full replacement satisfy the original task under a fresh binding? | The predicates checked on that certificate |
| Cochain repair | Is the change exactly a coboundary `d0*a` on the fixed carrier? | The same quotient class; the optimum is unchanged |
| Problem change | Were observations, carrier, norms or assumptions changed? | Nothing about the old problem; it is a new one |
| Prompt heuristic | Did a controlled comparison improve a predeclared outcome? | Bounded evidence for the tested tasks, model and budget |

## Laws that hold at every layer

1. **Presentation is not admission.** Writing a token down does not put it in
   the state. Only an explicit admission event does.
2. **No step without a rule.** With no admitted rules, every term is already in
   normal form. A model that "continues" anyway is inventing a rule.
3. **Separations are chosen, not forced.** When a task needs two equivalent
   things told apart, many observations will do it. Name the one you chose.
4. **Refuse with a type.** A failed rewrite returns a typed refusal packet, not
   a guess. Refusal leaves the state unchanged.
5. **Keep the history.** Seeing only the last step can hide the true state, so
   every step goes on an append-only record.
6. **No authority.** Every receipt is non-authoritative (`AuthorityEffect: None`,
   written `authority_effect` in JSON receipts; the short packet receipts on
   these pages leave the field implicit). Checking a result is separate from
   permission to act on it.

## Sources

- Pre-Genesis, Genesis, S(n), MSS-N and WDP: the
  [theory of finite quantum mechanics education folders](https://github.com/dbccpage/theory_of_finite_quantum_mechanics/tree/main/education)
- PFP: [`education/004_oepfp/rewriting`](https://github.com/dbccpage/proposal_fidelity_protocol_pfp/tree/main/education/004_oepfp/rewriting)

The strategy documents are specifications. Where they describe an evaluator,
grammar checker or pilot run, read each result at its stated scope.

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
| **Pre-Genesis** | Four glyphs, no rules yet. Nothing rewrites unless something is supplied. | [Overview](rewriting_pre_genesis.md) · [Strategies PG1–PG8](rewriting_pre_genesis_strategies.md) · [Examples](rewriting_pre_genesis_examples.md) |
| **Genesis** | A regime state that grows only through explicit admission events. | [Overview](rewriting_genesis.md) · [Strategies G1–G10](rewriting_genesis_strategies.md) · [Examples](rewriting_genesis_examples.md) |
| **S(n)** | Stage presentations with lifts up and typed retractions down. | [Overview](rewriting_sn.md) · [Sections and retractions](rewriting_sn_retraction.md) · [Examples](rewriting_sn_examples.md) · [Graph examples](rewriting_sn_graph_examples.md) |
| **MSS-N** | A 38-character wire language that can carry trees, numbers, complexes and rewrite rules. | [Overview](rewriting_mss_n.md) · [Strategies R1–R12](rewriting_mss_n_strategies.md) · [Examples](rewriting_mss_n_examples.md) · [Graph examples](rewriting_mss_n_graph_examples.md) |
| **PFP** | Proposals, checks and permission to use them, across all the layers above. | [Overview](rewriting_pfp.md) · [Residual repair](rewriting_pfp_residual_repair.md) · [Dialects and pilot](rewriting_pfp_dialects.md) · [Prompts as graphs](rewriting_pfp_graph_prompts.md) |
| **Shells** | Nested disciplines around a prompt's subtext, each with its own vocabulary and check. | [Overview](rewriting_shells.md) · [Worked example](rewriting_shells_example.md) |

**New here?** Start with the cycle `a>b>c>a`: the
[S(n) graph examples](rewriting_sn_graph_examples.md) and
[MSS-N graph examples](rewriting_mss_n_graph_examples.md) build everything else
from it, simple examples first.
| **WDP** | The mathematics underneath: what each repair, retention or measurement costs. | [Overview](rewriting_wdp.md) · [DDC operations](rewriting_wdp_ddc.md) · [Examples](rewriting_wdp_examples.md) |

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

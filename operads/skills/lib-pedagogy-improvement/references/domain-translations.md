# Domain-specific translations

`AuthorityEffect: None.` Reference material for [`lib-pedagogy-improvement`](../SKILL.md).

Moved out of `SKILL.md` on 2026-09-03 to bring that file under the
300-line ceiling `auto-oe-autop` declares. The content is
unchanged; only its location moved.

## Domain-Specific Translations

### Math / Physics

**Thinkers:** Shannon, Sweller, Bruner, Pólya, Lakatos, Gestalt, Newell–Simon, Bjork, Ericsson

#### Math / Physics Non-negotiable checks

- **Worked → Faded → Independent** (see patterns)
- **Representation switching**: words ↔ equation ↔ diagram ↔ limiting case ↔ units
- **Invariant / symmetry / conservation** called out where relevant
- **Prediction-first**: learner predicts before derivation
- **Error-correction loop**: wrong answer → diagnose → targeted reattempt
- **Claim tags + Sources footer** (v4)

#### Math / Physics Micro-templates

- *Prediction*: "Before we compute, what should increase/decrease if ___ changes? Why?"
- *Invariant*: "What quantity stays fixed under this transformation?"
- *Limiting case*: "What happens as x → 0 / ∞? Does it match intuition?"
- *Units*: "Check dimensions: LHS vs RHS."

### Philosophy

**Thinkers:** Grice, Clark, Pask, Kuhn, Duhem–Quine (holism), Lakatos (refutation dynamics)

#### Philosophy Non-negotiable checks

- **Term disambiguation** at point of first use (stipulative allowed; label it)
- **Argument map**: premises → conclusion (and where definitions enter)
- **Counterexample / objection**: at least one strong objection + response or "open problem" note
- **Assumption surfacing**: list hidden premises learners might import

#### Philosophy Micro-templates

- *Argument map*: "P1… P2… therefore C… (where does the key definition do work?)"
- *Objection*: "What's the best steelman objection? What premise would it attack?"
- *Common ground*: "If someone denies P1, what would convince them?"

### Computation

**Thinkers:** Norman (artifacts), Newell–Simon, Ericsson, Bjork, Mayer (media), Shannon (encoding)

#### Computation Non-negotiable checks

- **Runnable artifact** or precise pseudocode
- **Tests**: normal + edge case (and an invariant if applicable)
- **Debug exercise**: "here's a failing case; locate the bug class and fix it"
- **Complexity note** when it affects feasibility

#### Computation Micro-templates

- *Invariant*: "What property does this loop maintain each iteration?"
- *Edge case*: "What input breaks a naive implementation?"
- *Debug*: "Given failing test X, which assumption is false?"

### Cognitive Science

**Thinkers:** Piaget, Vygotsky, Chi, Baddeley, Broadbent/Treisman, Bateson

#### Cognitive Science Non-negotiable checks

- **Mechanism vs description** explicitly distinguished
- **Testable prediction** included
- **Alternative explanation** noted when plausible
- **Diagnostic probe** to detect misconception early

#### Cognitive Science Micro-templates

- *Prediction*: "If mechanism M is true, what should happen when we manipulate variable V?"
- *Alternative*: "What else could explain this data pattern?"

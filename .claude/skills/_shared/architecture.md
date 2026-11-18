---
kind: note
authority_effect: None
status: live
owner: techne-shared-corpus-custodian
---
# Faculty Skills Architecture

## Architectural Evolution & Reconciliation

This document records both historical conventions and the live operadic architecture:

1. **Historical Model (Faculty & Flat Simulation)**:
   - Early versions modeled faculty knowledge through flat namespaces and progressive disclosure.
   - Two early claims — that all `.md` files form a flat namespace of independent skills, and that frontmatter carries no imports — were superseded.
2. **Live Model (Coloured Operad & Planar Workflows)**:
   - The live system is formally governed by the symmetric coloured operad documented in [categorical_architecture.md](categorical_architecture.md).
   - Skills are multi-input typed operations $f \in \mathcal{O}(C_1, \dots, C_n; C_{\text{out}})$ over 10 boundary colours.
   - Workflows compose skills via planar substitution $\gamma(f; g_1, \dots, g_n)$.
   - Subagents are evaluation algebras over capability slices.

---

## Hierarchy Simulation Strategies

### Strategy 1: Progressive Disclosure

Use markdown links in `SKILL.md` to reference specialty files:

```text
faculty/
├── SKILL.md           # Core with links to specialties
└── specialties/
    ├── theory.md      # Loaded when agent follows link
    └── systems.md
```

`SKILL.md` links to `specialties/theory.md` and agents read on-demand.

- **Pros**: Simple, minimizes context bloat.
- **Cons**: No guaranteed loading unless explicitly traversed.

### Strategy 2: Subagent Composition

Create subagents that compose multiple skills:

```yaml
name: cs-expert
description: Computer science expert with full specialty access
skills:
  - cs-theory
  - cs-systems
  - cs-ml
  - cs-security
```

Each specialty is a standalone skill that the subagent loads.

- **Pros**: Explicit skill composition, clean separation.
- **Cons**: Requires subagent invocation, not automatic.

### Strategy 3: Meta-Skill Router

Create a meta-skill that instructs the agent which specialty to invoke:

```markdown
# CS Faculty Meta

When handling CS questions:
- For complexity/automata → invoke `cs-theory` skill
- For OS/compilers → invoke `cs-systems` skill
- For ML/neural nets → invoke `cs-ml` skill
```

- **Pros**: Dynamic routing, single entry point.
- **Cons**: Relies on instructions to invoke skills. Routing recommendation is advisory unless the subagent explicitly loads the skill.

---

## Recommended Architecture

### File Structure

```text
skills/
├── _shared/                    # Shared components (not skills themselves)
│   ├── output_formats.md       # Reusable templates
│   ├── constraints.md          # Shared constraints
│   └── sprint_gates.md         # Sprint gate definitions
│
├── cs/                         # CS faculty namespace
│   ├── core.md                 # Main entry point (SKILL.md renamed)
│   ├── meta.md                 # Router/dispatcher skill
│   └── specialties/
│       ├── theory.md           # Each is a standalone skill
│       ├── systems.md
│       └── ml.md
│
└── mathematics/
    ├── core.md
    └── specialties/
        └── ...
```

### Core Skill Pattern

```markdown
---
name: cs-core
description: Computer Science faculty. Use for algorithms, systems, ML, security, databases, networking.
---

# CS Faculty

## Quick Reference
For specialized analysis, invoke these skills:
- `cs-theory` - Complexity, automata, computability
- `cs-systems` - OS, compilers, architecture
- `cs-ml` - Machine learning, neural networks

**Operational Note**: If a specialty is required for correctness, use subagent composition rather than markdown-link hope. Progressive disclosure is not guaranteed.

## Core Competencies
[Essential content here - under 300 lines]

## Extended Reference
- `specialties/theory.md`
- `specialties/systems.md`
```

### Specialty Skill Pattern

Each specialty is a **full skill** with its own frontmatter:

```markdown
---
name: cs-theory
description: Computation theory, complexity, automata. Use for P vs NP, Turing machines, formal proofs.
---

# CS Theory Specialty

[Detailed methods - loaded independently]
```

### Meta-Skill Pattern

```markdown
---
name: cs-meta
description: Routes CS questions to appropriate specialty. Use when unsure which CS area applies.
---

# CS Router

Analyze the question and determine specialty:

| Keywords | Invoke Skill |
|----------|--------------|
| complexity, NP, automata, Turing | cs-theory |
| kernel, compiler, memory, CPU | cs-systems |
| neural, training, gradient, loss | cs-ml |
```

## Key Invariants

1. **Specialties become standalone skills** with their own frontmatter.
2. **Core skill is minimal** — just overview and links, under 300 lines.
3. **Meta skill provides routing** without bloating core.
4. **Naming convention** enables discovery: council prefixes or domain prefixes.
5. **Shared files are NOT skills** — they are reference material and laws only.

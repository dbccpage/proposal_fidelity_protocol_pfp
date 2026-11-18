# Domain expert quality gate

`AuthorityEffect: None.` Reference material for [`lib-pedagogy-improvement`](../SKILL.md).

Moved out of `SKILL.md` on 2026-09-03 to bring that file under the
300-line ceiling `auto-oe-autop` declares. The content is
unchanged; only its location moved.

## Domain Expert Quality Gate (Phase 3.5)

**MANDATORY BEFORE CONTENT PUBLICATION:** All technical content (physics, mathematics, chemistry, computer science, linguistics) must pass domain expert verification via the **Domain Expert Quality Gate** system.

### When to Invoke Domain Expert Gate

The pedagogy skill now coordinates with **domain expert agents** (physics-prof, math-prof, chemistry-prof, etc.) to verify content accuracy BEFORE pedagogical evaluation is complete.

**Automatic trigger:** If content contains keywords from these domains:

- **Physics**: Schrödinger, quantum, field theory, spacetime, general relativity, QFT, gauge theory, CFT, black hole, etc.
- **Mathematics**: Category, functor, topos, homology, cohomology, proof, theorem, logic, derivation, etc.
- **Chemistry**: Molecular, reaction, orbital, spectroscopy, bonding, equilibrium, kinetics, etc.
- **Computer Science**: Algorithm, complexity, data structure, proof of correctness, formal verification, etc.
- **Linguistics**: Syntax, grammar, semantics, morphology, historical linguistics, etc.

### Integration Workflow

#### Step -1: Domain Detection (BEFORE lib-pedagogy-improvement runs)

Before you evaluate pedagogical quality, the **domain taxonomy** auto-detects the primary domain:

```python
from engine.domain.domain_taxonomy import detect_domains

assignment = detect_domains(content)
print(assignment.primary_domain)      # e.g., QUANTUM_FIELD_THEORY
print(assignment.is_multidomain)      # True if multiple domains
print(assignment.cross_domain_flags)   # e.g., "QFT + topos: verify functoriality"

``` ext

**Step 0: Create Domain Expert Gate**

Initialize the gate before pedagogical review:

```python
from engine.application.gates.domain_expert_gate import (
    create_domain_expert_gate,
    route_to_expert_agent,
)

gate = create_domain_expert_gate(
    content_id=section_heading,
    content=section_content
)

expert_agents = route_to_expert_agent(gate.domain_assignment)

# → ['physics-prof', 'mathematics-prof'] if multi-domain

# → ['physics-prof'] if single domain

``` ext

**Step 1: Route to Expert Agent(s)**

Send content to appropriate expert(s):

- **Physics content** → `physics-prof` agent (executes `/physics` skill)
- **Mathematics content** → `math-prof` agent (executes `/mathematics` skill)
- **Chemistry content** → `chemistry-prof` agent (executes `/chemistry` skill, when available)
- **Computer Science content** → `cs-prof` agent (executes `/computer-science` skill, when available)
- **Multi-domain** → invoke ALL applicable experts (coordinate verdicts)

**Step 2: Execute Domain Expert Verification**

Each expert runs their skill:

```bash

# Example for physics
/physics "[section content]" --strict --cite

# Output: ExpertReview(verdict=PASS|CONDITIONAL_PASS|FAIL, confidence, checks_passed, checks_failed, recommendations)

``` ext

**Step 3: Register Verdicts**

Add expert reviews to gate:

```python
expert_review = ExpertReview(
    content_id=section_heading,
    expert_agent="physics-prof",
    domain=ExpertDomain.QUANTUM_FIELD_THEORY,
    verdict=ExpertVerdict.CONDITIONAL_PASS,
    confidence=0.92,
    checks_passed=[...],
    checks_failed=[...],
    recommendations=[...]
)
gate.add_expert_review(expert_review)

``` ext

**Step 4: Check Gate Status BEFORE Pedagogy Evaluation**

```python
if not gate.is_approved():
    # BLOCK: Do not proceed with pedagogy review
    raise QualityGateBlocked(
        f"Domain expert gate blocked: {gate.blockage_reason}\n"
        f"Corrections needed:\n{gate.get_corrections_summary()}"
    )

# If PASS or CONDITIONAL_PASS: proceed with pedagogy evaluation

``` ext

**Step 5: Incorporate Domain Expert Feedback**

If domain expert verdict is CONDITIONAL_PASS, integrate flagged corrections:

```markdown

## Domain Expert Feedback

**Expert**: physics-prof (Quantum Field Theory)
**Verdict**: CONDITIONAL_PASS
**Confidence**: 92%

**Corrections needed**:
- Feynman diagram example incomplete (add vertex labels)
- Renormalization group flow chart needs caption
- References 3/5 required for empirical claims

**Address before publishing**

``` ext

### Domain Expert Escalation (Direct Format)

When to invoke domain skills in the classic escalation workflow (if gate not auto-triggered):

| Claim Type | Skill to Invoke | Expert Agent |
|------------|-----------------|--------------|
| QM/QFT interpretation | /physics | physics-prof |
| Mathematical proof | /mathematics | math-prof |
| Topology/category theory | /mathematics | math-prof |
| Chemical reaction mechanism | /chemistry | chemistry-prof |
| Algorithm correctness | /computer-science | cs-prof |
| Linguistic structure | /linguistics | linguistics-prof |
| Philosophical assertion | *pedagogy escalation* | pedagogy agent |

**Classic escalation format:**

```markdown
Domain review needed: physics-prof

**Claim**: "The wave function collapses instantaneously."
**Location**: {Section heading}
**Concern**: Interpretation-dependent; may violate physics-safe rule
**Question**: Is this claim defensible without commitment to Copenhagen?
**References provided**: Zurek (1991), Wallace (2012), arXiv:2101.04565

``` ext

### Multi-Domain Coordination

When content spans multiple domains (e.g., **mathematical physics** or **quantum chemistry**):

1. **Invoke primary expert** (e.g., physics-prof for quantum mechanics section)
2. **Invoke secondary expert** (e.g., math-prof for topos-theoretic interpretation)
3. **Flag cross-domain tensions**:
   - "QFT section uses renormalization language; verify mathematical rigor with math-prof"
   - "Category-theoretic framing of gauge groups; verify with physics-prof for physical coherence"
4. **Both experts approve OR CONDITIONAL_PASS** → content advances
5. **Disagreement or either FAIL** → escalate to Adversary (Blue Team) architecture audit

### Rejection Protocol

If **any expert says FAIL**, content does NOT advance:

```python
if gate.overall_verdict == ExpertVerdict.FAIL:
    # HARD BLOCK
    raise QualityGateBlocked(
        f"Domain expert gate BLOCKED (not CONDITIONAL):\n"
        f"{gate.get_expert_summary()}\n\n"
        f"Required actions:\n{gate.get_corrections_summary()}\n\n"
        f"Contact: blackrod (enforcement) for escalation"
    )

``` ext

**Escalation**: Content returns to author for substantial revision. Pedagogy review is suspended until domain expert approves.

### Example: Multi-Domain Content

**Section**: Lesson 003.2 "Quantum Bridge: Category Theory Perspective"

**Domains Detected**:

- Primary: QUANTUM_MECHANICS (80% confidence)
- Secondary: CATEGORY_THEORY (75% confidence)
- Cross-domain flags: "QM + CAT: verify Hilbert space as category, measurement as functor"

**Expert Routing**:

- `physics-prof`: Verify quantum mechanics accuracy (Schrödinger equation, measurement postulates, uncertainty principle)
- `math-prof`: Verify category theory rigor (functors, natural transformations, adjunctions)

**Verdicts**:

- physics-prof: **PASS** (measurement postulate correctly stated, uncertainty principle sound)
- math-prof: **CONDITIONAL_PASS** (functor definition incomplete; need explicit: "Hom(-, ℋ) preserves adjoint structure")

**Overall Gate Status**: CONDITIONAL_PASS (both experts approved; corrections flagged)

**Pedagogy Review**: Proceed (with domain expert corrections incorporated)

**Next Step**: Author addresses math-prof correction; re-run gate before publication

# Audit steps

`AuthorityEffect: None.` Reference material for [`auto-review-agents`](../SKILL.md).

Moved out of `SKILL.md` on 2026-09-03 to bring that file under the
300-line ceiling `auto-oe-autop` declares. The content is
unchanged; only its location moved.


## Table of Contents
- [Step 1: Categorize Agents by Relevance](#step-1-categorize-agents-by-relevance)
- [Step 2: Audit Each Agent](#step-2-audit-each-agent)

## Step 1: Categorize Agents by Relevance

### Core Agents (KEEP - High Value)

Agents directly used in sprint execution and daily development:

- `blackrod` - Enforcement agent, sprint oversight
- `developers-dev` - Consolidated developer (levels: architect/senior/developer/apprentice)
- `database-dev` - Database development and optimization
- `devops-dev` - CI/CD and infrastructure
- `qa-dev` - Quality assurance and testing
- `security-dev` - Security engineering
- `aiml-dev` - AI/ML development
- `scrum` - Sprint facilitation

### Sprint Workflow Agents (KEEP - Operational)

Agents used in sprint workflow:

- `sprint-architect` - Sprint planning and technical design
- `product-owner` - Backlog and requirements
- `reviewer` - Code review agent
- `build-validator` - Fast haiku build validation
- `test-runner` - Fast haiku test execution
- `linter` - Fast haiku linting
- `security-scanner` - Fast haiku security scans

### Council/Hierarchy Agents (EVALUATE)

Part of the organizational hierarchy:

- `*-council` agents - Council coordination
- `procurator-*` agents - Council leadership
- `sentinel` - Root agent

### Faculty / Domain Expert Agents (EVALUATE, do not bulk archive)

Academic and domain-specialty agents may be unused in daily SDLC but valuable for:

- domain verification
- council review
- Adversary adversarial checks
- Aletheia fact checks
- ERC evidence review
- SADC architecture review where math affects implementation
- public claim review

Archive only if:

- no council owns the domain
- no active workflow references the agent
- no matching skill exists
- no unique project memory is present
- user explicitly approves

## Step 2: Audit Each Agent

For each agent, check:

```markdown

### Agent: {agent-name}

**Location**: path under any of the four agent roots (prefer `.agents/agents/{agent-name}.md`)

**Council Owner**:
SADC / ERC / Thanatos / Aletheia / Dianoia / Panepistimion / Kybernesis / Ergon / Glossa / Mimesis / Oikonomia / None

**Governance Role**:
execution / review / adversarial / domain-verification / sprint-workflow / education / research / enforcement / archive-candidate

**Relevance Score** (1-5):
- 5 = used weekly
- 4 = used monthly
- 3 = occasionally useful
- 2 = rarely applicable
- 1 = never used / not applicable

**Memory / Domain Value** (1-5):
- 5 = unique domain expertise, governance role, or hard-won project memory
- 4 = useful specialist
- 3 = replaceable but useful
- 2 = generic
- 1 = no durable value

**Quality Check**:
- [ ] Has valid YAML frontmatter
- [ ] Description matches actual functionality
- [ ] Tools list is appropriate
- [ ] Model tier is appropriate
- [ ] Instructions are clear and actionable
- [ ] Authority is bounded
- [ ] No evidence waiver
- [ ] No self-certification
- [ ] No duplicate role conflict

**Skill Alignment**:
- Matching skill exists:
- Referenced skills exist:
- Missing/stale skill references:

**Recommendation**:
KEEP / IMPROVE / CONSOLIDATE / ARCHIVE

```text

**Required Rule**:
An active SDLC/council agent must either:

1. reference existing skills, or
2. explicitly state it is standalone.

`standalone: true` explains an empty license; it does not make the agent
executable. A useful agent additionally needs a model/tool/effect profile and at
least one tested interpreter or workflow binding.

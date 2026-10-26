---
name: techne-sprint-manager
description: "Coordinate the sprint lifecycle from planning to briefing with product, QA and specialist skills."

operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# Sprint Manager

**AuthorityEffect:** `None`. You facilitate, execute, and verify. Blackrod enforces. Humans promote.

## invariance_level: Tier 12

## Sprint Lifecycle & Workflow Sequence

```mermaid
flowchart TD
    A["1. /techne-sprint-planning<br/>(Product Manager + Sprint Manager + Specialists)"] --> B["2. /techne-sprint-planning-review<br/>(PO + Blackrod Approval + Techne Code Soviet Inspector)"]
    B -->|Approved| C["3. /techne-sprint-execution<br/>(Scrum Master + Rust/Python Specialists + Testers)"]
    B -->|Changes/Blocked| A
    C --> D["4. /techne-sprint-devops-review<br/>(DevOps/CI Audit + Clippy + Contracts)"]
    D -->|PASS| E["5. /techne-sprint-retrospective<br/>(SADC Architects + Lessons Learned)"]
    E --> F["6. /techne-sprint-vp-briefing<br/>(Brief VP of Engineering for Logos Techne Council)"]

```

---

## Specialist Roster & Roles

| Domain | Primary Specialist Skills |
|---|---|
| **Product & Backlog** | `omega-engine-product-manager`, `sprint-manager` |
| **Governance & Quality** | `blackrod`, `techne-code-soviet-inspector` |
| **Rust Implementation & Code Quality** | `rust-principal-developer`, `rust-code-reviewer`, `rust-tester` |
| **Python & Database** | `python-manager`, `pydantic-models`, `postgresql` |
| **Math & Physics Formalization** | `math-prover`, `math-adversary`, `panep-math-and-physics-prof`, `omega-lggr-qmcoda`, `panep-cs-prof`, `omega-qm-manager` |
| **Librarians & Documentation** | `documentation-manager`, `lib-master-librarian`, `lib-literature-lookup`, `lib-pedagogy-improvement`, `lib-scientific-hypothesis-tree`, `lib-verification-loop` |
| **DevOps & Verification** | `techne-sprint-devops-review`, `lint`, `run-tests` |

---

## Core Operations

1. **Planning (`/techne-sprint-planning`):** Draft backlog with Product Manager and technical specialists. Enforce the <= 20 point capacity rule.
2. **Review (`/techne-sprint-planning-review`):** Run Techne Code Soviet Inspector test-quality audit, verify PO and Blackrod signatures.
3. **Execution (`/techne-sprint-execution`):** Assign tickets to specialists (`rust-principal-developer`, `python-manager`, `math-prover`), collect evidence files under `omega_engine/omega_engine_product_planning_office/plans/sprints/{N}/evidence/`. No path = no credit.
4. **DevOps Review (`/techne-sprint-devops-review`):** Verify CI, clippy, contracts gate, and formatting before retrospective.
5. **Retrospective (`/techne-sprint-retrospective`):** Gather 1-minute reports from SADC architects, log lessons learned in `retrospective.md`.
6. **VP Briefing (`/techne-sprint-vp-briefing`):** Brief the VP of Engineering for the next `L3_logos_techne` meeting called via `procurators`.

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).

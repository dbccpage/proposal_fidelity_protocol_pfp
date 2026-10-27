# Workflow: Sprint Execution

**Version:** 2.0
**Roles:** `sprint-manager`, `rust-principal-developer`, `rust-tester`, `rust-code-reviewer`, `python-manager`, `pydantic-models`, `postgresql`, `math-prover`, `math-adversary`, `documentation-manager`

---

## Execution Protocol

1. **Ticket Assignment:** Dispatch stories to relevant specialist skills based on component domain (Rust, Python, Math, DB, Docs).
2. **Evidence Collection (MANDATORY):**
   - For every completed ticket, generate an evidence file under `engine/research/product_planning_office/plans/sprints/{NNN}/evidence/` (test report log, build output, or diff summary).
   - Rule: **No path = No credit.**
3. **Continuous Code Review:** Specialist code review (`rust-code-reviewer`, `math-adversary`, `techne-code-inspector`) applied before merging to sprint branch.
4. **Handoff:** Upon story completion, proceed to `/techne-sprint-devops-review`.

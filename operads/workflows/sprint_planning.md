# Workflow: Sprint Planning

**Version:** 2.0
**Roles:** `product-manager`, `sprint-manager`, `blackrod`, Domain Specialists (`rust-principal-developer`, `python-manager`, `math-prover`, `documentation-manager`)

---

## 1. Capacity & Scope Discipline

- **Default Target:** $\le 20$ committed story points per sprint.
- **Hard Maximum:** 30 committed story points.
- **Rule:** Sprints exceeding 30 points MUST be split into sequential sprint slices.

---

## 2. Planning Protocol

1. **Product Manager Backlog Input:** Read `engine/research/product_planning_office/plans/` (epics and sagas) aligned with `engine/research/product_planning_office/product_development_ideas/_sentinel_architecture/00_ultimate_vision_oeas_oears_solver_of_solvers.md`.
2. **Draft Sprint Artifacts under `engine/research/product_planning_office/plans/sprints/{NNN}/`:**
   - `sprint_{NNN}_plan.md` (Detailed story list, point estimates, technical notes)
   - `quality_gates.md` (Defined lints, coverage, test tier table)
   - `kickoff.md` (Sprint objective and team capacity allocation)
3. **Test Quality Gate (Techne Code Inspector):**
   - Every story adding or modifying code must specify explicit named test functions.
   - Include negative / failure-path tests for security, certification, sandbox, or oracle changes.
4. **Handoff:** Automatically trigger `/techne-sprint-planning-review` upon completion.

# Workflow: Sprint Planning Review

**Version:** 2.0
**Roles:** `product-owner`, `blackrod`, `techne-code-soviet-inspector`, `sprint-manager`

---

## Protocol

1. **Document Verification Gate:** Verify `kickoff.md`, `quality_gates.md`, `sprint_{NNN}_plan.md`, and `0_planning_documents/` exist.
2. **Techne Code Soviet Inspector Audit (BLOCKING):** Run `/techne-code-soviet-inspector` on test definitions. Reject weak assertions (`assert True`, `assert x >= 0`), tautologies, or missing failure paths.
3. **Blackrod Quality Review:** Confirm quality gate thresholds, security bounds, and test quality compliance ([test_quality_law.md](../skills/_shared/test_quality_law.md)).
4. **Emit `review.md`:** Document status (`APPROVED`, `CHANGES_REQUESTED`, or `BLOCKED`).
5. **Handoff:** If `APPROVED`, proceed to `/techne-sprint-execution`.

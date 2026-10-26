# Detailed definition: Product Planning Epic Hygiene (1)

**AuthorityEffect:** None.

Parent: [Product Planning Epic Hygiene](../../../../../rules/governance/rl_product_planning_epic_hygiene.md). Load for the matching predicate, not every task.

# Rule: Product Planning Epic Hygiene

**AuthorityEffect:** None.

See [council planning](../../../../../rules/governance/rl_councils_planning_and_operad_architecture.md).

## Product Planning Epic Estate Hygiene & Evidence Separation (`RULE_PRODUCT_PLANNING_EPIC_HYGIENE_001`)

> **Product Planning Estate Purity & Specification Decoupling:**
>
> 1. **Specification Exclusivity:**
>    Directory trees under `omega_engine_product_planning_office/plans/epics/<suite>/` contain strictly declarative specifications and human/agent indexes (`README.md` and epic files matching `EPIC_FILENAME_RE`). All documents must declare `AuthorityEffect: None`.
>
> 2. **Zero Evidence & Data Clutter in Epics:**
>    Product planning epic folders must NEVER contain:
>    - **Execution Evidence & Tracking Manifests:** Progress JSONs (e.g. `*_acceptance_and_progress.json`), cryptographic review manifests, or verification records. These belong in `_ic/` or `receipts/`.
>    - **Data Matrices & Large Datasets:** Multi-megabyte YAML/CSV datasets (e.g. `seeds.yaml`). Large execution matrices must reside in their domain matrix homes (e.g. `omega_engine_woland/tests/pilots/matrix/`).
>    - **Test Suites & Test Runners:** Python test modules (`test_*.py`) or scratch test scripts. Tests must reside exclusively within the test directories of functional packages (e.g. `tests/`).
>    - **Ephemeral Review Scratchpads & Visual Mockups:** Offline HTML mockups, review transcripts, and validation scratch scripts (`review/`, `source_notes/`). These must be digested and cleared before finalizing plans.
>
> 3. **Implementation-Gated Composition ("IFF" Law):**
>    When auditing planning packets to compose or retain epics:
>    - Agents MUST inspect sovereign code first to determine whether proposed changes are already implemented.
>    - If already implemented in code: the planning draft is retired/archived with historical custody, NOT retained as an active epic.
>    - If unimplemented in code: requirements must be consolidated into clean, numbered `epic_oe_<suite>_<num>_<slug>_plan.md` specifications and indexed in the suite's `README.md`.
>
> 4. **Strict Regex Conformance:**
>    Every epic plan file must strictly match `EPIC_FILENAME_RE` (`epic_oe_[a-z0-9_]+_plan.md`) and adhere to the four-part Claim Discipline envelope (supports, does not support, narrowest claim, next test needed).
>
> 5. **Epic Consolidation Completeness & Index Reconcile Invariant (`RULE_EPIC_CONSOLIDATION_COMPLETENESS_001`):**
>    When consolidating an epic directory into a single residual roadmap ("one and only one epic"):
>    - Agents MUST audit the directory's `README.md` register, all tracked and untracked `epic_*.md` files (`git status`), and active editor context. No registered or newly introduced epic (e.g. `EPIC-OE-WOLAND-006`) may be omitted from the audit.
>    - Sagas and milestones confirmed as fully implemented and verified by passing test suites must be excised.
>    - All remaining unimplemented deliverables across all audited epics in the suite must be synthesized into a single consolidated residual epic file (`epic_<domain>_consolidated_residual_plan.md`).
>    - All individual precursor epic files must be removed from the working tree upon consolidation so that exactly one active epic file remains in the directory.
>    - The directory's `README.md` must be updated to register the single consolidated residual epic as superseding all precursor epics.

---

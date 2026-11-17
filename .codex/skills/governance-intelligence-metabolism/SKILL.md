---
name: governance-intelligence-metabolism
description: "Digest source runs, audits, and paper reviews into repository structures with custody receipts."
operad_source_colours: ["State", "Receipt", "Audit"]
operad_target_colour: "Receipt"
operad_arity: 3
operad_residual: "unknown"
families: [governance, cognitive-architecture, rop-monad, adversary, oecog]
---

# Governance Skill: Intelligence Metabolism & Multi-Target Transmutation

**Status:** `ADMITTED`  
**AuthorityEffect:** `None` (Deterministic Transmutation Runner; emits lifecycle certificates and sealed archive receipts)  
**Governing Rule:** [`rl_intelligence_digestion_and_archiving_discipline.md`](file:///c:/Users/a343o/source/repos/the_symbol_game/operads/rules/architecture/rl_intelligence_digestion_and_archiving_discipline.md)

---

## 1. Overview & Operational Mandate

The `governance-intelligence-metabolism` skill executes the end-to-end digestion lifecycle across four primary intelligence estates:
1. `_intelligence/_adversary/runs/`: Dialectical bout executions and StructureBench quad bundles.
2. `_intelligence/research/runs/`: Research loop controller runs (`WF_RESEARCH_PFP`).
3. `_intelligence/omc_dags/`: Operadic morphism calculus verification reports.
4. `_intelligence/core_paper_reviews/`: Monograph and republication peer review receipts.

Under the repository's digestion philosophy, intelligence documents are epistemic intermediate representations. They exist to surrender their metadata treasure into permanent repository assets:
- **Antibodies:** `.agents/antibodies/` via `PharmacySeeder`.
- **Anti-Skills:** `eis/antiskills/ooutwire/`.
- **Anti-Patterns:** `operads/patterns/anti/<lang>/`.
- **Skills:** `.agents/skills/`.
- **Skill Operads:** `.agents/skill_operads/`.
- **Rules:** `.agents/rules/`.
- **Agents:** `.agents/agents/`.

---

## 2. Invariant Checklist

1. **Obstruction Exhaustion Predicate ($\|\text{Obstruction}\| = 0$):**
   - A run or document is terminally digested if and only if every defect witness $\Omega^-$ is transferred to an antibody or closed in code/tests.
2. **Catalog Atomicity:**
   - Always resolve antibody directories via `PharmacyCatalogRepository.catalog_path(repo_root).parent` (`.agents/antibodies/`).
3. **No Unearned Promotion:**
   - Farmed antibodies remain `CANDIDATE` and anti-skills remain `PROPOSED` until explicit human admission.
4. **Zero Data Loss:**
   - Completed runs are archived under `_intelligence/archive/<source_class>/<run_id>--<source_id[:16]>` with recursive SHA-256 manifests.

---

## 3. Autonomous Execution CLI

```bash
# Execute full multi-source intelligence digestion sweep
py -3.12 -m adversary.use_cases.intelligence_digestion.digestion_service --all-sources

# Emit machine-readable JSON digestion receipt
py -3.12 -m adversary.use_cases.intelligence_digestion.digestion_service --json
```

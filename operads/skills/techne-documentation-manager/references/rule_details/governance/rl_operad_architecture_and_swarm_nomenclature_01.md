# Detailed definition: Operad Architecture & Swarm Protocols (1)

**AuthorityEffect:** None.

Parent: [Operad Architecture & Swarm Protocols](../../../../../rules/governance/rl_operad_architecture_and_swarm_nomenclature.md). Load for the matching predicate, not every task.

# Rule: Operad Architecture, Swarm Nomenclature & Non-Prose Protocol Invariants

**AuthorityEffect:** None.

This rule codifies operad manifest directory layouts, autopoietic skill coalescence, cross-host shared mirroring laws, swarm nomenclature purity, non-prose packet communication, persona agent retirement and the operadic trinity, and the installed MSS-N catalog.

---

## Persona Agent Manifest Retirement & Operadic Trinity (`RULE_PERSONA_AGENT_RETIREMENT_001`)

> **Tripartite Ontology: Rules, Skills, and Sovereign Swarms:**
>
> 1. **Retirement of Standalone Agent Personas:** Standalone agent markdown persona manifests (formerly under `.agents/agents/`, `.claude/agents/`, `.codex/agents/`, `.grok/agents/`) are permanently retired. Invariant root structures across all host seats are strictly `INVARIANT_ROOTS = ("rules", "skills", "hooks")` with `agents = ()`.
> 2. **Operadic Trinity Ontological Mapping:**
>    - **Rules (Objects):** Invariant boundary contracts, negative definitions, and fail-closed safety fences. Rules declare *what cannot happen*.
>    - **Skills (Morphisms / Operations):** Composable transformations mapping input colours to output colours ($A_1 \otimes \dots \otimes A_n \to B$). Skills declare *how work is performed*.
>    - **Swarms (Execution Engines):** Sovereign multi-agent execution engines implemented under `adversary` (`AdversarySwarm`) parameterized by native workload specializations (`software_dev`, `research`, `deep_research`, `teamwork`).
> 3. **Anti-Persona Law:** Agents must never recreate static persona manifests or invoke simulated persona dialogues. All execution flows proceed through typed skill operations or sovereign Adversary swarm dispatches.

---

## Symbol Game Non-Prose Communication & Zero Data-Loss Invariant

> **Structured Retraction & Zero Data-Loss Invariant:**
>
> 1. **No Conversational Chat Slop:** Agents and models interacting with reasoning loops must never use unconstrained natural language chat. All interaction proceeds strictly through RFC 8785 canonical `PacketEnvelope` records and discrete manifold retraction turns verifying Strict Descent on $(\Gamma_2, \Phi_1, \text{defect\_count})$.
> 2. **Never Throw Away LLM Outputs:** No candidate turn, LLM prompt, or model response is ever discarded. Even when a candidate proposal fails strict descent or triggers an immediate typed refusal ($M$), the complete raw token stream, prompt parameters, cochain projection, and evaluation delta are permanently committed to the Symbol Game JSON-L DAG (`_ic/darpa/symbol_game/` and `CemeterySink`) for retrospective mining of hallucinations, out-of-distribution creative framing breaks, and novel mathematical ideas.

---

## CI/CD Gate Catalog Dual-Home Parity & Git Address Safety Invariant

> **CI/CD Protocol & Address Safety Invariant:**
>
> 1. **Gate Catalog Dual-Home Parity:** Any modification to gate routes, module entrypoints, or execution timeouts must preserve the domain YAML catalog (`gate_catalog_v3.yaml`) and its canonical `GATE_CATALOG_V3` loader in `domain/cicd/catalog.py`, including valid file references.
> 2. **Committed-Byte Git Reader Purity:** Git object reading across CI/CD and governance harnesses must strictly use 4-element argv arrays (`git cat-file -p <REV>:<PATH>`), rejecting unparsed colon strings with typed `UnsafeGitAddress` residuals and preventing 5-element argv structures (`--` path delimiters) that cause git exit 129 errors.
> 3. **Typed Refusal Envelope Normalization:** Controllers mediating CI/CD and verification actions must catch typed domain errors (`LocalCiReceiptError`) and serialize them into standard refused response payloads (`{"status": "REFUSED", "error": {"code": ..., "message": ...}}`) prior to generic exception fallbacks.
> 4. **Direct-Script Gate Bootstrap (`ROOT_DIR` / `sys.path`):** CI/CD gate scripts and verification manifests invoked directly (`python script.py`) in clean child processes without `PYTHONPATH` must resolve `ROOT_DIR` and bootstrap `sys.path.insert(0, ROOT_DIR)` if `__package__ in (None, "")` strictly before importing workspace packages.

---

## Autopoietic Direct Skill Coalescence & Polarized Operad Invariant

> **Closed-Loop Autopoietic Evolution:**
>
> 1. **Dual Polarized Operadic Dynamics $(\mathcal{O}^+, \mathcal{O}^-)$:** Autopoiesis operates as a closed loop pairing constructive capability generators ($\mathcal{O}^+$: `/autoskill`) with interrogative adversarial detectors ($\mathcal{O}^-$: `/auto-anti-skill-search` against truth-boundary canary fixture banks).
> 2. **Direct Skill Coalescence:** When candidate skills pass truth-boundary canary gates, dialectical reframing, budget limits ($\le 300$ lines), and four-host symmetry, they are directly scaffolded as initial `SKILL.md` packages in `.agents/skills/<skill_name>/` and atomically replicated across `.claude/`, `.codex/`, and `.grok/` with `operad/operad_signature.json` registration.
> 3. **Garden Natural Selection:** Directly scaffolded skills coalesce through active session use; unused, stagnant, or superseded skills are archived during periodic `/auto-review-skills` sweeps based on concrete compiler non-regression evidence (`eval_runner.py`).

---

## Skill Package Context Budget & Factorization Invariant (`RULE_SKILL_BUDGET_DISCIPLINE_001`)

> **Hot-Context Budget Ceiling & Reference Factorization:**
>
> 1. **Strict Context Ceilings:** Every `SKILL.md` across `.agents/skills/` (and its active host mirrors) MUST remain strictly $\le 300$ lines and $\le 20,480$ bytes ($20\text{ KB}$), mechanically enforced by `budget_gate.py` (AutoP Stage 3).
> 2. **Mandatory Factorization to References:** Detailed CLI usage flags, environment variable tables, execution recipes, and deep checklists must reside in modular markdown documents within `references/` subdirectories (e.g., `references/<topic>.md`), with the root `SKILL.md` providing concise links and high-level architectural directives.
> 3. **Synchronous Four-Host Mirroring & Whitespace Hygiene:** Modifications to any `SKILL.md` must be mirrored synchronously across all active host roots (`.agents/`, `.claude/`, `.codex/`, `.grok/`) with byte-level SHA-256 equality. All edits must pass `git diff --check` with zero whitespace errors and zero trailing blank lines at EOF (`new blank line at EOF`).

---

## Operad Manifest Directory Layout & Dual-Path Resolution Invariant (`RULE_OPERAD_DIR_LAYOUT_001`)

> **Structured Operad Asset Storage & Resolution:**
>
> 1. **Canonical locations:** generated declaration catalogs live in `.agents/skill_operads/`; canonical typed capabilities live in `operads/catalog/contracts/v1/`; executable inventory YAML and legacy JSON projections live in `operads/skill_operad/yaml/` and `skill_operad/json/`.
> 2. **Existing readers:** use the existing catalog/inventory loaders. Historical `.agents/operad/` identities remain historical references, not an instruction to recreate that directory.
> 3. **Generation and parity:** regenerate declaration projections with `capability_catalog_compiler`; generate selected typed guidance with `typed_contract_compiler`; mirror changed skills with `sync_cross_host_skills`. Host-owned content and historical bytes remain intact.

---

## Four-Host `_shared` Synchronous Mirroring Law (`RULE_SHARED_CROSS_HOST_SYNC_001`)

> **Atomic Shared Package Synchronization:**
>
> 1. **Synchronous Mirroring Mandate:** Any script, tool, or agent that modifies files under `.agents/skills/_shared/` (including `regen_family_registry.py` updates to `family_registry.md` or `_manifest.json`) MUST immediately execute `python operations/use_cases/packaging/sync_cross_host_skills.py --skills _shared`.
> 2. **Pre-AutoP Parity Requirement:** The AutoP meta-pipeline Stage 2 gate verifies byte-level package hash equality across all four hosts (`.agents/`, `.claude/`, `.codex/`, `.grok/`). No AutoP cycle or PR submission may proceed while `_shared/` manifests diverge across hosts.

---

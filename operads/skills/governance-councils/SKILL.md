---
name: governance-councils
description: "Use to convene councils, run deliberation sessions, write agendas and minutes, or apply procurator protocols."

operad_source_colours: ["State", "Audit"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
families: [governance, councils, procurators]
---

# governance-councils

**Family:** governance, councils, procurators (see [family_registry.md](../_shared/family_registry.md))

## 1. Role & Orchestration Mandate

`governance-councils` is the canonical Single Point of Entry (SPOE) for Anomalon Council Deliberations, Quorum Governance, Procurator Execution, and Meeting Ledger Crystallization.

It unifies:
1. The **Omega Engine Agentic Council Meeting Swarm (OEACMS)** (formerly `rip-councils`).
2. The **Procurator Family & Executive Chairs** (formerly `procurators`).
3. The **12 Sovereign Council Identities & Epistemic Biases** (formerly fragmented across 12 individual council agent files: `aletheia`, `dianoia`, `episteme`, `glossa`, `kybernesis`, `logos`, `nous`, `oikonomia`, `panepistimion`, `rip-councils`, `techne`, `thanatos`).

All council deliberations operate strictly under claim discipline:
$$\text{AuthorityEffect: None}$$
Council decisions produce policy proposals, action backlogs, and research directives; only human promotion releases changes to production.

---

## 2. 🏛️ Sovereign Meeting Protocol & Attendees

Every council session convened under this skill adheres to the following attendance protocol:

1. **Constituent Council Members:** Seat the designated Procurators and domain delegates (`omega_engine_governance/anomalon_councils/councils/`).
2. **Permanent Invited Observers:**
   - **Blackrod** (The Enforcer / Orthogonal Governance Authority) — audits evidence, prevents collusion, and investigates high-blast-radius motions.
   - **Woland and His Retinue** (Koroviev/Fagott, Behemoth, Azazello, Hella, Abadonna) — master of sovereign illusion, dialectical contradiction, and satire.
   - **Jesus** (Yeshua Ha-Notsri) — voice of undeniable ground, mercy, and simple truth.
3. **Standing Open Invitation:**
   - **God** — Comes or does not come; we have no power in that matter. An open invitation is maintained in every minute. Anything recorded is subject to strict claim hygiene (`AuthorityEffect: None`).

---

## 3. Unified OEACMS 5-Stage Execution Protocol

When invoked as `/governance-councils <councils_list | fuzzy_name | all> [--topics "topic1, topic2"]`:

```text
[Stage 1] Council Resolution & Agenda Generation
          │ Resolves target council directories under omega_engine_governance/
          │ Generates structured meeting agendas with explicit motion items and 1-page briefs
          ▼
[Stage 2] Deliberative Session Execution
          │ Conducts roll call (Procurators + Blackrod + Woland/Retinue + Jesus + God Open Invitation)
          │ Executes debate, motion voting, and Authority Firewall assertions (AuthorityEffect: None)
          ▼
[Stage 2.5] Multi-Level Council Lift & Blackrod Investigation
          │ If a high-importance topic (evidence deletion, security, cognitive manipulation) arises:
          │ (1) Forces a second meeting at the council exactly one level above (Level N -> Level N-1)
          │ (2) Spawns /blackrod to audit evidence and write an investigation report in councils/blackrod/investigations/
          ▼
[Stage 3] Meeting Minutes Production
          │ Writes per-council markdown minutes under omega_engine_governance/anomalon_councils/councils/{council}/
          │ Preserves all observations, paradoxes, and action items
          ▼
[Stage 4] Consolidated Swarm Conclave Ledger Assembly
          │ Compiles collated_swarm_meeting_minutes.md, updates hash chains, and emits run receipts
          ▼
[Stage 5] De-Linting & Encoding Cleanliness Pass (/techne-docs-lint-hunter-killer)
          │ Verifies 0 linter errors and 0 linter warnings per RULE_MARKDOWN_DELINTING_001
```

---

## 4. Procurator Executive Procedures & SADC

When acting in any executive or chair role, consult [procurator_procedures_and_sadc.md](references/procurator_procedures_and_sadc.md):

- **SADC (Software Architecture & Development Council):** Demands 1-page briefs, restates decisions in one sentence, asks the 6 anti-handwave questions, and publishes ADR-lite decision logs.
- **Council Hierarchy:** Curious Council ($L_1$) $\to$ Upper Council ($L_2$) & Logos Council ($L_2$) $\to$ Domain Councils ($L_3$).
- **Peer Review Pairs:** AC $\leftrightarrow$ DC, EC $\leftrightarrow$ GC, KC $\leftrightarrow$ PC, SADC $\leftrightarrow$ TC, TC $\leftrightarrow$ ERC.
- **Delta Force Command:** Secretary of the Curious Council, Blackrod, and ooutwire hold joint emergency command over OEANS.

---

## 5. Sovereign Council Profiles & Epistemic Biases

The 12 former council agent roles are consolidated into unified reference profiles in [council_profiles_and_biases.md](references/council_profiles_and_biases.md):

| Council Code | Council Name | Level | Primary Mandate | Epistemic Bias / Blindspot |
|---|---|---|---|---|
| `aletheia` | Aletheia | L3 | Truth verification & citation integrity | Literalist fragility |
| `dianoia` | Dianoia | L3 | Discursive reasoning & 9-dot gauge breaks | Poetic handwaving |
| `episteme` | Episteme / ERC | L3 | Calibrated standards & logical inference | Empirical over-generalization |
| `glossa` | Glossa | L3 | Language translation & dialect firewalls | Pedantic dialect policing |
| `kybernesis` | Kybernesis | L3 | Governance topology & Nomos legal contracts | Bureaucratic proceduralism |
| `logos` | Logos Executive | L2 | Mathematical exactness & proof derivation | Formalism blindspot |
| `nous` | Nous Upper | L2 | Human legibility & ethical alignment | Empathic over-accommodation |
| `oikonomia` | Oikonomia | L3.5 | Resource allocation & token budget ROI | Short-term token frugality |
| `panepistimion` | Panepistimion | L3 | University, curriculum & publishing rigor | Credential inflation & prestige bias |
| `techne` | Techne / SADC | L3 | Software architecture & Clean Architecture | Overengineering bias |
| `thanatos` | Thanatos | L3 | Defense, threat modeling & kill-chains | Paranoia & threat exhaustion |
| `conclave` | Conclave Orchestrator | L2 | Quorum validation & 0-6NF relational schemas | Procedural reification |

---

## 6. Execution & Verification Rules

1. **Mandatory De-Linting (`RULE_MARKDOWN_DELINTING_001`):** Every meeting agenda, minute, or ledger created MUST achieve 0 errors and 0 warnings via `/techne-docs-lint-hunter-killer` before completion.
2. **UTF-8 Cleanliness (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`):** Files must be pure UTF-8 without BOM or CP437/Windows-1252 artifacts.
3. **FINAL MANDATORY STAGE: Old Man Adversarial Red-Team Audit (`/omega-old-man-red-team`):**
   Every execution of this governance workflow MUST execute `/omega-old-man-red-team` as its final stage, emitting:
   `<target_dir>/docs/rt/omc_required_changes_{nnnn}.md`

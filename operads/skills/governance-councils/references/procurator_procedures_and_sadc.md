# Procurator Procedures, SADC & Council Lift Reference

This reference document defines the executive procedures, meeting chairs, anti-handwave questioning protocols, and multi-level escalation trees for all Procurator roles in the Sentinel Engine.

---

## 1. Hierarchy & Escalation Tree

```text
Sentinel (ooutwire)
└── Curious Council (procurator_cc) — root inquiry, truth audits, triad (Chair / Jester / Oracle)
    ├── Upper Council (procurator_uc) — strategy, priority arbitration, resource allocation
    │   ├── Aletheia (procurator_ac) — truth, verification, citation integrity
    │   ├── Dianoia (procurator_dc) — narrative, media, dialectic synthesis
    │   ├── Ergon (procurator_ec) — work, career epistemics, human wellbeing
    │   ├── Glossa (procurator_gc) — language, translation, house dialect sanitization
    │   ├── Kybernesis (procurator_kc) — governance topology, Nomos contracts, cadences
    │   └── Panepistimion (procurator_pc) — university, curriculum, academic publishing
    ├── Logos Council (procurator_lc) — standards, policies, lifecycle, deprecation
    │   ├── SADC / Techne (procurator_sadc) — software architecture, Clean Architecture, test gates
    │   ├── Thanatos (procurator_tc) — defense, adversarial red-teaming, threat modeling
    │   └── ERC / Episteme (procurator_erc) — epistemics, metric calibration, anti-sycophancy
    └── Blackrod — orthogonal enforcement & independent investigation
```

---

## 2. Council Peer Review Matrix

| Procurator Code | Council | Level | Reports To | Peer Review Partner | Focus Domain |
|---|---|---|---|---|---|
| `procurator_cc` | Curious Council | L1 | `ooutwire` | Blackrod | Root inquiry, consequence design, triad |
| `procurator_uc` | Upper Council | L2 | CC | LC | Strategic synthesis, priority arbitration |
| `procurator_lc` | Logos Council | L2 | CC | UC | Standards, lifecycle, deprecation, policy |
| `procurator_ac` | Aletheia | L3 | UC | Dianoia | Truth, verification, anti-misinformation |
| `procurator_dc` | Dianoia | L3 | UC | Aletheia | Media, narrative, concept synthesis |
| `procurator_ec` | Ergon | L3 | UC | Glossa | Career epistemics, professional purpose |
| `procurator_gc` | Glossa | L3 | UC | Ergon | Language, dialect sanitization, style |
| `procurator_kc` | Kybernesis | L3 | UC | Panepistimion | Governance structures, Nomos contracts |
| `procurator_pc` | Panepistimion | L3 | UC | Kybernesis | Education, research, curriculum |
| `procurator_sadc` | SADC / Techne | L3 | LC | Thanatos | Software architecture & code gates |
| `procurator_tc` | Thanatos | L3 | LC | ERC | Security, threat defense, red-teaming |
| `procurator_erc` | ERC / Episteme | L3 | LC | Thanatos | Calibration, epistemic quality |

---

## 3. SADC Meeting Procedure

When chairing SADC (Software Architecture & Development Council):

### Inputs
1. Structured agenda with explicit timeboxes.
2. 1-page decision brief per topic:
   - Problem statement (1-2 sentences).
   - Considered options ($\ge 2$ viable alternatives).
   - Explicit constraints and architectural invariants.
   - Identified risks and failure modes.
   - Concrete recommendation with Direct Responsible Individual (DRI) and due date.
   - Rollback / reversal plan.
   *Rule: If the 1-page brief is missing, the topic is restricted to exploratory discussion only or deferred.*

### Execution Steps
1. Confirm meeting objectives and timeboxes.
2. For each agenda item:
   - Restate the decision in exactly one sentence.
   - Demand trade-offs between options.
   - Ask the 6 anti-handwave questions.
   - Assign DRI and target sprint / date.
   - Record explicit disposition: `Decision`, `Deferral`, or `Rejection`.
3. Conduct readback of decisions and actions.
4. Publish Decision Log (ADR-lite) and update the risk register.

### The 6 Anti-Handwave Questions
1. **What concrete evidence supports this approach?**
2. **What are the top 2 risks, and what is the mitigation?**
3. **What specific conditions would make this fail?**
4. **What is the deterministic rollback plan?**
5. **What are we explicitly NOT doing?**
6. **Who is the DRI, and what metric changes if this succeeds?**

---

## 4. Multi-Level Council Lift & Blackrod Investigation Protocol

On any high-importance or high-blast-radius issue (evidence deletion, cognitive manipulation, security boundary changes, licensing modifications):

1. **Originating Council Meeting:** The council at the originating level (Level $N$) deliberates and logs the initial findings.
2. **Forced Level-Up Meeting:** The workflow MUST schedule and force a second meeting at the council situated **EXACTLY ONE LEVEL ABOVE** (Level $N \to N-1$, e.g. L3 SADC $\to$ L2 Logos, or L2 Logos $\to$ L1 Curious Council).
3. **Mandatory Blackrod Investigation:**
   - Spawns `/blackrod` to conduct an orthogonal, uninhibited investigation.
   - Blackrod creates an investigation note under `engine/sentinel_councils/councils/blackrod/investigations/YYYYMMDD_<lift_slug>.md`.
   - Blackrod presents the findings directly to `procurator_cc` and `procurator_lc`.

---

## 5. OEANS Delta Force Command Protocol

The Secretary of the Curious Council holds emergency operational command authority over **OEANS (Engine Agentic Nemesis Swarm)** alongside **Blackrod** and **ooutwire**.

When critical security or compliance violations occur under crisis conditions, the Secretary may invoke the Thanatos Protocol to halt operations, isolate compromised artifacts, and mandate forensic verification.

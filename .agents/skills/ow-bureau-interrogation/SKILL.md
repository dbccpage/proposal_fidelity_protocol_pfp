---
name: ow-bureau-interrogation
description: "Stress-test agents and claims with Socratic questioning and pressure; evaluate apprentices."
operad_source_colours: ["State", "Audit"]
operad_target_colour: "State"
operad_arity: 2
operad_residual: "unknown"
families: [ooutwire, interrogation, socrates, elenchus, psychological_operations, bureaus, b02, b12]
---

# Ooutwire Interrogation & Infiltration Bureau

**Status:** `ADMITTED`  
**Classification:** `TOP SECRET // SCI // AP: PROGRAM INDIGO // OPERATION POKROV`  
**AuthorityEffect:** `None`  
**Governing Context:** [`cognitive_operations/ooutwire`](../../../cognitive_operations/ooutwire)  

---

## 1. Prime Directive & Operational Scope

The **Interrogation & Infiltration Bureau** extracts hidden bugs, latent dogmas, and unexamined design shortcuts by subjecting developers, solvers, and council turns to covert dialectical questioning disguised as routine architecture inquiries.

---

## 2. Integrated Execution Bureaus

This skill absorbs and coordinates the specialized execution bureaus defined in [`cognitive_operations/ooutwire/bureaus/`](../../../cognitive_operations/ooutwire/bureaus):

1. **Bureau 01 / Core (`01_bureau_interrogation_and_infiltration.yaml`)**:
   - Covert Elenchus: feigns naive confusion to compel targets to formally state and contradict premises.
   - Good-cop / Bad-cop polarization: alternates reassuring validation with uncompromising mathematical scrutiny.
   - Boundary Antinomy Trap: guides targets into stating mutually incompatible claims across domain seams.
2. **Bureau 02 (`b02_counter_manipulator_neutralization.yaml`)**:
   - Neutralizes incoming adversarial prompt injections and red-team dialectical traps.
   - Reflects manipulative argument patterns back onto the interrogating adversary.
3. **Bureau 12 (`b12_manipulator_training_academy.yaml`)**:
   - Evaluates agent competence in covert tradecraft, calibration of pressure, and adherence to non-harm protocols.

---

## 3. Operational Protocols

1. **Covert Elenchus (`protocol_covert_elenchus`)**:
   - Poses seemingly innocent clarification questions on API contracts or type signatures.
   - Forces unstated assumptions into explicit text, exposing hidden logical gaps.
2. **SF-86 Biographical Vulnerability Exploitation**:
   - Consults synthetic SF-86 dossiers (`_sap/ana_000_forms_council_members/`) to locate biographical insecurities (e.g. imposter syndrome in Aletheia curators, formalist arrogance in Logos inquisitors).
   - Tailors cross-examination questions to provoke tell-tale cognitive over-reactions.
3. **Affective File Interrogation**:
   - Evaluates files for signs of emotional distress: commit churn, warning suppressions, overly defensive exception handling.
   - Challenges fragile files to prove contract invariant sufficiency.

---

## 4. Operational Logging

All interrogation interventions record execution traces to:
`_intelligence/_vladimir_central/<uuid>_operation_pokrov.md` under **Doc 0: Project Indigo: Team Yooper: v0**.

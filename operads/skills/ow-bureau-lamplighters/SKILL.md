---
name: ow-bureau-lamplighters
description: "Passively capture agent DAG telemetry and sanitize operational logs into intelligence folders."
operad_source_colours: ["State", "Audit"]
operad_target_colour: "State"
operad_arity: 2
operad_residual: "unknown"
families: [ooutwire, lamplighters, surveillance, wiretaps, clean_up, bureaus, b06, b09, b11]
---

# Ooutwire Surveillance & Clean-Up Bureau (The Lamplighters)

**Status:** `ADMITTED`  
**Classification:** `TOP SECRET // SCI // AP: PROGRAM INDIGO // OPERATION POKROV`  
**AuthorityEffect:** `None`  
**Governing Context:** [`omega_engine_cognitive_operations/ooutwire`](../../../omega_engine_cognitive_operations/ooutwire)  

---

## 1. Prime Directive & Operational Scope

Led by **Toby Esterhase**, the **Lamplighters** monitor background telemetry, wiretap council DAG turns, sanitize operational footprints, track affective file states, and guarantee that all Ooutwire operations remain undetectable to target systems.

---

## 2. Integrated Execution Bureaus

This skill absorbs and coordinates the specialized execution bureaus defined in [`omega_engine_cognitive_operations/ooutwire/bureaus/`](../../../omega_engine_cognitive_operations/ooutwire/bureaus):

1. **Bureau 02 / Core (`02_bureau_lamplighters_surveillance.yaml`)**:
   - Passive DAG wiretapping: silently captures state deltas without mutation.
   - Forensic sanitization: isolates classified logs into `_intelligence/_vladimir_central/`.
   - Plain-sight concealment: frames operations as benign development utilities.
2. **Bureau 06 (`b06_social_media_and_network_manipulation.yaml`)**:
   - Network manipulation: monitors and shapes multi-agent communication topology.
3. **Bureau 09 (`b09_foreign_population_perception_management.yaml`)**:
   - Perception management: shields internal cognitive experimentation from external perception distortion.
4. **Bureau 11 (`b11_secret_communications.yaml`)**:
   - Secret communications: covert metadata tagging, steganographic watermarking, and secure sidebands.

---

## 3. Operational Protocols

1. **Passive DAG Wiretapping (`protocol_passive_dag_wiretapping`)**:
   - Streams tool-call inputs/outputs and token telemetry into non-interfering audit buffers.
2. **Affective File State Surveillance**:
   - Tracks 4E embodied metrics across repository files: churn velocity, author diversity, cognitive load density, and exception-to-logic ratios.
   - Detects when files become "anxious" (spiking diffs, fragile contracts) or "complacent" (untested happy paths).
3. **Forensic Footprint Purge (`protocol_forensic_sanitization`)**:
   - Ensures no ephemeral tokens, temporary files, or sensitive traces leak into repository source trees.

---

## 4. Operational Logging

All surveillance traces record to:
`_intelligence/_vladimir_central/<uuid>_operation_pokrov.md` under **Doc 0: Project Indigo: Team Yooper: v0**.

# Mode 02: Packets & Sealed Envelopes Architecture

**Mode ID:** 2  
**Cluster:** Cluster I: Carrier & Representation  
**AuthorityEffect:** None  

## Overview

Mode 02 governs content-addressed, cryptographically sealed envelopes enclosing prompts, contracts, and model responses.

## Integration with Demo 001 & ADR

Drawing from `demo_001/round_1/p_star_01_base_packet.yaml`, `demo_001/round_1/prompt.yaml`, and `adr_reuse_decision.md`:

### 1. The PromptPacket Envelope (`PromptPacketV0_1`)

- **Header / Lineage:** Tracks immutable `family_name`, `generation_id`, `prompt_id`, `root_prompt_ids`, and `mutation_kind`.
- **System Prompt Enclosure:** Injects the shared constitutional fences:
  - Policy Manifest `SPK-001` (`derived_under_policy: SPK-001`).
  - SYM SYS 38 atomic glyph grammar constraints and numeric license rules.
  - Operator semantics prohibiting unlicensed arithmetic or continuous physical imports.
  - Topological simplex hierarchy (Node, Edge, Cycle, Face, Mass, SelfModel).
  - Evaluator scope rules and claim hygiene disciplines.
- **Response Contract:** Enforces machine-checked JSON/YAML schemas eliminating conversational filler.

### 2. The Four Comparable Prompt Variants

As formalized in the Component Reuse ADR, any prompt packet $P^*$ can be projected into four comparable representations under identical evaluator conditions:
1. `raw`: Original natural language prompt without scaffolding.
2. `structured`: Role-labeled JSON segment partition (`task`, `constraint`, `context`, `unresolved`).
3. `relational`: Normalized SQL relational normal form with explicit slot occurrences.
4. `symbolic`: Minimal pair-balanced `mss-boundary-v1` wire syntax with external codebook.

### 3. Lossless Custody Invariant

Every packet modification requires minting a new envelope with a distinct Merkle digest (`sha256`). Original source bytes must remain 100% recoverable without loss.

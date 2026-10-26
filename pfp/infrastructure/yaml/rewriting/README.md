# Prompt Rewriting & Relational Boundaries

**AuthorityEffect:** `None`  
**Governing Standard:** Byte-Exact Role Spanning, Boundary Wire Encoding, Non-Authoritative Transformation  
**Master Specification:** [`rewriting_strategies_pfp_wire.md`](rewriting_strategies_pfp_wire.md)  
**Companion Specifications:** [`../../002_s_n/rewriting/rewriting_strategies_sn_wire.md`](../../002_s_n/rewriting/rewriting_strategies_sn_wire.md), [`../../003_minimal_symbol_system_n_mssn/rewriting/rewriting_strategies_mssn_wire.md`](../../003_minimal_symbol_system_n_mssn/rewriting/rewriting_strategies_mssn_wire.md)  

This directory defines the single canonical PFP prompt rewriting specification, AST diff models, relational normal form transformations, and byte-exact segment partition contracts for PFP.

---

## 1. Role in the Architecture

Prompt rewriting sits strictly between **Prompts** (`../prompts/`) and **Packetization** (`../packetization/`):
- Reads an incoming UTF-8 prompt byte-for-byte.
- Partitions the text into disjoint, contiguous byte spans with explicit semantic roles (`task`, `constraint`, `context`, `output`, `unresolved`).
- Compiles the structured prompt into an `mss-boundary-v1` wire term, isolating natural language inside an external source codebook.
- Produces an immutable compilation receipt verifying that no bytes were dropped, duplicated, or mutated without trace.

---

## 2. Directory Inventory

| Item | Type | Purpose & Scope |
|---|---|---|
| [`rewriting_strategies_pfp_wire.md`](rewriting_strategies_pfp_wire.md) | Master Specification | Master PFP rewriting specification consolidating prompt expansion $P \to P^\star \to \{P^\star_{\text{sub } ij}\}$, $\Gamma_{38}$ wire substrate, polygraph confluence, and Woland Retinue 13-gate verification matrix. |
| [`../pilots/pilot_output/`](../pilots/pilot_output/) | Pilot Test Data & Results | Execution outputs, [`results.md`](../pilots/pilot_output/results.md), and [`tests.md`](../pilots/pilot_output/tests.md) from prompt rewriting pilot runs. |

---

## 3. Boundary Wire Format (`mss-boundary-v1`)

For a declared task/constraint split such as:
```json
[
  {"start_byte": 0, "end_byte": 11, "role": "task"},
  {"start_byte": 11, "end_byte": 24, "role": "constraint"}
]
```

The resulting wire expression is:
```
<<p><v1><<q><s0>><<c><s1>>>
```
Where `s0` and `s1` resolve to the exact source substrings in the receipt. Natural language remains in the external codebook; only the structural topology is carried on the wire.


---

## Typed Contracts

- [`rewriting_types.py`](rewriting_types.py): Pydantic v2 models for byte spans, the contiguous partition rule, the `mss-boundary-v1` wire term, and the compilation receipt.
- [`rewriting_types.yaml`](rewriting_types.yaml): catalog of roles, partition rules, wire profile, and a validated example receipt.

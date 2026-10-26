---
documentation_contract: symbol-game-documentation/v1
title: MSS-N Wire Opcode and Constructor Registry
kind: reference
audience:
- engineers
- coding-agents
status: active
maturity: canonical
claim_status: partially-implemented
authority_effect: "None"
source_paths:
- omega_engine_pfp/domain/tower/parser.py
source_revision: c419cc6beb
prerequisites: []
verification: py -3.12 -m omega_engine_pfp.scripts.docs_integrity validate
aliases: []
related: []
last_verified: 2026-10-20
verification_scope: opcode dispatch read from omega_engine_pfp/domain/tower/parser.py; no test run
---


# 11. MSS-N Machine Wire Opcode and Constructor Registry

**Status:** Canonical Machine Wire Registry (Levels 0–21)  
**AuthorityEffect:** `None` (Defines wire syntax and parser admission table)  
**Alphabet:** $\Gamma_{38} = \mathtt{[a\text{-}z0\text{-}9<>]}$

> **Implementation status (2026-10-20, pin `c419cc6beb`).** The former source `the_symbol_game/reference/registry.md` is not present, and the earlier `claim_status: verified` had no cited check. The executable counterpart is `validate_packet_semantics` in [parser.py](../../../../omega_engine_pfp/domain/tower/parser.py) (line 650, docstring "Levels 0-8"). It dispatches semantic checks for 18 of the 42 constructors in section 2: `0`, `1`, `10`, `11`, `100`, `101`, `110`, `111`, `1010`, `1011` (arity only), `1100` (arity only), `1101`, `1110`, `1111`, `10000`, `10001`, `10010`, `11010`. Every other opcode, including `1001` `GluingRecord` and everything from `10011` upward except `11010`, parses syntactically and is not rejected; only its children are checked recursively. Read section 2 as a specification register, with the 18 listed opcodes implemented.

---

## 1. Global vs. Local Tag Architecture

To eliminate ambiguity across the 38-glyph wire format, the MSS-N specification strictly distinguishes two classes of bracketed tags:

1. **Global Packet Constructors (`op<<OPCODE>...>`):**
   - The primary identifier immediately following `op<<` is a **globally unique binary opcode** drawn from the table in §2.
   - No two global constructors may share the same opcode.
   - Global constructors determine the top-level AST node type and parser dispatch rule.

2. **Parent-Scoped Child Tags (`op<<LOCAL_TAG>...>` or `<TAG_VAL>`):**
   - When `op<<0>...>`, `op<<1>...>`, `op<<2>...>` appear nested inside an outer constructor, they are **parent-local field discriminators**, not global opcodes.
   - Their meaning is scoped entirely to the enclosing parent production rule.
   - Scalar status tokens (e.g., `<0>` for `Fail`, `<1>` for `Pass`, `<2>` for `Unknown` in Kleene logic) are field values, not opcodes.

3. **Numeric Encoding Standards:**
   - **Binary Integers:** Expressed as binary digit strings in atoms: e.g., `<0>` (0), `<1>` (1), `<10>` (2), `<11>` (3), `<100>` (4), `<101>` (5).
   - **Exact Signed Rationals ($\mathbb{Q}$):** Encoded via constructor `<10010>`:
     $$\mathtt{op<<10010><sign><num><den>>}$$
     where `sign` is `<0>` ($\ge 0$) or `<1>` ($< 0$), `num` is a binary integer, and `den` is a non-zero coprime binary integer ($\gcd(\mathrm{num}, \mathrm{den}) = 1$).
   - **Floating-point representations:** Strictly prohibited across all levels (Zero-Float Invariant).

   **Worked rational encodings** (laws from `validate_rational`, parser.py lines 524-568):

   | Value | Wire | Check |
   | --- | --- | --- |
   | $-3/4$ | `op<<10010><1><11><100>>` | sign `1`, num `11` = 3, den `100` = 4, gcd(3, 4) = 1: accepted |
   | $5/1$ | `op<<10010><0><101><1>>` | den `1`: accepted |
   | $0$ | `op<<10010><0><0><1>>` | the only accepted zero |
   | $-0$ | `op<<10010><1><0><1>>` | refused: canonical zero needs sign `0` |
   | $2/4$ | `op<<10010><0><10><100>>` | refused: gcd(2, 4) = 2 |

   Limit at the pin: `_parse_binary_int` (line 273) uses `int(word, 2)` and does not reject leading zeros, so `<011>` is read as 3. The same value therefore has more than one accepted spelling (`<11>` and `<011>`), and a byte digest of the wire is not unique per value unless a producer normalizes first.

---

## 2. Unified Global Opcode Registry (Levels 0–21)

| Binary Opcode | Dec | Level | Constructor Name | Semantic Role / Payload |
| :--- | :---: | :---: | :--- | :--- |
| `<>` | — | 0 | `Void` | Primitive difference / uncarved boundary seed |
| `<0>` | 0 | 1 | `UpLift` | Context lift admitting distinguished symbol pair |
| `<1>` | 1 | 2 | `Vertex` | 0-cell vertex identifier |
| `<10>` | 2 | 2 | `DirectedEdge` | 1-cell directed transition $(u \to v)$ |
| `<11>` | 3 | 2 | `GraphContainer` | Bounded collection of vertices and edges |
| `<100>` | 4 | 2 | `ObstructionWitness` | Binds uncertified obstruction `<>` to carrier |
| `<101>` | 5 | 3 | `AbstractSimplex` | Down-closed simplex with canonical vertex ordering |
| `<110>` | 6 | 5 | `EdgeLength` | Positive metric squared length record |
| `<111>` | 7 | 5 | `MetricSimplex` | Metric simplex with complete edge length records |
| `<1001>` | 9 | 5 | `GluingRecord` | Facet identification record between metric simplices |
| `<1010>` | 10 | 5 | `DeficitReceipt` | 2D Regge angular deficit receipt template |
| `<1011>` | 11 | 6 | `HigherCell` | 2-cell boundary relation between parallel paths |
| `<1100>` | 12 | 6 | `TypedRefusal` | Typed host error/refusal packet |
| `<1101>` | 13 | 7 | `PeriodicOrbitTable` | Outer container binding shift spec to orbits |
| `<1110>` | 14 | 7 | `OrbitRecord` | Orbit period, primitivity flag, and vertex sequence |
| `<1111>` | 15 | 8 | `AdjunctionPacket` | Adjoint functor pair $(F_n \dashv U_n)$ |
| `<10000>` | 16 | 8 | `HarmonicPacket` | Canonical $\ell^1$ cochain representative $\Pi_1([c])$ |
| `<10001>` | 17 | 8 | `DualCertReceipt` | Exact primal-dual zero-duality-gap receipt |
| `<10010>` | 18 | 8 | `RationalValue` | Exact signed rational number $\pm n / d$ |
| `<10011>` | 19 | 8 | `EdgeFlow` | Dual circulation edge flow assignment $y_e^*$ |
| `<10100>` | 20 | 9 | `DaggerPacket` | Dagger profunctor involution and reversal mapping |
| `<10101>` | 21 | 10 | `QuarantinePacket` | Quarantined spectral arithmetic shadow and boundary fences |
| `<10110>` | 22 | 11 | `PolygraphPacket` | Rewrite step sequence and divergent peak join verification |
| `<10111>` | 23 | 12 | `DDAEventPacket` | Proof-relevant 13-tuple DDA event record |
| `<11000>` | 24 | 12 | `KernelPacket` | Four-field irredundant runtime kernel $(B, C, x, \Omega)$ |
| `<11001>` | 25 | 13 | `AlternationPacket` | Bounded quantifier alternation and cycle detection |
| `<11010>` | 26 | 7 | `ShiftSpec` | De Bruijn shift parameters (alphabet size, block length) |
| `<11110>` | 30 | 8 | `UnitMap` | Adjunction unit natural transformation $\eta_n$ |
| `<11111>` | 31 | 8 | `CounitMap` | Adjunction counit natural transformation $\epsilon_n$ |
| `<100100>` | 36 | 13 | `ObserverEvalPacket` | $(C, p, \sim, W, \delta, \tau)$ observer evaluation packet |
| `<100101>` | 37 | 13 | `BQNFViewPacket` | BQNF incremental view maintenance and terminal route dispatch |
| `<100110>` | 38 | 14 | `BoundedAlternationPacket` | Bounded quantifier evaluation block and AST bound limits |
| `<100111>` | 39 | 15 | `MasterHorizonPacket` | R-B-G master horizon state and authority token |
| `<101000>` | 40 | 16 | `IndObjectPacket` | Filtered ind-object diagram stage and transition morphism |
| `<101001>` | 41 | 17 | `DialectContainer` | Dialect encapsulation container (`SymBin`, `SymLft`, etc.) |
| `<101010>` | 42 | 18 | `HodgePacket` | Discrete $\ell^2$ Hodge decomposition ($c = d_0 p + h + d_1^* q$) |
| `<101011>` | 43 | 19 | `ZetaShadowPacket` | Discrete transfer / Ihara spectral shadow and pole polynomial |
| `<101100>` | 44 | 20 | `ExpansionCyclePacket` | Replayable expansion cycle detection (`EXPANSION_CYCLE_DETECTED`) |
| `<101101>` | 45 | 21 | `Regge4DPacket` | Discrete 4D Regge simplicial metric and 2-face hinge curvature |
| `<101110>` | 46 | 5 | `AlgebraicScalar` | Minimal polynomial digest, isolating interval, and coordinate components |
| `<101111>` | 47 | 5 | `IntervalScalar` | Certified isolating interval enclosure bounds and verifier digest |
| `<110000>` | 48 | 2 | `DigestRef` | Content-addressed algorithm atom and hex digest atom |

---

## 3. Disambiguation Rules

1. **Collision Avoidance:**
   - Previous drafts assigned `<10001>` to both `DualCertReceipt` (Level 8) and `dagger_packet` (Level 9). Level 9 is now globally fixed to `<10100>`.
   - Previous drafts assigned `<10011>` to both `EdgeFlow` (Level 8) and `quarantine_packet` (Level 10). Level 10 is now globally fixed to `<10101>`.
   - Previous drafts assigned `<11010>` to both `ShiftSpec` (Level 7) and `bqnf_packet` (Level 13). `BQNFViewPacket` is globally fixed to `<100101>`.
   - Draft PKT-10 reused `<1100>` for `DigestRef`. Opcode `<1100>` is reserved exclusively for `TypedRefusal` (Level 6); structured `DigestRef` is globally assigned to `<110000>`.
   - Draft PKT-20 reused `<1001>` (Level 5 `GluingRecord`) for `AlgebraicScalar` and `<1011>` (Level 6 `HigherCell`) for `IntervalScalar`. `AlgebraicScalar` is globally assigned to `<101110>` and `IntervalScalar` to `<101111>`. Exact rational numbers on the wire use `<10010>` (`RationalValue`, Level 8).
   - Draft supplement collisions between `ObserverEvalPacket` and `BQNFViewPacket` at `<100101>` are resolved by assigning `ObserverEvalPacket` to `<100100>` and preserving `BQNFViewPacket` at `<100101>`.
2. **Version Pinning:**
   - Packets omitting an explicit version token are parsed under wire protocol specification `v1.0`.
   - Structural modifications to packet layouts require incrementing the version prefix and obtaining host compiler certification.

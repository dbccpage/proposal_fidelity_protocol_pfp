---
name: techne-code-lossless-parser
description: "Build byte-exact roundtrip parsers for Markdown, YAML and RFC 8785 canonical JSON."
operad_source_colours: ["Code", "Audit"]
operad_target_colour: "Code"
operad_arity: 2
operad_residual: "unknown"
operad_equivariant: false
agent_scope: ["all", "techne-code-soviet-builder", "techne-dev"]
families: [techne-code, parser, ast]
---

# Techne Code Lossless Parser

**Status:** `ADMITTED`
**AuthorityEffect:** `None` (Zero-authority invariant; document transformations and lossless serialization only)
**Governance Council:** `L3_logos_techne`

---

## 1. Prime Directive & Operational Mandate

The **Techne Code Lossless Parser** builds high-precision, roundtrippable parsers and serializers for Markdown, YAML, and JSON. Ensures that document modifications preserve untouched byte spans, comments, frontmatter, and code fences.

---

## 2. Core Parser & Serialization Invariants

### 1. Byte-Exact Roundtrip Invariant (`RULE_LOSSLESS_ROUNDTRIP_001`)

- Unmodified documents parsed and re-rendered by the parser must satisfy:
  $$\text{render}(\text{parse}(\text{raw\_bytes})) \equiv \text{raw\_bytes}$$
- Parsers must record `SourceByteSpan` slices for each document section to prevent formatting mangling.

### 2. RFC 8785 Canonical JSON Serialization (`RULE_RFC8785_CANONICAL_JSON_001`)

- All JSON manifests, activation profiles, and evaluation receipts must serialize according to RFC 8785:
  - UTF-8 encoding without BOM.
  - Strict ordinal byte ordering of object keys (`key=lambda s: s.encode('utf-8')`).
  - No whitespace between tokens (`separators=(',', ':')`).
  - Exact float representations without exponential formatting ambiguity.

### 3. Pure UTF-8 & Mojibake Elimination (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`)

- Parsers and serializers must reject Windows-1252 / CP437 character replacements (such as `â€™` or `â€"`).
- All inputs and outputs must be validated with strict UTF-8 decoding.

---

## 3. Mandatory De-Linting & Encoding Cleanliness

Every file created or modified during the execution of this skill MUST be pure UTF-8 without BOM and pass markdown/code linters with **0 errors and 0 warnings**.

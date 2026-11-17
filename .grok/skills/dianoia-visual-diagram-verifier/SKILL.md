---
name: dianoia-visual-diagram-verifier
description: "Check Mermaid diagrams, SVGs and visual artifacts for syntax, KaTeX formatting and readability before emitting."
families: [oecog, visual_verification]
operad_source_colours: ["Diagram", "State"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
---

# dianoia-visual-diagram-verifier

**Status:** `CANDIDATE`
**AuthorityEffect:** `None`
**Council:** `L2_dianoia`

## When to use

Use whenever authoring, updating, or reviewing visual diagrams (Mermaid, SVG, HTML cards)
before embedding them in artifacts, documentation, or user-facing messages.

## Inputs

- Markdown documents containing Mermaid diagram blocks (` ```mermaid ... ``` `).
- SVG or HTML visual layout artifacts.
- Target rendering constraints (KaTeX escaping, container boundaries).

## Protocol

1. Extract diagram code blocks and visual markup structures.
2. Validate diagram syntax:
   - Check Mermaid node definitions and connector arrow operators.
   - Verify label quoting rules when labels contain parentheses, braces, or special punctuation.
   - Check literal dollar signs ($) vs KaTeX math delimiters to prevent unexpected formatting breaks.
3. Validate layout sanity:
   - Verify node count and link density remain within legible visual budgets.
   - Detect orphaned nodes or broken reference labels.
4. Emit an evaluation receipt with corrected diagram syntax or confirmation of structural validity.

## Terminals

`SYNTAX_VALID`, `GRAMMAR_ERROR_DETECTED`, `LABEL_ESCAPE_FIXED`.

## Nonclaims

Visual verification checks syntax renderability, escaping rules, and structural layout compliance;
it does not evaluate whether the diagram's conceptual semantics faithfully model empirical reality.

## Metatheoretic & Educational SVG Standard (940×580 Canvas)

When authoring or verifying educational schematics (such as `_images/genesis_*.svg`, `_images/genesis_ongoing_*.svg`, `_images/wdp_*.svg`):

1. **Canvas & Viewport:** Must strictly declare `viewBox="0 0 940 580" width="100%" height="100%"`.
2. **Palette & Theme:**
   - Base canvas: `#0b0f19` with dark radial glow `#1e1b4b` (`cx="50%" cy="40%" r="60%"`).
   - Subtle coordinate grid: `#1e293b` with 30×30 unit spacing.
   - Text hierarchy: `#f8fafc` (primary titles), `#cbd5e1` / `#e2e8f0` (body), `#94a3b8` / `#64748b` (labels/subtitles).
3. **Dual-Column Structural Layout:**
   - **Header (`y=30`, height 60):** Level/Step badge, Title, Subtitle, and invariant pill.
   - **Left Column (`x=40, y=105`, width 370, height 400):** Formal specification box, syntax-colored Lean 4 / formal code block, bulleted axiomatic invariants.
   - **Right Column (`x=430, y=105`, width 470, height 400):** Operational state diagram, graph rewrite, quotient space, or reaction chamber.
   - **Footer (`x=40, y=520`, width 860, height 35):** System Invariant, Parity Anchor ($MSS\text{-}N$ / $S(n)$), and Status badge.
4. **Encoding & Integrity:** Pure UTF-8 without BOM, valid XML entity escapes (`&amp;`, `&lt;`, `&gt;`).

## 5. XML Entity & Tag Sanitization Protocol for Programmatic SVG Generation

When generating SVGs programmatically via scripts (e.g. Python string interpolation or template rendering):

1. **Standalone XML Predefined Entities Only:**  
   Standard XML recognizes ONLY 5 entities: `&amp;`, `&lt;`, `&gt;`, `&quot;`, `&apos;`.  
   Named HTML entities (such as `&tau;`, `&ne;`, `&times;`, `&Delta;`, `&delta;`, `&le;`, `&ge;`) trigger fatal `undefined entity` XML parse errors unless converted to raw UTF-8 or numeric entities.
2. **Angle Bracket Escaping in Text Nodes:**  
   Mathematical expressions containing inequalities or token glyphs (e.g. `<arb>`, `|M| < |S|`, `<= 2`) MUST be escaped as `&lt;` and `&gt;` in all text labels, or they will be parsed as malformed XML tags (`mismatched tag`).
3. **The Two-Stage XML Sanitizer Pattern:**
   ```python
   import html
   def unescape_xml_safe(s: str) -> str:
       # Step 1: Mask the 5 standard XML entities
       tokens = {
           '&amp;': '___AMP___', '&lt;': '___LT___', '&gt;': '___GT___',
           '&quot;': '___QUOT___', '&apos;': '___APOS___'
       }
       for k, v in tokens.items():
           s = s.replace(k, v)
       # Step 2: Unescape named HTML entities to native UTF-8 characters
       s = html.unescape(s)
       # Step 3: Restore the 5 standard XML entities
       for k, v in tokens.items():
           s = s.replace(v, k)
       return s
   ```
4. **Mandatory In-Memory Parse Verification:**  
   Never persist generated SVG markup to disk without verifying it with an in-memory XML parser:
   ```python
   import xml.etree.ElementTree as ET
   ET.fromstring(svg_content)  # Raises ParseError if invalid
   ```

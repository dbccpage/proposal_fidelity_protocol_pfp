# Video Storyboard: Lab 000.A: Build Grammar 000 from Bare Boundaries to Atoms

AuthorityEffect: None.

**Target Duration:** `120s`  
**Format:** 1080p 60fps / 940x580 Dark-Mode Canvas  
**Voiceover Style:** Concise, mathematically precise, zero hype. Ready for spoken voiceover recording.

---

## Scene Breakdown

| Scene | Timestamp | Visual Cue / On-Screen Action | Voiceover Script | Epistemic Target |
| :--- | :--- | :--- | :--- | :--- |
| **01** | `0:00 - 0:25` | Show diagram zooming into <> node. Text: Unmarked Medium != <> | "Welcome to Grammar 000. We begin not with an empty set, but with the creation of a boundary. The token bracket-bracket is our ground object." | `[Declared]` |
| **02** | `0:25 - 0:55` | Terminal execution of parse_simple('<>') returning Diff(). Prediction Gate 1 check. | "Before running the parser, predict what AST class represents an empty boundary. It is Diff. Notice how it carries no payload, yet partitions space." | `[Executed]` |
| **03** | `0:55 - 1:15` | Live test showing Atom('') raising ValueError, contrasted with Atom('0'). | "Atoms require non-empty words over Sigma-plus. The empty word is strictly excluded, ensuring structure and payload never blur." | `[Tested]` |
| **04** | `1:15 - 2:00` | Concatenation of <0><1> without commas, followed by adversarial rejection of malformed commas. | "Self-closing delimiters eliminate commas entirely. The parser resolves tokens with one-glyph lookahead in linear time." | `[Tested]` |

---

## Technical Recording Notes
1. Render accompanying diagram SVG in dark-mode (940x580) before live capture.
2. Execute notebook code cells live in terminal or headless environment to capture exact stdout.
3. Adhere strictly to the voiceover script pacing (120s target).

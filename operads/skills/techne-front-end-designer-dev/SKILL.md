---
name: techne-front-end-designer-dev
description: "Use for front-end UI design and web development. React, Tailwind, shadcn/ui, D3 charts, slides, accessibility."
operad_source_colours: ["State", "Code", "Paper", "Proof"]
operad_target_colour: "State"
operad_arity: 4
operad_residual: "unknown"
---

# Deprecated skills (consolidated)

- `goo-layer-presentation-remediation`
- `ext_awesome_claude_shadcn_ui_skills`
- `ext_awesome_claude_web_asset_generator`
- `ext_anthropics_frontend_design`
- `ext_anthropics_web_artifacts_builder`
- `ext_awesome_claude_claude_d3js_skill`
- `ext_awesome_claude_frontend_slides`
- `ext_anthropics_canvas_design`

## admission: admitted

---

## 1. Core Front-End Stack & Principles

1. **Modern Frameworks & Bundlers:** React 18/19, Next.js App Router, Vite, HTML5 semantic layout, ES2024 TypeScript/JavaScript.
2. **Styling & Design Tokens:** Vanilla CSS custom properties, Tailwind CSS (v3/v4), CSS Modules, CSS Grid/Flexbox, HSL color spaces.
3. **Visual Excellence (WOW Factor):** Dark mode default, vibrant gradients, glassmorphism (`backdrop-filter: blur(12px)`), subtle glowing borders, and sleek Google Fonts typography (Inter, Outfit, JetBrains Mono).
4. **Interactive Micro-Animations:** Smooth state transitions (`transition: all 0.2s ease`), keyframe animations (`@keyframes pulse-glow`), interactive hover states, micro-feedback on buttons, inputs, and cards.
5. **Responsive & Mobile-First:** Fluid layouts (`clamp()`), mobile drawer navigation, responsive breakpoints (`sm`, `md`, `lg`, `xl`), zero horizontal overflow.
6. **Web Accessibility (a11y) & SEO:** WAI-ARIA roles, keyboard navigation focus rings, contrast ratio compliance (WCAG 2.1 AA), single `<h1>` tag per page, unique element IDs.

---

## 2. Standard Design System Tokens

```css
:root {
  /* HSL Color Palette */
  --bg-dark-primary: hsl(222, 47%, 7%);
  --bg-dark-secondary: hsl(217, 33%, 12%);
  --bg-glass-card: rgba(22, 30, 46, 0.75);

  --accent-cyan: hsl(186, 100%, 50%);
  --accent-purple: hsl(265, 89%, 66%);
  --accent-emerald: hsl(158, 64%, 52%);

  --text-bright: hsl(210, 40%, 98%);
  --text-muted: hsl(215, 20%, 65%);

  /* Glassmorphism & Borders */
  --border-glass: rgba(255, 255, 255, 0.12);
  --border-glow: rgba(0, 242, 254, 0.3);
  --shadow-card: 0 12px 40px 0 rgba(0, 0, 0, 0.37);
  --shadow-glow: 0 8px 32px 0 rgba(0, 242, 254, 0.2);

  /* Typography */
  --font-heading: 'Outfit', 'Inter', system-ui, sans-serif;
  --font-body: 'Inter', system-ui, sans-serif;
  --font-code: 'JetBrains Mono', monospace;
}
```

---

## 3. Data Visualization, D3.js & Canvas Design

When building interactive data graphics or visual canvas interfaces:

1. **D3.js Data Driven Documents:** Dynamic SVG scales, force-directed network graphs, hierarchical tree maps, reactive time-series charts.
2. **HTML5 Canvas & WebGL:** High-performance pixel manipulation, particle systems, interactive control sliders, real-time animation loops (`requestAnimationFrame`).
3. **No Placeholders:** Generate real WebP/SVG visual assets using `generate_image` or inline vector graphics.

---

## 4. Web Artifacts & Frontend Presentation Slides

1. **Standalone Web Artifacts:**
   - Single-file HTML/CSS/JS applications with self-contained styling, dependencies, and state management.
2. **Frontend Slide Decks:**
   - Keyboard-navigable HTML presentation slides (`ArrowLeft`/`ArrowRight`, `Space`), smooth transition animations, progress indicators, dark mode typography.

---

## 5. Shadcn UI Component & Web Asset Generation

1. **Shadcn/UI & Radix Primitives:**
   - Standardize accessible, unstyled Radix UI primitives styled with Tailwind CSS (`@radix-ui/react-dialog`, `@radix-ui/react-dropdown-menu`, `@radix-ui/react-tabs`).
   - Use `cn()` utility (`clsx` + `tailwind-merge`) for conditional class merging.
   - Use Lucide Icons (`lucide-react`) for consistent UI iconography.
2. **Web Asset Pipeline (`Code -> Diagram / Image`):**
   - Translate code structures and design tokens into visual SVG diagrams or high-resolution WebP images.

---

## 6. Presentation Layer & Web API Remediation

When repairing or standardizing presentation services and Web API endpoints:

1. **Rust Presentation Crate Compatibility (`compat.rs`):**
   - Maintain zero-dependency internal submodules (`compat::self_review`, `compat::sweep_kernel`, `compat::proofer`) inside `omega_api/src/compat.rs`.
   - Re-export `SurfaceRecorder`, `SurfaceManifest`, `Decision`, `TerminalRecord`, and `terminalize_row`.
   - Ensure `omega_layer_presentation/omega_api` is registered in `omega_engine/Cargo.toml`.
2. **Python FastAPI Path & Defect Sanitization (`app.py`):**
   - Ensure `sys.path` dynamically resolves `repo_root`, `omega_engine_dir`, `omega_engine_py_dir`, and `presentation_root`.
   - Replace synthetic magic numbers in defect simulation endpoints (`/api/epk/simulate`) with explicit linear composition laws.

---

## 7. Implementation & Quality Checklist

- [ ] **CSS Foundation (`index.css`):** Reset, CSS variables, glassmorphism utilities, dark mode background defaults.
- [ ] **Semantic Structure:** Proper `<header>`, `<main>`, `<nav>`, `<section>`, `<footer>` tags.
- [ ] **Data Visualization & D3.js:** Interactive charts, SVG scales, canvas animation performance.
- [ ] **Standalone Web Artifacts:** Self-contained single-file HTML apps & interactive slide decks.
- [ ] **Shadcn/UI & Accessibility:** WAI-ARIA compliance, Radix primitives, keyboard navigation focus states.
- [ ] **Presentation Hygiene:** Clean FastAPI `sys.path` resolution and Rust `compat.rs` re-exports.

AuthorityEffect: None.

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).

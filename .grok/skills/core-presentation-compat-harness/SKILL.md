---
name: core-presentation-compat-harness
description: "Standardize compat modules and HTTP endpoint stubs for the presentation API, detached from archived crates."

operad_source_colours: ["State"]
operad_target_colour: "State"
operad_arity: 1
operad_residual: "unknown"
---

# core-presentation-compat-harness

## Authority & Compliance

- **AuthorityEffect**: `None`
- **Governance**: Techne / Nomos
- **Scope**: Presentation Layer Embedded Compatibility & Decoupled Router Harness (Axum, PyO3, Rust Presentation API).

---

## 🏛️ Architecture & Compatibility Layer

```text
[HTTP API Requests] ──► [core_api Router (Axum)]
                                │
                                ▼
                   ┌──────────────────────────┐
                   │  compat::self_review     │
                   │  compat::sweep_kernel    │ (Embedded stubs & decoupled models)
                   │  compat::proofer         │
                   └──────────────────────────┘
```

---

## Monograph header

A rendered research monograph opens with the four centered lines in `coda_atlas/_kits/paper_frontmatter_specification.md`: Title, Author, Date, Version. A subtitle, when the manuscript has one, is the single extra centered line between Title and Author. The next section is Abstract.

## 📋 Protocol & Engineering Laws

1. **Legacy Crate Detachment**: `core_api/Cargo.toml` MUST NOT depend on archived legacy crates (`core_sweep_kernel`, `core_proofer`). All required data types and response schemas MUST be embedded cleanly within `core_api/src/compat/`.
2. **Backward-Compatible Wire Schemas**: Public JSON response types (`SurfaceManifest`, `ValidationReport`, `ProofReceipt`) MUST preserve exact field names and serializations for existing clients.
3. **Activation & Corrigibility Isolation**: `core_corrigibility::gated_activate` MUST guard all boot and request pathways, guaranteeing `Shutdown` state compliance (`503 Service Unavailable` on active halt).

---

## 🛠️ Verification Commands

```powershell
# Verify core_api presentation layer builds and passes tests cleanly
cargo test -p core_api
```

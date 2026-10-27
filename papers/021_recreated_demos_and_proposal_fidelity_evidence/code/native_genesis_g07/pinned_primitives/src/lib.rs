//! # ooutwire_primitives
//!
//! `AuthorityEffect: None.`
//!
//! One file per primitive of the 19L57G1 estate, in dependency order, and
//! the smallest Core engine that can be assembled from them.  Nothing here
//! is the sealed derivation; everything here is a *reading* of it, written
//! so that the reading can be run and checked instead of remembered.
//!
//! ## The index
//!
//! The crate boundaries are the seven of Part IV §13.9 of the crosstab.  They
//! are modules here, not crates, so the whole thing builds and tests with one
//! command.  Splitting them later is mechanical.
//!
//! | crate boundary | primitive | file |
//! |---|---|---|
//! | coda-carrier | token — presentation identity, forgotten by the key | `token.rs` |
//! | coda-carrier | mark — internal identity, the admission index | `mark.rs` |
//! | coda-carrier | regime — admitted state and nothing else | `regime.rs` |
//! | coda-carrier | event — a presentation or an admission | `event.rs` |
//! | coda-carrier | supply — external presentation, provably inert (L1) | `supply.rs` |
//! | coda-carrier | admission — the only thing that changes state (L2, L6) | `admission.rs` |
//! | coda-carrier | imposition — an externally imposed requirement | `imposition.rs` |
//! | coda-carrier | retention — the history | `retention.rs` |
//! | coda-carrier | replay — rebuild from genesis (L4) | `replay.rs` |
//! | coda-carrier | certification — a claimed regime against its history (L5) | `certification.rs` |
//! | coda-carrier | fingerprint — the replay hash | `hash.rs` |
//! | coda-carrier | the L3 lexical signature census | `census.rs` |
//! | coda-observe | context — a form plus a slot tuple with holes | `context.rs` |
//! | coda-observe | judgment — the positive grammar (L7) | `judgment.rs` |
//! | coda-observe | profile — and the two bits inside `derivable` | `profile.rs` |
//! | coda-observe | separability — profiles differ; witness; collapsed pairs | `separability.rs` |
//! | coda-observe | observer — bits extractor plus reader; the four readers | `observer.rs` |
//! | coda-iso | renaming — a bijection pair; tokens travel and are forgotten | `renaming.rs` |
//! | coda-iso | canonical — the key; `≅` is *defined* as equal keys | `canonical.rs` |
//! | coda-iso | automorphism — the state's own symmetry; pair orbits | `automorphism.rs` |
//! | coda-price | candidate — a one-step augmentation | `candidate.rs` |
//! | coda-price | bounds — the declared finite candidate space (L10) | `bounds.rs` |
//! | coda-price | measure — `mu1`, `mu2`, declared never inferred (L12) | `measure.rs` |
//! | coda-price | response — validity, fast and naive, cross-checked (L11) | `response.rs` |
//! | coda-price | enumeration — pruned by four lemmas, cross-checked unpruned | `enumeration.rs` |
//! | coda-price | minima — CLASSES, never a choice (L8, L9) | `minima.rs` |
//! | coda-price | role — transition roles derived from accepted responses | `role.rs` |
//! | engine | reading — the two admission readings L and F | `reading.rs` |
//! | engine | closure — the declared pair-separation closure policy | `closure.rs` |
//! | engine | tree — the branch tree and its frontier | `tree.rs` |
//! | represented | menu — the declared finite proposal set | `menu.rs` |
//! | represented | repair — the repair family, sound and complete | `repair.rs` |
//! | represented | obstruction — requirement plus EXHAUSTIVE failure | `obstruction.rs` |
//! | represented | budget — fuel; gates rule 1 | `budget.rs` |
//! | represented | license — authorization; gates rule 2 | `license.rs` |
//! | represented | refusal — a non-absorbing record needing a certificate | `refusal.rs` |
//! | represented | support — what a transition can read; `notes_inert` | `support.rs` |
//! | represented | panel — certification up to the panel, never correspondence | `panel.rs` |
//! | represented | world — the represented state and its total step | `world.rs` |
//! | represented | hidden — the seven hidden-input countermodels | `hidden.rs` |
//! | coda-cert | certificate — exhaustion, witness, obstruction | `certificate.rs` |
//! | coda-terminal | scope — a result carries the scope it was certified under | `scope.rs` |
//! | coda-terminal | terminal — the five declared final statuses | `terminal.rs` |
//! | coda-audit | export — deterministic serialisation and full replay | `export.rs` |
//! | twelfth sort | boundary — one two-sided boundary, readings U and O | `boundary.rs` |
//! | outside | the push from outside: supply, demand, choice, licence, fuel | `outside.rs` |
//! | engine | omega — the fold with four holes | `core.rs` |
//! | study | PO-000 replicated — the projection-obstruction paper, exact and numerical rails, read through the primitives above | `alpha_projection_obstruction/` |
//!
//! ## What a green test suite certifies
//!
//! That the arithmetic in this crate agrees with the pinned values it names.
//! Not that the sealed derivation is right, not that this reading of it is
//! the only one, and not that any analogy anyone has drawn from it holds.
//! A receipt is never evidence of its payload (`FW-RECEIPT`).

#![forbid(unsafe_code)]
#![deny(missing_docs)]

// coda-carrier
pub mod token;
pub mod mark;
pub mod regime;
pub mod event;
pub mod supply;
pub mod admission;
pub mod imposition;
pub mod retention;
pub mod replay;
pub mod certification;
pub mod hash;
pub mod census;

// coda-observe
pub mod context;
pub mod judgment;
pub mod profile;
pub mod separability;
pub mod observer;

// coda-iso
pub mod renaming;
pub mod canonical;
pub mod automorphism;

// coda-price
pub mod candidate;
pub mod bounds;
pub mod measure;
pub mod response;
pub mod enumeration;
pub mod minima;
pub mod role;

// the sealed engine's structure
pub mod reading;
pub mod closure;
pub mod tree;

// the represented process
pub mod menu;
pub mod repair;
pub mod obstruction;
pub mod budget;
pub mod license;
pub mod refusal;
pub mod support;
pub mod panel;
pub mod world;
pub mod hidden;

// coda-cert, coda-terminal, coda-audit
pub mod certificate;
pub mod scope;
pub mod terminal;
pub mod export;

// the twelfth sort
pub mod boundary;

// the outside, and the engine
pub mod outside;
pub mod omega;

// a study: PO-000 (projection obstruction) replicated from the primitives.
// A directory module; the L3 census recurses into it.
pub mod alpha_projection_obstruction;

// test-only helpers; excluded from the L3 census by name
#[cfg(test)]
pub mod testkit;

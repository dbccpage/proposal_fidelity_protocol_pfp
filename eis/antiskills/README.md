# OE Anti-Skill Estate v0

This estate separates candidate learning from human-reviewed declarations.
Everything here has `AuthorityEffect: None`.

- `ooutwire/` contains mined proposals. A proposal is inert data and cannot be
  loaded by the prompt reviewer.
- `admitted/registry.json` remains the legacy v0 registry read by the
  deterministic prompt reviewer and remains empty. The separately verified
  truth-boundary V2 registry and its Adversary-only activation profile live under
  `admitted/truth_boundary_v2/`; they are not converted into v0 repair specs.
- `fixtures/` contains named evaluation cases and computed receipts. A passing
  fixture receipt is evidence about those exact cases only; it does not admit a
  candidate or prove future generalization.
- `schema.json` declares the strict public wire grammar. Python constructors
  also reject unknown fields and recompute content IDs.

V2 admission requires distinct contexts, a clean negative control, no
protected-field loss, a replayed `COMPUTED_PASS` receipt, and an explicit human
decision bound by the external governance verifier. The first admitted V2
registry is scoped only to `adversary-engineering-v1`; it neither activates the
legacy reviewer nor grants global activation. Frequency and syntactic validity
never grant admission.

The executable implementation lives in
`engine/crates/prompt_civilization/`. The source archive described in
[PROVENANCE.md](PROVENANCE.md) is never imported by the runtime.

Historical PR and conversation-DAG mining follows the shared
[Historical PR Immunity Campaign Contract](../../operads/skills/_shared/historical_pr_immunity_campaign.md).
Raw observations remain in the content-addressed campaign store and are never
runtime-loaded. Any anti-skill candidate bundles exported from the campaign
enter `ooutwire/` only. A merged PR, legacy antibody score, repeated trace, or
model consensus is never an admission label; a proposed anti-morphism requires
a later bound correction, repair, refusal, revert, or supersession. Unresolved
obstructions remain open local findings until a typed bridge is implemented.

## Claim ceiling

This is a prompt-structure and evidence-discipline system. It is not a truth,
hallucination, authorship, consciousness, or intent detector. An anti-skill is
not a word blacklist. It is a declared structural detector plus a separate
repair proposal and deterministic evaluation boundary.


## Rust audit overclaim: forbidden procedure and falsifier

**Status:** procedural candidate guidance, not an admitted wire spec or runtime
detector. Reuses the existing bounded-evidence discipline rather than creating
another registry entry or fabricating conversation episodes.

Forbidden procedure: treat regex audit matches as compiler-proven defects or a
mandate to bulk-derive `Ord` on every enum. In particular, a substring check that
accepts `PartialOrd` as `Ord`, reads a block comment as active `unsafe`, or treats
all source after the first `#[cfg(test)]` as test code cannot certify the estate.

Falsifier: run the actual auditor against a `PartialOrd`-only ordered-key fixture;
it must flag the missing total order. A fully ordered key, a commented-out
unsafe block, production code after a closed test module and a legitimate
unordered payload carrier are deciding controls for their respective claims.
Do not treat map values or `Result` errors as ordered keys, or promote
`PartialEq` to `Eq`. Check manual trait laws before structural derives.
Default JSON map behavior is not a canonicalization guarantee across Cargo
feature unification: compare actual nested-map hashes/IDs with `preserve_order`,
retain array-order controls, and preserve deliberate source-order display.
A name-bearing tape must survive reversed interning history, not merely sorted
allocation IDs. Retained loose-source harness results are not package tests.
The bounded allocation test certifies only its measured allocator/input/carrier.

Apply [the Rust anti-pattern skill](../skills/techne-code-rust-anti-patterns/SKILL.md)
and [ordered-key pattern](../patterns/anti/rust/AP_RS_002_domain_enum_missing_ord.md)
before promoting a match. Record file coverage separately from semantic review,
retain raw reports as historical evidence, and bind fresh repair results to the
current candidate. Creating prose guidance does not admit or activate a typed
anti-skill; strict schema, replayed evaluation and human admission remain required.

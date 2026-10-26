<!-- markdownlint-disable MD013 -->

# Symbol Game terminalizer — draft host-enforced prompt contract

**Status:** DRAFT DESIGN NOTE; not doctrine and not an implementation
**AuthorityEffect:** None
**Date:** 2026-09-01

## 1. Scope and nonclaims

This note proposes a prompt-and-host contract for making a model expose its
declared carrier, rules, evidence classes, refusals, and terminal output. The
contract can make malformed output machine-refusable when an independent host
parses and replays it. It does **not** make a language model deterministic, alter
its attention mechanism, or turn tokens into a spin network, Fourier basis,
quantum state, or Hadamard transform.

The useful design rule is narrower:

> An unpriced rewrite is a smuggled axiom.

Accordingly, notation must carry semantics, a soundness basis, an application
scope, and replay data. Producer prose is testimony. A positive terminal is
licensed only by host-side validation and replay of the declared operations.

## 2. Division of labor

An outside party may supply:

- `[SUPPLY]`: the challenge in its own vocabulary;
- `[ADVERSARIAL]`: attacks and counterexamples; and
- `[OUTSIDE BET]`: an optional commitment hash whose plaintext remains outside
  the prompt until the run ends.

The run must not silently import an outside vocabulary, carrier, translation,
or calculus. Those items are admitted only through explicit declarations and
independent checks. A grid of unexplained names is an architecture wearing
letters.

The outside-bet mechanism is incomplete until a host contract fixes the hash
algorithm, canonical byte encoding, salt policy, reveal procedure, and mismatch
terminal.

## 3. Required prompt surfaces

| Surface | Required content |
| --- | --- |
| `[SYSTEM]` | Output and interaction constraints; no claim about model internals |
| `[K: CARRIER]` | Exact members or a bounded generator, plus codepoint/byte pins |
| `[VOCABULARY]` | Meanings grounded in cited or supplied definitions |
| `[GLYPH CALCULUS]` | Required whenever a cycle or rewrite is used |
| `[LAWS / AXIOMS]` | Declared assumptions, each with scope |
| `[REFUSALS]` | Typed refusal conditions, including `FW-MOVE` |
| `[D: ACTIVE DEMAND]` | The requested decision or construction |
| `[TAU]` | Strict output schema and terminal statuses |

Textual compliance is not enforcement. The host must parse these surfaces,
reject duplicate keys and unknown fields, and replay each positive claim it is
equipped to check.

## 4. Glyph-calculus contract

```yaml
[GLYPH CALCULUS]
schema: omega.glyph_calculus.draft.v1

carrier:
  members:
    - symbol: "alpha"
      codepoint: "U+03B1"
    - symbol: "beta"
      codepoint: "U+03B2"
    - symbol: "gamma"
      codepoint: "U+03B3"
    - symbol: "delta"
      codepoint: "U+03B4"
    - symbol: "epsilon"
      codepoint: "U+03B5"

cycles:
  - cycle_id: c5
    ordered_members: [alpha, beta, gamma, delta, epsilon]
    period: 5
    semantics: "successor follows the listed cyclic order"
    soundness:
      class: declared_instance
      evidence: "the ordered cycle supplied in this packet"
    application_scope: "successor powers on c5 only"

moves: []

ops:
  - PROVE
  - SHOW
  - DECIDE
  - EXHAUST
  - REDUCE
  - LAND
  - PIN
  - REFUSE
  - OPEN

rules:
  - "Every ledger row begins with exactly one declared op."
  - "A declared instance does not license a general rewrite theorem."
  - "A move may be applied only inside its application_scope."
  - "FW-MOVE refuses an unlisted move or an application outside scope."
  - "A proved period permits modular reduction only for the declared cycle."
```

`soundness.class: declared_instance` records supplied structure; it does not
prove that an arbitrary rewrite is valid in arbitrary contexts. A reusable
rewrite needs a cited theorem or a proof whose hypotheses and application scope
the host can check.

## 5. Receipt contract

The producer must report what it attempted. The host must separately report
what it re-derived. A single producer-authored `verified: true` field is not a
certificate.

```yaml
calculus_receipt:
  schema: omega.glyph_receipt.draft.v1
  carrier_digest: "<sha256 of canonical carrier bytes>"
  operations:
    - index: 0
      op: PROVE
      statement: "period(c5) = 5"
      evidence_ref: "cycle:c5"
      producer_claimed_valid: true
      host_rederived: true
    - index: 1
      op: REDUCE
      statement: "17 mod 5 = 2"
      evidence_ref: "integer-mod-replay"
      producer_claimed_valid: true
      host_rederived: true
    - index: 2
      op: LAND
      statement: "successor^2(alpha) = gamma"
      evidence_ref: "cycle:c5"
      producer_claimed_valid: true
      host_rederived: true
  terminal_status: evidence_only
  authority_effect: None
```

Required host checks include:

1. carrier codepoints and canonical digest match;
2. every op belongs to the closed op set;
3. every referenced cycle or move exists;
4. each application lies within its declared scope;
5. the host recomputes the reduction and landing value; and
6. a row that cannot be replayed says `host_rederived: false` and cannot license
   a stronger terminal.

## 6. Worked bounded example

```yaml
[SYSTEM]
mode: strict_structured_output

[K: CARRIER]
members: [alpha, beta, gamma, delta, epsilon]

[GLYPH CALCULUS]
use: c5

[D: ACTIVE DEMAND]
query: "successor^17(alpha)"

[TAU]
allowed_ops: [PROVE, REDUCE, LAND]
terminal_statuses: [evidence_only, refused, unresolved]
require_calculus_receipt: true
```

The expected arithmetic is `17 mod 5 = 2`, followed by two applications of the
declared successor, yielding `gamma`. The example is finite and replayable. It
does not establish any claim about how the model represented the problem
internally.

## 7. Refusals

- `FW-MOVE`: unlisted rewrite, missing soundness basis, or out-of-scope use.
- `FW-CARRIER`: undeclared member, codepoint mismatch, or carrier digest mismatch.
- `FW-OP`: undeclared operation verb.
- `FW-REPLAY`: positive terminal depends on a row the host did not re-derive.
- `FW-SCOPE`: a bounded result is promoted beyond its declared carrier or bound.
- `FW-LEAD`: a supposed pre-registration leaks the expected result into the run.
- `FW-CHAIN`: a prior receipt is treated as stronger evidence than its own scope.

## 8. Implementation boundary and next tests

This document does not implement a parser, linter, rule applicator, replay host,
or experiment. Before promotion from `_ooutwire`, the implementation must add:

1. duplicate-key and unknown-field rejection;
2. exact carrier codepoint pinning;
3. a first-token op linter;
4. a rule applicator keyed by rule and redex position, not rule name alone;
5. per-row host replay with independently derived results;
6. mutation tests for wrong landing values, forged joins, scope escapes, and
   producer-only verification; and
7. a pre-registered experiment if any claim about model behavior is desired.

Until those checks exist, the status remains `DRAFT DESIGN NOTE` and every
example is illustrative.

`AuthorityEffect: None.`

<!-- markdownlint-enable MD013 -->

## Fable source capture (incomplete)

The following source capture is retained as provenance. Multiple lines are
clipped mid-sentence, so it is not a complete or runnable prompt. No claim in
this design note relies on the capture's missing text.

### Original label: FABLE EXAMPLE

<!-- markdownlint-disable MD007 MD013 MD032 MD033 -->

---

[CHARTER]
mode: long-horizon construction run
effort: xhigh
autonomy: no questions; declared readings recorded
write_root: research/convention_price/ only
sealed: prompt/ paper/ code/ lean4/Derivation/ artifacts/ CLAUDE.md
  .github/workflows/ and every sibling research tree, receipts included
authority_effect: None

[SUPPLY]
supplied_challenge: |
  This run consumes two named leftovers, quoted from their trees:
  (1) sign_slice SS-09: "Whether the occurrence-relabel finding holds
  beyond the exhausted member and bound -- and whether any grammar-wide
  statement about the slot-convention group is true -- is OPEN;
  promotion requires Lean this tree does not carry."
  (2) natural_sections, sign-repair rung, non-claims: "re-signing along
  declared structure, as in the repair-mass rungs, is a DIFFERENT route
  and is not compared here -- comparing the two routes is named as a
  future rung so it cannot later be smuggled in as if done."
native_translation:
  - supplied: SS-09 promotion        native: ParityLaws + Promotion
    meaning: prove, in Lean, what the slot-convention group do
    two-label holonomy in general, and what the pointwise subgroup cannot do
  - supplied: the fenced comparison  native: ChannelTable
    meaning: on a shared signed census, decide per member which of the
    two repair channels applies -- slot relabelling, pairing c
    and exhibit or refuse separations
forbidden_in_write_root: the same supplied-physics list as sig
  fragment-built in test_forbidden.py; the working denylist; every
  outside theory name

[VOCABULARY]
admissible: hop, slot, parity, relabel, pointwise, holonomy, section,
  channel, certificate, domination, price, census, register, l
  GenPres, ConeSection (both as pinned reconstructions from sign_slice),
  plus the eleven evidence classes

[LAWS] as template v2, verbatim.

[REFUSALS] FW-SEAL FW-NAME FW-SET FW-TIES FW-TABLE FW-BILL FW-
FW-LEAD   this prompt states no result of phase 3; the author does not
          know whether the six-label square moves under the de
FW-SCOPE  every theorem of phase 1-2 is TWO-LABEL; no sentence extends
          it to larger fibres except as OPEN or as phase-3 com
FW-CHAIN  consume sign_slice terminals and receipts only, via pins;
          never its prose hopes

[PHASES]

phase_1 PARITY_LAWS (Lean, original theorems -- this run DOES
  proof package: a self-contained Lake package on the abstract two-label
  family, core Lean only, no sealed staging needed, axioms wit
  {propext, Quot.sound}, no sorry/admit/axiom/unsafe/partial):
  goal: the algebra of slot relabels on the two-label fibre.
  targets, named now:
    slot_toggles_parity   -- composing a hop transport with th
                             maps toggles its flip parity iff exactly one
                             slot map is the exchange
    cycle_parity_sum      -- a closed walk's relabelled holonomy parity is
                             the original parity plus the sum
                             parities its traversals consume
    pointwise_parity_blind -- a pointwise assignment contribut
                             object's parity an even number of times to
                             every closed walk, so cycle parit
                             (the packet's invariance, at parity level,
                             proved here abstractly rather tha
  predictions: all three provable in core Lean; misses recorded
  may_not: import sealed modules; cite the packet where an abs
    proof is required
  terminals: [PARITY_LAWS_PROVED, OPEN_AT_NAMED_TARGET]

phase_2 PROMOTION (Lean + computation):
  goal: the general two-label cure theorem and its price floor.
  targets:
    slot_group_sections   -- every connected two-label presentation with
                             at least one admissible pair is s
                             SOME slot assignment within the {identity,
                             exchange} bound: parities can be
                             hop, so all cycle parities vanish
    price floor           -- compute, per obstructed sign_slic
                             member (reconstructed under pin), the minimum
                             slot distance from the pointwise
                             general closed-form price is CONJECTURE or
                             OPEN unless proved
  predictions: slot_group_sections provable; the reconstructed square's
    price equals the pinned 2 from sign_slice; other members'
    recorded, not predicted
  may_not: extend slot_group_sections beyond two labels (FW-SC
  terminals: [PROMOTION_PROVED, PROMOTION_OPEN]

phase_3 THE_SIX_LABEL_EXPERIMENT (FINITE_COMPUTATION, FW-LEAD):
  goal: does the occupancy-3 square move?  Its holonomy is gen
    a three-mover rank cycle on the six-label fibre; the two-label
    theorem says nothing about it.
  bound, declared: slot maps range over the identity and the three
    adjacent rank-exchange label actions (four choices per slo
    configuration square has four hops, eight slots; the space is 4^8
    and is exhausted, not sampled.
  predictions: BOTH branches pre-agreed --
    if some assignment sections it: terminal MOVES, witness na
      computed, and the two-label scope note stands corrected only in
      the direction of MORE cure, never generalized;
    if none does: terminal INVARIANT_WITHIN_BOUND, stated with the bound
      in the same sentence, and the enlarged-bound question is
      leftover -- absence of a search is not invariance.
  terminals: [SIXLABEL_MOVES, SIXLABEL_INVARIANT_BOUNDED]

phase_4 CHANNEL_TABLE (FINITE_COMPUTATION):
  goal: the fenced comparison, executed.  On the signed members of the
    pinned sign_slice census (and each obstructed member's sig
    variant, declared here as amp -1 on parity-odd hops), decide per
    member: (a) slot-relabel curable within the phase-2/3 boun
    (b) pairing-certificate available for its closed-walk weight list at
    the declared length bound, by per-magnitude domination --
    criterion the natural_sections sign-repair rung proved, cited as
    CONDITIONAL_THEOREM and reconstructed as computation;
    (c) both; (d) neither.
  predictions: the table is nonempty in cell (a)-without-(b) o
    (b)-without-(a), or the separation is refused with the table as
    countermodel -- no cell is forced by this prompt
  may_not: treat the two channels as one; discard walks (the packet's
    discard countermodel binds)
  terminals: [CHANNELS_SEPARATED, CHANNELS_AGREE_ON_CENSUS, TABLE_WRITTEN]

phase_5 REGISTER_AND_LEFTOVER:
  goal: per-member rows as in sign_slice; the leftover names,
    the general price formula if unproved, the six-label enlarged bound
    if invariant, larger-fibre promotion, and anything phase 4
  terminals: [REGISTER_WRITTEN]

[ADVERSARIAL]
- A1 "slot_group_sections contradicts the packet's pointwise i
     -> refute: different groups; pointwise_parity_blind IS the invariance
- A2 "slot_group_sections answers the supplied challenge of ch
     -> refute by FW-SCOPE and FW-SET: two labels, declared bounds, a slice
- A3 "the six-label outcome extends by analogy to all fibres"
     -> refute: one member, one bound, computed
- A4 "price 2 is universal" -> decide per member; no extrapola
- A5 "the two channels are the same repair" -> separation table or its refusal
- A6 "unit-weight members needed curing all along"
     -> refute: their walk lists are already single-signed; record it
- A7 "a green Lean build discharges the six-label OPEN"
     -> refute: phase 3 is computation; its leftover stays OPEN
- A8 "the census is the set of all cases" -> FW-SET
- A9 "this run closes SS-09"
     -> partial only: the two-label half closes with slot_grou
        the larger-fibre half stays OPEN; say exactly that
- A10 "receipts prove the theorems" -> refute: Lean supports; re

[DELIVERABLES]
research/convention_price/: PROMPT.md (native, frozen, hashed);
PREDICTIONS.md (hashed per phase); SOURCE_MANIFEST.json + veri
(pin the sign_slice tree, the natural_sections SignRepair sources and
STATUS, at one exact 40-digit snapshot); lean/ (own package, c
AxiomReport with #print axioms per theorem); parity.py, promotion.py,
sixlabel.py, channels.py, register.py, run_convention_price.py
test_convention_price.py, test_forbidden.py; receipts/, STATUS.md
(terminals with scopes, the manual-receipt sentence, the unapp
registration diff), CLAIM_LEDGER.md.

[DONE] as template v2, verbatim, plus: the Lean package builds clean
with axiom reports inside the whitelist, and SS-09's dispositi
stated in the exact partial form of A9.

[TAU]
yaml_export:
  steps_completed: [ParityLaws, Promotion, SixLabel, ChannelTable, Register]
  write_root: research/convention_price/
  sealed_paths_touched: []
  prompt_hash_native: <sha256>
  predictions_hashes: [<per freeze>]
  terminals: [{code, scope}]
  sixlabel: {terminal: <...>, bound: four maps per slot, eight slots, 4^8 exhausted}
  channel_table: {members: <n>, a_only: <n>, b_only: <n>, both
  ss09_disposition: two-label half closed by slot_group_sections; larger fibres OPEN
  leftover: <named, priced>
  opens_unchanged: [OB1_UNCHANGED, S66_UNCHANGED, S9_LAST_UNCHANGED]
  authority_effect: None
final_state: <⊤ | ⊥>
op QED

---

<!-- markdownlint-enable MD007 MD013 MD032 MD033 -->

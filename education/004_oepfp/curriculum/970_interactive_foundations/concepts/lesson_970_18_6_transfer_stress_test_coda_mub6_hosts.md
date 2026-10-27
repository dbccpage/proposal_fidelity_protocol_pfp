# Lesson 970.18 -- 6. Transfer stress test: CODA and MUB6 hosts

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_970_18_6_transfer_stress_test_coda_mub6_hosts.ipynb](../notebooks/lesson_970_18_6_transfer_stress_test_coda_mub6_hosts.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## 6. Transfer stress test: CODA and MUB6 hosts

The same lesson about refusing unlicensed evidence can be *tested* in
two other source trees. CODA's finite-QM campaign checks whether a
result matches a frozen schema; that does not check whether its values
are true. MUB6's packet firewall refuses an undeclared operator and a
forbidden carrier codepoint; that does not classify MUB(6). These are
distinct programs and distinct contracts. This exercise offers no
Alpha-to-CODA or Alpha-to-MUB6 semantics.

**Assessment D (3 points).** Predict which CODA result is rejected and
which two MUB6 inputs refuse. Run the source-backed checks, then explain
why a clean schema and a clean packet can still carry a false claim.

## Answer key and evidence ceiling

<details><summary>Open after attempting A–C</summary>

- A: `(2 data, 1 form, 6 events)`. `supply`, admission, and imposition
  are events; observations are diagnostics. Adding `check data` leaves
  the event count six.
- B: the supplied mutant refuses on line 4 with arity 2 versus 1.
  Deleting `admit instance seen a` leaves the positive derivability
  check without its witness.
- M: the first and second repair each emit a new form and instance;
  the inert checkpoint emits none. Reports can agree after regeneration
  even though states and histories differ. The cookie labels are an
  outside interpretation of uninterpreted tokens.
- C: the adapter refuses a changed source, forged output, absent map,
  and absent diagnostic, while the host's
  self-edge violates its irreflexivity rule. The one-edge zero is
  board-relative. The weighted cycle starts with `Phi_1=3` and reaches
  zero only by replacing its claims.
- D: CODA accepts the conforming field set and flags the added
  timestamp field. MUB6 accepts `ASSERT` but refuses `QED` and a
  control character. These are schema and packet checks, respectively.

</details>

**19/19 local exercise points** are available from A, B, M, C, and D
(D contributes three points when the section 6 checks pass). They check
source-backed execution on this machine. The missing work is a typed,
observation-preserving Alpha-to-Core interpretation and independent
evidence that the corresponding host is the intended Engine.
Source anchors: Alpha `src/lib.rs`, `examples/first.alpha`,
`examples/refused.alpha`; Symbol Game Paper 032
`code/l1_symbol_game_governor.py`; Paper 033
`code/symbol_game_toolkit.py`. The first cell prints current SHA-256
digests for those executable sources. The last code cell prints SHA-256
digests for CODA's `check_result_schema.py` and MUB6's
`packet_firewall.py`.

> **Claim-typing legend**
> - **[Pinned]**: taken from a file this repository already has.
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a carrier, rule, or heading chosen for this sitting.
> - **[Open]**: something this sitting does not decide.
## Anchors

- Former notebook: `13_alpha_to_core_execution`
- The code checks one finite example. It is not a general proof.

## Exercise

Change one declared input in the code cell. The check should fail for the wrong object and pass for the finite example written here.

# PFP ladder, round 2 diagnostic (2026-10-21)

AuthorityEffect: None. This note records why round 2 prompts were abstained or rejected, what was changed in the ladder
because of it, and what the changes do when the stored replies are replayed. Every number below comes from the run folders
under `dag/results/<NODE>/runs/*_ladder*` (request, raw reply, per-attempt verdict) and from an **offline replay** of the 816
stored replies through the changed code. No provider call was made for this note.

## 1. Data

Round 2 covers 629 final prompts: free phase 116 (free models, then Haiku 5.5), Sonnet phase 513 (Sonnet 5.5 only, one attempt,
`--no-lean`, `--abstain-stop 2`).

| Phase | accepted | abstained | blocked | total |
|---|---:|---:|---:|---:|
| free | 54 | 49 | 13 | 116 |
| Sonnet | 314 | 0 | 199 | 513 |

The Sonnet phase never abstains by construction (an abstention needs two models), so its 199 `blocked` rows include its
abstentions.

## 2. Why the 261 non-accepted prompts were not accepted

Primary cause per prompt, read from the evidence on disk (the host-check files, the packets, the model's own
`open_obligations`) and, for the verifier causes, from replaying the stored reply through the patched checker.

| Cause | Free (62) | Sonnet (199) |
|---|---:|---:|
| (c) the verifier rejected a correct claim | 8 | 33 |
| (c) acceptance threshold `min_verified = 2` (1 verified claim, 0 refused) | 26 | 53 |
| (a) retrieval miss: the statement or anchors name a file in the checkout but `@SRC` was empty | 0 | 13 |
| (a) irrelevant `@SRC` offered and the model returned nothing (for the free models this may be timidity) | 25 | 39 |
| (e) correct abstention: no code to ground in this checkout | 3 | 59 |
| (d) genuine model error as the final cause | 0 | 2 |
| (b) schema or format as the final cause | 0 | 0 |
| (f) infrastructure | 0 | 0 |

Genuine hallucinations are rare: nonexistent declaration, wrong location and false arithmetic together are 20 failures in 816
answered attempts. Sonnet was never truncated (513 of 513 `end_turn`).

Packet signal in the Sonnet phase: with no `@SRC` line 18% of prompts were accepted (22 of 120); with `@SRC` and operation
candidates 94% (134 of 143); with `@SRC` and no operation candidates 63% (158 of 250). By node status: PROVED_LEAN 73%,
COMPUTATIONALLY_CHECKED 75%, DEFINITION 61%, SOURCE_RECORD 60%, OPEN 49%, IMPORTED_ASSUMPTION 46%, CONDITIONAL 41%.

### schema_violation (307 counted)

296 come from `poolside/laguna-s-2.1:free` (0 of 57 answers accepted, 21 cut at `max_tokens`) and 11 from
`nvidia/nemotron-3.5-lightning:free`. Groq, Haiku and Sonnet have none. The verifier counted one violation per missing
required array and per malformed item, so about 42 attempts make 307. The schema was never in the prompt text, only in
`response_format`, which OpenRouter free models accept but do not enforce (and on a 400 the adapter resent without it, leaving
the model with no schema at all). The content was often real: laguna cited real declarations in a flat shape without `id`,
`carrier` and `ref`. Schema violations were never the final cause, but they used 59 of 255 answered tier-0 attempts (23%) and
appear in 26 of the 31 free runs that escalated to paid Haiku.

## 3. Verifier and packet defects found (all confirmed against the sources)

1. **Placeholder skeleton.** `theorem x : True := by sorry` with `claims_proved = false` was `vacuous_proof`. 241 of 513
   Sonnet attempts (47%) contained one (the prompt said "may use sorry"); it was 336 of the 955 recorded failures.
2. **A lemma could never verify with Lean off.** A lemma citing an existing declaration that passed the same checks as a
   relation stayed `unverifiable`. Example: COMP-C4-SUPPLY-GROWTH, a correct `restates` lemma citing
   `GenesisComputation.supply_growth`, was recorded as blocked.
3. **`composition_type_mismatch` was mostly not a type mismatch.** 107 of 112 failures meant "a generator is `proposed_new`";
   colours matched in 83 of the 105 well-formed compositions.
4. **Arity heuristic** (`wrong_signature`, 124 failures, 35 of them verifier errors): Rust `rust_arity` stopped at the first
   `)` (`impl Fn(usize, usize)` counted twice); Lean `DeclIndex.statement` cut at `{` (implicit binders), so
   `def Word.concat {..} : W -> W -> W` counted 0; a `self` / `&self` receiver was excluded although an operation on the
   receiver type is the usual reading (27 of the 35); Lean default arguments (`:=` inside parentheses) were mis-split.
5. **`normalise_ref_fields`** did not strip `pub`, so `pub fn f(..)` and `pub mod m;` became "no declaration `pub`" (7), and
   `g:` / `r:` tags copied from `@KNOWN+` became "no declaration `g`".
6. **`statement_drift`** fired on the digit of a group name (`SU(2)`).
7. **Retrieval** read only the statement, ignored file names and the bottleneck, and its file-name fallback matched generic
   words ("contract", "omega", "test"), offering `ContractModel` for unrelated nodes.
8. **Ungroundable nodes were sent**: 59 Sonnet runs had no `@SRC`, no operation candidates and no code in the checkout.
9. **`numeric_claims`** supply both the expression and the value and are only checked for arithmetic, so they can fill the
   `min_verified` bar. 71 of 368 accepts (19%) depended on numerics or compositions to reach 2, and 43 had only numeric
   verified items. **Not changed** (a decision for the owner); see section 6 for the count after the fixes.

## 4. Changes (all in `dag/pfp/llm_ladder/`)

| Change | Where |
|---|---|
| `accepted_partial`: `verified >= partial_min_verified (1)` and **zero** refused claims, below `min_verified`. Terminal, no escalation, not an abstention, never folded into `accepted`. Config `accept_partial` (default on), `partial_min_verified`; CLI `--no-partial`, `--partial-min-verified`. Exit code 3. Recorded as attempt status `accepted_partial`, summary `status` and `partial_attempt`, host-check status `partial_reviewed_pending_host_semantic_review`. | `config.DEFAULT_POLICY`, `runner.LadderRunner._partial`, `run`, `_finish`, `records.host_check_record`, `ladder.py`, `replay.py`, `pilot.py` |
| Placeholder skeleton is no failure when `claims_proved` is false (the skeleton is ignored and a notice recorded). `claims_proved = true` with a tautology is still `vacuous_proof`. | `verify.Verifier.verify_p0` (lemma block) |
| A lemma whose cited existing declaration verifies counts as verified, labelled `declaration_exists_statement_consistent_ref_verified_not_lean_checked`. When Lean elaborates, the stronger `lean_elaborates` label wins. | same, `ref_verified`, `lean_unavailable` |
| Rust arity with balanced brackets, `self`/`&self`/`&mut self`/`&'a self` counted either way; Python `self`/`cls` counted either way; Lean header cut only at a top-level `:=`, ` where` or `|`; defaulted binders may be omitted. | `verify.rust_params`, `check_arity`, `lean_arity_options`, `cut_header`, `DeclIndex.statement` |
| Compositions over unverified or `proposed_new` generators are `unverifiable`; naming a generator that is not in the reply stays a failure. | `verify.Verifier.verify_p0` (composition block) |
| `pub`, `pub(crate)`, `noncomputable`, `mod`, `type`, `static`, `g:`/`r:` stripped from `ref.decl`. | `verify.normalise_ref_fields` |
| Group-name digits in a claim are not drift. | `verify.numerals`, `statement_drift` |
| A missing top-level array is read as `[]` with one notice (`VerifyReport.notices`); a present non-array is still a violation. | `verify.Verifier.verify_p0.items` |
| Retrieval reads statement and bottleneck, resolves file names through `DeclIndex.paths_by_basename`, uses node anchors with line suffixes, and applies a relevance floor (words in more than 300 file stems do not count; fuzzy offers rank below every strong tier). | `packets.source_candidates`, `named_files`, `anchor_path` |
| Pre-dispatch skip `skipped_ungroundable` (see below). Config `skip_ungroundable` (default on), CLI `--no-skip-ungroundable`; exit code 4; the dry run prints "WOULD BE SKIPPED". The run folder keeps a receipt with `external_provider_calls: 0`. | `packets.groundability`, `runner.run`, `plan`, `ladder.py` |
| Free tier: `poolside/laguna-s-2.1:free` removed, nemotron moved last. | `config.DEFAULT_TIERS` |
| Reply shape in the system text (`schema_example`), a rule to leave `lean_skeleton` empty instead of a placeholder, and the schema text appended when the provider does not enforce it (including the 400 fallback). | `packets.SYSTEM_P0`, `providers.OpenAICompatProvider._body` |
| Lean: the code names no version; it reads `lean4/lean-toolchain` (now `v4.35.0`). Only `design.md` still said 4.33.1; corrected. | `design.md` |

**The skip rule.** A node is `skipped_ungroundable` when it has no operation or relation candidates, no code file that it
names or anchors present in the checkout, no `@KNOWN+` entry from its DAG neighbours, and either an empty `@SRC` or (for
`SOURCE_RECORD` and `IMPORTED_ASSUMPTION` nodes only) nothing but fuzzy file-name matches. A finite target (DAG statement begins
"Finite statement to formalize") is never skipped. `@KNOWN+` counts because 23 round-2 Sonnet runs with an empty `@SRC` were
accepted with two or more citations that came from it.

## 5. Replay of the 629 stored runs (816 answered replies) through the changed code

"Before" is the stored outcome. "After" re-judges the stored replies in order with the new verifier and policy: the first
accepted attempt ends the run as `accepted`, the first `accepted_partial` attempt ends it as `accepted_partial`, two distinct
abstaining models end it as `abstained`, otherwise `blocked`. The skip column uses the new retrieval and the `@KNOWN+` count
that was actually injected in the stored run.

| Phase | Outcome | Before | After, no skip | After, with skip |
|---|---|---:|---:|---:|
| free (116) | accepted | 54 | 57 | 54 |
| | accepted_partial | 0 | 27 | 25 |
| | abstained | 49 | 30 | 22 |
| | blocked | 13 | 2 | 2 |
| | skipped_ungroundable | 0 | 0 | 13 |
| Sonnet (513) | accepted | 314 | 347 | 320 |
| | accepted_partial | 0 | 51 | 41 |
| | abstained | 0 | 0 | 0 |
| | blocked | 199 | 115 | 65 |
| | skipped_ungroundable | 0 | 0 | 87 |

Flips of the 261 non-accepted prompts, no skip: free 8 to `accepted`, 24 to `accepted_partial`, the rest stay abstained or
blocked; Sonnet 33 to `accepted`, 51 to `accepted_partial`, 115 stay blocked. The skip then removes 87 Sonnet runs from
the sent set: 50 that would still be blocked, 10 that would be partial and 27 that would be accepted. By stored outcome
they are 64 blocked and 23 accepted; 14 of the 64 blocked would have flipped under the verifier fixes.

**Accept invariant.** All 368 prior accepts still contain an accepted attempt under the patched verifier (368 of 368). In the
ordered replay 363 remain `accepted`; 5 free runs end one attempt earlier, 3 as `accepted_partial` and 2 as `abstained`,
because an earlier attempt that used to carry a spurious failure is now partial or an abstention (TFQ-0020, TFQ-0132,
TFQ-0144, TFQ-0139, TFQ-0177). With the skip on, 24 prior accepts (23 Sonnet, 1 free) would not have been sent: 12 of them were
numeric-only accepts, 1 had one ref-backed citation, and 11 had two or more ref-backed citations (SOURCE_RECORD nodes whose
fuzzy `@SRC` happened to hold the cited declarations). That is the price of the skip; it can be switched off.

Failure classes over all answered attempts, before to after: `vacuous_proof` 347 to 11, `composition_type_mismatch` 112 to 12,
`wrong_signature` 124 to 90, `nonexistent_declaration` 14 to 8, `schema_violation` 307 to 263 (the remainder is per-item
malformation in laguna and nemotron replies), `statement_drift` 26 to 31 (placeholder lemmas now reach the drift check),
`composition_unlicensed` 2 to 3, `unjustified_generalisation` 0 to 1. (`unparseable_reply` is not replayed: those replies
have no parsed body.)

**Numeric dependence after the fixes** (ordered terminal `accepted`, no skip): Sonnet 62 of 347 (18%) need numeric claims to
reach 2 verified items and 48 have only numeric verified items; free 9 of 57 and 1. Numeric claims were not changed.

## 6. The 58 frontier nodes merged by PR #162 (CT-, CQFT-, ADS-, LQG-)

Offline probe of `compile_p0` on the merged tree (no provider call): **30 skipped, 28 kept.**

| Status | Skipped | Kept |
|---|---:|---:|
| SOURCE_RECORD | 20 | 4 |
| IMPORTED_ASSUMPTION | 10 | 2 |
| OPEN | 0 | 19 |
| PROVED_LEAN / DEFINITION | 0 | 3 |

All 13 nodes whose id ends in `-TARGET` are kept (the request expected 14; 13 carry that suffix in the index). The 6 kept
SOURCE_RECORD and IMPORTED nodes name or anchor code in the checkout (`Entanglement.lean`, `spin_foam.rs`,
`H036...Recovery.lean`, ...) or have `@KNOWN+` entries from neighbours. Nine kept nodes have no anchor, no `@KNOWN+` and no strong
`@SRC`: 5 `*-TARGET`/`*-GAP` OPEN nodes with only fuzzy matches, and 4 more OPEN nodes. The fuzzy-only branch of the skip
applies to SOURCE_RECORD and IMPORTED_ASSUMPTION nodes only, so OPEN nodes with weak matches are sent.
`LQG-AREA-SPECTRUM-EXACT-TARGET` has no code anywhere and is kept only because a finite target is exempt from the skip.

## 7. Notes for `the external PFP package` (read-only inspection, no run data from that repo)

* The schema-delivery defect does **not** occur there: `use_cases/pfp_prompt.py` appends `json.dumps(schema)` to the system
  text. This ladder had diverged from it.
* `parse_proposal` demands the exact key set; a weak model without enforced structured output will fail the envelope the
  same way (it has a `TASK_ENVELOPE` repair rule and two stages).
* `REPAIR_RULES['SCOPE']` says an abstention is not a solution. For a node with nothing groundable, classify it and skip it
  before dispatch rather than forcing a witness.
* The retrieval, arity and unverified-generator defects are properties of this ladder's `verify.py` and `packets.py`; that
  repo selects operations from a fixed catalogue and uses task judges.
* Lessons that transfer: replay stored replies through a patched checker before blaming the model; do not charge a model for
  an artefact the prompt invited ("may use sorry"); keep a count of notices separate from failures; check that every free
  model honours the schema before it joins a rotation.

## 8. Not determined

* Whether the 39 Sonnet and 25 free "irrelevant `@SRC`, empty answer" prompts had a relevant declaration in the repository.
* Whether the weak accepts are correct mathematics; the checker confirms names, numerals and arithmetic only.
* The effect of `@KNOWN-` injection on abstention.
* Lemma quality: both phases ran `--no-lean`, so nothing was elaborated.
* The replay judges stored replies, not new ones: the new system text, retrieval and free-tier list change what models see,
  so real outcomes will differ from the table.

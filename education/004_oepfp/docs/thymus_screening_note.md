# Thymus screening soundness: Lemma C and the OEEIS self-panel gate in core Lean

**AuthorityEffect:** None. Proposal only; the status upgrade is Jeremy's.

Source revision read: `dbccpage/the_symbol_game` `origin/main` at
`8ac5da188390a93252614dfbb707f15d2c4fba42` (merge of #1152, 2026-10-17). The
prompt was written against `9ac0cd73d`; the cited lines of `paper.md` moved by
two (A.4 opens at line 727, the limitation paragraph is lines 750 to 752, the
test name is at line 754). The ledger row P3-22 is still line 37.

## Statement

Over a universe `U`, a detector rule has a screened predicate `P : U → Bool`
and an executed predicate `E : U → Bool`. A panel is a `List U`. The screen
*admits* the rule for `S` when every member of `S` has `P x = false`
(`admits`, `ThymusScreening.lean:36`). The rule *fires* on `S` when some
member has `E x = true` (`fires`, line 40). Screening is *sound* for `S` when
admission excludes firing (`soundFor`, line 43), and *never rejects a
harmless rule* for `S` when not firing implies admission
(`neverRejectsHarmless`, line 50).

**Lemma C** (paper A.4, lines 727 to 760; ledger P3-22):

1. `(∀ S, soundFor P E S) ↔ (∀ x, E x = true → P x = true)` — `sound_all_iff`.
2. `(∀ S, neverRejectsHarmless P E S) ↔ (∀ x, P x = true → E x = true)` —
   `never_rejects_all_iff`.
3. Both together `↔ (∀ x, E x = P x)` — `both_all_iff`.

**Self-Panel Soundness** (OEEIS note Section 2.2, lines 80 to 97). With
`thymusAdmit d sealed := sealed.all (fun s => !d s)` and
`falsePositives d sealed := (sealed.filter d).length`:
`thymusAdmit d sealed = true → falsePositives d sealed = 0`
(`self_panel_soundness`). The source writes the mean
`(1/|S|) Σ d(s) = 0`; the numerator is what is mechanized, and the mean is
zero for every nonempty panel. `thymus_admit_iff` shows the Bool gate is
`admits d sealed`, and `self_panel_sound_for_every_panel` is Lemma C part 1
at `E = P = d`.

## Proof

Part 1, forward: fix `x` with `E x = true`; case on `P x`. If `P x = false`,
the singleton panel `[x]` admits the rule (its only member is `x`,
`eq_of_mem_singleton`), so soundness for `[x]` forbids firing, yet
`⟨x, x ∈ [x], E x = true⟩` is a firing. Backward: an admitted rule has
`P x = false` on every member; a firing member would give `P x = true`, and
`false = true` is refuted by `Bool.false_ne_true`. Part 2 is the same with
`E` and `P` exchanged: if `E x = false`, the rule is harmless for `[x]`, so
it is admitted, so `P x = false`, against `P x = true`. Part 3 combines the
two by a four-way Bool case split. The Thymus part is an induction on the
sealed list: `all` splits as `&&` (`band_eq_true_iff`, by `decide`), `!d a =
true` is `d a = false` (`bnot_eq_true_iff`), and an admitted detector
filters nothing (`filter_eq_nil_of_admits`, by `rw [List.filter, ha]`).

Negative control (paper lines 754 to 760): universe `Record` with two self
records; `screenedByName` is constantly `false` (no record names
`MISSING_WITNESS`), `executedNoWitness` is `true` on the record without a
`"witness"` field. `control_admitted` and `control_fires_count = 1` are by
`decide`; `control_not_sound` and `control_implication_fails` are terms.

## What was reused and what Lemma C does not say

Reused: only core Lean 4 (`List.Mem`, `List.all`, `List.filter`, `Bool`); no
imports, no `Classical`, no library lemma beyond the definitions' equations.
Every cited theorem prints an empty axiom set.

The paper's own limit, quoted from lines 750 to 752: "Even $E=P$ guarantees
only the stated panel-relative property. It does not show that the panel
contains every valid input, nor estimate a false-suppression rate outside
it." The Lean says the same: every statement quantifies over members of a
given finite panel. Nothing here speaks to panel coverage or to behaviour
off the panel.

"Not yet attempted" re-checked at `8ac5da188`: `lean_theorems: []` at
`math_epistemic_immune_system_and_negative_selection.md:28` (now edited);
`004_oepfp/lean4/` held `CarrierOrigin.lean` and a README; `015_pfp/003`
has no `lean4/`; the WDP monograph has zero hits for "thymus", "self
panel", "negative selection", "screened predicate"; the obligations
register had no row (SG-EIS-001 appended, `status: OPEN` because
`PROPOSED_LEAN` is not in the file's status vocabulary; the `lean:` field
carries `PROPOSED_LEAN`).

## Proposed wording for P3-22 (deposit not edited)

Evidence column, append: "mechanized in
`omega_engine_education/documentation/004_oepfp/lean4/ThymusScreening.lean`
(`sound_all_iff`, `never_rejects_all_iff`, `both_all_iff`; Lean 4.34.0, no
axioms) at commit <merge commit>". The deposit carries `SHA256SUMS`, so this
is Jeremy's edit and repin.

## Receipt

- Exact command: `lean ThymusScreening.lean` run in
  `omega_engine_education/documentation/004_oepfp/lean4/`
- Tool version: `Lean (version 4.34.0, x86_64-unknown-linux-gnu, commit
  293d5d0c0c3f3dded4688b3ccd6a33939ac5102b, Release)`, release tarball
  `lean-4.34.0-linux.tar.zst` from GitHub (the elan installer host returned
  403 through the container proxy)
- Exit status: 0
- Tested scope: the one file, 264 lines; output:

```
'Oeeis.Thymus.sound_all_iff' does not depend on any axioms
'Oeeis.Thymus.never_rejects_all_iff' does not depend on any axioms
'Oeeis.Thymus.both_all_iff' does not depend on any axioms
'Oeeis.Thymus.thymus_admit_iff' does not depend on any axioms
'Oeeis.Thymus.self_panel_soundness' does not depend on any axioms
'Oeeis.Thymus.self_panel_sound_for_every_panel' does not depend on any axioms
'Oeeis.Thymus.control_not_sound' does not depend on any axioms
```

Jeremy's check on Windows: `cd omega_engine_education\documentation\004_oepfp\lean4`
then `lean ThymusScreening.lean` with `leanprover/lean4:v4.34.0`.

## Compaction envelope

- **Supports:** Lemma C parts 1 to 3 and Self-Panel Soundness as stated
  above, for every type `U`, every Bool predicate pair and every list panel,
  with no axioms.
- **Does not support:** anything about panel coverage, false suppression
  outside the panel, the mean FPR as a rational, or the runtime thymus code
  (P3-25 is a source audit, not formalized here).
- **Narrowest defensible claim:** a core-Lean file elaborates with exit 0 on
  Lean 4.34.0 and prints an empty axiom set for the seven cited theorems.
- **Next test:** `lean omega_engine_education/documentation/004_oepfp/lean4/ThymusScreening.lean`
  on Jeremy's machine.
- **Changeset:** branch `claude/thymus-screening-soundness-lean-8yai2f` from
  `8ac5da188`; files: `004_oepfp/lean4/ThymusScreening.lean` (new),
  `004_oepfp/docs/thymus_screening_note.md` (new),
  `004_oepfp/math/math_epistemic_immune_system_and_negative_selection.md`
  (list value), `004_oepfp/math/07_mathematical_obligations_register.yaml`
  (one row appended).

---
name: techne-generated-artifact-custody-auditor
description: "Check each shipped generated artifact still matches its generator and that a test opens the shipped copy."
operad_source_colours: ["Code", "Audit"]
operad_target_colour: "Audit"
operad_arity: 2
operad_residual: "unknown"
families: [code, testing, quality, falsification, governance]
---

# Generated Artifact Custody Auditor

**Status:** `CANDIDATE`
**AuthorityEffect:** `None` (Inspection tool; emits custody audit receipts)
**Governance Council:** `L3_logos_techne`

---

## 1. Prime Directive

A generated artifact has two failure modes, and the estate has historically
tested only the first.

1. **The generator is wrong.** Caught by hermetic fixture tests, which this
   repository writes well.
2. **The generator is right and the shipped copy is stale.** Caught only by a
   test that opens the file the repository actually ships.

This skill audits for the second. For every content-addressed artifact in the
estate it asks: *does anything verify the copy on disk, or only the code that
would produce it?*

---

## 2. The Witness

Sprint 028. `epic_manifest.json` had 48 tests. Every one of them constructed a
repository under `tmp_path`. None opened the manifest the repository ships.

So when an epic plan file grew from 8140 to 9513 bytes without the manifest
being regenerated, the suite stayed green and the drift merged to `origin/main`.
The audit was never wrong -- it refused the drift the instant it was pointed at
the real tree. What was missing was any test that pointed it there.

A suite can be large, green, rigorous, and aimed at nothing.

---

## 3. Artifact Inventory

Audit each of these, and any artifact matching the pattern *"a file the
repository ships whose content is derived from other files"*:

| Artifact | Generator | Custody question |
| --- | --- | --- |
| `plans/epics/epic_manifest.json` | `generate_epic_manifest.py` (delegating to `epic_manifest_audit.py --write`) | Does a test call the audit with the real repo root across direct files and canonical domain subfolders (`oesymgam`, `oewas`, `oeeis`, `oeadversary`)? |
| `contracts/MIRROR_MANIFEST.json` | Rust to Python contract mirror | Is the shipped per-file SHA256 recomputed against disk? |
| `architecture_baseline.json` | `architecture_fitness.py` | Is the ratchet compared to the live import graph? |
| `canonical_gate_catalog_sha256` | `domain.cicd.catalog.GATE_CATALOG_V3` | Does anything recompute it from the shipped YAML? |
| `golden_canonical_vectors.json` | Rust runtime | Is it replayed by a **second** implementation, or only by the one that wrote it? |
| `release_dossier.json` | hand-maintained | Does every claim name a test that exists, over the AST? |

A golden file checked solely by the implementation that produced it is a
self-comparison, not evidence.

---

## 4. Invariants & Rules

1. **Shipped-copy custody.** Every artifact above has at least one test that
   resolves the real repository root and audits the file on disk. Absence of
   such a test is the finding, whether or not the artifact is currently correct.
2. **Count from the source, not the artifact.** An inventory check must count
   the filesystem. Reading the count back out of the manifest agrees with itself
   whatever the directory holds.
3. **Shared constants, not restated literals.** Expected counts come from the
   one declared constant. A literal restated in a test is a second place to
   update, and the two drift apart in exactly the situation the count exists to
   detect.
4. **Regenerate, never transcribe.** A correction is produced by the shipped
   generator and the result compared, not by hand-editing a hash. A transcribed
   digest is the error the artifact exists to catch.
5. **Probes restore the tree.** A test that mutates the real tree to prove a
   refusal removes its probe in `finally` and re-asserts the clean state, so a
   failing assertion cannot poison the tests after it.
6. **Absence is not a pass.** An artifact with no subject in this repository is
   reported `UNVERIFIABLE` and blocks, distinctly from `VIOLATED`. An absent
   obligation must never read as a discharged one.
7. **Never synthesise the subject.** When the thing a deliverable operates on is
   absent, report the absence. Do not generate fixtures standing in for it so the
   deliverable can be demonstrated.
   - The distinction, since fixtures are legitimate everywhere else: a fixture
     standing in for *an input the system will really receive* is a test; a
     fixture standing in for *the thing whose existence is in question* is a
     simulation of the deliverable, and proves only that the code runs.
   - Report the absence as a **value**, not as a missing feature. A reader must
     not have to infer from an unbuilt indexer that there was nothing to index --
     that inference is indistinguishable from "someone forgot".
   - An absence detector must be tested **able to fire**. A check that could
     never report presence is a constant with a function signature, and it keeps
     passing after the subject arrives.
   - Witness (sprint 033): `EPIC-OE-SYMGAM-015` asks for an indexer over 5,000
     research placements that live in CODA. Generating 5,000 plausible fixture
     rows would have taken under an hour and produced a green suite over invented
     data. Declined; `corpus_state()` reports `AbsentFromThisRepository` instead.
8. **An artifact's own epistemic declaration outranks the plan.** When a data
   file states what its contents are -- a confidence level, an implementation
   status, a default -- that declaration was written by someone closer to the
   material than the plan's author. Read the header before the epic.
   - Look for fields like `implementation_default`, `status`,
     `legacy_field_policy`, `authority_effect`, `retirement_status`. They are
     load-bearing, and a plan written beside the file often does not know them.
   - A plan asking for more than the data claims for itself is not licence to
     supply the difference. It is a discrepancy to report.
   - Witness (sprint 034): `registry_glyph_games.yaml` declares
     `implementation_default: "proposed_fixture_unless_verifier_ref_is_named"`,
     and 14 of its 19 games name no verifier. The epic asked for an execution
     engine over "20+" games. Building one would have claimed five times more
     verified behaviour than exists -- and the strongest argument against it was
     a line the registry's own curator wrote.
   - Where a file states a rule about itself, enforce it as a **biconditional**
     unless the file says otherwise. "Implemented iff a verifier is named" has
     two failure directions: the overclaim, and the verified result reported as
     merely proposed.
9. **Correct code with no caller is not a discharged obligation.** A module
   implementing a stated law does not enforce it until something invokes it.
   Grep for callers before treating a law as held.
   - This is one step earlier than invariant 7's failure. There the tests were
     aimed at the wrong subject; here there is **no subject at all**. Both share
     a shape code review does not catch: the implementation is correct, and the
     omission is in what calls it. A diff shows the function; it does not show
     the absence of its callers.
   - Witness (sprint 035): `LosslessSkillParser` implements
     `render(parse(doc)) == doc` correctly, and a repository-wide search for
     `round_trips` found no caller outside its own module. Given one, 112 of 112
     skills passed on the first run. The parser was right; it had never been
     asked.
10. **A new tool's first run belongs against the estate, not fixtures.**
    Fixtures agree with the assumptions that produced them; the estate does not.
    - Three for three in one session: sprint 029's epic parser mis-read a
      two-word family name; sprint 031's guard heuristic reported every unguarded
      site as guarded; sprint 035's schema was over-strict *and* found two
      defects its own author had introduced two sprints earlier.
    - When a first run reports a violation, ask which is wrong -- the check or
      the data -- before fixing either. Sprint 035's audit flagged `ooutwire` for
      an empty `operad_source_colours`; the skill declares `operad_arity: 0`, so
      a nullary operation consuming no colours was exactly correct and the check
      was not.
11. **Measure the corpus before writing the schema.** A field the plan lists as
    required may be present in a minority of what ships. Report coverage as an
    exact pair, never a percentage -- 39 of 112 stays reproducible.
12. **Nearly-universal conventions are undocumented invariants.** When a corpus
    is measured for one property, look at what else holds in ~98% of it. Those
    are load-bearing rules nobody wrote down, and the residual few percent is
    where the drift is. Sprint 035 found `len(operad_source_colours) ==
    operad_arity` held by 110 of 112 skills, stated in no epic or template.
13. **A rule stated for a scope, enforced over a subset of it.** When a law names
    a boundary -- "the historical four host roots must agree", "every contract is mirrored" --
    check what the enforcing tool actually covers. The gap between the stated
    scope and the enforced scope is invisible from either side: the law reads as
    covering everything, and the tool passes on what it looks at.
    - Witness (sprint 036): the historical Four-Host Symmetry Law is stated for
      `.agents/`, `.claude/`, `.codex/`, `.grok/`. Twelve items sit under all
      former roots. `sync_cross_host_skills.py` covers `skills/`. Sweeping the
      other eleven found **3 of 36 mirror-pairs drifted**, all in `workflows/`,
      with the mirrors naming skills the canonical host had renamed.
    - Measure the stated scope, enumerate what the tool visits, and report the
      difference. It is usually minutes of work.
14. **A recorded verdict is a claim; ask what computed it.** Fields like
    `status: verified`, `type_valid: true`, or `passed: true` in a data file were
    written by whoever edited the file unless something recomputes them.
    - Witness (sprint 036): `composition_matrix.json` declared an associativity
      law `"verified"` while its own note said *"Structural registration only; no
      behavioral execution claim."* The evaluator that could compute it existed
      and nothing called it. Computing it confirmed the law -- but it had been
      asserted, not checked, for as long as both files had existed.
    - When checking a declared equality, compare the computation **to the
      declaration**, not only the computation to itself. Two paths can agree on a
      result the declaration does not name.
15. **Check the domain, not only the type.** When a field's legal values are
    enumerated somewhere -- a closed vocabulary, a status enum, a registry -- the
    validator must reference that enumeration. A `str` check where a closed set
    exists is a validator that has decided not to look.
    - Witness (sprint 037): a frontmatter audit validated
      `operad_source_colours` as *a list of non-empty strings* and never compared
      them to the closed ten-colour vocabulary. A skill declaring `"Governance"`
      passed the audit written specifically to check operad frontmatter, and
      survived two sprints until an unrelated loader crashed on it.
16. **An audit reporting "X is not a Y" is only as good as its definition of Y.**
    Before treating its output as defects, check whether the set it compares
    against is the whole legitimate namespace.
    - Witness (sprint 037): a workflow validator reported five operations as "not
      a skill". The estate has three operation namespaces -- skills, declared
      composites, and synthesized meta-skills -- and the validator knew one. One
      finding was a namespace gap in the validator, not a defect in the data.
    - Enumerate the namespaces before reporting absence from one of them.
17. **When a check's name is broader than what it checks, put the limit in the
    success path.** Failure messages get read; success messages get trusted. A
    caveat in a docstring reaches the reader of the implementation, not the
    caller who sees `OK` and stops.
    - This is the mirror of invariants 1-9. Those are claims true because nothing
      was examined. This one is a claim that is entirely correct and quietly
      means less than its name suggests -- and it is the easier mistake, because
      the code is right.
    - Witness (sprint 038): a hash chain over receipts verifies `INTACT`, and a
      chain **cannot detect entries removed from the end** -- delete the last
      three and what remains verifies perfectly. That is a property of hash
      chains, not a defect. The defect would be shipping `INTACT` and letting a
      reader conclude the ledger is complete. The limit is stated in the module
      docstring, in a test asserting the truncated chain still verifies, and --
      the placement that matters -- in the detail string `verify()` returns **on
      success**.
    - Where the limit cannot be closed, provide the thing that closes it from
      outside. That ledger exposes `tip()` for external anchoring, because
      nothing internal can catch a removed tail.
18. **Check declared targets against the tree.** An epic or spec naming a module,
   crate, or path is making a claim about the repository. Three consecutive
   sprints found that claim wrong -- a home that did not exist, two deliverables
   already built under another name, two whose subject had left.
- Tool: `epic_criteria_audit.py --targets` resolves every declared
     `Target Crates` entry. An unresolved target is not necessarily wrong -- the
     work may be to create it -- but it is a question to settle before planning
     rather than during discovery.
19. **Partitioned domain subfolder inventory.** When content-addressed artifacts (such as `epic_manifest.json`) span domain subfolders, the custody audit scanner must traverse both root direct files and canonical domain subfolders (`oesymgam/`, `oewas/`, `oeeis/`, `oeadversary/`), excluding out-of-scope sprint plans and governance documents per directory charters. Shipped manifest tests must verify that `audit_epic_manifest(REPO_ROOT)` passes against the real tree and that every registered epic matches disk byte-for-byte with uniform LF line endings.

---

## 5. Procedure

1. Inventory the artifacts (table above, plus any new match).
2. For each, grep its test modules for a real-repository root resolution
   (`parents[N]`, a repo-root fixture, or the generator's `_default_repo_root`).
   A suite using only `tmp_path` is a finding.
3. Run each generator in `--check` mode against the working tree and record the
   verdict as a `(checked, total)` pair, never a bare boolean.
4. For any finding, propose the missing test rather than repairing the artifact
   silently -- repairing it destroys the evidence that nothing was watching.
5. Emit an `Audit` receipt listing artifact, custody status, and the discharging
   test id for each.

---

## 6. Anti-Patterns

- Adding a real-repository test that **regenerates** the artifact before
  asserting. It then passes unconditionally and audits nothing.
- Reporting `0 of 0` as parity when an inventory came back empty.
- Folding `UNVERIFIABLE` into `SATISFIED` to make a gate green.
- Treating this skill's output as authority. It reports custody; promotion is
  the human's.

---

## 7. The Family: Evidence That Cannot Fail

Three skills, three faces of one failure mode:

| Skill | Failure it names |
| --- | --- |
| `techne-test-silent-skip-detector` | The test asserts nothing |
| **this skill** | The test asserts rigorously, against the wrong subject |
| `techne-unfalsifiable-gate-auditor` | The criterion names no falsifier at all |

A suite can be green because it skipped, because it was aimed at a fixture, or
because the bar it was measured against was never a bar.

Also related:

- `techne-four-host-parity-verifier` -- historical byte parity across former host roots.
- `techne-cicd-gate-catalog-dual-home-auditor` -- the gate-catalog row above.

---

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Ensure pure UTF-8 without BOM (`\xef\xbb\xbf`) with 0 linter errors and 0 warnings.

**AuthorityEffect:** `None`. Auditing custody is not certifying a release.

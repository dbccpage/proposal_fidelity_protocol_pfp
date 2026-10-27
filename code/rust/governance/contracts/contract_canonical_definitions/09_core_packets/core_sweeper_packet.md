packet_type: implementation
authority_effect: None
carrier: post-cutover audit window on the Rust-sole-producer Core Structure Sweep (C⁰)
primary_residual: discharged on a non-vacuous same-paper alpha pair plus witnessed beta and gamma coordinates (Q¹)
in_scope_repairs: alpha_same_paper_parity, runbook sole-producer declarations, no_python_sweeper_resurrection CI test, shared exact adapter (d₀)
deferred_residuals: sweeper self-audit anomalies, core_sweeper_fast, runbook vocabulary drift (core_sweeper_phase_b_packet.md)
seal_condition: evaluate_sweep_audit returns ExactRepair; canonical authority requires a packet-bound witness and certify_checked_sweep_audit

Core Sweeper Post-Cutover Audit (Obstruction Descent Packet)
=============================================================

**Date:** 2026-06-20
**App:** `core_sweeper` (Rust-sole-producer Core Structure Sweep)
**Status:** RUNTIME-CLOSED — Rust sweeper is the sole producer of record (Python rail retired 2026-06-13, PR #537). Alpha now has a non-empty same-paper Python/Rust parity carrier, beta is pinned to the runbook oracle, gamma has a positive-control no-resurrection guard, and all three coordinates evaluate through the shared GTOC/GTLA adapter.

**Bundle status:** load-bearing, no sibling lemma-packets. The three post-cutover sub-claims (alpha retroactive parity, beta runbook continuity, gamma CI no-resurrection) are carried as three defect rows inside this single packet per A1, not as a bundle of sibling packets.

This packet matches the 13-section canonical form in
`engine/crates/core_contracts/src/contract_canonical_definitions/core/09_packets/core_obstruction_packet_standard.md`.
DDA bindings cite `core_homology`, `core_functional`,
`core_discrete_deformation_algebra` (DDA), `core_sweep_kernel`, and
`core_certifiers`. Markdown does not mint authority.
`core_sweep_kernel::terminalize::terminalize_row` emits a product-local lane
stamp only. Canonical authority can arise only from the exact checked packet,
a packet-bound `DescentWitness`, decided `IsAuth`, and
`core_certifiers::certify_checked_packet`.

1. Carrier & 2-Window Definition
--------------------------------

**Carrier:** The post-cutover audit window on the Rust-sole-producer Core
Structure Sweep — opened by PR #537 (merged 2026-06-13) and not yet sealed by
a retroactive parity audit + runbook continuity + CI guard.

The carrier is NOT "two live producers"; the Python rail is dead. The carrier
is the audit-trail residual:

* **Rust producer (sole, live)** — `core_sweeper` (binary in
  `engine/core_layer_applications/core_sweeper/src/main.rs`,
  CLI subcommands in `src/cli.rs`, use cases under `src/usecases/`),
  driving the pure-decision kernel `core_sweep_kernel`
  (`engine/crates/core_sweep_kernel/src/lib.rs`: `validator`,
  `route`, `terminalize`, `canon_hash`, `bundle`, `harness`,
  `authority_bridge`).

* **Archived Python rail (read-only, forensic)** — the 15 retired scripts
  preserved under `engine/research/core_sweeper/scripts/.archive/`
  with `RETIRED.md` at the parent level naming the cutover date
  (2026-06-13), PR (#537), and Tier B parity status. No live `.py` files
  remain at the `scripts/` top level. This packet treats the archive as
  read-only forensic material — never as a live producer.

The evaluation preorder is the per-row decision lattice of the structure sweep
(`validate -> route -> ingest -> gate -> synthesis -> promote -> terminalize`),
ordered by the `(packet_id, phase)` idempotence index. The 2-window inspects:

* **Local window** ($C^0 \to C^1$): one row's `(validator outcome, route
  decision, terminal record)` triple as recorded on disk in archived run
  artifacts (last Python-authored vs. first Rust-authored).

* **Closure window** ($C^1 \to C^2$): cross-run coherence over the
  append-only lane files and the terminalizer's sealed lane stamp across
  the cutover boundary — runs 003 (Python) and 004 (first Rust),
  read-only, plus the runbook and CI-guard surface that prevent future
  drift.

The audit boundary is fixed at 2026-06-13 (PR #537). The audit is
retroactive and read-only on the Python side.

2. Declare $C^0$
----------------

**$C^0$ (Assignments):**

* The Rust rail `core_sweep_kernel` (5 slices) is built, tested, and merged
  (PRs #535 + #537); Tier B byte-exact replay parity holds on runs 003 and 004
  (`tests/replay_parity_tier_b.rs`, `tests/replay_parity.rs`).

* The Python rail is retired as of 2026-06-13 (PR #537). The live
  `engine/research/core_sweeper/scripts/` tree contains only
  `RETIRED.md`, `.archive/` (15 historic scripts), `__pycache__/`, and
  `tests/`. There are NO live `.py` files at the top level.

* The Rust CLI `core_sweeper` exposes the 12 subcommands of the Python rail
  with verbatim exit codes (`cli.rs` header: `validate 0/1/2`, `route 0/1`,
  `ingest-pass 1 on echo mismatch/quarantine`, `claim 0/4`, `ingest-gate 1`,
  `prepare-synthesis 3 without --approve`, `promote dry-run unless
  --execute`, `init-run` errors on existing run).

* Hostile fixtures (26) and Tier B replay artifacts are still the acceptance
  contract — now on the Rust rail alone.

* `terminalize_row` is the sole producer of the Rust rail's product-local
  `Decision::Certified` / `host_terminal_status: Certificate` lane stamp. Its
  legacy `authority_ceiling = "established_within_declared_scope"` field is
  scoped to that product record and maps to no canonical authority outcome.
  The shared adapter binds exact alpha/beta/gamma evidence to a
  `CheckedPacket`; only the packet-bound certifier bridge may create
  `CertifiedAuthority`.

* The DDA crate (`core_discrete_deformation_algebra`) exposes `FaceLambda`,
  `NonDestructiveExtensionCertificate`, and `FiniteLambdaStepCertificate` —
  the licensed shape for any $\Meta$ proposal on the audit window.

* The remote-agent runbook (`research/core_sweeper/remote_agent_runbook.md`)
  is the operator-facing surface; whether it already names the Rust binary
  as sole producer with NO "choose your rail" framing is a $C^1$ check, not
  an assumption.

3. Declare $d_0$
----------------

**$d_0$ (Primitive Operator):** The lambda of gauge-trivial audit
refactorings — actions that do not change any externally observable
artifact a downstream consumer can hash. Permitted $d_0$ moves:

* Rename internal variables, reorder pure local statements, reflow
  comments in the Rust crates.

* Edit the runbook prose without changing the named commands, flags,
  exit codes, or trust-model rules.

* Add new test fixtures without changing the schemas of the existing 26.
* READ archived Python run artifacts and `.archive/` script contents
  for forensic / parity-audit purposes. Reading is gauge; writing or
  re-executing the archived rail is NOT.

* Add tests, audit fixtures, and CI guards to the Rust rail that
  enforce the post-cutover invariant.

What $d_0$ is NOT permitted to do (these are $C^1$ defects, not gauge):
re-create or re-execute the Python rail; restore any `.py` file from
`.archive/` to the live `scripts/` top level; relabel the archive as a
live producer; change canonical hashing, validator outcomes, router
decisions, or terminalizer seals; redirect remote-agent runbooks to a
non-Rust producer; or alter exit codes.

4. Emit $C^1$
-------------

**$C^1$ (Defects / Inconsistencies):** The cutover happened (PR #537);
the post-cutover audit window has not been sealed. Open residuals:

1. **No retroactive parity certificate.** Tier B replay parity holds on
   runs 003 and 004 individually, but no single audit asserts byte-exact
   `core_sweep_kernel::canon_hash::content_hash` equivalence between the
   LAST Python-authored archived run and the FIRST Rust-authored archived
   run on overlapping row ids. The audit must read both from disk
   (read-only) and produce one hash-equivalence table committed as a
   fixture.

2. **Runbook continuity unverified.** `research/core_sweeper/remote_agent_runbook.md`
   is the operator-facing surface after cutover. Whether it (a) names
   `core-sweeper` as the sole producer, (b) contains NO "choose your
   rail" framing, and (c) preserves every $d_0$-protected token
   (subcommand names, flags, exit codes) verbatim from the pre-cutover
   pinned oracle is currently un-tested.

3. **No CI no-resurrection guard.** Nothing fails CI if a developer
   adds a new live `.py` file under
   `engine/research/core_sweeper/scripts/` (outside `.archive/`,
   `__pycache__/`, and `tests/`). The cutover is enforced by convention
   today; the guard must be a real test.

4. **No sweeper self-audit.** The Rust sweeper has never been run on
   itself to produce an Core Structure Sweep report on its own crate
   tree — i.e. eat its own dogfood and emit a certified bundle whose
   row is the Rust sweeper's own source.

5. **`memory.md` stale.** Operator memory still records "Python cutover =
   operator decision at a run boundary"; the cutover has happened, so
   the entry's open framing is stale. (Memory edits are operator-only by
   doctrine; this packet ships a marker file, not the edit itself.)

5. Declare ZeroRel
------------------

**ZeroRel (Gauge Relation):** Two audit trajectories on the carrier are
ZeroRel-equivalent iff, for every retroactively-audited archived run, every
runbook-token check, every CI-guard fixture evaluation:

* the canonical content hash (`core_sweep_kernel::canon_hash::content_hash`,
  YAML merge-key-aware) of every recorded lane file is byte-equal,

* the validator outcome (`ValidationOutcome` variant + payload) is equal,
* the route decision (`RouteDecision` + `Phase`) is equal,
* the terminal record (`TerminalRecord`) is equal,
* the `(packet_id, phase)` idempotence index over each audited run is
  set-equal,

* the runbook's $d_0$-protected token set is byte-equal to the pinned
  oracle,

* and the CI guard rejects every fabricated-resurrection fixture and
  accepts every clean-Rust fixture (positive control).

Cosmetic differences inside archived `.md` lane files that do NOT
change `content_hash` are ZeroRel (the canonical hasher is precisely the
chosen gauge witness). The producer-identity coordinate is FIXED to
"Rust" on the live side and "archived Python" on the forensic side — the
audit reads, never re-runs.

6. Compute $Q^1$
----------------

**$Q^1$ (Quotient / Residuals):** The non-removable residual after
ZeroRel collapse is a single closed survivor:

> One sealed post-cutover audit window that (a) retroactively certifies
> byte-exact `content_hash` lane-equivalence between the LAST archived
> Python-authored run and the FIRST archived Rust-authored run on
> overlapping row ids, (b) certifies the runbook names the Rust binary as
> the sole producer of record with every $d_0$-protected token byte-preserved
> from the pinned oracle, and (c) ships a CI no-resurrection guard with
> positive control against any future live `.py` file under
> `engine/research/core_sweeper/scripts/`.

This residual cannot be removed by gauge shifts (the audit-trail gap is
an objective state, not a labelling choice). It cannot be removed by
$d_0$ refactoring (adding a real audit + guard is structural, not
cosmetic). It is exactly the kind of $Q^1$ that is repairable by a
licensed $\Meta$ — a `FaceLambda` from the DDA — at the audit-window
boundary.

There are no co-equal Q¹ residuals (no `core_sweeper_fast` candidate
is in scope; `research/core_sweeper_fast/remote_agent_runbook.md`
is out of carrier for this packet).

7. Declare $d_1$
----------------

**$d_1$ (Closure Operator):** The triple-overlap closure across the
post-cutover audit window. For three overlapping coordinates:

* the retroactive parity certificate (LAST Python run vs. FIRST Rust
  run on archived artifacts),

* the runbook-continuity certificate (Rust-sole-producer declaration +
  $d_0$-token preservation), and

* the CI no-resurrection guard (with positive control over fabricated
  Python-rail resurrection),

$d_1$ requires that all three patches agree as cocycles: the retroactive
parity is read-only on archived artifacts (no Python re-execution); the
runbook edit preserves every named CLI surface; and the CI guard rejects
exactly the resurrection set (live `.py` files under `scripts/` outside
the `.archive/`, `__pycache__/`, `tests/` allowlist) and accepts the
clean set. None of the three may regress the others.

8. Compute $\Gamma_2$
---------------------

**$\Gamma_2$ (Closure Failure Mass):** Per A1, computed per defect. The historical-surface witness ($\Gamma_2 = 0$ on Tier B replay parity for runs 003 and 004) is held by the committed kernel tests and is shared baseline for all three defects; each defect's audit-window contribution is currently unmeasured pending the audit sprint cochain.

| Defect | $\Gamma_2$ | Witness |
| --- | --- | --- |
| alpha (retroactive parity) | $0$ on a non-vacuous carrier | `tests/alpha_same_paper_parity.rs` requires `overlap_count > 0` and equality of hash, validator, route, and product-terminal fields for the same paper and packet ID. |
| beta (runbook continuity) | $0$ | `tests/runbook_declares_rust_sole_producer.rs` verifies the non-empty pinned $d_0$ token oracle. |
| gamma (CI no-resurrection) | $0$ | `tests/no_python_sweeper_resurrection.rs` accepts the live root and rejects the committed positive control. |
| delta_self_audit (self-audit) | deferred / Phase-B | future core_sweeper_phase_b_packet |
| delta_memory_stale (memory stale) | retired by marker | marker file + operator action |

The audit sprint must drive every row's $\Gamma_2$ to $0$ before the packet may seal at the Target terminal in section 13.

9. Compute $\Phi_1$
-------------------

**$\Phi_1$ (Quotient Obstruction Mass):** Per A1, computed per defect. The single $Q^1$ closed-survivor class of section 6 decomposes into three observable primal coordinates $(\alpha, \beta, \gamma)$; each carries unit mass at packet authoring and the same audit-window face-lambda drives each to $0$.

| Defect | $\Phi_1$ | Witness |
| --- | --- | --- |
| alpha (retroactive parity) | $0$ | The committed same-paper table contains a real shared packet ID and all parity dimensions are equal. |
| beta (runbook continuity) | $0$ | Every token in the non-empty preservation oracle remains in the Rust-only runbook. |
| gamma (CI no-resurrection) | $0$ | The live scripts root passes and the fabricated Python resurrection is rejected. |
| delta_self_audit (self-audit) | deferred / Phase-B | future core_sweeper_phase_b_packet |
| delta_memory_stale (memory stale) | retired by marker | marker file + operator action |

The mass on each row is irreducible by $d_0$: read-only forensic audits cannot synthesize the parity certificate, runbook certificate, or CI guard out of cosmetic edits.

10. Classify System State
-------------------------

Per A1, classified per defect. The trichotomy classes are: Exact repair (no lift), Closed survivor (stabilize / terminalize / lift with preservation witness), Active closure failure (repair closure or request higher-cell / lift with coherence witness), and No rule (typed refusal / new packet-family request).

| Defect | Class |
| --- | --- |
| alpha (retroactive parity) | Exact repair — non-vacuous same-paper parity residual is zero. |
| beta (runbook continuity) | Exact repair — runbook oracle residual is zero. |
| gamma (CI no-resurrection) | Exact repair — live/positive-control guard residual is zero. |
| delta_self_audit (self-audit) | No rule (deferred to Phase-B successor packet) |
| delta_memory_stale (memory stale) | Closed survivor (retired by marker file + operator action) |

The shared adapter classifies the joint alpha/beta/gamma residual as `ExactRepair`. This classification is checked evidence only and creates no authority by itself.

11. Propose $\Meta$ (Lift Candidate)
------------------------------------

**Oracles required:** none. Per A3, no imported representation theorem (Gleason, Hilbert space, Born ontology, or any transformation licensed from outside the declared finite 2-window) is consumed by this packet. Every witness in section 12 is computable inside the existing DDA / `core_sweep_kernel` / `core_functional` contract on the audit window.

**$\Meta$ (Lift / Structural Extension):** Propose a single DDA face
lambda that seals the post-cutover audit window.

* **Lambda type:** `core_discrete_deformation_algebra::FaceLambda`
  with face index = the audit-window boundary at PR #537 (2026-06-13).

* **Non-destruction witness:** an
  `core_discrete_deformation_algebra::NonDestructiveExtensionCertificate`
  attesting that (1) the archived Python rail under
  `engine/research/core_sweeper/scripts/.archive/` is preserved
  byte-equal (no edits, no deletions), (2) the runbook's
  $d_0$-protected token set (subcommand names, flags, exit codes from §3)
  is byte-equal to the pinned pre-edit oracle after the runbook edit,
  and (3) Tier B byte-exact replay parity continues to pass on runs 003
  and 004 (`tests/replay_parity_tier_b.rs`).

* **Finite-step witness:** a `FiniteLambdaStepCertificate` enumerating
  three audit steps (retroactive parity audit, runbook continuity
  audit, CI no-resurrection guard) so the lift is a finite face-lambda
  composition, not an unbounded refactor.

* **Preservation witness (cocycle side):** the Tier B parity test
  continues to pass on runs 003 and 004 after the audit lands, AND a
  new test `tests/retroactive_parity_audit.rs` is added that loads
  archived Python and Rust run artifacts (read-only) and asserts
  `content_hash` equality across every overlapping row id.

* **Obstruction witness:** $\Phi_1 = 1$, $Q^1$ = "one sealed post-cutover
  audit window", computed by reading sections 6 and 9 of this packet.
  After the lift, $\Phi_1 = 0$ on the carrier and the packet
  terminalizes Repaired.

* **Terminal routes:** `core_sweep_kernel::terminalize::terminalize_row`
  stamps only the product lane. `core_sweeper::evaluate_sweep_audit` builds
  the exact shared evaluation and checked packet. The separately named
  `certify_checked_sweep_audit` wrapper delegates to the sole
  `core_certifiers::certify_checked_packet` bridge and requires a
  packet-bound descent witness plus decided `IsAuth`. Markdown and product
  lane stamps mint no canonical authority.

* **License:** this $\Meta$ is licensed by the existing operator
  ruling that the cutover happened at PR #537 (2026-06-13) and the
  post-cutover audit trail is a residual to be closed — not by any new
  authority created here.

The lambda is a Repaired-class lift, not an oracle request: every
witness is computable inside the existing DDA / `core_sweep_kernel`
contract; no new algebraic structure is introduced.

12. Execute DDA
---------------

**DDC (Discrete Deformation Calculus):** The execution sequence is a
finite composition of DDA face lambdas, each backed by a runnable
test on the Rust rail. No Lean obligations are added by this packet
(the audit is operational, not a new theorem on the kernel's
algebra).

1. **Quotient projection ($R$).** Confirm $Q^1$ by reading sections
   6 and 9 against the committed kernel:

   ```bash
   cd C:/Users/a343o/source/repos/sentinel/engine
   cargo test -j 1 -p core_sweep_kernel
   cargo test -j 1 -p core_sweeper --test replay_parity_tier_b
   ```

   Both must pass before the lambda is proposed.

2. **Face lambda ($\Meta$).** Apply the three audit steps:
   * Add the retroactive parity audit test that reads the archived
     last-Python-run and first-Rust-run artifacts (read-only) and
     asserts byte-exact `content_hash` equality on overlapping row ids.

   * Edit `engine/research/core_sweeper/remote_agent_runbook.md`
     so it names the Rust binary as the sole producer of record with
     no "choose your rail" framing, and pin every $d_0$-protected
     token to a fixture oracle that the runbook continuity test
     enforces byte-equal.

   * Add CI guard `tests/no_python_sweeper_resurrection.rs` that fails
     if any live `.py` file appears under
     `engine/research/core_sweeper/scripts/` outside the
     allowlist (`.archive/`, `__pycache__/`, `tests/`), with a
     positive-control fixture the guard MUST reject.

3. **Descent ($D$) / preservation check.** Re-run Tier B replay
   parity and the new audit tests:

   ```bash
   cd C:/Users/a343o/source/repos/sentinel/engine
   cargo test -j 1 -p core_sweeper --test replay_parity_tier_b
   cargo test -j 1 -p core_sweeper --test retroactive_parity_audit
   cargo test -j 1 -p core_sweeper --test runbook_declares_rust_sole_producer
   cargo test -j 1 -p core_sweeper --test no_python_sweeper_resurrection
   ```

   All four must pass. The first protects history; the others are the
   non-destruction witnesses for the audit-window lambda.

4. **Integration ($I$).** Run the $\Phi_1 / \Gamma_2$ closure check
   on the carrier exactly and append the result to the DDA log. Per A5
   this step is the canonical $I$ (Integration / DDA-log append); the
   previous draft labelled it "Diagnostic ($D'$)", which is not a member
   of the canonical DDA alphabet {E, R, C, I, Meta/Lambda, D, M, T} —
   the work it does (computing closure certificates and recording
   observers into the audit log) is exactly Integration. Build an
   `core_functional::ExactPhi1Certificate` directly (it is the named
   entry point for an exact obstruction certificate; the auditor
   constructs the cochain residual + dual annihilators + primal
   value inside the test body), then pass it through
   `core_functional::Phi1Functional::verify_exact_certificate(cert)`
   to obtain a sealed `VerifiedExactPhi1`; assert `.value()`
   returns `&BigRational::from(0)`. The cochain represents the three
   named sub-claims $(\alpha, \beta, \gamma)$ from §13 as primal
   residual coordinates. Build a `DegreeOneResidualQ` against an
   `ExactCochainComplexQ` on the same carrier, then call
   `core_functional::Gamma2Functional::try_compute_exact_quotient(&residual_q)`
   and assert `.value() == &BigRational::from(0)`. Record two
   `core_functional::Observer` audit-only structs (one for $\Phi_1$,
   one for $\Gamma_2$) — `{id: String, kind: ObserverKind}` records,
   NOT callables; they have no `.observe()` method, only audit
   identity. Expectation after the lambda: $\Phi_1 = 0$, $\Gamma_2 = 0$
   over all three coordinates.

5. **Product terminal and canonical gate.** When a self-audit row is produced,
   its product terminal record is stamped by
   `core_sweep_kernel::terminalize::terminalize_row(&row,
   author_model, gate_model) -> TerminalRecord`. The survivor path returns
   `Decision::Certified` and
   `host_terminal_status == "Certificate"`. There is no
   `Decision::Repaired` variant, and `authority_bridge` maps this product
   stamp to no canonical terminal. Separately, call
   `evaluate_sweep_audit`; only an `ExactRepair` checked packet with a
   packet-bound `DescentWitness` and decided `IsAuth` may cross
   `certify_checked_sweep_audit`. Markdown in this packet is diagnostic,
   not authoritative.

**EPK side-channel:** `core_epk` may emit residual diagnostics on
the audit window (paper 020), but cannot mint authority. Symbol Game
adapter (`pfp`) is not invoked by this packet.

13. Terminal Status
-------------------

Per A1 and A4, terminal status is recorded per defect, separating Current terminal, Target terminal, and the Seal Condition. Product terminalization is not canonical authority. The only authority path is the checked packet plus a packet-bound `DescentWitness`, decided `IsAuth`, and `core_certifiers::certify_checked_packet`. Markdown does not mint authority.

| Defect | Current | Target | Seal Condition |
| --- | --- | --- | --- |
| alpha (retroactive parity) | Repaired | Repaired | `alpha_same_paper_parity` requires a non-empty overlap and full parity; `gtoc_adapter` binds the zero residual to the shared exact packet. |
| beta (runbook continuity) | Repaired | Repaired | `runbook_declares_rust_sole_producer` verifies the pinned non-empty oracle; `gtoc_adapter` binds the zero residual. |
| gamma (CI no-resurrection) | Repaired | Repaired | `no_python_sweeper_resurrection` verifies live acceptance and positive-control rejection; `gtoc_adapter` binds the zero residual. |
| delta_self_audit (self-audit) | deferred / Phase-B | dogfood sweep row | future core_sweeper_phase_b_packet |
| delta_memory_stale (memory stale) | retired by marker | operator-memory edit outside packet authority | marker file + operator action |

The cross-defect integration seal requires `phi1_zero_after_audit` to return exact $\Phi_1 = 0$ and $\Gamma_2 = 0$, plus `gtoc_adapter` to return `ExactRepair`. `Decision::Certified` remains only the kernel product-lane success stamp.

**Alpha closure update (2026-07-17).** The historical run-003/run-004 pair remains intentionally disjoint and is retained only for Tier-B history replay. `tests/alpha_same_paper_parity.rs` now supplies the missing same-paper carrier: one archived-Python and one Rust-replay snapshot share `paper_001` and `SCP-001-02-001`; the test requires `overlap_count > 0` and checks hash, validator, route, and product-terminal equality. The committed `alpha_same_paper_parity_table.json` is the non-vacuous alpha witness consumed by the exact closure test.

**Operator-memory retirement (closes packet §4 C1 #5).** The
`memory.md` staleness defect is retired in this sprint via a marker
file at `engine/research/core_sweeper/post_cutover_audit/operator_memory_retirement.md`
naming the merged terminalizer-seal PR. The operator's actual `MEMORY.md`
edit is the operator's privilege (memory is operator-only by doctrine);
the marker is the cochain witness this packet ships.

**Out of carrier (NOT residuals of this packet):** the Python rail
itself is out of scope — it was retired 2026-06-13 (PR #537) and the
live `engine/research/core_sweeper/scripts/` tree contains only
`RETIRED.md`, `.archive/`, `__pycache__/`, and `tests/`. Re-running the
Python rail is forbidden (the audit is read-only on archived
artifacts). `core_sweeper_fast` is also out of carrier per §6.

**defer:** A Phase-B successor packet
`core_sweeper_phase_b_packet.md` (to be authored only if any of the
following surfaces) covers: (i) any drift in the runbook
$d_0$-protected vocabulary after S5 lands, (ii) `core_sweeper_fast`,
and (iii) any sweeper self-audit anomaly emitted by a future dogfood
run. None of these are declared $Q^1$ residuals of this packet; they
are forward defers.

14. S16-001 current-base disposition
------------------------------------

At observer `e5ff14fe71b7dc4ddd732c8ca43b50a23c89544c`, `core_sweeper::gtoc_adapter::evaluate_sweep_audit` constructs `GtocExactInput` and calls `core_pipeline::gtoc_gtla::evaluate_exact`; same-paper parity and focused adapter tests are present. Production convergence and a separately promoted cross-lane receipt remain owned by `S16-005`. This lane remains `OpenObstruction`, with `AuthorityEffect::None` and no human promotion. The S16-001 census records the current packet hash and source manifest; the historical `runtime-converged` marker is implementation evidence, not authority.

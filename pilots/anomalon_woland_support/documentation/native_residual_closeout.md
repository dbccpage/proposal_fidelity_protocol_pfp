# Woland native residual closeout

AuthorityEffect: None. Baseline: `9bb95a38a10951f28ddc432a2808a7277c8652d0`.

N1/N2/F1/V1 use existing owners. `run_research_envelope` uses native-required
CODA/LGGR ports; P1 `WdpAbstentionGovernor.report` uses native WDP certificate
replay. Independent Python witness checks and paper differential tests remain.
Main's retirement of the incorrect Python Phi1 heuristic is preserved: CODA's
explicit reference selection uses the separately verified native L1 oracle.
Missing native tools never select a production fallback.

## Run the public finite tasks

From the repository with its normal Python environment:

```powershell
cargo build --offline --manifest-path omega_engine/crates_rs/Cargo.toml -p omega_symbol_game --bin omega_symbol_game -j 1 --target-dir .scratch/native-residual-build
$env:OMEGA_SYMBOL_GAME_HOST = (Resolve-Path '.scratch/native-residual-build/debug/omega_symbol_game.exe').Path
python -m omega_engine_woland.documentation.examples.native_residuals --output .scratch/native-residual-example
```

Choose a **new** output directory. The example calls public Woland and P1
consumers, retains native captures and checks distinct task bindings. Its inner
envelope bouts are explicit fixtures, with no model calls or authority.

| Task | CODA | LGGR | P1 at declared budget |
| --- | --- | --- | --- |
| `woland-native-residual-public-1` | Exact repair; `phi1=0` | Identity; delta `0` | `ResolvedWithinBudget`, budget `3` |
| `woland-native-residual-public-2` | Coherent residual; `phi1=2` | Local green/global red; delta `-1` | `Exhausted`, budget `2` |

Each task has fresh source/candidate/question bindings. CODA replays primal/dual
bounds; LGGR recomputes products and thresholds. Green flags or digests alone
establish neither result nor detector adequacy.

## Actual full-Retinue IDE run

Run `woland-residual-closeout-20261016` completed all 22 roles, 22 checked IDE
captures, two successful original-task episodes, one AutoP/learning finish and
five strict applicable-gate checkpoints. Roles were sequential perspectives in
this IDE session; implementation helpers retain separate PFP replies. These
are not 22 independent model agents. External provider dispatches were zero;
IDE billing remains unobserved.
This run belongs to implementation commit `ad633a78a153bae3e9fd81f3a0c6208623c38e51`.
Later main reconciliation preserves its frozen executable and historical captures;
integrated-head checks are recorded separately rather than relabeling this run.

Main reconciliation at `bef50fb2e243414aea7aa97dbf8ecf13fa085cde` preserved its
native-only Phi1 correction. The integrated executable is
`88f8b91d7ce98e08d1224361cb723c2db5a22f4af9f1988cf8877c6cd57d2489`.
Forty-two CODA compatibility/native/refusal controls passed on it, followed by
three boundary controls covering all 15 WDP reference records, strict scoped
intake replay and required-witness HOLD. Both public finite examples also passed
with fresh captures. These are integrated-head checks, not a second swarm run.

The host selected [software scope](../config/software_gate_scope_v1.json) before
work: IG05 at intake, then Natasha/PFP transport once captures existed. Required
gates passed at every applicable checkpoint. The 33 unselected scientific,
proof and empirical predicates are explicitly not applicable, not PASS.
Configured observers must appear at post-check and stopped checkpoints; listing
them only in the unvisited successful-run `native_finish` cannot enforce them.
Unscoped historical runs retain all35 behavior and their original outcomes.

Use `/woland` and the existing [shared-backend commands](shared_teamwork.md).
Python embedding uses that guide's coordinator with
`bind_native_gate_check(..., policy='require_pass', gate_scope=scope)`.
The shell waits for actual IDE replies and cannot impersonate the IDE session.
When attaching learned changes, retain every original artifact in the separate
host mapping. This demonstration resumed the same pending learner after fixing
an incomplete driver mapping; raw reply, state and allowance were preserved.

The canonical bundle is
`_ic/woland/runs/woland-residual-closeout-20261016-000a2c9cc661` in the primary
checkout. Reporting-only retry obtained sink write access without changing the
completed state or executing another task, checker or learner. Its five files
are `uns.md`, `uts.jsonl`, `ddc.jsonl`, `summary.json` and `receipt.json`.
Read-only replay verified every retained PFP binding and native gate batch,
33 observed actions, 37 DDC records and 37 unique ordered UTS events. All 11
pinned historical state/report files remained byte-identical.

| Binding | SHA-256 |
| --- | --- |
| Native executable | `89a48efd5aba73d149c889afe5fb069e26161678b88602e7fdf469e407c3973e` |
| Saved state | `a75335b18a8f222cebcd0a051b0a0deba8b78d88ac00257f9a877cfb9ebf1e7a` |
| Canonical receipt ID | `1cb71bc10828b864306ac3ede86317e8b60e4ed00f74ea9443cf63343d76baaf` |

## Deciding verification and limits

- Application owners: 57 Python checks passed, including all 15 reference
  certificate records, public P1 labels, malformed scalars/replies, source
  binding and historical custody bytes.
- Woland consumer/bridge owners: 27 checks passed, including the public
  research-envelope route, missing tools and forged/transplanted witnesses.
  Scope/historical-wire and three configured-observer controls passed separately.
- Rust: the selected `omega_wdp --lib application_kernel::tests` target passed
  both tests with `-j 1`; no whole-workspace result is claimed.
- Lean: selected `Woland.NativeModelBridge` build and full census passed:
  660 declarations, 266 theorems, no added axioms or `sorry`.
  [`Gate14.byte_mismatch_projects_to_bottom`](../../lean4/research_programs/woland/NativeModelBridge.lean)
  derives the concrete finite negative under named replay/source/projection/model
  premises and the existing foundational axiom policy.

Profiles are flat rational CODA carriers of dimension at most eight, bounded
2x2 rational closed paths, and bounded ASCII exact-rational WDP replay. General
compiler fidelity, detector adequacy, unrestricted mathematical claims, other
WDP product migrations and HoTT are not established. P2 retains its explicit
legacy loader. Broader prior-art transfers remain research hypotheses.
The unrelated global prior-art inventory audit still refuses `INVENTORY_INVALID`;
historical inventory bytes were not repinned to hide it.

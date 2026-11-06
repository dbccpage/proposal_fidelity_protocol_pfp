# Reusable PFP batch toolkit

Adapted from the tools of batch `20261020T000351Z_prompts_132_151` (which stay sealed and are not edited). What is
reusable is the bookkeeping; what is not is any per-node mathematics. Each node brings its own spec: a reviewed profile,
an operad delta, an independent checker, a wire formatter, optional semantic near-miss mutants and the candidate data.
Nothing here calls a provider, and nothing accepts a theorem. AuthorityEffect: None.

Run every command from the repository root as `python -X utf8 dag/pfp/batch_tools/pfp_batch.py <command>`.
`--root DIR` selects another tree (the tests use it); `PFP_ROOT` does the same.

## What changed from the 132-151 tools

| Old | New |
|---|---|
| Hard-coded `C:\Users\...` roots, Born-boundary specs, `born_boundary_checker` | Root found from the file; node-specific parts supplied by `specs/<NODE>.json` |
| Per-batch copy of the tools inside the sealed batch | One shared toolkit; the batch records `tooling_pins` (informational, never required to match on replay) |
| Native gates hard-coded to Python, one Rust test, one Lean module | Declarative `p2_gates` per node; `needs: cargo` or `lean` select the guard and environment |
| Lean version implied by the installed compiler | Read from `lean4/lean-toolchain`; `lean --version` must name it, or P2 reports a repairable `G5_SCOPE` defect and integrate refuses |
| Cargo target wherever; errno 28 on a full disk | Short `CARGO_TARGET_DIR`, pre-clear when over `--max-target-gb`, free-space pre-check (`--min-free-gb`) |
| P4 = output-coordinate perturbations | Coordinate mutants plus a task-specific **semantic near-miss hook** and valid semantic controls |
| `next_test` boilerplate | `validate_spec` refuses boilerplate or a `next_test` equal to `does_not_support` |
| Companions as `X.contract.yaml` / `X.score.yaml` | `X.contract.score.yaml` through `scripts/contract_scores.write_legacy`, plus `X.<ext>.doc.yaml` |
| `verify_batch.py` compared the live index to the sealed one (breaks after the next batch) and expected old companion names | Compares only the batch's own rows, checks the combined companion layout |
| Self-review only | `dag_status_depends_on_result` in the profile requires a second reviewer who is not the author before `finalize` seals |

Not reusable and deliberately left behind: `tools/specs.py`, `born_boundary_checker.py` and friends, `native.py`
(user-specific `PACKAGES` path), `lean_order.json`, `integrate_after_source_successor.py`, the header-only PG-SN successor
custody and `publish.py` with its branch name and `gh` call baked in.

## Per-batch command sequence

Rows are taken from `dag/operads/index.json` in order: the first un-run row starts the batch, with no cherry-picking.
`--batch` accepts a folder name under `dag/results/batches/` or a path.

```
# 0. environment
python -X utf8 dag/pfp/batch_tools/pfp_batch.py toolchain
python -X utf8 dag/pfp/batch_tools/pfp_batch.py disk-check --need-gb 20

# 1. select and seal  (writes selection.json, index_before.json, execution_policy.json, .gitattributes)
python -X utf8 dag/pfp/batch_tools/pfp_batch.py init --count 20 [--start <first un-run position>] [--batch-id ID]

# 2. P0 request and byte-custody inventory for every selected node
python -X utf8 dag/pfp/batch_tools/pfp_batch.py prepare-p0 --batch B [--external external=PATH]

# 3. write dag/results/batches/B/specs/<NODE>.json (and the checker/format/mutant files it names), then
python -X utf8 dag/pfp/batch_tools/pfp_batch.py p0 --batch B        # reviewed missions + host review
python -X utf8 dag/pfp/batch_tools/pfp_batch.py p1 --batch B        # seal candidate, snapshots, request

# 4. P2 host verification, P4 challenge, P5 record (retained P2 results are reused)
python -X utf8 dag/pfp/batch_tools/pfp_batch.py p2  --batch B --node ID      # optional, to look at a gate alone
python -X utf8 dag/pfp/batch_tools/pfp_batch.py run --batch B [--waive-semantic "reason"]

# 5. repair, only after a repairable host check; a repair is a new attempt and keeps the failed one
python -X utf8 dag/pfp/batch_tools/pfp_batch.py p3 --batch B --node ID --attempt p3a
python -X utf8 dag/pfp/batch_tools/pfp_batch.py p1 --batch B --node ID --attempt p3a   # spec key repairs.p3a
python -X utf8 dag/pfp/batch_tools/pfp_batch.py run --batch B --node ID --attempt p3a

# 6. review, companions, integration, seal
python -X utf8 dag/pfp/batch_tools/pfp_batch.py review     --batch B --label <stamp>_batch_audit [--second-reviews FILE]
python -X utf8 dag/pfp/batch_tools/pfp_batch.py companions --batch B
python -X utf8 dag/pfp/batch_tools/pfp_batch.py integrate  --batch B
python -X utf8 dag/pfp/batch_tools/pfp_batch.py finalize   --batch B --review-label <stamp>_batch_audit

# 7. replay (twice: normal and -O), then commit; push and PR only when asked
python -X utf8 dag/pfp/batch_tools/pfp_batch.py verify  --batch B
python -X utf8 -O dag/pfp/batch_tools/verify_batch.py B
python -X utf8 dag/pfp/batch_tools/pfp_batch.py publish --batch B --message "..." --trailer "Co-Authored-By: ..."
```

Order matters: `companions` and `integrate` must follow `review` (they bind the reviewed bytes) and precede `finalize`.
Edit nothing under a finalized batch; `verify` fails on any sealed byte.

## The node spec (`specs/<NODE_ID>.json`)

```
profile        reviewed profile; required keys are listed in stages.PROFILE_KEYS
               claim_boundary {supports, does_not_support, narrowest_claim, next_test}
               p2_gates       [{id, argv, cwd, needs: null|cargo|lean, stdin_file, pins}]
               p2_checks      {lean: {gate, anchors}, wire: {gate, module}, tests: {name: {gate, stream, pattern}}}
               challenge      {ignore_paths, max_coordinate_mutants, semantic_waiver}
               dag_status_depends_on_result   bool, forces a second reviewer
               review         {reviewed_target_qualification}
public_input   JSON visible to the checker (written beside it as public_input.json)
operad_delta   add_or_refine_generators / _relations, checked_compositions, failed_compositions, counterexamples, open_obligations
checker        file copied to the run as check_candidate.py; check(request, candidate) raises ValueError to reject
format         file copied as format_certificate.py; lines(data) is the wire form compared with the native replay
semantic_mutants  optional file, see below
candidate      {data, public_tsv}; repairs.<attempt> has the same shape (+ optional source_names)
```

Gate argv tokens: `{python}`, `{cargo}`, `{lean}`, `{root}`, `{run}`, `{attempt}`, `{candidate}`, `{request}`.

## Semantic near-miss hook (P4)

Coordinate mutants (one leaf changed, one list tail dropped, one key deleted) are generated for every candidate. They
catch a careless checker but say little about the mathematics. The node therefore supplies `semantic_mutants.py`:

```python
def semantic_mutants(data, profile):   # each must be REJECTED by check_candidate
    return [{'id': 'swap_basis', 'rationale': 'why a reviewer would believe it', 'mutate': fn}]

def semantic_controls(data, profile):  # optional; each must be ACCEPTED
    return [{'id': 'relabel_rows', 'rationale': 'valid change beside the near miss', 'mutate': fn}]
```

`mutate(data)` edits a copy in place and must change it. Good near misses are counterexamples to the unpaid bridge named
in `does_not_support`: a wrong carrier, a gauge off by one, a swapped convention, a finite instance that fails the general
statement. P4 refuses to run without at least one, unless `--waive-semantic` (or `challenge.semantic_waiver`) carries a
written reason of 40 characters or more; the waiver is recorded in `p4/host_check.json`, the README and `verify`.

## Disk and cargo guard

`disk-check`, `p2`, `run` and `integrate` call `disk_precheck` (default 20 GiB free before Rust, 1 GiB before Lean). Rust gates
run with `CARGO_TARGET_DIR` set by `cargo_target_guard`: a short path (`~/.pfp-ct` by default, refusing Windows paths over 40
characters because of MAX_PATH), cleared first when larger than `--max-target-gb` (default 6), then re-checked for free
space. Pass `--cargo-target PATH` to choose another short directory. The guard report is stored in each P2 checkpoint.

## Lean version

`lean4/lean-toolchain` is the only place a version is named. `selection.json` records it; P2 and integrate run
`lean --version` through a receipt and fail the gate when the output does not name it. A toolchain migration therefore
needs no tool change. The tests use a throwaway tree with a made-up toolchain version and a stand-in `lean` executable.

## Tests

```
python -X utf8 dag/pfp/batch_tools/test_batch_tools.py -v
```

They build a temporary tree with three dummy nodes (prompts from `dag/pfp/generate_prompts.py`), a git base commit, and run
selection, P0-P5, a repair attempt, review, second-reviewer refusal, companions, integrate (normal and `-O`), finalize,
verify (including tamper detection), publish and the disk/cargo/Lean guards. No network, no Mathlib, no cargo build.

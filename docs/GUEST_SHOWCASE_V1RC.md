# Guest showcase for omegaengine_pfp_v1.0rc

AuthorityEffect: None.

This page is the three-minute path for an invited guest. The default path spends nothing. A live model call stays closed unless a separate whole-run budget manifest admits it, and the published page never opens that path.

## What you can check

1. A scenario lab with the moves ASSERT, CUT, VERIFY, and RETRACT, plus a browser SHA-256 check of one sealed sample.
2. A three-tier funnel view: cheap Python and Lean 4 permutations, an operational quotient, then offline role adapters named opus-5.5-xhigh and fable-5.2.
3. A six-arm strand replay. On the sealed curriculum the holdout accuracy of the full loop matches PFP alone. That null is part of the receipt.

The sealed campaign supports exact comparisons among those six offline arms, including the zero holdout delta. It does not support a positive held-out transfer claim, a live-model result, or a statement about tasks outside the sealed curriculum. The narrowest claim is the equality of those two holdout rows and the token ordering on that same receipt. Negative controls are the direct arm, the best-of-k arm, and the naive-memory arm.

## One-command local replay

From the repository root, with the existing virtualenv:

```text
.venv\Scripts\python.exe -B -X utf8 -m pfp_core.release_surface_v1rc
```

On Linux or macOS the interpreter is `.venv/bin/python` with the same flags. The command prints two digests and does not contact a model provider.

Install the Python tools, if the environment is new, with `pip install -e ".[dev,workflows]"`. Do not use `uv run`. The console scripts are `pfp-lab` and `pfp-lab-web`.

The Rust command, after `cargo build --manifest-path code/rust/pfp_cli/Cargo.toml --release`, is:

```text
code/rust/pfp_cli/target/release/pfp demo
```

On Windows the built file name is `pfp.exe`. `pfp-cli` is its own workspace, separate from `code/rust/Cargo.toml`.

`pfp demo` prints a non-empty local report. `pfp --help` is not the replay.

## Static page

`pfp-lab-web` serves the same page on `http://127.0.0.1:8765/`. Opening `pfp_lab/web/static/index.html` directly also loads `app.js` and `app.css` beside that file. The published GitHub Pages bundle is that static directory. Live mode asks for an invite token and still performs no provider call in this bundle.

## Kernel root

`FunnelCompressionClosure` is a root of `SymbolGameKernel` in `lean4/lakefile.lean`. This checkout has no `lean4/PfpKernel.lean`. The Lean file's axiom listing is the root-scope record for that closure.

## Release tag

Merging to `main`, or pushing the tag `v1.0.0-rc1`, runs `.github/workflows/deploy_showcase_v1rc.yml`. The tag also builds standalone `pfp` binaries and a `SHA256SUMS` file. The sums committed at the repository root cover the guest page sources.

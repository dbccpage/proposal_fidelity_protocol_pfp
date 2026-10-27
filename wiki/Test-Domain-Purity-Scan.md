# Test: Domain Purity Scan

A static check, using Python's `ast` module, that the domain modules of the
paper-run package never touch the disk. Pure modules may not call `open()` or
any `read_bytes`, `read_text`, `write_bytes` or `write_text` method. The few
modules that do I/O are listed with the exact calls they make today, so new
I/O cannot creep in without someone changing the list.

## What it tests

`test_paper_run_domain_purity.py` (15 tests) scans `demos/paper_run_rules/paperrun/`:

- Each of the 12 pure modules (claims, obligations, transitions, run plan,
  stage list, services, result type, planning use case) has zero disk-I/O
  calls.
- Every module in the package is classified as either pure or recorded; a new
  file that is neither fails the test.
- The three recorded modules stay within their allowance: `carrier.py` may
  call `read_text`, `tree_hash.py` may call `read_bytes`, `stage_driver.py`
  may call `read_text`.
- A negative control: the scanner finds both calls in a planted file. Without
  it, an empty result could mean the scanner is blind.

## Why it matters to PFP

PFP checks are meant to be pure functions over frozen inputs: given the same
carrier and the same events, they give the same verdict. A domain function
that quietly reads a file is no longer a function of its inputs, and its
result cannot be replayed from a receipt. Keeping I/O at the edge (the carrier
and the tape) is what lets the role rules be tested without a filesystem. See
[Core Concepts](Core-Concepts.md).

## Setup and inputs

None. The test reads the package source files next to it and parses them; it
imports nothing from the package.

## How to run

From the repository root:

    python -m pytest demos/paper_run_rules/test_paper_run_domain_purity.py -q

## Expected output

`15 passed` in under a second.

## What a failure means

- A pure module reports a call: someone added file access to the domain. Move
  it to an adapter and pass the data in.
- "Every module is classified" fails: a new module was added; declare it pure
  or record what I/O it needs.
- An unrecorded call in an I/O module: its disk access grew; either record it
  deliberately or remove it.

## How to modify it

Edit `PURE_MODULES` and `RECORDED_IO` at the top of the test. To catch more
kinds of I/O (for example `Path.open`, `os.remove` or `shutil` calls), add
names to `IO_METHODS` or extend `disk_io_calls`, and add a planted example to
the negative control. The scanner is about 15 lines and can be pointed at any
package folder.

## Port notes

Ported from an internal test suite, where it scanned a larger research
package with its own list of legacy I/O files. Here it is pointed at the
ported `paperrun` package, the allowance list matches that package, and the
classification test and negative control are new.

## Location

`demos/paper_run_rules/test_paper_run_domain_purity.py`.

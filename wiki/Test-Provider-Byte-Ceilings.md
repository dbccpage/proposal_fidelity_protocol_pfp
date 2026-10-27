# Test: Provider Byte Ceilings

Before a prompt is sent to a language-model provider, and before a reply is
decoded, both are checked against fixed byte ceilings: 64 KiB for the combined
prompt, 1 MiB for the raw reply. These tests check that the ceilings bound the
right thing (the combined prompt, the whole reply body), count bytes rather
than characters, refuse with bounded work, and produce a refusal receipt that
contains no payload text.

## What it tests

`test_reply_guard_byte_ceilings.py` (15 tests).

Prompt ceiling (`CandidateRequest.check_payload_ceiling`):

- exactly 64 KiB is admitted; one byte more is refused with
  `SWARM_PROVIDER_PROMPT_TOO_LARGE`;
- a system part and a user part that are each under the ceiling but over it
  together are refused, and so are chat messages that add up past it;
- 16,385 four-byte emoji are refused although there are fewer characters
  than the limit;
- a 20-million-character prompt is refused with `observed_bytes` equal to
  limit + 1, which shows the check stopped reading early;
- a secret marker in the prompt does not appear in the error or the receipt;
- an unpaired surrogate (not valid UTF-8) is refused with its own code;
- a prompt refusal is a different exception type from a budget refusal.

Reply ceiling (`check_reply_bytes` and `decode_reply`):

- a `memoryview` over 4-byte integers is measured and hashed as octets, so
  the receipt digest covers exactly limit + 1 bytes;
- a reply padded to 1 MiB + 1 byte is refused; at 1 MiB and one byte below
  it is admitted;
- a large `metadata` field cannot hide behind a two-byte `content`;
- an already decoded dictionary is refused: only raw bytes count as evidence.

## Why it matters to PFP

PFP treats everything coming from a model as untrusted input. A size that is
measured but not enforced bounds nothing, and a check that reads the whole
oversize input to refuse it has already done the expensive work. The receipt
rules matter for custody: a refusal says which limit fired and how much was
observed, with a digest of only the bytes actually read, and never repeats the
hostile text. See [Core Concepts](Core-Concepts.md).

## Setup and inputs

None beyond the standard library. Prompts and replies are built in the test.
No network or provider is used.

## How to run

From the repository root:

    python -m pytest demos/provider_reply_guard/test_reply_guard_byte_ceilings.py -q

## Expected output

`15 passed` in under a second.

## What a failure means

- An over-limit case admitted: the ceiling is checked on the wrong thing
  (one field, decoded content, characters).
- `observed_bytes` larger than limit + 1: the check walked the whole payload.
- A marker found in a message: refusals now leak input text into logs.

## How to modify it

The ceilings and refusal codes are in `replyguard/limits.py`; the request and
reply checks are in `replyguard/provider_types.py`. Pass `limit=` to
`check_payload_ceiling` or `check_reply_bytes` to try other sizes. The refusal
codes keep their original names.

## Port notes

Ported from an internal test suite. The original also drove a full provider
gateway and checked that a refused prompt charged no budget and reached no
provider; that gateway depends on unported runtime pieces, so those checks
were not ported. The reply checks call `decode_reply` directly instead of
going through the gateway. The chat-message case is new.

## Location

`demos/provider_reply_guard/` (package `replyguard/`).

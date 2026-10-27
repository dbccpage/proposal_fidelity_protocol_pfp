# Test: Strict Provider Reply JSON

A model provider's reply arrives as raw bytes that should be a JSON object.
Python's default `json.loads` quietly accepts things that make a reply
ambiguous: duplicate keys (last one wins), `NaN` and `Infinity`, and numbers
that overflow to infinity. This test checks a strict decoder that refuses all
of these with a fixed message, before any provider-specific parsing, and
without echoing the reply.

## What it tests

`test_reply_guard_strict_json.py` (30 tests, mostly parametrised) against
`replyguard.wire.decode_reply`:

- Clean replies decode to exactly the original value, whether given as
  `bytes`, `bytearray` or `memoryview`, including large finite floats, keys
  that differ only in case, and text that looks like an instruction.
- Duplicate keys are refused, including a duplicate spelled with a `e`
  escape and a duplicate deep inside metadata. Each case is built so that a
  last-key-wins decoder would return the clean value, so the refusal is about
  ambiguity alone.
- `NaN`, `Infinity`, `-Infinity`, `1e999` and `-1e999` are refused even in
  nested metadata nobody reads.
- Invalid UTF-8, bare words, trailing garbage and bad escapes become one
  decode error, and a marker in the reply does not appear in the message.
- An integer longer than the interpreter's digit limit is a decode refusal,
  not a crash.
- `null`, `[]`, `true` and `42` are refused: the root must be an object.
- An oversize reply is refused on size before JSON decoding starts.

Every refusal case first decodes a clean reply, as a positive control.

## Why it matters to PFP

Receipts and checks downstream rely on reading the same reply the same way
every time. If a reply can carry two values for `content` or a token count,
two readers can disagree about what the model said. Refusing ambiguity at the
boundary keeps one meaning per reply. See [Core Concepts](Core-Concepts.md)
and [Provider Byte Ceilings](Test-Provider-Byte-Ceilings.md).

## Setup and inputs

Standard library only. Replies are small JSON documents built in the test and
then edited by string replacement.

## How to run

From the repository root:

    python -m pytest demos/provider_reply_guard/test_reply_guard_strict_json.py -q

## Expected output

`30 passed` in under a second.

## What a failure means

- A duplicate or non-finite case decoded: the decoder hooks
  (`object_pairs_hook`, `parse_float`, `parse_constant`) were removed or
  bypassed.
- A clean case changed value: the decoder rewrote data it should keep.
- A message containing `CANARY`: an error now quotes the reply.

## How to modify it

The decoder is about 30 lines in `replyguard/wire.py`. Add a case to a
parametrize list to cover a new ambiguity, keeping the rule that the edited
reply must still parse under plain `json.loads`.

## Port notes

Ported from an internal test suite. The original went through a full provider
gateway and also recorded that the provider-specific parser was never called
on a refused reply; here the decoder is called directly, which keeps every
input and expected message but drops that call-order check. One non-ASCII
sample character was replaced with another.

## Location

`demos/provider_reply_guard/test_reply_guard_strict_json.py`.

# Provider reply guard

Guards that sit between a proposal engine and a language-model provider:

- a combined prompt ceiling measured in UTF-8 bytes, refused with bounded work;
- a reply ceiling measured on the raw response octets, before any decoding;
- a strict JSON decoder that refuses duplicate keys, non-finite numbers,
  undecodable bytes and non-object roots, without echoing the reply.

`replyguard/` holds the ported modules (standard library only); the
`test_reply_guard_*.py` files are the tests. No network is used.

Run from the repository root:

    python -m pytest demos/provider_reply_guard -q

Expected: `45 passed`.

Wiki pages: Test-Provider-Byte-Ceilings, Test-Strict-Provider-Reply-JSON.

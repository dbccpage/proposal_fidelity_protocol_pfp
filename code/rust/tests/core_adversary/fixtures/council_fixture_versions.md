# Council fixture versions

`python_council_before_native_v1.json` is the exact original fixture from
commit `f7ad2e3d17`, captured before the Python council implementation delegated
to Rust. Its embedded YAML and expected identities are tested together.

`python_council_v1.json` remains byte-identical to the repository's preceding
revision. Commit `e6537cc3cf` rewrote its embedded YAML locations while retaining
the older expected catalog identities. It is retained as historical material;
it cannot serve as a consistent assembly vector.

`python_council_catalog_v2.json` captures the current canonical YAML with the
existing generator. It checks current catalog binding and the Python/Rust
surface, while the original pre-native fixture supplies the independent
historical implementation comparison. The current generator delegates through
the native loader and is not a second independent implementation.

Regenerate only a new current capture with:

```text
python -m adversary.tests.generate_rust_council_fixtures --output python_council_catalog_v2.json
```

The generator does not rewrite the immutable native layout or historical files.

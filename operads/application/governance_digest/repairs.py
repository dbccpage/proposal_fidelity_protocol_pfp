"""Checked-in repairs. Fingerprints are the pre-edit span and the post-edit span.

They are not recomputed from whatever the file happens to contain. A later edit
that is not this planned text matches neither value and is ``anchor_changed``.
AuthorityEffect: None.
"""

from __future__ import annotations

from ...domain.governance_digest.records import EditLocator, RepairSpec

PY_RULE = "omega_engine_operads/rules/engineering/rl_python_engineering_standards.md"
PY_CONTRACTS_RULE = "omega_engine_operads/rules/engineering/rl_python_contracts_and_runtime_invariants.md"
RS_RULE = "omega_engine_operads/rules/engineering/rl_rust_engineering_standards.md"
RS_SKILL = "omega_engine_operads/skills/techne-code-rust-anti-patterns/SKILL.md"
HUNTER = "omega_engine_operads/skills/auto-code-anti-pattern-hunter/SKILL.md"

PY_NESTING_HEADING = "## Structural Pattern Matching & Control Flow Nesting Invariant (`RULE_PYTHON_CYCLOMATIC_AND_NESTING_DISCIPLINE_001`)"
PY_MONKEY_HEADING = "## Standard Library Monkeypatch Signature Parity Invariant (`RULE_PYTHON_MONKEYPATCH_SIGNATURE_PARITY_001`)"
MYPY_HEADING = "## Scoped Mypy Import Checking Invariant (`RULE_PYTHON_MYPY_IGNORE_SCOPE_001`)"
RS_ORDERED_HEADING = "## Rust Ordered Key Collection Invariant (`RULE_RUST_ORDERED_KEY_DERIVE_001`)"
RS_COLLISION_HEADING = "## Rust Crate File Collision Prevention Invariant (`RULE_RUST_CRATE_COLLISION_PREVENTION_001`)"
RS_002_ROW = (
    "| `AP_RS_002` | Domain Enum Missing Ord/PartialOrd | Non-deterministic `HashMap` fallback, broken Merkle trees | "
    "[`HP_RS_002`](../../patterns/helpful/rust/HP_RS_002_deterministic_key_trait_derive.md) "
    "Deterministic Key Trait Derive |"
)
LEAN_LINK = (
    "[**`techne-code-python-lean4-anti-patterns`**](file:///c:/Users/a343o/source/repos/the_symbol_game/"
    "omega_engine_operads/skills/techne-code-python-lean4-anti-patterns/SKILL.md)"
)

CITE_PY_002 = "\n> **Pattern estate:** `AP_PY_002` / `HP_PY_002` (`omega_engine_operads/patterns/anti/python/`).\n\n"
CITE_RS_CARGO = (
    "\n> **Pattern estate:** `AP_RS_001` / `HP_RS_001`, `AP_RS_003` / `HP_RS_003` "
    "(`omega_engine_operads/patterns/anti/rust/`).\n\n"
)
CITE_RS_002 = "\n> **Pattern estate:** `AP_RS_002` / `HP_RS_002` (`omega_engine_operads/patterns/anti/rust/`).\n\n"
MYPY_BLOCK = (
    "## Scoped Mypy Import Checking Invariant (`RULE_PYTHON_MYPY_IGNORE_SCOPE_001`)\n"
    "\n"
    "> **No global `ignore_missing_imports`:**\n"
    ">\n"
    "> 1. Setting `ignore_missing_imports = true` under an unscoped `[tool.mypy]` "
    "silences missing modules across the whole tree.\n"
    "> 2. Scope overrides to the modules that need them. "
    "See `AP_PY_001` / `HP_PY_001` in `omega_engine_operads/patterns/anti/python/`.\n"
    "\n"
)
RS_003_ROW = (
    "\n| `AP_RS_003` | Incremental Cache Disk Exhaustion | Incremental `target/debug/incremental` fills the disk | "
    "[`HP_RS_003`](../../patterns/helpful/rust/HP_RS_003_incremental_cache_pruning.md) Incremental Cache Pruning |"
)
LEAN_REPLACEMENT = "[**`techne-code-lean4-anti-patterns`**](../techne-code-lean4-anti-patterns/SKILL.md)"

# Filled from the pre-edit tree by the same ``measure`` function the digest uses.
# Keys are repair ids. Values are (pre_fingerprint, post_fingerprint).
CHECKED_FINGERPRINTS: dict[str, tuple[str, str]] = {
    "cite-py-002": (
        "cda2cacd493d29d8e0cb49036a65c3b60ab9d17bcd3134cf2735e7cb45711254",
        "750cd69051061b8f260936404822a0478d2dc7d4c011c5652a2e2639df2d7801",
    ),
    "insert-py-001": (
        "fade46c503131953e8c22320711d84cf670e2861ffdb0b5ddaab689f7605e3a5",
        "2fea96eacf3545fbed2e9547924f4831618eb076e7bf6f46203a26d99297e1be",
    ),
    "cite-rs-cargo": (
        "c70f6810f0d272c4bed63cb342eabbf8d74d842f25aaed20bcfcc1c28c77ba16",
        "1776f121a35a6aa9b05025d478dfd431437ece35e0c159c531427518e1119655",
    ),
    "cite-rs-002": (
        "e1db677def082eba3287ace2560e26267747abc573bca2fcda039135503e1131",
        "b683024a25fc5b00b20ffffcf2400bc128db6ca34f9db858e3c67f8a37a4294e",
    ),
    "skill-row-rs-003": (
        "6d2a5a14e84bfdb9a31979c8aedbebdf3a090ef5c40b7beeb45212db7d6b0520",
        "c5401f17b7a048e45d6f28ae731aca65b4347af9b8bcb0dab2d9f1f89767a571",
    ),
    "hunter-lean-link": (
        "31db00e3a41c2cbdc271fe7a11e817f4aedbfbc3df7a6e2587157c41e91ef0d6",
        "629b8838acde5d4a29a3f6bcca3eb32f67d12b7177603b14b058b8e0c5c683d5",
    ),
}
CHECKED_PATTERN_SHA256: dict[str, str] = {
    "AP_PY_001": "2a30b3dd22bba3cf7eade9b6740a2cb7b175e31733897e27718b5d56025e14bd",
    "HP_PY_001": "b43ddc11d7506ec98b52af3a7948de9245c9cef0461e87936dd097e1a01965d3",
    "AP_PY_002": "2b33fff3bf5eb62617aeebf3e3fbc62c1bd9cd897c7daa99a4dd7b5594098716",
    "HP_PY_002": "1704835026464f520716df6c5cbea6720d72fa0c1a1b746ea3a9d39be0d3f2d3",
    "AP_RS_001": "b65b7d250cb71dd74b8af1406d046b66356dc6cf3e30fc514fa23ec0f832c0b5",
    "HP_RS_001": "3033e0a4eaba386237a39f1cb4914213cd0a4d429876a70cf9b545064eabdeb1",
    "AP_RS_002": "bf76ca36e3d3da09320f56f7c2892ddfbb8b3f6bef9fc1c6d08d00ae3c8ab21c",
    "HP_RS_002": "f3f8db1abec1d47d320d9f84694db3852d1e271cc7fcfa9dcdcae0aeec2dff93",
    "AP_RS_003": "58db005f3e7a79895d43108f1652a9a7edb6dec90bc9670827dc10f92ab3d2ef",
    "HP_RS_003": "4c3d86a2e1fe276d710e013afb8b4f70c5a65cf41cee8cac775e61bff71e5894",
    "AP_LN_001": "77cca5762e32ef100016f0812a29b0e4d8246a0fe408a99bdc1d76e1fc77aa6b",
    "HP_LN_001": "c399141bb7b6624c7d87ad229fb99bc1db5d08d43cb03f8d3d29b327d8431ca4",
    "AP_LN_002": "f4c78dbf23fbb1ba57c1e620934a46220249db849f17c110019896f1cae58363",
    "HP_LN_002": "545e2f7b5b0902a44b238185bbcaa5ca01b472e0e1d1dc46c5431972ba3878ac",
}


def _spec(
    repair_id: str,
    edit_kind: str,
    target_path: str,
    target_section: str,
    pattern_ids: tuple[str, ...],
    locator: EditLocator,
    replacement_text: str,
) -> RepairSpec:
    pre, post = CHECKED_FINGERPRINTS[repair_id]
    return RepairSpec(
        repair_id=repair_id,
        edit_kind=edit_kind,
        target_path=target_path,
        target_section=target_section,
        pattern_ids=pattern_ids,
        locator=locator,
        replacement_text=replacement_text,
        pre_fingerprint=pre,
        post_fingerprint=post,
        pattern_sha256=tuple((pattern_id, CHECKED_PATTERN_SHA256[pattern_id]) for pattern_id in pattern_ids),
    )


def live_repairs() -> tuple[RepairSpec, ...]:
    """The only repairs the applier will write."""
    if not CHECKED_FINGERPRINTS:
        return ()
    return (
        _spec(
            "cite-py-002",
            "cite_pattern",
            PY_CONTRACTS_RULE,
            "RULE_PYTHON_HASH_EQUALITY_NORMALIZATION_001",
            ("AP_PY_002", "HP_PY_002"),
            EditLocator("insert_before", anchor_text=PY_MONKEY_HEADING),
            CITE_PY_002,
        ),
        _spec(
            "insert-py-001",
            "insert_invariant",
            PY_RULE,
            "RULE_PYTHON_MYPY_IGNORE_SCOPE_001",
            ("AP_PY_001", "HP_PY_001"),
            EditLocator("insert_before", anchor_text=PY_NESTING_HEADING, new_heading=MYPY_HEADING),
            MYPY_BLOCK,
        ),
        _spec(
            "cite-rs-cargo",
            "cite_pattern",
            RS_RULE,
            "RULE_CARGO_WORKSPACE_ROOT_001",
            ("AP_RS_001", "HP_RS_001", "AP_RS_003", "HP_RS_003"),
            EditLocator("insert_before", anchor_text=RS_ORDERED_HEADING),
            CITE_RS_CARGO,
        ),
        _spec(
            "cite-rs-002",
            "cite_pattern",
            RS_RULE,
            "RULE_RUST_ORDERED_KEY_DERIVE_001",
            ("AP_RS_002", "HP_RS_002"),
            EditLocator("insert_before", anchor_text=RS_COLLISION_HEADING),
            CITE_RS_002,
        ),
        _spec(
            "skill-row-rs-003",
            "skill_table_row",
            RS_SKILL,
            "pattern_table",
            ("AP_RS_003", "HP_RS_003"),
            EditLocator("insert_after", anchor_text=RS_002_ROW),
            RS_003_ROW,
        ),
        _spec(
            "hunter-lean-link",
            "replace_link",
            HUNTER,
            "Connected Specialist Skills",
            ("AP_LN_001", "HP_LN_001", "AP_LN_002", "HP_LN_002"),
            EditLocator("replace", old_text=LEAN_LINK),
            LEAN_REPLACEMENT,
        ),
    )

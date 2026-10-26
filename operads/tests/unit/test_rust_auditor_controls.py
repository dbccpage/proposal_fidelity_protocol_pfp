"""Harmful and benign controls for the Rust auditors' lexical boundaries."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
ANTI = REPO / ".agents/skills/techne-code-rust-anti-patterns/scripts/rust_anti_pattern_auditor.py"
REVIEW = REPO / ".agents/skills/techne-code-rust-code-reviewer/scripts/rust_crate_reviewer.py"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _run(script: Path, root: Path, report: Path, *extra: str, check: bool = True):
    root_option = "--path" if script == ANTI else "--base-dir"
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            root_option,
            str(root),
            *(["--check"] if check else []),
            "--report-out",
            str(report),
            *extra,
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO,
        timeout=30,
    )
    payload = json.loads(report.read_text(encoding="utf-8")) if report.exists() else None
    return completed, payload


@pytest.mark.parametrize("script", [ANTI, REVIEW], ids=["anti-pattern", "reviewer"])
def test_exact_order_trait_harmful_and_benign_controls(tmp_path: Path, script: Path) -> None:
    source = tmp_path / "lib.rs"
    _write(source, "#[derive(Debug, PartialEq, Eq, PartialOrd)]\npub enum Key { First, Second }\n")
    failed, payload = _run(script, tmp_path, tmp_path / "bad.json")
    assert failed.returncode == 1, failed.stderr
    rows = payload["findings"] if script == ANTI else payload["<non-crate>"]["enums_missing_ord"]
    assert len(rows) == 1
    assert rows[0]["line"] == 2

    _write(
        source,
        "#[derive(\n Debug, PartialEq, Eq,\n PartialOrd, Ord,\n)]\npub enum Key { First, Second }\n",
    )
    passed, payload = _run(script, tmp_path, tmp_path / "good.json")
    assert passed.returncode == 0, passed.stderr
    rows = payload["findings"] if script == ANTI else payload["<non-crate>"]["enums_missing_ord"]
    assert rows == []


@pytest.mark.parametrize("script", [ANTI, REVIEW], ids=["anti-pattern", "reviewer"])
def test_payload_candidates_do_not_claim_confirmed_ordering_defects(
    tmp_path: Path, script: Path
) -> None:
    _write(
        tmp_path / "lib.rs",
        "#[derive(Debug, PartialEq)]\npub enum Reading { Value(f64), Missing }\n"
        "#[cfg(test)] mod checks {\n"
        "#[derive(Debug, PartialEq)] pub enum Fixture { A }\n}\n",
    )
    completed, payload = _run(script, tmp_path, tmp_path / "report.json")
    # Retain review leads rather than silently suppressing unresolved traits.
    assert completed.returncode == 1, completed.stderr
    rows = payload["findings"] if script == ANTI else payload["<non-crate>"]["enums_missing_ord"]
    assert len(rows) == 2
    assert [row["enum"] for row in rows] == ["Reading", "Fixture"]
    for row in rows:
        assert row["confirmation"] == "unverified"
        assert row["trait_resolution"] == "derive_only"
        assert row["severity"] == "REVIEW"
        assert row["has_eq"] is False
        assert row["has_partial_eq"] is True
    assert [row["is_test"] for row in rows] == [False, True]


@pytest.mark.parametrize("script", [ANTI, REVIEW], ids=["anti-pattern", "reviewer"])
def test_checkout_ancestor_named_tests_does_not_reclassify_production(
    tmp_path: Path, script: Path
) -> None:
    root = tmp_path / "tests" / "checkout"
    _write(root / "lib.rs", "#[derive(Debug)]\npub enum Production { A }\n")
    completed, payload = _run(script, root, tmp_path / "report.json")
    assert completed.returncode == 1
    rows = payload["findings"] if script == ANTI else payload["<non-crate>"]["enums_missing_ord"]
    assert rows[0]["is_test"] is False


MASKED_FIXTURE = """/* outer
  /* #[derive(Debug)] pub enum Nested { A } unsafe { panic!("bad") } */
  #[derive(Debug)] pub enum Comment { A } HashMap TODO
*/
// #[derive(Debug)] pub enum LineComment { A } unsafe { nope.unwrap(); }
const TEXT: &str = "unsafe { HashMap panic!() x.unwrap() } \\\" quoted";
const RAW: &str = r###" #[derive(Debug)] pub enum Raw { A }
unsafe { HashMap x.unwrap(); panic!("noise"); } /* nested? */ "###;
const BYTES: &[u8] = br##"unsafe { HashSet x.unwrap(); }"##;
const CHAR: char = '{';
const ESCAPED: char = '\\'';
fn borrow<'a>(value: &'a str) -> &'a str { value }
#[derive(Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum Real { A }
"""


@pytest.mark.parametrize("script", [ANTI, REVIEW], ids=["anti-pattern", "reviewer"])
def test_comments_strings_characters_and_lifetimes_are_not_code(
    tmp_path: Path, script: Path
) -> None:
    _write(tmp_path / "lib.rs", MASKED_FIXTURE)
    completed, payload = _run(script, tmp_path, tmp_path / "report.json")
    assert completed.returncode == 0, completed.stderr
    if script == ANTI:
        assert payload["findings"] == []
    else:
        data = payload["<non-crate>"]
        for key in (
            "enums_missing_ord",
            "unsafe_usages",
            "unwraps_in_src",
            "panics_in_src",
            "hashmap_usages",
            "todos",
        ):
            assert data[key] == [], key


def test_test_items_end_at_their_own_brace_and_filenames_are_not_test_scope(tmp_path: Path) -> None:
    _write(
        tmp_path / "contest.rs",
        """#[cfg(test)]
mod checks {
    fn nested() { unsafe { } Some(1).unwrap(); }
    mod deeper { fn check() { panic!("test"); } }
}
fn production_after() { unsafe { } Some(1).unwrap(); panic!("production"); }
#[test]
fn standalone() { Some(2).unwrap(); panic!("test"); }
fn production_last() { Some(3).expect("production"); }
""",
    )
    completed, payload = _run(REVIEW, tmp_path, tmp_path / "report.json")
    assert completed.returncode == 0, completed.stderr
    data = payload["<non-crate>"]
    assert data["test_files"] == 0
    assert [row["line"] for row in data["unwraps_in_src"]] == [6, 9]
    assert [row["line"] for row in data["panics_in_src"]] == [6]
    assert [(row["line"], row["is_test"]) for row in data["unsafe_usages"]] == [
        (3, True),
        (6, False),
    ]


def test_same_line_test_and_production_have_separate_offsets(tmp_path: Path) -> None:
    _write(
        tmp_path / "lib.rs",
        "#[test] fn check() { None::<()>.unwrap(); unsafe {} } fn live() { None::<()>.unwrap(); unsafe {} }\n",
    )
    completed, payload = _run(REVIEW, tmp_path, tmp_path / "report.json")
    assert completed.returncode == 0
    data = payload["<non-crate>"]
    assert len(data["unwraps_in_src"]) == 1
    assert [row["is_test"] for row in data["unsafe_usages"]] == [True, False]


def test_default_full_tree_coverage_includes_eighteen_noncrate_files(tmp_path: Path) -> None:
    for crate in ("z_crate", "a_crate"):
        _write(tmp_path / crate / "Cargo.toml", "[package]\nname='sample'\nversion='0.1.0'\n")
        _write(tmp_path / crate / "src/lib.rs", "pub fn library() {}\n")
    for index in range(17):
        _write(tmp_path / "loose" / f"case_{index:02}.rs", "pub fn helper() {}\n")
    _write(tmp_path / "build_contracts.rs", "pub fn build() {}\n")
    _write(tmp_path / "a_crate/target/cached.rs", "pub enum Cached { A }\n")
    _write(tmp_path / "a_crate/tests/actual.rs", "fn check() { None::<()>.unwrap(); }\n")
    completed, payload = _run(REVIEW, tmp_path, tmp_path / "report.json")
    assert completed.returncode == 1  # local target is independently refused
    assert list(payload) == ["a_crate", "z_crate", "<non-crate>"]
    assert sum(data["total_rs_files"] for data in payload.values()) == 21
    assert payload["<non-crate>"]["total_rs_files"] == 18
    assert payload["a_crate"]["test_files"] == 1
    assert payload["a_crate"]["unwraps_in_src"] == []
    assert payload["<non-crate>"]["files"] == sorted(payload["<non-crate>"]["files"])
    again, repeated = _run(REVIEW, tmp_path, tmp_path / "repeat.json")
    assert again.returncode == 1
    assert repeated == payload


def test_shared_workspace_target_is_not_a_crate_local_duplication(tmp_path: Path) -> None:
    _write(tmp_path / "loose.rs", "pub fn helper() {}\n")
    _write(tmp_path / "crate/Cargo.toml", "[package]\nname='sample'\nversion='0.1.0'\n")
    _write(tmp_path / "crate/src/lib.rs", "pub fn library() {}\n")
    (tmp_path / "target").mkdir()
    shared, payload = _run(REVIEW, tmp_path, tmp_path / "shared.json")
    assert shared.returncode == 0, shared.stderr
    assert payload["<non-crate>"]["has_local_target"] is False
    assert payload["crate"]["has_local_target"] is False
    assert sum(data["total_rs_files"] for data in payload.values()) == 2

    (tmp_path / "crate/target").mkdir()
    duplicated, payload = _run(REVIEW, tmp_path, tmp_path / "duplicated.json")
    assert duplicated.returncode == 1
    assert payload["crate"]["has_local_target"] is True
    assert payload["<non-crate>"]["has_local_target"] is False


@pytest.mark.parametrize("script", [ANTI, REVIEW], ids=["anti-pattern", "reviewer"])
def test_invalid_explicit_root_does_not_fallback_to_live_repository(
    tmp_path: Path, script: Path
) -> None:
    completed, _ = _run(script, tmp_path / "missing", tmp_path / "report.json")
    assert completed.returncode == 2
    assert "missing" in completed.stderr
    assert "Rust" in completed.stderr


def test_invalid_explicit_crate_is_an_error(tmp_path: Path) -> None:
    for crate in ("missing", "..", "../omega_solvers"):
        completed, _ = _run(REVIEW, tmp_path, tmp_path / "report.json", "--crate", crate)
        assert completed.returncode == 2


@pytest.mark.parametrize("script", [ANTI, REVIEW], ids=["anti-pattern", "reviewer"])
def test_invalid_utf8_is_reported_as_error_even_without_check(tmp_path: Path, script: Path) -> None:
    (tmp_path / "broken.rs").write_bytes(b"fn valid() {}\n\xff")
    completed, payload = _run(script, tmp_path, tmp_path / "report.json", check=False)
    assert completed.returncode == 2
    errors = payload["errors"] if script == ANTI else payload["<non-crate>"]["errors"]
    assert errors
    assert "decode" in errors[0]
    assert "broken.rs" in errors[0]


def test_unreadable_source_cannot_be_silent_green(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write(tmp_path / "crate/src/lib.rs", "fn fine() {}\n")
    spec = importlib.util.spec_from_file_location("rust_auditor_control_reviewer", REVIEW)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original_read = Path.read_text

    def denied(path: Path, *args, **kwargs):
        if path.suffix == ".rs":
            raise PermissionError("planted unreadable source")
        return original_read(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", denied)
    data = module.audit_crate("crate", tmp_path)
    assert data["total_rs_files"] == 1
    assert "planted unreadable source" in data["errors"][0]

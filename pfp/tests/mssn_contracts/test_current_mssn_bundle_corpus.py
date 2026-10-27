"""Real-file corpus admission controls; no providers, PFP stages or host replay."""

import json
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

import pytest

from pfp.infrastructure import pilot_runner as owner

MANIFEST_REL = "adversary/tests/pilots/matrix/mssn_expected/manifest.v1.json"


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


@pytest.fixture
def current_bundle_tree(tmp_path):
    """Copy only the declared real source/fixture bytes; never repair stale pins."""
    repo = next(parent for parent in Path(__file__).resolve().parents if (parent / ".git").exists())
    original = repo / MANIFEST_REL
    manifest = json.loads(original.read_bytes())
    root = tmp_path / "owned_source_root"
    folder = root / Path(MANIFEST_REL).parent
    folder.mkdir(parents=True)
    for binding in manifest["source_bindings"].values():
        raw = (repo / binding["path"]).read_bytes()
        assert sha256(raw).hexdigest() == binding["sha256"], "Current compilation pin must be reviewed/refreshed before execution"
        target = root / binding["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    for key in ("seed", "expected", "response_schema"):
        binding = manifest["entries"][0][key]
        raw = (original.parent / binding["path"]).read_bytes()
        assert sha256(raw).hexdigest() == binding["sha256"]
        (folder / binding["path"]).write_bytes(raw)
    path = folder / original.name
    write_json(path, manifest)
    return root, path, manifest


def validate(tree):
    root, path, _ = tree
    return owner.validate_current_mssn_bundle_manifest(path, source_root=root)


def reseal_fixture(tree, key, raw):
    _, path, manifest = tree
    binding = manifest["entries"][0][key]
    (path.parent / binding["path"]).write_bytes(raw)
    binding["sha256"] = sha256(raw).hexdigest()
    write_json(path, manifest)


def test_one_current_bundle_is_partial_coverage_and_required_aggregate_fails(current_bundle_tree):
    result = validate(current_bundle_tree)
    assert result["availability"] == "AVAILABLE"
    assert result["validated_count"] == 1
    assert result["required_count"] == 50
    assert result["missing_ids"] == [f"DEMO_{number:02d}" for number in range(2, 51)]
    assert result["status"] == "FAIL"
    assert result["errors"] == []
    assert result["finite_fixture_execution_count"] == 0
    assert result["pfp_stage_execution_count"] == 0
    assert result["provider_execution_count"] == 0
    request = owner.build_seed_requests("DEMO_01")
    expected_user = request["requests"][0]["messages"][1]["content"].encode("utf-8")
    assert result["record_results"][0]["user_sha256"] == sha256(expected_user).hexdigest()


def test_every_bound_file_is_read_once_for_validation_and_digest(current_bundle_tree, monkeypatch):
    original = owner._mssn_read_snapshot
    reads = []

    def observed(path):
        reads.append(path)
        return original(path)

    monkeypatch.setattr(owner, "_mssn_read_snapshot", observed)
    assert validate(current_bundle_tree)["validated_count"] == 1
    assert len(reads) == len(set(reads))


def test_missing_manifest_translates_to_unavailable_zero_coverage(current_bundle_tree):
    _, path, _ = current_bundle_tree
    path.unlink()
    result = validate(current_bundle_tree)
    assert result["availability"] == "UNAVAILABLE"
    assert result["validated_count"] == 0
    assert result["status"] == "FAIL"


@pytest.mark.parametrize("raw", (b"{", b'{}', b'{"schema":1,"schema":2}'), ids=("parse", "shape", "duplicate_json_key"))
def test_bad_manifest_cannot_mint_coverage(current_bundle_tree, raw):
    _, path, _ = current_bundle_tree
    path.write_bytes(raw)
    result = validate(current_bundle_tree)
    assert result["status"] == "FAIL"
    assert result["validated_count"] == 0
    assert result["availability"] == "UNAVAILABLE"


@pytest.mark.parametrize("identity", ("DEMO_51", "DEMO-N01", False, []), ids=("extra", "other_corpus", "bool", "list"))
def test_unknown_or_wrong_type_ids_fail_before_positive_record_work(current_bundle_tree, identity):
    _, path, manifest = current_bundle_tree
    manifest["entries"][0]["demo_id"] = identity
    write_json(path, manifest)
    result = validate(current_bundle_tree)
    assert result["validated_count"] == 0
    assert result["status"] == "FAIL"


def test_duplicate_ids_never_count_twice(current_bundle_tree):
    _, path, manifest = current_bundle_tree
    manifest["entries"].append(deepcopy(manifest["entries"][0]))
    write_json(path, manifest)
    assert validate(current_bundle_tree)["validated_count"] == 0


def test_empty_manifest_remains_all_fifty_missing(current_bundle_tree):
    _, path, manifest = current_bundle_tree
    manifest["entries"] = []
    write_json(path, manifest)
    result = validate(current_bundle_tree)
    assert result["validated_count"] == 0
    assert len(result["missing_ids"]) == 50
    assert result["status"] == "FAIL"


def test_absent_expected_fixture_is_not_a_validated_bundle(current_bundle_tree):
    _, path, manifest = current_bundle_tree
    (path.parent / manifest["entries"][0]["expected"]["path"]).unlink()
    result = validate(current_bundle_tree)
    assert result["validated_count"] == 0
    assert result["errors"]


@pytest.mark.parametrize("name", ("../outside.json", "nested/file.json", "owned\\file.json", "C:file.json", "file.json.", False), ids=("parent", "slash", "backslash", "drive", "trailing_dot", "bool"))
def test_unsafe_or_wrong_type_fixture_names_are_refused(current_bundle_tree, name):
    _, path, manifest = current_bundle_tree
    manifest["entries"][0]["expected"]["path"] = name
    write_json(path, manifest)
    assert validate(current_bundle_tree)["validated_count"] == 0


def test_raw_fixture_mutation_with_old_digest_is_refused(current_bundle_tree):
    _, path, manifest = current_bundle_tree
    binding = manifest["entries"][0]["expected"]
    (path.parent / binding["path"]).write_bytes(b"{}\n")
    result = validate(current_bundle_tree)
    assert result["validated_count"] == 0
    assert result["errors"][0]["code"] == "FIXTURE_RAW_DIGEST_MISMATCH"


def test_seed_byte_mutation_is_refused_even_with_new_fixture_digest(current_bundle_tree):
    _, path, manifest = current_bundle_tree
    raw = (path.parent / manifest["entries"][0]["seed"]["path"]).read_bytes()
    reseal_fixture(current_bundle_tree, "seed", raw + b" ")
    result = validate(current_bundle_tree)
    assert result["validated_count"] == 0
    assert result["errors"][0]["code"] == "SEED_BYTES_MISMATCH"


@pytest.mark.parametrize("role", ("template", "assembler", "schema_owner", "loader"))
def test_changed_compilation_source_or_template_cannot_use_old_pin(current_bundle_tree, role):
    root, _, manifest = current_bundle_tree
    target = root / manifest["source_bindings"][role]["path"]
    target.write_bytes(target.read_bytes() + b"\n")
    result = validate(current_bundle_tree)
    assert result["validated_count"] == 0
    assert result["availability"] == "UNAVAILABLE"


@pytest.mark.parametrize("key", ("authority_effect", "response_contract"))
def test_wrong_top_level_contract_is_unavailable(current_bundle_tree, key):
    _, path, manifest = current_bundle_tree
    manifest[key] = "wrong"
    write_json(path, manifest)
    assert validate(current_bundle_tree)["availability"] == "UNAVAILABLE"


@pytest.mark.parametrize("raw", (b"{", b"system_prompt: 1\nuser_prompt: '[USER PROMPT]'\n", b"system_prompt: S\nuser_prompt: no_slot\n"), ids=("yaml", "field_type", "slot"))
def test_even_resealed_invalid_template_is_a_typed_unavailable_input(current_bundle_tree, raw):
    root, path, manifest = current_bundle_tree
    binding = manifest["source_bindings"]["template"]
    (root / binding["path"]).write_bytes(raw)
    binding["sha256"] = sha256(raw).hexdigest()
    write_json(path, manifest)
    result = validate(current_bundle_tree)
    assert result["availability"] == "UNAVAILABLE"
    assert result["validated_count"] == 0


def test_resealed_malformed_catalog_is_translated_to_unavailable(current_bundle_tree):
    root, path, manifest = current_bundle_tree
    binding = manifest["source_bindings"]["catalog"]
    raw = b"seeds: [\n"
    (root / binding["path"]).write_bytes(raw)
    binding["sha256"] = sha256(raw).hexdigest()
    write_json(path, manifest)
    result = validate(current_bundle_tree)
    assert result["availability"] == "UNAVAILABLE"
    assert result["validated_count"] == 0


@pytest.mark.parametrize("field", ("root", "seeds", "by_folder", "counts"))
def test_resealed_nonmapping_catalog_is_structured_unavailable(current_bundle_tree, field):
    root, path, manifest = current_bundle_tree
    binding = manifest["source_bindings"]["catalog"]
    payload = {"schema": "pfp.seeds.v1", "seeds": {}, "total_seeds": 0, "by_folder": {}, "counts": {}}
    if field == "root":
        payload = []
    else:
        payload[field] = []
    raw = json.dumps(payload).encode("utf-8")
    (root / binding["path"]).write_bytes(raw)
    binding["sha256"] = sha256(raw).hexdigest()
    write_json(path, manifest)
    result = validate(current_bundle_tree)
    assert result["availability"] == "UNAVAILABLE"
    assert result["validated_count"] == 0
    assert result["status"] == "FAIL"
    assert result["errors"] == [{"code": "BUNDLE_INPUT_UNAVAILABLE_OR_INVALID", "error_class": "ValueError"}]


def test_resealed_catalog_with_nonstring_prompt_is_structured_unavailable(current_bundle_tree):
    root, path, manifest = current_bundle_tree
    binding = manifest["source_bindings"]["catalog"]
    raw = b'{"schema":"pfp.seeds.v1","total_seeds":1,"seeds":{"x":{"seed_id":"x","folder":"x","seed_prompt":1,"seed_sha256":"invalid","title":"fixture"}},"by_folder":{"x":"x"},"counts":{"x":1}}'
    (root / binding["path"]).write_bytes(raw)
    binding["sha256"] = sha256(raw).hexdigest()
    write_json(path, manifest)
    result = validate(current_bundle_tree)
    assert result["availability"] == "UNAVAILABLE"
    assert result["validated_count"] == 0
    assert result["status"] == "FAIL"
    assert result["errors"] == [{"code": "BUNDLE_INPUT_UNAVAILABLE_OR_INVALID", "error_class": "ValueError"}]


@pytest.mark.parametrize("invalid_root", (False, 1, []), ids=("bool", "int", "list"))
def test_invalid_source_root_type_is_structured_unavailable(current_bundle_tree, invalid_root):
    _, path, _ = current_bundle_tree
    result = owner.validate_current_mssn_bundle_manifest(path, source_root=invalid_root)
    assert result["availability"] == "UNAVAILABLE"
    assert result["validated_count"] == 0
    assert result["status"] == "FAIL"
    assert result["errors"] == [{"code": "BUNDLE_INPUT_UNAVAILABLE_OR_INVALID", "error_class": "TypeError"}]


def test_resealed_malformed_expected_json_is_not_positive_coverage(current_bundle_tree):
    reseal_fixture(current_bundle_tree, "expected", b'{"raw":1,"raw":2}\n')
    result = validate(current_bundle_tree)
    assert result["validated_count"] == 0
    assert result["errors"]


def test_resealed_malformed_schema_has_explicit_schema_error(current_bundle_tree):
    reseal_fixture(current_bundle_tree, "response_schema", b'{"type":"array","prefixItems":[]}\n')
    result = validate(current_bundle_tree)
    assert result["validated_count"] == 0
    assert result["errors"][0]["code"] == "INVALID_SCHEMA"


def test_resealed_different_valid_schema_is_not_current_contract(current_bundle_tree):
    reseal_fixture(current_bundle_tree, "response_schema", b'{"type":"object"}\n')
    result = validate(current_bundle_tree)
    assert result["validated_count"] == 0
    assert result["errors"][0]["code"] == "CURRENT_CANDIDATE_SCHEMA_MISMATCH"


def test_resealed_wrong_expected_shape_has_explicit_expected_error(current_bundle_tree):
    reseal_fixture(current_bundle_tree, "expected", b'{}\n')
    result = validate(current_bundle_tree)
    assert result["validated_count"] == 0
    assert result["errors"][0]["code"] == "INVALID_EXPECTED"


def test_final_leaf_symlink_is_refused_if_os_allows_fixture(current_bundle_tree, tmp_path):
    _, path, manifest = current_bundle_tree
    target = path.parent / manifest["entries"][0]["expected"]["path"]
    outside = tmp_path / "outside.json"
    outside.write_bytes(target.read_bytes())
    target.unlink()
    try:
        target.symlink_to(outside)
    except OSError as error:
        pytest.skip(f"OS refused owned symlink: {type(error).__name__}")
    result = validate(current_bundle_tree)
    assert result["validated_count"] == 0
    assert result["errors"][0]["code"] == "BUNDLE_REGULAR_LEAF_REQUIRED"


def test_corpus_shape_admission_does_not_claim_raw_or_profile_authentication(current_bundle_tree):
    _, path, manifest = current_bundle_tree
    candidate = json.loads((path.parent / manifest["entries"][0]["expected"]["path"]).read_bytes())
    candidate["raw"], candidate["profile"] = "><", "raw_glyphs"
    reseal_fixture(current_bundle_tree, "expected", json.dumps(candidate).encode("utf-8"))
    result = validate(current_bundle_tree)
    assert result["validated_count"] == 1
    assert result["finite_fixture_execution_count"] == 0
    assert result["status"] == "FAIL"

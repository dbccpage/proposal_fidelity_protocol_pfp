"""Historical replay must fail closed on drift, escape and network use."""

import hashlib
import json

import pytest

from omega_engine_pfp.infrastructure.adapters.pfp_frozen_replay import inside, replay_bundle


def bundle_fixture(root, source):
    bundle = root / "evidence"
    name = "replay_probe/__main__.py"
    target = bundle / "frozen_sources" / name
    target.parent.mkdir(parents=True)
    target.write_bytes(source)
    manifest = {
        "schema": "pfp.frozen-runtime-bundle.v1",
        "files": {name: hashlib.sha256(source).hexdigest()},
        "evidence_paths": [],
        "profiles": {"probe": {"module": "replay_probe", "argv": []}},
    }
    (bundle / "frozen_runtime.json").write_text(json.dumps(manifest), encoding="utf-8")
    return bundle, target


def test_snapshot_runtime_blocks_network_before_import(tmp_path):
    source = b"""import json, socket
try:
    socket.create_connection(("example.invalid", 443))
except RuntimeError as exc:
    print(json.dumps({"network": str(exc)}))
"""
    bundle, _ = bundle_fixture(tmp_path, source)
    assert replay_bundle(tmp_path, bundle, "probe") == {
        "network": "OFFLINE_REPLAY_NETWORK_FORBIDDEN"
    }
    assert not list((tmp_path / "scratch/pfp-frozen-replay").iterdir())


def test_snapshot_byte_tamper_refuses_before_execution(tmp_path):
    bundle, target = bundle_fixture(tmp_path, b'print("{}")\n')
    target.write_bytes(target.read_bytes() + b" ")
    with pytest.raises(ValueError, match="FROZEN_SOURCE_DIGEST_MISMATCH"):
        replay_bundle(tmp_path, bundle, "probe")


def test_moved_evidence_is_reconstructed_at_its_original_snapshot_path(tmp_path):
    source = b'''import json
from pathlib import Path
print(json.dumps({"retained": Path("omega_engine_education/pilots/evidence/probe/raw.bin").read_bytes().hex()}))
'''
    bundle, _ = bundle_fixture(tmp_path, source)
    current = tmp_path / "omega_engine_woland/tests/pilots/evidence/probe"
    current.mkdir(parents=True)
    raw = b"original retained provider bytes\x00\xff"
    (current / "raw.bin").write_bytes(raw)
    manifest_path = bundle / "frozen_runtime.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["evidence_paths"] = ["omega_engine_education/pilots/evidence/probe"]
    manifest_bytes = json.dumps(manifest).encode()
    manifest_path.write_bytes(manifest_bytes)
    assert replay_bundle(tmp_path, bundle, "probe") == {"retained": raw.hex()}
    assert manifest_path.read_bytes() == manifest_bytes
    assert (current / "raw.bin").read_bytes() == raw
    assert not (tmp_path / "omega_engine_education").exists()
    assert not list((tmp_path / "scratch/pfp-frozen-replay").iterdir())


@pytest.mark.parametrize(
    "name", ["../escape.py", ".git/config", ".GIT/config", "nested/../../escape.py"]
)
def test_snapshot_paths_cannot_escape_or_write_git(tmp_path, name):
    with pytest.raises(ValueError, match="FROZEN_REPLAY_PATH_ESCAPE"):
        inside(tmp_path, name)


def test_snapshot_blocks_udp_before_import(tmp_path):
    source = b"""import json, socket
try:
    socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(b"probe", ("127.0.0.1", 9))
except RuntimeError as exc:
    print(json.dumps({"network": str(exc)}))
"""
    bundle, _ = bundle_fixture(tmp_path, source)
    assert replay_bundle(tmp_path, bundle, "probe") == {
        "network": "OFFLINE_REPLAY_NETWORK_FORBIDDEN"
    }


def test_evidence_cannot_replace_verified_executable(tmp_path):
    bundle, _ = bundle_fixture(tmp_path, b'print("{}")\n')
    evidence = tmp_path / "replay_probe"
    evidence.mkdir()
    (evidence / "__main__.py").write_text('raise RuntimeError("unverified executable")\n')
    path = bundle / "frozen_runtime.json"
    manifest = json.loads(path.read_bytes())
    manifest["evidence_paths"] = ["replay_probe"]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    assert replay_bundle(tmp_path, bundle, "probe") == {}


def test_evidence_cannot_inject_unpinned_package_initializer(tmp_path):
    bundle, _ = bundle_fixture(tmp_path, b'print("{}")\n')
    evidence = tmp_path / "replay_probe"
    evidence.mkdir()
    (evidence / "__init__.py").write_text('raise RuntimeError("unverified initializer")\n')
    path = bundle / "frozen_runtime.json"
    manifest = json.loads(path.read_bytes())
    manifest["evidence_paths"] = ["replay_probe"]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    assert replay_bundle(tmp_path, bundle, "probe") == {}

"""Read retired campaign metadata from Git; keep existing capsule bytes untouched."""
from __future__ import annotations

import json
import subprocess

import yaml

from .cases import PILOTS
from .._paths import repository_root

CAMPAIGN = "dossier_replay_20261011"
ROOT = repository_root(PILOTS)
HISTORICAL_REVISION = "06ff2c8183f087eacbede53321693ed6052c763b"


def historical_bytes(relative):
    """Read retired campaign metadata from its pinned Git commit, without restoring it."""
    allowed = {
        f"matrix/{CAMPAIGN}.yaml", f"matrix/{CAMPAIGN}_free.yaml",
        f"matrix/{CAMPAIGN}_guidance.yaml",
        f"matrix/migration_custody_20261011/{CAMPAIGN}_sources.json",
        "matrix/replay_custody_20261011/free_followup/authorization.yaml",
        "matrix/replay_custody_20261011/free_followup/manifest.json",
    }
    if relative not in allowed:
        raise ValueError("UNREGISTERED_HISTORICAL_CAMPAIGN_PATH")
    result = subprocess.run(
        ["git", "show", f"{HISTORICAL_REVISION}:omega_engine_education/pilots/{relative}"],
        cwd=ROOT, capture_output=True, check=False,
    )
    if result.returncode:
        raise ValueError("HISTORICAL_CAMPAIGN_BYTES_UNAVAILABLE")
    return result.stdout


def historical_plan(suffix=""):
    return yaml.safe_load(historical_bytes(f"matrix/{CAMPAIGN}{suffix}.yaml"))


def write_once(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = value if isinstance(value, bytes) else yaml.safe_dump(value, sort_keys=False, allow_unicode=True).encode("utf-8")
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"IMMUTABLE_ARTIFACT_CONFLICT: {path}")
        return
    with path.open("xb") as stream:
        stream.write(data)


def prepare():
    # This campaign is retired. Replaying it must not recreate deleted plans or capsules.
    return historical_plan()


if __name__ == "__main__":
    result = prepare()
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}, indent=2))

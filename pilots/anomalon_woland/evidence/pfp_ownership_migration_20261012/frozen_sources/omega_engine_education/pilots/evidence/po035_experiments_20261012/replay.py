"""Offline replay using the retained tokenizer rather than a user cache."""

import gzip
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from omega_engine_education.pfp.infrastructure.po035 import experiment_models, experiments


def validate_counts(outputs):
    """Reject incomplete evidence even when the underlying replayer skips a run."""
    expected_pilots = set(experiments.BY_ID)
    expected_calls = {"scratchpad": 4, "temperature": 2, "logit": 2}
    if set(outputs) != set(expected_calls):
        raise ValueError("missing or unexpected experiment group")
    for kind, calls in expected_calls.items():
        rows = outputs[kind]
        if len(rows) != len(expected_pilots) or {r["pilot_id"] for r in rows} != expected_pilots:
            raise ValueError(f"incomplete or duplicate pilot set: {kind}")
        if any(r["replayed_calls"] != calls or r["terminal"] != "LOOP_LIMIT" for r in rows):
            raise ValueError(f"incomplete call sequence: {kind}")


def main():
    root = Path(__file__).resolve().parent
    raw = gzip.decompress((root / "tokenizer.json.gz").read_bytes())
    # Verifies the full pinned tokenizer bytes before redirecting file resolution.
    experiment_models.format_only_logit_bias(raw)
    # Use this checkout's writable scratch area, including on sandboxed Windows.
    scratch = experiments.ROOT / "scratch" / "po035-replay"
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="tokenizer-", dir=scratch) as directory:
        tokenizer = Path(directory) / "tokenizer.json"
        tokenizer.write_bytes(raw)
        # Only the filesystem location changes; generation and judges are never mocked.
        with patch.object(experiment_models, "cached_tokenizer_path", return_value=tokenizer):
            outputs = {
                kind: experiments.replay(kind, list(experiments.BY_ID))
                for kind in ("scratchpad", "temperature", "logit")
            }
    validate_counts(outputs)
    print(json.dumps({"new_provider_calls": 0, "replays": outputs}))


if __name__ == "__main__":
    main()

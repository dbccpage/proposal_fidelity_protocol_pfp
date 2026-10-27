"""Source-bound seed preparation; no provider simulations."""

from copy import deepcopy

import pytest
import yaml

from pfp.infrastructure import pilot_runner


def test_all_seeds_keep_exact_prompt_bytes():
    source = yaml.safe_load(pilot_runner.SEED_CATALOG.read_bytes())
    seeds = pilot_runner.load_seed_catalog()
    assert len(seeds.demos) == 74
    for seed in seeds.demos:
        assert seed.seed == source["seeds"][seed.id]["seed_prompt"]
    request = pilot_runner.build_seed_requests("DEMO_01")
    assert seeds.get_by_id("DEMO_01").seed in request["requests"][0]["messages"][1]["content"]
    assert request["provider_calls"] == 0
    assert request["execution_status"] == "PREPARED_ONLY"
    assert "expected_predicates" not in request


def test_mutated_seed_is_refused(tmp_path):
    source = deepcopy(yaml.safe_load(pilot_runner.SEED_CATALOG.read_bytes()))
    source["seeds"]["DEMO_01"]["seed_prompt"] += "changed"
    changed = tmp_path / "seeds.yaml"
    changed.write_text(yaml.safe_dump(source), encoding="utf-8")
    with pytest.raises(ValueError, match="SEED_BINDING_MISMATCH"):
        pilot_runner.load_seed_catalog(changed)

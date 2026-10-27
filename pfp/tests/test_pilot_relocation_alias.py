"""Legacy challenge imports resolve to the canonical relocated package."""

import importlib


def test_legacy_challenge_alias_preserves_module_and_type_identity():
    legacy = importlib.import_module(
        "projects.mssn_sn_symgam.challenges.b_cohomology.swarm.budget_controller"
    )
    canonical = importlib.import_module(
        "pfp.tests.demo_004.b_cohomology.swarm.budget_controller"
    )
    assert legacy is canonical
    assert legacy.BudgetController is canonical.BudgetController


def test_legacy_neural_runner_uses_the_same_hook_module():
    prefix = "pilots.llm_mechanism.c001_attention_distractor_mask"
    hook = importlib.import_module(prefix + ".attention_hook")
    runner = importlib.import_module(prefix + ".empirical_neural_mcnemar_evaluation")
    assert runner.apply_distractor_key_mask is hook.apply_distractor_key_mask
    assert runner.apply_distractor_key_mask.__globals__ is vars(hook)


def test_legacy_demos_alias_preserves_package_identity():
    legacy = importlib.import_module("projects.mssn_sn_symgam.demos")
    canonical = importlib.import_module(
        "adversary.tests.pilots"
    )
    assert legacy is canonical

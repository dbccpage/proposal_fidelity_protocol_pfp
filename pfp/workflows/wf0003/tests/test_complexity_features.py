"""Ex-ante features and explicit unknowns for unscoped research prompts."""

from pfp.workflows.measurement import measure_seed


def task(values):
    return dict(
        seed_prompt="Calculate the sum.", input=dict(values=values), checker="integer_sum_v1"
    )


def test_size_and_arithmetic_work_are_separate_from_surface_length():
    small = measure_seed(task([1, 2, 3]))
    large = measure_seed(task(list(range(64))))
    assert small["surface"]["characters"] == large["surface"]["characters"]
    assert small["task"]["reference_binary_additions"] == 2
    assert large["task"]["reference_binary_additions"] == 63
    assert large["task"]["reference_balanced_addition_depth"] == 6
    assert large["surface"]["model_token_count"] is None
    assert large["scalar_complexity_score"] is None


def test_operand_precision_is_distinct_from_count():
    small = measure_seed(task([1, 2]))
    big = measure_seed(task([10**50, 10**60]))
    assert small["task"]["operand_count"] == big["task"]["operand_count"]
    assert big["task"]["max_operand_bits"] > small["task"]["max_operand_bits"]


def test_fermion_programme_is_unscoped_not_infinite_or_trivially_easy():
    seed = dict(seed_prompt="Solve the Fermion Sign Problem", input={}, checker="schema_only")
    result = measure_seed(
        seed, dict(family="fermion_sign_problem", objective_kind="OPEN_RESEARCH_PROGRAMME")
    )
    assert result["scope"]["needs_scope_contract"] is True
    assert result["task"]["declared_search_states"] is None
    assert result["task"]["operand_count"] is None
    assert result["verification"]["task_correctness_check_available"] is False
    assert result["scalar_complexity_score"] is None

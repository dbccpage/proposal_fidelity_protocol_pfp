from replay import TASK, check, main


def test_valid_witness():
    assert check(TASK, (1, 0), ("equation",)) is True


def test_wrong_witness_refused():
    assert check(TASK, (0, 0), ("equation",)) is False


def test_wrong_task_refused():
    assert check("another-task", (1, 0), ("equation",)) is False


def test_false_prose_claim_refused():
    assert check(TASK, (1, 0), ("equation", "all_solutions_x_one")) is False


def test_unbound_quote_refused():
    assert check(TASK, (1, 0), ("equation", "source_quote")) is False


def test_mandatory_task_claim_retained():
    assert check(TASK, (0, 0), ()) is False


def test_main_execution():
    main()

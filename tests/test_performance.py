from evaluation.performance import evaluate_all_scenarios


def test_all_scenarios_return_results():

    result = evaluate_all_scenarios(steps=10)

    assert result["success"] is True
    assert len(result["results"]) == 4


def test_normal_scenario_completes_deliveries():

    result = evaluate_all_scenarios(steps=10)

    normal = next(
        item for item in result["results"]
        if item["Scenario"] == "Normal"
    )

    assert normal["Completed Deliveries"] == 2
    assert normal["Pending Deliveries"] == 0


def test_breakdown_scenario_reduces_completion():

    result = evaluate_all_scenarios(steps=10)

    breakdown = next(
        item for item in result["results"]
        if item["Scenario"] == "Breakdown"
    )

    assert breakdown["Completed Deliveries"] == 1
    assert breakdown["Pending Deliveries"] == 1
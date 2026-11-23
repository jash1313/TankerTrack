from database import get_latest_schedule_for_simulation
from simulation.model import TankerDistributionModel


def run_latest_simulation(
    steps=5,
    scenario="normal",
    breakdown_tanker_id=None
):

    assignments = get_latest_schedule_for_simulation()

    if not assignments:

        return {
            "success": False,
            "message": "No saved schedule found.",
            "model": None,
            "model_results": None,
            "agent_results": None
        }

    valid_scenarios = [
        "normal",
        "traffic",
        "breakdown",
        "high_demand"
    ]

    if scenario not in valid_scenarios:

        return {
            "success": False,
            "message": "Invalid simulation scenario.",
            "model": None,
            "model_results": None,
            "agent_results": None
        }

    if scenario == "breakdown":

        available_tankers = list({
            item["tanker_id"] for item in assignments
        })

        if breakdown_tanker_id not in available_tankers:

            return {
                "success": False,
                "message": "Select a valid tanker for breakdown.",
                "model": None,
                "model_results": None,
                "agent_results": None
            }

    model = TankerDistributionModel(
        assignments,
        scenario=scenario,
        breakdown_tanker_id=breakdown_tanker_id
    )

    for _ in range(steps):
        model.step()

    return {
        "success": True,
        "message": "Simulation completed successfully.",
        "model": model,
        "model_results": model.datacollector.get_model_vars_dataframe(),
        "agent_results": model.datacollector.get_agent_vars_dataframe()
    }
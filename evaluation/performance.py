import pandas as pd

from database import get_latest_schedule_for_simulation
from simulation.runner import run_latest_simulation


def calculate_performance(result):

    model = result["model"]
    model_df = result["model_results"]
    agent_df = result["agent_results"]

    total_deliveries = model.total_deliveries

    final = model_df.iloc[-1]

    completed = int(final["Completed Deliveries"])
    pending = int(final["Pending Deliveries"])

    completion_rate = (
        completed / total_deliveries * 100
        if total_deliveries else 0
    )

    # Calculate average completion step.
    completion_changes = (
        model_df["Completed Deliveries"].diff().fillna(
            model_df["Completed Deliveries"]
        )
    )

    completion_steps = []

    for step, count in completion_changes.items():
        completion_steps.extend([float(step)] * int(count))

    average_delivery_steps = (
        sum(completion_steps) / len(completion_steps)
        if completion_steps else 0
    )

    # Calculate tanker utilization.
    if not agent_df.empty:
        utilization = (
            (agent_df["Status"] == "Travelling").sum()
            / len(agent_df)
        ) * 100
    else:
        utilization = 0

    # Calculate fairness using Jain's fairness index.
    if not agent_df.empty:

        latest_agents = (
            agent_df
            .reset_index()
            .sort_values("Step")
            .groupby("Tanker ID")
            .tail(1)
        )

        workloads = latest_agents[
            "Completed Deliveries"
        ].astype(float).tolist()

        numerator = sum(workloads) ** 2
        denominator = (
            len(workloads) * sum(x ** 2 for x in workloads)
        )

        fairness = (
            numerator / denominator
            if denominator else 0
        )

    else:
        fairness = 0

    return {
        "Total Deliveries": total_deliveries,
        "Completed Deliveries": completed,
        "Pending Deliveries": pending,
        "Completion Rate (%)": round(completion_rate, 2),
        "Average Completion Step": round(
            average_delivery_steps, 2
        ),
        "Tanker Utilization (%)": round(utilization, 2),
        "Fairness Index": round(fairness, 3)
    }


def evaluate_all_scenarios(steps=10):

    assignments = get_latest_schedule_for_simulation()

    if not assignments:
        return {
            "success": False,
            "message": "No saved schedule available.",
            "results": []
        }

    tanker_ids = sorted({
        item["tanker_id"] for item in assignments
    })

    scenarios = [
        ("Normal", "normal", None),
        ("Traffic", "traffic", None),
        ("Breakdown", "breakdown", tanker_ids[0]),
        ("High Demand", "high_demand", None)
    ]

    results = []

    for name, scenario, breakdown_id in scenarios:

        simulation = run_latest_simulation(
            steps=steps,
            scenario=scenario,
            breakdown_tanker_id=breakdown_id
        )

        if not simulation["success"]:
            continue

        metrics = calculate_performance(simulation)

        metrics["Scenario"] = name

        results.append(metrics)

    return {
        "success": bool(results),
        "message": "Performance evaluation completed.",
        "results": results
    }
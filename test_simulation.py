from simulation.model import TankerDistributionModel


def test_tanker_simulation():

    assignments = [
        {
            "request_id": "R1",
            "tanker_id": "T1",
            "quantity": 3000,
            "location": "Area A"
        },
        {
            "request_id": "R2",
            "tanker_id": "T2",
            "quantity": 3000,
            "location": "Area B"
        }
    ]

    model = TankerDistributionModel(assignments)

    assert len(model.agents) == 2

    # Five steps complete one delivery per tanker.
    for _ in range(5):
        model.step()

    completed = sum(
        agent.completed_deliveries
        for agent in model.agents
    )

    assert completed == 2
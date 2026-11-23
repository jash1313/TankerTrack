import mesa


class TankerAgent(mesa.Agent):

    def __init__(self, model, tanker_id, tasks, travel_steps=5,
                 breakdown=False):

        super().__init__(model)

        self.tanker_id = tanker_id
        self.tasks = tasks

        self.travel_steps = travel_steps
        self.breakdown = breakdown

        self.current_task_index = 0
        self.travel_progress = 0

        self.completed_deliveries = 0
        self.status = "Idle"

        self.current_request = None

        if self.breakdown:
            self.status = "Breakdown"

        elif self.tasks:
            self.current_request = self.tasks[0]
            self.status = "Travelling"

    def step(self):

        if self.breakdown:
            self.status = "Breakdown"
            return

        if self.current_task_index >= len(self.tasks):
            self.status = "Idle"
            return

        self.status = "Travelling"

        self.travel_progress += 100 / self.travel_steps

        if self.travel_progress >= 100:

            self.completed_deliveries += 1

            self.current_task_index += 1
            self.travel_progress = 0

            if self.current_task_index < len(self.tasks):

                self.current_request = self.tasks[
                    self.current_task_index
                ]

                self.status = "Travelling"

            else:
                self.current_request = None
                self.status = "Idle"


class TankerDistributionModel(mesa.Model):

    def __init__(
        self,
        assignments,
        scenario="normal",
        breakdown_tanker_id=None
    ):

        super().__init__()

        self.scenario_name = scenario

        tanker_tasks = {}

        for assignment in assignments:

            tanker_id = assignment["tanker_id"]

            tanker_tasks.setdefault(tanker_id, []).append(assignment)

        # High-demand scenario:
        # Add one synthetic delivery to every tanker.

        if scenario == "high_demand":

            for tanker_id, tasks in tanker_tasks.items():

                if tasks:

                    extra_task = tasks[0].copy()

                    extra_task["request_id"] = (
                        "SIM-HIGH-" + tanker_id
                    )

                    tasks.append(extra_task)

        # Traffic doubles the travel duration.

        travel_steps = 10 if scenario == "traffic" else 5

        for tanker_id, tasks in tanker_tasks.items():

            is_broken = (
                scenario == "breakdown"
                and tanker_id == breakdown_tanker_id
            )

            TankerAgent(
                self,
                tanker_id,
                tasks,
                travel_steps=travel_steps,
                breakdown=is_broken
            )

        self.total_deliveries = sum(
            len(tasks) for tasks in tanker_tasks.values()
        )

        self.datacollector = mesa.DataCollector(

            model_reporters={

                "Completed Deliveries": (
                    lambda model: sum(
                        agent.completed_deliveries
                        for agent in model.agents
                    )
                ),

                "Active Tankers": (
                    lambda model: sum(
                        1 for agent in model.agents
                        if agent.status == "Travelling"
                    )
                ),

                "Broken Tankers": (
                    lambda model: sum(
                        1 for agent in model.agents
                        if agent.status == "Breakdown"
                    )
                ),

                "Pending Deliveries": (
                    lambda model: model.total_deliveries
                    - sum(
                        agent.completed_deliveries
                        for agent in model.agents
                    )
                )
            },

            agent_reporters={

                "Tanker ID": "tanker_id",
                "Status": "status",
                "Completed Deliveries": "completed_deliveries",
                "Travel Progress": "travel_progress"

            }
        )

    def step(self):

        self.agents.do("step")

        self.datacollector.collect(self)
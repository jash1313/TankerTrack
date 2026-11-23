import streamlit as st
import pandas as pd
import plotly.express as px

from database import (
    initialize_database,
    add_tanker,
    add_request,
    get_all_tankers,
    get_all_requests,
    update_request_status,
    save_schedule,
    get_latest_schedule,
    get_schedule_history,
    get_latest_schedule_for_simulation,
)
from csp.scheduler import generate_schedule_from_database
from simulation.runner import run_latest_simulation
from evaluation.compare import run_scheduler_comparison
from evaluation.performance import evaluate_all_scenarios


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="TankerTrack | Municipal Control",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded",
)

initialize_database()


# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0B1120;
        color: #E2E8F0;
    }
    [data-testid="stSidebar"] {
        background-color: #111827;
    }
    h1, h2, h3 {
        color: #F1F5F9;
    }
    .stButton > button {
        background-color: #0284C7;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 8px 20px;
    }
    .stButton > button:hover {
        background-color: #0369A1;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# DATA LOADING
# --------------------------------------------------
def load_tankers():
    return pd.DataFrame(
        get_all_tankers(),
        columns=[
            "Tanker ID",
            "Capacity (L)",
            "Current Water (L)",
            "Location",
            "Available",
            "Status",
        ],
    )


def load_requests():
    return pd.DataFrame(
        get_all_requests(),
        columns=[
            "Request ID",
            "Area",
            "Quantity (L)",
            "Priority",
            "Preferred Time",
            "Location",
            "Status",
            "Created At",
        ],
    )


tankers = load_tankers()
requests = load_requests()


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------
st.sidebar.markdown("# 🚛 TankerTrack")
st.sidebar.caption("Municipal Water Distribution System")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "NAVIGATION",
    ["Overview", "Tanker Management", "Water Requests", "AI Scheduler"],
)

st.sidebar.markdown("---")
st.sidebar.markdown("### SYSTEM STATUS")
st.sidebar.success("Database Connected")
st.sidebar.success("AI Engine: Operational")
st.sidebar.markdown("---")
st.sidebar.caption("TankerTrack | Fundamentals of AI")


# ==================================================
# OVERVIEW PAGE
# ==================================================
if page == "Overview":
    st.title("🚛 Municipal Control Dashboard")
    st.caption("Overview of municipal water distribution")
    st.markdown("---")

    total_tankers = len(tankers)
    available_tankers = (
        int(tankers["Available"].sum()) if not tankers.empty else 0
    )
    total_requests = len(requests)
    pending_requests = (
        int((requests["Status"] == "Pending").sum())
        if not requests.empty else 0
    )
    completed_requests = (
        int((requests["Status"] == "Completed").sum())
        if not requests.empty else 0
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tankers", total_tankers)
    c2.metric("Available Tankers", available_tankers)
    c3.metric("Total Requests", total_requests)
    c4.metric("Pending Requests", pending_requests)

    st.markdown("---")
    left, right = st.columns(2)

    with left:
        st.subheader("🚛 Tanker Availability")
        if not tankers.empty:
            availability = tankers["Status"].value_counts().reset_index()
            availability.columns = ["Status", "Count"]
            fig = px.pie(
                availability,
                names="Status",
                values="Count",
                hole=0.55,
                title="Tanker Status Distribution",
            )
            fig.update_layout(
                paper_bgcolor="#0B1120",
                plot_bgcolor="#0B1120",
                font_color="white",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No tankers registered yet.")

    with right:
        st.subheader("📊 Water Request Priorities")
        if not requests.empty:
            priority_data = requests["Priority"].value_counts().reset_index()
            priority_data.columns = ["Priority", "Count"]
            fig = px.bar(
                priority_data,
                x="Priority",
                y="Count",
                text="Count",
                title="Requests by Priority",
            )
            fig.update_layout(
                paper_bgcolor="#0B1120",
                plot_bgcolor="#0B1120",
                font_color="white",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No water requests registered yet.")

    st.markdown("---")
    st.subheader("📋 Recent Water Requests")
    if not requests.empty:
        st.dataframe(
            requests.tail(5),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No requests available.")


# ==================================================
# TANKER MANAGEMENT PAGE
# ==================================================
elif page == "Tanker Management":
    st.title("🚛 Tanker Management")
    st.caption("Register and monitor municipal water tankers")
    st.markdown("---")

    st.subheader("➕ Register New Tanker")
    with st.form("tanker_form"):
        c1, c2 = st.columns(2)
        with c1:
            tanker_id = st.text_input("Tanker ID", placeholder="Example: T2")
            capacity = st.number_input(
                "Total Capacity (Litres)", min_value=1, value=5000
            )
        with c2:
            current_water = st.number_input(
                "Current Water Level (Litres)", min_value=0, value=5000
            )
            location = st.text_input(
                "Current Location", placeholder="Example: Depot A"
            )
        submitted = st.form_submit_button("Register Tanker")

    if submitted:
        if not tanker_id.strip() or not location.strip():
            st.error("Please enter the tanker ID and location.")
        elif current_water > capacity:
            st.error("Current water cannot exceed tanker capacity.")
        else:
            success = add_tanker(
                tanker_id.strip(),
                int(capacity),
                int(current_water),
                location.strip(),
            )
            if success:
                st.success(f"Tanker {tanker_id} registered successfully!")
                st.rerun()
            else:
                st.error("Tanker ID already exists.")

    st.markdown("---")
    st.subheader("📋 Registered Tankers")
    tankers = load_tankers()
    if not tankers.empty:
        st.dataframe(tankers, use_container_width=True, hide_index=True)
    else:
        st.info("No tankers registered yet.")


# ==================================================
# WATER REQUESTS PAGE
# ==================================================
elif page == "Water Requests":
    st.title("💧 Water Request Management")
    st.caption("Register and monitor municipal water demands")
    st.markdown("---")

    st.subheader("➕ Create Water Request")
    with st.form("request_form"):
        c1, c2 = st.columns(2)
        with c1:
            request_id = st.text_input("Request ID", placeholder="Example: R2")
            area = st.text_input("Area Name", placeholder="Example: Area B")
            quantity = st.number_input(
                "Required Water (Litres)", min_value=1, value=3000
            )
        with c2:
            priority = st.selectbox(
                "Priority", ["Low", "Medium", "High", "Emergency"]
            )
            preferred_time = st.text_input(
                "Preferred Delivery Time", placeholder="Example: 10:00 AM"
            )
            location = st.text_input(
                "Delivery Location", placeholder="Example: Location B"
            )
        submitted = st.form_submit_button("Submit Water Request")

    if submitted:
        if not request_id.strip() or not area.strip() or not location.strip():
            st.error("Please complete all required fields.")
        else:
            success = add_request(
                request_id.strip(),
                area.strip(),
                int(quantity),
                priority,
                preferred_time.strip(),
                location.strip(),
            )
            if success:
                st.success("Water request registered successfully!")
                st.rerun()
            else:
                st.error("Request ID already exists.")

    st.markdown("---")
    st.subheader("📋 All Water Requests")
    requests = load_requests()

    if not requests.empty:
        st.dataframe(requests, use_container_width=True, hide_index=True)
        st.markdown("---")
        st.subheader("Update Request Status")

        with st.form("status_form"):
            selected_request = st.selectbox(
                "Select Request", requests["Request ID"].tolist()
            )
            new_status = st.selectbox(
                "New Status", ["Pending", "Assigned", "In Progress", "Completed"]
            )
            update_button = st.form_submit_button("Update Status")

        if update_button:
            if update_request_status(selected_request, new_status):
                st.success("Request status updated!")
                st.rerun()
            else:
                st.error("Unable to update request.")
    else:
        st.info("No water requests available.")


# ==================================================
# AI SCHEDULER PAGE
# ==================================================
elif page == "AI Scheduler":
    st.title("🧠 AI Scheduling Engine")
    st.caption("Constraint Satisfaction Problem based tanker allocation")
    st.markdown("---")

    tankers = load_tankers()
    requests = load_requests()
    pending_requests = (
        requests[requests["Status"] == "Pending"]
        if not requests.empty else pd.DataFrame()
    )

    st.subheader("CSP Scheduling System")
    st.write(
        "Generate a tanker allocation schedule using AC-3 constraint "
        "propagation and Backtracking Search."
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Registered Tankers", len(tankers))
    c2.metric("Pending Requests", len(pending_requests))
    c3.metric("CSP Algorithm", "AC-3 + Backtracking")

    st.markdown("---")
    st.subheader("📥 Scheduling Input")

    if tankers.empty:
        st.warning("Please register at least one tanker first.")
    elif pending_requests.empty:
        st.info("There are no pending water requests to schedule.")
    else:
        st.write("### Pending Water Requests")
        st.dataframe(
            pending_requests[
                ["Request ID", "Area", "Quantity (L)", "Priority", "Preferred Time"]
            ],
            use_container_width=True,
            hide_index=True,
        )

        if st.button("🚀 Generate AI Schedule", type="primary"):
            with st.spinner("Running CSP scheduling algorithms..."):
                result = generate_schedule_from_database()

            if result["success"]:
                run_id = save_schedule(result["assignments"])
                st.success(
                    f"AI schedule generated and saved successfully! Run ID: {run_id}"
                )
            else:
                st.error(result.get("message", "The CSP scheduler did not find a solution."))

            st.subheader("⚙️ Algorithm Execution Results")
            c1, c2, c3 = st.columns(3)
            c1.metric("Candidate Assignments", result.get("domains_before", 0))
            c2.metric("AC-3 Values Removed", result.get("removed_values", 0))
            c3.metric("Final Assignments", len(result.get("assignments", {})))

            before_count = result.get("domains_before", 0)
            after_count = result.get("domains_after", 0)
            c1, c2 = st.columns(2)
            c1.metric("Domains Before AC-3", before_count)
            c2.metric("Domains After AC-3", after_count)

            assignments = result.get("assignments", {})
            if assignments:
                schedule_data = []
                for request_id, assignment in assignments.items():
                    schedule_data.append(
                        {
                            "Request ID": request_id,
                            "Assigned Tanker": assignment.tanker_id,
                            "Delivery Time": assignment.display_time(),
                            "Water Quantity (L)": assignment.quantity,
                            "Delivery Location": assignment.location,
                        }
                    )
                st.subheader("🚛 Recommended Tanker Allocation")
                st.dataframe(
                    pd.DataFrame(schedule_data),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No assignments were generated.")

            st.caption(
                "AC-3 removes candidate values that have no compatible values "
                "in connected domains."
            )
            st.info(
                "Backtracking Search attempts to find a valid combination "
                "of tanker assignments."
            )

    st.markdown("---")
    st.subheader("🧠 AI Scheduling Workflow")
    st.markdown(
        """
        1. Read tanker and pending request information from SQLite.
        2. Create CSP variables and possible assignment domains.
        3. Apply tanker capacity and water availability constraints.
        4. Run AC-3 constraint propagation.
        5. Apply Backtracking Search with MRV and LCV heuristics.
        6. Generate the recommended tanker allocation schedule.
        """
    )

    st.markdown("---")
    st.subheader("📚 Saved Schedule History")
    history = get_schedule_history()

    if history:
        history_df = pd.DataFrame(
            history,
            columns=["Run ID", "Generated At", "Status", "Total Assignments"],
        )
        st.dataframe(history_df, use_container_width=True, hide_index=True)

        latest_schedule = get_latest_schedule()
        if latest_schedule:
            st.subheader("📋 Latest Saved Schedule")
            latest_df = pd.DataFrame(
                latest_schedule,
                columns=[
                    "Request ID",
                    "Tanker ID",
                    "Delivery Time",
                    "Quantity (L)",
                    "Location",
                ],
            )
            st.dataframe(latest_df, use_container_width=True, hide_index=True)
    else:
        st.info("No saved schedules available.")

    # --------------------------------------------------
    # MESA MULTI-AGENT SIMULATION
    # --------------------------------------------------
    st.markdown("---")
    st.title("🤖 MESA Multi-Agent Simulation")
    st.caption(
        "Simulate municipal tanker deliveries using independent tanker agents."
    )
    st.write("The simulation uses the latest schedule saved in SQLite.")

    scenario_options = {
        "Normal Operation": "normal",
        "Traffic Congestion": "traffic",
        "Tanker Breakdown": "breakdown",
        "High Water Demand": "high_demand",
    }
    selected_scenario = st.selectbox(
        "Select Simulation Scenario", list(scenario_options.keys())
    )
    scenario = scenario_options[selected_scenario]

    simulation_steps = st.number_input(
        "Number of Simulation Steps",
        min_value=1,
        max_value=100,
        value=5,
        key="simulation_steps",
    )

    breakdown_tanker_id = None
    if scenario == "breakdown":
        saved_assignments = get_latest_schedule_for_simulation()
        tanker_options = sorted(
            {item["tanker_id"] for item in saved_assignments}
        )
        if tanker_options:
            breakdown_tanker_id = st.selectbox(
                "Select Tanker to Break Down", tanker_options
            )
        else:
            st.warning("No saved tanker assignments available.")

    if st.button("▶ Run MESA Simulation", type="primary"):
        with st.spinner("Running multi-agent simulation..."):
            st.session_state["simulation_result"] = run_latest_simulation(
                steps=int(simulation_steps),
                scenario=scenario,
                breakdown_tanker_id=breakdown_tanker_id,
            )

    simulation_result = st.session_state.get("simulation_result")
    if simulation_result:
        if simulation_result["success"]:
            st.success("Simulation completed successfully!")
            model_results = simulation_result["model_results"]
            agent_results = simulation_result["agent_results"]

            if not model_results.empty:
                final_result = model_results.iloc[-1]
                c1, c2, c3 = st.columns(3)
                c1.metric(
                    "Completed Deliveries",
                    int(final_result["Completed Deliveries"]),
                )
                c2.metric("Active Tankers", int(final_result["Active Tankers"]))
                c3.metric(
                    "Pending Deliveries",
                    int(final_result["Pending Deliveries"]),
                )

                st.subheader("📈 Delivery Progress")
                progress_chart = px.line(
                    model_results,
                    y="Completed Deliveries",
                    markers=True,
                    title="Completed Deliveries Over Simulation Steps",
                )
                progress_chart.update_layout(
                    paper_bgcolor="#0B1120",
                    plot_bgcolor="#0B1120",
                    font_color="white",
                    xaxis_title="Simulation Step",
                    yaxis_title="Completed Deliveries",
                )
                st.plotly_chart(progress_chart, use_container_width=True)

            st.subheader("🚛 Tanker Agent Performance")
            if not agent_results.empty:
                agent_summary = (
                    agent_results.reset_index()
                    .sort_values(["AgentID", "Step"])
                    .groupby("Tanker ID", as_index=False)
                    .tail(1)
                )
                st.dataframe(
                    agent_summary[
                        [
                            "Tanker ID",
                            "Status",
                            "Completed Deliveries",
                            "Travel Progress",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

            st.subheader("📋 Complete Simulation Data")
            st.dataframe(model_results, use_container_width=True)
        else:
            st.warning(simulation_result.get("message", "Simulation failed."))

    # --------------------------------------------------
    # BASELINE VS CSP COMPARISON
    # --------------------------------------------------
    st.markdown("---")
    st.title("📊 Baseline vs AI-CSP Comparison")
    st.write(
        "Compare Greedy First-Fit scheduling against the CSP-based "
        "AI scheduling algorithm."
    )

    if st.button("📊 Run Scheduler Comparison"):
        with st.spinner("Comparing scheduling algorithms..."):
            st.session_state["comparison_result"] = run_scheduler_comparison()

    comparison = st.session_state.get("comparison_result")
    if comparison:
        baseline = comparison["baseline"]
        csp = comparison["csp"]
        st.success("Comparison completed!")

        comparison_df = pd.DataFrame(
            {
                "Metric": [
                    "Requests Scheduled",
                    "Completion Rate (%)",
                    "Execution Time (seconds)",
                ],
                "Greedy Baseline": [
                    baseline["scheduled"],
                    round(baseline["completion_rate"], 2),
                    round(baseline["execution_time"], 6),
                ],
                "AI-CSP": [
                    csp["scheduled"],
                    round(csp["completion_rate"], 2),
                    round(csp["execution_time"], 6),
                ],
            }
        )
        st.subheader("Algorithm Performance")
        st.dataframe(
            comparison_df, use_container_width=True, hide_index=True
        )

        chart_df = pd.DataFrame(
            {
                "Algorithm": ["Greedy Baseline", "AI-CSP"],
                "Completion Rate": [
                    baseline["completion_rate"],
                    csp["completion_rate"],
                ],
            }
        )
        fig = px.bar(
            chart_df,
            x="Algorithm",
            y="Completion Rate",
            text="Completion Rate",
            title="Request Completion Rate Comparison",
            range_y=[0, 100],
        )
        fig.update_layout(
            paper_bgcolor="#0B1120",
            plot_bgcolor="#0B1120",
            font_color="white",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Execution time is a measurement from this run and can vary "
            "between runs and dataset sizes."
        )

    # --------------------------------------------------
    # PERFORMANCE EVALUATION
    # --------------------------------------------------
    st.markdown("---")
    st.title("📈 System Performance Evaluation")
    st.write(
        "Evaluate tanker distribution performance under four operating scenarios."
    )

    evaluation_steps = st.number_input(
        "Evaluation Simulation Steps",
        min_value=1,
        max_value=100,
        value=10,
        key="evaluation_steps",
    )

    if st.button("Run Complete Performance Evaluation"):
        with st.spinner("Evaluating all scenarios..."):
            st.session_state["evaluation_result"] = evaluate_all_scenarios(
                steps=int(evaluation_steps)
            )

    evaluation = st.session_state.get("evaluation_result")
    if evaluation:
        if evaluation["success"]:
            st.success(evaluation["message"])
            performance_df = pd.DataFrame(evaluation["results"])

            st.subheader("📊 Performance Results")
            st.dataframe(
                performance_df, use_container_width=True, hide_index=True
            )

            st.subheader("Delivery Completion Comparison")
            fig = px.bar(
                performance_df,
                x="Scenario",
                y="Completion Rate (%)",
                color="Scenario",
                text="Completion Rate (%)",
                title="Delivery Completion Rate",
            )
            fig.update_layout(
                paper_bgcolor="#0B1120",
                plot_bgcolor="#0B1120",
                font_color="white",
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("Tanker Utilization")
            utilization_fig = px.bar(
                performance_df,
                x="Scenario",
                y="Tanker Utilization (%)",
                text="Tanker Utilization (%)",
                title="Tanker Utilization by Scenario",
            )
            utilization_fig.update_layout(
                paper_bgcolor="#0B1120",
                plot_bgcolor="#0B1120",
                font_color="white",
            )
            st.plotly_chart(utilization_fig, use_container_width=True)
        else:
            st.warning(evaluation.get("message", "Evaluation failed."))

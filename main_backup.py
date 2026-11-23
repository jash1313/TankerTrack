import streamlit as st
import pandas as pd
import plotly.express as px
from database import get_latest_schedule_for_simulation
from evaluation.compare import run_scheduler_comparison
from evaluation.performance import evaluate_all_scenarios
from database import (
    get_latest_schedule,
    get_schedule_history,
    initialize_database,
    add_tanker,
    add_request,
    get_all_tankers,
    get_all_requests,
    update_request_status,
    get_latest_schedule,
    get_schedule_history
)
from csp.scheduler import generate_schedule_from_database
from database import (
    initialize_database,
    add_tanker,
    add_request,
    get_all_tankers,
    get_all_requests,
    update_request_status,
    save_schedule,
    get_latest_schedule,
    get_schedule_history
)
from simulation.runner import run_latest_simulation

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="TankerTrack | Municipal Control",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

initialize_database()

# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown("""
<style>

.stApp {
    background-color: #0B1120;
    color: #E2E8F0;
}

[data-testid="stSidebar"] {
    background-color: #111827;
}

.metric-card {
    background: linear-gradient(135deg, #172554, #1E293B);
    padding: 22px;
    border-radius: 12px;
    border: 1px solid #334155;
}

.metric-title {
    color: #94A3B8;
    font-size: 14px;
}

.metric-value {
    color: #38BDF8;
    font-size: 30px;
    font-weight: bold;
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
""", unsafe_allow_html=True)


# --------------------------------------------------
# DATA LOADING
# --------------------------------------------------

def load_tankers():
    data = get_all_tankers()

    return pd.DataFrame(
        data,
        columns=[
            "Tanker ID",
            "Capacity (L)",
            "Current Water (L)",
            "Location",
            "Available",
            "Status"
        ]
    )


def load_requests():
    data = get_all_requests()

    return pd.DataFrame(
        data,
        columns=[
            "Request ID",
            "Area",
            "Quantity (L)",
            "Priority",
            "Preferred Time",
            "Location",
            "Status",
            "Created At"
        ]
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
    [
        "Overview",
        "Tanker Management",
        "Water Requests",
        "AI Scheduler"
    ]
)

st.sidebar.markdown("---")

st.sidebar.markdown("### SYSTEM STATUS")
st.sidebar.success("Database Connected")
st.sidebar.success("AI Engine: Operational")

st.sidebar.markdown("---")
st.sidebar.caption("TankerTrack | Fundamentals of AI")


# --------------------------------------------------
# OVERVIEW PAGE
# --------------------------------------------------

if page == "Overview":

    st.title("🚛 Municipal Control Dashboard")
    st.caption("Real-time overview of municipal water distribution")

    st.markdown("---")

    total_tankers = len(tankers)
    available_tankers = (
        int(tankers["Available"].sum())
        if not tankers.empty else 0
    )

    total_requests = len(requests)

    pending_requests = (
        len(requests[requests["Status"] == "Pending"])
        if not requests.empty else 0
    )

    completed_requests = (
        len(requests[requests["Status"] == "Completed"])
        if not requests.empty else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Tankers", total_tankers)

    with col2:
        st.metric("Available Tankers", available_tankers)

    with col3:
        st.metric("Total Requests", total_requests)

    with col4:
        st.metric("Pending Requests", pending_requests)

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
                title="Tanker Status Distribution"
            )

            fig.update_layout(
                paper_bgcolor="#0B1120",
                plot_bgcolor="#0B1120",
                font_color="white"
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
                title="Requests by Priority",
                text="Count"
            )

            fig.update_layout(
                paper_bgcolor="#0B1120",
                plot_bgcolor="#0B1120",
                font_color="white"
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
            hide_index=True
        )
    else:
        st.info("No requests available.")


# --------------------------------------------------
# TANKER MANAGEMENT
# --------------------------------------------------

elif page == "Tanker Management":

    st.title("🚛 Tanker Management")
    st.caption("Register and monitor municipal water tankers")

    st.markdown("---")

    st.subheader("➕ Register New Tanker")

    with st.form("tanker_form"):

        col1, col2 = st.columns(2)

        with col1:
            tanker_id = st.text_input("Tanker ID", placeholder="Example: T2")
            capacity = st.number_input(
                "Total Capacity (Litres)",
                min_value=1,
                value=5000
            )

        with col2:
            current_water = st.number_input(
                "Current Water Level (Litres)",
                min_value=0,
                value=5000
            )

            location = st.text_input(
                "Current Location",
                placeholder="Example: Depot A"
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
                    capacity,
                    current_water,
                    location.strip()
                )

                if success:
                    st.success(f"Tanker {tanker_id} registered successfully!")
                    st.rerun()

                else:
                    st.error("Tanker ID already exists.")

    st.markdown("---")

    st.subheader("📋 Registered Tankers")

    if not tankers.empty:

        st.dataframe(
            tankers,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No tankers registered yet.")


# --------------------------------------------------
# WATER REQUEST MANAGEMENT
# --------------------------------------------------

elif page == "Water Requests":

    st.title("💧 Water Request Management")
    st.caption("Register and monitor municipal water demands")

    st.markdown("---")

    st.subheader("➕ Create Water Request")

    with st.form("request_form"):

        col1, col2 = st.columns(2)

        with col1:

            request_id = st.text_input(
                "Request ID",
                placeholder="Example: R2"
            )

            area = st.text_input(
                "Area Name",
                placeholder="Example: Area B"
            )

            quantity = st.number_input(
                "Required Water (Litres)",
                min_value=1,
                value=3000
            )

        with col2:

            priority = st.selectbox(
                "Priority",
                ["Low", "Medium", "High", "Emergency"]
            )

            preferred_time = st.text_input(
                "Preferred Delivery Time",
                placeholder="Example: 10:00 AM"
            )

            location = st.text_input(
                "Delivery Location",
                placeholder="Example: Location B"
            )

        submitted = st.form_submit_button("Submit Water Request")

        if submitted:

            if not request_id.strip() or not area.strip() or not location.strip():
                st.error("Please complete all required fields.")

            else:

                success = add_request(
                    request_id.strip(),
                    area.strip(),
                    quantity,
                    priority,
                    preferred_time.strip(),
                    location.strip()
                )

                if success:
                    st.success("Water request registered successfully!")
                    st.rerun()

                else:
                    st.error("Request ID already exists.")

    st.markdown("---")

    st.subheader("📋 All Water Requests")

    if not requests.empty:

        st.dataframe(
            requests,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")

        st.subheader("Update Request Status")

        request_ids = requests["Request ID"].tolist()

        with st.form("status_form"):

            selected_request = st.selectbox(
                "Select Request",
                request_ids
            )

            new_status = st.selectbox(
                "New Status",
                ["Pending", "Assigned", "In Progress", "Completed"]
            )

            update_button = st.form_submit_button("Update Status")

            if update_button:

                success = update_request_status(
                    selected_request,
                    new_status
                )

                if success:
                    st.success("Request status updated!")
                    st.rerun()

                else:
                    st.error("Unable to update request.")

    else:
        st.info("No water requests available.")


# --------------------------------------------------
# AI SCHEDULER PAGE
# --------------------------------------------------

# --------------------------------------------------
# AI SCHEDULER PAGE
# --------------------------------------------------

elif page == "AI Scheduler":

    st.title("🧠 AI Scheduling Engine")

    st.caption(
        "Constraint Satisfaction Problem based tanker allocation"
    )

    st.markdown("---")

    st.subheader("CSP Scheduling System")

    st.write(
        "Generate an optimized tanker allocation schedule "
        "using AC-3 constraint propagation and Backtracking Search."
    )

    pending_requests = (
        requests[requests["Status"] == "Pending"]
        if not requests.empty else pd.DataFrame()
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Registered Tankers", len(tankers))

    with col2:
        st.metric("Pending Requests", len(pending_requests))

    with col3:
        st.metric("CSP Algorithm", "AC-3 + Backtracking")

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
            hide_index=True
        )

        st.markdown("---")

        if st.button("🚀 Generate AI Schedule", type="primary"):

            with st.spinner("Running CSP scheduling algorithms..."):

                result = generate_schedule_from_database()

                if result["success"]:
                    run_id = save_schedule(result["assignments"])
                    st.success(
                        f"AI Schedule generated and saved successfully! "
                        f"Schedule Run ID: {run_id}"
                    )

                st.markdown("---")

                st.subheader("⚙️ Algorithm Execution Results")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "Candidate Assignments",
                        result["domains_before"]
                    )

                with col2:
                    st.metric(
                        "AC-3 Values Removed",
                        result["removed_values"]
                    )

                with col3:
                    st.metric(
                        "Final Assignments",
                        len(result["assignments"])
                    )

                st.markdown("---")

                st.subheader("🚛 Recommended Tanker Allocation")

                if result["assignments"]:

                    schedule_data = []

                    for request_id, assignment in result["assignments"].items():

                        schedule_data.append({
                            "Request ID": request_id,
                            "Assigned Tanker": assignment.tanker_id,
                            "Delivery Time": assignment.display_time(),
                            "Water Quantity (L)": assignment.quantity,
                            "Delivery Location": assignment.location
                        })

                    schedule_df = pd.DataFrame(schedule_data)

                    st.dataframe(
                        schedule_df,
                        use_container_width=True,
                        hide_index=True
                    )

                else:
                    st.info("No assignments were generated.")

                st.markdown("---")

                st.subheader("🔍 CSP Domain Analysis")

                before_count = result["domains_before"]
                after_count = result["domains_after"]

                col1, col2 = st.columns(2)

                with col1:
                    st.metric("Domains Before AC-3", before_count)

                with col2:
                    st.metric("Domains After AC-3", after_count)

                st.caption(
                    "AC-3 removes assignment values that have no "
                    "compatible values in connected domains."
                )

                st.info(
                    "Backtracking Search was used to find a valid "
                    "combination of tanker assignments."
                )

                if not result["success"]:
                    st.error(result["message"])
                    st.warning(
                        "The CSP engine could not find a valid schedule. "
                        "Check tanker capacity, water availability, "
                        "and request requirements."
                    )

    st.markdown("---")

    st.subheader("🧠 AI Scheduling Workflow")

    st.markdown("""
    1. Read tanker and pending request information from SQLite.
    2. Create CSP variables and possible assignment domains.
    3. Apply tanker capacity and water availability constraints.
    4. Run AC-3 constraint propagation.
    5. Apply Backtracking Search with MRV and LCV heuristics.
    6. Generate the recommended tanker allocation schedule.
    """)

    st.markdown("---")

st.subheader("📚 Saved Schedule History")

history = get_schedule_history()

if history:

    history_df = pd.DataFrame(
        history,
        columns=[
            "Run ID",
            "Generated At",
            "Status",
            "Total Assignments"
        ]
    )

    st.dataframe(
        history_df,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("📋 Latest Saved Schedule")

    latest_schedule = get_latest_schedule()

    if latest_schedule:

        latest_df = pd.DataFrame(
            latest_schedule,
            columns=[
                "Request ID",
                "Tanker ID",
                "Delivery Time",
                "Quantity (L)",
                "Location"
            ]
        )

        st.dataframe(
            latest_df,
            use_container_width=True,
            hide_index=True
        )

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

st.write(
    "The simulation uses the latest schedule saved in SQLite."
)

scenario_options = {
    "Normal Operation": "normal",
    "Traffic Congestion": "traffic",
    "Tanker Breakdown": "breakdown",
    "High Water Demand": "high_demand"
}

selected_scenario = st.selectbox(
    "Select Simulation Scenario",
    list(scenario_options.keys())
)

scenario = scenario_options[selected_scenario]

simulation_steps = st.number_input(
    "Number of Simulation Steps",
    min_value=1,
    max_value=100,
    value=5
)

breakdown_tanker_id = None

if scenario == "breakdown":

    saved_assignments = get_latest_schedule_for_simulation()

    tanker_options = sorted({
        item["tanker_id"]
        for item in saved_assignments
    })

    if tanker_options:
        breakdown_tanker_id = st.selectbox(
            "Select Tanker to Break Down",
            tanker_options
        )
    else:
        st.warning("No saved tanker assignments available.")

if st.button("▶ Run MESA Simulation", type="primary"):

    with st.spinner("Running multi-agent simulation..."):

        simulation_result = run_latest_simulation(
            steps=int(simulation_steps),
            scenario=scenario,
            breakdown_tanker_id=breakdown_tanker_id
        )

    if simulation_result["success"]:
        st.success("Simulation completed successfully!")
    else:
        st.error(simulation_result["message"])

    if simulation_result["success"]:

        st.success("Simulation completed successfully!")

        model_results = simulation_result["model_results"]
        agent_results = simulation_result["agent_results"]

        final_result = model_results.iloc[-1]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Completed Deliveries",
                int(final_result["Completed Deliveries"])
            )

        with col2:
            st.metric(
                "Active Tankers",
                int(final_result["Active Tankers"])
            )

        with col3:
            st.metric(
                "Pending Deliveries",
                int(final_result["Pending Deliveries"])
            )

        st.markdown("---")

        st.subheader("📈 Delivery Progress")

        progress_chart = px.line(
            model_results,
            y="Completed Deliveries",
            markers=True,
            title="Completed Deliveries Over Simulation Steps"
        )

        progress_chart.update_layout(
            paper_bgcolor="#0B1120",
            plot_bgcolor="#0B1120",
            font_color="wh(.venv) batman@jash:~/TankerTrack$ nl -ba main.py | sed -n '850,1050p'
   850          st.subheader("🚛 Tanker Agent Performance")
   851
   852          agent_summary = (
   853              agent_results
   854              .reset_index()
   855              .sort_values(["AgentID", "Step"])
   856              .groupby("Tanker ID", as_index=False)
   857              .tail(1)
   858          )
   859
   860          st.dataframe(
   861              agent_summary[
   862                  [
   863                      "Tanker ID",
   864                      "Status",
   865                      "Completed Deliveries",
   866                      "Travel Progress"
   867                  ]
   868              ],
   869              use_container_width=True,
   870              hide_index=True
   871          )
   872
   873          st.subheader("📋 Complete Simulation Data")
   874
   875          st.dataframe(
   876              model_results,
   877              use_container_width=True
   878          )
   879
   880      else:
   881
   882          st.warning(simulation_result["message"])
   883
   884              # --------------------------------------------------
   885      # BASELINE VS CSP COMPARISON
   886      # --------------------------------------------------
   887
   888      st.markdown("---")
   889
   890      st.title("📊 Baseline vs AI-CSP Comparison")
   891
   892      st.write(
   893          "Compare Greedy First-Fit scheduling against "
   894          "the CSP-based AI scheduling algorithm."
   895      )
   896      
   897      if st.button("📊 Run Scheduler Comparison"):
   898
   899          with st.spinner("Comparing scheduling algorithms..."):
   900
   901              comparison = run_scheduler_comparison()
   902
   903          baseline = comparison["baseline"]
   904          csp = comparison["csp"]
   905
   906          st.success("Comparison completed!")
   907
   908          comparison_df = pd.DataFrame({
   909              "Metric": [
   910                  "Requests Scheduled",
   911                  "Completion Rate (%)",
   912                  "Execution Time (seconds)"
   913              ],
   914              "Greedy Baseline": [
   915                  baseline["scheduled"],
   916                  round(baseline["completion_rate"], 2),
   917                  round(baseline["execution_time"], 6)
   918              ],
   919              "AI-CSP": [
   920                  csp["scheduled"],
   921                  round(csp["completion_rate"], 2),
   922                  round(csp["execution_time"], 6)
   923              ]
   924          })
   925
   926          st.subheader("Algorithm Performance")
   927
   928          st.dataframe(
   929              comparison_df,
   930              use_container_width=True,
   931              hide_index=True
   932          )
   933
   934          chart_df = pd.DataFrame({
   935              "Algorithm": [
   936                  "Greedy Baseline",
   937                  "AI-CSP"
   938              ],
   939              "Completion Rate": [
   940                  baseline["completion_rate"],
   941                  csp["completion_rate"]
   942              ]
   943          })
   944
   945          fig = px.bar(
   946              chart_df,
   947              x="Algorithm",
   948              y="Completion Rate",
   949              text="Completion Rate",
   950              title="Request Completion Rate Comparison",
   951              range_y=[0, 100]
   952          )
   953
   954          fig.update_layout(
   955              paper_bgcolor="#0B1120",
   956              plot_bgcolor="#0B1120",
   957              font_color="white"
   958          )
   959
   960          st.plotly_chart(
   961              fig,
   962              use_container_width=True
   963          )
   964
   965              # --------------------------------------------------
   966      # PERFORMANCE EVALUATION
   967      # --------------------------------------------------
   968
   969      st.markdown("---")
   970
   971      st.title("📈 System Performance Evaluation")
   972
   973      st.write(
   974          "Evaluate tanker distribution performance "
   975          "under four operating scenarios."
   976      )
   977
   978      evaluation_steps = st.number_input(
   979          "Evaluation Simulation Steps",
   980          min_value=1,
   981          max_value=100,
   982          value=10,
   983          key="evaluation_steps"
   984      )
   985
   986      if st.button("Run Complete Performance Evaluation"):
   987
   988          with st.spinner("Evaluating all scenarios..."):
   989
   990              evaluation = evaluate_all_scenarios(
   991                  steps=int(evaluation_steps)
   992              )
   993
   994          if evaluation["success"]:
   995
   996              st.success(evaluation["message"])
   997
   998              performance_df = pd.DataFrame(
   999                  evaluation["results"]
  1000              )
  1001
  1002              st.subheader("📊 Performance Results")
  1003
  1004              st.dataframe(
  1005                  performance_df,
  1006                  use_container_width=True,
  1007                  hide_index=True
  1008              )
  1009
  1010              st.subheader("Delivery Completion Comparison")
  1011
  1012              fig = px.bar(
  1013                  performance_df,
  1014                  x="Scenario",
  1015                  y="Completion Rate (%)",
  1016                  color="Scenario",
  1017                  text="Completion Rate (%)",
  1018                  title="Delivery Completion Rate"
  1019              )
  1020
  1021              fig.update_layout(
  1022                  paper_bgcolor="#0B1120",
  1023                  plot_bgcolor="#0B1120",
  1024                  font_color="white",
  1025                  showlegend=False
  1026              )
  1027
  1028              st.plotly_chart(
  1029                  fig,
  1030                  use_container_width=True
  1031              )
  1032
  1033              st.subheader("Tanker Utilization")
  1034
  1035              utilization_fig = px.bar(
  1036                  performance_df,
  1037                  x="Scenario",
  1038                  y="Tanker Utilization (%)",
  1039                  text="Tanker Utilization (%)",
  1040                  title="Tanker Utilization by Scenario"
  1041              )
  1042
  1043              utilization_fig.update_layout(
  1044                  paper_bgcolor="#0B1120",
  1045                  plot_bgcolor="#0B1120",
  1046                  font_color="white"
  1047              )
  1048
  1049              st.plotly_chart(
  1050                  utilization_fig,
(.venv) batman@jash:~/TankerTrack$ tail -n 180 main.py
            model_results,
            use_container_width=True
        )

    else:

        st.warning(simulation_result["message"])

            # --------------------------------------------------
    # BASELINE VS CSP COMPARISON
    # --------------------------------------------------

    st.markdown("---")

    st.title("📊 Baseline vs AI-CSP Comparison")

    st.write(
        "Compare Greedy First-Fit scheduling against "
        "the CSP-based AI scheduling algorithm."
    )

    if st.button("📊 Run Scheduler Comparison"):

        with st.spinner("Comparing scheduling algorithms..."):

            comparison = run_scheduler_comparison()

        baseline = comparison["baseline"]
        csp = comparison["csp"]

        st.success("Comparison completed!")

        comparison_df = pd.DataFrame({
            "Metric": [
                "Requests Scheduled",
                "Completion Rate (%)",
                "Execution Time (seconds)"
            ],
            "Greedy Baseline": [
                baseline["scheduled"],
                round(baseline["completion_rate"], 2),
                round(baseline["execution_time"], 6)
            ],
            "AI-CSP": [
                csp["scheduled"],
                round(csp["completion_rate"], 2),
                round(csp["execution_time"], 6)
            ]
        })

        st.subheader("Algorithm Performance")

        st.dataframe(
            comparison_df,
            use_container_width=True,
            hide_index=True
        )

        chart_df = pd.DataFrame({
            "Algorithm": [
                "Greedy Baseline",
                "AI-CSP"
            ],
            "Completion Rate": [
                baseline["completion_rate"],
                csp["completion_rate"]
            ]
        })

        fig = px.bar(
            chart_df,
            x="Algorithm",
            y="Completion Rate",
            text="Completion Rate",
            title="Request Completion Rate Comparison",
            range_y=[0, 100]
        )

        fig.update_layout(
            paper_bgcolor="#0B1120",
            plot_bgcolor="#0B1120",
            font_color="white"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

            # --------------------------------------------------
    # PERFORMANCE EVALUATION
    # --------------------------------------------------

    st.markdown("---")

    st.title("📈 System Performance Evaluation")

    st.write(
        "Evaluate tanker distribution performance "
        "under four operating scenarios."
    )

    evaluation_steps = st.number_input(
        "Evaluation Simulation Steps",
        min_value=1,
        max_value=100,
        value=10,
        key="evaluation_steps"
    )

    if st.button("Run Complete Performance Evaluation"):

        with st.spinner("Evaluating all scenarios..."):

            evaluation = evaluate_all_scenarios(
                steps=int(evaluation_steps)
            )

        if evaluation["success"]:

            st.success(evaluation["message"])

            performance_df = pd.DataFrame(
                evaluation["results"]
            )

            st.subheader("📊 Performance Results")

            st.dataframe(
                performance_df,
                use_container_width=True,
                hide_index=True
            )

            st.subheader("Delivery Completion Comparison")

            fig = px.bar(
                performance_df,
                x="Scenario",
                y="Completion Rate (%)",
                color="Scenario",
                text="Completion Rate (%)",
                title="Delivery Completion Rate"
            )

            fig.update_layout(
                paper_bgcolor="#0B1120",
                plot_bgcolor="#0B1120",
                font_color="white",
                showlegend=False
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            st.subheader("Tanker Utilization")

            utilization_fig = px.bar(
                performance_df,
                x="Scenario",
                y="Tanker Utilization (%)",
                text="Tanker Utilization (%)",
                title="Tanker Utilization by Scenario"
            )

            utilization_fig.update_layout(
                paper_bgcolor="#0B1120",
                plot_bgcolor="#0B1120",
                font_color="white"
            )

            st.plotly_chart(
                utilization_fig,
                use_container_width=True
            )

        else:
            st.warning(evaluation["message"])(.venv) ite",
            xaxis_title="Simulation Step",
            yaxis_title="Completed Deliveries"
        )

        st.plotly_chart(
            progress_chart,
            use_container_width=True
        )

        st.markdown("---")

        st.subheader("🚛 Tanker Agent Performance")

        agent_summary = (
            agent_results
            .reset_index()
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
                    "Travel Progress"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        st.subheader("📋 Complete Simulation Data")

        st.dataframe(
            model_results,
            use_container_width=True
        )

    else:

        st.warning(simulation_result["message"])

            # --------------------------------------------------
    # BASELINE VS CSP COMPARISON
    # --------------------------------------------------

    st.markdown("---")

    st.title("📊 Baseline vs AI-CSP Comparison")

    st.write(
        "Compare Greedy First-Fit scheduling against "
        "the CSP-based AI scheduling algorithm."
    )

    if st.button("📊 Run Scheduler Comparison"):

        with st.spinner("Comparing scheduling algorithms..."):

            comparison = run_scheduler_comparison()

        baseline = comparison["baseline"]
        csp = comparison["csp"]

        st.success("Comparison completed!")

        comparison_df = pd.DataFrame({
            "Metric": [
                "Requests Scheduled",
                "Completion Rate (%)",
                "Execution Time (seconds)"
            ],
            "Greedy Baseline": [
                baseline["scheduled"],
                round(baseline["completion_rate"], 2),
                round(baseline["execution_time"], 6)
            ],
            "AI-CSP": [
                csp["scheduled"],
                round(csp["completion_rate"], 2),
                round(csp["execution_time"], 6)
            ]
        })

        st.subheader("Algorithm Performance")

        st.dataframe(
            comparison_df,
            use_container_width=True,
            hide_index=True
        )

        chart_df = pd.DataFrame({
            "Algorithm": [
                "Greedy Baseline",
                "AI-CSP"
            ],
            "Completion Rate": [
                baseline["completion_rate"],
                csp["completion_rate"]
            ]
        })

        fig = px.bar(
            chart_df,
            x="Algorithm",
            y="Completion Rate",
            text="Completion Rate",
            title="Request Completion Rate Comparison",
            range_y=[0, 100]
        )

        fig.update_layout(
            paper_bgcolor="#0B1120",
            plot_bgcolor="#0B1120",
            font_color="white"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

            # --------------------------------------------------
    # PERFORMANCE EVALUATION
    # --------------------------------------------------

    st.markdown("---")

    st.title("📈 System Performance Evaluation")

    st.write(
        "Evaluate tanker distribution performance "
        "under four operating scenarios."
    )

    evaluation_steps = st.number_input(
        "Evaluation Simulation Steps",
        min_value=1,
        max_value=100,
        value=10,
        key="evaluation_steps"
    )

    if st.button("Run Complete Performance Evaluation"):

        with st.spinner("Evaluating all scenarios..."):

            evaluation = evaluate_all_scenarios(
                steps=int(evaluation_steps)
            )

        if evaluation["success"]:

            st.success(evaluation["message"])

            performance_df = pd.DataFrame(
                evaluation["results"]
            )

            st.subheader("📊 Performance Results")

            st.dataframe(
                performance_df,
                use_container_width=True,
                hide_index=True
            )

            st.subheader("Delivery Completion Comparison")

            fig = px.bar(
                performance_df,
                x="Scenario",
                y="Completion Rate (%)",
                color="Scenario",
                text="Completion Rate (%)",
                title="Delivery Completion Rate"
            )

            fig.update_layout(
                paper_bgcolor="#0B1120",
                plot_bgcolor="#0B1120",
                font_color="white",
                showlegend=False
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            st.subheader("Tanker Utilization")

            utilization_fig = px.bar(
                performance_df,
                x="Scenario",
                y="Tanker Utilization (%)",
                text="Tanker Utilization (%)",
                title="Tanker Utilization by Scenario"
            )

            utilization_fig.update_layout(
                paper_bgcolor="#0B1120",
                plot_bgcolor="#0B1120",
                font_color="white"
            )

            st.plotly_chart(
                utilization_fig,
                use_container_width=True
            )

        else:
            st.warning(evaluation["message"])
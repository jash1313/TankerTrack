import streamlit as st
import pandas as pd
import plotly.express as px

from database import (
    initialize_database,
    add_tanker,
    add_request,
    get_all_tankers,
    get_all_requests,
    update_request_status
)

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
st.sidebar.info("AI Engine: Under Development")

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

elif page == "AI Scheduler":

    st.title("🧠 AI Scheduling Engine")

    st.caption(
        "Constraint Satisfaction Problem based tanker allocation"
    )

    st.markdown("---")

    st.info(
        "The AI scheduling engine is currently under development. "
        "CSP, AC-3 and Backtracking will be integrated in a later phase."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("CSP Variables", "Pending")

    with col2:
        st.metric("AC-3", "Pending")

    with col3:
        st.metric("Backtracking", "Pending")

    st.markdown("---")

    st.subheader("System Input Summary")

    st.write(f"Registered Tankers: {len(tankers)}")
    st.write(f"Registered Requests: {len(requests)}")

    st.markdown("---")

    st.subheader("Planned AI Workflow")

    st.markdown("""
    1. Collect tanker and water request information.
    2. Create CSP variables and domains.
    3. Apply capacity and availability constraints.
    4. Run AC-3 constraint propagation.
    5. Apply Backtracking Search.
    6. Generate the final tanker allocation schedule.
    7. Pass the schedule to MESA for simulation.
    """)

    st.warning("No actual AI scheduling is performed yet.")
